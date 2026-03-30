"""Tests for multi-source lookup facade."""

import pytest
from unittest.mock import MagicMock

from cyberscale.api.lookup import UnifiedLookup


def _make_nvd_result(cve_id: str, score: float) -> dict:
    return {
        "id": cve_id,
        "description": "NVD description of the vulnerability.",
        "cvss_score": score,
        "cvss_version": "3.1",
        "cvss_vector": "CVSS:3.1/...",
        "cwe": "CWE-79",
        "published": "2024-01-01",
        "last_modified": "2024-01-02",
        "source": "nvd",
    }


def _make_euvd_result(cve_id: str, score: float) -> dict:
    return {
        "euvd_id": "EUVD-2024-12345",
        "description": "EUVD description of the vulnerability.",
        "cvss_score": score,
        "cvss_version": "3.1",
        "cvss_vector": "CVSS:3.1/...",
        "cve_ids": [cve_id],
        "aliases": [cve_id],
        "epss": 30.0,
        "products": ["ExampleProduct"],
        "vendors": ["ExampleVendor"],
        "date_published": "2024-01-01",
        "date_updated": "2024-01-02",
        "source": "euvd",
    }


def test_lookup_merges_nvd_and_euvd():
    nvd = MagicMock()
    euvd = MagicMock()
    circl = MagicMock()

    nvd.get_cve.return_value = _make_nvd_result("CVE-2024-1234", 7.5)
    euvd.search.return_value = [_make_euvd_result("CVE-2024-1234", 7.5)]
    circl.get_vulnerability.return_value = None

    lookup = UnifiedLookup(nvd=nvd, euvd=euvd, circl=circl)
    result = lookup.lookup_cve("CVE-2024-1234")

    assert result["id"] == "CVE-2024-1234"
    assert result["cvss_score"] == 7.5
    assert result["sources"] == ["nvd", "euvd"]


def test_lookup_falls_back_when_nvd_missing():
    nvd = MagicMock()
    euvd = MagicMock()
    circl = MagicMock()

    nvd.get_cve.return_value = None
    euvd.search.return_value = []
    circl.get_vulnerability.return_value = {
        "id": "CVE-2024-1234",
        "title": "Test",
        "description": "CIRCL description of the vulnerability.",
        "cvss_score": 6.0,
        "cvss_version": "3.1",
        "cwe": "CWE-89",
        "published": "2024-01-01",
        "last_modified": "2024-01-01",
        "source": "circl",
    }

    lookup = UnifiedLookup(nvd=nvd, euvd=euvd, circl=circl)
    result = lookup.lookup_cve("CVE-2024-1234")

    assert result["id"] == "CVE-2024-1234"
    assert result["cvss_score"] == 6.0
    assert result["sources"] == ["circl"]


def test_lookup_returns_none_when_all_miss():
    nvd = MagicMock()
    euvd = MagicMock()
    circl = MagicMock()

    nvd.get_cve.return_value = None
    euvd.search.return_value = []
    circl.get_vulnerability.return_value = None

    lookup = UnifiedLookup(nvd=nvd, euvd=euvd, circl=circl)
    result = lookup.lookup_cve("CVE-9999-0000")

    assert result is None
