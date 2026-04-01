"""Tests for authority feedback store."""

import json

import pytest

from cyberscale.feedback import (
    AuthorityDecision, store_decision, load_decisions, compute_rule_accuracy,
)


@pytest.fixture
def feedback_path(tmp_path):
    return tmp_path / "test_decisions.json"


def _make_decision(**kwargs):
    defaults = {
        "incident_id": "INC-001",
        "timestamp": "2026-04-01T10:00:00Z",
        "ms_established": "LU",
        "suggested_t": "T3",
        "suggested_o": "O3",
        "suggested_classification": "large_scale",
        "actual_t": "T3",
        "actual_o": "O3",
        "actual_classification": "large_scale",
        "override_reason": "",
        "entity_count": 5,
        "tier": "national",
    }
    defaults.update(kwargs)
    return AuthorityDecision(**defaults)


class TestStoreAndLoad:
    def test_store_and_load(self, feedback_path):
        d = _make_decision()
        store_decision(d, path=feedback_path)
        decisions = load_decisions(feedback_path)
        assert len(decisions) == 1
        assert decisions[0]["incident_id"] == "INC-001"

    def test_append_multiple(self, feedback_path):
        store_decision(_make_decision(incident_id="INC-001"), path=feedback_path)
        store_decision(_make_decision(incident_id="INC-002"), path=feedback_path)
        decisions = load_decisions(feedback_path)
        assert len(decisions) == 2

    def test_load_empty(self, feedback_path):
        assert load_decisions(feedback_path) == []


class TestComputeAccuracy:
    def test_all_correct(self):
        decisions = [
            {"suggested_t": "T3", "actual_t": "T3",
             "suggested_o": "O3", "actual_o": "O3",
             "suggested_classification": "large_scale",
             "actual_classification": "large_scale"},
        ]
        m = compute_rule_accuracy(decisions)
        assert m["t_accuracy"] == 1.0
        assert m["o_accuracy"] == 1.0
        assert m["matrix_accuracy"] == 1.0

    def test_overrides_detected(self):
        decisions = [
            {"suggested_t": "T3", "actual_t": "T4",
             "suggested_o": "O2", "actual_o": "O3",
             "suggested_classification": "large_scale",
             "actual_classification": "cyber_crisis"},
        ]
        m = compute_rule_accuracy(decisions)
        assert m["t_accuracy"] == 0.0
        assert "T3→T4" in m["t_override_patterns"]
        assert "O2→O3" in m["o_override_patterns"]

    def test_empty(self):
        m = compute_rule_accuracy([])
        assert m["total"] == 0
