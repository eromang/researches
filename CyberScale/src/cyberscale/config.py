"""Centralized configuration for CyberScale.

Loads valid enums from reference JSON where possible. Centralizes model
defaults that were previously scattered across 5+ modules.

Import from here instead of hardcoding values in individual modules.
"""

from __future__ import annotations

import json
from pathlib import Path


_REF_DIR = Path(__file__).parent.parent.parent / "data" / "reference"


# ---------------------------------------------------------------------------
# Valid enums — loaded from reference data
# ---------------------------------------------------------------------------

def _load_entity_types() -> set[str]:
    """Load entity type IDs from nis2_entity_types.json."""
    path = _REF_DIR / "nis2_entity_types.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ids = {et["id"] for et in data["entity_types"]}
    # Add non-NIS2 types not in the JSON
    ids.update({"generic_enterprise", "generic_sme", "generic_individual"})
    return ids


def _load_sectors() -> set[str]:
    """Load sector IDs from nis2_entity_types.json (unique sectors + non_nis2)."""
    path = _REF_DIR / "nis2_entity_types.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sectors = {et["sector"] for et in data["entity_types"]}
    sectors.add("non_nis2")
    return sectors


VALID_ENTITY_TYPES: set[str] = _load_entity_types()
VALID_SECTORS: set[str] = _load_sectors()

# Impact taxonomy — small fixed enums, not worth externalizing to JSON
VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}
VALID_FINANCIAL_IMPACT = {"none", "minor", "significant", "severe"}
VALID_SAFETY_IMPACT = {"none", "health_risk", "health_damage", "death"}


# ---------------------------------------------------------------------------
# Model defaults — previously scattered across 5 model classes
# ---------------------------------------------------------------------------

DEFAULT_MC_PASSES = 5
DEFAULT_MAX_LENGTH_SCORER = 192
DEFAULT_MAX_LENGTH_CONTEXTUAL = 256

# Confidence thresholds (max_prob -> confidence label)
CONFIDENCE_HIGH_THRESHOLD = 0.7
CONFIDENCE_MEDIUM_THRESHOLD = 0.4


def max_prob_to_confidence(max_prob: float) -> str:
    """Convert max probability to confidence label.

    Previously duplicated in scorer.py, contextual.py, technical.py,
    operational.py, scorer_multitask.py with identical logic.
    """
    if max_prob >= CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    if max_prob >= CONFIDENCE_MEDIUM_THRESHOLD:
        return "medium"
    return "low"
