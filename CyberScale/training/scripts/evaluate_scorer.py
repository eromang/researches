"""Comprehensive evaluation of the Phase 1 severity scorer model (4-class classification).

Produces: overall accuracy, macro F1, per-class precision/recall/F1,
confusion matrix, confidence calibration, and a markdown report with pass/fail summary.

Usage:
    cd CyberScale
    poetry run python training/scripts/evaluate_scorer.py \
        --model data/models/scorer \
        --data training/data/training_cves.csv \
        --config training/configs/scorer.json \
        --output evaluation/scorer_report.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Allow importing from src/ when running from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.scorer import SeverityScorer  # noqa: E402

# Class index <-> label mapping (must match training)
LABEL_NAMES = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
LABEL_ORDER = ["Low", "Medium", "High", "Critical"]


# ---------------------------------------------------------------------------
# Helpers (must match training split logic exactly)
# ---------------------------------------------------------------------------
def score_to_label(score: float) -> int:
    """Convert CVSS score to class index (mirrors train_scorer.py)."""
    if score >= 9.0:
        return 3  # Critical
    if score >= 7.0:
        return 2  # High
    if score >= 4.0:
        return 1  # Medium
    return 0  # Low


def load_test_split(
    data_path: Path, config: dict
) -> tuple[list[str], list[str | None], list[int]]:
    """Load CSV and return test split (descriptions, cwes, true_labels).

    Reproduces the exact same split as training using the same seed,
    test_split ratio, and stratification bins.
    """
    eval_cfg = config["evaluation"]
    model_cfg = config["model"]
    seed = model_cfg.get("seed", 42)
    test_size = eval_cfg.get("test_split", 0.15)

    df = pd.read_csv(data_path)
    df = df.dropna(subset=["description", "cvss_score"]).reset_index(drop=True)

    descriptions = df["description"].tolist()
    cwes = df["cwe"].tolist() if "cwe" in df.columns else [None] * len(df)
    scores = df["cvss_score"].astype(float).tolist()

    # Convert scores to class labels (same as training)
    labels = [score_to_label(s) for s in scores]

    indices = list(range(len(descriptions)))

    _, test_idx = train_test_split(
        indices, test_size=test_size, random_state=seed, stratify=labels
    )

    test_desc = [descriptions[i] for i in test_idx]
    test_cwes = [cwes[i] for i in test_idx]
    test_labels = [labels[i] for i in test_idx]

    return test_desc, test_cwes, test_labels


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(
    model_path: Path,
    data_path: Path,
    config: dict,
    output_path: Path,
) -> dict:
    """Run full evaluation and write markdown report."""
    model_cfg = config["model"]
    mc_passes = model_cfg.get("mc_dropout_passes", 5)

    # Load model
    print(f"Loading model from {model_path} ...", flush=True)
    scorer = SeverityScorer(
        model_path=model_path,
        mc_passes=mc_passes,
        max_length=model_cfg.get("max_length", 192),
    )

    # Load test split
    print(f"Loading test split from {data_path} ...", flush=True)
    descriptions, cwes, true_labels = load_test_split(data_path, config)
    print(f"Test samples: {len(descriptions)}", flush=True)

    # Predict
    pred_labels: list[int] = []
    pred_bands: list[str] = []
    pred_confidences: list[str] = []

    label_to_idx = {v: k for k, v in LABEL_NAMES.items()}

    for i, (desc, cwe) in enumerate(zip(descriptions, cwes)):
        cwe_str = str(cwe) if cwe and str(cwe).lower() not in ("nan", "none", "") else None
        result = scorer.predict(desc, cwe=cwe_str)
        pred_bands.append(result.band)
        pred_labels.append(label_to_idx[result.band])
        pred_confidences.append(result.confidence)

        if (i + 1) % 100 == 0:
            print(f"  Predicted {i + 1}/{len(descriptions)}", flush=True)

    print(f"  Predicted {len(descriptions)}/{len(descriptions)} (done)", flush=True)

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    y_true = np.array(true_labels)
    y_pred = np.array(pred_labels)

    overall_acc = float(accuracy_score(y_true, y_pred))
    macro_f1 = float(f1_score(y_true, y_pred, average="macro"))

    # Per-class report (as dict)
    cls_report = classification_report(
        y_true, y_pred,
        labels=[0, 1, 2, 3],
        target_names=LABEL_ORDER,
        output_dict=True,
        zero_division=0,
    )

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1, 2, 3])

    # ------------------------------------------------------------------
    # Confidence calibration
    # ------------------------------------------------------------------
    conf_groups: dict[str, dict] = defaultdict(lambda: {"count": 0, "correct": 0})
    for conf, pl, tl in zip(pred_confidences, pred_labels, true_labels):
        conf_groups[conf]["count"] += 1
        if pl == tl:
            conf_groups[conf]["correct"] += 1

    conf_calibration: dict[str, dict] = {}
    for level in ("high", "medium", "low"):
        grp = conf_groups.get(level)
        if grp and grp["count"] > 0:
            conf_calibration[level] = {
                "count": grp["count"],
                "accuracy": round(grp["correct"] / grp["count"], 4),
            }
        else:
            conf_calibration[level] = {"count": 0, "accuracy": None}

    # ------------------------------------------------------------------
    # Pass / Fail
    # ------------------------------------------------------------------
    acc_pass = overall_acc > 0.75
    f1_pass = macro_f1 > 0.70

    metrics = {
        "accuracy": round(overall_acc, 4),
        "macro_f1": round(macro_f1, 4),
        "test_samples": len(descriptions),
        "acc_pass": acc_pass,
        "f1_pass": f1_pass,
        "overall_pass": acc_pass and f1_pass,
        "per_class": {
            name: {
                "precision": round(cls_report[name]["precision"], 4),
                "recall": round(cls_report[name]["recall"], 4),
                "f1": round(cls_report[name]["f1-score"], 4),
                "count": int(cls_report[name]["support"]),
            }
            for name in LABEL_ORDER
        },
        "confusion_matrix": cm.tolist(),
        "confidence_calibration": conf_calibration,
    }

    # ------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------
    print("\n--- Evaluation Results ---", flush=True)
    print(f"  Accuracy:  {overall_acc:.4f}  {'PASS' if acc_pass else 'FAIL'} (target > 0.75)", flush=True)
    print(f"  Macro F1:  {macro_f1:.4f}  {'PASS' if f1_pass else 'FAIL'} (target > 0.70)", flush=True)
    print(f"  Overall:   {'PASS' if metrics['overall_pass'] else 'FAIL'}", flush=True)

    # ------------------------------------------------------------------
    # Write markdown report
    # ------------------------------------------------------------------
    report = generate_markdown_report(metrics, config)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to {output_path}", flush=True)

    return metrics


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------
def generate_markdown_report(metrics: dict, config: dict) -> str:
    """Generate a markdown evaluation report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    overall = "PASS" if metrics["overall_pass"] else "FAIL"
    acc_status = "PASS" if metrics["acc_pass"] else "FAIL"
    f1_status = "PASS" if metrics["f1_pass"] else "FAIL"

    lines = [
        "# Phase 1 Scorer Evaluation Report",
        "",
        f"**Generated:** {ts}",
        f"**Test samples:** {metrics['test_samples']}",
        f"**MC dropout passes:** {config['model'].get('mc_dropout_passes', 5)}",
        f"**Overall:** {overall}",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value | Target | Status |",
        "|--------|-------|--------|--------|",
        f"| Accuracy | {metrics['accuracy']:.4f} | > 0.75 | {acc_status} |",
        f"| Macro F1 | {metrics['macro_f1']:.4f} | > 0.70 | {f1_status} |",
        "",
        "## Per-Class Breakdown",
        "",
        "| Class | Precision | Recall | F1 | Count |",
        "|-------|-----------|--------|----|-------|",
    ]

    for name in LABEL_ORDER:
        cls = metrics["per_class"][name]
        lines.append(
            f"| {name} | {cls['precision']:.4f} | {cls['recall']:.4f} "
            f"| {cls['f1']:.4f} | {cls['count']} |"
        )

    lines.extend([
        "",
        "## Confidence Calibration",
        "",
        "| Confidence | Count | Accuracy |",
        "|------------|-------|----------|",
    ])

    for level in ("high", "medium", "low"):
        cal = metrics["confidence_calibration"].get(level, {})
        count = cal.get("count", 0)
        acc_val = cal.get("accuracy")
        acc_str = f"{acc_val:.4f}" if acc_val is not None else "--"
        lines.append(f"| {level} | {count} | {acc_str} |")

    # Confusion matrix
    cm = metrics["confusion_matrix"]
    lines.extend([
        "",
        "## Confusion Matrix",
        "",
        "```",
        f"{'':>12s}  {'Low':>8s}  {'Medium':>8s}  {'High':>8s}  {'Critical':>8s}   <- predicted",
    ])
    for i, name in enumerate(LABEL_ORDER):
        row = "  ".join(f"{cm[i][j]:>8d}" for j in range(4))
        lines.append(f"{name:>12s}  {row}")
    lines.extend([
        "^ actual",
        "```",
    ])

    lines.extend([
        "",
        "## Pass/Fail Summary",
        "",
        f"- Accuracy > 75%: **{acc_status}** ({metrics['accuracy']:.4f})",
        f"- Macro F1 > 70%: **{f1_status}** ({metrics['macro_f1']:.4f})",
        f"- **Overall: {overall}**",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate Phase 1 severity scorer model"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model directory",
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to training CSV (same file used for training)",
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to scorer.json config",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for markdown report output",
    )

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    evaluate(
        model_path=Path(args.model),
        data_path=Path(args.data),
        config=config,
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
