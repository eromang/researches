"""Tests for per-sample weight support in training scripts."""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from train_technical import CVEDataset as TCVEDataset
from train_operational import CVEDataset as OCVEDataset


@pytest.fixture
def sample_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")


def test_t_dataset_returns_weight_when_present(sample_tokenizer):
    texts = ["test text [SEP] service_impact: partial entities: 1 sectors: 1 cascading: none data_impact: none"]
    labels = [0]
    weights = [0.8]
    ds = TCVEDataset(texts, labels, sample_tokenizer, weights=weights)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(0.8)


def test_t_dataset_defaults_weight_to_1(sample_tokenizer):
    texts = ["test text [SEP] service_impact: partial entities: 1 sectors: 1 cascading: none data_impact: none"]
    labels = [0]
    ds = TCVEDataset(texts, labels, sample_tokenizer)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(1.0)


def test_o_dataset_returns_weight_when_present(sample_tokenizer):
    texts = ["test text [SEP] sectors: 1 relevance: essential ms_affected: 1 cross_border: none capacity_exceeded: false"]
    labels = [0]
    weights = [0.8]
    ds = OCVEDataset(texts, labels, sample_tokenizer, weights=weights)
    item = ds[0]
    assert "weight" in item
    assert item["weight"].item() == pytest.approx(0.8)
