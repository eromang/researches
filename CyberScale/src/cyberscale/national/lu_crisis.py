"""Luxembourg HCPN national crisis qualification.

Implements the Cadre national de qualification (HCPN v1.0, 22.08.2025).
Three cumulative criteria for incidents, four for threats.

Scoped to IMPACT ON LUXEMBOURG regardless of entity establishment.
An entity established in IE with impact on LU banking is in scope.

Several sub-criteria have undefined quantitative thresholds (delegated to
sectoral authorities). The module returns 'undetermined' for these — it
evaluates what it can, flags what it can't, and recommends consultation
when uncertain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


_REF_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data" / "reference" / "hcpn_crisis_qualification.json"
)

_cached: dict | None = None


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_REF_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CriterionResult:
    """Result of evaluating a single qualification criterion.

    status: "met" | "not_met" | "undetermined" | "bypassed"
    """
    status: str
    details: list[str] = field(default_factory=list)

    @property
    def is_met(self) -> bool:
        return self.status == "met"

    @property
    def is_undetermined(self) -> bool:
        return self.status == "undetermined"

    @property
    def is_bypassed(self) -> bool:
        return self.status == "bypassed"


@dataclass
class HcpnQualificationResult:
    """Full HCPN qualification result."""

    qualifies: bool
    qualification_level: str  # e.g., "national_major_incident" or "none"
    cooperation_mode: str  # "crise" | "alerte_cerc" | "permanent"
    criteria: dict[str, CriterionResult] = field(default_factory=dict)
    fast_tracked: bool = False
    recommend_consultation: bool = False
    consultation_reasons: list[str] = field(default_factory=list)
    event_type: str = "incident"  # "incident" | "threat"

    def to_dict(self) -> dict:
        return {
            "qualifies": self.qualifies,
            "qualification_level": self.qualification_level,
            "cooperation_mode": self.cooperation_mode,
            "criteria": {
                k: {"status": v.status, "details": v.details}
                for k, v in self.criteria.items()
            },
            "fast_tracked": self.fast_tracked,
            "recommend_consultation": self.recommend_consultation,
            "consultation_reasons": self.consultation_reasons,
            "event_type": self.event_type,
        }


# ---------------------------------------------------------------------------
# Criterion 1 — Essential service affected
# ---------------------------------------------------------------------------


def evaluate_criterion_1(
    sectors_affected: list[str],
    entity_types: list[str],
) -> CriterionResult:
    """Check if at least one essential service is affected.

    Reference list: CER essential services (EU Delegated Regulation 2023/2450).
    Scope is extensible by competent authorities.
    """
    data = _load()
    essential_sectors = set(data["essential_services"]["sectors"])

    matched = [s for s in sectors_affected if s in essential_sectors]
    if matched:
        return CriterionResult(
            status="met",
            details=[f"Essential service(s) affected: {', '.join(matched)}"],
        )

    return CriterionResult(
        status="not_met",
        details=[f"No essential service affected. Sectors: {sectors_affected}"],
    )


# ---------------------------------------------------------------------------
# Criterion 2 — Prejudice to vital interests or essential needs
# ---------------------------------------------------------------------------


def _check_interdependent_sectors(
    sectors_affected: list[str],
    service_impact: str,
) -> bool:
    """Check if disrupted sectors are interdependent via sector_dependencies.json."""
    from cyberscale.aggregation import _load_sector_dependencies

    if service_impact not in ("unavailable", "sustained"):
        return False

    deps = _load_sector_dependencies().get("dependencies", {})
    affected = set(sectors_affected)

    for sector in affected:
        sector_deps = deps.get(sector, {})
        direct = set(sector_deps.get("direct", []))
        if direct & affected:
            return True
    return False


def evaluate_criterion_2(
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    sectors_affected: list[str] | None = None,
    affected_persons_count: int = 0,
    cross_border: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
) -> CriterionResult:
    """Evaluate Criterion 2: prejudice to vital interests.

    At least one of seven sub-criteria must be satisfied.
    Returns "met" for deterministic sub-criteria, "undetermined" when
    thresholds are delegated to sectoral authorities.
    """
    sectors = sectors_affected or []
    data = _load()
    sub_criteria_ref = data["criterion_2_sub_criteria"]["sub_criteria"]
    essential_sectors = set(data["essential_services"]["sectors"])

    met_details: list[str] = []
    undetermined_details: list[str] = []

    # --- Sub-criterion: human_impact (fully deterministic) ---
    if safety_impact == "death":
        met_details.append("Human impact: at least one death")
    elif safety_impact == "health_damage":
        met_details.append("Human impact: serious injuries/health harm to multiple individuals")

    # --- Sub-criterion: national_security (fully deterministic) ---
    ns_ref = next(sc for sc in sub_criteria_ref if sc["id"] == "national_security")
    if threat_actor_type in ns_ref["trigger_actor_types"]:
        met_details.append(f"National security: threat actor type '{threat_actor_type}'")
    if any(s in ns_ref.get("trigger_sectors", []) for s in sectors):
        met_details.append("National security: affects defence/intelligence/sensitive government systems")

    # --- Sub-criterion: sensitive_data_loss (fully deterministic) ---
    sd_ref = next(sc for sc in sub_criteria_ref if sc["id"] == "sensitive_data_loss")
    if (
        data_impact in ("exfiltrated", "compromised", "systemic")
        and sensitive_data_type in sd_ref["trigger_data_types"]
    ):
        met_details.append(f"Sensitive data loss: {sensitive_data_type} — {data_impact}")

    # --- Sub-criterion: service_interruption (partially deterministic) ---
    essential_affected = [s for s in sectors if s in essential_sectors]
    if service_impact == "unavailable" and essential_affected:
        met_details.append(
            f"Service interruption: total interruption of essential service(s) {essential_affected}"
        )
    elif service_impact in ("degraded", "partial") and essential_affected:
        undetermined_details.append(
            "Service interruption: degraded essential service — 'significant duration' threshold defined by sectoral authorities"
        )

    # --- Sub-criterion: economic_consequences (partially deterministic) ---
    if _check_interdependent_sectors(sectors, service_impact):
        met_details.append(
            f"Economic consequences: major disruption of interdependent sectors {sectors}"
        )
    elif financial_impact in ("significant", "severe"):
        undetermined_details.append(
            "Economic consequences: significant/severe financial impact — 'critical threshold' defined by sectoral authorities"
        )

    # --- Sub-criterion: geographic_spread (undetermined) ---
    if cross_border:
        undetermined_details.append(
            "Geographic spread: cross-border propagation potential — 'significant geographic area' not explicitly quantified"
        )

    # --- Sub-criterion: users_affected (always undetermined when > 0) ---
    if affected_persons_count > 0:
        undetermined_details.append(
            f"Users affected: {affected_persons_count:,} persons — 'substantial portion' of population defined by sectoral authorities"
        )

    # Determine overall status
    if met_details:
        return CriterionResult(status="met", details=met_details)
    if undetermined_details:
        return CriterionResult(status="undetermined", details=undetermined_details)
    return CriterionResult(status="not_met", details=[
        "No Criterion 2 sub-criteria met or indicated"
    ])
