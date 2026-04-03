#!/usr/bin/env python3
"""CyberScale — End-to-end demo: Belgium national layer.

Exercises the three-tier routing for Belgian entities (IR → BE national → NIS2 ML)
with real ML models and deterministic CCB horizontal thresholds.

Scenarios:
1. BE energy — malicious SCADA access (significant via CCB malicious CIA)
2. BE hospital — 30% users down 2h (significant via CCB availability)
3. BE transport — severe financial loss (significant via CCB financial)
4. BE energy — death reported (significant via CCB third-party damage)
5. BE chemicals — trade secret exfiltration (significant via CCB financial)
6. BE cloud provider — IR entity, bypasses BE national
7. BE bank — DORA entity, falls to NIS2 ML
8. BE energy — 15% users 3h (not significant, below 20% threshold)
9. BE manufacturing — total outage 1.5h (significant, 100% implied)
10. BE energy — minor incident (not significant)
11. Phase 3a: National CSIRT classification for BE entities

Usage:
    poetry run python evaluation/e2e_be_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.contextual import ContextualClassifier
from cyberscale.tools.entity_incident import _assess_entity_incident
from cyberscale.tools.national_incident import _assess_national_incident


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
            print(f"    Triggered:    {tc[:75]}")
    if sig.get("competent_authority"):
        print(f"    Authority:    {sig['competent_authority']}")
    if sig.get("ilr_reference"):
        print(f"    ILR ref:      {sig['ilr_reference']}")
    if sig.get("ccb_reference"):
        print(f"    CCB ref:      {sig['ccb_reference']}")
    if sig.get("applicable_frameworks"):
        for fw in sig["applicable_frameworks"]:
            auth = fw.get("competent_authority", "N/A")
            note = fw.get("note", "")
            if note:
                print(f"    Framework:    {fw['framework']} ({auth}) — {note[:60]}")
            else:
                print(f"    Framework:    {fw['framework']} ({auth})")
    if sig.get("reporting_hint"):
        print(f"    Hint:         {sig['reporting_hint'][:80]}...")
    print(f"    Early warn:   recommended={ew['recommended']}")
    print()


def main() -> None:
    print("=" * 70)
    print("  CyberScale — Belgium National Layer E2E Demo")
    print("  CCB NIS2 Notification Guide v1.3 (August 2025)")
    print("=" * 70)

    ctx_path = PROJECT_ROOT / "data" / "models" / "contextual"
    if not ctx_path.exists():
        print("\nERROR: Contextual model not deployed at data/models/contextual/")
        print("Run training or download from HuggingFace first.")
        sys.exit(1)

    clf = ContextualClassifier(model_path=ctx_path)
    print("\n  Contextual model loaded.\n")

    # ==================================================================
    section("TIER 2 — Belgium National Thresholds (CCB Horizontal)")
    # ==================================================================

    # 1. Malicious SCADA access
    r1 = _assess_entity_incident(
        clf,
        description="Suspected state-sponsored intrusion into Belgian electricity distribution SCADA systems. Unauthorized access detected to control systems.",
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="BE",
        suspected_malicious=True,
        data_impact="accessed",
        service_impact="degraded",
        impact_duration_hours=4,
    )
    entity_summary("1. BE Energy — Malicious SCADA access", r1)

    # 2. Hospital availability
    r2 = _assess_entity_incident(
        clf,
        description="Belgian university hospital IT systems partially disrupted by ransomware. 30% of clinical workstations affected for 2 hours.",
        sector="health",
        entity_type="healthcare_provider",
        ms_established="BE",
        suspected_malicious=True,
        data_impact="compromised",
        service_impact="degraded",
        impact_duration_hours=2,
    )
    entity_summary("2. BE Hospital — Malicious compromise + degraded service", r2)

    # 3. Transport severe financial loss
    r3 = _assess_entity_incident(
        clf,
        description="SNCB signalling systems compromised. Major financial impact from cancelled services and emergency response costs exceeding EUR 500K.",
        sector="transport",
        entity_type="railway_undertaking",
        ms_established="BE",
        suspected_malicious=True,
        data_impact="accessed",
        financial_impact="severe",
        service_impact="unavailable",
        impact_duration_hours=6,
    )
    entity_summary("3. BE Rail (SNCB) — Severe financial loss", r3)

    # 4. Energy with death
    r4 = _assess_entity_incident(
        clf,
        description="Cyberattack on Belgian gas distribution causes valve control loss. One fatality at industrial site due to gas leak.",
        sector="energy",
        entity_type="gas_undertaking",
        ms_established="BE",
        safety_impact="death",
        service_impact="unavailable",
        impact_duration_hours=3,
    )
    entity_summary("4. BE Gas — Death reported (third-party damage)", r4)

    # 5. Trade secret exfiltration
    r5 = _assess_entity_incident(
        clf,
        description="APT group exfiltrates proprietary chemical formulas from Belgian chemicals manufacturer. Industrial espionage confirmed.",
        sector="chemicals",
        entity_type="chemicals_manufacturer",
        ms_established="BE",
        suspected_malicious=True,
        data_impact="exfiltrated",
    )
    entity_summary("5. BE Chemicals — Trade secret exfiltration", r5)

    # ==================================================================
    section("TIER 1 — IR Thresholds (EU-wide, bypass BE national)")
    # ==================================================================

    # 6. Cloud provider — IR entity
    r6 = _assess_entity_incident(
        clf,
        description="Belgian cloud provider experiencing 45-minute complete outage affecting enterprise customers across Benelux.",
        sector="digital_infrastructure",
        entity_type="cloud_computing_provider",
        ms_established="BE",
        ms_affected=["BE", "NL", "LU"],
        service_impact="unavailable",
        suspected_malicious=True,
        impact_duration_hours=0.75,
    )
    entity_summary("6. BE Cloud Provider — IR entity (Art. 7)", r6)

    # ==================================================================
    section("TIER 3 — NIS2 ML Fallback")
    # ==================================================================

    # 7. Bank — DORA excluded
    r7 = _assess_entity_incident(
        clf,
        description="Belgian bank online platform disrupted for 4 hours. Customer transactions affected.",
        sector="banking",
        entity_type="credit_institution",
        ms_established="BE",
        service_impact="unavailable",
        financial_impact="severe",
        impact_duration_hours=4,
    )
    entity_summary("7. BE Bank — DORA excluded, NIS2 ML fallback", r7)

    # ==================================================================
    section("BOUNDARY CASES — Not Significant")
    # ==================================================================

    # 8. Below 20% threshold
    r8 = _assess_entity_incident(
        clf,
        description="Minor network disruption at Belgian energy provider. 15% of customers experience intermittent service for 3 hours.",
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="BE",
        service_impact="degraded",
        impact_duration_hours=3,
    )
    entity_summary("8. BE Energy — 15% users 3h (below 20% threshold)", r8)

    # 9. Manufacturing total outage — significant (100% implied)
    r9 = _assess_entity_incident(
        clf,
        description="Belgian machinery manufacturer production systems completely offline for 1.5 hours due to ransomware.",
        sector="manufacturing",
        entity_type="machinery_manufacturer",
        ms_established="BE",
        service_impact="unavailable",
        suspected_malicious=True,
        data_impact="compromised",
        impact_duration_hours=1.5,
    )
    entity_summary("9. BE Manufacturing — Total outage 1.5h (significant)", r9)

    # 10. Minor incident
    r10 = _assess_entity_incident(
        clf,
        description="Brief partial disruption at Belgian electricity provider. Minor configuration issue resolved in 30 minutes.",
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="BE",
        service_impact="partial",
        financial_impact="minor",
        impact_duration_hours=0.5,
    )
    entity_summary("10. BE Energy — Minor incident (not significant)", r10)

    # ==================================================================
    section("PHASE 3a — BE National CSIRT Classification")
    # ==================================================================

    print("  Aggregating BE entity notifications from scenarios 1, 3, 4...\n")

    be_notifications = [
        {
            "sector": "energy",
            "ms_established": "BE",
            "service_impact": "degraded",
            "data_impact": "accessed",
            "financial_impact": "none",
            "safety_impact": "none",
            "affected_persons_count": 1000,
        },
        {
            "sector": "transport",
            "ms_established": "BE",
            "service_impact": "unavailable",
            "data_impact": "accessed",
            "financial_impact": "severe",
            "safety_impact": "none",
            "affected_persons_count": 5000,
        },
        {
            "sector": "energy",
            "ms_established": "BE",
            "service_impact": "unavailable",
            "data_impact": "none",
            "financial_impact": "none",
            "safety_impact": "death",
            "affected_persons_count": 500,
        },
    ]

    be_nat = _assess_national_incident(
        "Coordinated attack on Belgian critical infrastructure: energy SCADA, rail signalling, gas distribution.",
        be_notifications,
    )

    print(f"  MS:             {be_nat['ms_established']}")
    print(f"  Entities:       {be_nat['entity_count']}")
    print(f"  T-level:        {be_nat['technical']['level']}")
    for b in be_nat["technical"]["basis"]:
        print(f"                  - {b}")
    print(f"  O-level:        {be_nat['operational']['level']}")
    for b in be_nat["operational"]["basis"]:
        print(f"                  - {b}")
    print(f"  Classification: {be_nat['classification']} ({be_nat['provision']})")
    print(f"  Label:          {be_nat['label']}")
    print(f"  Cross-border:   {be_nat['cross_border']}")

    # ==================================================================
    section("ROUTING SUMMARY")
    # ==================================================================

    print("  TIER 1 — IR (EU-wide, takes precedence):")
    print(f"    Cloud Provider: model={r6['significance']['model']}, significant={r6['significance']['significant_incident']}")
    print()
    print("  TIER 2 — BE National (CCB horizontal thresholds):")
    print(f"    Energy SCADA:   model={r1['significance']['model']}, significant={r1['significance']['significant_incident']}")
    print(f"    Hospital:       model={r2['significance']['model']}, significant={r2['significance']['significant_incident']}")
    print(f"    Rail SNCB:      model={r3['significance']['model']}, significant={r3['significance']['significant_incident']}")
    print(f"    Gas (death):    model={r4['significance']['model']}, significant={r4['significance']['significant_incident']}")
    print(f"    Chemicals:      model={r5['significance']['model']}, significant={r5['significance']['significant_incident']}")
    print(f"    Manufacturing:  model={r9['significance']['model']}, significant={r9['significance']['significant_incident']}")
    print()
    print("  TIER 2 — BE National (not significant):")
    print(f"    Energy 15%:     model={r8['significance']['model']}, significant={r8['significance']['significant_incident']}")
    print(f"    Energy minor:   model={r10['significance']['model']}, significant={r10['significance']['significant_incident']}")
    print()
    print("  TIER 3 — NIS2 ML (fallback for DORA-excluded):")
    print(f"    Bank:           model={r7['significance']['model']}, significant={r7['significance']['significant_incident']}")
    print()
    print("  NATIONAL CSIRT:")
    print(f"    BE National:    {be_nat['classification']} ({be_nat['technical']['level']}/{be_nat['operational']['level']})")
    print()


if __name__ == "__main__":
    main()
