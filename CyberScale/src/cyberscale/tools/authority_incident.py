"""Phase 3 MCP tool — Authority-facing incident classification.

Provides assess_incident: list of entity notifications → aggregation →
deterministic T-level → O-model → Blueprint matrix → classification.

This is the full authority pipeline for CSIRT Network / EU-CyCLONe use.
"""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_o_classifier = None
_o_model_path = Path("data/models/operational")


def _get_o_classifier():
    global _o_classifier
    if _o_classifier is None:
        if not _o_model_path.exists():
            return None
        from cyberscale.models.operational import OperationalClassifier
        _o_classifier = OperationalClassifier(model_path=_o_model_path)
    return _o_classifier


# ---------------------------------------------------------------------------
# Internal helper (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_incident(
    o_clf,
    description: str,
    entity_notifications: list[dict],
    entity_relevance: str = "essential",
) -> dict:
    """Full authority classification pipeline.

    1. Aggregate entity notifications → worst-case impacts + deterministic T-level
    2. O-model prediction using aggregated fields
    3. Blueprint matrix lookup (T x O)
    4. Return structured result for authority review
    """
    from cyberscale.aggregation import aggregate_entity_notifications
    from cyberscale.matrix.dual_scale import classify_incident

    # Step 1: Aggregation
    agg = aggregate_entity_notifications(entity_notifications)

    # Step 2: O-model prediction
    o_result = o_clf.predict(
        description,
        sectors_affected=agg.sectors_affected,
        entity_relevance=entity_relevance,
        ms_affected=agg.ms_affected,
        cross_border_pattern=agg.cross_border_pattern,
        capacity_exceeded=agg.capacity_exceeded,
        financial_impact=agg.financial_impact,
        safety_impact=agg.safety_impact,
        affected_persons_count=agg.affected_persons_count,
        affected_entities=agg.affected_entities,
    )

    # Step 3: Matrix lookup
    matrix = classify_incident(agg.t_level, o_result.level)

    return {
        "aggregation": agg.to_dict(),
        "technical": {
            "level": agg.t_level,
            "basis": agg.t_basis,
            "source": "deterministic_aggregation",
        },
        "operational": o_result.to_dict(),
        "classification": matrix.classification,
        "label": matrix.label,
        "provision": matrix.provision,
        "entity_count": len(entity_notifications),
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_incident(
        description: str,
        entity_notifications: list[dict],
        entity_relevance: str = "essential",
    ) -> dict:
        """Authority-facing incident classification: aggregates entity notifications,
        derives deterministic T-level, runs O-model, and produces Blueprint matrix
        classification with coordination level.

        Each entity_notification dict should contain:
        - sector, ms_established, ms_affected (list)
        - service_impact, data_impact, financial_impact, safety_impact
        - affected_persons_count, suspected_malicious, impact_duration_hours

        The authority reviews all suggested values before final classification.
        """
        if not entity_notifications:
            return {"error": "At least one entity notification is required."}

        o_clf = _get_o_classifier()
        if o_clf is None:
            return {"error": "No trained O-model available. Deploy to data/models/operational/."}

        return _assess_incident(
            o_clf, description, entity_notifications,
            entity_relevance=entity_relevance,
        )
