"""Phase 3 MCP tools — Incident dual-scale classification with model integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_t_classifier = None
_o_classifier = None
_t_model_path = Path("data/models/technical")
_o_model_path = Path("data/models/operational")


def _get_t_classifier():
    global _t_classifier
    if _t_classifier is None:
        if not _t_model_path.exists():
            return None
        from cyberscale.models.technical import TechnicalClassifier
        _t_classifier = TechnicalClassifier(model_path=_t_model_path)
    return _t_classifier


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


def _classify_technical(
    clf,
    description: str,
    service_impact: str,
    affected_entities: int,
    sectors_affected: int,
    cascading: str,
    data_impact: str,
) -> dict:
    """Classify technical severity using the T-model."""
    result = clf.predict(
        description,
        service_impact=service_impact,
        affected_entities=affected_entities,
        sectors_affected=sectors_affected,
        cascading=cascading,
        data_impact=data_impact,
    )
    return result.to_dict()


def _classify_operational(
    clf,
    description: str,
    sectors_affected: int,
    entity_relevance: str,
    ms_affected: int,
    cross_border_pattern: str,
    capacity_exceeded: bool,
) -> dict:
    """Classify operational severity using the O-model."""
    result = clf.predict(
        description,
        sectors_affected=sectors_affected,
        entity_relevance=entity_relevance,
        ms_affected=ms_affected,
        cross_border_pattern=cross_border_pattern,
        capacity_exceeded=capacity_exceeded,
    )
    return result.to_dict()


def _classify_full(
    t_clf,
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
) -> dict:
    """Full classification: T-level + O-level + Blueprint matrix lookup."""
    t_result = _classify_technical(
        t_clf, description, service_impact, affected_entities,
        sectors_affected, cascading, data_impact,
    )
    o_result = _classify_operational(
        o_clf, description, sectors_affected, entity_relevance,
        ms_affected, cross_border_pattern,
        capacity_exceeded,
    )

    from cyberscale.matrix.dual_scale import classify_incident
    matrix_result = classify_incident(t_result["level"], o_result["level"])

    result = {
        "technical": t_result,
        "operational": o_result,
        "classification": matrix_result.classification,
        "label": matrix_result.label,
        "provision": matrix_result.provision,
    }

    # Cross-model consistency warnings for extreme asymmetric results
    t_level = t_result["level"]
    o_level = o_result["level"]
    warnings = []
    if t_level == "T4" and o_level == "O1":
        warnings.append(
            "Asymmetric result: maximum technical severity (T4) with minimum "
            "operational impact (O1). Verify that operational fields accurately "
            "reflect coordination needs and cross-border impact."
        )
    if t_level == "T1" and o_level == "O4":
        warnings.append(
            "Asymmetric result: minimum technical severity (T1) with maximum "
            "operational impact (O4). Verify that technical fields accurately "
            "reflect service disruption and data compromise."
        )
    if warnings:
        result["warnings"] = warnings

    return result


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def classify_incident_technical(
        description: str,
        service_impact: str = "partial",
        affected_entities: int = 1,
        sectors_affected: int = 1,
        cascading: str = "none",
        data_impact: str = "none",
    ) -> dict:
        """Classify incident technical severity (T1-T4)."""
        clf = _get_t_classifier()
        if clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/technical/."}
        return _classify_technical(
            clf, description, service_impact, affected_entities,
            sectors_affected, cascading, data_impact,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    def classify_incident_operational(
        description: str,
        sectors_affected: int = 1,
        entity_relevance: str = "non_essential",
        ms_affected: int = 1,
        cross_border_pattern: str = "none",
        capacity_exceeded: bool = False,
    ) -> dict:
        """Classify incident operational severity (O1-O4)."""
        clf = _get_o_classifier()
        if clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/operational/."}
        return _classify_operational(
            clf, description, sectors_affected, entity_relevance,
            ms_affected, cross_border_pattern,
            capacity_exceeded,
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
    ) -> dict:
        """Full incident classification: T-level + O-level + Blueprint matrix result."""
        t_clf = _get_t_classifier()
        if t_clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/technical/."}
        o_clf = _get_o_classifier()
        if o_clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/operational/."}
        return _classify_full(
            t_clf, o_clf, description, service_impact, affected_entities,
            sectors_affected, cascading, data_impact, entity_relevance,
            ms_affected, cross_border_pattern,
            capacity_exceeded,
        )
