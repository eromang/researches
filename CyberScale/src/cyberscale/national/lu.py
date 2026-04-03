"""Luxembourg national-layer incident significance assessment.

Deterministic threshold logic from ILR NIS1 transposition regulations.
Digital infrastructure entities are excluded (IR thresholds take precedence).
DORA applies separately for banking/financial market entities (CSSF).

POST/LuxTrust use sector thresholds — no entity-specific overrides.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


_THRESHOLDS_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data" / "reference" / "lu_thresholds.json"
)

_cached: dict | None = None


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_THRESHOLDS_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


# ---------------------------------------------------------------------------
# Sector coverage check
# ---------------------------------------------------------------------------

# Sectors where LU ILR thresholds exist (keys in lu_thresholds.json "sectors")
_LU_SECTOR_KEYS: set[str] | None = None

# Entity types that map to an LU sector
_LU_ENTITY_MAP: dict[str, str] | None = None


def _build_entity_map() -> dict[str, str]:
    global _LU_ENTITY_MAP, _LU_SECTOR_KEYS
    if _LU_ENTITY_MAP is None:
        data = _load()
        _LU_SECTOR_KEYS = set(data["sectors"].keys())
        _LU_ENTITY_MAP = {}
        for _sector, mappings in data["sector_mapping"].items():
            if _sector == "description":
                continue
            for entity_type, lu_key in mappings.items():
                if lu_key is not None:
                    _LU_ENTITY_MAP[entity_type] = lu_key
    return _LU_ENTITY_MAP


def is_lu_covered(sector: str, entity_type: str) -> bool:
    """Check if entity falls under LU ILR thresholds.

    Returns False for:
    - Digital infrastructure entities (IR thresholds take precedence)
    - Banking/financial market (DORA applies separately)
    - Sectors not covered by NIS1 ILR regulations
    """
    from cyberscale.models.contextual_ir import is_ir_entity

    # IR entities always use EU-wide IR thresholds, even in Luxembourg
    if is_ir_entity(entity_type):
        return False

    entity_map = _build_entity_map()
    return entity_type in entity_map


def get_lu_sector_key(entity_type: str) -> str | None:
    """Return the LU threshold sector key for an entity type, or None."""
    entity_map = _build_entity_map()
    return entity_map.get(entity_type)


def is_lu_dora(sector: str) -> bool:
    """Check if a sector falls under DORA in Luxembourg."""
    data = _load()
    return sector in data["non_covered_sectors"]["dora_coverage"]


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class LuSignificanceResult:
    """Result of Luxembourg ILR threshold assessment."""

    significant_incident: bool
    triggered_criteria: list[str]
    ilr_reference: str
    common_criteria_met: list[str] = field(default_factory=list)
    competent_authority: str = "ILR"
    applicable_frameworks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "triggered_criteria": self.triggered_criteria,
            "ilr_reference": self.ilr_reference,
            "common_criteria_met": self.common_criteria_met,
            "competent_authority": self.competent_authority,
            "applicable_frameworks": self.applicable_frameworks,
        }


# ---------------------------------------------------------------------------
# Common criteria check (all NIS1 sectors)
# ---------------------------------------------------------------------------


def _check_common_criteria(
    safety_impact: str,
    financial_impact: str,
    affected_persons_count: int,
    sector_key: str,
) -> list[str]:
    """Check common criteria that apply to all LU NIS1 sectors."""
    data = _load()
    common = data["common_criteria"]
    met: list[str] = []

    # Safety risk
    if safety_impact in ("health_risk", "health_damage", "death"):
        met.append("Common: safety/security risk")

    # Material damage — road transport has higher threshold
    if financial_impact in ("significant", "severe"):
        if sector_key == "transport_road":
            met.append(f"Common: material damage (road transport ≥ EUR {common['material_damage_eur_road_transport']['amount']:,})")
        else:
            met.append(f"Common: material damage ≥ EUR {common['material_damage_eur']['amount']:,}")

    # Data loss > 50 LU users
    if affected_persons_count > common["data_loss_users_lu"]["users"]:
        met.append(f"Common: data CIA+A loss > {common['data_loss_users_lu']['users']} LU users")

    return met


# ---------------------------------------------------------------------------
# Per-sector assessment functions
# ---------------------------------------------------------------------------


def _assess_energy_electricity(
    pods_affected: int,
    voltage_level: str,
    impact_duration_hours: float,
    scada_unavailable_min: int,
    cross_border: bool,
) -> list[str]:
    """Assess electricity sector against ILR/N22/4 thresholds."""
    triggered: list[str] = []
    duration_min = int(impact_duration_hours * 60)

    data = _load()
    thresholds = data["sectors"]["energy_electricity"]["thresholds"]

    # Automatic triggers
    for auto in thresholds["automatic"]:
        if auto["condition"] == "hv_ehv_transmission" and voltage_level in ("hv", "ehv", "hv_ehv"):
            triggered.append("ILR/N22/4: HV/EHV transmission network incident")
        elif auto["condition"] == "scada_impact" and scada_unavailable_min > 0:
            triggered.append("ILR/N22/4: SCADA system impact")
        elif auto["condition"] == "cross_border" and cross_border:
            triggered.append("ILR/N22/4: cross-border impact")

    # POD thresholds
    if pods_affected > 0:
        if voltage_level in ("lv", ""):
            for t in thresholds["lv_pod"]:
                if pods_affected >= t["pods"] and (t["duration_min"] == 0 or duration_min >= t["duration_min"]):
                    triggered.append(f"ILR/N22/4: ≥ {t['pods']} LV-POD for ≥ {t['duration_min']} min")
                    break  # Most severe matching threshold
        elif voltage_level == "mv":
            for t in thresholds["mv_pod"]:
                if pods_affected >= t["pods"] and (t["duration_min"] == 0 or duration_min >= t["duration_min"]):
                    triggered.append(f"ILR/N22/4: ≥ {t['pods']} MV-POD for ≥ {t['duration_min']} min")
                    break

    return triggered


def _assess_energy_gas(
    scada_unavailable_min: int,
    cross_border: bool,
    impact_duration_hours: float,
    affected_persons_count: int,
    **kwargs,
) -> list[str]:
    """Assess gas sector against ILR/N22/3 thresholds."""
    triggered: list[str] = []

    valve_control_loss = kwargs.get("valve_control_loss", False)
    measurement_falsification = kwargs.get("measurement_falsification", False)
    transmission_network_incident = kwargs.get("transmission_network_incident", False)

    if valve_control_loss:
        triggered.append("ILR/N22/3: motorized valve control loss")
    if measurement_falsification:
        triggered.append("ILR/N22/3: measurement data falsification")
    if scada_unavailable_min >= 30:
        triggered.append("ILR/N22/3: SCADA/EDP unavailable ≥ 30 minutes")
    if transmission_network_incident:
        triggered.append("ILR/N22/3: transmission network incident")
    if cross_border:
        triggered.append("ILR/N22/3: cross-border impact")
    if impact_duration_hours >= 2 and affected_persons_count > 50:
        triggered.append("ILR/N22/3: data availability loss ≥ 2h AND > 50 users")

    return triggered


def _assess_transport_rail(
    trains_cancelled_pct: float,
    slots_impacted: int,
    impact_duration_hours: float,
    **kwargs,
) -> list[str]:
    """Assess rail transport against ILR/N22/1 thresholds."""
    triggered: list[str] = []

    freight_cancelled_pct = kwargs.get("freight_cancelled_pct", 0.0)

    if trains_cancelled_pct >= 5.0:
        triggered.append("ILR/N22/1: ≥ 5% trains cancelled per day")
    if slots_impacted >= 100:
        triggered.append("ILR/N22/1: ≥ 100 slots impacted per day")
    if impact_duration_hours >= 4:
        triggered.append("ILR/N22/1: infrastructure management unavailable ≥ 4h")
    if freight_cancelled_pct >= 20.0:
        triggered.append("ILR/N22/1: ≥ 20% freight trains cancelled/delayed ≥ 1h")
    if impact_duration_hours >= 12:
        triggered.append("ILR/N22/1: capacity management unavailable ≥ 12h")

    return triggered


def _assess_transport_road(
    impact_duration_hours: float,
    affected_persons_count: int,
    financial_impact: str,
) -> list[str]:
    """Assess road transport against ILR/N22/2 thresholds."""
    triggered: list[str] = []

    if impact_duration_hours >= 2:
        triggered.append("ILR/N22/2: service unavailability ≥ 2 hours")
    if affected_persons_count > 50:
        triggered.append("ILR/N22/2: data CIA+A loss > 50 users")
    # Road transport uses EUR 200K, checked via common criteria with sector override

    return triggered


def _assess_transport_air(
    flights_cancelled: int,
    impact_duration_hours: float,
    **kwargs,
) -> list[str]:
    """Assess air transport against ILR/N23/1 thresholds."""
    triggered: list[str] = []

    if flights_cancelled > 4:
        triggered.append("ILR/N23/1: > 4 flights cancelled to/from LU per day")
    if impact_duration_hours > 4:
        triggered.append("ILR/N23/1: operations systems unavailable > 4 hours")

    cargo_flights_unable = kwargs.get("cargo_flights_unable", 0)
    if cargo_flights_unable >= 2 and impact_duration_hours > 24:
        triggered.append("ILR/N23/1: inability to operate ≥ 2 cargo flights > 24h")

    return triggered


def _assess_health_hospital(
    persons_health_impact: int,
    safety_impact: str,
) -> list[str]:
    """Assess hospital sector against ILR/N22/5 thresholds."""
    triggered: list[str] = []

    if safety_impact in ("death",) or persons_health_impact >= 1:
        if safety_impact == "death":
            triggered.append("ILR/N22/5: ≥ 1 person with irreversible health impact (death)")
        elif safety_impact == "health_damage":
            if persons_health_impact >= 1:
                triggered.append("ILR/N22/5: ≥ 1 person with irreversible health impact")
        elif persons_health_impact >= 10:
            triggered.append("ILR/N22/5: ≥ 10 persons with reversible health impact")

    return triggered


def _assess_health_laboratory(
    analyses_affected_pct: float,
    impact_duration_hours: float,
    persons_health_impact: int,
) -> list[str]:
    """Assess medical laboratory against ILR/N22/5 thresholds."""
    triggered: list[str] = []

    if persons_health_impact >= 1:
        triggered.append("ILR/N22/5: ≥ 1 person endangered")

    duration_days = impact_duration_hours / 24.0

    if analyses_affected_pct >= 100 and impact_duration_hours >= 2:
        triggered.append("ILR/N22/5: 100% analyses affected for ≥ 2 hours")
    elif analyses_affected_pct >= 50 and impact_duration_hours >= 4:
        triggered.append("ILR/N22/5: 50-100% analyses affected for ≥ 4 hours")
    elif analyses_affected_pct >= 10 and duration_days >= 1:
        triggered.append("ILR/N22/5: 10-50% analyses affected for ≥ 1 day")
    elif analyses_affected_pct >= 2 and duration_days >= 2:
        triggered.append("ILR/N22/5: 2-10% analyses affected for ≥ 2 days")

    return triggered


def _assess_drinking_water(
    affected_persons_count: int,
    users_pct: float,
    impact_duration_hours: float,
    cross_border: bool,
) -> list[str]:
    """Assess drinking water against ILR/N21/2 thresholds."""
    triggered: list[str] = []
    duration_days = impact_duration_hours / 24.0

    if cross_border:
        triggered.append("ILR/N21/2: cross-border impact")

    if users_pct >= 25 and affected_persons_count >= 50000:
        triggered.append("ILR/N21/2: ≥ 25% users, ≥ 50,000 users, any duration")
    elif users_pct >= 10 and affected_persons_count >= 15000 and impact_duration_hours >= 4:
        triggered.append("ILR/N21/2: 10-25% users, ≥ 15,000 users, ≥ 4 hours")
    elif users_pct >= 5 and affected_persons_count >= 5000 and impact_duration_hours >= 24:
        triggered.append("ILR/N21/2: 5-10% users, ≥ 5,000 users, ≥ 24 hours")
    elif users_pct >= 1 and affected_persons_count >= 500 and duration_days >= 2:
        triggered.append("ILR/N21/2: 1-5% users, ≥ 500 users, ≥ 2 days")
    elif affected_persons_count >= 50 and duration_days >= 4:
        triggered.append("ILR/N21/2: < 1% users, ≥ 50 users, ≥ 4 days")

    return triggered


def _assess_digital_service_providers(
    affected_persons_count: int,
    impact_duration_hours: float,
    safety_impact: str,
    financial_impact: str,
) -> list[str]:
    """Assess digital service providers against ILR/N21/1 thresholds."""
    triggered: list[str] = []

    user_hours = affected_persons_count * impact_duration_hours
    if user_hours > 5000000:
        triggered.append("ILR/N21/1: > 5,000,000 user-hours")

    if affected_persons_count > 100000:
        triggered.append("ILR/N21/1: > 100,000 EU users (integrity/confidentiality)")

    if safety_impact in ("health_risk", "health_damage", "death"):
        triggered.append("ILR/N21/1: safety risk")

    if financial_impact == "severe":
        triggered.append("ILR/N21/1: > EUR 1,000,000 material damage")

    return triggered


# ---------------------------------------------------------------------------
# Main assessment function
# ---------------------------------------------------------------------------


def assess_lu_significance(
    sector: str,
    entity_type: str,
    service_impact: str = "none",
    data_impact: str = "none",
    affected_persons_count: int = 0,
    financial_impact: str = "none",
    safety_impact: str = "none",
    impact_duration_hours: float = 0,
    cross_border: bool = False,
    suspected_malicious: bool = False,  # Accepted for router compatibility
    # Sector-specific fields
    sector_specific: dict | None = None,
) -> LuSignificanceResult:
    """Assess incident significance against Luxembourg ILR thresholds.

    Deterministic: checks common criteria + sector-specific thresholds.
    Returns significant_incident=True if ANY criterion triggers.
    """
    ss = sector_specific or {}

    sector_key = get_lu_sector_key(entity_type)
    if sector_key is None:
        # Check DORA coverage
        if is_lu_dora(sector):
            return LuSignificanceResult(
                significant_incident=False,
                triggered_criteria=[],
                ilr_reference="DORA",
                common_criteria_met=[],
                competent_authority="CSSF",
                applicable_frameworks=[{
                    "framework": "DORA",
                    "competent_authority": "CSSF",
                    "initial_notification_hours": 4,
                    "intermediate_report_hours": 72,
                    "final_report_days": 30,
                    "note": "DORA thresholds assessed separately by CSSF",
                }],
            )
        return LuSignificanceResult(
            significant_incident=False,
            triggered_criteria=[],
            ilr_reference="none",
            common_criteria_met=[],
            applicable_frameworks=[],
        )

    data = _load()
    sector_data = data["sectors"][sector_key]
    ilr_ref = sector_data["reference"]

    # Check common criteria
    common_met = _check_common_criteria(
        safety_impact, financial_impact, affected_persons_count, sector_key,
    )

    # Check sector-specific thresholds
    sector_triggered: list[str] = []

    if sector_key == "energy_electricity":
        sector_triggered = _assess_energy_electricity(
            pods_affected=ss.get("pods_affected", 0),
            voltage_level=ss.get("voltage_level", ""),
            impact_duration_hours=impact_duration_hours,
            scada_unavailable_min=ss.get("scada_unavailable_min", 0),
            cross_border=cross_border,
        )
    elif sector_key == "energy_gas":
        sector_triggered = _assess_energy_gas(
            scada_unavailable_min=ss.get("scada_unavailable_min", 0),
            cross_border=cross_border,
            impact_duration_hours=impact_duration_hours,
            affected_persons_count=affected_persons_count,
            valve_control_loss=ss.get("valve_control_loss", False),
            measurement_falsification=ss.get("measurement_falsification", False),
            transmission_network_incident=ss.get("transmission_network_incident", False),
        )
    elif sector_key == "transport_rail":
        sector_triggered = _assess_transport_rail(
            trains_cancelled_pct=ss.get("trains_cancelled_pct", 0.0),
            slots_impacted=ss.get("slots_impacted", 0),
            impact_duration_hours=impact_duration_hours,
            freight_cancelled_pct=ss.get("freight_cancelled_pct", 0.0),
        )
    elif sector_key == "transport_road":
        sector_triggered = _assess_transport_road(
            impact_duration_hours=impact_duration_hours,
            affected_persons_count=affected_persons_count,
            financial_impact=financial_impact,
        )
    elif sector_key == "transport_air":
        sector_triggered = _assess_transport_air(
            flights_cancelled=ss.get("flights_cancelled", 0),
            impact_duration_hours=impact_duration_hours,
            cargo_flights_unable=ss.get("cargo_flights_unable", 0),
        )
    elif sector_key == "health_hospital":
        sector_triggered = _assess_health_hospital(
            persons_health_impact=ss.get("persons_health_impact", 0),
            safety_impact=safety_impact,
        )
    elif sector_key == "health_laboratory":
        sector_triggered = _assess_health_laboratory(
            analyses_affected_pct=ss.get("analyses_affected_pct", 0.0),
            impact_duration_hours=impact_duration_hours,
            persons_health_impact=ss.get("persons_health_impact", 0),
        )
    elif sector_key == "drinking_water":
        sector_triggered = _assess_drinking_water(
            affected_persons_count=affected_persons_count,
            users_pct=ss.get("users_pct", 0.0),
            impact_duration_hours=impact_duration_hours,
            cross_border=cross_border,
        )
    elif sector_key == "digital_service_providers":
        sector_triggered = _assess_digital_service_providers(
            affected_persons_count=affected_persons_count,
            impact_duration_hours=impact_duration_hours,
            safety_impact=safety_impact,
            financial_impact=financial_impact,
        )

    all_triggered = sector_triggered
    is_significant = len(all_triggered) > 0 or len(common_met) > 0

    # Build applicable frameworks
    deadlines = sector_data.get("notification_deadlines", {})
    frameworks = [{
        "framework": "NIS1-LU (ILR)",
        "ilr_reference": ilr_ref,
        "competent_authority": sector_data.get("competent_authority", "ILR"),
        "pre_notification_hours": deadlines.get("pre_notification_hours", 24),
        "full_notification_days": deadlines.get("full_notification_days", 15),
    }]

    return LuSignificanceResult(
        significant_incident=is_significant,
        triggered_criteria=all_triggered,
        ilr_reference=ilr_ref,
        common_criteria_met=common_met,
        competent_authority=sector_data.get("competent_authority", "ILR"),
        applicable_frameworks=frameworks,
    )
