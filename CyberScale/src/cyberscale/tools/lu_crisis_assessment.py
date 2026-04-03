"""HCPN national crisis qualification MCP tools.

Provides two tools:
- assess_lu_crisis_incident: Qualify incident against HCPN criteria
- assess_lu_crisis_threat: Qualify cyber threat against HCPN criteria

These are authority-level tools scoped to IMPACT ON LUXEMBOURG regardless
of entity establishment. They operate ABOVE entity significance — an event
may meet NIS2 notification thresholds without qualifying for the national
crisis plan, and vice versa.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Internal helpers (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_lu_crisis_incident(
    description: str,
    sectors_affected: list[str],
    entity_types: list[str],
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    suspected_malicious: bool = False,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> dict:
    """Assess incident against HCPN national crisis qualification criteria."""
    from cyberscale.national.lu_crisis import qualify_hcpn_incident

    result = qualify_hcpn_incident(
        sectors_affected=sectors_affected,
        entity_types=entity_types,
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        capacity_exceeded=capacity_exceeded,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
        suspected_malicious=suspected_malicious,
        coordination_required=coordination_required,
        urgent_decisions_required=urgent_decisions_required,
        prejudice_actual=prejudice_actual,
    )
    return result.to_dict()


def _assess_lu_crisis_threat(
    description: str,
    sectors_affected: list[str],
    entity_types: list[str],
    threat_probability: str,
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> dict:
    """Assess cyber threat against HCPN national crisis qualification criteria."""
    from cyberscale.national.lu_crisis import qualify_hcpn_threat

    result = qualify_hcpn_threat(
        sectors_affected=sectors_affected,
        entity_types=entity_types,
        threat_probability=threat_probability,
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        capacity_exceeded=capacity_exceeded,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
        coordination_required=coordination_required,
        urgent_decisions_required=urgent_decisions_required,
        prejudice_actual=prejudice_actual,
    )
    return result.to_dict()


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_lu_crisis_incident(
        description: str,
        sectors_affected: list[str],
        entity_types: list[str],
        safety_impact: str = "none",
        service_impact: str = "none",
        data_impact: str = "none",
        financial_impact: str = "none",
        affected_persons_count: int = 0,
        cross_border: bool = False,
        capacity_exceeded: bool = False,
        threat_actor_type: str | None = None,
        sensitive_data_type: str | None = None,
        suspected_malicious: bool = False,
        coordination_required: bool | None = None,
        urgent_decisions_required: bool | None = None,
        prejudice_actual: bool = False,
    ) -> dict:
        """HCPN national crisis qualification for incidents (Luxembourg).

        Determines whether a cyber incident triggers the PGGCCN national
        crisis plan and which cooperation mode applies.

        Scoped to IMPACT ON LUXEMBOURG — the entity causing the incident
        may be established in any Member State.

        Three cumulative criteria must be met:
        1. At least one essential service affected (CER reference list)
        2. Prejudice to vital interests (7 sub-criteria, at least 1)
        3. Coordination AND decision urgency (both required)

        Fast-track: malicious unauthorized access with grave operational
        disruption bypasses Criterion 2.

        Qualification level:
        - cross_border OR capacity_exceeded -> large_scale_cybersecurity_incident
        - otherwise -> national_major_incident

        Cooperation mode:
        - prejudice_actual=true -> Crise
        - prejudice_actual=false -> Alerte/CERC
        """
        return _assess_lu_crisis_incident(
            description=description,
            sectors_affected=sectors_affected,
            entity_types=entity_types,
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            capacity_exceeded=capacity_exceeded,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
            suspected_malicious=suspected_malicious,
            coordination_required=coordination_required,
            urgent_decisions_required=urgent_decisions_required,
            prejudice_actual=prejudice_actual,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_lu_crisis_threat(
        description: str,
        sectors_affected: list[str],
        entity_types: list[str],
        threat_probability: str,
        safety_impact: str = "none",
        service_impact: str = "none",
        data_impact: str = "none",
        financial_impact: str = "none",
        affected_persons_count: int = 0,
        cross_border: bool = False,
        capacity_exceeded: bool = False,
        threat_actor_type: str | None = None,
        sensitive_data_type: str | None = None,
        coordination_required: bool | None = None,
        urgent_decisions_required: bool | None = None,
        prejudice_actual: bool = False,
    ) -> dict:
        """HCPN national crisis qualification for cyber threats (Luxembourg).

        Four cumulative criteria:
        1. Essential service targeted
        2. Probability of materialisation (High or Imminent only)
        3. Potential prejudice to vital interests (7 sub-criteria)
        4. Coordination AND decision urgency

        threat_probability: "low" | "moderate" | "high" | "imminent"
        """
        return _assess_lu_crisis_threat(
            description=description,
            sectors_affected=sectors_affected,
            entity_types=entity_types,
            threat_probability=threat_probability,
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            capacity_exceeded=capacity_exceeded,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
            coordination_required=coordination_required,
            urgent_decisions_required=urgent_decisions_required,
            prejudice_actual=prejudice_actual,
        )
