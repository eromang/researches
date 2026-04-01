"""Tests for improved T1/O1 generation balance."""

import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from generate_incidents import generate_t_samples, generate_o_samples


def test_t1_raw_count_at_least_500():
    t_raw = generate_t_samples(2000, paraphrase_variants=3, seed=42)
    t1_count = sum(1 for s in t_raw if s["label"] == "T1")
    assert t1_count >= 500, f"T1 raw count {t1_count} < 500"


def test_o1_raw_count_at_least_800():
    o_raw = generate_o_samples(2000, paraphrase_variants=3, seed=42)
    o1_count = sum(1 for s in o_raw if s["label"] == "O1")
    assert o1_count >= 800, f"O1 raw count {o1_count} < 800"


def test_no_class_regression():
    t_raw = generate_t_samples(2000, paraphrase_variants=3, seed=42)
    o_raw = generate_o_samples(2000, paraphrase_variants=3, seed=42)
    t_counts = Counter(s["label"] for s in t_raw)
    o_counts = Counter(s["label"] for s in o_raw)
    for level in ["T3", "T4"]:
        assert t_counts[level] >= 1000, f"{level} dropped to {t_counts[level]}"
    for level in ["O3", "O4"]:
        assert o_counts[level] >= 500, f"{level} dropped to {o_counts[level]}"
