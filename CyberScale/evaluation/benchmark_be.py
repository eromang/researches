"""Benchmark for Belgium national threshold scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SCENARIOS_PATH = PROJECT_ROOT / "data" / "reference" / "curated_be_incidents.json"


def run_benchmark() -> tuple[int, int, list[str]]:
    from cyberscale.national.be import assess_be_significance, is_be_covered
    from cyberscale.models.contextual_ir import is_ir_entity

    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    passed = 0
    failures: list[str] = []

    for s in scenarios:
        sid = s["id"]
        entity_type = s["entity_type"]
        sector = s["sector"]

        # Determine expected routing
        if is_ir_entity(entity_type):
            actual_model = "ir_thresholds"
            # For IR entities, we just check routing — not BE significance
            if s["expected_model"] == "ir_thresholds":
                passed += 1
                print(f"  PASS {sid}: {s['name']} (routed to IR)")
                continue
            else:
                failures.append(f"{sid}: expected model {s['expected_model']} but entity is IR")
                print(f"  FAIL {sid}: {s['name']} — IR entity mismatch")
                continue

        # BE assessment
        result = assess_be_significance(
            sector=sector,
            entity_type=entity_type,
            service_impact=s.get("service_impact", "none"),
            data_impact=s.get("data_impact", "none"),
            financial_impact=s.get("financial_impact", "none"),
            safety_impact=s.get("safety_impact", "none"),
            affected_persons_count=s.get("affected_persons_count", 0),
            affected_persons_pct=s.get("affected_persons_pct", 0.0),
            impact_duration_hours=s.get("impact_duration_hours", 0),
            suspected_malicious=s.get("suspected_malicious", False),
            cross_border=s.get("cross_border", False),
            trade_secret_exfiltration=s.get("trade_secret_exfiltration", False),
        )

        ok = True
        errs: list[str] = []

        if result.significant_incident != s["expected_significant"]:
            errs.append(f"significant: got {result.significant_incident}, expected {s['expected_significant']}")
            ok = False

        if "expected_criteria_contains" in s and result.significant_incident:
            needle = s["expected_criteria_contains"].lower()
            if not any(needle in c.lower() for c in result.triggered_criteria):
                errs.append(f"criteria missing '{needle}' in {result.triggered_criteria}")
                ok = False

        if ok:
            passed += 1
            print(f"  PASS {sid}: {s['name']}")
        else:
            failures.append(f"{sid}: {'; '.join(errs)}")
            print(f"  FAIL {sid}: {s['name']} -- {'; '.join(errs)}")

    return passed, len(scenarios), failures


def main():
    print("=" * 60)
    print("Belgium National Threshold Benchmark")
    print("=" * 60)

    passed, total, failures = run_benchmark()

    print(f"\n{'=' * 60}")
    print(f"Result: {passed}/{total} scenarios correct")
    if failures:
        print(f"\nFailures:")
        for f in failures:
            print(f"  - {f}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
