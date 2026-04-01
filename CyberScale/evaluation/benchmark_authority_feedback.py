#!/usr/bin/env python3
"""Authority feedback regression benchmark.

Compares deterministic rules against accumulated authority decisions
to identify systematic rule gaps and calibration opportunities.

Usage:
    poetry run python evaluation/benchmark_authority_feedback.py \
        --feedback data/feedback/authority_decisions.json \
        --output evaluation/authority_feedback_report.md
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.feedback import load_decisions, compute_rule_accuracy

print = partial(print, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Authority feedback regression benchmark")
    parser.add_argument("--feedback", type=Path, default=Path("data/feedback/authority_decisions.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/authority_feedback_report.md"))
    args = parser.parse_args()

    decisions = load_decisions(args.feedback)
    if not decisions:
        print("No authority decisions found. Feedback store is empty.")
        print("Decisions are recorded when authorities override suggested classifications.")
        return

    metrics = compute_rule_accuracy(decisions)

    print(f"Authority decisions: {metrics['total']}")
    print(f"T-level accuracy: {metrics['t_accuracy']*100:.1f}%")
    print(f"O-level accuracy: {metrics['o_accuracy']*100:.1f}%")
    print(f"Matrix accuracy: {metrics['matrix_accuracy']*100:.1f}%")

    report = f"""# Authority Feedback Regression Report

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Decisions:** {metrics['total']}

## Rule Accuracy vs Authority Ground Truth

| Metric | Accuracy |
|--------|----------|
| T-level | {metrics['t_accuracy']*100:.1f}% |
| O-level | {metrics['o_accuracy']*100:.1f}% |
| Matrix classification | {metrics['matrix_accuracy']*100:.1f}% |

## Per-level Accuracy

### T-level
| Level | Accuracy | Support |
|-------|----------|---------|
"""
    for level in ["T1", "T2", "T3", "T4"]:
        acc = metrics.get("t_per_level", {}).get(level)
        support = sum(1 for d in decisions if d["actual_t"] == level)
        if acc is not None:
            report += f"| {level} | {acc*100:.1f}% | {support} |\n"

    report += "\n### O-level\n| Level | Accuracy | Support |\n|-------|----------|---------||\n"
    for level in ["O1", "O2", "O3", "O4"]:
        acc = metrics.get("o_per_level", {}).get(level)
        support = sum(1 for d in decisions if d["actual_o"] == level)
        if acc is not None:
            report += f"| {level} | {acc*100:.1f}% | {support} |\n"

    t_overrides = metrics.get("t_override_patterns", {})
    o_overrides = metrics.get("o_override_patterns", {})
    if t_overrides or o_overrides:
        report += "\n## Override Patterns\n\n"
        if t_overrides:
            report += "### T-level overrides\n| Pattern | Count |\n|---------|-------|\n"
            for pattern, count in sorted(t_overrides.items(), key=lambda x: -x[1]):
                report += f"| {pattern} | {count} |\n"
        if o_overrides:
            report += "\n### O-level overrides\n| Pattern | Count |\n|---------|-------|\n"
            for pattern, count in sorted(o_overrides.items(), key=lambda x: -x[1]):
                report += f"| {pattern} | {count} |\n"

    report += "\n## Recommendations\n\n"
    if metrics['t_accuracy'] < 0.8:
        report += "- **T-level rules need review** — accuracy below 80%\n"
    if metrics['o_accuracy'] < 0.8:
        report += "- **O-level rules need review** — accuracy below 80%\n"
    if not t_overrides and not o_overrides:
        report += "- Rules are well-calibrated — no systematic override patterns detected\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport: {args.output}")


if __name__ == "__main__":
    main()
