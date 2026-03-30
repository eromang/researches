"""Tests for CWE enrichment in Phase 1 training data."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make training/ importable as a package from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from training.scripts.fetch_bulk_cves import extract_cwe  # noqa: E402


class TestCweExtraction:
    """Verify that CWE IDs are extracted from cvelistV5 format."""

    def test_extract_cwe_from_problem_types(self):
        """cvelistV5 stores CWE in cna.problemTypes[].descriptions[].cweId."""
        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-79", "lang": "en"}
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) == "CWE-79"

    def test_extract_cwe_skips_noinfo(self):
        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-noinfo", "lang": "en"}
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) is None

    def test_extract_cwe_missing_field(self):
        record = {"containers": {"cna": {}}}
        assert extract_cwe(record) is None

    def test_extract_cwe_multiple_picks_first_valid(self):
        record = {
            "containers": {
                "cna": {
                    "problemTypes": [
                        {
                            "descriptions": [
                                {"type": "CWE", "cweId": "CWE-Other", "lang": "en"},
                                {"type": "CWE", "cweId": "CWE-787", "lang": "en"},
                            ]
                        }
                    ]
                }
            }
        }
        assert extract_cwe(record) == "CWE-787"


class TestCVEDatasetCWE:
    """Verify that the training dataset includes CWE in tokenized text."""

    def test_cwe_included_in_text(self):
        from transformers import AutoTokenizer
        from training.scripts.train_scorer import CVEDataset

        tokenizer = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
        ds = CVEDataset(
            descriptions=["Buffer overflow in libfoo"],
            cwes=["CWE-119"],
            labels=[2],
            tokenizer=tokenizer,
            max_length=64,
        )
        item = ds[0]
        decoded = tokenizer.decode(item["input_ids"], skip_special_tokens=True)
        assert "cwe: CWE-119" in decoded

    def test_cwe_none_omitted(self):
        from transformers import AutoTokenizer
        from training.scripts.train_scorer import CVEDataset

        tokenizer = AutoTokenizer.from_pretrained("answerdotai/ModernBERT-base")
        ds = CVEDataset(
            descriptions=["Buffer overflow in libfoo"],
            cwes=[None],
            labels=[2],
            tokenizer=tokenizer,
            max_length=64,
        )
        item = ds[0]
        decoded = tokenizer.decode(item["input_ids"], skip_special_tokens=True)
        assert "cwe:" not in decoded
