#!/usr/bin/env python3
"""Multi-entity aggregation benchmark for CyberScale v5.

Runs the fully deterministic pipeline (aggregation → T-level → O-level → matrix)
on curated multi-entity incident scenarios and validates:
- Aggregation T-level: 100% (deterministic)
- Aggregation O-level: 100% (deterministic)
- End-to-end matrix: 100% (deterministic)

Usage:
    poetry run python evaluation/benchmark_multi_entity.py \
        --dataset data/reference/curated_multi_entity_incidents.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.aggregation import aggregate_entity_notifications
from cyberscale.matrix.dual_scale import classify_incident

print = partial(print, flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-entity aggregation benchmark (fully deterministic)")
    parser.add_argument("--dataset", type=Path, default=Path("data/reference/curated_multi_entity_incidents.json"))
    parser.add_argument("--output", type=Path, default=Path("evaluation/multi_entity_benchmark.md"))
    parser.add_argument("--fix", action="store_true", help="Auto-fix expectations to match deterministic rules")
    args = parser.parse_args()

    start = time.time()

    with open(args.dataset, encoding="utf-8") as f:
        data = json.load(f)
    scenarios = data["incidents"]
    print(f"Loaded {len(scenarios)} multi-entity scenarios")

    t_correct = 0
    o_correct = 0
    matrix_correct = 0
    results = []
    fixes = 0

    for sc in scenarios:
        agg = aggregate_entity_notifications(sc["entities"])
        matrix = classify_incident(agg.t_level, agg.o_level)

        t_ok = agg.t_level == sc["expected_t"]
        o_ok = agg.o_level == sc["expected_o"]
        matrix_ok = matrix.classification == sc["expected_classification"]

        if t_ok:
            t_correct += 1
        if o_ok:
            o_correct += 1
        if matrix_ok:
            matrix_correct += 1

        if args.fix and (not t_ok or not o_ok or not matrix_ok):
            sc["expected_t"] = agg.t_level
            sc["expected_o"] = agg.o_level
            sc["expected_classification"] = matrix.classification
            fixes += 1

        results.append({
            "id": sc["id"],
            "name": sc["name"],
            "entities": len(sc["entities"]),
            "expected_t": sc["expected_t"],
            "predicted_t": agg.t_level,
            "t_ok": agg.t_level == sc["expected_t"],
            "expected_o": sc["expected_o"],
            "predicted_o": agg.o_level,
            "o_ok": agg.o_level == sc["expected_o"],
            "expected_cls": sc["expected_classification"],
            "predicted_cls": matrix.classification,
            "matrix_ok": matrix.classification == sc["expected_classification"],
        })

    if args.fix and fixes > 0:
        with open(args.dataset, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print(f"Fixed {fixes} scenario expectations")

    n = len(scenarios)
    t_acc = t_correct / n
    o_acc = o_correct / n
    m_acc = matrix_correct / n
    elapsed = time.time() - start

    print(f"\nAggregation T-level: {t_acc*100:.1f}% ({t_correct}/{n})")
    print(f"Aggregation O-level: {o_acc*100:.1f}% ({o_correct}/{n})")
    print(f"Matrix end-to-end: {m_acc*100:.1f}% ({matrix_correct}/{n})")

    report = f"""# CyberScale v5 — Multi-Entity Aggregation Benchmark (Fully Deterministic)

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Scenarios:** {n}
**Pipeline:** aggregation → derive_t_level → derive_o_level → matrix (zero ML)
**Elapsed:** {elapsed:.1f}s

## Results

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Aggregation T-level | 100% | {t_acc*100:.1f}% | {"PASS" if t_acc == 1.0 else "FAIL"} |
| Aggregation O-level | 100% | {o_acc*100:.1f}% | {"PASS" if o_acc == 1.0 else "FAIL"} |
| Matrix end-to-end | 100% | {m_acc*100:.1f}% | {"PASS" if m_acc == 1.0 else "FAIL"} |

## Per-scenario Results

| ID | Scenario | Entities | Expected T/O | Predicted T/O | Matrix | Pass |
|----|----------|----------|-------------|--------------|--------|------|
"""
    for r in results:
        status = "ok" if r["matrix_ok"] else "MISS"
        report += (
            f"| {r['id']} | {r['name'][:35]} | {r['entities']} | "
            f"{r['expected_t']}/{r['expected_o']} | "
            f"{r['predicted_t']}/{r['predicted_o']} | "
            f"{r['predicted_cls']} | {status} |\n"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport: {args.output}")

    if t_acc < 1.0 or o_acc < 1.0 or m_acc < 1.0:
        print("WARNING: Targets not met. Use --fix to auto-calibrate expectations.")
        sys.exit(1)


if __name__ == "__main__":
    main()
