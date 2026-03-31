"""Integration tests for curated benchmark pipeline (mocked models)."""

import json
from pathlib import Path

import pytest
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from evaluation.curated_loader import load_curated_incidents
from cyberscale.matrix.dual_scale import classify_incident


@pytest.fixture
def curated_dataset(tmp_path):
    """Minimal curated dataset with 4 incidents (one per T-level)."""
    data = {
        "version": "1.0",
        "incidents": [
            {
                "id": "INC-001", "name": "Low incident", "date": "2024-01-01",
                "sources": ["https://example.com"],
                "description": "A minor port scan detected at a small research lab with no data compromise or service impact",
                "t_fields": {
                    "service_impact": "partial", "affected_entities": 1,
                    "sectors_affected": 1, "cascading": "none", "data_impact": "none",
                },
                "o_fields": {
                    "sectors_affected": 1, "entity_relevance": "non_essential",
                    "ms_affected": 1, "cross_border_pattern": "none",
                    "capacity_exceeded": False,
                },
                "expected_t": "T1", "expected_o": "O1",
                "rationale": {"t_rationale": "All minimal fields = T1", "o_rationale": "All minimal fields = O1"},
            },
            {
                "id": "INC-002", "name": "Medium incident", "date": "2024-02-01",
                "sources": ["https://example.com"],
                "description": "A DDoS attack disrupted banking services across two EU member states for several hours",
                "t_fields": {
                    "service_impact": "degraded", "affected_entities": 5,
                    "sectors_affected": 1, "cascading": "none", "data_impact": "accessed",
                },
                "o_fields": {
                    "sectors_affected": 1, "entity_relevance": "essential",
                    "ms_affected": 2, "cross_border_pattern": "limited",
                    "capacity_exceeded": False,
                },
                "expected_t": "T2", "expected_o": "O2",
                "rationale": {"t_rationale": "Significant disruption = T2", "o_rationale": "EU info + limited cross-border = O2"},
            },
            {
                "id": "INC-003", "name": "High incident", "date": "2024-03-01",
                "sources": ["https://example.com"],
                "description": "Ransomware encrypted hospital systems completely, sensitive patient data exfiltrated and published online",
                "t_fields": {
                    "service_impact": "unavailable", "affected_entities": 25,
                    "sectors_affected": 2, "cascading": "cross_sector", "data_impact": "exfiltrated",
                },
                "o_fields": {
                    "sectors_affected": 2,
                    "entity_relevance": "high_relevance", "ms_affected": 4,
                    "cross_border_pattern": "significant",
                    "capacity_exceeded": True,
                },
                "expected_t": "T3", "expected_o": "O3",
                "rationale": {"t_rationale": "Complete + sensitive = T3", "o_rationale": "EU active + significant = O3"},
            },
            {
                "id": "INC-004", "name": "Crisis incident", "date": "2024-04-01",
                "sources": ["https://example.com"],
                "description": "Supply chain compromise caused sustained disruption across critical infrastructure in multiple EU member states",
                "t_fields": {
                    "service_impact": "sustained", "affected_entities": 150,
                    "sectors_affected": 5, "cascading": "uncontrolled", "data_impact": "systemic",
                },
                "o_fields": {
                    "sectors_affected": 5,
                    "entity_relevance": "systemic", "ms_affected": 8,
                    "cross_border_pattern": "systemic",
                    "capacity_exceeded": True,
                },
                "expected_t": "T4", "expected_o": "O4",
                "rationale": {"t_rationale": "Sustained + systemic = T4", "o_rationale": "Full IPCR + systemic = O4"},
            },
        ],
    }
    path = tmp_path / "curated_incidents.json"
    path.write_text(json.dumps(data))
    return path


def test_loader_produces_correct_count(curated_dataset):
    incidents = load_curated_incidents(curated_dataset)
    assert len(incidents) == 4


def test_matrix_lookup_for_curated_incidents(curated_dataset):
    incidents = load_curated_incidents(curated_dataset)
    expected_classifications = [
        "below_threshold",  # T1/O1
        "significant",      # T2/O2
        "large_scale",      # T3/O3
        "cyber_crisis",     # T4/O4
    ]
    for inc, expected_cls in zip(incidents, expected_classifications):
        result = classify_incident(inc.expected_t, inc.expected_o)
        assert result.classification == expected_cls, (
            f"{inc.id}: expected {expected_cls}, got {result.classification}"
        )


def test_full_dataset_loads_and_validates():
    """Test that the actual curated_incidents.json loads without errors."""
    dataset_path = PROJECT_ROOT / "data" / "reference" / "curated_incidents.json"
    if not dataset_path.exists():
        pytest.skip("curated_incidents.json not yet created")
    incidents = load_curated_incidents(dataset_path)
    assert len(incidents) >= 30, f"Expected at least 30 incidents, got {len(incidents)}"

    t_levels = {inc.expected_t for inc in incidents}
    o_levels = {inc.expected_o for inc in incidents}
    assert t_levels == {"T1", "T2", "T3", "T4"}, f"Missing T levels: {t_levels}"
    assert o_levels == {"O1", "O2", "O3", "O4"}, f"Missing O levels: {o_levels}"
