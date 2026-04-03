#!/usr/bin/env python3
"""CyberScale v8 — End-to-end demo: HCPN national crisis qualification.

Exercises the HCPN crisis qualification layer (Cadre national v1.0) with
all key scenarios. This layer operates ABOVE entity significance — it
determines whether an event triggers the PGGCCN national crisis plan.

Scenarios:
1. Energy grid attack — national major incident (Crise)
2. Hospital ransomware — national major incident (Alerte/CERC)
3. Cross-border transport + energy — large-scale (Crise)
4. Malicious DNS access — fast-track (C2 bypassed)
5. Government data exfiltration — national security trigger
6. Degraded water supply — undetermined, recommend consultation
7. Food sector — non-essential, does not qualify
8. Energy incident handled locally — no coordination, does not qualify
9. Capacity exceeded — large-scale cybersecurity incident
10. Imminent APT threat — national major cyber threat (Alerte/CERC)
11. Low probability threat — does not qualify

Usage:
    poetry run python evaluation/e2e_v8_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.national.lu_crisis import qualify_hcpn_incident, qualify_hcpn_threat


def section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def show_result(name: str, result) -> None:
    d = result.to_dict()
    qualifies = d["qualifies"]
    level = d["qualification_level"]
    mode = d["cooperation_mode"]
    fast = d["fast_tracked"]
    consult = d["recommend_consultation"]

    status = "QUALIFIES" if qualifies else "DOES NOT QUALIFY"
    print(f"  {name}")
    print(f"    {status}")
    print(f"    Level:       {level}")
    print(f"    Mode:        {mode}")
    if fast:
        print(f"    Fast-track:  YES (Criterion 2 bypassed)")
    if consult:
        print(f"    RECOMMEND CONSULTATION:")
        for reason in d["consultation_reasons"]:
            print(f"      - {reason}")

    # Show criteria summary
    for cname, cdata in d["criteria"].items():
        status_str = cdata["status"].upper()
        detail = cdata["details"][0] if cdata["details"] else ""
        if len(detail) > 70:
            detail = detail[:67] + "..."
        print(f"    {cname}: {status_str} — {detail}")
    print()


def main():
    print("=" * 70)
    print("  CyberScale v8 — HCPN National Crisis Qualification Demo")
    print("  Cadre national de qualification (HCPN v1.0, 22.08.2025)")
    print("=" * 70)

    # ----------------------------------------------------------------
    section("INCIDENT SCENARIOS")
    # ----------------------------------------------------------------

    # 1. Energy grid attack — national major incident (Crise)
    # Note: suspected_malicious=False to show normal C2 path (not fast-track)
    show_result(
        "1. Energy grid attack — state actor, deaths",
        qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=["electricity_undertaking"],
            safety_impact="death",
            service_impact="unavailable",
            threat_actor_type="state_actor",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # 2. Hospital ransomware — Alerte/CERC (potential prejudice)
    # Note: no suspected_malicious to show C2 health_damage sub-criterion
    show_result(
        "2. Hospital ransomware — potential prejudice",
        qualify_hcpn_incident(
            sectors_affected=["health"],
            entity_types=["healthcare_provider"],
            safety_impact="health_damage",
            service_impact="unavailable",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        ),
    )

    # 3. Cross-border — large-scale cybersecurity incident
    show_result(
        "3. Cross-border transport + energy — large-scale",
        qualify_hcpn_incident(
            sectors_affected=["transport", "energy"],
            entity_types=["railway_undertaking", "electricity_undertaking"],
            safety_impact="death",
            service_impact="unavailable",
            cross_border=True,
            threat_actor_type="state_actor",
            suspected_malicious=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # 4. Fast-track — malicious DNS access
    show_result(
        "4. Malicious DNS access — fast-track (C2 bypassed)",
        qualify_hcpn_incident(
            sectors_affected=["digital_infrastructure"],
            entity_types=["dns_service_provider"],
            service_impact="unavailable",
            data_impact="accessed",
            suspected_malicious=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # 5. Government data exfiltration — national security
    show_result(
        "5. Government data exfiltration — national security",
        qualify_hcpn_incident(
            sectors_affected=["public_administration"],
            entity_types=[],
            data_impact="exfiltrated",
            threat_actor_type="state_actor",
            sensitive_data_type="government_data",
            suspected_malicious=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # 6. Degraded water supply — undetermined
    show_result(
        "6. Degraded water supply — undetermined thresholds",
        qualify_hcpn_incident(
            sectors_affected=["drinking_water"],
            entity_types=["drinking_water_supplier"],
            safety_impact="health_risk",
            service_impact="degraded",
            affected_persons_count=50000,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        ),
    )

    # 7. Food sector — non-essential
    show_result(
        "7. Food sector — non-essential, does not qualify",
        qualify_hcpn_incident(
            sectors_affected=["food"],
            entity_types=[],
            service_impact="unavailable",
            suspected_malicious=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # 8. Energy — no coordination needed
    show_result(
        "8. Energy incident — handled locally, no coordination",
        qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=["electricity_undertaking"],
            safety_impact="death",
            service_impact="unavailable",
            coordination_required=False,
            urgent_decisions_required=False,
            prejudice_actual=True,
        ),
    )

    # 9. Capacity exceeded — large-scale
    # Note: no suspected_malicious to show C2 sensitive_data + national_security path
    show_result(
        "9. Capacity exceeded — large-scale cybersecurity incident",
        qualify_hcpn_incident(
            sectors_affected=["digital_infrastructure"],
            entity_types=[],
            service_impact="unavailable",
            threat_actor_type="state_actor",
            sensitive_data_type="critical_strategic_data",
            data_impact="exfiltrated",
            capacity_exceeded=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        ),
    )

    # ----------------------------------------------------------------
    section("THREAT SCENARIOS")
    # ----------------------------------------------------------------

    # 10. Imminent APT — national major cyber threat
    show_result(
        "10. Imminent APT on energy — Alerte/CERC",
        qualify_hcpn_threat(
            sectors_affected=["energy"],
            entity_types=["electricity_undertaking"],
            threat_probability="imminent",
            safety_impact="death",
            service_impact="unavailable",
            threat_actor_type="state_actor",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        ),
    )

    # 11. Low probability — does not qualify
    show_result(
        "11. Low probability threat — does not qualify",
        qualify_hcpn_threat(
            sectors_affected=["banking"],
            entity_types=[],
            threat_probability="low",
            safety_impact="death",
            service_impact="unavailable",
            threat_actor_type="state_actor",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        ),
    )

    # ----------------------------------------------------------------
    section("SUMMARY")
    # ----------------------------------------------------------------

    print("  Scenarios 1-5, 9:    QUALIFY  — various paths to crisis activation")
    print("  Scenario 4:          QUALIFY  — fast-track (Criterion 2 bypassed)")
    print("  Scenario 6:          NO       — undetermined, recommends consultation")
    print("  Scenarios 7-8:       NO       — C1 fails (food) / C3 fails (no coordination)")
    print("  Scenario 10:         QUALIFY  — threat, Alerte/CERC mode")
    print("  Scenario 11:         NO       — low probability threat rejected")
    print()


if __name__ == "__main__":
    main()
