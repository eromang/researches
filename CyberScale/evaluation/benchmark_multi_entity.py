#!/usr/bin/env python3
"""Multi-entity aggregation benchmark for CyberScale Phase C.

Runs the aggregation → O-model → matrix pipeline on curated multi-entity
incident scenarios and validates:
- Aggregation T-level: 100% (deterministic)
- O-model accuracy: > 70%
- End-to-end matrix: > 70%

Usage:
    poetry run python evaluation/benchmark_multi_entity.py \
        --o-model data/models/operational \
        --dataset data/reference/curated_multi_entity_incidents.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from datetime import datetime
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.aggregation import aggregate_entity_notifications
from cyberscale.models.operational import OperationalClassifier
from cyberscale.matrix.dual_scale import classify_incident

print = partial(print, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-entity aggregation benchmark")
    parser.add_argument("--o-model", type=Path, default=Path("data/models/operational"))
    parser.add_argument("--dataset", type=Path, default=Path("data/reference/curated_multi_entity_incidents.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/multi_entity_benchmark.md"))
    parser.add_argument("--mc-passes", type=int, default=3)
    args = parser.parse_args()

    start = time.time()

    # Load scenarios
    with open(args.dataset, encoding="utf-8") as f:
        data = json.load(f)
    scenarios = data["incidents"]
    print(f"Loaded {len(scenarios)} multi-entity scenarios")

    # Load O-model
    print(f"Loading O-model from {args.o_model}...")
    o_model = OperationalClassifier(args.o_model, mc_passes=args.mc_passes)

    # Run benchmark
    t_correct = 0
    o_correct = 0
    matrix_correct = 0
    results = []

    for sc in scenarios:
        # Step 1: Aggregation (deterministic)
        agg = aggregate_entity_notifications(sc["entities"])

        # Step 2: O-model
        o_result = o_model.predict(
            description=sc["description"],
            sectors_affected=agg.sectors_affected,
            entity_relevance="essential",  # default for authority assessment
            ms_affected=agg.ms_affected,
            cross_border_pattern=agg.cross_border_pattern,
            capacity_exceeded=agg.capacity_exceeded,
            financial_impact=agg.financial_impact,
            safety_impact=agg.safety_impact,
            affected_persons_count=agg.affected_persons_count,
            affected_entities=agg.affected_entities,
        )

        # Step 3: Matrix
        matrix = classify_incident(agg.t_level, o_result.level)

        t_ok = agg.t_level == sc["expected_t"]
        o_ok = o_result.level == sc["expected_o"]
        matrix_ok = matrix.classification == sc["expected_classification"]

        if t_ok:
            t_correct += 1
        if o_ok:
            o_correct += 1
        if matrix_ok:
            matrix_correct += 1

        results.append({
            "id": sc["id"],
            "name": sc["name"],
            "entities": len(sc["entities"]),
            "expected_t": sc["expected_t"],
            "predicted_t": agg.t_level,
            "t_ok": t_ok,
            "expected_o": sc["expected_o"],
            "predicted_o": o_result.level,
            "o_ok": o_ok,
            "expected_cls": sc["expected_classification"],
            "predicted_cls": matrix.classification,
            "matrix_ok": matrix_ok,
        })

    n = len(scenarios)
    t_acc = t_correct / n
    o_acc = o_correct / n
    m_acc = matrix_correct / n
    elapsed = time.time() - start

    print(f"\nAggregation T-level: {t_acc*100:.1f}% ({t_correct}/{n})")
    print(f"O-model accuracy: {o_acc*100:.1f}% ({o_correct}/{n})")
    print(f"Matrix end-to-end: {m_acc*100:.1f}% ({matrix_correct}/{n})")

    # Generate report
    report = f"""# CyberScale Phase C — Multi-Entity Aggregation Benchmark

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Scenarios:** {n}
**O-model:** `{args.o_model}`
**Elapsed:** {elapsed:.1f}s

## Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Aggregation T-level | 100% | {t_acc*100:.1f}% | {"PASS" if t_acc == 1.0 else "FAIL"} |
| O-model accuracy | > 70% | {o_acc*100:.1f}% | {"PASS" if o_acc > 0.70 else "FAIL"} |
| Matrix end-to-end | > 70% | {m_acc*100:.1f}% | {"PASS" if m_acc > 0.70 else "FAIL"} |

## Per-scenario Results

| ID | Scenario | Entities | Expected T/O | Predicted T/O | Matrix | Pass |
|----|----------|----------|-------------|--------------|--------|------|
"""
    for r in results:
        status = "ok" if r["matrix_ok"] else "MISS"
        t_mark = "" if r["t_ok"] else " *"
        o_mark = "" if r["o_ok"] else " *"
        report += (
            f"| {r['id']} | {r['name'][:35]} | {r['entities']} | "
            f"{r['expected_t']}/{r['expected_o']} | "
            f"{r['predicted_t']}{t_mark}/{r['predicted_o']}{o_mark} | "
            f"{r['predicted_cls']} | {status} |\n"
        )

    # Failure analysis
    t_misses = [r for r in results if not r["t_ok"]]
    o_misses = [r for r in results if not r["o_ok"]]
    if t_misses:
        report += "\n## T-level Mismatches\n\n"
        for r in t_misses:
            report += f"- **{r['id']}** {r['name']}: expected {r['expected_t']}, got {r['predicted_t']}\n"
    if o_misses:
        report += "\n## O-level Mismatches\n\n"
        for r in o_misses:
            report += f"- **{r['id']}** {r['name']}: expected {r['expected_o']}, got {r['predicted_o']}\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport: {args.output}")

    if t_acc < 1.0 or o_acc <= 0.70 or m_acc <= 0.70:
        print("\nWARNING: One or more targets not met.")
        sys.exit(1)


if __name__ == "__main__":
    main()
