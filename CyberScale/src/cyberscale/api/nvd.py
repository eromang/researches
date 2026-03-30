"""NVD API v2.0 client."""

from typing import Any

from cyberscale.api.base import APIClient


class NVDClient(APIClient):
    """Client for NIST NVD API v2.0."""

    def __init__(self, api_key: str | None = None):
        super().__init__(
            base_url="https://services.nvd.nist.gov/rest/json/cves/2.0",
            timeout=15,
            min_interval=6.0 if api_key is None else 0.6,
        )
        if api_key:
            self._session.headers.update({"apiKey": api_key})

    def get_cve(self, cve_id: str) -> dict[str, Any] | None:
        """Fetch a single CVE by ID. Returns normalised dict or None."""
        data = self.get("", params={"cveId": cve_id})
        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return None
        return self._parse_cve(vulns[0]["cve"])

    def search(
        self,
        severity: str | None = None,
        start_index: int = 0,
        results_per_page: int = 20,
    ) -> list[dict[str, Any]]:
        """Search CVEs with optional severity filter."""
        params: dict[str, Any] = {
            "startIndex": start_index,
            "resultsPerPage": min(results_per_page, 100),
        }
        if severity:
            params["cvssV3Severity"] = severity.upper()
        data = self.get("", params=params)
        return [
            parsed
            for v in data.get("vulnerabilities", [])
            if (parsed := self._parse_cve(v["cve"])) is not None
        ]

    def _parse_cve(self, cve: dict) -> dict[str, Any] | None:
        """Normalise raw NVD CVE record."""
        description = self._extract_description(cve)
        if not description or len(description) < 10:
            return None

        cvss_score, cvss_version, cvss_vector = self._extract_cvss(cve)

        return {
            "id": cve["id"],
            "description": description,
            "cvss_score": cvss_score,
            "cvss_version": cvss_version,
            "cvss_vector": cvss_vector,
            "cwe": self._extract_cwe(cve),
            "published": cve.get("published"),
            "last_modified": cve.get("lastModified"),
            "source": "nvd",
        }

    @staticmethod
    def _extract_description(cve: dict) -> str | None:
        for desc in cve.get("descriptions", []):
            if desc.get("lang") == "en":
                return desc["value"]
        return None

    @staticmethod
    def _extract_cvss(cve: dict) -> tuple[float | None, str | None, str | None]:
        metrics = cve.get("metrics", {})
        for key in ("cvssMetricV31", "cvssMetricV30"):
            entries = metrics.get(key, [])
            if entries:
                data = entries[0].get("cvssData", {})
                return (
                    data.get("baseScore"),
                    data.get("version"),
                    data.get("vectorString"),
                )
        return None, None, None

    @staticmethod
    def _extract_cwe(cve: dict) -> str | None:
        for weakness in cve.get("weaknesses", []):
            for desc in weakness.get("description", []):
                value = desc.get("value", "")
                if value.startswith("CWE-") and value not in ("CWE-Other", "CWE-noinfo"):
                    return value
        return None
