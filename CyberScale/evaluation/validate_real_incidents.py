#!/usr/bin/env python3
"""Validate CyberScale pipeline against real incidents from RETEX analyses.

Runs real incident data through the HCPN crisis qualification layer and
compares against documented actual outcomes. Extensible — add new incidents
to data/reference/real_incident_validation.json.

Validation layers:
1. HCPN crisis qualification (v8) — for LU-scoped incidents
2. Entity significance routing check — which model tier was used

Usage:
    poetry run python evaluation/validate_real_incidents.py
    poetry run python evaluation/validate_real_incidents.py --verbose
    poetry run python evaluation/validate_real_incidents.py --incident RETEX-LU-2025-POST
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

INCIDENTS_PATH = PROJECT_ROOT / "data" / "reference" / "real_incident_validation.json"


def load_incidents(incident_filter: str | None = None) -> list[dict]:
    with open(INCIDENTS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    incidents = data["incidents"]
    if incident_filter:
        incidents = [i for i in incidents if i["id"] == incident_filter]
    return incidents


# ---------------------------------------------------------------------------
# HCPN Crisis Qualification Validation
# ---------------------------------------------------------------------------


def validate_hcpn(incident: dict, verbose: bool = False) -> tuple[bool, list[str]]:
    """Validate HCPN crisis qualification against actual outcome."""
    from cyberscale.national.lu_crisis import qualify_hcpn_incident

    hcpn_expected = incident["expected_cyberscale"].get("hcpn_crisis", {})

    # Skip non-applicable incidents (non-LU)
    if hcpn_expected.get("not_applicable"):
        return True, [f"SKIP (HCPN not applicable — {incident['country']} incident)"]

    result = qualify_hcpn_incident(
        sectors_affected=hcpn_expected["sectors_affected"],
        entity_types=hcpn_expected.get("entity_types", []),
        safety_impact=hcpn_expected.get("safety_impact", "none"),
        service_impact=hcpn_expected.get("service_impact", "none"),
        data_impact=hcpn_expected.get("data_impact", "none"),
        financial_impact=hcpn_expected.get("financial_impact", "none"),
        affected_persons_count=hcpn_expected.get("affected_persons_count", 0),
        cross_border=hcpn_expected.get("cross_border", False),
        capacity_exceeded=hcpn_expected.get("capacity_exceeded", False),
        threat_actor_type=hcpn_expected.get("threat_actor_type"),
        sensitive_data_type=hcpn_expected.get("sensitive_data_type"),
        suspected_malicious=hcpn_expected.get("suspected_malicious", False),
        coordination_required=hcpn_expected.get("coordination_required"),
        urgent_decisions_required=hcpn_expected.get("urgent_decisions_required"),
        prejudice_actual=hcpn_expected.get("prejudice_actual", False),
    )

    errors: list[str] = []
    details: list[str] = []

    # Check qualifies
    exp_qualifies = hcpn_expected["expected_qualifies"]
    if result.qualifies != exp_qualifies:
        errors.append(f"qualifies: got {result.qualifies}, expected {exp_qualifies}")

    # Check level
    exp_level = hcpn_expected["expected_level"]
    if result.qualification_level != exp_level:
        errors.append(f"level: got {result.qualification_level}, expected {exp_level}")

    # Check mode
    exp_mode = hcpn_expected["expected_mode"]
    if result.cooperation_mode != exp_mode:
        errors.append(f"mode: got {result.cooperation_mode}, expected {exp_mode}")

    # Optional checks
    if "expected_fast_tracked" in hcpn_expected:
        if result.fast_tracked != hcpn_expected["expected_fast_tracked"]:
            errors.append(f"fast_tracked: got {result.fast_tracked}, expected {hcpn_expected['expected_fast_tracked']}")

    if "expected_recommend_consultation" in hcpn_expected:
        if result.recommend_consultation != hcpn_expected["expected_recommend_consultation"]:
            errors.append(f"recommend_consultation: got {result.recommend_consultation}, expected {hcpn_expected['expected_recommend_consultation']}")

    # Compare with actual outcome
    actual = incident["actual_outcomes"]
    if verbose:
        details.append(f"  CyberScale:  qualifies={result.qualifies}, level={result.qualification_level}, mode={result.cooperation_mode}")
        details.append(f"  Actual:      crisis_activated={actual['crisis_activated']}, pggccn_mode={actual.get('pggccn_mode')}")
        details.append(f"  Fast-track:  {result.fast_tracked}")
        details.append(f"  Consult:     {result.recommend_consultation}")

        # Show criteria
        for cname, cr in result.criteria.items():
            details.append(f"  {cname}: {cr.status}")
            for d in cr.details:
                details.append(f"    {d[:80]}")

        # Concordance with reality
        actual_crisis = actual["crisis_activated"]
        if result.qualifies == actual_crisis:
            details.append(f"  CONCORDANCE: CyberScale agrees with actual outcome")
        elif result.qualifies and not actual_crisis:
            details.append(f"  DIVERGENCE:  CyberScale says qualifies, but no crisis was activated in reality")
            details.append(f"    Possible reasons: authority judgment inputs may differ, or crisis was borderline")
        elif not result.qualifies and actual_crisis:
            details.append(f"  DIVERGENCE:  CyberScale says does not qualify, but crisis WAS activated in reality")
            details.append(f"    Possible reasons: authority used different criteria, or CyberScale inputs incomplete")

        if result.recommend_consultation:
            details.append(f"  CONSULTATION RECOMMENDED:")
            for reason in result.consultation_reasons:
                details.append(f"    - {reason[:80]}")

    ok = len(errors) == 0
    return ok, errors + details


# ---------------------------------------------------------------------------
# Main runner
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Validate CyberScale against real incidents")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--incident", "-i", type=str, help="Validate single incident by ID")
    args = parser.parse_args()

    incidents = load_incidents(args.incident)
    if not incidents:
        print(f"No incidents found" + (f" matching '{args.incident}'" if args.incident else ""))
        sys.exit(1)

    print("=" * 70)
    print("  CyberScale Real Incident Validation")
    print(f"  Dataset: {len(incidents)} incidents from RETEX analyses")
    print("=" * 70)

    passed = 0
    failed = 0
    skipped = 0
    divergences: list[str] = []

    for incident in incidents:
        iid = incident["id"]
        name = incident["name"]
        country = incident["country"]
        actual = incident["actual_outcomes"]

        print(f"\n--- {iid}: {name} ({country}, {incident['date']}) ---")

        # HCPN validation
        ok, messages = validate_hcpn(incident, verbose=args.verbose)

        if messages and messages[0].startswith("SKIP"):
            print(f"  HCPN: {messages[0]}")
            skipped += 1
        elif ok:
            print(f"  HCPN: PASS")
            passed += 1
        else:
            print(f"  HCPN: FAIL")
            failed += 1

        for msg in messages:
            if not msg.startswith("SKIP"):
                print(f"  {msg}" if not msg.startswith("  ") else msg)

        # Always show concordance summary
        hcpn_expected = incident["expected_cyberscale"].get("hcpn_crisis", {})
        if not hcpn_expected.get("not_applicable"):
            exp_qualifies = hcpn_expected["expected_qualifies"]
            actual_crisis = actual["crisis_activated"]
            if exp_qualifies != actual_crisis:
                reason = incident.get("notes", "")
                divergences.append(f"{iid}: expected={exp_qualifies}, actual_crisis={actual_crisis}")
                if not args.verbose:
                    print(f"  Note: CyberScale expectation ({exp_qualifies}) differs from actual crisis activation ({actual_crisis})")

    # Summary
    print(f"\n{'='*70}")
    print(f"  RESULTS: {passed} passed, {failed} failed, {skipped} skipped (non-LU)")
    print(f"  Total incidents: {len(incidents)}")

    if divergences:
        print(f"\n  DIVERGENCES (expected vs actual crisis activation):")
        for d in divergences:
            print(f"    {d}")
        print(f"\n  Divergences are expected — CyberScale inputs are analyst-provided")
        print(f"  approximations of what the authority judgment would have been.")

    if failed:
        print(f"\n  {failed} FAILURES — CyberScale output doesn't match expected values")
        sys.exit(1)
    else:
        print(f"\n  All validations passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
