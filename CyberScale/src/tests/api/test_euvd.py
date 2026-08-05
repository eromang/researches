"""Tests for EUVD API client."""

import pytest
import responses

from cyberscale.api.euvd import EUVDClient


EUVD_BASE = "https://euvdservices.enisa.europa.eu/api"


@responses.activate
def test_search_by_score_range():
    responses.add(
        responses.GET,
        f"{EUVD_BASE}/search",
        json={
            "items": [
                {
                    "id": "EUVD-2025-12345",
                    "description": "A critical vulnerability in ExampleProduct.",
                    "baseScore": 9.1,
                    "baseScoreVersion": "3.1",
                    "baseScoreVector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                    "aliases": "CVE-2025-1234\nGHSA-xxxx",
                    "references": "https://example.com/advisory",
                    "epss": 45.2,
                    "datePublished": "Mar 15, 2025, 10:00:00 AM",
                    "dateUpdated": "Mar 16, 2025, 12:00:00 PM",
                    "assigner": "mitre",
                    "enisaIdProduct": [{"product": {"name": "ExampleProduct"}}],
                    "enisaIdVendor": [{"vendor": {"name": "ExampleVendor"}}],
                }
            ],
            "total": 1,
        },
        status=200,
    )

    client = EUVDClient()
    results = client.search(from_score=9.0, to_score=10.0, size=10)

    assert len(results) == 1
    assert results[0]["euvd_id"] == "EUVD-2025-12345"
    assert results[0]["description"] == "A critical vulnerability in ExampleProduct."
    assert results[0]["cvss_score"] == 9.1
    assert results[0]["cve_ids"] == ["CVE-2025-1234"]


@responses.activate
def test_search_unscored_returns_none_cvss():
    responses.add(
        responses.GET,
        f"{EUVD_BASE}/search",
        json={
            "items": [
                {
                    "id": "EUVD-2025-99999",
                    "description": "An unscored vulnerability.",
                    "baseScore": -1.0,
                    "baseScoreVersion": "",
                    "baseScoreVector": "",
                    "aliases": "CVE-2025-9999",
                    "references": "",
                    "epss": 0.0,
                    "datePublished": "Mar 20, 2025, 10:00:00 AM",
                    "dateUpdated": "",
                    "assigner": "mitre",
                    "enisaIdProduct": [],
                    "enisaIdVendor": [],
                }
            ],
            "total": 1,
        },
        status=200,
    )

    client = EUVDClient()
    results = client.search(size=10)

    assert results[0]["cvss_score"] is None


@responses.activate
def test_lookup_by_euvd_id():
    responses.add(
        responses.GET,
        f"{EUVD_BASE}/enisaid",
        json={
            "id": "EUVD-2025-12345",
            "description": "A critical vulnerability.",
            "baseScore": 9.1,
            "baseScoreVersion": "3.1",
            "baseScoreVector": "CVSS:3.1/...",
            "aliases": "CVE-2025-1234",
            "references": "",
            "epss": 45.2,
            "datePublished": "Mar 15, 2025, 10:00:00 AM",
            "dateUpdated": "",
            "assigner": "mitre",
            "enisaIdProduct": [],
            "enisaIdVendor": [],
            "enisaIdVulnerability": [],
        },
        status=200,
    )

    client = EUVDClient()
    result = client.get_by_euvd_id("EUVD-2025-12345")

    assert result["euvd_id"] == "EUVD-2025-12345"
    assert result["cvss_score"] == 9.1


@responses.activate
def test_get_exploited_paginates_through_search():
    """The exploited set lives behind /search, not /exploitedvulnerabilities.

    /exploitedvulnerabilities returns a 4-record "latest" view and ignores
    size/page/limit; the full set was 1,665 entries on 2026-08-05.
    """
    page0 = [
        {"id": f"EUVD-2026-{i:05d}", "aliases": f"CVE-2026-{i:05d}", "baseScore": 7.5}
        for i in range(100)
    ]
    page1 = [
        {"id": "EUVD-2026-99999", "aliases": "CVE-2026-99999", "baseScore": 9.8}
    ]
    responses.add(responses.GET, f"{EUVD_BASE}/search",
                  json={"items": page0, "total": 101}, status=200)
    responses.add(responses.GET, f"{EUVD_BASE}/search",
                  json={"items": page1, "total": 101}, status=200)

    results = EUVDClient().get_exploited()

    assert len(results) == 101
    assert results[-1]["cve_ids"] == ["CVE-2026-99999"]
    # exploited filter must be sent, and pagination must advance
    assert responses.calls[0].request.params["exploited"] == "true"
    assert responses.calls[0].request.params["page"] == "0"
    assert responses.calls[1].request.params["page"] == "1"


@responses.activate
def test_get_exploited_respects_limit():
    responses.add(
        responses.GET, f"{EUVD_BASE}/search",
        json={"items": [{"id": f"EUVD-{i}", "aliases": f"CVE-2026-{i:05d}"}
                        for i in range(100)], "total": 200},
        status=200,
    )
    results = EUVDClient().get_exploited(limit=5)
    assert len(results) == 5


@responses.activate
def test_get_exploited_latest_uses_legacy_endpoint():
    responses.add(
        responses.GET, f"{EUVD_BASE}/exploitedvulnerabilities",
        json=[{"id": "EUVD-2026-00001", "aliases": "CVE-2026-00001"}], status=200,
    )
    results = EUVDClient().get_exploited_latest()
    assert len(results) == 1
    assert results[0]["cve_ids"] == ["CVE-2026-00001"]
