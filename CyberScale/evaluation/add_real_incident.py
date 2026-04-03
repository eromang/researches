#!/usr/bin/env python3
"""Add a real incident to the validation dataset.

Interactive script that prompts for incident data, runs it through the
CyberScale HCPN qualifier to show what the pipeline would produce, then
saves to data/reference/real_incident_validation.json.

Usage:
    poetry run python evaluation/add_real_incident.py
    poetry run python evaluation/add_real_incident.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

INCIDENTS_PATH = PROJECT_ROOT / "data" / "reference" / "real_incident_validation.json"

# Valid values for constrained fields
SECTORS = [
    "energy", "transport", "banking", "financial_market_infrastructures",
    "health", "drinking_water", "waste_water", "digital_infrastructure",
    "ict_service_management", "public_administration", "space",
    "postal", "waste_management", "manufacturing", "chemicals",
    "food", "digital_providers", "research",
]

SERVICE_IMPACTS = ["none", "partial", "degraded", "unavailable", "sustained"]
DATA_IMPACTS = ["none", "accessed", "exfiltrated", "compromised", "systemic"]
SAFETY_IMPACTS = ["none", "health_risk", "health_damage", "death"]
FINANCIAL_IMPACTS = ["none", "minor", "significant", "severe"]
THREAT_ACTOR_TYPES = ["state_actor", "terrorist_group", "hybrid_operation"]
SENSITIVE_DATA_TYPES = ["government_data", "industrial_secrets", "critical_strategic_data"]
COOPERATION_MODES = ["crise", "alerte_cerc", "permanent"]


def prompt(label: str, default: str = "", options: list[str] | None = None) -> str:
    hint = ""
    if options:
        hint = f" [{'/'.join(options)}]"
    if default:
        hint += f" (default: {default})"
    while True:
        val = input(f"  {label}{hint}: ").strip()
        if not val and default:
            return default
        if options and val and val not in options:
            print(f"    Invalid. Choose from: {', '.join(options)}")
            continue
        return val


def prompt_bool(label: str, default: bool | None = None) -> bool | None:
    hint = " [yes/no/unknown]"
    if default is not None:
        hint += f" (default: {'yes' if default else 'no'})"
    else:
        hint += " (default: unknown)"
    while True:
        val = input(f"  {label}{hint}: ").strip().lower()
        if not val:
            return default
        if val in ("yes", "y", "true", "1"):
            return True
        if val in ("no", "n", "false", "0"):
            return False
        if val in ("unknown", "u", "null", "none"):
            return None
        print("    Enter yes, no, or unknown")


def prompt_int(label: str, default: int = 0) -> int:
    while True:
        val = input(f"  {label} (default: {default}): ").strip()
        if not val:
            return default
        try:
            return int(val)
        except ValueError:
            print("    Enter a number")


def prompt_float(label: str, default: float = 0) -> float:
    while True:
        val = input(f"  {label} (default: {default}): ").strip()
        if not val:
            return default
        try:
            return float(val)
        except ValueError:
            print("    Enter a number")


def prompt_list(label: str, options: list[str]) -> list[str]:
    print(f"  {label} (comma-separated)")
    print(f"    Available: {', '.join(options)}")
    val = input(f"    > ").strip()
    if not val:
        return []
    items = [v.strip() for v in val.split(",")]
    invalid = [v for v in items if v not in options]
    if invalid:
        print(f"    Warning: unknown values: {invalid}")
    return items


def prompt_optional(label: str, options: list[str]) -> str | None:
    val = prompt(label, default="none", options=["none"] + options)
    return None if val == "none" else val


def main():
    parser = argparse.ArgumentParser(description="Add real incident to validation dataset")
    parser.add_argument("--dry-run", action="store_true", help="Show result without saving")
    args = parser.parse_args()

    print("=" * 70)
    print("  Add Real Incident to CyberScale Validation Dataset")
    print("=" * 70)

    # --- Basic info ---
    print("\n--- Incident Identity ---")
    incident_id = prompt("ID (e.g., RETEX-LU-2026-NAME)")
    name = prompt("Name")
    date = prompt("Date (YYYY-MM-DD)")
    country = prompt("Country (ISO 2-letter)", options=["LU", "NL", "DE", "FR", "BE", "PL", "EU"])
    source = prompt("Vault source path (relative to vault root)", default="")

    # --- Incident data ---
    print("\n--- Incident Parameters ---")
    description = prompt("Description (1-2 sentences)")
    sectors_affected = prompt_list("Sectors affected", SECTORS)

    print(f"  Entity types (comma-separated, from nis2_entity_types.json)")
    entity_types_str = input(f"    > ").strip()
    entity_types = [v.strip() for v in entity_types_str.split(",")] if entity_types_str else []

    ms_established = prompt("MS established", default=country)
    ms_affected_str = prompt("MS affected (comma-separated)", default=country)
    ms_affected = [v.strip() for v in ms_affected_str.split(",")]

    service_impact = prompt("Service impact", default="none", options=SERVICE_IMPACTS)
    data_impact = prompt("Data impact", default="none", options=DATA_IMPACTS)
    safety_impact = prompt("Safety impact", default="none", options=SAFETY_IMPACTS)
    financial_impact = prompt("Financial impact", default="none", options=FINANCIAL_IMPACTS)
    affected_persons_count = prompt_int("Affected persons count")
    impact_duration_hours = prompt_float("Impact duration (hours)")
    cross_border = prompt_bool("Cross-border impact", default=False)
    capacity_exceeded = prompt_bool("Capacity exceeded", default=False)
    suspected_malicious = prompt_bool("Suspected malicious", default=False)
    threat_actor_type = prompt_optional("Threat actor type", THREAT_ACTOR_TYPES)
    sensitive_data_type = prompt_optional("Sensitive data type", SENSITIVE_DATA_TYPES)

    # --- Actual outcomes ---
    print("\n--- Actual Outcomes (what really happened) ---")
    crisis_activated = prompt_bool("Crisis management activated", default=False)
    crisis_mechanism = prompt("Crisis mechanism (if activated)", default="") or None
    pggccn_mode = prompt_optional("PGGCCN mode (if activated)", COOPERATION_MODES)
    significant_nis2 = prompt_bool("Significant under NIS2", default=None)

    print("  Notification frameworks (comma-separated: NIS2, NIS1, DORA, GDPR, etc.)")
    nf_str = input("    > ").strip()
    notification_frameworks = [v.strip() for v in nf_str.split(",")] if nf_str else []

    early_warning_sent = prompt_bool("Early warning sent", default=None)
    notable = prompt("Notable aspects", default="")

    # --- HCPN expected values ---
    print("\n--- HCPN Crisis Qualification (expected CyberScale output) ---")

    is_lu_applicable = country == "LU" or any("LU" in ms for ms in ms_affected)

    if not is_lu_applicable:
        print("  Non-LU incident — HCPN not applicable. Marking as skip.")
        hcpn_expected = {"not_applicable": True, "comment": f"{country} incident — HCPN does not apply"}
    else:
        print("  Authority judgment inputs (what an analyst would provide):")
        coordination_required = prompt_bool("Coordination required")
        urgent_decisions_required = prompt_bool("Urgent decisions required")
        prejudice_actual = prompt_bool("Prejudice actual (vs potential)", default=False)

        # Run through CyberScale to show prediction
        from cyberscale.national.lu_crisis import qualify_hcpn_incident

        result = qualify_hcpn_incident(
            sectors_affected=sectors_affected,
            entity_types=entity_types,
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border or False,
            capacity_exceeded=capacity_exceeded or False,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
            suspected_malicious=suspected_malicious or False,
            coordination_required=coordination_required,
            urgent_decisions_required=urgent_decisions_required,
            prejudice_actual=prejudice_actual or False,
        )

        print(f"\n  --- CyberScale HCPN Result ---")
        print(f"  Qualifies:      {result.qualifies}")
        print(f"  Level:          {result.qualification_level}")
        print(f"  Mode:           {result.cooperation_mode}")
        print(f"  Fast-tracked:   {result.fast_tracked}")
        print(f"  Consultation:   {result.recommend_consultation}")
        for cname, cr in result.criteria.items():
            print(f"  {cname}: {cr.status}")
            for d in cr.details:
                print(f"    {d[:80]}")

        if crisis_activated is not None:
            if result.qualifies == crisis_activated:
                print(f"\n  CONCORDANCE with actual outcome")
            else:
                print(f"\n  DIVERGENCE: CyberScale={result.qualifies}, actual crisis={crisis_activated}")

        print("\n  Accept these as expected values? (or override)")
        accept = prompt("Accept CyberScale output as expected", default="yes", options=["yes", "no"])

        if accept == "yes":
            expected_qualifies = result.qualifies
            expected_level = result.qualification_level
            expected_mode = result.cooperation_mode
        else:
            expected_qualifies = prompt_bool("Expected qualifies", default=result.qualifies)
            expected_level = prompt("Expected level", default=result.qualification_level)
            expected_mode = prompt("Expected mode", default=result.cooperation_mode, options=COOPERATION_MODES + ["permanent"])

        hcpn_expected = {
            "sectors_affected": sectors_affected,
            "entity_types": entity_types,
            "safety_impact": safety_impact,
            "service_impact": service_impact,
            "data_impact": data_impact,
            "financial_impact": financial_impact,
            "affected_persons_count": affected_persons_count,
            "cross_border": cross_border or False,
            "capacity_exceeded": capacity_exceeded or False,
            "suspected_malicious": suspected_malicious or False,
            "threat_actor_type": threat_actor_type,
            "sensitive_data_type": sensitive_data_type,
            "coordination_required": coordination_required,
            "urgent_decisions_required": urgent_decisions_required,
            "prejudice_actual": prejudice_actual or False,
            "expected_qualifies": expected_qualifies,
            "expected_level": expected_level,
            "expected_mode": expected_mode,
        }

        if result.recommend_consultation:
            hcpn_expected["expected_recommend_consultation"] = True

    # --- Notes ---
    print("\n--- Notes ---")
    notes = prompt("Analyst notes (mapping decisions, ambiguities)", default="")

    # --- Build the incident record ---
    record = {
        "id": incident_id,
        "name": name,
        "date": date,
        "country": country,
        "source": source,
        "incident_data": {
            "description": description,
            "sectors_affected": sectors_affected,
            "entity_types": entity_types,
            "ms_established": ms_established,
            "ms_affected": ms_affected,
            "service_impact": service_impact,
            "data_impact": data_impact,
            "safety_impact": safety_impact,
            "financial_impact": financial_impact,
            "affected_persons_count": affected_persons_count,
            "impact_duration_hours": impact_duration_hours,
            "cross_border": cross_border or False,
            "capacity_exceeded": capacity_exceeded or False,
            "suspected_malicious": suspected_malicious or False,
            "threat_actor_type": threat_actor_type,
            "sensitive_data_type": sensitive_data_type,
        },
        "actual_outcomes": {
            "crisis_activated": crisis_activated,
            "crisis_mechanism": crisis_mechanism,
            "pggccn_mode": pggccn_mode,
            "significant_nis2": significant_nis2,
            "notification_frameworks": notification_frameworks,
            "early_warning_sent": early_warning_sent,
            "notable": notable,
        },
        "expected_cyberscale": {
            "entity_significance": {
                "comment": "To be validated",
                "expected_significant": significant_nis2,
            },
            "hcpn_crisis": hcpn_expected,
        },
        "notes": notes,
    }

    # --- Preview ---
    print(f"\n{'='*70}")
    print("  RECORD PREVIEW")
    print(f"{'='*70}")
    print(json.dumps(record, indent=2, ensure_ascii=False))

    if args.dry_run:
        print("\n  [DRY RUN — not saved]")
        return

    # --- Save ---
    confirm = prompt("\nSave to validation dataset?", default="yes", options=["yes", "no"])
    if confirm != "yes":
        print("  Cancelled.")
        return

    with open(INCIDENTS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # Check for duplicate ID
    existing_ids = {i["id"] for i in data["incidents"]}
    if incident_id in existing_ids:
        print(f"  ERROR: ID '{incident_id}' already exists. Use a different ID.")
        return

    data["incidents"].append(record)

    with open(INCIDENTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\n  Saved to {INCIDENTS_PATH}")
    print(f"  Total incidents: {len(data['incidents'])}")
    print(f"\n  Validate with: poetry run python evaluation/validate_real_incidents.py --incident {incident_id} -v")


if __name__ == "__main__":
    main()
