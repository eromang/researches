"""Tests for Phase 2 — Contextual severity classifier."""

from __future__ import annotations

import pytest

from cyberscale.models.contextual import (
    ContextualClassifier, ContextualResult, VALID_ENTITY_TYPES,
)


class TestContextualResult:
    def test_result_fields(self):
        r = ContextualResult(severity="High", confidence="high", key_factors=["health sector", "RCE"])
        assert r.severity == "High"
        assert len(r.key_factors) == 2

    def test_to_dict(self):
        r = ContextualResult(severity="Critical", confidence="medium", key_factors=["cross-border"])
        d = r.to_dict()
        assert d["severity"] == "Critical"
        assert d["key_factors"] == ["cross-border"]


class TestValidEntityTypes:
    def test_entity_types_is_set(self):
        assert isinstance(VALID_ENTITY_TYPES, set)

    def test_contains_annex_i_entities(self):
        for et in ["healthcare_provider", "credit_institution", "cloud_computing_provider", "managed_service_provider"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_contains_annex_ii_entities(self):
        for et in ["postal_service_provider", "chemicals_manufacturer", "food_producer", "research_organisation"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_contains_non_nis2_entities(self):
        for et in ["generic_enterprise", "generic_sme", "generic_individual"]:
            assert et in VALID_ENTITY_TYPES, f"{et} missing from VALID_ENTITY_TYPES"

    def test_old_entity_types_not_present(self):
        for old in ["individual", "sme", "msp", "hospital", "cloud_provider", "utility", "government", "bank"]:
            assert old not in VALID_ENTITY_TYPES, f"Old entity type {old} should not be in VALID_ENTITY_TYPES"

    def test_entity_type_count(self):
        assert len(VALID_ENTITY_TYPES) >= 55


class TestFormatInput:
    def test_with_all_fields(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input("Buffer overflow in X", sector="health", cross_border=True, score=8.5)
        assert "Buffer overflow in X" in text
        assert "sector: health" in text
        assert "cross_border: true" in text
        assert "score: 8.5" in text

    def test_without_score(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input("Buffer overflow in X", sector="energy", cross_border=False, score=None)
        assert "sector: energy" in text
        assert "cross_border: false" in text
        assert "score:" not in text

    def test_sector_validation(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(ValueError, match="Unknown sector"):
            clf._format_input("desc", sector="invalid_sector", cross_border=False)

    def test_deployment_scale_not_accepted(self):
        """deployment_scale was removed in v3 — entity_type encodes scale."""
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(TypeError):
            clf._format_input(
                "Buffer overflow", sector="health", cross_border=True,
                score=8.5, deployment_scale="enterprise",
            )

    def test_entity_type_validation_rejects_old_types(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        with pytest.raises(ValueError, match="Unknown entity_type"):
            clf._format_input(
                "Buffer overflow", sector="health", cross_border=True,
                score=8.5, entity_type="hospital",
            )

    def test_entity_type_validation_accepts_new_types(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="health", cross_border=True,
            score=8.5, entity_type="healthcare_provider",
        )
        assert "entity_type: healthcare_provider" in text

    def test_cer_critical_entity_true_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
            cer_critical_entity=True,
        )
        assert "cer_critical_entity: true" in text

    def test_cer_critical_entity_false_not_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert "cer_critical_entity:" not in text

    def test_cer_critical_entity_none_not_in_format(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow", sector="food", cross_border=False,
            score=6.0, entity_type="food_producer",
        )
        assert "cer_critical_entity:" not in text


class TestClassificationOutput:
    def test_probs_to_severity(self):
        assert ContextualClassifier.probs_to_severity([0.05, 0.10, 0.75, 0.10]) == "High"

    def test_probs_to_severity_critical(self):
        assert ContextualClassifier.probs_to_severity([0.0, 0.0, 0.1, 0.9]) == "Critical"

    def test_confidence_high(self):
        assert ContextualClassifier.max_prob_to_confidence(0.85) == "high"

    def test_confidence_medium(self):
        assert ContextualClassifier.max_prob_to_confidence(0.55) == "medium"

    def test_confidence_low(self):
        assert ContextualClassifier.max_prob_to_confidence(0.30) == "low"


class TestKeyFactors:
    def test_basic_factors(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5)
        assert "health sector" in factors
        assert "cross-border exposure" in factors
        assert "critical base score" in factors

    def test_no_cross_border(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0)
        assert "energy sector" in factors
        assert "cross-border exposure" not in factors
        assert "critical base score" not in factors

    def test_entity_type_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, entity_type="healthcare_provider")
        assert "healthcare_provider entity" in factors

    def test_cer_critical_entity_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors(
            "food", False, 6.0, entity_type="food_producer",
            cer_critical_entity=True,
        )
        assert "CER critical entity (essential override)" in factors

    def test_cer_critical_entity_false_no_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors(
            "food", False, 6.0, entity_type="food_producer",
            cer_critical_entity=False,
        )
        assert not any("CER" in f for f in factors)

    def test_no_deployment_factor(self):
        """deployment_scale was removed in v3."""
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0, entity_type="electricity_undertaking")
        assert not any("deployment" in f for f in factors)
