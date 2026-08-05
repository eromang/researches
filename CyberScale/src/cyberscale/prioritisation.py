"""Phase 0 — remediation prioritisation. Ranking only, never a rate.

CyberScale scores how bad a vulnerability is. This module answers the other
question: given finite capacity, which one first. It is the age-adjusted
exploit-likelihood term from the local exploit hazard model
([arXiv:2607.24618](https://arxiv.org/abs/2607.24618)), used purely as a sort key.

Scope is deliberately narrow, and the boundaries come from measurement rather
than caution. Full validation: `../../Exploit-Hazard-Validation/`.

**Ranking only.** The model's headline output is "expected exploit events per
day". FIRST defines an EPSS score as the probability that one of its data
partners' sensors detects exploitation activity, so that figure counts
third-party sensor detections — not compromises, not incidents. Measured
against the richest public exploitation feed it runs about 55x high, stably.
The offset is a unit mismatch rather than an error, which is worse: the number
is not so much wrong as not about anything a defender can observe. So nothing
here emits a rate, an event count, or a probability of at least one event.

**What the age term actually buys.** Over four frozen snapshots and three
ground-truth sources, age-adjusted ranking beat raw EPSS on AUC-ROC in 11 of 11
cells (+0.025 to +0.086) and improved coverage at the top 5,000 in 10 of 11.
At the top 100 and top 1,000 it is a wash — 4 better, 4 worse, 3 flat. The gain
is in the tail: it rescues true positives buried deep in the EPSS ordering. It
does not tell a team with capacity for a hundred fixes what to do on Monday, and
`rank()` says so in its own output.

**`k` is configuration, not a constant.** It varies with who reported the
exploitation (0.52 for curated catalogues, 0.72 for sensor telemetry), drifts
with the observation date (0.684 in Jan 2025, 0.576 in Aug 2026), and moves
+0.025 if the longest 10% of observations are dropped. The default here is a
*ranking* choice, not a calibration claim — see DEFAULT_K.

**Outside the NIS2 path.** Art. 23 significance is impact-based; an incident
does not become notifiable because a vulnerability was likely to be exploited.
Hazard belongs to Art. 21 risk management. Nothing in this module may be
consumed by the significance or incident-classification surfaces.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)

#: EPSS forecast horizon in days. The scale parameter is anchored so that the
#: probability of exploitation over this window reproduces the EPSS input.
T_ELM = 30.0

#: Default Weibull shape.
#:
#: NOT 0.605, the paper's calibrated value that CIRCL's vulnerability-lookup
#: ships as its API default. Two measured reasons:
#:
#: 1. Properly estimated with censoring handled, k is 0.52 for curated
#:    catalogues and 0.72 for sensor telemetry. 0.605 falls outside every one
#:    of those intervals.
#: 2. For *ranking* — which is all this module does — lower k performs better.
#:    k=0.550 edged k=0.605 on both AUC-ROC and AUC-PR across the snapshots,
#:    and k=0.834, the value that best *describes* observed exploitation
#:    timing, was the worst ranker of the three tested.
#:
#: That tension is real and unresolved: the k that fits the data is not the k
#: that prioritises well. This default resolves it in favour of ranking,
#: because ranking is this module's only job.
DEFAULT_K = 0.55

#: Age is floored at one day. For k < 1 the Weibull hazard is singular at t = 0,
#: and both the paper's reference implementation and CIRCL's use the same floor.
_MIN_AGE_DAYS = 1.0

_EPS = 1e-12


def hazard_sort_key(epss: float, age_days: float, k: float = DEFAULT_K) -> float:
    """Age-adjusted exploit likelihood, for ordering only.

    This is the Weibull instantaneous hazard of the local exploit hazard model
    (Eq. 6-7), and its *magnitude carries no defensible interpretation* — see
    the module docstring. Use it to sort; do not display it, sum it, or convert
    it to an expected count.

    At k = 1 it reduces to the exponential case, which is a strictly increasing
    transform of EPSS, so the ranking becomes identical to ranking on EPSS.
    That is the model's own documented degenerate case and a useful control.
    """
    if not 0.0 <= epss <= 1.0:
        raise ValueError(f"epss must lie in [0, 1], got {epss}")
    if k <= 0:
        raise ValueError(f"k must be positive, got {k}")
    if age_days < 0:
        raise ValueError(f"age_days must be non-negative, got {age_days}")

    p = min(max(float(epss), _EPS), 1.0 - _EPS)
    # log1p(-p), not log(1 - p): the latter loses relative precision for small p.
    cumulative = -math.log1p(-p)
    lam = T_ELM / cumulative ** (1.0 / k)
    t = max(float(age_days), _MIN_AGE_DAYS)
    return (k / lam) * (t / lam) ** (k - 1.0)


@dataclass
class RankedVulnerability:
    """One vulnerability's position in a remediation queue.

    Carries the inputs that produced the position so the ordering can be
    argued with. Deliberately carries no rate, count or probability.
    """

    cve_id: str
    rank: int
    epss: float
    age_days: int
    exploited: bool | None = None
    exploit_sources: list[str] = field(default_factory=list)
    published: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cve_id": self.cve_id,
            "rank": self.rank,
            "epss": self.epss,
            "age_days": self.age_days,
            "exploited": self.exploited,
            "exploit_sources": self.exploit_sources,
            "published": self.published,
            "notes": self.notes,
        }


@dataclass
class PrioritisationResult:
    """A ranked remediation queue, with the caveats the evidence requires."""

    ranked: list[RankedVulnerability]
    k: float
    as_of: str
    skipped: list[dict[str, str]] = field(default_factory=list)
    guidance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ranked": [r.to_dict() for r in self.ranked],
            "k": self.k,
            "as_of": self.as_of,
            "skipped": self.skipped,
            "guidance": self.guidance,
            "not_provided": (
                "No exploit rate, event count, or probability of at least one event. "
                "The model's rate output is denominated in third-party sensor "
                "detections and runs ~55x above any observable feed; it is not "
                "reportable and is deliberately absent."
            ),
            "regulatory_scope": (
                "NIS2 Art. 21 risk management (what to remediate first). NOT an "
                "input to Art. 23 significance, which is impact-based."
            ),
        }


def _age_days(published: str | None, as_of: date) -> int | None:
    if not isinstance(published, str) or len(published) < 10:
        return None
    try:
        return (as_of - date.fromisoformat(published[:10])).days
    except ValueError:
        return None


def rank(
    vulnerabilities: Iterable[dict[str, Any]],
    k: float = DEFAULT_K,
    as_of: date | None = None,
    top_n: int | None = None,
) -> PrioritisationResult:
    """Rank vulnerabilities by age-adjusted exploit likelihood.

    Each input needs `cve_id`, `epss` and `published`; the shape returned by
    `UnifiedLookup.lookup_cve()` satisfies this directly. Entries missing either
    input are reported in `skipped` with the reason rather than dropped or
    silently sorted last — an unrankable vulnerability is an unknown, and
    placing it at the bottom of a remediation queue would assert the opposite.
    """
    as_of = as_of or date.today()
    scored: list[tuple[float, RankedVulnerability]] = []
    skipped: list[dict[str, str]] = []

    for v in vulnerabilities:
        cve_id = v.get("cve_id") or v.get("id") or "<unknown>"
        epss = v.get("epss")
        age = _age_days(v.get("published"), as_of)

        if epss is None:
            skipped.append({"cve_id": cve_id, "reason": "no EPSS score"})
            continue
        if age is None:
            skipped.append({"cve_id": cve_id, "reason": "no usable publication date"})
            continue

        notes: list[str] = []
        if v.get("exploited") is True:
            srcs = v.get("exploit_sources") or []
            notes.append(
                "already recorded as exploited"
                + (f" ({', '.join(srcs)})" if srcs else "")
                + " — a realised observation, not a forecast; treat as a floor on urgency"
            )
        elif v.get("exploited") is None and "exploited" in v:
            notes.append("exploitation status unknown — the lookup failed, this is not a 'no'")
        if age < 0:
            notes.append("publication date is in the future relative to as_of; age floored at 1 day")

        scored.append((
            hazard_sort_key(float(epss), max(age, 0), k),
            RankedVulnerability(
                cve_id=cve_id,
                rank=0,
                epss=float(epss),
                age_days=age,
                exploited=v.get("exploited"),
                exploit_sources=list(v.get("exploit_sources") or []),
                published=v.get("published"),
                notes=notes,
            ),
        ))

    # Descending score; ties broken by CVE id so the order is reproducible.
    scored.sort(key=lambda pair: (-pair[0], pair[1].cve_id))
    ranked = []
    for i, (_, rv) in enumerate(scored, 1):
        rv.rank = i
        ranked.append(rv)
    if top_n is not None:
        ranked = ranked[:top_n]

    guidance = [
        "Measured against observed exploitation, this ordering beats ranking on "
        "raw EPSS on AUC-ROC in 11 of 11 test cells, and improves coverage at "
        "the top 5,000 in 10 of 11.",
        "At the top 100 and top 1,000 it is a wash — 4 better, 4 worse, 3 flat. "
        "If your remediation capacity is in that range, expect no measurable "
        "gain over ranking on EPSS alone.",
        f"k={k} is a ranking choice, not a calibration claim. Properly estimated "
        "values are 0.52 for curated catalogues and 0.72 for sensor telemetry, "
        "and the best-fitting value is not the best-ranking one.",
    ]
    if skipped:
        guidance.append(
            f"{len(skipped)} vulnerabilities could not be ranked and are listed "
            "in `skipped`. They are not at the bottom of the queue; they are "
            "outside it."
        )

    logger.info("prioritisation.rank: %d ranked, %d skipped, k=%s",
                len(ranked), len(skipped), k)
    return PrioritisationResult(
        ranked=ranked, k=k, as_of=as_of.isoformat(), skipped=skipped, guidance=guidance,
    )
