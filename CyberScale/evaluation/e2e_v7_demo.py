#!/usr/bin/env python3
"""CyberScale v7 — End-to-end demo: Luxembourg national layer.

Exercises the three-tier routing (IR → LU national → NIS2 ML) with
real ML models and deterministic LU ILR thresholds. Covers:

1. LU electricity (national thresholds — LV-POD matrix)
2. LU rail transport (national thresholds — train cancellation)
3. LU hospital (national thresholds — health impact)
4. LU cloud provider (IR thresholds — bypasses national)
5. LU bank (DORA — falls through to NIS2 ML)
6. DE electricity (non-LU — NIS2 ML fallback)
7. National CSIRT classification for LU entities
8. EU-CyCLONe classification across LU/DE

Usage:
    poetry run python evaluation/e2e_v7_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.contextual import ContextualClassifier
from cyberscale.tools.entity_incident import _assess_entity_incident
from cyberscale.tools.national_incident import _assess_national_incident
from cyberscale.tools.eu_incident import _assess_eu_incident


def section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def entity_summary(name: str, result: dict) -> None:
    sig = result["significance"]
    ew = result["early_warning"]
    print(f"  --- {name} ---")
    print(f"    Severity:     {result['severity']} ({result['confidence']})")
    print(f"    Model:        {sig['model']}")
    print(f"    Significant:  {sig['significant_incident']}")
    if sig.get("triggered_criteria"):
        print(f"    Triggered:    {sig['triggered_criteria']}")
    if sig.get("ilr_reference"):
        print(f"    ILR ref:      {sig['ilr_reference']}")
    if sig.get("common_criteria_met"):
        print(f"    Common:       {sig['common_criteria_met']}")
    if sig.get("applicable_frameworks"):
        for fw in sig["applicable_frameworks"]:
            print(f"    Framework:    {fw['framework']} ({fw.get('competent_authority', 'N/A')})")
    if sig.get("reporting_hint"):
        print(f"    Hint:         {sig['reporting_hint'][:80]}...")
    print(f"    Early warn:   recommended={ew['recommended']}, deadline={ew['deadline']}")
    print()


def main() -> None:
    section("CyberScale v7 End-to-End Demo — Luxembourg National Layer")

    ctx_path = PROJECT_ROOT / "data" / "models" / "contextual"
    if not ctx_path.exists():
        print("ERROR: Contextual model not deployed at data/models/contextual/")
        print("Run training or download from HuggingFace first.")
        sys.exit(1)

    clf = ContextualClassifier(model_path=ctx_path)
    print("  Contextual model loaded.\n")

    # =========================================================================
    # TIER 2: LU National Thresholds
    # =========================================================================
    section("Tier 2 — Luxembourg National Thresholds (ILR)")

    # 1. LU Electricity — LV-POD matrix
    r1 = _assess_entity_incident(
        clf,
        description="Cyberattack on Creos Luxembourg distribution network causes power outage affecting 600 low-voltage delivery points for 45 minutes",
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="LU",
        service_impact="unavailable",
        impact_duration_hours=0.75,
        sector_specific={"pods_affected": 600, "voltage_level": "lv"},
    )
    entity_summary("Creos LU Electricity (LV-POD 600 × 45min)", r1)

    # 2. CFL Rail — train cancellation
    r2 = _assess_entity_incident(
        clf,
        description="Ransomware encrypts CFL signalling systems, 7% of daily train services cancelled across Luxembourg rail network",
        sector="transport",
        entity_type="railway_undertaking",
        ms_established="LU",
        suspected_malicious=True,
        sector_specific={"trains_cancelled_pct": 7.0},
    )
    entity_summary("CFL Rail (7% trains cancelled)", r2)

    # 3. CHL Hospital — health impact
    r3 = _assess_entity_incident(
        clf,
        description="Centre Hospitalier de Luxembourg IT systems compromised, 12 patients experience delayed treatment with reversible health impact",
        sector="health",
        entity_type="healthcare_provider",
        ms_established="LU",
        safety_impact="health_risk",
        suspected_malicious=True,
        sector_specific={"persons_health_impact": 12},
    )
    entity_summary("CHL Hospital (12 persons reversible)", r3)

    # =========================================================================
    # TIER 1: IR Thresholds (bypass LU national)
    # =========================================================================
    section("Tier 1 — IR Thresholds (EU-wide, bypass LU national)")

    # 4. POST Cloud — IR entity in LU
    r4 = _assess_entity_incident(
        clf,
        description="POST Luxembourg cloud computing platform experiencing complete outage affecting enterprise customers across Benelux",
        sector="digital_infrastructure",
        entity_type="cloud_computing_provider",
        ms_established="LU",
        ms_affected=["LU", "DE", "BE"],
        service_impact="unavailable",
        affected_persons_count=5000,
        suspected_malicious=True,
        impact_duration_hours=4,
    )
    entity_summary("POST Cloud (IR — Art. 7)", r4)

    # =========================================================================
    # TIER 3: NIS2 ML Fallback
    # =========================================================================
    section("Tier 3 — NIS2 ML Fallback (non-covered sectors)")

    # 5. LU Bank — DORA applies, falls through to NIS2 ML
    r5 = _assess_entity_incident(
        clf,
        description="Luxembourg bank online platform compromised, customer transactions disrupted for 3 hours",
        sector="banking",
        entity_type="credit_institution",
        ms_established="LU",
        service_impact="unavailable",
        financial_impact="significant",
        impact_duration_hours=3,
    )
    entity_summary("LU Bank (DORA/NIS2 ML)", r5)

    # 6. DE Electricity — no national module, NIS2 ML
    r6 = _assess_entity_incident(
        clf,
        description="German electricity provider SCADA disrupted, distribution network partially affected",
        sector="energy",
        entity_type="electricity_undertaking",
        ms_established="DE",
        service_impact="degraded",
        impact_duration_hours=3,
    )
    entity_summary("DE Electricity (NIS2 ML — no national module)", r6)

    # =========================================================================
    # PHASE 3a: National CSIRT Classification
    # =========================================================================
    section("Phase 3a — LU National CSIRT Classification (deterministic)")

    lu_notifications = [
        {"sector": "energy", "ms_established": "LU",
         "service_impact": "unavailable", "data_impact": "none",
         "financial_impact": "none", "safety_impact": "none",
         "affected_persons_count": 600},
        {"sector": "transport", "ms_established": "LU",
         "service_impact": "degraded", "data_impact": "compromised",
         "financial_impact": "none", "safety_impact": "none",
         "affected_persons_count": 0},
        {"sector": "health", "ms_established": "LU",
         "service_impact": "degraded", "data_impact": "none",
         "financial_impact": "none", "safety_impact": "health_risk",
         "affected_persons_count": 12},
    ]
    lu_nat = _assess_national_incident(
        "Coordinated attack on Luxembourg critical infrastructure: energy, rail, hospital",
        lu_notifications,
    )
    print(f"  T-level:        {lu_nat['technical']['level']} ({lu_nat['technical']['basis']})")
    print(f"  O-level:        {lu_nat['operational']['level']} ({lu_nat['operational']['basis']})")
    print(f"  Classification: {lu_nat['classification']} ({lu_nat['provision']})")
    print(f"  Cross-border:   {lu_nat['cross_border']}")

    # DE national
    de_notifications = [
        {"sector": "energy", "ms_established": "DE",
         "service_impact": "degraded", "data_impact": "none",
         "financial_impact": "none", "safety_impact": "none",
         "affected_persons_count": 1000},
    ]
    de_nat = _assess_national_incident(
        "German electricity provider SCADA disrupted", de_notifications,
    )
    print(f"\n  DE National: {de_nat['classification']} ({de_nat['technical']['level']}/{de_nat['operational']['level']})")

    # =========================================================================
    # PHASE 3b: EU-CyCLONe
    # =========================================================================
    section("Phase 3b — EU-CyCLONe Classification")

    eu_result = _assess_eu_incident(
        description="Coordinated cyberattack on Luxembourg critical infrastructure with spillover to German energy sector",
        national_classifications=[lu_nat, de_nat],
        cyclone_officer_inputs=[
            {
                "ms": "LU",
                "national_capacity_status": "strained",
                "political_sensitivity": "elevated",
                "coordination_needs": "eu_active",
                "intelligence_context": "Coordinated attack on LU critical infrastructure: energy, rail, hospital. ILR thresholds met for multiple sectors.",
                "escalation_recommendation": "none",
            },
            {
                "ms": "DE",
                "national_capacity_status": "normal",
                "political_sensitivity": "none",
                "coordination_needs": "eu_info",
                "intelligence_context": "Limited spillover from LU incident. Distribution network partially degraded, no customer impact.",
                "escalation_recommendation": "none",
            },
        ],
    )

    print(f"  EU T-level:       {eu_result['eu_technical']['level']}")
    print(f"  EU O-level:       {eu_result['eu_operational']['level']} (base: {eu_result['eu_operational']['base_level']})")
    print(f"  Officer escalation: {eu_result['eu_operational']['officer_escalation']}")
    if eu_result['eu_operational']['officer_reasons']:
        for reason in eu_result['eu_operational']['officer_reasons']:
            print(f"    - {reason}")
    print(f"  Classification:   {eu_result['classification']} ({eu_result['provision']})")
    print(f"  Coordination:     {eu_result['coordination_level']}")
    print(f"  MS involved:      {eu_result['ms_involved']}")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    section("v7 Three-Tier Routing Summary")

    print("  TIER 1 — IR (EU-wide, takes precedence):")
    print(f"    POST Cloud:     model={r4['significance']['model']}, significant={r4['significance']['significant_incident']}")
    print()
    print("  TIER 2 — LU National (ILR thresholds):")
    print(f"    Creos Electric: model={r1['significance']['model']}, significant={r1['significance']['significant_incident']}, ref={r1['significance']['ilr_reference']}")
    print(f"    CFL Rail:       model={r2['significance']['model']}, significant={r2['significance']['significant_incident']}, ref={r2['significance']['ilr_reference']}")
    print(f"    CHL Hospital:   model={r3['significance']['model']}, significant={r3['significance']['significant_incident']}, ref={r3['significance']['ilr_reference']}")
    print()
    print("  TIER 3 — NIS2 ML (fallback):")
    print(f"    LU Bank:        model={r5['significance']['model']}, significant={r5['significance']['significant_incident']}")
    print(f"    DE Electricity: model={r6['significance']['model']}, significant={r6['significance']['significant_incident']}")
    print()
    print("  NATIONAL → EU:")
    print(f"    LU National:    {lu_nat['classification']} ({lu_nat['technical']['level']}/{lu_nat['operational']['level']})")
    print(f"    DE National:    {de_nat['classification']} ({de_nat['technical']['level']}/{de_nat['operational']['level']})")
    print(f"    EU-CyCLONe:     {eu_result['classification']} → {eu_result['coordination_level']}")


if __name__ == "__main__":
    main()
