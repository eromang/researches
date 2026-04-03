"""Belgium national-layer incident significance assessment.

Horizontal thresholds from CCB NIS2 Notification Guide v1.3 (August 2025).
Unlike Luxembourg (per-sector ILR matrices), Belgium applies the same
criteria across all NIS2 sectors.

IR entities (Art. 5-14) and DORA entities (banking/financial) are excluded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


_THRESHOLDS_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data" / "reference" / "be_thresholds.json"
)

_cached: dict | None = None


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_THRESHOLDS_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------


def is_be_covered(sector: str, entity_type: str) -> bool:
    """Check if entity falls under Belgium CCB horizontal thresholds.

    Returns False for:
    - IR entities (EU-wide thresholds take precedence)
    - DORA entities (banking/financial, BNB supervision)
    - Non-NIS2 entities
    """
    from cyberscale.models.contextual_ir import is_ir_entity

    if is_ir_entity(entity_type):
        return False

    data = _load()
    dora_sectors = data["exclusions"]["dora_entities"]["sectors"]
    if sector in dora_sectors:
        return False

    if sector == "non_nis2":
        return False

    return True


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BeSignificanceResult:
    """Result of Belgium CCB threshold assessment."""

    significant_incident: bool
    triggered_criteria: list[str]
    ccb_reference: str = "CCB NIS2 Guide v1.3"
    competent_authority: str = "CCB"
    applicable_frameworks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "triggered_criteria": self.triggered_criteria,
            "ccb_reference": self.ccb_reference,
            "competent_authority": self.competent_authority,
            "applicable_frameworks": self.applicable_frameworks,
        }


# ---------------------------------------------------------------------------
# Main assessment function
# ---------------------------------------------------------------------------


def assess_be_significance(
    sector: str,
    entity_type: str,
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    affected_persons_pct: float = 0.0,
    impact_duration_hours: float = 0,
    suspected_malicious: bool = False,
    cross_border: bool = False,
    trade_secret_exfiltration: bool = False,
    sector_specific: dict | None = None,  # Accepted for router compatibility, not used
) -> BeSignificanceResult:
    """Assess incident significance against Belgium CCB horizontal thresholds.

    Five categories (any one triggers):
    1. Suspected malicious CIA compromise
    2. Availability: ≥20% users for ≥1h
    3. Financial loss: >EUR 250K or >5% turnover
    4. Third-party damage: death, hospitalisation, injuries
    5. Recurring events (cannot evaluate from single incident — flagged in output)
    """
    data = _load()
    criteria = data["significant_incident_criteria"]
    triggered: list[str] = []

    # Check DORA exclusion
    dora_sectors = data["exclusions"]["dora_entities"]["sectors"]
    if sector in dora_sectors:
        return BeSignificanceResult(
            significant_incident=False,
            triggered_criteria=[],
            ccb_reference="DORA",
            competent_authority="BNB",
            applicable_frameworks=[{
                "framework": "DORA",
                "competent_authority": "Banque Nationale de Belgique",
                "note": "Banking/financial entities excluded from NIS2 notification (Art. 6, §3)",
            }],
        )

    # 1. Malicious CIA compromise
    if suspected_malicious and data_impact in ("accessed", "exfiltrated", "compromised", "systemic"):
        triggered.append("Malicious CIA compromise: suspected malicious unauthorized access")

    # 2. Availability
    # service_impact=unavailable implies 100% of users affected
    effective_pct = affected_persons_pct
    if service_impact in ("unavailable", "sustained") and effective_pct == 0:
        effective_pct = 100.0

    avail_threshold = criteria["availability"]["thresholds"][0]
    if effective_pct >= avail_threshold["users_pct"] and impact_duration_hours >= avail_threshold["duration_hours"]:
        triggered.append(
            f"Availability: ≥{avail_threshold['users_pct']}% users for ≥{avail_threshold['duration_hours']}h "
            f"(actual: {effective_pct:.0f}% for {impact_duration_hours:.1f}h)"
        )

    # 3. Financial loss (>EUR 250K or >5% turnover)
    fin = criteria["financial_loss"]
    if financial_impact in ("significant", "severe"):
        triggered.append(
            f"Financial loss: {financial_impact} impact (threshold: >{fin['threshold_eur']:,} EUR or >{fin['threshold_turnover_pct']}% turnover)"
        )
    if trade_secret_exfiltration:
        triggered.append("Financial loss: exfiltration of trade secrets (Directive 2016/943)")

    # 4. Third-party damage
    if safety_impact == "death":
        triggered.append("Third-party damage: death")
    elif safety_impact == "health_damage":
        triggered.append("Third-party damage: hospitalisation/injuries/disabilities")

    # Build frameworks
    frameworks = [{
        "framework": "NIS2",
        "competent_authority": "CCB",
        "notification_channel": data["notification_channel"],
        "early_warning_hours": data["notification_timeline"]["early_warning_hours"],
        "incident_notification_hours": data["notification_timeline"]["incident_notification_hours"],
        "final_report_days": data["notification_timeline"]["final_report_days"],
    }]

    return BeSignificanceResult(
        significant_incident=len(triggered) > 0,
        triggered_criteria=triggered,
        competent_authority="CCB",
        applicable_frameworks=frameworks,
    )
