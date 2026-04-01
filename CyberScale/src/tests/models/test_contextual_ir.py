"""Tests for Phase 2 — IR/NIS2 model split and significance assessment."""

from __future__ import annotations

import pytest

from cyberscale.models.contextual_ir import (
    is_ir_entity,
    assess_ir_significance,
    assess_nis2_significance,
    IRAssessmentResult,
    NIS2AssessmentResult,
    get_ir_entity_types,
)
from cyberscale.models.contextual import ContextualResult


class TestIREntityRouting:
    def test_ir_entity_types_loaded(self):
        ir_types = get_ir_entity_types()
        assert len(ir_types) >= 10
        assert "cloud_computing_provider" in ir_types
        assert "dns_service_provider" in ir_types

    def test_is_ir_entity_true(self):
        assert is_ir_entity("cloud_computing_provider") is True
        assert is_ir_entity("dns_service_provider") is True
        assert is_ir_entity("managed_service_provider") is True
        assert is_ir_entity("online_marketplace_provider") is True

    def test_is_ir_entity_false(self):
        assert is_ir_entity("healthcare_provider") is False
        assert is_ir_entity("credit_institution") is False
        assert is_ir_entity("generic_enterprise") is False
        assert is_ir_entity("electricity_undertaking") is False


class TestIRAssessment:
    def test_service_unavailability_triggers(self):
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            service_impact="unavailable",
        )
        assert result.significant_incident is True
        assert "service_unavailability" in result.triggered_criteria

    def test_data_compromise_triggers(self):
        result = assess_ir_significance(
            entity_type="dns_service_provider",
            data_impact="exfiltrated",
        )
        assert result.significant_incident is True
        assert "data_integrity_confidentiality" in result.triggered_criteria

    def test_affected_persons_threshold(self):
        # cloud_computing_provider threshold is 1000
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            affected_persons_count=1000,
        )
        assert result.significant_incident is True
        assert any("affected_persons" in c for c in result.triggered_criteria)

    def test_below_threshold_not_triggered(self):
        # cloud_computing_provider threshold is 1000
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            affected_persons_count=999,
        )
        assert not any("affected_persons" in c for c in result.triggered_criteria)

    def test_suspected_malicious_triggers(self):
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            suspected_malicious=True,
        )
        assert result.significant_incident is True
        assert "suspected_malicious" in result.triggered_criteria

    def test_all_none_not_significant(self):
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
        )
        assert result.significant_incident is False
        assert len(result.triggered_criteria) == 0

    def test_multiple_criteria(self):
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            service_impact="sustained",
            data_impact="systemic",
            suspected_malicious=True,
            cross_border=True,
        )
        assert result.significant_incident is True
        assert len(result.triggered_criteria) >= 3

    def test_result_to_dict(self):
        result = assess_ir_significance(
            entity_type="dns_service_provider",
            service_impact="unavailable",
        )
        d = result.to_dict()
        assert d["significant_incident"] is True
        assert isinstance(d["triggered_criteria"], list)
        assert d["entity_type"] == "dns_service_provider"
        assert isinstance(d["applicable_articles"], list)

    def test_safety_impact_triggers(self):
        result = assess_ir_significance(
            entity_type="cloud_computing_provider",
            safety_impact="death",
        )
        assert result.significant_incident is True
        assert "safety_impact" in result.triggered_criteria

    def test_degradation_plus_duration(self):
        result = assess_ir_significance(
            entity_type="dns_service_provider",
            service_impact="degraded",
            impact_duration_hours=1,
        )
        assert result.significant_incident is True
        assert "service_degradation_duration" in result.triggered_criteria


class TestNIS2Assessment:
    def test_critical_high_confidence_likely(self):
        cr = ContextualResult(severity="Critical", confidence="high", key_factors=["health sector"])
        result = assess_nis2_significance(cr, entity_affected=True)
        assert result.significant_incident == "likely"

    def test_high_medium_confidence_likely(self):
        cr = ContextualResult(severity="High", confidence="medium", key_factors=["energy sector"])
        result = assess_nis2_significance(cr, entity_affected=True)
        assert result.significant_incident == "likely"

    def test_medium_uncertain(self):
        cr = ContextualResult(severity="Medium", confidence="medium", key_factors=["banking sector"])
        result = assess_nis2_significance(cr, entity_affected=True)
        assert result.significant_incident == "uncertain"

    def test_low_unlikely(self):
        cr = ContextualResult(severity="Low", confidence="low", key_factors=["non_nis2 sector"])
        result = assess_nis2_significance(cr, entity_affected=True)
        assert result.significant_incident == "unlikely"

    def test_not_entity_affected_downgrades(self):
        cr = ContextualResult(severity="Critical", confidence="high", key_factors=["health sector"])
        result = assess_nis2_significance(cr, entity_affected=False)
        assert result.significant_incident == "uncertain"

    def test_result_to_dict(self):
        cr = ContextualResult(severity="High", confidence="high", key_factors=["transport sector"])
        result = assess_nis2_significance(cr, entity_affected=True)
        d = result.to_dict()
        assert d["significant_incident"] == "likely"
        assert d["severity"] == "High"
        assert "reporting_hint" in d
