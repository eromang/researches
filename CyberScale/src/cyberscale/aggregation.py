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

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cyberscale.aggregation")


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


_DEPS_PATH = Path(__file__).parent.parent.parent / "data" / "reference" / "sector_dependencies.json"
_cached_deps: dict | None = None


def _load_sector_dependencies() -> dict:
    global _cached_deps
    if _cached_deps is None:
        if _DEPS_PATH.exists():
            with open(_DEPS_PATH, encoding="utf-8") as f:
                _cached_deps = json.load(f)
        else:
            _cached_deps = {"dependencies": {}}
    return _cached_deps


def propagate_cascading(
    impacted_sectors: set[str],
    sector_impacts: dict[str, str],
) -> tuple[set[str], str]:
    """Propagate impact through sector dependency graph.

    Args:
        impacted_sectors: Set of sectors with reported entities.
        sector_impacts: Map of sector → worst service_impact for that sector.

    Returns:
        (all_affected_sectors, cascading_level) where all_affected_sectors
        includes propagated downstream sectors.
    """
    deps = _load_sector_dependencies().get("dependencies", {})
    all_sectors = set(impacted_sectors)

    for sector in impacted_sectors:
        impact = sector_impacts.get(sector, "none")
        sector_deps = deps.get(sector, {})

        # Direct dependencies: propagate if unavailable or sustained
        if impact in ("unavailable", "sustained"):
            for downstream in sector_deps.get("direct", []):
                all_sectors.add(downstream)

        # Indirect dependencies: propagate only if sustained
        if impact == "sustained":
            for downstream in sector_deps.get("indirect", []):
                all_sectors.add(downstream)

    cascading_level = _derive_cascading_from_count(len(all_sectors))
    if all_sectors - impacted_sectors:
        logger.info(
            "cascading propagation: %s -> %s (level=%s)",
            impacted_sectors, all_sectors - impacted_sectors, cascading_level,
        )
    return all_sectors, cascading_level


def _derive_cascading_from_count(sectors_affected: int) -> str:
    """Derive cascading level from total number of affected sectors."""
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
        logger.info("derive_t_level: %s basis=%s", "T4", basis)
        return "T4", basis
    if data_impact == "systemic":
        basis.append("systemic data impact")
        logger.info("derive_t_level: %s basis=%s", "T4", basis)
        return "T4", basis
    if service_impact == "unavailable" and cascading == "uncontrolled":
        basis.append("unavailable service + uncontrolled cascading")
        logger.info("derive_t_level: %s basis=%s", "T4", basis)
        return "T4", basis

    # T3: unavailable OR exfiltrated OR cross_sector cascading OR entities > 50
    if service_impact == "unavailable":
        basis.append("unavailable service impact")
        logger.info("derive_t_level: %s basis=%s", "T3", basis)
        return "T3", basis
    if data_impact == "exfiltrated":
        basis.append("exfiltrated data impact")
        logger.info("derive_t_level: %s basis=%s", "T3", basis)
        return "T3", basis
    if cascading == "cross_sector":
        basis.append("cross-sector cascading")
        logger.info("derive_t_level: %s basis=%s", "T3", basis)
        return "T3", basis
    if affected_entities > 50:
        basis.append(f"{affected_entities} entities affected")
        logger.info("derive_t_level: %s basis=%s", "T3", basis)
        return "T3", basis

    # T2: degraded OR accessed/compromised OR limited cascading OR entities > 10
    if service_impact == "degraded":
        basis.append("degraded service impact")
        logger.info("derive_t_level: %s basis=%s", "T2", basis)
        return "T2", basis
    if data_impact in ("accessed", "compromised"):
        basis.append(f"{data_impact} data impact")
        logger.info("derive_t_level: %s basis=%s", "T2", basis)
        return "T2", basis
    if cascading == "limited":
        basis.append("limited cascading")
        logger.info("derive_t_level: %s basis=%s", "T2", basis)
        return "T2", basis
    if affected_entities > 10:
        basis.append(f"{affected_entities} entities affected")
        logger.info("derive_t_level: %s basis=%s", "T2", basis)
        return "T2", basis

    # T1
    basis.append("below escalation thresholds")
    logger.info("derive_t_level: %s basis=%s", "T1", basis)
    return "T1", basis


def derive_o_level(
    cross_border_pattern: str,
    capacity_exceeded: bool,
    entity_relevance: str,
    ms_affected: int,
    sectors_affected: int,
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    affected_entities: int = 1,
) -> tuple[str, list[str]]:
    """Deterministic O-level from aggregated operational/consequence fields.

    Returns (o_level, basis) where basis lists the triggering rules.
    Rules ported from generate_incidents.py assign_o_level() with
    consequence dimension escalation added in v5.
    """
    basis = []

    # --- Consequence escalation: safety or massive persons → +1 effective level ---
    consequence_boost = 0
    if safety_impact in ("health_damage", "death"):
        consequence_boost += 1
        basis.append(f"{safety_impact} safety impact")
    if affected_persons_count >= 100000:
        consequence_boost += 1
        basis.append(f"{affected_persons_count} persons affected")
    if financial_impact == "severe" and affected_entities >= 10:
        consequence_boost += 1
        basis.append("severe financial impact across multiple entities")
    consequence_boost = min(consequence_boost, 1)  # cap at +1

    # --- Base O-level from structural fields ---

    # O4: (systemic cross-border + capacity_exceeded)
    #     OR (systemic entity + 6+ MS)
    #     OR (systemic cross-border + systemic entity)
    if cross_border_pattern == "systemic" and capacity_exceeded:
        basis.append("systemic cross-border + capacity exceeded")
        logger.info("derive_o_level: %s basis=%s", "O4", basis)
        return "O4", basis
    if entity_relevance == "systemic" and ms_affected >= 6:
        basis.append(f"systemic entity + {ms_affected} MS")
        logger.info("derive_o_level: %s basis=%s", "O4", basis)
        return "O4", basis
    if cross_border_pattern == "systemic" and entity_relevance == "systemic":
        basis.append("systemic cross-border + systemic entity")
        logger.info("derive_o_level: %s basis=%s", "O4", basis)
        return "O4", basis

    # O3: significant cross-border
    #     OR (high_relevance + 3+ MS) OR capacity_exceeded
    #     OR (systemic entity + 3+ MS)
    o3_triggers = []
    if cross_border_pattern == "significant":
        o3_triggers.append("significant cross-border pattern")
    if entity_relevance == "high_relevance" and ms_affected >= 3:
        o3_triggers.append(f"high_relevance entity + {ms_affected} MS")
    if capacity_exceeded:
        o3_triggers.append("national capacity exceeded")
    if entity_relevance == "systemic" and ms_affected >= 3:
        o3_triggers.append(f"systemic entity + {ms_affected} MS")
    if o3_triggers:
        basis.extend(o3_triggers)
        # With consequence boost, O3 → O4
        if consequence_boost > 0:
            logger.info("derive_o_level: %s basis=%s", "O4", basis)
            return "O4", basis
        logger.info("derive_o_level: %s basis=%s", "O3", basis)
        return "O3", basis

    # O2: limited cross-border
    #     OR (essential + 2+ MS) OR 3+ sectors
    #     OR (high_relevance + 2+ MS)
    o2_triggers = []
    if cross_border_pattern == "limited":
        o2_triggers.append("limited cross-border pattern")
    if entity_relevance == "essential" and ms_affected >= 2:
        o2_triggers.append(f"essential entity + {ms_affected} MS")
    if sectors_affected >= 3:
        o2_triggers.append(f"{sectors_affected} sectors affected")
    if entity_relevance == "high_relevance" and ms_affected >= 2:
        o2_triggers.append(f"high_relevance entity + {ms_affected} MS")
    if o2_triggers:
        basis.extend(o2_triggers)
        if consequence_boost > 0:
            logger.info("derive_o_level: %s basis=%s", "O3", basis)
            return "O3", basis
        logger.info("derive_o_level: %s basis=%s", "O2", basis)
        return "O2", basis

    # O1: everything else
    if consequence_boost > 0:
        basis.append("below structural thresholds but consequence escalation")
        logger.info("derive_o_level: %s basis=%s", "O2", basis)
        return "O2", basis

    basis.append("below operational thresholds")
    logger.info("derive_o_level: %s basis=%s", "O1", basis)
    return "O1", basis


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

    # Deterministic T-level and O-level
    t_level: str
    t_basis: list[str]
    o_level: str = "O1"
    o_basis: list[str] = field(default_factory=list)

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
            "o_level": self.o_level,
            "o_basis": self.o_basis,
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

    sector_impacts: dict[str, list[str]] = {}  # sector → list of service_impacts

    for n in notifications:
        service_impacts.append(n.get("service_impact", "none"))
        data_impacts.append(n.get("data_impact", "none"))
        financial_impacts.append(n.get("financial_impact", "none"))
        safety_impacts.append(n.get("safety_impact", "none"))
        total_persons += n.get("affected_persons_count", 0)

        if "sector" in n:
            sectors.add(n["sector"])
            sector_impacts.setdefault(n["sector"], []).append(n.get("service_impact", "none"))
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
    n_ms = len(ms_set)

    # Sector dependency-aware cascading
    per_sector_worst = {
        s: _worst_case(impacts, _SERVICE_IMPACT_ORDER)
        for s, impacts in sector_impacts.items()
    }
    all_affected_sectors, cascading = propagate_cascading(sectors, per_sector_worst)
    n_sectors = len(all_affected_sectors)
    cross_border_pattern = _derive_cross_border_pattern(n_ms)
    capacity_exceeded = _derive_capacity_exceeded(
        affected_entities, n_sectors, n_ms, safety,
    )

    # Deterministic T-level and O-level
    t_level, t_basis = derive_t_level(svc, data, cascading, affected_entities)
    o_level, o_basis = derive_o_level(
        cross_border_pattern, capacity_exceeded, "essential",
        n_ms, n_sectors, fin, safety, total_persons, affected_entities,
    )

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
        o_level=o_level,
        o_basis=o_basis,
        sector_list=sorted(all_affected_sectors),
        ms_list=sorted(ms_set),
    )
