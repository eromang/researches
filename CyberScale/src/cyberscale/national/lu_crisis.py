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
