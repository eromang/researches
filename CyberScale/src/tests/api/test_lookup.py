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


def _lookup_with(nvd_result, kev_status):
    """UnifiedLookup wired to mocks; kev_status may be an Exception to raise."""
    nvd, euvd, circl = MagicMock(), MagicMock(), MagicMock()
    nvd.get_cve.return_value = nvd_result
    euvd.search.return_value = []
    circl.get_vulnerability.return_value = None
    if isinstance(kev_status, Exception):
        circl.get_kev_status.side_effect = kev_status
    else:
        circl.get_kev_status.return_value = kev_status
    return UnifiedLookup(nvd=nvd, euvd=euvd, circl=circl)


def test_exploitation_dates_and_time_to_exploit_are_merged():
    lookup = _lookup_with(
        _make_nvd_result("CVE-2024-3400", 10.0) | {"published": "2024-04-12T17:15:51"},
        {
            "cve_id": "CVE-2024-3400",
            "exploited": True,
            "exploited_date": "2024-04-17",
            "exploit_sources": ["cisa-kev", "shadowserver"],
            "in_cisa_kev": True,
            "observed_by_sensors": True,
        },
    )

    result = lookup.lookup_cve("CVE-2024-3400")

    assert result["exploited"] is True
    assert result["exploited_date"] == "2024-04-17"
    assert result["published"] == "2024-04-12T17:15:51"
    assert result["time_to_exploit_days"] == 5
    assert result["exploit_sources"] == ["cisa-kev", "shadowserver"]
    assert result["exploitation_lookup"] == "ok"


def test_time_to_exploit_can_be_negative():
    """Exploited before publication is a real case, not an error to clamp."""
    lookup = _lookup_with(
        _make_nvd_result("CVE-2024-9999", 9.0) | {"published": "2024-06-10"},
        {"cve_id": "CVE-2024-9999", "exploited": True, "exploited_date": "2024-06-01",
         "exploit_sources": ["shadowserver"], "in_cisa_kev": False,
         "observed_by_sensors": True},
    )
    assert lookup.lookup_cve("CVE-2024-9999")["time_to_exploit_days"] == -9


def test_failed_exploitation_lookup_is_none_not_false():
    """A network failure must not be reported as 'not exploited'."""
    lookup = _lookup_with(
        _make_nvd_result("CVE-2024-0001", 5.0), RuntimeError("connection reset")
    )

    result = lookup.lookup_cve("CVE-2024-0001")

    assert result["exploited"] is None
    assert result["exploitation_lookup"] == "failed"
    assert "exploited_date" not in result


def test_age_days_uses_reference_date():
    from datetime import date
    lookup = _lookup_with(
        _make_nvd_result("CVE-2024-0002", 5.0) | {"published": "2024-01-01"},
        {"cve_id": "CVE-2024-0002", "exploited": False, "exploited_date": None,
         "exploit_sources": [], "in_cisa_kev": False},
    )
    result = lookup.lookup_cve("CVE-2024-0002")
    assert lookup.age_days(result, as_of=date(2024, 3, 1)) == 60
