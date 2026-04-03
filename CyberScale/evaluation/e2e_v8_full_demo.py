#!/usr/bin/env python3
"""CyberScale v8 — Full end-to-end demo: entity → national → HCPN crisis.

Exercises the complete pipeline from entity-level assessment through
national CSIRT classification to HCPN national crisis qualification.

Scenario: Coordinated state-sponsored attack on Luxembourg critical
infrastructure — energy grid (Creos), rail (CFL), hospital (CHL).
Cross-border spillover to Belgian energy.

Pipeline:
  1. Entity assessments (v7 three-tier routing)
  2. Phase 3a national CSIRT classification (deterministic)
  3. HCPN crisis qualification (v8 — determines PGGCCN activation)

Usage:
    poetry run python evaluation/e2e_v8_full_demo.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.contextual import ContextualClassifier
from cyberscale.tools.entity_incident import _assess_entity_incident
from cyberscale.tools.national_incident import _assess_national_incident
from cyberscale.national.lu_crisis import qualify_hcpn_incident


def section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def entity_summary(name: str, result: dict) -> None:
    sig = result["significance"]
    ew = result["early_warning"]
    print(f"  {name}")
    print(f"    Severity:     {result['severity']} ({result['confidence']})")
    print(f"    Model:        {sig['model']}")
    print(f"    Significant:  {sig['significant_incident']}")
    if sig.get("triggered_criteria"):
        for tc in sig["triggered_criteria"][:3]:
            print(f"    Triggered:    {tc[:70]}")
    if sig.get("ilr_reference"):
        print(f"    ILR ref:      {sig['ilr_reference']}")
    print(f"    Early warn:   recommended={ew['recommended']}")
    print()


def main() -> None:
    print("=" * 70)
    print("  CyberScale v8 — Full Pipeline Demo")
    print("  Entity Assessment -> National Classification -> HCPN Crisis")
    print("=" * 70)

    # Load contextual model
    ctx_path = PROJECT_ROOT / "data" / "models" / "contextual"
    if not ctx_path.exists():
        print("\nERROR: Contextual model not deployed at data/models/contextual/")
        print("Run training or download from HuggingFace first.")
        sys.exit(1)

    clf = ContextualClassifier(model_path=ctx_path)
    print("\n  Contextual model loaded.\n")

    # ==================================================================
    section("STEP 1 — Entity-Level Assessments (v7 three-tier routing)")
    # ==================================================================

    print("  Scenario: Coordinated state-sponsored attack on Luxembourg")
    print("  critical infrastructure with cross-border spillover.\n")

    # 1a. Creos Luxembourg — energy grid attack
    r_energy = _assess_entity_incident(
        clf,
        description=(
            "State-sponsored cyberattack on Creos Luxembourg SCADA systems. "
            "HV/EHV transmission network compromised, cascading outage affecting "
            "10,000+ low-voltage delivery points. One fatality reported at "
            "industrial site due to power-dependent life support failure."
        ),
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="LU",
        ms_affected=["LU", "BE"],
        service_impact="unavailable",
        data_impact="compromised",
        safety_impact="death",
        financial_impact="severe",
        affected_persons_count=10000,
        suspected_malicious=True,
        impact_duration_hours=6,
        sector_specific={
            "pods_affected": 10000,
            "voltage_level": "hv_ehv",
            "scada_unavailable_min": 360,
        },
    )
    entity_summary("Creos LU — Energy (HV/EHV, 10K POD, SCADA)", r_energy)

    # 1b. CFL — rail transport disrupted
    r_rail = _assess_entity_incident(
        clf,
        description=(
            "CFL signalling and traffic management systems encrypted by "
            "ransomware. 15% of daily train services cancelled. Infrastructure "
            "management systems unavailable for 5 hours."
        ),
        sector="transport",
        entity_type="railway_undertaking",
        ms_established="LU",
        service_impact="unavailable",
        data_impact="compromised",
        affected_persons_count=5000,
        suspected_malicious=True,
        impact_duration_hours=5,
        sector_specific={
            "trains_cancelled_pct": 15.0,
            "slots_impacted": 200,
        },
    )
    entity_summary("CFL — Rail (15% cancelled, 5h outage)", r_rail)

    # 1c. CHL Hospital — health impact
    r_health = _assess_entity_incident(
        clf,
        description=(
            "Centre Hospitalier de Luxembourg IT systems compromised in "
            "coordinated attack. Emergency department systems down, 3 patients "
            "with serious health complications due to delayed treatment."
        ),
        sector="health",
        entity_type="healthcare_provider",
        ms_established="LU",
        service_impact="unavailable",
        data_impact="compromised",
        safety_impact="health_damage",
        affected_persons_count=500,
        suspected_malicious=True,
        impact_duration_hours=8,
        sector_specific={"persons_health_impact": 3},
    )
    entity_summary("CHL Hospital (3 serious health impacts)", r_health)

    # 1d. BE energy spillover
    r_be = _assess_entity_incident(
        clf,
        description=(
            "Belgian electricity distribution partially affected by cascading "
            "failure from Luxembourg HV/EHV grid. Degraded service in border "
            "region, no customer outages."
        ),
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="BE",
        service_impact="degraded",
        impact_duration_hours=2,
    )
    entity_summary("BE Electricity (spillover, degraded)", r_be)

    # ==================================================================
    section("STEP 2 — Phase 3a: LU National CSIRT Classification")
    # ==================================================================

    lu_notifications = [
        {
            "sector": "energy",
            "ms_established": "LU",
            "ms_affected": ["LU", "BE"],
            "service_impact": "unavailable",
            "data_impact": "compromised",
            "financial_impact": "severe",
            "safety_impact": "death",
            "affected_persons_count": 10000,
        },
        {
            "sector": "transport",
            "ms_established": "LU",
            "service_impact": "unavailable",
            "data_impact": "compromised",
            "financial_impact": "none",
            "safety_impact": "none",
            "affected_persons_count": 5000,
        },
        {
            "sector": "health",
            "ms_established": "LU",
            "service_impact": "unavailable",
            "data_impact": "compromised",
            "financial_impact": "none",
            "safety_impact": "health_damage",
            "affected_persons_count": 500,
        },
    ]

    lu_nat = _assess_national_incident(
        "Coordinated state-sponsored attack on Luxembourg critical infrastructure: "
        "energy grid, rail, hospital. Cross-border impact to Belgium.",
        lu_notifications,
    )

    print(f"  MS:             {lu_nat['ms_established']}")
    print(f"  Entities:       {lu_nat['entity_count']}")
    print(f"  T-level:        {lu_nat['technical']['level']}")
    for b in lu_nat["technical"]["basis"]:
        print(f"                  - {b}")
    print(f"  O-level:        {lu_nat['operational']['level']}")
    for b in lu_nat["operational"]["basis"]:
        print(f"                  - {b}")
    print(f"  Classification: {lu_nat['classification']} ({lu_nat['provision']})")
    print(f"  Label:          {lu_nat['label']}")
    print(f"  Cross-border:   {lu_nat['cross_border']}")

    # ==================================================================
    section("STEP 3 — v8: HCPN National Crisis Qualification")
    # ==================================================================

    print("  The HCPN qualifier operates ABOVE entity significance.")
    print("  It uses impact data from Steps 1-2 plus authority judgment.\n")

    # Derive inputs from the incident data
    # These would come from the national CSIRT + intelligence services
    hcpn_result = qualify_hcpn_incident(
        # From entity assessments and Phase 3a
        sectors_affected=["energy", "transport", "health"],
        entity_types=[
            "electricity_undertaking",
            "railway_undertaking",
            "healthcare_provider",
        ],
        safety_impact="death",
        service_impact="unavailable",
        data_impact="compromised",
        financial_impact="severe",
        affected_persons_count=15500,
        cross_border=True,  # BE affected
        capacity_exceeded=False,
        # Authority judgment inputs (from CERC/SRE/intelligence)
        threat_actor_type="state_actor",
        sensitive_data_type=None,
        suspected_malicious=True,
        coordination_required=True,
        urgent_decisions_required=True,
        prejudice_actual=True,
    )

    d = hcpn_result.to_dict()
    print(f"  QUALIFIES:      {d['qualifies']}")
    print(f"  Level:          {d['qualification_level']}")
    print(f"  Mode:           {d['cooperation_mode']}")
    print(f"  Fast-tracked:   {d['fast_tracked']}")
    print(f"  Consultation:   {d['recommend_consultation']}")
    print()

    for cname, cdata in d["criteria"].items():
        print(f"  {cname}: {cdata['status'].upper()}")
        for detail in cdata["details"]:
            print(f"    - {detail[:80]}")
    print()

    if d["consultation_reasons"]:
        print("  CONSULTATION REASONS:")
        for reason in d["consultation_reasons"]:
            print(f"    - {reason[:80]}")
        print()

    # ==================================================================
    section("PIPELINE SUMMARY")
    # ==================================================================

    sig_energy = r_energy["significance"]
    sig_rail = r_rail["significance"]
    sig_health = r_health["significance"]

    print("  ENTITY LAYER (v7):")
    print(f"    Creos Energy:   {sig_energy['model']}, significant={sig_energy['significant_incident']}")
    print(f"    CFL Rail:       {sig_rail['model']}, significant={sig_rail['significant_incident']}")
    print(f"    CHL Hospital:   {sig_health['model']}, significant={sig_health['significant_incident']}")
    print()
    print("  NATIONAL CSIRT (Phase 3a):")
    print(f"    Classification: {lu_nat['classification']} ({lu_nat['technical']['level']}/{lu_nat['operational']['level']})")
    print(f"    Cross-border:   {lu_nat['cross_border']} -> CSIRT Network sharing")
    print()
    print("  HCPN CRISIS QUALIFICATION (v8):")
    print(f"    Qualifies:      {d['qualifies']}")
    print(f"    Level:          {d['qualification_level']}")
    print(f"    Mode:           {d['cooperation_mode']}")
    print()
    print("  PGGCCN ACTIVATION:")
    if d["qualifies"]:
        if d["cooperation_mode"] == "crise":
            print("    -> CC (Cellule de Crise) activated at CNC Senningen")
            print("    -> CCI (Communication) + PCO-C Cyber (Operational)")
            print("    -> Minister chairs crisis response")
        else:
            print("    -> CERC (Cellule d'Evaluation du Risque Cyber) activated")
            print("    -> 24/7 via designated points of contact")
        if d["qualification_level"] == "large_scale_cybersecurity_incident":
            print("    -> EU-CyCLONe coordination triggered (large-scale)")
            print("    -> Phase 3b EU-level assessment recommended")
    else:
        print("    -> No PGGCCN activation")
    print()


if __name__ == "__main__":
    main()
