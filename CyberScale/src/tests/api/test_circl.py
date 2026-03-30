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
