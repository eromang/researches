"""Tests for curated incident mixing into training data."""

import csv
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "evaluation"))

from mix_curated import convert_to_t_csv, convert_to_o_csv, mix_into_training


@pytest.fixture
def sample_incident():
    return {
        "id": "INC-001",
        "name": "Test",
        "date": "2024-01-01",
        "sources": ["https://example.com"],
        "description": "A ransomware attack disrupted hospital systems causing complete shutdown of IT services for days",
        "t_fields": {
            "service_impact": "unavailable",
            "affected_entities": 25,
            "sectors_affected": 2,
            "cascading": "cross_sector",
            "data_impact": "exfiltrated",
        },
        "o_fields": {
            "sectors_affected": 2,
            "entity_relevance": "high_relevance",
            "ms_affected": 4,
            "cross_border_pattern": "significant",
            "capacity_exceeded": True,
        },
        "expected_t": "T3",
        "expected_o": "O3",
        "rationale": {
            "t_rationale": "Complete disruption plus sensitive data",
            "o_rationale": "EU active coordination needed",
        },
    }


def test_convert_to_t_csv_format(sample_incident):
    rows = convert_to_t_csv(sample_incident, paraphrase_variants=0)
    assert len(rows) == 1
    row = rows[0]
    assert "[SEP]" in row["text"]
    assert "service_impact: unavailable" in row["text"]
    assert "entities: 25" in row["text"]
    assert "data_impact: exfiltrated" in row["text"]
    assert row["label"] == "T3"
    assert row["weight"] == 1.0


def test_convert_to_o_csv_format(sample_incident):
    rows = convert_to_o_csv(sample_incident, paraphrase_variants=0)
    assert len(rows) == 1
    row = rows[0]
    assert "[SEP]" in row["text"]
    assert "relevance: high_relevance" in row["text"]
    assert "ms_affected: 4" in row["text"]
    assert "capacity_exceeded: true" in row["text"]
    assert row["label"] == "O3"
    assert row["weight"] == 1.0


def test_paraphrase_variants(sample_incident):
    rows = convert_to_t_csv(sample_incident, paraphrase_variants=3)
    assert len(rows) == 4
    assert all(r["label"] == "T3" for r in rows)
    assert all(r["weight"] == 1.0 for r in rows)
    texts = [r["text"] for r in rows]
    assert len(set(texts)) > 1


def test_mix_into_training(sample_incident, tmp_path):
    synth_path = tmp_path / "synthetic.csv"
    with open(synth_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerow({"text": "synthetic example [SEP] disruption: partial", "label": "T1"})

    output_path = tmp_path / "mixed.csv"
    mix_into_training(
        synthetic_csv=synth_path,
        curated_incidents=[sample_incident],
        output_csv=output_path,
        model_type="t",
        paraphrase_variants=0,
        synthetic_weight=0.8,
    )

    with open(output_path) as f:
        reader = list(csv.DictReader(f))

    assert len(reader) == 2
    synth_row = [r for r in reader if "synthetic" in r["text"]][0]
    curated_row = [r for r in reader if "synthetic" not in r["text"]][0]
    assert float(synth_row["weight"]) == 0.8
    assert float(curated_row["weight"]) == 1.0
