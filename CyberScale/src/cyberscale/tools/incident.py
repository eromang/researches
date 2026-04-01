"""Phase 3 MCP tools — Fully deterministic incident classification.

v5: Both T-level and O-level are derived deterministically from structured
fields. No ML models needed for Phase 3 — pure rules + matrix lookup.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Internal helper functions (testable without MCP)
# ---------------------------------------------------------------------------


def _classify_full(
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
    """Full classification: deterministic T-level + deterministic O-level + Blueprint matrix."""
    from cyberscale.aggregation import derive_t_level, derive_o_level
    from cyberscale.matrix.dual_scale import classify_incident

    t_level, t_basis = derive_t_level(
        service_impact, data_impact, cascading, affected_entities,
    )
    o_level, o_basis = derive_o_level(
        cross_border_pattern, capacity_exceeded, entity_relevance,
        ms_affected, sectors_affected, financial_impact, safety_impact,
        affected_persons_count, affected_entities,
    )

    matrix_result = classify_incident(t_level, o_level)

    result = {
        "technical": {
            "level": t_level,
            "basis": t_basis,
            "source": "deterministic",
        },
        "operational": {
            "level": o_level,
            "basis": o_basis,
            "source": "deterministic",
        },
        "classification": matrix_result.classification,
        "label": matrix_result.label,
        "provision": matrix_result.provision,
    }

    # Cross-model consistency warnings
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
        """Full incident classification: deterministic T-level + deterministic O-level + Blueprint matrix.

        Fully deterministic — no ML models required. Both T-level and O-level
        are derived from structured impact and operational fields.
        """
        return _classify_full(
            description, service_impact, affected_entities,
            sectors_affected, cascading, data_impact, entity_relevance,
            ms_affected, cross_border_pattern, capacity_exceeded,
            financial_impact, safety_impact, affected_persons_count,
        )
