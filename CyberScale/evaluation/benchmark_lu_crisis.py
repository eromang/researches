"""Benchmark for HCPN national crisis qualification scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCENARIOS_PATH = (
    Path(__file__).parent.parent / "data" / "reference" / "curated_lu_crisis_scenarios.json"
)


def run_benchmark() -> tuple[int, int, list[str]]:
    """Run all curated HCPN scenarios, return (passed, total, failures)."""
    from cyberscale.national.lu_crisis import qualify_hcpn_incident, qualify_hcpn_threat

    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    passed = 0
    failures: list[str] = []

    for s in scenarios:
        sid = s["id"]

        if s["event_type"] == "incident":
            result = qualify_hcpn_incident(
                sectors_affected=s["sectors_affected"],
                entity_types=s.get("entity_types", []),
                safety_impact=s.get("safety_impact", "none"),
                service_impact=s.get("service_impact", "none"),
                data_impact=s.get("data_impact", "none"),
                financial_impact=s.get("financial_impact", "none"),
                affected_persons_count=s.get("affected_persons_count", 0),
                cross_border=s.get("cross_border", False),
                capacity_exceeded=s.get("capacity_exceeded", False),
                threat_actor_type=s.get("threat_actor_type"),
                sensitive_data_type=s.get("sensitive_data_type"),
                suspected_malicious=s.get("suspected_malicious", False),
                coordination_required=s.get("coordination_required"),
                urgent_decisions_required=s.get("urgent_decisions_required"),
                prejudice_actual=s.get("prejudice_actual", False),
            )
        elif s["event_type"] == "threat":
            result = qualify_hcpn_threat(
                sectors_affected=s["sectors_affected"],
                entity_types=s.get("entity_types", []),
                threat_probability=s["threat_probability"],
                safety_impact=s.get("safety_impact", "none"),
                service_impact=s.get("service_impact", "none"),
                data_impact=s.get("data_impact", "none"),
                financial_impact=s.get("financial_impact", "none"),
                affected_persons_count=s.get("affected_persons_count", 0),
                cross_border=s.get("cross_border", False),
                capacity_exceeded=s.get("capacity_exceeded", False),
                threat_actor_type=s.get("threat_actor_type"),
                sensitive_data_type=s.get("sensitive_data_type"),
                coordination_required=s.get("coordination_required"),
                urgent_decisions_required=s.get("urgent_decisions_required"),
                prejudice_actual=s.get("prejudice_actual", False),
            )
        else:
            failures.append(f"{sid}: unknown event_type '{s['event_type']}'")
            continue

        ok = True
        errs: list[str] = []

        if result.qualifies != s["expected_qualifies"]:
            errs.append(f"qualifies: got {result.qualifies}, expected {s['expected_qualifies']}")
            ok = False
        if result.qualification_level != s["expected_level"]:
            errs.append(f"level: got {result.qualification_level}, expected {s['expected_level']}")
            ok = False
        if result.cooperation_mode != s["expected_mode"]:
            errs.append(f"mode: got {result.cooperation_mode}, expected {s['expected_mode']}")
            ok = False

        if "expected_fast_tracked" in s and result.fast_tracked != s["expected_fast_tracked"]:
            errs.append(f"fast_tracked: got {result.fast_tracked}, expected {s['expected_fast_tracked']}")
            ok = False

        if "expected_recommend_consultation" in s and result.recommend_consultation != s["expected_recommend_consultation"]:
            errs.append(f"recommend_consultation: got {result.recommend_consultation}, expected {s['expected_recommend_consultation']}")
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
    print("HCPN National Crisis Qualification Benchmark")
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
