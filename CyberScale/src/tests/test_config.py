"""Tests for centralized config module."""

from __future__ import annotations

import pytest

from cyberscale.config import (
    VALID_SECTORS,
    VALID_ENTITY_TYPES,
    VALID_SERVICE_IMPACT,
    VALID_DATA_IMPACT,
    VALID_FINANCIAL_IMPACT,
    VALID_SAFETY_IMPACT,
    DEFAULT_MC_PASSES,
    DEFAULT_MAX_LENGTH_SCORER,
    DEFAULT_MAX_LENGTH_CONTEXTUAL,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
    max_prob_to_confidence,
)


class TestValidSectors:
    def test_loaded_from_reference(self):
        assert "energy" in VALID_SECTORS
        assert "transport" in VALID_SECTORS
        assert "health" in VALID_SECTORS
        assert "digital_infrastructure" in VALID_SECTORS
        assert "public_administration" in VALID_SECTORS
        assert "non_nis2" in VALID_SECTORS

    def test_is_set(self):
        assert isinstance(VALID_SECTORS, set)

    def test_has_expected_count(self):
        assert len(VALID_SECTORS) == 19


class TestValidEntityTypes:
    def test_loaded_from_reference_json(self):
        assert "electricity_undertaking" in VALID_ENTITY_TYPES
        assert "trust_service_provider" in VALID_ENTITY_TYPES
        assert "generic_enterprise" in VALID_ENTITY_TYPES

    def test_is_set(self):
        assert isinstance(VALID_ENTITY_TYPES, set)

    def test_has_expected_count(self):
        assert len(VALID_ENTITY_TYPES) == 59


class TestImpactEnums:
    def test_service_impact_values(self):
        assert VALID_SERVICE_IMPACT == {"none", "partial", "degraded", "unavailable", "sustained"}

    def test_data_impact_values(self):
        assert VALID_DATA_IMPACT == {"none", "accessed", "exfiltrated", "compromised", "systemic"}

    def test_financial_impact_values(self):
        assert VALID_FINANCIAL_IMPACT == {"none", "minor", "significant", "severe"}

    def test_safety_impact_values(self):
        assert VALID_SAFETY_IMPACT == {"none", "health_risk", "health_damage", "death"}


class TestModelDefaults:
    def test_mc_passes(self):
        assert DEFAULT_MC_PASSES == 5

    def test_max_length_scorer(self):
        assert DEFAULT_MAX_LENGTH_SCORER == 192

    def test_max_length_contextual(self):
        assert DEFAULT_MAX_LENGTH_CONTEXTUAL == 256

    def test_confidence_thresholds(self):
        assert CONFIDENCE_HIGH_THRESHOLD == 0.7
        assert CONFIDENCE_MEDIUM_THRESHOLD == 0.4


class TestMaxProbToConfidence:
    def test_high(self):
        assert max_prob_to_confidence(0.9) == "high"
        assert max_prob_to_confidence(0.7) == "high"

    def test_medium(self):
        assert max_prob_to_confidence(0.5) == "medium"
        assert max_prob_to_confidence(0.4) == "medium"

    def test_low(self):
        assert max_prob_to_confidence(0.3) == "low"
        assert max_prob_to_confidence(0.1) == "low"
