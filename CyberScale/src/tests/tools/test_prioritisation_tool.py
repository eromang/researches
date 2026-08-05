"""Tests for the Phase 0 prioritisation MCP tool.

Beyond the mechanics, these assert the regulatory separation: the tool must not
become an input to NIS2 significance determination, and must not leak a rate.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from cyberscale.tools.prioritisation import _prioritise_vulnerabilities


def _v(cve, epss, published, **kw):
    return {"cve_id": cve, "epss": epss, "published": published, **kw}


class TestInputs:
    def test_requires_one_of_the_two_inputs(self):
        assert "error" in _prioritise_vulnerabilities()

    def test_ranks_supplied_records(self):
        r = _prioritise_vulnerabilities(
            vulnerabilities=[_v("CVE-A", 0.02, "2026-01-01"),
                             _v("CVE-B", 0.7, "2026-01-01")],
            as_of="2026-08-01",
        )
        assert [x["cve_id"] for x in r["ranked"]] == ["CVE-B", "CVE-A"]

    def test_resolves_cve_ids_through_lookup(self):
        lookup = MagicMock()
        lookup.lookup_cve.return_value = {
            "id": "CVE-2026-1", "epss": 0.4, "published": "2026-06-01",
            "exploited": True, "exploit_sources": ["shadowserver"],
        }
        r = _prioritise_vulnerabilities(cve_ids=["CVE-2026-1"], as_of="2026-08-01",
                                        lookup=lookup)
        assert r["ranked"][0]["cve_id"] == "CVE-2026-1"
        assert r["ranked"][0]["exploit_sources"] == ["shadowserver"]

    def test_unresolvable_cve_is_reported_not_ranked_last(self):
        lookup = MagicMock()
        lookup.lookup_cve.return_value = None
        r = _prioritise_vulnerabilities(cve_ids=["CVE-9999-0000"], as_of="2026-08-01",
                                        lookup=lookup)
        assert r["ranked"] == []
        assert r["unresolved"][0]["cve_id"] == "CVE-9999-0000"
        assert "not last in it" in " ".join(r["guidance"])

    def test_rejects_malformed_as_of(self):
        r = _prioritise_vulnerabilities(vulnerabilities=[_v("CVE-A", 0.1, "2026-01-01")],
                                        as_of="01/08/2026")
        assert "error" in r and "ISO date" in r["error"]

    def test_k_is_overridable(self):
        items = [_v("CVE-OLD", 0.30, "2020-01-01"), _v("CVE-NEW", 0.05, "2026-07-25")]
        at_one = _prioritise_vulnerabilities(vulnerabilities=items, k=1.0, as_of="2026-08-01")
        assert at_one["ranked"][0]["cve_id"] == "CVE-OLD"
        assert at_one["k"] == 1.0


class TestRegulatorySeparation:
    """The tool must stay on the Art. 21 side of the line."""

    def _payload(self):
        return _prioritise_vulnerabilities(
            vulnerabilities=[_v("CVE-A", 0.5, "2026-01-01")], as_of="2026-08-01")

    def test_declares_art_21_and_disclaims_art_23(self):
        scope = self._payload()["regulatory_scope"]
        assert "Art. 21" in scope
        assert "Art. 23" in scope and "NOT" in scope

    def test_emits_no_significance_determination(self):
        """A significance verdict here would invite use as an Art. 23 input.

        Checked structurally rather than by substring: the disclaimer legitimately
        contains the word "significance" while saying this is not one.
        """
        payload = self._payload()
        banned = {"significant_incident", "significance", "notifiable",
                  "early_warning", "t_level", "o_level", "triggered_criteria"}
        assert not banned & set(payload), f"top-level keys leak: {banned & set(payload)}"
        for entry in payload["ranked"]:
            assert not banned & set(entry), f"ranked entry leaks: {banned & set(entry)}"

    def test_emits_no_rate_or_count(self):
        payload = self._payload()
        banned = {"daily_hazard", "events_per_day", "expected_events",
                  "horizon_probability", "h_agg", "score", "hazard"}
        assert not banned & set(payload)
        for entry in payload["ranked"]:
            assert not banned & set(entry), (
                "the sort key must not be exposed: its magnitude carries no "
                "defensible interpretation"
            )

    def test_server_registers_it_separately_from_the_nis2_tools(self):
        """Phase 0 is its own surface, not folded into entity_incident."""
        import inspect
        from cyberscale.tools import entity_incident
        src = inspect.getsource(entity_incident)
        assert "prioritis" not in src.lower(), (
            "the NIS2 significance path must not reference prioritisation"
        )
