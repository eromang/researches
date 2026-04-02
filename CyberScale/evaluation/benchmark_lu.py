#!/usr/bin/env python3
"""Benchmark CyberScale v7 Luxembourg national threshold assessment.

Runs 20 curated LU scenarios through the three-tier router and validates:
1. Correct routing (IR / national_lu / nis2_ml)
2. Correct significance determination
3. Correct triggered criteria
4. Correct ILR reference

All thresholds are deterministic — expected accuracy is 100%.

Usage:
    poetry run python evaluation/benchmark_lu.py \
        --dataset data/reference/curated_lu_incidents.json \
        --output evaluation/lu_benchmark.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from functools import partial
from pathlib import Path
from unittest.mock import MagicMock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.contextual import ContextualResult
from cyberscale.tools.entity_incident import _assess_entity_incident

print = partial(print, flush=True)


def load_scenarios(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["scenarios"]


def run_scenario(scenario: dict) -> dict:
    """Run a single scenario through the three-tier router."""
    mock_clf = MagicMock()
    mock_clf.predict.return_value = ContextualResult(
        severity="High", confidence="high",
        key_factors=[f"{scenario['sector']} sector"],
    )

    kwargs = {
        "description": scenario["description"],
        "sector": scenario["sector"],
        "entity_type": scenario["entity_type"],
        "ms_established": scenario.get("ms_established", "EU"),
        "service_impact": scenario.get("service_impact", "none"),
        "data_impact": scenario.get("data_impact", "none"),
        "financial_impact": scenario.get("financial_impact", "none"),
        "safety_impact": scenario.get("safety_impact", "none"),
        "affected_persons_count": scenario.get("affected_persons_count", 0),
        "suspected_malicious": scenario.get("suspected_malicious", False),
        "impact_duration_hours": scenario.get("impact_duration_hours", 0),
        "sector_specific": scenario.get("sector_specific"),
    }

    result = _assess_entity_incident(mock_clf, **kwargs)
    return result


def evaluate_scenario(scenario: dict, result: dict) -> dict:
    """Evaluate a scenario result against expected outcomes."""
    checks = {}

    # Check routing model
    expected_model = scenario["expected_model"]
    actual_model = result["significance"]["model"]
    checks["routing"] = actual_model == expected_model

    # Check significance
    if "expected_significant" in scenario:
        actual_sig = result["significance"]["significant_incident"]
        checks["significance"] = actual_sig == scenario["expected_significant"]
    elif "expected_significant_type" in scenario:
        actual_sig = result["significance"]["significant_incident"]
        checks["significance"] = isinstance(actual_sig, str) == (scenario["expected_significant_type"] == "string")

    # Check triggered criteria
    if "expected_criteria_contains" in scenario:
        triggered = result["significance"].get("triggered_criteria", [])
        common = result["significance"].get("common_criteria_met", [])
        all_criteria = triggered + common
        keyword = scenario["expected_criteria_contains"]
        checks["criteria"] = any(keyword in c for c in all_criteria)

    # Check ILR reference
    if "expected_ilr_reference" in scenario:
        actual_ref = result["significance"].get("ilr_reference", "")
        checks["ilr_reference"] = actual_ref == scenario["expected_ilr_reference"]

    return {
        "id": scenario["id"],
        "name": scenario["name"],
        "all_pass": all(checks.values()),
        "checks": checks,
        "expected_model": expected_model,
        "actual_model": actual_model,
    }


def generate_report(
    dataset_path: str,
    evaluations: list[dict],
    elapsed_seconds: float,
) -> str:
    total = len(evaluations)
    passed = sum(1 for e in evaluations if e["all_pass"])
    failed = total - passed

    # Count by routing tier
    routing_counts = {}
    routing_correct = {}
    for e in evaluations:
        model = e["expected_model"]
        routing_counts[model] = routing_counts.get(model, 0) + 1
        if e["checks"].get("routing", False):
            routing_correct[model] = routing_correct.get(model, 0) + 1

    report = f"""# CyberScale v7 — Luxembourg National Threshold Benchmark

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Dataset:** `{dataset_path}`
**Scenarios:** {total}
**Elapsed:** {elapsed_seconds:.1f}s

## Summary

| Metric | Result | Target |
|--------|--------|--------|
| Overall accuracy | {passed}/{total} ({passed/total*100:.0f}%) | 100% |
| Routing correctness | {sum(routing_correct.values())}/{total} | 100% |
| Significance correctness | {sum(1 for e in evaluations if e['checks'].get('significance', True))}/{total} | 100% |

## Routing Tier Distribution

| Tier | Count | Correct |
|------|-------|---------|
"""
    for model in sorted(routing_counts.keys()):
        count = routing_counts[model]
        correct = routing_correct.get(model, 0)
        report += f"| {model} | {count} | {correct}/{count} |\n"

    report += """
## Per-scenario Results

| ID | Scenario | Expected Model | Actual Model | Pass |
|----|----------|---------------|-------------|------|
"""
    for e in evaluations:
        status = "PASS" if e["all_pass"] else "**FAIL**"
        report += f"| {e['id']} | {e['name'][:50]} | {e['expected_model']} | {e['actual_model']} | {status} |\n"

    # Failures detail
    failures = [e for e in evaluations if not e["all_pass"]]
    if failures:
        report += "\n## Failures\n\n"
        for e in failures:
            report += f"### {e['id']} — {e['name']}\n\n"
            for check_name, check_pass in e["checks"].items():
                status = "PASS" if check_pass else "**FAIL**"
                report += f"- {check_name}: {status}\n"
            report += "\n"
    else:
        report += "\n## All scenarios passed.\n"

    return report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark v7 Luxembourg national thresholds"
    )
    parser.add_argument(
        "--dataset", type=Path,
        default=Path("data/reference/curated_lu_incidents.json"),
    )
    parser.add_argument(
        "--output", type=Path,
        default=Path("evaluation/lu_benchmark.md"),
    )
    args = parser.parse_args()

    start = time.time()

    print(f"Loading scenarios from {args.dataset}...")
    scenarios = load_scenarios(args.dataset)
    print(f"Loaded {len(scenarios)} scenarios")

    evaluations = []
    for scenario in scenarios:
        print(f"  {scenario['id']}: {scenario['name'][:60]}...", end=" ")
        result = run_scenario(scenario)
        evaluation = evaluate_scenario(scenario, result)
        evaluations.append(evaluation)
        status = "PASS" if evaluation["all_pass"] else "FAIL"
        print(status)

    elapsed = time.time() - start

    passed = sum(1 for e in evaluations if e["all_pass"])
    total = len(evaluations)
    print(f"\nResults: {passed}/{total} passed ({passed/total*100:.0f}%)")

    report = generate_report(
        dataset_path=str(args.dataset),
        evaluations=evaluations,
        elapsed_seconds=elapsed,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"Report written to {args.output}")

    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
