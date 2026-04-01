"""Early warning recommendation logic for NIS2 Art. 23(4)(a).

When an incident is assessed as significant, entities must submit an early
warning to the competent authority or CSIRT within 24 hours. This module
provides the recommendation output for entity-facing tools.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EarlyWarningRecommendation:
    """Early warning recommendation for an entity incident."""

    recommended: bool
    deadline: str          # "24h" per Art. 23(4)(a)
    required_content: list[str]
    next_step: str

    def to_dict(self) -> dict:
        return {
            "recommended": self.recommended,
            "deadline": self.deadline,
            "required_content": self.required_content,
            "next_step": self.next_step,
        }


def recommend_early_warning(
    significant_incident: bool | str,
    suspected_malicious: bool = False,
    cross_border: bool = False,
) -> EarlyWarningRecommendation:
    """Generate early warning recommendation based on significance assessment.

    Args:
        significant_incident: True/False for IR entities, or
            "likely"/"unlikely"/"uncertain" for NIS2 entities.
        suspected_malicious: Whether the incident is suspected malicious.
        cross_border: Whether the incident has cross-border impact.

    Returns:
        EarlyWarningRecommendation with structured guidance.
    """
    # Normalize to bool-ish
    if isinstance(significant_incident, str):
        is_significant = significant_incident == "likely"
        is_uncertain = significant_incident == "uncertain"
    else:
        is_significant = bool(significant_incident)
        is_uncertain = False

    if is_significant:
        required = ["Whether the incident is suspected to be caused by unlawful or malicious acts"]
        if suspected_malicious:
            required.append("Initial assessment of malicious nature and actor type if known")
        if cross_border:
            required.append("Whether the incident has or could have cross-border impact")
        required.append("Initial assessment of the incident scope and impact")

        return EarlyWarningRecommendation(
            recommended=True,
            deadline="24h",
            required_content=required,
            next_step=(
                "Submit early warning to competent authority or CSIRT within 24 hours "
                "per NIS2 Art. 23(4)(a). Follow up with incident notification within "
                "72 hours per Art. 23(4)(b) containing initial assessment, severity, "
                "impact, and indicators of compromise where available."
            ),
        )

    if is_uncertain:
        return EarlyWarningRecommendation(
            recommended=True,
            deadline="24h",
            required_content=[
                "Whether the incident is suspected to be caused by unlawful or malicious acts",
                "Current assessment of incident scope (may be preliminary)",
            ],
            next_step=(
                "Significance is uncertain — recommend submitting a precautionary early "
                "warning within 24 hours per NIS2 Art. 23(4)(a). Continue monitoring "
                "the incident and update assessment as impact evolves."
            ),
        )

    return EarlyWarningRecommendation(
        recommended=False,
        deadline="24h",
        required_content=[],
        next_step=(
            "Based on current assessment, this incident does not appear to meet NIS2 "
            "Art. 23 significance criteria. Continue monitoring and reassess if impact "
            "changes. No early warning required at this time."
        ),
    )
