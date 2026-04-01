"""Tests for Phase 3a national incident assessment."""


class TestAssessNationalIncident:
    def test_single_ms_classification(self):
        from cyberscale.tools.national_incident import _assess_national_incident

        notifications = [
            {"sector": "health", "ms_established": "LU",
             "service_impact": "unavailable", "data_impact": "exfiltrated",
             "financial_impact": "significant", "safety_impact": "health_damage",
             "affected_persons_count": 5000},
            {"sector": "banking", "ms_established": "LU",
             "service_impact": "degraded", "data_impact": "accessed",
             "financial_impact": "minor", "safety_impact": "none",
             "affected_persons_count": 1000},
        ]
        result = _assess_national_incident("Ransomware in LU", notifications)
        assert result["ms_established"] == "LU"
        assert result["technical"]["level"] in ("T3", "T4")
        assert result["technical"]["source"] == "deterministic"
        assert result["entity_count"] == 2

    def test_cross_border_flag(self):
        from cyberscale.tools.national_incident import _assess_national_incident

        notifications = [
            {"sector": "health", "ms_established": "LU", "ms_affected": ["DE", "FR"],
             "service_impact": "unavailable", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none",
             "affected_persons_count": 0},
        ]
        result = _assess_national_incident("Cross-border incident", notifications)
        assert result["cross_border"] is True
        assert result["csirt_network_sharing"] is True

    def test_no_cross_border(self):
        from cyberscale.tools.national_incident import _assess_national_incident

        notifications = [
            {"sector": "research", "ms_established": "LU",
             "service_impact": "partial", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none",
             "affected_persons_count": 0},
        ]
        result = _assess_national_incident("Local incident", notifications)
        assert result["cross_border"] is False
        assert result["csirt_network_sharing"] is False

    def test_multi_ms_rejected(self):
        from cyberscale.tools.national_incident import _assess_national_incident

        notifications = [
            {"sector": "health", "ms_established": "LU",
             "service_impact": "none", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none"},
            {"sector": "health", "ms_established": "DE",
             "service_impact": "none", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none"},
        ]
        result = _assess_national_incident("Mixed MS", notifications)
        assert "error" in result
        assert "single MS" in result["error"]


class TestValidateSingleMS:
    def test_valid(self):
        from cyberscale.tools.national_incident import _validate_single_ms
        ok, ms, err = _validate_single_ms([
            {"ms_established": "LU"}, {"ms_established": "LU"},
        ])
        assert ok is True
        assert ms == "LU"

    def test_mixed_ms(self):
        from cyberscale.tools.national_incident import _validate_single_ms
        ok, ms, err = _validate_single_ms([
            {"ms_established": "LU"}, {"ms_established": "DE"},
        ])
        assert ok is False

    def test_missing_ms(self):
        from cyberscale.tools.national_incident import _validate_single_ms
        ok, ms, err = _validate_single_ms([{"sector": "health"}])
        assert ok is False
