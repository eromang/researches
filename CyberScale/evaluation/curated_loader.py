"""Loader and validator for curated incident benchmark datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

VALID_T_LEVELS = {"T1", "T2", "T3", "T4"}
VALID_O_LEVELS = {"O1", "O2", "O3", "O4"}
VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_CASCADING = {"none", "limited", "cross_sector", "uncontrolled"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}
VALID_ENTITY_RELEVANCE = {"non_essential", "essential", "high_relevance", "systemic"}
VALID_CROSS_BORDER = {"none", "limited", "significant", "systemic"}


@dataclass
class CuratedIncident:
    """A single curated incident with ground-truth labels."""

    id: str
    name: str
    date: str
    sources: list[str]
    description: str
    t_fields: dict
    o_fields: dict
    expected_t: str
    expected_o: str
    rationale: dict


def load_curated_incidents(path: Path) -> list[CuratedIncident]:
    """Load and validate curated incidents from a JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    incidents = []

    for raw in data["incidents"]:
        _validate_incident(raw)
        incidents.append(CuratedIncident(
            id=raw["id"],
            name=raw["name"],
            date=raw["date"],
            sources=raw["sources"],
            description=raw["description"],
            t_fields=raw["t_fields"],
            o_fields=raw["o_fields"],
            expected_t=raw["expected_t"],
            expected_o=raw["expected_o"],
            rationale=raw["rationale"],
        ))

    return incidents


def _validate_incident(raw: dict) -> None:
    """Validate a single incident dict, raising ValueError on problems."""
    inc_id = raw.get("id", "unknown")

    t = raw["expected_t"]
    if t not in VALID_T_LEVELS:
        raise ValueError(f"{inc_id}: invalid expected_t '{t}', must be one of {VALID_T_LEVELS}")

    o = raw["expected_o"]
    if o not in VALID_O_LEVELS:
        raise ValueError(f"{inc_id}: invalid expected_o '{o}', must be one of {VALID_O_LEVELS}")

    tf = raw["t_fields"]
    if tf["service_impact"] not in VALID_SERVICE_IMPACT:
        raise ValueError(f"{inc_id}: invalid service_impact '{tf['service_impact']}'")
    if tf["cascading"] not in VALID_CASCADING:
        raise ValueError(f"{inc_id}: invalid cascading '{tf['cascading']}'")
    if tf["data_impact"] not in VALID_DATA_IMPACT:
        raise ValueError(f"{inc_id}: invalid data_impact '{tf['data_impact']}'")

    of = raw["o_fields"]
    if of["entity_relevance"] not in VALID_ENTITY_RELEVANCE:
        raise ValueError(f"{inc_id}: invalid entity_relevance '{of['entity_relevance']}'")
    if of["cross_border_pattern"] not in VALID_CROSS_BORDER:
        raise ValueError(f"{inc_id}: invalid cross_border_pattern '{of['cross_border_pattern']}'")
