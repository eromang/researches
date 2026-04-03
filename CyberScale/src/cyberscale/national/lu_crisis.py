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
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("cyberscale.national.lu_crisis")


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


# ---------------------------------------------------------------------------
# Criterion 3 — Coordination and decision urgency
# ---------------------------------------------------------------------------


def evaluate_criterion_3(
    coordination_required: bool | None,
    urgent_decisions_required: bool | None,
) -> CriterionResult:
    """Evaluate Criterion 3: both coordination AND urgency must be true.

    None values represent uncertainty. Per framework guidance:
    "If answers are affirmative or uncertain, rapid consultation should be
    initiated." Uncertainty -> undetermined (not not_met).
    """
    coord_uncertain = coordination_required is None
    urgent_uncertain = urgent_decisions_required is None

    if coord_uncertain or urgent_uncertain:
        reasons = []
        if coord_uncertain:
            reasons.append("coordination requirement uncertain")
        if urgent_uncertain:
            reasons.append("decision urgency uncertain")
        return CriterionResult(
            status="undetermined",
            details=[
                f"Criterion 3: {', '.join(reasons)} — "
                "framework guidance: uncertainty triggers consultation"
            ],
        )

    if coordination_required and urgent_decisions_required:
        return CriterionResult(
            status="met",
            details=["Coordination required AND urgent decisions required"],
        )

    reasons = []
    if not coordination_required:
        reasons.append("interministerial coordination not required")
    if not urgent_decisions_required:
        reasons.append("no immediate executive decisions needed")
    return CriterionResult(
        status="not_met",
        details=[f"Criterion 3 not met: {', '.join(reasons)}"],
    )


# ---------------------------------------------------------------------------
# Fast-track check
# ---------------------------------------------------------------------------


def _check_fast_track(
    suspected_malicious: bool,
    data_impact: str,
    service_impact: str,
) -> bool:
    """Check if fast-track provision applies.

    Fast-track: unauthorised access, suspected malicious, likely to cause
    grave operational disruptions -> skip Criterion 2, go directly to Criterion 3.
    """
    return (
        suspected_malicious
        and data_impact in ("accessed", "exfiltrated", "compromised", "systemic")
        and service_impact in ("unavailable", "sustained")
    )


# ---------------------------------------------------------------------------
# Main incident qualification
# ---------------------------------------------------------------------------


def qualify_hcpn_incident(
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
) -> HcpnQualificationResult:
    """Qualify an incident against HCPN crisis criteria.

    Three cumulative criteria must be met:
    1. Essential service affected
    2. Prejudice to vital interests (at least one sub-criterion) — bypassed on fast-track
    3. Coordination and decision urgency (both conditions)

    Fast-track: malicious unauthorized access with grave disruption
    bypasses Criterion 2 and goes directly to Criterion 3.

    prejudice_actual: True if prejudice has already occurred (-> Crise),
    False if prejudice is potential (-> Alerte/CERC).
    """
    criteria: dict[str, CriterionResult] = {}
    consultation_reasons: list[str] = []

    # Criterion 1
    c1 = evaluate_criterion_1(sectors_affected, entity_types)
    criteria["criterion_1"] = c1

    # Fast-track check
    fast_tracked = False
    if c1.is_met and _check_fast_track(suspected_malicious, data_impact, service_impact):
        fast_tracked = True
        criteria["criterion_2"] = CriterionResult(
            status="bypassed",
            details=["Fast-track: malicious unauthorized access with grave operational disruption — Criterion 2 bypassed per framework provision, proceeding directly to Criterion 3"],
        )
    else:
        # Criterion 2
        c2 = evaluate_criterion_2(
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            sectors_affected=sectors_affected,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
        )
        criteria["criterion_2"] = c2

    # Criterion 3
    c3 = evaluate_criterion_3(coordination_required, urgent_decisions_required)
    criteria["criterion_3"] = c3

    # Collect undetermined criteria for consultation recommendation
    for name, cr in criteria.items():
        if cr.is_undetermined:
            consultation_reasons.extend(
                f"{name}: {d}" for d in cr.details
            )

    # Determine qualification: all criteria must be met or bypassed
    logger.info(
        "hcpn_incident: c1=%s c2=%s c3=%s fast_track=%s",
        criteria["criterion_1"].status,
        criteria["criterion_2"].status,
        criteria["criterion_3"].status,
        fast_tracked,
    )
    all_satisfied = all(
        cr.is_met or cr.is_bypassed for cr in criteria.values()
    )
    any_undetermined = any(cr.is_undetermined for cr in criteria.values())

    if all_satisfied:
        if cross_border or capacity_exceeded:
            level = "large_scale_cybersecurity_incident"
        else:
            level = "national_major_incident"
        mode = "crise" if prejudice_actual else "alerte_cerc"
    else:
        level = "none"
        mode = "permanent"

    logger.info(
        "hcpn_incident result: qualifies=%s level=%s mode=%s consult=%s",
        all_satisfied, level, mode, any_undetermined,
    )
    return HcpnQualificationResult(
        qualifies=all_satisfied,
        qualification_level=level,
        cooperation_mode=mode,
        criteria=criteria,
        fast_tracked=fast_tracked,
        recommend_consultation=any_undetermined,
        consultation_reasons=consultation_reasons,
        event_type="incident",
    )


# ---------------------------------------------------------------------------
# Threat probability assessment (Criterion 2 for threats)
# ---------------------------------------------------------------------------


def evaluate_threat_probability(probability: str) -> CriterionResult:
    """Evaluate threat probability — only High and Imminent qualify."""
    data = _load()
    levels = data["threat_probability_levels"]["levels"]
    level_map = {lv["level"]: lv for lv in levels}

    if probability not in level_map:
        return CriterionResult(
            status="not_met",
            details=[f"Unknown probability level: {probability}"],
        )

    lv = level_map[probability]
    if lv["qualifies"]:
        return CriterionResult(
            status="met",
            details=[f"Threat probability: {lv['label']} ({probability}) — qualifies"],
        )
    return CriterionResult(
        status="not_met",
        details=[f"Threat probability: {lv['label']} ({probability}) — does not qualify (only High/Imminent qualify)"],
    )


# ---------------------------------------------------------------------------
# Main threat qualification
# ---------------------------------------------------------------------------


def qualify_hcpn_threat(
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
) -> HcpnQualificationResult:
    """Qualify a cyber threat against HCPN crisis criteria.

    Four cumulative criteria (same three as incidents + probability):
    1. Essential service targeted
    2. Probability of materialisation (High or Imminent)
    3. Potential prejudice to vital interests (same 7 sub-criteria)
    4. Coordination and decision urgency
    """
    criteria: dict[str, CriterionResult] = {}
    consultation_reasons: list[str] = []

    # Criterion 1: Essential service targeted
    c1 = evaluate_criterion_1(sectors_affected, entity_types)
    criteria["criterion_1"] = c1

    # Criterion 2 (threat-specific): Probability
    c2_prob = evaluate_threat_probability(threat_probability)
    criteria["criterion_2_probability"] = c2_prob

    # Criterion 3: Potential prejudice to vital interests
    c3 = evaluate_criterion_2(
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        sectors_affected=sectors_affected,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
    )
    criteria["criterion_3_prejudice"] = c3

    # Criterion 4: Coordination and decision urgency
    c4 = evaluate_criterion_3(coordination_required, urgent_decisions_required)
    criteria["criterion_4_urgency"] = c4

    # Collect undetermined
    for name, cr in criteria.items():
        if cr.is_undetermined:
            consultation_reasons.extend(f"{name}: {d}" for d in cr.details)

    all_met = all(cr.is_met for cr in criteria.values())
    any_undetermined = any(cr.is_undetermined for cr in criteria.values())

    if all_met:
        if cross_border or capacity_exceeded:
            level = "large_scale_cyber_threat"
        else:
            level = "national_major_cyber_threat"
        mode = "crise" if prejudice_actual else "alerte_cerc"
    else:
        level = "none"
        mode = "permanent"

    logger.info(
        "hcpn_threat: c1=%s c2_prob=%s c3_prejudice=%s c4_urgency=%s",
        criteria["criterion_1"].status,
        criteria["criterion_2_probability"].status,
        criteria["criterion_3_prejudice"].status,
        criteria["criterion_4_urgency"].status,
    )
    logger.info(
        "hcpn_threat result: qualifies=%s level=%s mode=%s consult=%s",
        all_met, level, mode, any_undetermined,
    )
    return HcpnQualificationResult(
        qualifies=all_met,
        qualification_level=level,
        cooperation_mode=mode,
        criteria=criteria,
        fast_tracked=False,
        recommend_consultation=any_undetermined,
        consultation_reasons=consultation_reasons,
        event_type="threat",
    )
