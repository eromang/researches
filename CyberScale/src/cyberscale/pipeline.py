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
    cross_border: bool,
    cwe: Optional[str] = None,
    entity_type: Optional[str] = None,
    cer_critical_entity: Optional[bool] = None,
    # Phase 3 fields (all optional — omit to skip Phase 3)
    technical=None,
    operational=None,
    service_disruption: Optional[str] = None,
    affected_entities: Optional[int] = None,
    sectors_affected: Optional[str] = None,
    cascading: Optional[str] = None,
    data_compromise: Optional[str] = None,
    entity_relevance: Optional[str] = None,
    ms_affected: Optional[int] = None,
    cross_border_pattern: Optional[str] = None,
    coordination_needs: Optional[str] = None,
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
        description, sector, cross_border,
        score=p1.score,
        entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
    )

    # --- Phase 3: Incident classification (optional) ---
    has_phase3 = (
        technical is not None
        and operational is not None
        and service_disruption is not None
    )

    if has_phase3:
        n_sectors = len([s for s in sectors_affected.split(",") if s.strip()])
        t_result = technical.predict(
            description,
            service_disruption=service_disruption,
            affected_entities=affected_entities,
            sectors_affected=n_sectors,
            cascading=cascading,
            data_compromise=data_compromise,
        )
        o_result = operational.predict(
            description,
            sectors_affected=sectors_affected,
            entity_relevance=entity_relevance,
            ms_affected=ms_affected,
            cross_border_pattern=cross_border_pattern,
            coordination_needs=coordination_needs,
            capacity_exceeded=capacity_exceeded,
        )

        from cyberscale.matrix.dual_scale import classify_incident
        matrix = classify_incident(t_result.level, o_result.level)

        return PipelineResult(
            phase1_score=p1.score,
            phase1_band=p1.band,
            phase1_confidence=p1.confidence,
            phase2_severity=p2.severity,
            phase2_confidence=p2.confidence,
            phase2_key_factors=p2.key_factors,
            phase3_t_level=t_result.level,
            phase3_o_level=o_result.level,
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
