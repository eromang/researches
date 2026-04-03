"""Phase 2 MCP tool — Entity-facing incident assessment.

Provides assess_entity_incident: single entity + incident context →
severity + significant_incident + early warning recommendation.

Routes to IR threshold logic or NIS2 ML model based on entity_type.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger("cyberscale.tools.entity_incident")


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_classifier_instance = None
_model_path = Path("data/models/contextual")


def _get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        if not _model_path.exists():
            return None
        from cyberscale.models.contextual import ContextualClassifier
        _classifier_instance = ContextualClassifier(model_path=_model_path)
    return _classifier_instance


# ---------------------------------------------------------------------------
# Internal helper (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_entity_incident(
    clf,
    description: str,
    sector: str,
    entity_type: str,
    ms_established: str = "EU",
    ms_affected: list[str] | None = None,
    score: float | None = None,
    cer_critical_entity: bool | None = None,
    # Impact fields
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    suspected_malicious: bool = False,
    impact_duration_hours: int = 0,
    # LU sector-specific fields (v7)
    sector_specific: dict | None = None,
) -> dict:
    """Assess a single entity's incident: severity + significance + early warning.

    Three-tier routing (v7):
    1. IR entity type → IR thresholds (EU-wide, Arts. 5-14)
    2. LU-covered sector (ms_established=LU) → LU ILR thresholds
    3. All others → NIS2 ML model (qualitative)
    """
    from cyberscale.models.contextual_ir import (
        is_ir_entity, assess_ir_significance, assess_nis2_significance,
    )
    from cyberscale.models.early_warning import recommend_early_warning
    from cyberscale.national.registry import get_national_module

    cross_border = bool(
        ms_affected and any(ms != ms_established for ms in ms_affected)
    )

    # Run Phase 2 contextual model for severity
    contextual_result = clf.predict(
        description, sector,
        ms_established=ms_established, ms_affected=ms_affected,
        score=score, entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
        entity_affected=True,
        service_impact=service_impact, data_impact=data_impact,
        financial_impact=financial_impact, safety_impact=safety_impact,
        affected_persons_count=affected_persons_count,
        suspected_malicious=suspected_malicious,
        impact_duration_hours=impact_duration_hours,
    )

    # Three-tier routing: IR → National → NIS2 ML
    significance = None
    significant_incident = None

    # Tier 1: IR thresholds (EU-wide, takes precedence over national)
    if is_ir_entity(entity_type):
        ir_result = assess_ir_significance(
            entity_type=entity_type,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            safety_impact=safety_impact,
            affected_persons_count=affected_persons_count,
            suspected_malicious=suspected_malicious,
            impact_duration_hours=impact_duration_hours,
            cross_border=cross_border,
        )
        significance = ir_result.to_dict()
        significance["model"] = "ir_thresholds"
        significant_incident = ir_result.significant_incident
        logger.info(
            "entity_incident routing: tier=IR entity_type=%s significant=%s",
            entity_type, ir_result.significant_incident,
        )

    # Tier 2: National thresholds (if available for this MS + sector)
    if significance is None:
        national = get_national_module(ms_established)
        if national is not None:
            is_covered_fn, assess_fn = national
            if is_covered_fn(sector, entity_type):
                nat_result = assess_fn(
                    sector=sector,
                    entity_type=entity_type,
                    service_impact=service_impact,
                    data_impact=data_impact,
                    affected_persons_count=affected_persons_count,
                    financial_impact=financial_impact,
                    safety_impact=safety_impact,
                    impact_duration_hours=impact_duration_hours,
                    cross_border=cross_border,
                    suspected_malicious=suspected_malicious,
                    sector_specific=sector_specific,
                )
                significance = nat_result.to_dict()
                significance["model"] = f"national_{ms_established.lower()}_thresholds"
                significant_incident = nat_result.significant_incident
                logger.info(
                    "entity_incident routing: tier=national_%s sector=%s entity_type=%s significant=%s",
                    ms_established.lower(), sector, entity_type, nat_result.significant_incident,
                )

    # Tier 3: NIS2 ML model (qualitative fallback)
    if significance is None:
        nis2_result = assess_nis2_significance(
            contextual_result, entity_affected=True,
        )
        significance = nis2_result.to_dict()
        significance["model"] = "nis2_ml"
        significant_incident = nis2_result.significant_incident
        logger.info(
            "entity_incident routing: tier=nis2_ml sector=%s entity_type=%s significant=%s",
            sector, entity_type, nis2_result.significant_incident,
        )

    # Early warning recommendation
    early_warning = recommend_early_warning(
        significant_incident=significant_incident,
        suspected_malicious=suspected_malicious,
        cross_border=cross_border,
    )

    out = {
        "severity": contextual_result.severity,
        "confidence": contextual_result.confidence,
        "key_factors": contextual_result.key_factors,
        "sector": sector,
        "entity_type": entity_type,
        "ms_established": ms_established,
        "cross_border": cross_border,
        "significance": significance,
        "early_warning": early_warning.to_dict(),
    }
    if ms_affected:
        out["ms_affected"] = ms_affected

    return out


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_entity_incident(
        description: str,
        sector: str,
        entity_type: str,
        ms_established: str = "EU",
        ms_affected: list[str] | None = None,
        severity_score: float | None = None,
        cer_critical_entity: bool | None = None,
        service_impact: str = "none",
        data_impact: str = "none",
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
        suspected_malicious: bool = False,
        impact_duration_hours: int = 0,
        sector_specific: dict | None = None,
    ) -> dict:
        """Assess a single entity's incident: contextual severity + significant incident determination + early warning recommendation.

        Three-tier routing (v7):
        1. IR entity types → IR quantitative thresholds (EU-wide, Arts. 5-14)
        2. LU-covered sectors (ms_established=LU) → LU ILR national thresholds
        3. All others → NIS2 ML model (qualitative)

        sector_specific: Optional dict with sector-specific fields for LU thresholds
        (e.g., pods_affected, voltage_level, trains_cancelled_pct, scada_unavailable_min).
        Only used when ms_established=LU and entity falls under LU ILR coverage.
        """
        from cyberscale.models.contextual import VALID_SECTORS, VALID_ENTITY_TYPES

        if sector not in VALID_SECTORS:
            return {"error": f"Unknown sector: {sector}. Valid: {sorted(VALID_SECTORS)}"}
        if entity_type not in VALID_ENTITY_TYPES:
            return {"error": f"Unknown entity_type: {entity_type}. See nis2_entity_types.json."}

        clf = _get_classifier()
        if clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/contextual/."}

        return _assess_entity_incident(
            clf, description, sector, entity_type,
            ms_established=ms_established, ms_affected=ms_affected,
            score=severity_score, cer_critical_entity=cer_critical_entity,
            service_impact=service_impact, data_impact=data_impact,
            financial_impact=financial_impact, safety_impact=safety_impact,
            affected_persons_count=affected_persons_count,
            suspected_malicious=suspected_malicious,
            impact_duration_hours=impact_duration_hours,
            sector_specific=sector_specific,
        )
