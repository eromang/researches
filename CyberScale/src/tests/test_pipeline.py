"""Tests for the composable Phase 1 → 2 → 3 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import pytest

from cyberscale.pipeline import PipelineResult, run_pipeline


@dataclass
class FakeScorer:
    """Stub Phase 1 scorer."""
    def predict(self, description: str, cwe: Optional[str] = None):
        @dataclass
        class R:
            score: float = 7.5
            confidence: str = "high"
            band: str = "High"
            def to_dict(self):
                return {"score": self.score, "confidence": self.confidence, "band": self.band}
        return R()


@dataclass
class FakeContextual:
    """Stub Phase 2 classifier."""
    def predict(self, description, sector, cross_border, score=None, **kwargs):
        @dataclass
        class R:
            severity: str = "High"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or ["health sector"]
            def to_dict(self):
                return {"severity": self.severity, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


@dataclass
class FakeTechnical:
    """Stub Phase 3 T-model."""
    def predict(self, description, **kwargs):
        @dataclass
        class R:
            level: str = "T3"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or []
            def to_dict(self):
                return {"level": self.level, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


@dataclass
class FakeOperational:
    """Stub Phase 3 O-model."""
    def predict(self, description, **kwargs):
        @dataclass
        class R:
            level: str = "O3"
            confidence: str = "high"
            key_factors: list = None
            def __post_init__(self):
                self.key_factors = self.key_factors or []
            def to_dict(self):
                return {"level": self.level, "confidence": self.confidence, "key_factors": self.key_factors}
        return R()


class TestRunPipeline:
    def test_full_pipeline_returns_all_phases(self):
        result = run_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            technical=FakeTechnical(),
            operational=FakeOperational(),
            description="Critical RCE in hospital system",
            sector="health",
            cross_border=True,
            service_disruption="complete",
            affected_entities=50,
            sectors_affected="health,digital_infrastructure",
            cascading="cross_sector",
            data_compromise="sensitive",
            entity_relevance="high_relevance",
            ms_affected=3,
            cross_border_pattern="significant",
            coordination_needs="eu_active",
            capacity_exceeded=False,
        )
        assert result.phase1_score == 7.5
        assert result.phase1_band == "High"
        assert result.phase2_severity == "High"
        assert result.phase3_t_level == "T3"
        assert result.phase3_o_level == "O3"
        assert result.classification in (
            "below_threshold", "significant", "large_scale", "cyber_crisis"
        )

    def test_pipeline_without_phase3(self):
        result = run_pipeline(
            scorer=FakeScorer(),
            contextual=FakeContextual(),
            description="SQL injection in banking portal",
            sector="banking",
            cross_border=False,
        )
        assert result.phase1_score == 7.5
        assert result.phase2_severity == "High"
        assert result.phase3_t_level is None
        assert result.phase3_o_level is None
        assert result.classification is None

    def test_pipeline_passes_cwe_to_scorer(self):
        calls = []
        class TrackingScorer:
            def predict(self, description, cwe=None):
                calls.append(cwe)
                @dataclass
                class R:
                    score: float = 5.0
                    confidence: str = "medium"
                    band: str = "Medium"
                return R()

        run_pipeline(
            scorer=TrackingScorer(),
            contextual=FakeContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
            cwe="CWE-119",
        )
        assert calls == ["CWE-119"]

    def test_pipeline_passes_score_to_contextual(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(score)
                @dataclass
                class R:
                    severity: str = "Medium"
                    confidence: str = "medium"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),
            contextual=TrackingContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
        )
        assert calls == [7.5]


class TestCerCriticalEntityPassthrough:
    def test_pipeline_passes_cer_to_contextual(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(kwargs.get("cer_critical_entity"))
                @dataclass
                class R:
                    severity: str = "High"
                    confidence: str = "high"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),
            contextual=TrackingContextual(),
            description="DoS in food supply",
            sector="food",
            cross_border=False,
            cer_critical_entity=True,
        )
        assert calls == [True]

    def test_pipeline_cer_none_by_default(self):
        calls = []
        class TrackingContextual:
            def predict(self, description, sector, cross_border, score=None, **kwargs):
                calls.append(kwargs.get("cer_critical_entity"))
                @dataclass
                class R:
                    severity: str = "Medium"
                    confidence: str = "medium"
                    key_factors: list = None
                    def __post_init__(self):
                        self.key_factors = self.key_factors or []
                return R()

        run_pipeline(
            scorer=FakeScorer(),
            contextual=TrackingContextual(),
            description="Buffer overflow",
            sector="energy",
            cross_border=False,
        )
        assert calls == [None]

    def test_pipeline_rejects_deployment_scale(self):
        """deployment_scale was removed in v3."""
        import inspect
        sig = inspect.signature(run_pipeline)
        assert "deployment_scale" not in sig.parameters
