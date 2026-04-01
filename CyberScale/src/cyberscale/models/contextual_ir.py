"""Phase 2 — IR incident significance assessment (deterministic thresholds).

Implements quantitative threshold logic from Commission Implementing Regulation
(EU) 2024/2690, Articles 5-14. Used for IR entity types that have specific
per-sector thresholds for significant incident determination.

For non-IR entity types, use the NIS2 ML model in contextual.py instead.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


_THRESHOLDS_PATH = Path(__file__).parent.parent.parent.parent / "data" / "reference" / "ir_incident_thresholds.json"

_cached_thresholds: dict | None = None


def _load_thresholds() -> dict:
    global _cached_thresholds
    if _cached_thresholds is None:
        with open(_THRESHOLDS_PATH, encoding="utf-8") as f:
            _cached_thresholds = json.load(f)
    return _cached_thresholds


def get_ir_entity_types() -> set[str]:
    """Return the set of entity types governed by IR thresholds."""
    data = _load_thresholds()
    return set(data["ir_entity_types"])


IR_ENTITY_TYPES = None  # lazy-loaded


def is_ir_entity(entity_type: str) -> bool:
    """Check if an entity type falls under IR threshold logic."""
    global IR_ENTITY_TYPES
    if IR_ENTITY_TYPES is None:
        IR_ENTITY_TYPES = get_ir_entity_types()
    return entity_type in IR_ENTITY_TYPES


@dataclass
class IRAssessmentResult:
    """Result of IR significant incident assessment."""

    significant_incident: bool
    triggered_criteria: list[str]
    entity_type: str
    applicable_articles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "triggered_criteria": self.triggered_criteria,
            "entity_type": self.entity_type,
            "applicable_articles": self.applicable_articles,
        }


def assess_ir_significance(
    entity_type: str,
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    suspected_malicious: bool = False,
    impact_duration_hours: int = 0,
    cross_border: bool = False,
) -> IRAssessmentResult:
    """Assess incident significance using IR quantitative thresholds.

    Deterministic: returns True if any criterion is met.
    """
    data = _load_thresholds()
    criteria = data["criteria"]
    triggered: list[str] = []
    articles: list[str] = []

    # Service unavailability
    c = criteria["service_unavailability"]
    if service_impact in c["trigger_values"]:
        triggered.append("service_unavailability")
        articles.extend(c["articles"])

    # Service degradation + duration
    c = criteria["service_degradation_duration"]
    if service_impact in ("degraded", "unavailable", "sustained") and impact_duration_hours >= 1:
        triggered.append("service_degradation_duration")
        articles.extend(c["articles"])

    # Data integrity/confidentiality
    c = criteria["data_integrity_confidentiality"]
    if data_impact in c["trigger_values"]:
        triggered.append("data_integrity_confidentiality")
        articles.extend(c["articles"])

    # Affected persons threshold (per-entity-type)
    c = criteria["affected_persons_threshold"]
    threshold = c["thresholds"].get(entity_type, 0)
    if threshold > 0 and affected_persons_count >= threshold:
        triggered.append(f"affected_persons >= {threshold}")
        articles.extend(c["articles"])

    # Financial loss
    c = criteria["financial_loss"]
    if financial_impact in c["trigger_values"]:
        triggered.append("financial_loss")
        articles.extend(c["articles"])

    # Safety impact
    c = criteria["safety_impact"]
    if safety_impact in c["trigger_values"]:
        triggered.append("safety_impact")
        articles.extend(c["articles"])

    # Suspected malicious (always escalates for IR)
    c = criteria["suspected_malicious"]
    if suspected_malicious:
        triggered.append("suspected_malicious")
        articles.extend(c["articles"])

    # Cross-border impact
    c = criteria["cross_border_impact"]
    if cross_border:
        triggered.append("cross_border_impact")
        articles.extend(c["articles"])

    # Deduplicate articles preserving order
    seen = set()
    unique_articles = []
    for a in articles:
        if a not in seen:
            seen.add(a)
            unique_articles.append(a)

    return IRAssessmentResult(
        significant_incident=len(triggered) > 0,
        triggered_criteria=triggered,
        entity_type=entity_type,
        applicable_articles=unique_articles,
    )


@dataclass
class NIS2AssessmentResult:
    """Result of NIS2 ML-based significant incident assessment."""

    significant_incident: str  # "likely" / "unlikely" / "uncertain"
    severity: str              # Critical / High / Medium / Low
    confidence: str            # high / medium / low
    reporting_hint: str
    key_factors: list[str]

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "severity": self.severity,
            "confidence": self.confidence,
            "reporting_hint": self.reporting_hint,
            "key_factors": self.key_factors,
        }


def assess_nis2_significance(
    contextual_result,
    entity_affected: bool = False,
) -> NIS2AssessmentResult:
    """Assess incident significance using NIS2 ML model output.

    Maps severity + confidence to a significant_incident assessment:
    - Critical with high confidence → "likely"
    - High with high confidence → "likely"
    - Critical/High with medium confidence → "likely"
    - Medium with any confidence → "uncertain"
    - Low → "unlikely"
    """
    severity = contextual_result.severity
    confidence = contextual_result.confidence

    if severity in ("Critical", "High") and confidence in ("high", "medium"):
        sig = "likely"
    elif severity in ("Critical", "High"):
        sig = "likely"
    elif severity == "Medium":
        sig = "uncertain"
    else:
        sig = "unlikely"

    # Override: if entity is not affected, significance is lower
    if not entity_affected:
        if sig == "likely":
            sig = "uncertain"

    hints = {
        "likely": "This incident likely meets NIS2 Art. 23 significance criteria. Submit early warning within 24 hours.",
        "uncertain": "Significance uncertain. Monitor impact evolution and reassess within 24 hours.",
        "unlikely": "This incident is unlikely to meet NIS2 significance criteria based on current assessment.",
    }

    return NIS2AssessmentResult(
        significant_incident=sig,
        severity=severity,
        confidence=confidence,
        reporting_hint=hints[sig],
        key_factors=contextual_result.key_factors,
    )
