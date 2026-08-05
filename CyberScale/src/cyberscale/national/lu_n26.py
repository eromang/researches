"""Luxembourg ILR draft regulation N26 — important incident criteria.

Implements the twelve criteria of Art. 2(1) of the projet de règlement ILR/N26/X
(public consultation CP/N26/2), which replaces the NIS1-era sector regulations
with a single generic regime under the loi du 5 mai 2026.

**This regulation is not in force.** `lu.py` remains the default assessor for
Luxembourg. This module exists so the impact can be measured before the
consultation closes, and so the switch is a configuration change rather than a
rewrite when the text is adopted.

Two structural differences from `lu.py` matter more than the individual
thresholds:

1. **No sector routing.** The abrogated N21/N22/N23 regulations each defined
   sector-specific thresholds (LV-PODs for electricity, cancelled trains for
   rail). Art. 2(1) is generic and applies to every covered entity. Sector
   specificity can only return through the annexes of Art. 2(5), which were not
   published with the consultation draft.

2. **Lower and broader triggers.** One hour of partial degradation, or 50
   affected users, or any cross-border effect, each suffice on their own. Under
   the current regulations most of those cases sit below threshold.

Four criteria need inputs CyberScale's impact taxonomy does not carry today:
trade-secret exfiltration (d), physical access compromise (f), direct financial
loss and turnover in euro (j), and prejudice amounts (k). They are accepted as
optional arguments and reported as *not evaluable* when absent — never silently
treated as not triggered.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

_THRESHOLDS_PATH = (
    Path(__file__).parent.parent.parent.parent / "data" / "reference" / "lu_n26_thresholds.json"
)
_cached: dict | None = None

# Data impacts that count as an effect on authenticity, integrity or confidentiality
_CIA_IMPACTS = {"accessed", "compromised", "exfiltrated", "systemic"}
# Service impacts that count as partial or total inaccessibility
_DISRUPTED = {"degraded", "unavailable", "sustained"}


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_THRESHOLDS_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


@dataclass
class LuN26Result:
    """Outcome of an assessment against the draft N26 criteria."""

    significant_incident: bool
    triggered_criteria: list[str] = field(default_factory=list)
    not_evaluable: list[str] = field(default_factory=list)
    excluded_reason: str | None = None
    competent_authority: str = "ILR"
    regulation: str = "ILR/N26/X (draft, CP/N26/2)"
    in_force: bool = False

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "triggered_criteria": self.triggered_criteria,
            "not_evaluable": self.not_evaluable,
            "excluded_reason": self.excluded_reason,
            "competent_authority": self.competent_authority,
            "regulation": self.regulation,
            "in_force": self.in_force,
        }


# Entity types named in the title of IR (EU) 2024/2690, quoted verbatim in the
# recital of the N26 draft. This is the authority for Art. 2(6) scope.
_IR_TITLE_ENTITY_TYPES = frozenset({
    "dns_service_provider",
    "tld_registry",
    "cloud_computing_provider",
    "data_centre_operator",
    "cdn_provider",
    "managed_service_provider",
    "managed_security_service_provider",
    "online_marketplace_provider",
    "search_engine_provider",
    "social_network_provider",
    "trust_service_provider",
})

# Resolved 2026-08-05 against the Official Journal text. `ir_incident_thresholds.json`
# had additionally listed ixp_operator, public_ecn_provider and public_ecs_provider as
# IR entity types. Article 1 of IR (EU) 2024/2690 names eleven entity types and Articles
# 5 to 14 cover exactly those; none covers IXPs or electronic communications providers.
# The three were removed from that file, so they now fall under this regulation like any
# other national-scope entity. Kept as a named set because the error mattered: while it
# stood, telecom operators were silently excluded from the whole N26 regime.
_REMOVED_FROM_IR_SCOPE_2026_08_05 = frozenset({
    "ixp_operator",
    "public_ecn_provider",
    "public_ecs_provider",
})


def ir_scope(entity_type: str) -> str:
    """Art. 2(6) scope for an entity type: 'ir' or 'national'.

    Authority is Article 1 of IR (EU) 2024/2690, not the entity list in
    ir_incident_thresholds.json, which was wrong until 2026-08-05.
    """
    return "ir" if entity_type in _IR_TITLE_ENTITY_TYPES else "national"


def is_ir_governed(entity_type: str) -> bool:
    """True only where IR coverage is not in doubt. See `ir_scope`."""
    return ir_scope(entity_type) == "ir"


def assess_lu_n26_significance(
    sector: str = "",
    entity_type: str = "",
    service_impact: str = "none",
    data_impact: str = "none",
    affected_persons_count: int = 0,
    safety_impact: str = "none",
    impact_duration_hours: float = 0.0,
    cross_border: bool = False,
    suspected_malicious: bool = False,
    *,
    users_affected_pct_lu: float | None = None,
    liable_serious_disruption: bool | None = None,
    public_safety_risk: bool | None = None,
    scheduled_maintenance: bool = False,
    trade_secret_exfiltration: bool | None = None,
    physical_access_compromised: bool | None = None,
    direct_financial_loss_eur: float | None = None,
    annual_turnover_eur: float | None = None,
    prejudice_legal_person_eur: float | None = None,
    prejudice_natural_person_eur: float | None = None,
) -> LuN26Result:
    """Assess an incident against the draft N26 Art. 2(1) criteria.

    Any single criterion triggers. Criteria whose inputs were not supplied are
    listed in `not_evaluable` rather than counted as not triggered — a missing
    input is an unknown, not a negative.
    """
    triggered: list[str] = []
    unknown: list[str] = []

    # Art. 2(2) — scheduled maintenance is not an important incident.
    if scheduled_maintenance:
        return LuN26Result(
            significant_incident=False,
            excluded_reason="Art. 2(2): planned interruption / scheduled maintenance",
        )

    # Art. 2(6) — IR 2024/2690 entities are out of scope of this regulation.
    scope = ir_scope(entity_type) if entity_type else "national"
    if scope == "ir":
        return LuN26Result(
            significant_incident=False,
            excluded_reason=(
                f"Art. 2(6): {entity_type} is governed by IR (EU) 2024/2690, "
                "which this regulation does not displace"
            ),
        )


    disrupted = service_impact in _DISRUPTED

    # (a) > 1 hour, OR > 5% of users of the service in Luxembourg
    if disrupted:
        if impact_duration_hours > 1:
            triggered.append(f"Art. 2(1)(a): service disrupted for {impact_duration_hours}h (> 1h)")
        elif users_affected_pct_lu is not None and users_affected_pct_lu > 5:
            triggered.append(f"Art. 2(1)(a): {users_affected_pct_lu}% of LU users affected (> 5%)")
        elif users_affected_pct_lu is None and impact_duration_hours <= 1:
            unknown.append("Art. 2(1)(a): users_affected_pct_lu not supplied; duration alone is below 1h")

    # (b) unauthorised access, suspected malicious, liable to cause serious disruption
    if suspected_malicious and data_impact in _CIA_IMPACTS:
        if liable_serious_disruption is True:
            triggered.append("Art. 2(1)(b): malicious unauthorised access liable to cause serious disruption")
        elif liable_serious_disruption is None:
            unknown.append("Art. 2(1)(b): liable_serious_disruption is a judgement call and was not supplied")

    # (c) CIA impact affecting > 50 users in Luxembourg
    if data_impact in _CIA_IMPACTS and affected_persons_count > 50:
        triggered.append(f"Art. 2(1)(c): {data_impact} affecting {affected_persons_count} users (> 50)")

    # (d) trade secret exfiltration
    if trade_secret_exfiltration is True:
        triggered.append("Art. 2(1)(d): exfiltration of trade secrets")
    elif trade_secret_exfiltration is None:
        unknown.append("Art. 2(1)(d): trade_secret_exfiltration not supplied")

    # (e) cross-border or international impact
    if cross_border:
        triggered.append("Art. 2(1)(e): cross-border or international impact")

    # (f) physical access to infrastructure compromised
    if physical_access_compromised is True:
        triggered.append("Art. 2(1)(f): physical access to infrastructure compromised")
    elif physical_access_compromised is None:
        unknown.append("Art. 2(1)(f): physical_access_compromised not supplied")

    # (g) risk to public safety, security or health
    if public_safety_risk is True or safety_impact in ("health_damage", "death"):
        triggered.append("Art. 2(1)(g): risk to public safety, security or health")
    elif public_safety_risk is None:
        unknown.append("Art. 2(1)(g): public_safety_risk not supplied")

    # (h) considerable damage to the health of a natural person
    if safety_impact == "health_damage":
        triggered.append("Art. 2(1)(h): considerable damage to the health of a natural person")

    # (i) death of a natural person
    if safety_impact == "death":
        triggered.append("Art. 2(1)(i): death of a natural person")

    # (j) direct financial loss >= min(500 000, 5% of turnover)
    if direct_financial_loss_eur is not None:
        threshold = 500_000.0
        if annual_turnover_eur is not None:
            threshold = min(threshold, 0.05 * annual_turnover_eur)
        if direct_financial_loss_eur >= threshold:
            triggered.append(
                f"Art. 2(1)(j): direct loss EUR {direct_financial_loss_eur:,.0f} "
                f">= threshold EUR {threshold:,.0f}"
            )
        elif annual_turnover_eur is None:
            unknown.append(
                "Art. 2(1)(j): below EUR 500 000 but annual_turnover_eur not supplied — "
                "the 5% limb may still bind"
            )
    else:
        unknown.append("Art. 2(1)(j): direct_financial_loss_eur not supplied")

    # (k) prejudice to a legal or natural person
    if prejudice_legal_person_eur is not None and prejudice_legal_person_eur >= 50_000:
        triggered.append(f"Art. 2(1)(k): prejudice to a legal person EUR {prejudice_legal_person_eur:,.0f} (>= 50 000)")
    if prejudice_natural_person_eur is not None and prejudice_natural_person_eur >= 10_000:
        triggered.append(f"Art. 2(1)(k): prejudice to a natural person EUR {prejudice_natural_person_eur:,.0f} (>= 10 000)")
    if prejudice_legal_person_eur is None and prejudice_natural_person_eur is None:
        unknown.append("Art. 2(1)(k): prejudice amounts not supplied")

    # (l) annex criteria — the annexes were not published with the draft
    unknown.append("Art. 2(1)(l): annex criteria not published with the consultation draft")

    result = LuN26Result(
        significant_incident=bool(triggered),
        triggered_criteria=triggered,
        not_evaluable=unknown,
    )
    logger.info(
        "assess_lu_n26: significant=%s triggered=%d not_evaluable=%d",
        result.significant_incident, len(triggered), len(unknown),
    )
    return result


def assess_recurrence(
    occurrences: int,
    window_months: float,
    same_root_cause: bool,
    combined_direct_loss_eur: float | None = None,
    annual_turnover_eur: float | None = None,
) -> LuN26Result:
    """Art. 2(4): individually sub-threshold incidents that are collectively important.

    All three conditions must hold: at least two occurrences within six months,
    the same apparent root cause, and collective satisfaction of criterion (j).

    CyberScale assesses one incident at a time and holds no incident history, so
    the caller must supply the aggregate. This is exposed separately rather than
    folded into the main assessor to keep that requirement explicit.
    """
    if occurrences < 2 or window_months > 6 or not same_root_cause:
        return LuN26Result(
            significant_incident=False,
            excluded_reason=(
                f"Art. 2(4): needs >=2 occurrences within 6 months sharing a root cause "
                f"(got {occurrences} in {window_months} months, same_root_cause={same_root_cause})"
            ),
        )
    if combined_direct_loss_eur is None:
        return LuN26Result(
            significant_incident=False,
            not_evaluable=["Art. 2(4)(c): combined_direct_loss_eur not supplied — criterion (j) cannot be evaluated"],
        )
    threshold = 500_000.0
    if annual_turnover_eur is not None:
        threshold = min(threshold, 0.05 * annual_turnover_eur)
    if combined_direct_loss_eur >= threshold:
        return LuN26Result(
            significant_incident=True,
            triggered_criteria=[
                f"Art. 2(4): {occurrences} incidents in {window_months} months, same root cause, "
                f"combined loss EUR {combined_direct_loss_eur:,.0f} >= EUR {threshold:,.0f}"
            ],
        )
    return LuN26Result(
        significant_incident=False,
        excluded_reason=f"Art. 2(4)(c): combined loss below EUR {threshold:,.0f}",
    )


def notification_deadlines(entity_type: str = "") -> dict:
    """Art. 3 deadlines, with the trust service provider derogation applied."""
    t = _load()["notification_timeline"]
    incident_hours = t["incident_notification"]["deadline_hours"]
    derogation = None
    if entity_type == "trust_service_provider":
        incident_hours = t["trust_service_provider_derogation"]["deadline_hours"]
        derogation = "Art. 3(5): trust service providers notify within 24h, not 72h"
    return {
        "preliminary_hours": t["preliminary"]["deadline_hours"],
        "preliminary_clock": t["preliminary"]["clock_starts"],
        "incident_notification_hours": incident_hours,
        "incident_notification_clock": t["incident_notification"]["clock_starts"],
        "final_report_days": t["final_report"]["deadline_days"],
        "derogation": derogation,
    }
