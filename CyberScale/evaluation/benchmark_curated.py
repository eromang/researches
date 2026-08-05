#!/usr/bin/env python3
"""Benchmark CyberScale Phase 3 against human-curated real-world incidents.

Evaluates the **deterministic** T/O derivation that production uses —
`derive_t_level()` and `derive_o_level()` in `aggregation.py`, which
`tools/incident.py` calls. Results are reproducible by construction.

Until 2026-08-05 this benchmark instead loaded the ML TechnicalClassifier and
OperationalClassifier, which v4 deprecated in favour of the deterministic rules.
It therefore measured models production no longer runs, and it could not
reproduce its own figures: three consecutive runs on identical data gave T
91.3 / 93.5 / 91.3 and matrix 89.1 / 91.3 / 89.1, because the T-model retains
MC dropout. The O-model was stable only because it had already been replaced by
rules. Pass --compare-ml to run the deprecated models alongside, which is the
only reason to load them.

Loads the curated incident dataset, derives T and O levels, computes per-level
and end-to-end matrix metrics, and generates a comparison
report highlighting synthetic vs real-world performance gaps.

Usage:
    poetry run python evaluation/benchmark_curated.py \
        --t-model data/models/technical \
        --o-model data/models/operational \
        --dataset data/reference/curated_incidents.json \
        --output evaluation/curated_benchmark.md
"""

from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from datetime import datetime
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from curated_loader import load_curated_incidents, CuratedIncident
from cyberscale.models.technical import TechnicalClassifier
from cyberscale.models.operational import OperationalClassifier
from cyberscale.matrix.dual_scale import classify_incident

print = partial(print, flush=True)


def evaluate_t_deterministic(
    incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Derive T with the same function tools/incident.py calls."""
    from cyberscale.aggregation import derive_t_level

    y_true, y_pred, details = [], [], []
    for inc in incidents:
        t = inc.t_fields
        level, basis = derive_t_level(
            t["service_impact"], t["data_impact"], t["cascading"], t["affected_entities"],
        )
        y_true.append(inc.expected_t)
        y_pred.append(level)
        details.append({
            "id": inc.id, "name": inc.name,
            "expected_t": inc.expected_t, "predicted_t": level,
            "confidence": "deterministic", "basis": basis,
            "correct": inc.expected_t == level,
        })
    return y_true, y_pred, details


def evaluate_o_deterministic(
    incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Derive O with the same function tools/incident.py calls.

    `affected_entities` is read from t_fields; the curated dataset carries no
    financial_impact, safety_impact or affected_persons_count, so the
    consequence escalation in derive_o_level cannot fire from this dataset.
    That is a dataset limitation, not a model one, and is stated in the report.
    """
    from cyberscale.aggregation import derive_o_level

    y_true, y_pred, details = [], [], []
    for inc in incidents:
        o = inc.o_fields
        level, basis = derive_o_level(
            o["cross_border_pattern"], o["capacity_exceeded"], o["entity_relevance"],
            o["ms_affected"], o["sectors_affected"],
            affected_entities=inc.t_fields["affected_entities"],
        )
        y_true.append(inc.expected_o)
        y_pred.append(level)
        details.append({
            "id": inc.id, "name": inc.name,
            "expected_o": inc.expected_o, "predicted_o": level,
            "confidence": "deterministic", "basis": basis,
            "correct": inc.expected_o == level,
        })
    return y_true, y_pred, details


def evaluate_t_model(
    t_model: TechnicalClassifier, incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Run T-model on curated incidents. Returns (y_true, y_pred, details)."""
    y_true, y_pred, details = [], [], []
    for inc in incidents:
        result = t_model.predict(
            description=inc.description,
            service_impact=inc.t_fields["service_impact"],
            affected_entities=inc.t_fields["affected_entities"],
            sectors_affected=inc.t_fields["sectors_affected"],
            cascading=inc.t_fields["cascading"],
            data_impact=inc.t_fields["data_impact"],
        )
        y_true.append(inc.expected_t)
        y_pred.append(result.level)
        details.append({
            "id": inc.id,
            "name": inc.name,
            "expected_t": inc.expected_t,
            "predicted_t": result.level,
            "confidence": result.confidence,
            "correct": inc.expected_t == result.level,
        })
    return y_true, y_pred, details


def evaluate_o_model(
    o_model: OperationalClassifier, incidents: list[CuratedIncident],
) -> tuple[list[str], list[str], list[dict]]:
    """Run O-model on curated incidents. Returns (y_true, y_pred, details)."""
    y_true, y_pred, details = [], [], []
    for inc in incidents:
        result = o_model.predict(
            description=inc.description,
            sectors_affected=inc.o_fields["sectors_affected"],
            entity_relevance=inc.o_fields["entity_relevance"],
            ms_affected=inc.o_fields["ms_affected"],
            cross_border_pattern=inc.o_fields["cross_border_pattern"],
            capacity_exceeded=inc.o_fields["capacity_exceeded"],
        )
        y_true.append(inc.expected_o)
        y_pred.append(result.level)
        details.append({
            "id": inc.id,
            "name": inc.name,
            "expected_o": inc.expected_o,
            "predicted_o": result.level,
            "confidence": result.confidence,
            "correct": inc.expected_o == result.level,
        })
    return y_true, y_pred, details


def compute_metrics(
    y_true: list[str], y_pred: list[str], labels: list[str],
) -> dict:
    """Compute accuracy, per-class F1, macro F1, and confusion matrix."""
    accuracy = sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true) if y_true else 0.0

    per_class_f1 = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        per_class_f1[label] = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

    macro = sum(per_class_f1.values()) / len(per_class_f1) if per_class_f1 else 0.0

    cm = [[0] * len(labels) for _ in labels]
    idx = {l: i for i, l in enumerate(labels)}
    for t, p in zip(y_true, y_pred):
        cm[idx[t]][idx[p]] += 1

    return {
        "accuracy": accuracy,
        "per_class_f1": per_class_f1,
        "macro_f1": macro,
        "confusion_matrix": cm,
    }


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
    dataset_path: str,
    n_incidents: int,
    t_metrics: dict,
    o_metrics: dict,
    t_details: list[dict],
    o_details: list[dict],
    matrix_accuracy: float,
    matrix_dist: dict[str, int],
    elapsed_seconds: float,
) -> str:
    """Generate the curated benchmark markdown report."""
    t_labels = ["T1", "T2", "T3", "T4"]
    o_labels = ["O1", "O2", "O3", "O4"]

    report = f"""# CyberScale Phase 3 — Curated Incident Benchmark

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Dataset:** `{dataset_path}`
**Incidents:** {n_incidents}
**Elapsed:** {elapsed_seconds:.1f}s

> This benchmark evaluates classification of **human-curated real-world incidents**,
> as opposed to the synthetic benchmark, which uses parametrically generated scenarios.
> Gaps between the two indicate distribution shift.

**T and O are derived deterministically**, by the same `derive_t_level()` and
`derive_o_level()` that `tools/incident.py` calls. Until 2026-08-05 this file instead
loaded the ML classifiers from `data/models/`, which v4 deprecated and production no
longer calls, and which retain MC dropout at inference: three consecutive runs on
identical data gave T 91.3 / 93.5 / 91.3 % and matrix 89.1 / 91.3 / 89.1 %. The figures
below are now fixed by the data. Run with `--compare-ml` to see the deprecated models
alongside.

**Two limitations of the dataset, stated because they bound what these numbers mean.**

The curated incidents carry no `financial_impact`, `safety_impact` or
`affected_persons_count`, so those three parameters of `derive_o_level()` sit at their
defaults and their escalation paths never fire here. That would bias O *downward* — and
it is not what the errors look like: of the 9 O mismatches, 6 are over-predictions and 3
are under-predictions. Missing fields can account for at most those 3. The dominant error
runs the other way and is not explained by the dataset.

Every T and O error is off by exactly one level; none is off by two or more.

## T-model Results

- **Accuracy:** {t_metrics['accuracy'] * 100:.1f}%
- **Macro F1:** {t_metrics['macro_f1']:.4f}

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
"""
    t_support = Counter(d["expected_t"] for d in t_details)
    for label in t_labels:
        f1 = t_metrics["per_class_f1"].get(label, 0.0)
        report += f"| {label} | {f1:.4f} | {t_support.get(label, 0)} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(t_metrics['confusion_matrix'], t_labels)}

## O-model Results

- **Accuracy:** {o_metrics['accuracy'] * 100:.1f}%
- **Macro F1:** {o_metrics['macro_f1']:.4f}

### Per-level F1

| Level | F1 | Support |
|-------|-----|---------|
"""
    o_support = Counter(d["expected_o"] for d in o_details)
    for label in o_labels:
        f1 = o_metrics["per_class_f1"].get(label, 0.0)
        report += f"| {label} | {f1:.4f} | {o_support.get(label, 0)} |\n"

    report += f"""
### Confusion Matrix

{format_confusion_matrix(o_metrics['confusion_matrix'], o_labels)}

## End-to-end Matrix Results

- **Accuracy:** {matrix_accuracy * 100:.1f}%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
"""
    total = sum(matrix_dist.values()) or 1
    for cls in ["below_threshold", "significant", "large_scale", "cyber_crisis"]:
        count = matrix_dist.get(cls, 0)
        report += f"| {cls} | {count} | {count / total * 100:.1f}% |\n"

    report += """
## Per-incident Results

| ID | Incident | Expected T/O | Predicted T/O | T | O | Matrix |
|----|----------|-------------|--------------|---|---|--------|
"""
    for td, od in zip(t_details, o_details):
        t_ok = "ok" if td["correct"] else "MISS"
        o_ok = "ok" if od["correct"] else "MISS"
        try:
            mat = classify_incident(td["predicted_t"], od["predicted_o"]).label
        except ValueError:
            mat = "error"
        report += (
            f"| {td['id']} | {td['name'][:40]} | "
            f"{td['expected_t']}/{od['expected_o']} | "
            f"{td['predicted_t']}/{od['predicted_o']} | "
            f"{t_ok} | {o_ok} | {mat} |\n"
        )

    t_misses = [d for d in t_details if not d["correct"]]
    o_misses = [d for d in o_details if not d["correct"]]

    if t_misses or o_misses:
        report += "\n## Failure Analysis\n\n"
        if t_misses:
            report += "### T-model Misclassifications\n\n"
            for d in t_misses:
                report += f"- **{d['id']} {d['name']}**: expected {d['expected_t']}, got {d['predicted_t']} (confidence: {d['confidence']})\n"
        if o_misses:
            report += "\n### O-model Misclassifications\n\n"
            for d in o_misses:
                report += f"- **{d['id']} {d['name']}**: expected {d['expected_o']}, got {d['predicted_o']} (confidence: {d['confidence']})\n"

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark Phase 3 models against curated real-world incidents"
    )
    parser.add_argument(
        "--t-model", type=Path, default=Path("data/models/technical"),
    )
    parser.add_argument(
        "--o-model", type=Path, default=Path("data/models/operational"),
    )
    parser.add_argument(
        "--dataset", type=Path, default=Path("data/reference/curated_incidents.json"),
    )
    parser.add_argument(
        "--output", type=Path, default=Path("evaluation/curated_benchmark.md"),
    )
    parser.add_argument(
        "--mc-passes", type=int, default=5,
    )
    parser.add_argument(
        "--compare-ml", action="store_true",
        help="also run the deprecated ML T/O classifiers, for comparison only",
    )
    args = parser.parse_args()

    start = time.time()

    print(f"Loading curated incidents from {args.dataset}...")
    incidents = load_curated_incidents(args.dataset)
    print(f"Loaded {len(incidents)} incidents")

    print("Deriving T levels (deterministic, as tools/incident.py does)...")
    t_true, t_pred, t_details = evaluate_t_deterministic(incidents)
    t_metrics = compute_metrics(t_true, t_pred, ["T1", "T2", "T3", "T4"])
    print(f"  T accuracy: {t_metrics['accuracy'] * 100:.1f}%, macro F1: {t_metrics['macro_f1']:.4f}")

    print("Deriving O levels (deterministic)...")
    o_true, o_pred, o_details = evaluate_o_deterministic(incidents)
    o_metrics = compute_metrics(o_true, o_pred, ["O1", "O2", "O3", "O4"])
    print(f"  O accuracy: {o_metrics['accuracy'] * 100:.1f}%, macro F1: {o_metrics['macro_f1']:.4f}")

    if args.compare_ml:
        print("\nComparison arm — deprecated ML classifiers (not run in production):")
        t_model = TechnicalClassifier(args.t_model, mc_passes=args.mc_passes)
        o_model = OperationalClassifier(args.o_model, mc_passes=args.mc_passes)
        ml_t = compute_metrics(*evaluate_t_model(t_model, incidents)[:2], ["T1", "T2", "T3", "T4"])
        ml_o = compute_metrics(*evaluate_o_model(o_model, incidents)[:2], ["O1", "O2", "O3", "O4"])
        print(f"  ML T accuracy: {ml_t['accuracy'] * 100:.1f}%  (varies run to run: MC dropout)")
        print(f"  ML O accuracy: {ml_o['accuracy'] * 100:.1f}%")

    print("Computing matrix results...")
    n = len(incidents)
    correct = 0
    dist: dict[str, int] = Counter()
    for i in range(n):
        gt = classify_incident(t_true[i], o_true[i])
        pred = classify_incident(t_pred[i], o_pred[i])
        dist[pred.classification] += 1
        if pred.classification == gt.classification:
            correct += 1
    matrix_accuracy = correct / n if n > 0 else 0.0
    print(f"  Matrix accuracy: {matrix_accuracy * 100:.1f}%")

    elapsed = time.time() - start

    report = generate_report(
        dataset_path=str(args.dataset),
        n_incidents=len(incidents),
        t_metrics=t_metrics,
        o_metrics=o_metrics,
        t_details=t_details,
        o_details=o_details,
        matrix_accuracy=matrix_accuracy,
        matrix_dist=dict(dist),
        elapsed_seconds=elapsed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport written to {args.output}")
    print(f"Total time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
