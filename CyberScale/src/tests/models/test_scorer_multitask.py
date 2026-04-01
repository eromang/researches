"""Tests for Phase 6 multi-task vulnerability scorer model."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import torch
import torch.nn as nn

from cyberscale.models.scorer_multitask import (
    DEFAULT_COMPONENT_CONFIGS,
    MultiTaskScorer,
    MultiTaskScorerResult,
    MultiTaskSeverityScorer,
)


# ---------------------------------------------------------------------------
# Helpers -- lightweight mock encoder to avoid downloading ModernBERT in CI
# ---------------------------------------------------------------------------


class _FakeEncoderConfig:
    hidden_size = 64


class _FakeEncoderOutput:
    def __init__(self, last_hidden_state: torch.Tensor):
        self.last_hidden_state = last_hidden_state


class _FakeEncoder(nn.Module):
    """Minimal stand-in for ``AutoModel.from_pretrained``.

    Uses a real linear projection so that outputs are deterministic for the
    same input (important for dropout=0 tests).
    """

    def __init__(self):
        super().__init__()
        self.config = _FakeEncoderConfig()
        self._proj = nn.Linear(1, self.config.hidden_size)

    def forward(self, input_ids, attention_mask):
        batch_size = input_ids.size(0)
        seq_len = input_ids.size(1)
        # Derive hidden states deterministically from input_ids
        x = input_ids.float().unsqueeze(-1)  # (B, S, 1)
        hidden = self._proj(x)               # (B, S, hidden_size)
        return _FakeEncoderOutput(hidden)


def _build_model(dropout: float = 0.3) -> MultiTaskScorer:
    """Build a ``MultiTaskScorer`` with the fake encoder patched in."""
    with patch(
        "cyberscale.models.scorer_multitask.AutoModel.from_pretrained",
        return_value=_FakeEncoder(),
    ):
        model = MultiTaskScorer(
            base_model="fake-model",
            num_band_labels=4,
            component_configs=DEFAULT_COMPONENT_CONFIGS,
            dropout=dropout,
        )
    return model


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestMultiTaskScorerForward:
    """forward() returns correctly-shaped band and component logits."""

    def test_band_logits_shape(self):
        torch.manual_seed(42)
        model = _build_model()
        input_ids = torch.randint(0, 100, (2, 16))
        attention_mask = torch.ones_like(input_ids)

        band_logits, comp_logits = model(input_ids, attention_mask)

        assert band_logits.shape == (2, 4)

    def test_component_logits_keys(self):
        torch.manual_seed(42)
        model = _build_model()
        input_ids = torch.randint(0, 100, (2, 16))
        attention_mask = torch.ones_like(input_ids)

        _, comp_logits = model(input_ids, attention_mask)

        assert set(comp_logits.keys()) == set(DEFAULT_COMPONENT_CONFIGS.keys())

    def test_component_logits_shapes(self):
        torch.manual_seed(42)
        model = _build_model()
        batch_size = 3
        input_ids = torch.randint(0, 100, (batch_size, 16))
        attention_mask = torch.ones_like(input_ids)

        _, comp_logits = model(input_ids, attention_mask)

        for name, cfg in DEFAULT_COMPONENT_CONFIGS.items():
            assert comp_logits[name].shape == (
                batch_size,
                cfg["num_labels"],
            ), f"Shape mismatch for component {name}"

    def test_single_sample(self):
        torch.manual_seed(42)
        model = _build_model()
        input_ids = torch.randint(0, 100, (1, 8))
        attention_mask = torch.ones_like(input_ids)

        band_logits, comp_logits = model(input_ids, attention_mask)

        assert band_logits.shape == (1, 4)
        assert comp_logits["av"].shape == (1, 4)
        assert comp_logits["ac"].shape == (1, 2)


class TestMultiTaskScorerStandalone:
    """Band prediction works independently of component heads."""

    def test_band_logits_independent_of_components(self):
        """Zeroing component head weights should not affect band logits."""
        torch.manual_seed(42)
        model = _build_model()
        input_ids = torch.randint(0, 100, (1, 16))
        attention_mask = torch.ones_like(input_ids)

        model.eval()
        with torch.no_grad():
            band_logits_a, _ = model(input_ids, attention_mask)

        # Zero-out every component head
        for head in model.component_heads.values():
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)

        with torch.no_grad():
            band_logits_b, comp_logits = model(input_ids, attention_mask)

        # Band logits should be identical
        assert torch.allclose(band_logits_a, band_logits_b)

        # Component logits should now be all zeros
        for logits in comp_logits.values():
            assert torch.allclose(logits, torch.zeros_like(logits))

    def test_custom_component_configs(self):
        """Model accepts a reduced set of component heads."""
        custom = {"av": {"num_labels": 4}, "ac": {"num_labels": 2}}
        with patch(
            "cyberscale.models.scorer_multitask.AutoModel.from_pretrained",
            return_value=_FakeEncoder(),
        ):
            model = MultiTaskScorer(
                base_model="fake-model",
                component_configs=custom,
                dropout=0.0,
            )

        input_ids = torch.randint(0, 100, (1, 8))
        attention_mask = torch.ones_like(input_ids)
        _, comp_logits = model(input_ids, attention_mask)

        assert set(comp_logits.keys()) == {"av", "ac"}


class TestMCDropout:
    """MC dropout produces variation across forward passes."""

    def test_different_outputs_with_dropout(self):
        torch.manual_seed(42)
        model = _build_model(dropout=0.5)  # high dropout for obvious variation
        model.eval()

        input_ids = torch.randint(0, 100, (1, 16))
        attention_mask = torch.ones_like(input_ids)

        # Enable dropout (MC mode)
        for m in model.modules():
            if isinstance(m, nn.Dropout):
                m.train()

        results = []
        with torch.no_grad():
            for _ in range(10):
                band_logits, _ = model(input_ids, attention_mask)
                results.append(band_logits.clone())

        # With dropout enabled, not all passes should be identical
        all_same = all(torch.allclose(results[0], r) for r in results[1:])
        assert not all_same, "MC dropout passes should produce different outputs"

    def test_deterministic_without_dropout(self):
        torch.manual_seed(42)
        model = _build_model(dropout=0.0)
        model.eval()

        input_ids = torch.randint(0, 100, (1, 16))
        attention_mask = torch.ones_like(input_ids)

        results = []
        with torch.no_grad():
            for _ in range(5):
                band_logits, _ = model(input_ids, attention_mask)
                results.append(band_logits.clone())

        for r in results[1:]:
            assert torch.allclose(results[0], r), (
                "With dropout=0 all passes should be identical"
            )


class TestComponentLabelMaps:
    """Label maps and reverse maps cover all eight components."""

    def test_all_components_present(self):
        expected = {"av", "ac", "pr", "ui", "scope", "conf", "integ", "avail"}
        assert set(MultiTaskScorer.COMPONENT_LABEL_MAPS.keys()) == expected
        assert set(MultiTaskScorer.REVERSE_LABEL_MAPS.keys()) == expected

    @pytest.mark.parametrize(
        "component,labels",
        [
            ("av", ["N", "A", "L", "P"]),
            ("ac", ["L", "H"]),
            ("pr", ["N", "L", "H"]),
            ("ui", ["N", "R"]),
            ("scope", ["U", "C"]),
            ("conf", ["N", "L", "H"]),
            ("integ", ["N", "L", "H"]),
            ("avail", ["N", "L", "H"]),
        ],
    )
    def test_label_map_values(self, component: str, labels: list[str]):
        fwd = MultiTaskScorer.COMPONENT_LABEL_MAPS[component]
        assert set(fwd.keys()) == set(labels)
        # Indices should be contiguous 0..n-1
        assert set(fwd.values()) == set(range(len(labels)))

    def test_reverse_maps_roundtrip(self):
        for comp, fwd in MultiTaskScorer.COMPONENT_LABEL_MAPS.items():
            rev = MultiTaskScorer.REVERSE_LABEL_MAPS[comp]
            for letter, idx in fwd.items():
                assert rev[idx] == letter


class TestMultiTaskScorerResult:
    """MultiTaskScorerResult dataclass."""

    def test_fields(self):
        r = MultiTaskScorerResult(
            score=8.5,
            confidence="high",
            band="High",
            predicted_vector={"av": "N", "ac": "L"},
        )
        assert r.score == 8.5
        assert r.confidence == "high"
        assert r.band == "High"
        assert r.predicted_vector == {"av": "N", "ac": "L"}

    def test_to_dict(self):
        vec = {"av": "N", "ac": "L", "pr": "H"}
        r = MultiTaskScorerResult(
            score=5.5, confidence="medium", band="Medium", predicted_vector=vec
        )
        d = r.to_dict()
        assert d["score"] == 5.5
        assert d["confidence"] == "medium"
        assert d["band"] == "Medium"
        assert d["predicted_vector"] == vec

    def test_to_dict_returns_plain_dict(self):
        r = MultiTaskScorerResult(
            score=2.0,
            confidence="low",
            band="Low",
            predicted_vector={},
        )
        d = r.to_dict()
        assert isinstance(d, dict)


class TestSaveAndLoad:
    """Round-trip save_pretrained / from_pretrained."""

    def test_roundtrip(self, tmp_path):
        torch.manual_seed(42)
        model = _build_model(dropout=0.1)
        model.save_pretrained(tmp_path / "ckpt")

        with patch(
            "cyberscale.models.scorer_multitask.AutoModel.from_pretrained",
            return_value=_FakeEncoder(),
        ):
            loaded = MultiTaskScorer.from_pretrained(tmp_path / "ckpt")

        # Config should match
        assert model.get_config() == loaded.get_config()

    def test_config_json_written(self, tmp_path):
        model = _build_model()
        model.save_pretrained(tmp_path / "ckpt")
        assert (tmp_path / "ckpt" / "config.json").exists()
        assert (tmp_path / "ckpt" / "model.pt").exists()


class TestStaticHelpers:
    """Static scoring helpers on MultiTaskSeverityScorer."""

    def test_probs_to_band_critical(self):
        assert MultiTaskSeverityScorer.probs_to_band([0.0, 0.0, 0.1, 0.9]) == "Critical"

    def test_probs_to_band_low(self):
        assert MultiTaskSeverityScorer.probs_to_band([0.8, 0.1, 0.05, 0.05]) == "Low"

    def test_probs_to_score_pure_high(self):
        score = MultiTaskSeverityScorer.probs_to_score([0.0, 0.0, 1.0, 0.0])
        assert score == 8.0

    def test_confidence_high(self):
        assert MultiTaskSeverityScorer.max_prob_to_confidence(0.85) == "high"

    def test_confidence_medium(self):
        assert MultiTaskSeverityScorer.max_prob_to_confidence(0.55) == "medium"

    def test_confidence_low(self):
        assert MultiTaskSeverityScorer.max_prob_to_confidence(0.30) == "low"

    def test_score_to_band(self):
        assert MultiTaskSeverityScorer.score_to_band(9.5) == "Critical"
        assert MultiTaskSeverityScorer.score_to_band(7.5) == "High"
        assert MultiTaskSeverityScorer.score_to_band(5.0) == "Medium"
        assert MultiTaskSeverityScorer.score_to_band(2.0) == "Low"
