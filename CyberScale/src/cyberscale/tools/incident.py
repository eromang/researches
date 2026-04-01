"""Phase 3 MCP tools — Incident classification with deterministic T-level + O-model.

v4: T-level is now derived deterministically from aggregated impact fields
via the aggregation layer. The TechnicalClassifier ML model is deprecated
for inference — its training data generation rules are preserved in
aggregation.derive_t_level() for consistency.
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
# Internal helper functions (testable without MCP)
# ---------------------------------------------------------------------------


def _classify_operational(
    clf,
    description: str,
    sectors_affected: int,
    entity_relevance: str,
    ms_affected: int,
    cross_border_pattern: str,
    capacity_exceeded: bool,
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    affected_entities: int = 1,
) -> dict:
    """Classify operational severity using the O-model."""
    result = clf.predict(
        description,
        sectors_affected=sectors_affected,
        entity_relevance=entity_relevance,
        ms_affected=ms_affected,
        cross_border_pattern=cross_border_pattern,
        capacity_exceeded=capacity_exceeded,
        financial_impact=financial_impact,
        safety_impact=safety_impact,
        affected_persons_count=affected_persons_count,
        affected_entities=affected_entities,
    )
    return result.to_dict()


def _classify_full(
    o_clf,
    description: str,
    service_impact: str,
    affected_entities: int,
    sectors_affected: int,
    cascading: str,
    data_impact: str,
    entity_relevance: str,
    ms_affected: int,
    cross_border_pattern: str,
    capacity_exceeded: bool,
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
) -> dict:
    """Full classification: deterministic T-level + O-model + Blueprint matrix."""
    from cyberscale.aggregation import derive_t_level
    from cyberscale.matrix.dual_scale import classify_incident

    # Deterministic T-level
    t_level, t_basis = derive_t_level(
        service_impact, data_impact, cascading, affected_entities,
    )

    o_result = _classify_operational(
        o_clf, description, sectors_affected, entity_relevance,
        ms_affected, cross_border_pattern, capacity_exceeded,
        financial_impact, safety_impact, affected_persons_count,
        affected_entities,
    )

    matrix_result = classify_incident(t_level, o_result["level"])

    result = {
        "technical": {
            "level": t_level,
            "basis": t_basis,
            "source": "deterministic",
        },
        "operational": o_result,
        "classification": matrix_result.classification,
        "label": matrix_result.label,
        "provision": matrix_result.provision,
    }

    # Cross-model consistency warnings
    o_level = o_result["level"]
    warnings = []
    if t_level == "T4" and o_level == "O1":
        warnings.append(
            "Asymmetric result: maximum technical severity (T4) with minimum "
            "operational impact (O1). Verify operational fields."
        )
    if t_level == "T1" and o_level == "O4":
        warnings.append(
            "Asymmetric result: minimum technical severity (T1) with maximum "
            "operational impact (O4). Verify technical fields."
        )
    if warnings:
        result["warnings"] = warnings

    return result


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def classify_incident_operational(
        description: str,
        sectors_affected: int = 1,
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        capacity_exceeded: bool = False,
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
        affected_entities: int = 1,
    ) -> dict:
        """Classify incident operational severity (O1-O4)."""
        clf = _get_o_classifier()
        if clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/operational/."}
        return _classify_operational(
            clf, description, sectors_affected, entity_relevance,
            ms_affected, cross_border_pattern, capacity_exceeded,
            financial_impact, safety_impact, affected_persons_count,
            affected_entities,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    def classify_incident(
        description: str,
        service_impact: str = "partial",
        affected_entities: int = 1,
        sectors_affected: int = 1,
        cascading: str = "none",
        data_impact: str = "none",
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        capacity_exceeded: bool = False,
        financial_impact: str = "none",
        safety_impact: str = "none",
        affected_persons_count: int = 0,
    ) -> dict:
        """Full incident classification: deterministic T-level + O-model + Blueprint matrix.

        T-level is now derived deterministically from service_impact, data_impact,
        cascading, and affected_entities (no ML model required).
        """
        o_clf = _get_o_classifier()
        if o_clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/operational/."}
        return _classify_full(
            o_clf, description, service_impact, affected_entities,
            sectors_affected, cascading, data_impact, entity_relevance,
            ms_affected, cross_border_pattern, capacity_exceeded,
            financial_impact, safety_impact, affected_persons_count,
        )
