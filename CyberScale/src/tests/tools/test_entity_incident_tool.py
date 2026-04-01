"""Tests for assess_entity_incident MCP tool helper."""

from unittest.mock import MagicMock

from cyberscale.models.contextual import ContextualResult


class TestAssessEntityIncident:
    def test_ir_entity_uses_thresholds(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical", confidence="high",
            key_factors=["digital_infrastructure sector", "unavailable service impact"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Cloud platform outage affecting thousands of users",
            sector="digital_infrastructure",
            entity_type="cloud_computing_provider",
            ms_established="DE",
            service_impact="unavailable",
            affected_persons_count=5000,
            suspected_malicious=True,
        )
        assert result["severity"] == "Critical"
        assert result["significance"]["model"] == "ir_thresholds"
        assert result["significance"]["significant_incident"] is True
        assert "service_unavailability" in result["significance"]["triggered_criteria"]
        assert result["early_warning"]["recommended"] is True
        assert result["early_warning"]["deadline"] == "24h"

    def test_nis2_entity_uses_ml(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["health sector", "exfiltrated data impact"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Ransomware encrypted hospital patient records",
            sector="health",
            entity_type="healthcare_provider",
            ms_established="FR",
            ms_affected=["DE"],
            data_impact="exfiltrated",
        )
        assert result["severity"] == "High"
        assert result["significance"]["model"] == "nis2_ml"
        assert result["significance"]["significant_incident"] == "likely"
        assert result["early_warning"]["recommended"] is True
        assert result["cross_border"] is True

    def test_low_severity_no_early_warning(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low", confidence="high",
            key_factors=["non_nis2 sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Minor port scan detected",
            sector="non_nis2",
            entity_type="generic_enterprise",
        )
        assert result["severity"] == "Low"
        assert result["significance"]["model"] == "nis2_ml"
        assert result["significance"]["significant_incident"] == "unlikely"
        assert result["early_warning"]["recommended"] is False

    def test_ir_no_criteria_met(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Low", confidence="medium",
            key_factors=["digital_infrastructure sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Minor config drift on DNS server",
            sector="digital_infrastructure",
            entity_type="dns_service_provider",
        )
        assert result["significance"]["model"] == "ir_thresholds"
        assert result["significance"]["significant_incident"] is False
        assert result["early_warning"]["recommended"] is False

    def test_output_structure(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="medium",
            key_factors=["energy sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="SCADA compromise",
            sector="energy",
            entity_type="electricity_undertaking",
            ms_established="DE",
            service_impact="degraded",
            impact_duration_hours=4,
        )
        # Required top-level keys
        assert "severity" in result
        assert "confidence" in result
        assert "key_factors" in result
        assert "sector" in result
        assert "entity_type" in result
        assert "ms_established" in result
        assert "cross_border" in result
        assert "significance" in result
        assert "early_warning" in result
        # Significance structure
        sig = result["significance"]
        assert "significant_incident" in sig
        assert "model" in sig
        # Early warning structure
        ew = result["early_warning"]
        assert "recommended" in ew
        assert "deadline" in ew
        assert "next_step" in ew
