"""Phase 3 MCP tool — Authority-facing incident classification.

Provides assess_incident: list of entity notifications → aggregation →
deterministic T-level + deterministic O-level → Blueprint matrix → classification.

v5: Fully deterministic — no ML models needed for Phase 3.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Internal helper (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_incident(
    description: str,
    entity_notifications: list[dict],
) -> dict:
    """Full authority classification pipeline (fully deterministic).

    1. Aggregate entity notifications → worst-case impacts
    2. Deterministic T-level from aggregated technical impact
    3. Deterministic O-level from aggregated operational/consequence fields
    4. Blueprint matrix lookup (T x O)
    5. Return structured result for authority review
    """
    from cyberscale.aggregation import aggregate_entity_notifications
    from cyberscale.matrix.dual_scale import classify_incident

    # Step 1: Aggregation (includes T-level and O-level derivation)
    agg = aggregate_entity_notifications(entity_notifications)

    # Step 2: Matrix lookup
    matrix = classify_incident(agg.t_level, agg.o_level)

    return {
        "aggregation": agg.to_dict(),
        "technical": {
            "level": agg.t_level,
            "basis": agg.t_basis,
            "source": "deterministic",
        },
        "operational": {
            "level": agg.o_level,
            "basis": agg.o_basis,
            "source": "deterministic",
        },
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
    ) -> dict:
        """Authority-facing incident classification: aggregates entity notifications,
        derives deterministic T-level and O-level, and produces Blueprint matrix
        classification with coordination level.

        Fully deterministic — no ML models required.

        Each entity_notification dict should contain:
        - sector, ms_established, ms_affected (list)
        - service_impact, data_impact, financial_impact, safety_impact
        - affected_persons_count, suspected_malicious, impact_duration_hours

        The authority reviews all suggested values before final classification.
        """
        if not entity_notifications:
            return {"error": "At least one entity notification is required."}

        return _assess_incident(description, entity_notifications)
