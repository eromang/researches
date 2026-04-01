"""Tests for curated incident dataset loader."""

import json
from pathlib import Path

import pytest
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.curated_loader import load_curated_incidents, CuratedIncident


@pytest.fixture
def sample_dataset(tmp_path):
    """Create a minimal valid dataset for testing."""
    data = {
        "version": "1.0",
        "incidents": [
            {
                "id": "INC-001",
                "name": "Test incident",
                "date": "2024-01-01",
                "sources": ["https://example.com"],
                "description": "A test ransomware attack on a hospital that disrupted all IT systems for several days",
                "t_fields": {
                    "service_impact": "unavailable",
                    "affected_entities": 1,
                    "sectors_affected": 1,
                    "cascading": "none",
                    "data_impact": "exfiltrated",
                },
                "o_fields": {
                    "sectors_affected": 1,
                    "entity_relevance": "essential",
                    "ms_affected": 1,
                    "cross_border_pattern": "none",
                    "capacity_exceeded": False,
                },
                "expected_t": "T3",
                "expected_o": "O1",
                "rationale": {
                    "t_rationale": "Complete disruption plus sensitive data compromise triggers T3",
                    "o_rationale": "Single member state, national coordination, essential entity = O1",
                },
            }
        ],
    }
    path = tmp_path / "curated_incidents.json"
    path.write_text(json.dumps(data))
    return path


def test_load_returns_list_of_curated_incidents(sample_dataset):
    incidents = load_curated_incidents(sample_dataset)
    assert len(incidents) == 1
    assert isinstance(incidents[0], CuratedIncident)


def test_curated_incident_has_required_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.id == "INC-001"
    assert incident.name == "Test incident"
    assert incident.expected_t == "T3"
    assert incident.expected_o == "O1"


def test_curated_incident_t_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.t_fields["service_impact"] == "unavailable"
    assert incident.t_fields["affected_entities"] == 1
    assert incident.t_fields["data_impact"] == "exfiltrated"


def test_curated_incident_o_fields(sample_dataset):
    incident = load_curated_incidents(sample_dataset)[0]
    assert incident.o_fields["sectors_affected"] == 1
    assert incident.o_fields["entity_relevance"] == "essential"
    assert incident.o_fields["capacity_exceeded"] is False


def test_invalid_t_level_raises(tmp_path):
    data = {
        "version": "1.0",
        "incidents": [{
            "id": "INC-001", "name": "Bad", "date": "2024-01-01",
            "sources": ["https://example.com"],
            "description": "A test incident with invalid T level that should fail validation checks",
            "t_fields": {
                "service_impact": "unavailable", "affected_entities": 1,
                "sectors_affected": 1, "cascading": "none", "data_impact": "none",
            },
            "o_fields": {
                "sectors_affected": 1, "entity_relevance": "essential",
                "ms_affected": 1, "cross_border_pattern": "none",
            },
            "expected_t": "T5",
            "expected_o": "O1",
            "rationale": {"t_rationale": "bad level test rationale here", "o_rationale": "bad level test rationale here"},
        }],
    }
    path = tmp_path / "bad.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="T5"):
        load_curated_incidents(path)


def test_empty_incidents_returns_empty_list(tmp_path):
    data = {"version": "1.0", "incidents": []}
    path = tmp_path / "empty.json"
    path.write_text(json.dumps(data))
    assert load_curated_incidents(path) == []
