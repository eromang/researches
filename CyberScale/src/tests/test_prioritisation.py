"""Tests for Phase 0 remediation prioritisation.

The properties under test are the ones the validation work established, not
implementation details: the score is a sort key with no reportable magnitude,
k=1 collapses to EPSS ordering, unrankable entries are excluded rather than
sorted last, and no rate ever reaches the output.
"""

from __future__ import annotations

from datetime import date

import pytest

from cyberscale.prioritisation import (
    DEFAULT_K,
    T_ELM,
    PrioritisationResult,
    hazard_sort_key,
    rank,
)


def _v(cve, epss, published, **kw):
    return {"cve_id": cve, "epss": epss, "published": published, **kw}


class TestSortKey:
    def test_k_equals_one_reproduces_epss_ordering(self):
        """At k=1 the Weibull reduces to the exponential, which is a strictly
        increasing transform of EPSS — so age stops mattering entirely."""
        pairs = [(0.01, 5), (0.5, 900), (0.2, 30), (0.9, 1), (0.001, 4000)]
        by_hazard = sorted(pairs, key=lambda p: -hazard_sort_key(p[0], p[1], k=1.0))
        by_epss = sorted(pairs, key=lambda p: -p[0])
        assert by_hazard == by_epss

    def test_age_reorders_only_when_k_below_one(self):
        """Two vulnerabilities, same EPSS, different ages."""
        young = hazard_sort_key(0.1, age_days=2, k=0.55)
        old = hazard_sort_key(0.1, age_days=2000, k=0.55)
        assert young > old, "for k<1 hazard decays with age"

        assert hazard_sort_key(0.1, 2, k=1.0) == pytest.approx(
            hazard_sort_key(0.1, 2000, k=1.0)
        ), "at k=1 age is irrelevant"

    def test_scale_anchoring_recovers_the_epss_input(self):
        """lambda is derived so the cumulative hazard over the ELM horizon
        equals -ln(1-p). This is the model's own anchoring invariant."""
        import math
        for p in (0.001, 0.05, 0.5, 0.97231):
            for k in (0.4, 0.55, 0.605, 1.0, 1.3):
                lam = T_ELM / (-math.log1p(-p)) ** (1.0 / k)
                cumulative = (T_ELM / lam) ** k
                assert cumulative == pytest.approx(-math.log1p(-p), rel=1e-9)

    def test_age_floored_at_one_day(self):
        """For k<1 the hazard is singular at t=0; both reference
        implementations floor at one day, so a zero-age CVE must not blow up."""
        v = hazard_sort_key(0.5, age_days=0, k=0.55)
        assert v == hazard_sort_key(0.5, age_days=1, k=0.55)
        assert v < float("inf")

    def test_rejects_out_of_range_inputs(self):
        with pytest.raises(ValueError):
            hazard_sort_key(1.5, 10)
        with pytest.raises(ValueError):
            hazard_sort_key(0.1, -5)
        with pytest.raises(ValueError):
            hazard_sort_key(0.1, 10, k=0)

    def test_epss_zero_and_one_stay_finite(self):
        assert hazard_sort_key(0.0, 10) >= 0
        assert hazard_sort_key(1.0, 10) < float("inf")


class TestRanking:
    def test_ranks_are_dense_and_ordered(self):
        r = rank(
            [_v("CVE-1", 0.01, "2026-07-01"), _v("CVE-2", 0.9, "2026-07-01"),
             _v("CVE-3", 0.3, "2026-07-01")],
            as_of=date(2026, 8, 1),
        )
        assert [x.rank for x in r.ranked] == [1, 2, 3]
        assert r.ranked[0].cve_id == "CVE-2"

    def test_unrankable_entries_are_excluded_not_sorted_last(self):
        """A vulnerability we cannot score is an unknown. Putting it at the
        bottom of a remediation queue asserts it is least urgent."""
        r = rank(
            [_v("CVE-OK", 0.5, "2026-01-01"),
             _v("CVE-NOEPSS", None, "2026-01-01"),
             _v("CVE-NODATE", 0.5, None)],
            as_of=date(2026, 8, 1),
        )
        ids = [x.cve_id for x in r.ranked]
        assert ids == ["CVE-OK"]
        reasons = {s["cve_id"]: s["reason"] for s in r.skipped}
        assert "no EPSS score" in reasons["CVE-NOEPSS"]
        assert "no usable publication date" in reasons["CVE-NODATE"]

    def test_ties_break_reproducibly(self):
        items = [_v(f"CVE-{i}", 0.2, "2026-01-01") for i in range(5)]
        a = [x.cve_id for x in rank(items, as_of=date(2026, 8, 1)).ranked]
        b = [x.cve_id for x in rank(list(reversed(items)), as_of=date(2026, 8, 1)).ranked]
        assert a == b

    def test_k_is_configurable_and_changes_the_order(self):
        items = [_v("CVE-OLD-HIGH", 0.30, "2020-01-01"),
                 _v("CVE-NEW-LOW", 0.05, "2026-07-25")]
        low_k = [x.cve_id for x in rank(items, k=0.4, as_of=date(2026, 8, 1)).ranked]
        at_one = [x.cve_id for x in rank(items, k=1.0, as_of=date(2026, 8, 1)).ranked]
        assert at_one[0] == "CVE-OLD-HIGH", "k=1 ignores age, so higher EPSS wins"
        assert low_k[0] == "CVE-NEW-LOW", "strong age decay promotes the fresh CVE"

    def test_default_k_is_not_the_paper_value(self):
        """0.605 is the paper's calibrated value and CIRCL's API default. It
        falls outside every properly-estimated interval, and ranks worse."""
        assert DEFAULT_K == 0.55
        assert DEFAULT_K != 0.605

    def test_exploited_is_annotated_not_scored(self):
        r = rank([_v("CVE-X", 0.2, "2026-01-01", exploited=True,
                     exploit_sources=["shadowserver"])], as_of=date(2026, 8, 1))
        note = " ".join(r.ranked[0].notes)
        assert "already recorded as exploited" in note
        assert "shadowserver" in note

    def test_unknown_exploitation_is_not_reported_as_no(self):
        r = rank([_v("CVE-Y", 0.2, "2026-01-01", exploited=None)], as_of=date(2026, 8, 1))
        assert "not a 'no'" in " ".join(r.ranked[0].notes)

    def test_top_n_truncates(self):
        items = [_v(f"CVE-{i}", i / 100, "2026-01-01") for i in range(1, 21)]
        assert len(rank(items, top_n=5, as_of=date(2026, 8, 1)).ranked) == 5


class TestOutputContract:
    """The output must not carry anything the evidence cannot support."""

    def _payload(self):
        return rank([_v("CVE-1", 0.5, "2026-01-01", exploited=False)],
                    as_of=date(2026, 8, 1)).to_dict()

    def test_no_rate_or_count_anywhere_in_the_output(self):
        import json
        blob = json.dumps(self._payload()).lower()
        for banned in ("daily_hazard", "expected_events", "events_per_day",
                       "horizon_probability", "h_agg", "hazard_score"):
            assert banned not in blob, f"{banned} must not reach the output"

    def test_states_what_it_does_not_provide(self):
        d = self._payload()
        assert "not_provided" in d
        assert "55x" in d["not_provided"]

    def test_declares_its_regulatory_scope(self):
        d = self._payload()
        assert "Art. 21" in d["regulatory_scope"]
        assert "NOT" in d["regulatory_scope"] and "Art. 23" in d["regulatory_scope"]

    def test_guidance_states_the_top_n_limitation(self):
        d = self._payload()
        joined = " ".join(d["guidance"])
        assert "top 100" in joined and "wash" in joined, (
            "the measured absence of gain at low N must be surfaced, not buried"
        )
