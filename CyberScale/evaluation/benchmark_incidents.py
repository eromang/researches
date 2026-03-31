#!/usr/bin/env python3
"""End-to-end evaluation benchmark for CyberScale Phase 3 incident classification.

Generates a fresh test set (seed=999), runs T-model and O-model predictions,
computes per-model and end-to-end matrix metrics, and validates 6 illustrative
use cases from the Blueprint taxonomy.

Usage:
    poetry run python evaluation/benchmark_incidents.py \
        --t-model data/models/technical \
        --o-model data/models/operational \
        --output evaluation/incident_benchmark.md
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from datetime import datetime
from functools import partial
from pathlib import Path

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from generate_incidents import (
    assign_t_level,
    assign_o_level,
    generate_t_samples,
    generate_o_samples,
    balance_classes,
    BASE_TEMPLATES,
    SECTORS,
    SERVICE_IMPACTS,
    CASCADING,
    DATA_IMPACTS,
    ENTITY_RELEVANCE,
    CROSS_BORDER,
    MS_AFFECTED_RANGE,
    CAPACITY_EXCEEDED,
    ENTITIES_RANGE,
    SECTORS_AFFECTED_RANGE,
)
from cyberscale.models.technical import TechnicalClassifier
from cyberscale.models.operational import OperationalClassifier
from cyberscale.matrix.dual_scale import classify_incident

print = partial(print, flush=True)

BENCHMARK_SEED = 999
TEST_SIZE_PER_CLASS = 125  # 125 x 4 = 500

# ---------------------------------------------------------------------------
# Illustrative use cases (Blueprint taxonomy)
# ---------------------------------------------------------------------------

ILLUSTRATIVE_CASES = [
    {
        "name": "Below threshold (T1/O1)",
        "description": "Minor port scan at a small non-essential research lab, national only",
        "t_fields": {
            "service_impact": "partial",
            "affected_entities": 1,
            "sectors_affected": 1,
            "cascading": "none",
            "data_impact": "none",
        },
        "o_fields": {
            "sectors_affected": 1,
            "entity_relevance": "non_essential",
            "ms_affected": 1,
            "cross_border_pattern": "none",
            "capacity_exceeded": False,
        },
        "expected_t": "T1",
        "expected_o": "O1",
    },
    {
        "name": "Significant (T2/O2)",
        "description": "DDoS on essential banking service, 2 MS, limited cross-border",
        "t_fields": {
            "service_impact": "degraded",
            "affected_entities": 5,
            "sectors_affected": 1,
            "cascading": "none",
            "data_impact": "none",
        },
        "o_fields": {
            "sectors_affected": 1,
            "entity_relevance": "essential",
            "ms_affected": 2,
            "cross_border_pattern": "limited",
            "capacity_exceeded": False,
        },
        "expected_t": "T2",
        "expected_o": "O2",
    },
    {
        "name": "Large-scale (T3/O3)",
        "description": "Ransomware at hospital chain, unavailable services, 4 MS, significant cross-border",
        "t_fields": {
            "service_impact": "unavailable",
            "affected_entities": 25,
            "sectors_affected": 2,
            "cascading": "cross_sector",
            "data_impact": "exfiltrated",
        },
        "o_fields": {
            "sectors_affected": 2,
            "entity_relevance": "high_relevance",
            "ms_affected": 4,
            "cross_border_pattern": "significant",
            "capacity_exceeded": True,
        },
        "expected_t": "T3",
        "expected_o": "O3",
    },
    {
        "name": "Cyber crisis (T4/O4)",
        "description": "Supply chain compromise of digital infrastructure, sustained disruption, systemic cascade, 8 MS",
        "t_fields": {
            "service_impact": "sustained",
            "affected_entities": 150,
            "sectors_affected": 5,
            "cascading": "uncontrolled",
            "data_impact": "systemic",
        },
        "o_fields": {
            "sectors_affected": 5,
            "entity_relevance": "systemic",
            "ms_affected": 8,
            "cross_border_pattern": "systemic",
            "capacity_exceeded": True,
        },
        "expected_t": "T4",
        "expected_o": "O4",
    },
    {
        "name": "Asymmetric high-T/low-O (T4/O1)",
        "description": "Systemic data exfiltration from single non-essential research lab, national only",
        "t_fields": {
            "service_impact": "sustained",
            "affected_entities": 1,
            "sectors_affected": 1,
            "cascading": "none",
            "data_impact": "systemic",
        },
        "o_fields": {
            "sectors_affected": 1,
            "entity_relevance": "non_essential",
            "ms_affected": 1,
            "cross_border_pattern": "none",
            "capacity_exceeded": False,
        },
        "expected_t": "T4",
        "expected_o": "O1",
    },
    {
        "name": "Asymmetric low-T/high-O (T1/O4)",
        "description": "Minor phishing at systemic digital infrastructure provider, 7 MS, systemic cross-border",
        "t_fields": {
            "service_impact": "partial",
            "affected_entities": 1,
            "sectors_affected": 1,
            "cascading": "none",
            "data_impact": "none",
        },
        "o_fields": {
            "sectors_affected": 1,
            "entity_relevance": "systemic",
            "ms_affected": 7,
            "cross_border_pattern": "systemic",
            "capacity_exceeded": True,
        },
        "expected_t": "T1",
        "expected_o": "O4",
    },
]


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def compute_confusion_matrix(
    y_true: list[str], y_pred: list[str], labels: list[str],
) -> list[list[int]]:
    """Compute confusion matrix as list-of-lists."""
    idx = {l: i for i, l in enumerate(labels)}
    n = len(labels)
    cm = [[0] * n for _ in range(n)]
    for t, p in zip(y_true, y_pred):
        cm[idx[t]][idx[p]] += 1
    return cm


def compute_per_class_f1(
    y_true: list[str], y_pred: list[str], labels: list[str],
) -> dict[str, float]:
    """Compute per-class F1 scores."""
    f1s = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1s[label] = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return f1s


def compute_accuracy(y_true: list[str], y_pred: list[str]) -> float:
    """Compute accuracy."""
    if not y_true:
        return 0.0
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


def macro_f1(per_class: dict[str, float]) -> float:
    """Compute macro F1 from per-class dict."""
    if not per_class:
        return 0.0
    return sum(per_class.values()) / len(per_class)


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------

def format_confusion_matrix(cm: list[list[int]], labels: list[str]) -> str:
    """Format confusion matrix as markdown table."""
    lines = []
    header = "| Actual \\ Predicted | " + " | ".join(labels) + " |"
    sep = "|" + "---|" * (len(labels) + 1)
    lines.append(header)
    lines.append(sep)
    for i, label in enumerate(labels):
        row = f"| **{label}** | " + " | ".join(str(cm[i][j]) for j in range(len(labels))) + " |"
        lines.append(row)
    return "\n".join(lines)


def generate_report(
    t_model_path: str,
    o_model_path: str,
    n_scenarios: int,
    t_accuracy: float,
    t_macro_f1: float,
    t_per_class: dict[str, float],
    t_cm: list[list[int]],
    o_accuracy: float,
    o_macro_f1: float,
    o_per_class: dict[str, float],
    o_cm: list[list[int]],
    matrix_accuracy: float,
    matrix_dist: dict[str, int],
    use_case_results: list[dict],
    elapsed_seconds: float,
) -> str:
    """Generate the full markdown benchmark report."""
    t_labels = ["T1", "T2", "T3", "T4"]
    o_labels = ["O1", "O2", "O3", "O4"]

    # Pass/fail targets
    t_pass = t_macro_f1 > 0.75
    o_pass = o_macro_f1 > 0.75
    matrix_pass = matrix_accuracy > 0.70
    uc_pass = all(r["pass"] for r in use_case_results)
    overall_pass = t_pass and o_pass and matrix_pass

    report = f"""# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**T-model:** `{t_model_path}`
**O-model:** `{o_model_path}`
**Test scenarios:** {n_scenarios}
**Seed:** {BENCHMARK_SEED}
**Elapsed:** {elapsed_seconds:.1f}s

## T-model Results

- **Accuracy:** {t_accuracy * 100:.2f}%
- **Macro F1:** {t_macro_f1:.4f}

### Per-level F1

| Level | F1 |
|-------|-----|
"""
    for label in t_labels:
        report += f"| {label} | {t_per_class.get(label, 0.0):.4f} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(t_cm, t_labels)}

## O-model Results

- **Accuracy:** {o_accuracy * 100:.2f}%
- **Macro F1:** {o_macro_f1:.4f}

### Per-level F1

| Level | F1 |
|-------|-----|
"""
    for label in o_labels:
        report += f"| {label} | {o_per_class.get(label, 0.0):.4f} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(o_cm, o_labels)}

## End-to-end Matrix Results

- **Accuracy:** {matrix_accuracy * 100:.2f}%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
"""
    total = sum(matrix_dist.values())
    for cls in ["below_threshold", "significant", "large_scale", "cyber_crisis"]:
        count = matrix_dist.get(cls, 0)
        pct = count / total * 100 if total > 0 else 0
        report += f"| {cls} | {count} | {pct:.1f}% |\n"

    report += """
## Illustrative Use Cases

| # | Scenario | Expected T/O | Predicted T/O | Matrix | Pass |
|---|----------|-------------|--------------|--------|------|
"""
    for i, r in enumerate(use_case_results, 1):
        status = "PASS" if r["pass"] else "FAIL"
        report += (
            f"| {i} | {r['name']} | {r['expected_t']}/{r['expected_o']} | "
            f"{r['predicted_t']}/{r['predicted_o']} | {r['matrix']} | {status} |\n"
        )

    report += f"""
## Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| T-model macro F1 | > 75% | {t_macro_f1 * 100:.1f}% | {"PASS" if t_pass else "FAIL"} |
| O-model macro F1 | > 75% | {o_macro_f1 * 100:.1f}% | {"PASS" if o_pass else "FAIL"} |
| Matrix end-to-end | > 70% | {matrix_accuracy * 100:.1f}% | {"PASS" if matrix_pass else "FAIL"} |
| Illustrative cases | 6/6 | {sum(1 for r in use_case_results if r["pass"])}/6 | {"PASS" if uc_pass else "FAIL"} |
| **Overall** | **All pass** | | **{"PASS" if overall_pass else "FAIL"}** |
"""
    return report


# ---------------------------------------------------------------------------
# Test set generation
# ---------------------------------------------------------------------------

def generate_test_set(n_per_class: int, seed: int) -> tuple[list[dict], list[dict]]:
    """Generate balanced T and O test sets with different seed from training."""
    print(f"Generating T-level test set (seed={seed}, {n_per_class}/class)...")
    t_raw = generate_t_samples(n_per_class, paraphrase_variants=1, seed=seed)
    t_balanced = balance_classes(t_raw, n_per_class, seed)

    print(f"Generating O-level test set (seed={seed}, {n_per_class}/class)...")
    o_raw = generate_o_samples(n_per_class, paraphrase_variants=1, seed=seed)
    o_balanced = balance_classes(o_raw, n_per_class, seed)

    return t_balanced, o_balanced


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def extract_t_fields_from_text(text: str) -> dict:
    """Parse structured fields from the [SEP]-delimited text format."""
    # Text format: "description [SEP] service_impact: X entities: Y sectors: Z cascading: W data_impact: V"
    sep_idx = text.find("[SEP]")
    if sep_idx < 0:
        return {}
    fields_str = text[sep_idx + 6:].strip()
    fields = {}
    # Parse key: value pairs (values may be multi-word but keys are known)
    keys = ["service_impact", "entities", "sectors", "cascading", "data_impact"]
    for i, key in enumerate(keys):
        start = fields_str.find(f"{key}:")
        if start < 0:
            continue
        val_start = start + len(key) + 2  # skip "key: "
        # Find next key or end
        end = len(fields_str)
        for next_key in keys[i + 1:]:
            nk_pos = fields_str.find(f"{next_key}:")
            if nk_pos > 0:
                end = nk_pos
                break
        fields[key] = fields_str[val_start:end].strip()
    return fields


def extract_o_fields_from_text(text: str) -> dict:
    """Parse structured fields from the [SEP]-delimited text format."""
    sep_idx = text.find("[SEP]")
    if sep_idx < 0:
        return {}
    fields_str = text[sep_idx + 6:].strip()
    fields = {}
    keys = ["sectors", "relevance", "ms_affected", "cross_border", "capacity_exceeded"]
    for i, key in enumerate(keys):
        start = fields_str.find(f"{key}:")
        if start < 0:
            continue
        val_start = start + len(key) + 2
        end = len(fields_str)
        for next_key in keys[i + 1:]:
            nk_pos = fields_str.find(f"{next_key}:")
            if nk_pos > 0:
                end = nk_pos
                break
        fields[key] = fields_str[val_start:end].strip()
    return fields


def evaluate_t_model(
    t_model: TechnicalClassifier, t_test: list[dict],
) -> tuple[list[str], list[str]]:
    """Run T-model predictions on test set, return (y_true, y_pred)."""
    y_true, y_pred = [], []
    for i, sample in enumerate(t_test):
        if (i + 1) % 100 == 0:
            print(f"  T-model: {i + 1}/{len(t_test)}")
        # The text already has the [SEP] format — feed directly
        text = sample["text"]
        fields = extract_t_fields_from_text(text)
        desc_end = text.find("[SEP]")
        description = text[:desc_end].strip() if desc_end > 0 else text

        result = t_model.predict(
            description=description,
            service_impact=fields.get("service_impact", "partial"),
            affected_entities=int(fields.get("entities", "1")),
            sectors_affected=int(fields.get("sectors", "1")),
            cascading=fields.get("cascading", "none"),
            data_impact=fields.get("data_impact", "none"),
        )
        y_true.append(sample["label"])
        y_pred.append(result.level)
    return y_true, y_pred


def evaluate_o_model(
    o_model: OperationalClassifier, o_test: list[dict],
) -> tuple[list[str], list[str]]:
    """Run O-model predictions on test set, return (y_true, y_pred)."""
    y_true, y_pred = [], []
    for i, sample in enumerate(o_test):
        if (i + 1) % 100 == 0:
            print(f"  O-model: {i + 1}/{len(o_test)}")
        text = sample["text"]
        fields = extract_o_fields_from_text(text)
        desc_end = text.find("[SEP]")
        description = text[:desc_end].strip() if desc_end > 0 else text

        result = o_model.predict(
            description=description,
            sectors_affected=int(fields.get("sectors", "1")),
            entity_relevance=fields.get("relevance", "non_essential"),
            ms_affected=int(fields.get("ms_affected", "1")),
            cross_border_pattern=fields.get("cross_border", "none"),
            capacity_exceeded=fields.get("capacity_exceeded", "false").lower() == "true",
        )
        y_true.append(sample["label"])
        y_pred.append(result.level)
    return y_true, y_pred


def evaluate_matrix(
    t_true: list[str], t_pred: list[str],
    o_true: list[str], o_pred: list[str],
) -> tuple[float, dict[str, int]]:
    """Compute end-to-end matrix accuracy using paired T/O predictions.

    Uses min(len(t), len(o)) pairs for matrix evaluation.
    """
    n = min(len(t_true), len(o_true))
    correct = 0
    dist: dict[str, int] = Counter()

    for i in range(n):
        gt_matrix = classify_incident(t_true[i], o_true[i])
        pred_matrix = classify_incident(t_pred[i], o_pred[i])
        dist[pred_matrix.classification] += 1
        if pred_matrix.classification == gt_matrix.classification:
            correct += 1

    accuracy = correct / n if n > 0 else 0.0
    return accuracy, dict(dist)


def evaluate_use_cases(
    t_model: TechnicalClassifier,
    o_model: OperationalClassifier,
) -> list[dict]:
    """Evaluate the 6 illustrative use cases."""
    results = []
    for case in ILLUSTRATIVE_CASES:
        t_result = t_model.predict(description=case["description"], **case["t_fields"])
        o_result = o_model.predict(description=case["description"], **case["o_fields"])
        matrix_result = classify_incident(t_result.level, o_result.level)

        # Pass if within +/-1 level for both T and O
        t_num = int(t_result.level[1])
        t_exp = int(case["expected_t"][1])
        o_num = int(o_result.level[1])
        o_exp = int(case["expected_o"][1])
        is_pass = abs(t_num - t_exp) <= 1 and abs(o_num - o_exp) <= 1

        results.append({
            "name": case["name"],
            "expected_t": case["expected_t"],
            "expected_o": case["expected_o"],
            "predicted_t": t_result.level,
            "predicted_o": o_result.level,
            "matrix": matrix_result.label,
            "pass": is_pass,
        })
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CyberScale Phase 3 end-to-end incident classification benchmark"
    )
    parser.add_argument(
        "--t-model", type=Path, default=Path("data/models/technical"),
        help="Path to trained T-model directory",
    )
    parser.add_argument(
        "--o-model", type=Path, default=Path("data/models/operational"),
        help="Path to trained O-model directory",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evaluation/incident_benchmark.md"),
        help="Output path for markdown report",
    )
    parser.add_argument(
        "--mc-passes", type=int, default=5,
        help="MC dropout passes (lower = faster, default 5 for benchmark)",
    )
    args = parser.parse_args()

    start = time.time()

    # 1. Generate test set
    t_test, o_test = generate_test_set(TEST_SIZE_PER_CLASS, BENCHMARK_SEED)
    print(f"Test set: {len(t_test)} T-samples, {len(o_test)} O-samples")

    # 2. Load models
    print(f"Loading T-model from {args.t_model}...")
    t_model = TechnicalClassifier(args.t_model, mc_passes=args.mc_passes)
    print(f"Loading O-model from {args.o_model}...")
    o_model = OperationalClassifier(args.o_model, mc_passes=args.mc_passes)

    # 3. Evaluate T-model
    print("Evaluating T-model...")
    t_true, t_pred = evaluate_t_model(t_model, t_test)
    t_labels = ["T1", "T2", "T3", "T4"]
    t_accuracy = compute_accuracy(t_true, t_pred)
    t_per_class = compute_per_class_f1(t_true, t_pred, t_labels)
    t_mf1 = macro_f1(t_per_class)
    t_cm = compute_confusion_matrix(t_true, t_pred, t_labels)
    print(f"  T-model accuracy: {t_accuracy * 100:.2f}%, macro F1: {t_mf1:.4f}")

    # 4. Evaluate O-model
    print("Evaluating O-model...")
    o_true, o_pred = evaluate_o_model(o_model, o_test)
    o_labels = ["O1", "O2", "O3", "O4"]
    o_accuracy = compute_accuracy(o_true, o_pred)
    o_per_class = compute_per_class_f1(o_true, o_pred, o_labels)
    o_mf1 = macro_f1(o_per_class)
    o_cm = compute_confusion_matrix(o_true, o_pred, o_labels)
    print(f"  O-model accuracy: {o_accuracy * 100:.2f}%, macro F1: {o_mf1:.4f}")

    # 5. End-to-end matrix evaluation
    print("Computing end-to-end matrix results...")
    matrix_acc, matrix_dist = evaluate_matrix(t_true, t_pred, o_true, o_pred)
    print(f"  Matrix accuracy: {matrix_acc * 100:.2f}%")

    # 6. Illustrative use cases
    print("Evaluating illustrative use cases...")
    uc_results = evaluate_use_cases(t_model, o_model)
    for r in uc_results:
        status = "PASS" if r["pass"] else "FAIL"
        print(f"  {r['name']}: {r['predicted_t']}/{r['predicted_o']} -> {r['matrix']} [{status}]")

    elapsed = time.time() - start

    # 7. Generate report
    report = generate_report(
        t_model_path=str(args.t_model),
        o_model_path=str(args.o_model),
        n_scenarios=len(t_test) + len(o_test),
        t_accuracy=t_accuracy,
        t_macro_f1=t_mf1,
        t_per_class=t_per_class,
        t_cm=t_cm,
        o_accuracy=o_accuracy,
        o_macro_f1=o_mf1,
        o_per_class=o_per_class,
        o_cm=o_cm,
        matrix_accuracy=matrix_acc,
        matrix_dist=matrix_dist,
        use_case_results=uc_results,
        elapsed_seconds=elapsed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport written to {args.output}")
    print(f"Total time: {elapsed:.1f}s")

    # Exit with non-zero if any target missed
    if t_mf1 <= 0.75 or o_mf1 <= 0.75 or matrix_acc <= 0.70:
        print("\nWARNING: One or more targets not met.")
        sys.exit(1)


if __name__ == "__main__":
    main()
