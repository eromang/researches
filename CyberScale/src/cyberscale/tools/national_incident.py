"""Phase 3a MCP tool — National CSIRT incident classification.

Provides assess_national_incident: entity notifications from a single MS →
scoped aggregation → deterministic T/O levels → Blueprint matrix.

This is the national-level classification for a single member state's CSIRT.
Cross-border flag triggers CSIRT Network sharing (Art. 15) and Phase 3b.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Internal helpers (testable without MCP)
# ---------------------------------------------------------------------------


def _validate_single_ms(notifications: list[dict]) -> tuple[bool, str, str]:
    """Validate all entities are established in the same MS.

    Returns (ok, ms_established, error_message).
    """
    ms_values = set()
    for n in notifications:
        ms = n.get("ms_established")
        if ms:
            ms_values.add(ms)

    if not ms_values:
        return False, "", "No ms_established found in notifications"
    if len(ms_values) > 1:
        return False, "", (
            f"National assessment requires single MS, got {sorted(ms_values)}. "
            "Use assess_eu_incident for multi-MS incidents."
        )
    return True, ms_values.pop(), ""


def _assess_national_incident(
    description: str,
    entity_notifications: list[dict],
) -> dict:
    """National CSIRT classification (single MS, fully deterministic).

    1. Validate all entities share ms_established
    2. Aggregate entity notifications (scoped to this MS)
    3. Deterministic T-level and O-level
    4. Blueprint matrix lookup
    5. Determine cross-border flag for CSIRT Network sharing
    """
    from cyberscale.aggregation import aggregate_entity_notifications
    from cyberscale.matrix.dual_scale import classify_incident

    # Validate single MS
    ok, ms_established, err = _validate_single_ms(entity_notifications)
    if not ok:
        return {"error": err}

    # Aggregation
    agg = aggregate_entity_notifications(entity_notifications)

    # Matrix
    matrix = classify_incident(agg.t_level, agg.o_level)

    # Cross-border: any entity reports ms_affected with different MS
    cross_border = agg.ms_affected > 1

    return {
        "ms_established": ms_established,
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
        "cross_border": cross_border,
        "csirt_network_sharing": cross_border,
        "entity_count": len(entity_notifications),
    }


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_national_incident(
        description: str,
        entity_notifications: list[dict],
    ) -> dict:
        """National CSIRT incident classification (Phase 3a).

        Aggregates entity notifications from a single member state,
        derives deterministic T-level and O-level, and produces Blueprint
        matrix classification.

        All entities must share the same ms_established value.
        If cross-border impact is detected, csirt_network_sharing=true
        signals that this should be shared via the CSIRT Network (Art. 15)
        for Phase 3b EU-level assessment.

        Fully deterministic — no ML models required.
        """
        if not entity_notifications:
            return {"error": "At least one entity notification is required."}

        return _assess_national_incident(description, entity_notifications)
