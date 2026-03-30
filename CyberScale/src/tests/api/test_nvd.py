"""Tests for NVD API client."""

import pytest
import responses

from cyberscale.api.nvd import NVDClient


NVD_BASE = "https://services.nvd.nist.gov/rest/json/cves/2.0"


@responses.activate
def test_get_cve_returns_parsed_vulnerability():
    responses.add(
        responses.GET,
        NVD_BASE,
        json={
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-1234",
                        "descriptions": [
                            {"lang": "en", "value": "A buffer overflow vulnerability in ExampleProduct."}
                        ],
                        "metrics": {
                            "cvssMetricV31": [
                                {
                                    "cvssData": {
                                        "baseScore": 7.5,
                                        "vectorString": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:H",
                                        "version": "3.1",
                                    }
                                }
                            ]
                        },
                        "weaknesses": [
                            {
                                "description": [{"lang": "en", "value": "CWE-120"}]
                            }
                        ],
                        "published": "2024-03-15T10:00:00.000",
                        "lastModified": "2024-03-16T12:00:00.000",
                    }
                }
            ],
            "totalResults": 1,
        },
        status=200,
    )

    client = NVDClient()
    result = client.get_cve("CVE-2024-1234")

    assert result["id"] == "CVE-2024-1234"
    assert result["description"] == "A buffer overflow vulnerability in ExampleProduct."
    assert result["cvss_score"] == 7.5
    assert result["cvss_version"] == "3.1"
    assert result["cwe"] == "CWE-120"


@responses.activate
def test_get_cve_not_found_returns_none():
    responses.add(
        responses.GET,
        NVD_BASE,
        json={"vulnerabilities": [], "totalResults": 0},
        status=200,
    )

    client = NVDClient()
    result = client.get_cve("CVE-9999-0000")

    assert result is None


@responses.activate
def test_get_cve_prefers_v31_over_v30():
    responses.add(
        responses.GET,
        NVD_BASE,
        json={
            "vulnerabilities": [
                {
                    "cve": {
                        "id": "CVE-2024-5678",
                        "descriptions": [
                            {"lang": "en", "value": "Test vulnerability."}
                        ],
                        "metrics": {
                            "cvssMetricV31": [
                                {"cvssData": {"baseScore": 8.0, "vectorString": "CVSS:3.1/...", "version": "3.1"}}
                            ],
                            "cvssMetricV30": [
                                {"cvssData": {"baseScore": 7.0, "vectorString": "CVSS:3.0/...", "version": "3.0"}}
                            ],
                        },
                        "weaknesses": [],
                        "published": "2024-01-01T00:00:00.000",
                        "lastModified": "2024-01-01T00:00:00.000",
                    }
                }
            ],
            "totalResults": 1,
        },
        status=200,
    )

    client = NVDClient()
    result = client.get_cve("CVE-2024-5678")

    assert result["cvss_score"] == 8.0
    assert result["cvss_version"] == "3.1"
