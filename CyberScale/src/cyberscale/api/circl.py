"""CIRCL VulnLookup API client."""

from typing import Any

import requests

from cyberscale.api.base import APIClient


class CIRCLClient(APIClient):
    """Client for CIRCL Vulnerability Lookup API."""

    def __init__(self, base_url: str = "https://vulnerability.circl.lu"):
        super().__init__(
            base_url=base_url,
            timeout=15,
            min_interval=0.5,
        )

    def get_vulnerability(self, cve_id: str) -> dict[str, Any] | None:
        """Fetch detailed vulnerability data by CVE ID."""
        try:
            data = self.get(f"/api/vulnerability/{cve_id}")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            raise
        return self._parse_cve5(data, cve_id)

    def search(
        self,
        source: str | None = None,
        cwe: str | None = None,
        product: str | None = None,
        since: str | None = None,
        sort_order: str = "desc",
        per_page: int = 10,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        """Search vulnerabilities with filters."""
        params: dict[str, Any] = {
            "sort_order": sort_order,
            "per_page": min(per_page, 100),
            "page": page,
        }
        if source:
            params["source"] = source
        if cwe:
            params["cwe"] = cwe.upper().strip()
        if product:
            params["product"] = product
        if since:
            params["since"] = since

        return self.get("/api/vulnerability/", params=params)

    def _parse_cve5(self, data: dict, cve_id: str) -> dict[str, Any] | None:
        """Parse CVE 5.0 JSON format from CIRCL."""
        cna = data.get("containers", {}).get("cna", {})
        metadata = data.get("cveMetadata", {})

        description = self._extract_description(cna)
        if not description or len(description) < 10:
            return None

        cvss_score, cvss_version = self._extract_cvss(cna)

        return {
            "id": metadata.get("cveId", cve_id),
            "title": cna.get("title"),
            "description": description,
            "cvss_score": cvss_score,
            "cvss_version": cvss_version,
            "cwe": self._extract_cwe(cna),
            "published": metadata.get("datePublished"),
            "last_modified": metadata.get("dateUpdated"),
            "source": "circl",
        }

    @staticmethod
    def _extract_description(cna: dict) -> str | None:
        for desc in cna.get("descriptions", []):
            if desc.get("lang") == "en":
                return desc["value"]
        descriptions = cna.get("descriptions", [])
        return descriptions[0]["value"] if descriptions else None

    @staticmethod
    def _extract_cvss(cna: dict) -> tuple[float | None, str | None]:
        for metric in cna.get("metrics", []):
            for key in ("cvssV3_1", "cvssV3_0"):
                if key in metric:
                    return metric[key].get("baseScore"), metric[key].get("version")
        return None, None

    @staticmethod
    def _extract_cwe(cna: dict) -> str | None:
        for pt in cna.get("problemTypes", []):
            for desc in pt.get("descriptions", []):
                cwe_id = desc.get("cweId", "")
                if cwe_id.startswith("CWE-"):
                    return cwe_id
        return None
