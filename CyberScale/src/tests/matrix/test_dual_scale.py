"""Tests for Blueprint dual-scale matrix."""

import pytest

from cyberscale.matrix.dual_scale import classify_incident, MatrixResult


def test_t4_o4_is_cyber_crisis():
    result = classify_incident("T4", "O4")
    assert result.classification == "cyber_crisis"
    assert result.label == "Cyber crisis"
    assert result.provision == "7(d)"


def test_t1_o1_is_below_threshold():
    result = classify_incident("T1", "O1")
    assert result.classification == "below_threshold"
    assert result.label == "Below threshold"
    assert result.provision == "7(a)"


def test_t2_o3_is_large_scale():
    result = classify_incident("T2", "O3")
    assert result.classification == "large_scale"
    assert result.label == "Large-scale"
    assert result.provision == "7(c)"


def test_t3_o1_is_significant():
    result = classify_incident("T3", "O1")
    assert result.classification == "significant"
    assert result.label == "Significant"
    assert result.provision == "7(b)"


def test_invalid_t_level_raises():
    with pytest.raises(ValueError, match="Invalid T-level"):
        classify_incident("T5", "O1")


def test_invalid_o_level_raises():
    with pytest.raises(ValueError, match="Invalid O-level"):
        classify_incident("T1", "O5")


def test_all_16_matrix_cells():
    """Verify all 16 combinations produce valid results."""
    expected = {
        ("T4", "O4"): "cyber_crisis",
        ("T4", "O3"): "cyber_crisis",
        ("T4", "O2"): "large_scale",
        ("T4", "O1"): "large_scale",
        ("T3", "O4"): "cyber_crisis",
        ("T3", "O3"): "large_scale",
        ("T3", "O2"): "large_scale",
        ("T3", "O1"): "significant",
        ("T2", "O4"): "large_scale",
        ("T2", "O3"): "large_scale",
        ("T2", "O2"): "significant",
        ("T2", "O1"): "significant",
        ("T1", "O4"): "large_scale",
        ("T1", "O3"): "significant",
        ("T1", "O2"): "significant",
        ("T1", "O1"): "below_threshold",
    }

    for (t, o), expected_class in expected.items():
        result = classify_incident(t, o)
        assert result.classification == expected_class, f"Failed for {t}/{o}"
