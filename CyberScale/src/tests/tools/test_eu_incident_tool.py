"""Tests for Phase 3b EU-CyCLONe incident assessment."""

from cyberscale.tools.eu_incident import (
    _assess_eu_incident,
    aggregate_cyclone_officers,
    _aggregate_national_to_eu,
)


class TestAggregateCycloneOfficers:
    def test_no_escalation(self):
        officers = [
            {"national_capacity_status": "normal", "political_sensitivity": "none",
             "escalation_recommendation": "none"},
        ]
        o, reasons = aggregate_cyclone_officers(officers, "O2")
        assert o == "O2"
        assert len(reasons) == 0

    def test_overwhelmed_escalates(self):
        officers = [
            {"national_capacity_status": "overwhelmed", "political_sensitivity": "none",
             "escalation_recommendation": "none"},
        ]
        o, reasons = aggregate_cyclone_officers(officers, "O2")
        assert o == "O3"
        assert any("overwhelmed" in r for r in reasons)

    def test_high_political_escalates(self):
        officers = [
            {"national_capacity_status": "normal", "political_sensitivity": "high",
             "escalation_recommendation": "none"},
        ]
        o, reasons = aggregate_cyclone_officers(officers, "O2")
        assert o == "O3"

    def test_escalation_request(self):
        officers = [
            {"national_capacity_status": "normal", "political_sensitivity": "none",
             "escalation_recommendation": "escalate"},
        ]
        o, reasons = aggregate_cyclone_officers(officers, "O2")
        assert o == "O3"

    def test_multiple_escalations_capped_at_2(self):
        officers = [
            {"national_capacity_status": "overwhelmed", "political_sensitivity": "high",
             "escalation_recommendation": "escalate"},
        ]
        o, _ = aggregate_cyclone_officers(officers, "O1")
        assert o == "O3"  # O1 + 2 = O3 (capped at +2)

    def test_o4_stays_o4(self):
        officers = [
            {"national_capacity_status": "overwhelmed", "political_sensitivity": "high",
             "escalation_recommendation": "escalate"},
        ]
        o, _ = aggregate_cyclone_officers(officers, "O4")
        assert o == "O4"  # already max

    def test_two_strained_escalates(self):
        officers = [
            {"national_capacity_status": "strained", "political_sensitivity": "none",
             "escalation_recommendation": "none"},
            {"national_capacity_status": "strained", "political_sensitivity": "none",
             "escalation_recommendation": "none"},
        ]
        o, reasons = aggregate_cyclone_officers(officers, "O2")
        assert o == "O3"
        assert any("strained" in r for r in reasons)

    def test_one_strained_no_escalation(self):
        officers = [
            {"national_capacity_status": "strained", "political_sensitivity": "none",
             "escalation_recommendation": "none"},
        ]
        o, _ = aggregate_cyclone_officers(officers, "O2")
        assert o == "O2"

    def test_de_escalate_ignored(self):
        officers = [
            {"national_capacity_status": "normal", "political_sensitivity": "none",
             "escalation_recommendation": "de-escalate"},
        ]
        o, _ = aggregate_cyclone_officers(officers, "O3")
        assert o == "O3"  # never de-escalate


class TestAggregateNationalToEU:
    def test_worst_case_across_ms(self):
        nationals = [
            {"technical": {"level": "T2"}, "operational": {"level": "O2"}, "ms_established": "LU"},
            {"technical": {"level": "T3"}, "operational": {"level": "O3"}, "ms_established": "DE"},
        ]
        t, o, _ = _aggregate_national_to_eu(nationals)
        assert t == "T3"
        assert o == "O3"

    def test_significant_3ms_escalation(self):
        """Significant (O2) in 3+ MS → minimum O3 at EU level."""
        nationals = [
            {"technical": {"level": "T2"}, "operational": {"level": "O2"}, "ms_established": "LU"},
            {"technical": {"level": "T2"}, "operational": {"level": "O2"}, "ms_established": "DE"},
            {"technical": {"level": "T1"}, "operational": {"level": "O2"}, "ms_established": "FR"},
        ]
        t, o, basis = _aggregate_national_to_eu(nationals)
        assert o == "O3"
        assert any("3" in b and "escalation" in b for b in basis)


class TestAssessEUIncident:
    def test_full_pipeline_no_officers(self):
        nationals = [
            {"technical": {"level": "T3"}, "operational": {"level": "O3"},
             "ms_established": "LU", "classification": "large_scale"},
            {"technical": {"level": "T2"}, "operational": {"level": "O2"},
             "ms_established": "DE", "classification": "significant"},
        ]
        result = _assess_eu_incident("Cross-border ransomware", nationals)
        assert result["eu_technical"]["level"] == "T3"
        assert result["classification"] in ("large_scale", "cyber_crisis")
        assert result["national_count"] == 2
        assert "LU" in result["ms_involved"]
        assert "DE" in result["ms_involved"]

    def test_officer_escalation(self):
        nationals = [
            {"technical": {"level": "T3"}, "operational": {"level": "O2"},
             "ms_established": "LU"},
            {"technical": {"level": "T2"}, "operational": {"level": "O2"},
             "ms_established": "DE"},
        ]
        officers = [
            {"ms": "DE", "national_capacity_status": "overwhelmed",
             "political_sensitivity": "high",
             "escalation_recommendation": "escalate",
             "intelligence_context": "Suspected state actor"},
        ]
        result = _assess_eu_incident("Incident", nationals, officers)
        assert result["eu_operational"]["officer_escalation"] is True
        assert int(result["eu_operational"]["level"][1]) > int(result["eu_operational"]["base_level"][1])
        assert result["coordination_level"] in ("eu_active", "full_ipcr")

    def test_intelligence_briefing_collected(self):
        nationals = [
            {"technical": {"level": "T2"}, "operational": {"level": "O2"},
             "ms_established": "LU"},
        ]
        officers = [
            {"ms": "LU", "national_capacity_status": "normal",
             "political_sensitivity": "none",
             "escalation_recommendation": "none",
             "intelligence_context": "Suspected APT29 campaign"},
        ]
        result = _assess_eu_incident("Incident", nationals, officers)
        assert "intelligence_briefing" in result
        assert result["intelligence_briefing"][0]["context"] == "Suspected APT29 campaign"

    def test_coordination_level_from_o_level(self):
        nationals = [
            {"technical": {"level": "T4"}, "operational": {"level": "O4"},
             "ms_established": "LU"},
        ]
        result = _assess_eu_incident("Crisis", nationals)
        assert result["coordination_level"] == "full_ipcr"
