#!/usr/bin/env python3
"""CyberScale v5 — End-to-end demo: Entity → National → EU.

Simulates a cross-border supply chain attack affecting a LU cloud provider
and a DE hospital. Walks through all three tiers:
1. Entity self-assessment (Phase 1+2) — ML + IR thresholds
2. National CSIRT classification (Phase 3a) — deterministic
3. EU-CyCLONe classification (Phase 3b) — deterministic + CyCLONe Officers

Usage:
    poetry run python evaluation/e2e_v5_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.scorer import SeverityScorer
from cyberscale.models.contextual import ContextualClassifier
from cyberscale.models.contextual_ir import (
    is_ir_entity, assess_ir_significance, assess_nis2_significance,
)
from cyberscale.models.early_warning import recommend_early_warning
from cyberscale.tools.national_incident import _assess_national_incident
from cyberscale.tools.eu_incident import _assess_eu_incident


def section(title: str) -> None:
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def main() -> None:
    section("CyberScale v5 End-to-End Demo")
    print("Scenario: Supply chain attack via compromised cloud provider update.")
    print("  - LU cloud provider: service unavailable, data accessed, 5000 users")
    print("  - DE hospital: ransomware via cloud dependency, patient data exfiltrated")
    print("  - FR bank: degraded services via shared cloud infrastructure")

    # =========================================================================
    # PHASE 1 — Vulnerability Scoring
    # =========================================================================
    section("Phase 1 — Vulnerability Scoring (ML)")

    scorer_path = PROJECT_ROOT / "data" / "models" / "scorer"
    if scorer_path.exists():
        scorer = SeverityScorer(scorer_path)
        p1 = scorer.predict(
            "Supply chain compromise in cloud management platform allows "
            "remote code execution via trojanized software update",
            cwe="CWE-506",
        )
        print(f"  Score: {p1.score}/10  Band: {p1.band}  Confidence: {p1.confidence}")
        phase1_score = p1.score
    else:
        print("  [Scorer model not deployed — using CVSS estimate]")
        phase1_score = 9.1

    # =========================================================================
    # PHASE 2 — Entity Self-Assessment (3 entities)
    # =========================================================================
    section("Phase 2 — Entity Incident Assessment (ML + IR Thresholds)")

    ctx_path = PROJECT_ROOT / "data" / "models" / "contextual"
    if ctx_path.exists():
        ctx = ContextualClassifier(ctx_path)
        has_model = True
    else:
        print("  [Contextual model not deployed — using mock severity]")
        has_model = False

    # --- Entity 1: LU Cloud Provider (IR entity) ---
    print("--- Entity 1: LU Cloud Provider ---")
    print(f"  entity_type: cloud_computing_provider")
    print(f"  IR entity: {is_ir_entity('cloud_computing_provider')}")

    if has_model:
        e1_ctx = ctx.predict(
            "Cloud platform outage after trojanized update deployed to production",
            sector="digital_infrastructure",
            ms_established="LU", ms_affected=["DE", "FR"],
            score=phase1_score,
            entity_type="cloud_computing_provider",
            entity_affected=True,
            service_impact="unavailable", data_impact="accessed",
            financial_impact="significant", safety_impact="none",
            affected_persons_count=5000,
            suspected_malicious=True, impact_duration_hours=4,
        )
        print(f"  Contextual severity: {e1_ctx.severity} ({e1_ctx.confidence})")

    e1_ir = assess_ir_significance(
        entity_type="cloud_computing_provider",
        service_impact="unavailable", data_impact="accessed",
        financial_impact="significant",
        affected_persons_count=5000,
        suspected_malicious=True, impact_duration_hours=4,
        cross_border=True,
    )
    print(f"  IR significant: {e1_ir.significant_incident}")
    print(f"  Triggered: {e1_ir.triggered_criteria}")
    print(f"  Articles: {e1_ir.applicable_articles[:3]}...")

    e1_ew = recommend_early_warning(
        e1_ir.significant_incident, suspected_malicious=True, cross_border=True,
    )
    print(f"  Early warning: recommended={e1_ew.recommended}, deadline={e1_ew.deadline}")

    # --- Entity 2: DE Hospital (NIS2 entity) ---
    print("\n--- Entity 2: DE Hospital ---")
    print(f"  entity_type: healthcare_provider")
    print(f"  IR entity: {is_ir_entity('healthcare_provider')}")

    if has_model:
        e2_ctx = ctx.predict(
            "Ransomware encrypted hospital patient records after cloud supply chain compromise",
            sector="health",
            ms_established="DE",
            score=phase1_score,
            entity_type="healthcare_provider",
            entity_affected=True,
            service_impact="unavailable", data_impact="exfiltrated",
            financial_impact="severe", safety_impact="health_damage",
            affected_persons_count=50000,
            suspected_malicious=True, impact_duration_hours=72,
        )
        print(f"  Contextual severity: {e2_ctx.severity} ({e2_ctx.confidence})")
        e2_nis2 = assess_nis2_significance(e2_ctx, entity_affected=True)
        print(f"  NIS2 significant: {e2_nis2.significant_incident}")
        print(f"  Reporting hint: {e2_nis2.reporting_hint[:80]}...")
    else:
        print("  [Using mock: severity=Critical, significant=likely]")

    e2_ew = recommend_early_warning("likely", suspected_malicious=True, cross_border=False)
    print(f"  Early warning: recommended={e2_ew.recommended}, deadline={e2_ew.deadline}")

    # --- Entity 3: FR Bank (NIS2 entity, less affected) ---
    print("\n--- Entity 3: FR Bank ---")
    print(f"  entity_type: credit_institution")

    if has_model:
        e3_ctx = ctx.predict(
            "Online banking degraded after cloud provider outage disrupted API services",
            sector="banking",
            ms_established="FR",
            entity_type="credit_institution",
            entity_affected=True,
            service_impact="degraded", data_impact="none",
            financial_impact="minor", safety_impact="none",
            affected_persons_count=100000,
            suspected_malicious=False, impact_duration_hours=2,
        )
        print(f"  Contextual severity: {e3_ctx.severity} ({e3_ctx.confidence})")
        e3_nis2 = assess_nis2_significance(e3_ctx, entity_affected=True)
        print(f"  NIS2 significant: {e3_nis2.significant_incident}")
    else:
        print("  [Using mock: severity=Medium, significant=uncertain]")

    e3_ew = recommend_early_warning("uncertain", suspected_malicious=False)
    print(f"  Early warning: recommended={e3_ew.recommended} (precautionary)")

    # =========================================================================
    # PHASE 3a — National CSIRT Classification
    # =========================================================================
    section("Phase 3a — National Classification (deterministic)")

    # LU CSIRT: 1 entity (cloud provider)
    lu_notifications = [
        {"sector": "digital_infrastructure", "ms_established": "LU",
         "ms_affected": ["DE", "FR"],
         "service_impact": "unavailable", "data_impact": "accessed",
         "financial_impact": "significant", "safety_impact": "none",
         "affected_persons_count": 5000},
    ]
    lu_result = _assess_national_incident(
        "Supply chain compromise at LU cloud provider", lu_notifications,
    )
    print("--- LU National CSIRT ---")
    print(f"  T-level: {lu_result['technical']['level']} ({lu_result['technical']['basis']})")
    print(f"  O-level: {lu_result['operational']['level']} ({lu_result['operational']['basis']})")
    print(f"  Classification: {lu_result['classification']} ({lu_result['provision']})")
    print(f"  Cross-border: {lu_result['cross_border']} → CSIRT Network sharing")

    # DE CSIRT: 1 entity (hospital)
    de_notifications = [
        {"sector": "health", "ms_established": "DE",
         "service_impact": "unavailable", "data_impact": "exfiltrated",
         "financial_impact": "severe", "safety_impact": "health_damage",
         "affected_persons_count": 50000},
    ]
    de_result = _assess_national_incident(
        "Ransomware at DE hospital via cloud supply chain", de_notifications,
    )
    print("\n--- DE National CSIRT ---")
    print(f"  T-level: {de_result['technical']['level']} ({de_result['technical']['basis']})")
    print(f"  O-level: {de_result['operational']['level']} ({de_result['operational']['basis']})")
    print(f"  Classification: {de_result['classification']} ({de_result['provision']})")
    print(f"  Cross-border: {de_result['cross_border']}")

    # FR CSIRT: 1 entity (bank)
    fr_notifications = [
        {"sector": "banking", "ms_established": "FR",
         "service_impact": "degraded", "data_impact": "none",
         "financial_impact": "minor", "safety_impact": "none",
         "affected_persons_count": 100000},
    ]
    fr_result = _assess_national_incident(
        "Banking service degradation from cloud provider outage", fr_notifications,
    )
    print("\n--- FR National CSIRT ---")
    print(f"  T-level: {fr_result['technical']['level']} ({fr_result['technical']['basis']})")
    print(f"  O-level: {fr_result['operational']['level']} ({fr_result['operational']['basis']})")
    print(f"  Classification: {fr_result['classification']} ({fr_result['provision']})")
    print(f"  Cross-border: {fr_result['cross_border']}")

    # =========================================================================
    # PHASE 3b — EU-CyCLONe Classification
    # =========================================================================
    section("Phase 3b — EU-CyCLONe Classification (deterministic + Officers)")

    eu_result = _assess_eu_incident(
        description="Cross-border supply chain attack via trojanized cloud update affecting health, digital infrastructure, and banking across 3 MS",
        national_classifications=[lu_result, de_result, fr_result],
        cyclone_officer_inputs=[
            {
                "ms": "LU",
                "national_capacity_status": "strained",
                "political_sensitivity": "elevated",
                "coordination_needs": "eu_active",
                "intelligence_context": "Suspected APT29, same TTPs as SolarWinds-style campaign. Initial vector was compromised build pipeline.",
                "escalation_recommendation": "none",
            },
            {
                "ms": "DE",
                "national_capacity_status": "overwhelmed",
                "political_sensitivity": "high",
                "coordination_needs": "eu_active",
                "intelligence_context": "Hospital patient safety at risk. 3 cancelled surgeries. National media coverage. BSI activated crisis team.",
                "escalation_recommendation": "escalate",
            },
            {
                "ms": "FR",
                "national_capacity_status": "normal",
                "political_sensitivity": "none",
                "coordination_needs": "eu_info",
                "intelligence_context": "Banking degradation contained. No data breach. Customer impact minimal.",
                "escalation_recommendation": "none",
            },
        ],
    )

    print("--- EU-CyCLONe Assessment ---")
    print(f"  EU T-level: {eu_result['eu_technical']['level']}")
    print(f"  EU O-level: {eu_result['eu_operational']['level']} (base: {eu_result['eu_operational']['base_level']})")
    print(f"  Officer escalation: {eu_result['eu_operational']['officer_escalation']}")
    if eu_result['eu_operational']['officer_reasons']:
        for reason in eu_result['eu_operational']['officer_reasons']:
            print(f"    - {reason}")
    print(f"  Classification: {eu_result['classification']} ({eu_result['provision']})")
    print(f"  Coordination: {eu_result['coordination_level']}")
    print(f"  MS involved: {eu_result['ms_involved']}")
    print(f"  Basis: {eu_result['aggregation_basis']}")

    if "intelligence_briefing" in eu_result:
        print(f"\n  Intelligence briefing ({len(eu_result['intelligence_briefing'])} entries):")
        for entry in eu_result['intelligence_briefing']:
            print(f"    [{entry['ms']}] {entry['context'][:80]}...")

    # =========================================================================
    # SUMMARY
    # =========================================================================
    section("Summary")

    print("  ENTITY LAYER (ML):")
    print(f"    LU cloud (IR): significant={e1_ir.significant_incident}, early_warning={e1_ew.recommended}")
    print(f"    DE hospital (NIS2): early_warning={e2_ew.recommended}")
    print(f"    FR bank (NIS2): early_warning={e3_ew.recommended} (precautionary)")
    print()
    print("  NATIONAL LAYER (deterministic):")
    print(f"    LU: {lu_result['classification']} ({lu_result['technical']['level']}/{lu_result['operational']['level']}), cross_border={lu_result['cross_border']}")
    print(f"    DE: {de_result['classification']} ({de_result['technical']['level']}/{de_result['operational']['level']}), cross_border={de_result['cross_border']}")
    print(f"    FR: {fr_result['classification']} ({fr_result['technical']['level']}/{fr_result['operational']['level']}), cross_border={fr_result['cross_border']}")
    print()
    print("  EU LAYER (deterministic + Officers):")
    print(f"    EU: {eu_result['classification']} ({eu_result['eu_technical']['level']}/{eu_result['eu_operational']['level']})")
    print(f"    Coordination: {eu_result['coordination_level']}")
    print(f"    Officer escalation: {eu_result['eu_operational']['officer_escalation']}")
    print()
    print("  Pipeline: zero ML models in Phase 3. ML only in Phase 1+2 (entity text interpretation).")


if __name__ == "__main__":
    main()
