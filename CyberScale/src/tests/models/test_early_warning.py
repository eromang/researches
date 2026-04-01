"""Tests for early warning recommendation logic."""

from cyberscale.models.early_warning import recommend_early_warning


class TestEarlyWarningIR:
    def test_significant_recommends(self):
        ew = recommend_early_warning(significant_incident=True)
        assert ew.recommended is True
        assert ew.deadline == "24h"
        assert len(ew.required_content) >= 1

    def test_not_significant_not_recommended(self):
        ew = recommend_early_warning(significant_incident=False)
        assert ew.recommended is False
        assert len(ew.required_content) == 0

    def test_malicious_adds_content(self):
        ew = recommend_early_warning(significant_incident=True, suspected_malicious=True)
        assert any("malicious" in c.lower() for c in ew.required_content)

    def test_cross_border_adds_content(self):
        ew = recommend_early_warning(significant_incident=True, cross_border=True)
        assert any("cross-border" in c.lower() for c in ew.required_content)


class TestEarlyWarningNIS2:
    def test_likely_recommends(self):
        ew = recommend_early_warning(significant_incident="likely")
        assert ew.recommended is True
        assert ew.deadline == "24h"

    def test_uncertain_recommends_precautionary(self):
        ew = recommend_early_warning(significant_incident="uncertain")
        assert ew.recommended is True
        assert "precautionary" in ew.next_step.lower() or "uncertain" in ew.next_step.lower()

    def test_unlikely_not_recommended(self):
        ew = recommend_early_warning(significant_incident="unlikely")
        assert ew.recommended is False

    def test_to_dict(self):
        ew = recommend_early_warning(significant_incident="likely", suspected_malicious=True)
        d = ew.to_dict()
        assert d["recommended"] is True
        assert d["deadline"] == "24h"
        assert isinstance(d["required_content"], list)
        assert isinstance(d["next_step"], str)
