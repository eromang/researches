"""Composable Phase 1 → Phase 2 → Phase 3 pipeline.

Chains the three CyberScale phases:
  Phase 1 (scorer): vulnerability description + CWE → score, band, confidence
  Phase 2 (contextual): description + sector + cross_border + Phase 1 score → contextual severity
  Phase 3 (incident): T-model + O-model → Blueprint matrix classification
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PipelineResult:
    """Combined result from all pipeline phases."""

    # Phase 1
    phase1_score: float
    phase1_band: str
    phase1_confidence: str

    # Phase 2
    phase2_severity: str
    phase2_confidence: str
    phase2_key_factors: list[str]

    # Phase 3 (optional — only when incident fields provided)
    phase3_t_level: Optional[str] = None
    phase3_o_level: Optional[str] = None
    classification: Optional[str] = None
    label: Optional[str] = None
    provision: Optional[str] = None


def run_pipeline(
    scorer,
    contextual,
    description: str,
    sector: str,
    ms_established: str = "EU",
    ms_affected: Optional[list[str]] = None,
    cwe: Optional[str] = None,
    entity_type: Optional[str] = None,
    cer_critical_entity: Optional[bool] = None,
    # Phase 3 fields (all optional — omit to skip Phase 3)
    service_impact: Optional[str] = None,
    affected_entities: Optional[int] = None,
    sectors_affected: Optional[int] = None,
    cascading: Optional[str] = None,
    data_impact: Optional[str] = None,
    entity_relevance: Optional[str] = None,
    p3_ms_affected: Optional[int] = None,
    cross_border_pattern: Optional[str] = None,
    capacity_exceeded: Optional[bool] = None,
) -> PipelineResult:
    """Run the composable assessment pipeline.

    Phase 1 score is automatically fed into Phase 2 as context.
    Phase 3 runs only when technical/operational classifiers and
    incident fields are provided.
    """
    # --- Phase 1: Vulnerability scoring ---
    p1 = scorer.predict(description, cwe=cwe)

    # --- Phase 2: Contextual severity (receives Phase 1 score) ---
    p2 = contextual.predict(
        description, sector,
        ms_established=ms_established, ms_affected=ms_affected,
        score=p1.score,
        entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
    )

    # --- Phase 3: Incident classification (optional, fully deterministic) ---
    has_phase3 = service_impact is not None

    if has_phase3:
        from cyberscale.aggregation import derive_t_level, derive_o_level
        t_level, _ = derive_t_level(
            service_impact, data_impact or "none",
            cascading or "none", affected_entities or 1,
        )
        o_level, _ = derive_o_level(
            cross_border_pattern or "none",
            capacity_exceeded or False,
            entity_relevance or "non_essential",
            p3_ms_affected or 1,
            sectors_affected or 1,
        )

        from cyberscale.matrix.dual_scale import classify_incident
        matrix = classify_incident(t_level, o_level)

        return PipelineResult(
            phase1_score=p1.score,
            phase1_band=p1.band,
            phase1_confidence=p1.confidence,
            phase2_severity=p2.severity,
            phase2_confidence=p2.confidence,
            phase2_key_factors=p2.key_factors,
            phase3_t_level=t_level,
            phase3_o_level=o_level,
            classification=matrix.classification,
            label=matrix.label,
            provision=matrix.provision,
        )

    return PipelineResult(
        phase1_score=p1.score,
        phase1_band=p1.band,
        phase1_confidence=p1.confidence,
        phase2_severity=p2.severity,
        phase2_confidence=p2.confidence,
        phase2_key_factors=p2.key_factors,
    )
