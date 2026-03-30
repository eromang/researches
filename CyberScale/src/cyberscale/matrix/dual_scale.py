"""Blueprint dual-scale incident severity matrix.

Implements Council Recommendation C/2025/3445, Provision 30.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MatrixResult:
    """Result of a dual-scale matrix classification."""

    t_level: str
    o_level: str
    classification: str
    label: str
    provision: str


VALID_T_LEVELS = {"T1", "T2", "T3", "T4"}
VALID_O_LEVELS = {"O1", "O2", "O3", "O4"}

MATRIX = {
    "T4": {"O4": "cyber_crisis", "O3": "cyber_crisis", "O2": "large_scale", "O1": "large_scale"},
    "T3": {"O4": "cyber_crisis", "O3": "large_scale", "O2": "large_scale", "O1": "significant"},
    "T2": {"O4": "large_scale", "O3": "large_scale", "O2": "significant", "O1": "significant"},
    "T1": {"O4": "large_scale", "O3": "significant", "O2": "significant", "O1": "below_threshold"},
}

CLASSIFICATIONS = {
    "below_threshold": {"label": "Below threshold", "provision": "7(a)"},
    "significant": {"label": "Significant", "provision": "7(b)"},
    "large_scale": {"label": "Large-scale", "provision": "7(c)"},
    "cyber_crisis": {"label": "Cyber crisis", "provision": "7(d)"},
}


def classify_incident(t_level: str, o_level: str) -> MatrixResult:
    """Classify an incident given T-level and O-level."""
    if t_level not in VALID_T_LEVELS:
        raise ValueError(f"Invalid T-level: {t_level}. Must be one of {VALID_T_LEVELS}")
    if o_level not in VALID_O_LEVELS:
        raise ValueError(f"Invalid O-level: {o_level}. Must be one of {VALID_O_LEVELS}")

    classification = MATRIX[t_level][o_level]
    info = CLASSIFICATIONS[classification]

    return MatrixResult(
        t_level=t_level,
        o_level=o_level,
        classification=classification,
        label=info["label"],
        provision=info["provision"],
    )
