"""Tests for Phase 1 vulnerability scorer model."""

import pytest
import torch

from cyberscale.models.scorer import SeverityScorer, ScorerResult


class TestScorerResult:
    def test_result_fields(self):
        r = ScorerResult(score=7.5, confidence="high", band="High")
        assert r.score == 7.5
        assert r.confidence == "high"
        assert r.band == "High"

    def test_to_dict(self):
        r = ScorerResult(score=7.5, confidence="high", band="High")
        d = r.to_dict()
        assert d["score"] == 7.5
        assert d["confidence"] == "high"
        assert d["band"] == "High"


class TestScorerFormatInput:
    def test_description_only(self):
        scorer = SeverityScorer.__new__(SeverityScorer)
        text = scorer._format_input("Buffer overflow in libfoo", cwe=None)
        assert text == "Buffer overflow in libfoo"

    def test_description_with_cwe(self):
        scorer = SeverityScorer.__new__(SeverityScorer)
        text = scorer._format_input("Buffer overflow in libfoo", cwe="CWE-119")
        assert "cwe: CWE-119" in text
        assert "Buffer overflow in libfoo" in text


class TestScoreToBand:
    def test_critical(self):
        assert SeverityScorer.score_to_band(9.5) == "Critical"

    def test_high(self):
        assert SeverityScorer.score_to_band(7.5) == "High"

    def test_medium(self):
        assert SeverityScorer.score_to_band(5.0) == "Medium"

    def test_low(self):
        assert SeverityScorer.score_to_band(2.0) == "Low"

    def test_boundary_9(self):
        assert SeverityScorer.score_to_band(9.0) == "Critical"

    def test_boundary_7(self):
        assert SeverityScorer.score_to_band(7.0) == "High"

    def test_boundary_4(self):
        assert SeverityScorer.score_to_band(4.0) == "Medium"

    def test_zero(self):
        assert SeverityScorer.score_to_band(0.0) == "Low"


class TestClassificationOutput:
    def test_probs_to_band_high(self):
        assert SeverityScorer.probs_to_band([0.05, 0.10, 0.75, 0.10]) == "High"

    def test_probs_to_band_critical(self):
        assert SeverityScorer.probs_to_band([0.0, 0.0, 0.1, 0.9]) == "Critical"

    def test_probs_to_band_low(self):
        assert SeverityScorer.probs_to_band([0.8, 0.1, 0.05, 0.05]) == "Low"

    def test_probs_to_score_pure_high(self):
        score = SeverityScorer.probs_to_score([0.0, 0.0, 1.0, 0.0])
        assert score == 8.0

    def test_probs_to_score_pure_low(self):
        score = SeverityScorer.probs_to_score([1.0, 0.0, 0.0, 0.0])
        assert score == 2.0

    def test_probs_to_score_mixed(self):
        score = SeverityScorer.probs_to_score([0.05, 0.10, 0.75, 0.10])
        assert 7.0 <= score <= 8.5

    def test_confidence_high(self):
        assert SeverityScorer.max_prob_to_confidence(0.85) == "high"

    def test_confidence_medium(self):
        assert SeverityScorer.max_prob_to_confidence(0.55) == "medium"

    def test_confidence_low(self):
        assert SeverityScorer.max_prob_to_confidence(0.30) == "low"


class TestVarianceToConfidence:
    def test_low_variance_high_confidence(self):
        assert SeverityScorer.variance_to_confidence(0.1) == "high"

    def test_medium_variance(self):
        assert SeverityScorer.variance_to_confidence(0.5) == "medium"

    def test_high_variance_low_confidence(self):
        assert SeverityScorer.variance_to_confidence(1.5) == "low"
