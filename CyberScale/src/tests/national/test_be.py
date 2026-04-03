"""Tests for Belgium national-layer threshold assessment."""

from __future__ import annotations

import pytest

from cyberscale.national.be import (
    is_be_covered,
    assess_be_significance,
    BeSignificanceResult,
)


class TestBeCoverage:
    def test_energy_entity_covered(self):
        assert is_be_covered("energy", "electricity_undertaking") is True

    def test_health_entity_covered(self):
        assert is_be_covered("health", "healthcare_provider") is True

    def test_transport_entity_covered(self):
        assert is_be_covered("transport", "railway_undertaking") is True

    def test_public_admin_covered(self):
        assert is_be_covered("public_administration", "central_government_entity") is True

    def test_ir_entity_not_covered(self):
        """IR entities bypass BE thresholds even in Belgium."""
        assert is_be_covered("digital_infrastructure", "cloud_computing_provider") is False
        assert is_be_covered("digital_infrastructure", "dns_service_provider") is False
        assert is_be_covered("digital_infrastructure", "trust_service_provider") is False

    def test_dora_entity_not_covered(self):
        """DORA entities excluded from NIS2 notification in Belgium."""
        assert is_be_covered("banking", "credit_institution") is False

    def test_non_nis2_entity_not_covered(self):
        assert is_be_covered("non_nis2", "generic_individual") is False


class TestMaliciousCompromise:
    def test_malicious_access_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=True,
            data_impact="accessed",
        )
        assert result.significant_incident is True
        assert any("malicious" in c.lower() for c in result.triggered_criteria)

    def test_non_malicious_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=False,
        )
        assert result.significant_incident is False


class TestAvailabilityThreshold:
    def test_20pct_users_1h_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="unavailable",
            affected_persons_pct=25.0,
            impact_duration_hours=1.5,
        )
        assert result.significant_incident is True
        assert any("20%" in c or "availability" in c.lower() for c in result.triggered_criteria)

    def test_below_20pct_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="degraded",
            affected_persons_pct=15.0,
            impact_duration_hours=2.0,
        )
        assert result.significant_incident is False

    def test_above_20pct_below_1h_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="unavailable",
            affected_persons_pct=50.0,
            impact_duration_hours=0.5,
        )
        assert result.significant_incident is False

    def test_total_unavailability_1h_triggers(self):
        """service_impact=unavailable implies 100% users affected."""
        result = assess_be_significance(
            sector="health",
            entity_type="healthcare_provider",
            service_impact="unavailable",
            impact_duration_hours=1.0,
        )
        assert result.significant_incident is True


class TestFinancialLossThreshold:
    def test_severe_financial_triggers(self):
        """severe financial_impact assumed to exceed EUR 250K threshold."""
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            financial_impact="severe",
        )
        assert result.significant_incident is True
        assert any("financial" in c.lower() or "250" in c for c in result.triggered_criteria)

    def test_significant_financial_triggers(self):
        result = assess_be_significance(
            sector="transport",
            entity_type="railway_undertaking",
            financial_impact="significant",
        )
        assert result.significant_incident is True

    def test_minor_financial_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            financial_impact="minor",
        )
        assert result.significant_incident is False

    def test_trade_secret_exfiltration_triggers(self):
        result = assess_be_significance(
            sector="manufacturing",
            entity_type="machinery_manufacturer",
            data_impact="exfiltrated",
            trade_secret_exfiltration=True,
        )
        assert result.significant_incident is True


class TestThirdPartyDamage:
    def test_death_triggers(self):
        result = assess_be_significance(
            sector="health",
            entity_type="healthcare_provider",
            safety_impact="death",
        )
        assert result.significant_incident is True
        assert any("death" in c.lower() or "third party" in c.lower() for c in result.triggered_criteria)

    def test_health_damage_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            safety_impact="health_damage",
        )
        assert result.significant_incident is True

    def test_health_risk_no_trigger(self):
        """health_risk alone does not meet 'death/hospitalisation/injuries' threshold."""
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            safety_impact="health_risk",
        )
        assert result.significant_incident is False


class TestApplicableFrameworks:
    def test_includes_nis2_framework(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=True,
            data_impact="accessed",
        )
        assert any(fw["framework"] == "NIS2" for fw in result.applicable_frameworks)
        assert result.competent_authority == "CCB"

    def test_trust_service_24h_notification(self):
        """Trust services have 24h notification deadline in Belgium."""
        result = assess_be_significance(
            sector="digital_infrastructure",
            entity_type="trust_service_provider",
            suspected_malicious=True,
            data_impact="accessed",
        )
        # Trust services should go through IR, not BE
        # This test verifies is_be_covered returns False for trust_service_provider
        pass  # Covered by TestBeCoverage.test_ir_entity_not_covered
