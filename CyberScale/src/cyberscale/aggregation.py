"""Multi-entity incident aggregation layer.

Aggregates entity notification dicts (Phase 2 incident mode outputs) into
a single incident-level summary for authority-facing classification.

Produces:
- Worst-case impact fields (service, data, financial, safety)
- Sum of affected_persons_count
- Counts: affected_entities, sectors_affected, ms_affected
- Derived: cascading, cross_border_pattern, capacity_exceeded
- Deterministic T-level from aggregated technical impact
"""

from __future__ import annotations

from dataclasses import dataclass, field


# Ordered severity scales for worst-case selection
_SERVICE_IMPACT_ORDER = {"none": 0, "partial": 1, "degraded": 2, "unavailable": 3, "sustained": 4}
_DATA_IMPACT_ORDER = {"none": 0, "accessed": 1, "exfiltrated": 2, "compromised": 3, "systemic": 4}
_FINANCIAL_IMPACT_ORDER = {"none": 0, "minor": 1, "significant": 2, "severe": 3}
_SAFETY_IMPACT_ORDER = {"none": 0, "health_risk": 1, "health_damage": 2, "death": 3}


def _worst_case(values: list[str], order: dict[str, int]) -> str:
    """Return the worst-case value from a list using the severity ordering."""
    if not values:
        return list(order.keys())[0]  # "none"
    return max(values, key=lambda v: order.get(v, 0))


def _derive_cascading(sectors_affected: int) -> str:
    """Derive cascading level from number of sectors affected."""
    if sectors_affected >= 5:
        return "uncontrolled"
    if sectors_affected >= 3:
        return "cross_sector"
    if sectors_affected >= 2:
        return "limited"
    return "none"


def _derive_cross_border_pattern(ms_affected: int) -> str:
    """Derive cross-border pattern from number of member states."""
    if ms_affected >= 6:
        return "systemic"
    if ms_affected >= 3:
        return "significant"
    if ms_affected >= 2:
        return "limited"
    return "none"


def _derive_capacity_exceeded(
    affected_entities: int,
    sectors_affected: int,
    ms_affected: int,
    safety_impact: str,
) -> bool:
    """Heuristic: national capacity likely exceeded when scale is large."""
    if affected_entities >= 50 and sectors_affected >= 3:
        return True
    if ms_affected >= 5:
        return True
    if safety_impact in ("health_damage", "death") and affected_entities >= 10:
        return True
    return False


def derive_t_level(
    service_impact: str,
    data_impact: str,
    cascading: str,
    affected_entities: int,
) -> tuple[str, list[str]]:
    """Deterministic T-level from aggregated impact fields.

    Returns (t_level, basis) where basis lists the triggering rules.
    Rules mirror generate_incidents.py assign_t_level.
    """
    basis = []

    # T4: sustained OR systemic data OR (unavailable + uncontrolled)
    if service_impact == "sustained":
        basis.append("sustained service impact")
        return "T4", basis
    if data_impact == "systemic":
        basis.append("systemic data impact")
        return "T4", basis
    if service_impact == "unavailable" and cascading == "uncontrolled":
        basis.append("unavailable service + uncontrolled cascading")
        return "T4", basis

    # T3: unavailable OR exfiltrated OR cross_sector cascading OR entities > 50
    if service_impact == "unavailable":
        basis.append("unavailable service impact")
        return "T3", basis
    if data_impact == "exfiltrated":
        basis.append("exfiltrated data impact")
        return "T3", basis
    if cascading == "cross_sector":
        basis.append("cross-sector cascading")
        return "T3", basis
    if affected_entities > 50:
        basis.append(f"{affected_entities} entities affected")
        return "T3", basis

    # T2: degraded OR accessed/compromised OR limited cascading OR entities > 10
    if service_impact == "degraded":
        basis.append("degraded service impact")
        return "T2", basis
    if data_impact in ("accessed", "compromised"):
        basis.append(f"{data_impact} data impact")
        return "T2", basis
    if cascading == "limited":
        basis.append("limited cascading")
        return "T2", basis
    if affected_entities > 10:
        basis.append(f"{affected_entities} entities affected")
        return "T2", basis

    # T1
    basis.append("below escalation thresholds")
    return "T1", basis


@dataclass
class AggregationResult:
    """Result of multi-entity incident aggregation."""

    # Aggregated impact fields
    service_impact: str
    data_impact: str
    financial_impact: str
    safety_impact: str
    affected_persons_count: int
    affected_entities: int
    sectors_affected: int
    ms_affected: int

    # Derived fields
    cascading: str
    cross_border_pattern: str
    capacity_exceeded: bool

    # Deterministic T-level
    t_level: str
    t_basis: list[str]

    # Sector and MS lists for transparency
    sector_list: list[str] = field(default_factory=list)
    ms_list: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "service_impact": self.service_impact,
            "data_impact": self.data_impact,
            "financial_impact": self.financial_impact,
            "safety_impact": self.safety_impact,
            "affected_persons_count": self.affected_persons_count,
            "affected_entities": self.affected_entities,
            "sectors_affected": self.sectors_affected,
            "ms_affected": self.ms_affected,
            "cascading": self.cascading,
            "cross_border_pattern": self.cross_border_pattern,
            "capacity_exceeded": self.capacity_exceeded,
            "t_level": self.t_level,
            "t_basis": self.t_basis,
            "sector_list": self.sector_list,
            "ms_list": self.ms_list,
        }


def aggregate_entity_notifications(notifications: list[dict]) -> AggregationResult:
    """Aggregate a list of entity notification dicts into incident-level summary.

    Each notification dict is expected to have the structure from
    assess_entity_incident output or a compatible dict with:
    - sector, entity_type, ms_established
    - ms_affected (list[str], optional)
    - severity, significance, early_warning (from Phase 2)

    Plus optional impact fields from the entity's report:
    - service_impact, data_impact, financial_impact, safety_impact
    - affected_persons_count, suspected_malicious, impact_duration_hours
    """
    if not notifications:
        raise ValueError("At least one entity notification is required")

    # Collect values across all entities
    service_impacts = []
    data_impacts = []
    financial_impacts = []
    safety_impacts = []
    total_persons = 0
    sectors = set()
    ms_set = set()

    for n in notifications:
        service_impacts.append(n.get("service_impact", "none"))
        data_impacts.append(n.get("data_impact", "none"))
        financial_impacts.append(n.get("financial_impact", "none"))
        safety_impacts.append(n.get("safety_impact", "none"))
        total_persons += n.get("affected_persons_count", 0)

        if "sector" in n:
            sectors.add(n["sector"])
        if "ms_established" in n:
            ms_set.add(n["ms_established"])
        for ms in n.get("ms_affected", []):
            ms_set.add(ms)

    # Worst-case aggregation
    svc = _worst_case(service_impacts, _SERVICE_IMPACT_ORDER)
    data = _worst_case(data_impacts, _DATA_IMPACT_ORDER)
    fin = _worst_case(financial_impacts, _FINANCIAL_IMPACT_ORDER)
    safety = _worst_case(safety_impacts, _SAFETY_IMPACT_ORDER)

    affected_entities = len(notifications)
    n_sectors = len(sectors)
    n_ms = len(ms_set)

    # Derived fields
    cascading = _derive_cascading(n_sectors)
    cross_border_pattern = _derive_cross_border_pattern(n_ms)
    capacity_exceeded = _derive_capacity_exceeded(
        affected_entities, n_sectors, n_ms, safety,
    )

    # Deterministic T-level
    t_level, t_basis = derive_t_level(svc, data, cascading, affected_entities)

    return AggregationResult(
        service_impact=svc,
        data_impact=data,
        financial_impact=fin,
        safety_impact=safety,
        affected_persons_count=total_persons,
        affected_entities=affected_entities,
        sectors_affected=n_sectors,
        ms_affected=n_ms,
        cascading=cascading,
        cross_border_pattern=cross_border_pattern,
        capacity_exceeded=capacity_exceeded,
        t_level=t_level,
        t_basis=t_basis,
        sector_list=sorted(sectors),
        ms_list=sorted(ms_set),
    )
