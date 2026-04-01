"""Authority feedback store for rule calibration.

Stores authority decisions (suggested vs actual classification) and provides
regression analysis to identify systematic rule gaps.

The feedback loop is manual: authorities override → decisions accumulate →
periodic regression benchmark identifies patterns → rules adjusted.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


_DEFAULT_STORE_PATH = Path("data/feedback/authority_decisions.json")


@dataclass
class AuthorityDecision:
    """A single authority override decision."""

    incident_id: str
    timestamp: str
    ms_established: str

    # What the tool suggested
    suggested_t: str
    suggested_o: str
    suggested_classification: str

    # What the authority decided
    actual_t: str
    actual_o: str
    actual_classification: str

    # Context
    override_reason: str
    entity_count: int
    tier: str  # "national" or "eu"


def store_decision(
    decision: AuthorityDecision,
    path: Path = _DEFAULT_STORE_PATH,
) -> None:
    """Append a decision to the feedback store."""
    path.parent.mkdir(parents=True, exist_ok=True)

    decisions = load_decisions(path)
    decisions.append(asdict(decision))

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"version": "1.0", "decisions": decisions}, f, indent=2)
        f.write("\n")


def load_decisions(path: Path = _DEFAULT_STORE_PATH) -> list[dict]:
    """Load all decisions from the feedback store."""
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("decisions", [])


def compute_rule_accuracy(decisions: list[dict]) -> dict:
    """Compute rule accuracy vs authority ground truth.

    Returns per-level accuracy and overall accuracy for T and O levels.
    """
    if not decisions:
        return {"total": 0, "t_accuracy": 0.0, "o_accuracy": 0.0, "matrix_accuracy": 0.0}

    n = len(decisions)
    t_correct = sum(1 for d in decisions if d["suggested_t"] == d["actual_t"])
    o_correct = sum(1 for d in decisions if d["suggested_o"] == d["actual_o"])
    m_correct = sum(1 for d in decisions if d["suggested_classification"] == d["actual_classification"])

    # Per-level breakdown
    t_levels = {"T1", "T2", "T3", "T4"}
    o_levels = {"O1", "O2", "O3", "O4"}

    t_per_level = {}
    for level in t_levels:
        level_decisions = [d for d in decisions if d["actual_t"] == level]
        if level_decisions:
            correct = sum(1 for d in level_decisions if d["suggested_t"] == level)
            t_per_level[level] = correct / len(level_decisions)

    o_per_level = {}
    for level in o_levels:
        level_decisions = [d for d in decisions if d["actual_o"] == level]
        if level_decisions:
            correct = sum(1 for d in level_decisions if d["suggested_o"] == level)
            o_per_level[level] = correct / len(level_decisions)

    # Override patterns
    t_overrides = {}
    o_overrides = {}
    for d in decisions:
        if d["suggested_t"] != d["actual_t"]:
            key = f"{d['suggested_t']}→{d['actual_t']}"
            t_overrides[key] = t_overrides.get(key, 0) + 1
        if d["suggested_o"] != d["actual_o"]:
            key = f"{d['suggested_o']}→{d['actual_o']}"
            o_overrides[key] = o_overrides.get(key, 0) + 1

    return {
        "total": n,
        "t_accuracy": t_correct / n,
        "o_accuracy": o_correct / n,
        "matrix_accuracy": m_correct / n,
        "t_per_level": t_per_level,
        "o_per_level": o_per_level,
        "t_override_patterns": t_overrides,
        "o_override_patterns": o_overrides,
    }
