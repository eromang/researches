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

    def test_lu_entity_uses_national_thresholds(self):
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["energy sector", "SCADA impact"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="SCADA system compromise at Luxembourg electricity provider",
            sector="energy",
            entity_type="electricity_undertaking",
            ms_established="LU",
            impact_duration_hours=2,
            sector_specific={"pods_affected": 600, "voltage_level": "lv"},
        )
        assert result["significance"]["model"] == "national_lu_thresholds"
        assert result["significance"]["significant_incident"] is True
        assert any("LV-POD" in c for c in result["significance"]["triggered_criteria"])
        assert result["significance"]["ilr_reference"] == "ILR/N22/4"
        assert result["early_warning"]["recommended"] is True

    def test_lu_ir_entity_bypasses_national(self):
        """IR entities in LU still use IR thresholds, not LU national."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical", confidence="high",
            key_factors=["digital_infrastructure sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Cloud outage at Luxembourg provider",
            sector="digital_infrastructure",
            entity_type="cloud_computing_provider",
            ms_established="LU",
            service_impact="unavailable",
        )
        assert result["significance"]["model"] == "ir_thresholds"

    def test_lu_non_covered_sector_falls_back_to_nis2(self):
        """LU entity in sector not covered by ILR uses NIS2 ML."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Medium", confidence="medium",
            key_factors=["waste_water sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Wastewater system disruption in Luxembourg",
            sector="waste_water",
            entity_type="waste_water_operator",
            ms_established="LU",
        )
        assert result["significance"]["model"] == "nis2_ml"

    def test_be_entity_uses_national_thresholds(self):
        """BE entity routes to Belgium national thresholds."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["energy sector", "malicious access"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Malicious access to Belgian energy provider SCADA",
            sector="energy",
            entity_type="electricity_undertaking",
            ms_established="BE",
            suspected_malicious=True,
            data_impact="accessed",
        )
        assert result["significance"]["model"] == "national_be_thresholds"
        assert result["significance"]["significant_incident"] is True
        assert any("malicious" in c.lower() for c in result["significance"]["triggered_criteria"])
        assert result["significance"]["competent_authority"] == "CCB"

    def test_be_ir_entity_bypasses_national(self):
        """IR entities in BE still use IR thresholds, not BE national."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="Critical", confidence="high",
            key_factors=["digital_infrastructure sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Cloud outage at Belgian provider",
            sector="digital_infrastructure",
            entity_type="cloud_computing_provider",
            ms_established="BE",
            service_impact="unavailable",
        )
        assert result["significance"]["model"] == "ir_thresholds"

    def test_be_dora_entity_falls_to_nis2(self):
        """DORA entities in BE are excluded from BE national — fall to NIS2 ML."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["banking sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Belgian bank transaction disruption",
            sector="banking",
            entity_type="credit_institution",
            ms_established="BE",
            service_impact="unavailable",
            financial_impact="severe",
        )
        # DORA entities excluded by is_be_covered → falls through to NIS2 ML
        assert result["significance"]["model"] == "nis2_ml"

    def test_no_national_module_falls_back_to_nis2(self):
        """Entity in MS without national module uses NIS2 ML."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["energy sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Electricity outage in Germany",
            sector="energy",
            entity_type="electricity_undertaking",
            ms_established="DE",
        )
        assert result["significance"]["model"] == "nis2_ml"

    def test_lu_sector_specific_fields_passthrough(self):
        """sector_specific dict reaches LU assessment."""
        from cyberscale.tools.entity_incident import _assess_entity_incident

        mock_clf = MagicMock()
        mock_clf.predict.return_value = ContextualResult(
            severity="High", confidence="high",
            key_factors=["transport sector"],
        )
        result = _assess_entity_incident(
            mock_clf,
            description="Rail disruption in Luxembourg",
            sector="transport",
            entity_type="railway_undertaking",
            ms_established="LU",
            sector_specific={"trains_cancelled_pct": 6.0},
        )
        assert result["significance"]["model"] == "national_lu_thresholds"
        assert result["significance"]["significant_incident"] is True
        assert any("trains" in c for c in result["significance"]["triggered_criteria"])

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
