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
