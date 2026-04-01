"""Phase 3b MCP tool — EU-CyCLONe incident classification.

Provides assess_eu_incident: national classifications from multiple MS +
CyCLONe Officer situational inputs → EU-level classification + coordination.

CyCLONe Officer inputs can escalate (never de-escalate) the mechanical result.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# CyCLONe Officer escalation logic
# ---------------------------------------------------------------------------

VALID_POLITICAL_SENSITIVITY = {"none", "elevated", "high"}
VALID_CAPACITY_STATUS = {"normal", "strained", "overwhelmed"}
VALID_COORDINATION_NEEDS = {"national", "eu_info", "eu_active", "full_ipcr"}
VALID_ESCALATION_REC = {"none", "escalate", "de-escalate"}

_O_LEVEL_ORDER = {"O1": 1, "O2": 2, "O3": 3, "O4": 4}
_O_LEVEL_FROM_NUM = {1: "O1", 2: "O2", 3: "O3", 4: "O4"}


def aggregate_cyclone_officers(
    officer_inputs: list[dict],
    base_o_level: str,
) -> tuple[str, list[str]]:
    """Aggregate CyCLONe Officer inputs into EU O-level adjustment.

    Returns (adjusted_o_level, escalation_reasons).
    Can only escalate, never de-escalate below base_o_level.
    """
    escalation_steps = 0
    reasons = []

    # Capacity status
    capacity_statuses = [o.get("national_capacity_status", "normal") for o in officer_inputs]
    if "overwhelmed" in capacity_statuses:
        escalation_steps += 1
        n = capacity_statuses.count("overwhelmed")
        reasons.append(f"{n} MS capacity overwhelmed")
    elif capacity_statuses.count("strained") >= 2:
        escalation_steps += 1
        n = capacity_statuses.count("strained")
        reasons.append(f"{n} MS capacity strained")

    # Political sensitivity
    sensitivities = [o.get("political_sensitivity", "none") for o in officer_inputs]
    if "high" in sensitivities:
        escalation_steps += 1
        reasons.append("high political sensitivity")

    # Explicit escalation request
    recommendations = [o.get("escalation_recommendation", "none") for o in officer_inputs]
    if "escalate" in recommendations:
        escalation_steps += 1
        n = recommendations.count("escalate")
        reasons.append(f"{n} MS requesting escalation")

    # Apply (capped at +2, O4 max)
    escalation_steps = min(escalation_steps, 2)
    base_num = _O_LEVEL_ORDER.get(base_o_level, 1)
    adjusted_num = min(base_num + escalation_steps, 4)
    adjusted = _O_LEVEL_FROM_NUM[adjusted_num]

    return adjusted, reasons


def _aggregate_national_to_eu(
    national_classifications: list[dict],
) -> tuple[str, str, list[str]]:
    """Aggregate national T/O levels into EU-level base classification.

    Takes worst-case T and O across all national assessments.
    Returns (eu_t_level, eu_o_level, basis).

    Additional EU-level escalation: significant in 3+ MS → large_scale minimum.
    """
    if not national_classifications:
        raise ValueError("At least one national classification is required")

    t_nums = []
    o_nums = []
    ms_list = []
    basis = []

    for nc in national_classifications:
        t = nc.get("technical", {}).get("level", "T1")
        o = nc.get("operational", {}).get("level", "O1")
        ms = nc.get("ms_established", "??")
        t_nums.append(int(t[1]))
        o_nums.append(int(o[1]))
        ms_list.append(ms)

    eu_t = f"T{max(t_nums)}"
    eu_o = f"O{max(o_nums)}"
    basis.append(f"worst-case across {len(national_classifications)} national assessments")

    # EU escalation: significant (>=O2) in 3+ MS → minimum large_scale (O3)
    significant_ms = sum(1 for n in o_nums if n >= 2)
    if significant_ms >= 3 and max(o_nums) < 3:
        eu_o = "O3"
        basis.append(f"significant in {significant_ms} MS → EU-level O3 escalation")

    return eu_t, eu_o, basis


# ---------------------------------------------------------------------------
# Internal helper (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_eu_incident(
    description: str,
    national_classifications: list[dict],
    cyclone_officer_inputs: list[dict] | None = None,
) -> dict:
    """EU-CyCLONe classification (Phase 3b).

    1. Aggregate national classifications (worst-case T/O)
    2. Apply EU-level escalation rules
    3. Apply CyCLONe Officer escalation overrides
    4. Blueprint matrix lookup
    """
    from cyberscale.matrix.dual_scale import classify_incident

    # Step 1-2: Aggregate nationals
    eu_t, eu_o_base, agg_basis = _aggregate_national_to_eu(national_classifications)

    # Step 3: CyCLONe Officer escalation
    officer_reasons = []
    if cyclone_officer_inputs:
        eu_o_final, officer_reasons = aggregate_cyclone_officers(
            cyclone_officer_inputs, eu_o_base,
        )
    else:
        eu_o_final = eu_o_base

    # Step 4: Matrix
    matrix = classify_incident(eu_t, eu_o_final)

    # Coordination level from O-level
    coordination_map = {
        "O1": "national",
        "O2": "eu_info",
        "O3": "eu_active",
        "O4": "full_ipcr",
    }

    # Collect MS info
    ms_list = [nc.get("ms_established", "??") for nc in national_classifications]

    # Collect intelligence context from officers
    intel_context = []
    if cyclone_officer_inputs:
        for oi in cyclone_officer_inputs:
            ctx = oi.get("intelligence_context", "")
            if ctx:
                ms = oi.get("ms", "??")
                intel_context.append({"ms": ms, "context": ctx})

    result = {
        "eu_technical": {
            "level": eu_t,
            "source": "worst-case across national assessments",
        },
        "eu_operational": {
            "level": eu_o_final,
            "base_level": eu_o_base,
            "officer_escalation": eu_o_final != eu_o_base,
            "officer_reasons": officer_reasons,
            "source": "national aggregation + CyCLONe Officer overrides",
        },
        "classification": matrix.classification,
        "label": matrix.label,
        "provision": matrix.provision,
        "coordination_level": coordination_map.get(eu_o_final, "national"),
        "ms_involved": ms_list,
        "national_count": len(national_classifications),
        "aggregation_basis": agg_basis,
    }

    if intel_context:
        result["intelligence_briefing"] = intel_context

    return result


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_eu_incident(
        description: str,
        national_classifications: list[dict],
        cyclone_officer_inputs: list[dict] | None = None,
    ) -> dict:
        """EU-CyCLONe incident classification (Phase 3b).

        Aggregates national CSIRT classifications from multiple member states,
        applies EU-level escalation rules, and incorporates CyCLONe Officer
        situational inputs for final EU classification.

        national_classifications: list of Phase 3a outputs (from assess_national_incident).
        cyclone_officer_inputs: optional list of per-MS officer inputs with:
          - political_sensitivity (none/elevated/high)
          - national_capacity_status (normal/strained/overwhelmed)
          - coordination_needs (national/eu_info/eu_active/full_ipcr)
          - intelligence_context (free text)
          - escalation_recommendation (none/escalate/de-escalate)

        Officer inputs can escalate (never de-escalate) the mechanical result.
        """
        if not national_classifications:
            return {"error": "At least one national classification is required."}

        return _assess_eu_incident(
            description, national_classifications,
            cyclone_officer_inputs=cyclone_officer_inputs,
        )
