"""Tests for CIRCL VulnLookup API client."""

import pytest
import responses

from cyberscale.api.circl import CIRCLClient


CIRCL_BASE = "https://vulnerability.circl.lu"


@responses.activate
def test_get_vulnerability():
    responses.add(
        responses.GET,
        f"{CIRCL_BASE}/api/vulnerability/CVE-2024-1234",
        json={
            "containers": {
                "cna": {
                    "title": "Buffer overflow in ExampleProduct",
                    "descriptions": [
                        {"lang": "en", "value": "A buffer overflow in ExampleProduct allows RCE."}
                    ],
                    "metrics": [
                        {
                            "cvssV3_1": {
                                "baseScore": 7.5,
                                "baseSeverity": "HIGH",
                                "version": "3.1",
                                "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                            }
                        }
                    ],
                    "problemTypes": [
                        {"descriptions": [{"cweId": "CWE-120", "description": "Buffer overflow"}]}
                    ],
                }
            },
            "cveMetadata": {
                "cveId": "CVE-2024-1234",
                "datePublished": "2024-03-15T10:00:00.000Z",
                "dateUpdated": "2024-03-16T12:00:00.000Z",
            },
        },
        status=200,
    )

    client = CIRCLClient()
    result = client.get_vulnerability("CVE-2024-1234")

    assert result["id"] == "CVE-2024-1234"
    assert "buffer overflow" in result["description"].lower()
    assert result["cvss_score"] == 7.5
    assert result["cwe"] == "CWE-120"


@responses.activate
def test_search_by_cwe():
    responses.add(
        responses.GET,
        f"{CIRCL_BASE}/api/vulnerability/",
        json=[
            {"id": "CVE-2024-1111", "title": "XSS in Product A"},
            {"id": "CVE-2024-2222", "title": "XSS in Product B"},
        ],
        status=200,
    )

    client = CIRCLClient()
    results = client.search(cwe="CWE-79", per_page=10)

    assert len(results) == 2
    assert results[0]["id"] == "CVE-2024-1111"


@responses.activate
def test_get_vulnerability_not_found():
    responses.add(
        responses.GET,
        f"{CIRCL_BASE}/api/vulnerability/CVE-9999-0000",
        status=404,
    )

    client = CIRCLClient()
    result = client.get_vulnerability("CVE-9999-0000")

    assert result is None


def _kev_record(cve: str, source: str, first_seen: str) -> dict:
    return {
        "vulnerability": {"vulnId": cve, "altId": []},
        "status": {"exploited": True, "status_reason": "confirmed"},
        "timestamps": {"first_seen_at": f"{first_seen}T08:45:39+00:00"},
        "evidence": [{"source": source, "type": "public_report"}],
    }


@responses.activate
def test_get_kev_status_returns_earliest_date_across_sources():
    responses.add(
        responses.GET, f"{CIRCL_BASE}/api/kev",
        json={"metadata": {"count": 3}, "data": [
            _kev_record("CVE-2024-3400", "shadowserver", "2024-04-17"),
            _kev_record("CVE-2024-3400", "cisa-kev", "2024-04-12"),
            _kev_record("CVE-2024-3400", "kevintel", "2024-04-12"),
        ]},
        status=200,
    )

    status = CIRCLClient().get_kev_status("CVE-2024-3400")

    assert status["exploited"] is True
    assert status["exploited_date"] == "2024-04-12"   # earliest, not first listed
    assert status["exploit_sources"] == ["cisa-kev", "kevintel", "shadowserver"]
    assert status["in_cisa_kev"] is True
    assert status["observed_by_sensors"] is True


@responses.activate
def test_get_kev_status_absent_is_false_not_missing():
    """A CVE the catalog does not list is False, distinct from a failed lookup."""
    responses.add(responses.GET, f"{CIRCL_BASE}/api/kev",
                  json={"metadata": {"count": 0}, "data": []}, status=200)

    status = CIRCLClient().get_kev_status("CVE-2024-0001")

    assert status["exploited"] is False
    assert status["exploited_date"] is None
    assert status["exploit_sources"] == []
    assert status["in_cisa_kev"] is False


@responses.activate
def test_get_kev_skips_non_cve_identifiers():
    """CIRCL also carries EDB-/SSV-/GCVE- ids, which have no CVE to key on."""
    responses.add(
        responses.GET, f"{CIRCL_BASE}/api/kev",
        json={"metadata": {"count": 3}, "data": [
            _kev_record("CVE-2026-1111", "kevintel", "2026-01-05"),
            _kev_record("EDB-52028", "kevintel", "2026-01-06"),
            _kev_record("GCVE-1-2026-0020", "kevintel", "2026-01-07"),
        ]},
        status=200,
    )

    records = CIRCLClient().get_kev()

    assert len(records) == 1
    assert records[0]["cve_id"] == "CVE-2026-1111"
    assert records[0]["exploited_date"] == "2026-01-05"
