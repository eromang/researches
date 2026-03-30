"""Tests for Phase 2 — Contextual severity classifier."""

from __future__ import annotations

import pytest

from cyberscale.models.contextual import ContextualClassifier, ContextualResult


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


class TestFormatInputV2:
    def test_with_deployment_scale(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=True,
            score=8.5, deployment_scale="enterprise",
        )
        assert "deployment_scale: enterprise" in text

    def test_with_entity_type(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=True,
            score=8.5, entity_type="hospital",
        )
        assert "entity_type: hospital" in text

    def test_with_both_new_fields(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="health", cross_border=False,
            score=7.0, deployment_scale="critical_operator", entity_type="hospital",
        )
        assert "deployment_scale: critical_operator" in text
        assert "entity_type: hospital" in text

    def test_without_new_fields_unchanged(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        text = clf._format_input(
            "Buffer overflow in X", sector="energy", cross_border=False, score=None,
        )
        assert "deployment_scale:" not in text
        assert "entity_type:" not in text


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


class TestKeyFactorsV2:
    def test_deployment_scale_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, deployment_scale="critical_operator")
        assert "critical_operator deployment" in factors

    def test_entity_type_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("health", True, 9.5, entity_type="hospital")
        assert "hospital entity" in factors

    def test_small_deployment_factor(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("non_nis2", False, 5.0, deployment_scale="individual")
        assert "individual deployment" in factors

    def test_no_new_factors_when_none(self):
        clf = ContextualClassifier.__new__(ContextualClassifier)
        factors = clf._extract_key_factors("energy", False, 5.0)
        assert not any("deployment" in f for f in factors)
        assert not any("entity" in f for f in factors)
