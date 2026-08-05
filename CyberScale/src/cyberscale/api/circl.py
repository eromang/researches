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

    def get_kev_status(self, cve_id: str) -> dict[str, Any]:
        """Exploitation status and dates for one CVE, from CIRCL's KEV catalog.

        Returns a record whether or not the CVE is listed, so callers can tell
        "the catalog says no" from "the lookup failed" — the latter raises.

        `exploited_date` is the earliest first-seen date across upstream sources.
        Validated against CISA's own `dateAdded` on the 1,660 overlapping
        entries: 1,659 exact matches, so the dates carry upstream timing rather
        than CIRCL ingest time.
        """
        data = self.get("/api/kev", params={"vuln_id": cve_id})
        records = [self._parse_kev_item(item) for item in data.get("data", [])]
        records = [r for r in records if r]

        if not records:
            return {
                "cve_id": cve_id,
                "exploited": False,
                "exploited_date": None,
                "exploit_sources": [],
                "in_cisa_kev": False,
            }

        dates = sorted(r["exploited_date"] for r in records if r["exploited_date"])
        sources = sorted({s for r in records for s in r["sources"]})
        return {
            "cve_id": cve_id,
            "exploited": True,
            "exploited_date": dates[0] if dates else None,
            "exploit_sources": sources,
            "in_cisa_kev": "cisa-kev" in sources,
            "observed_by_sensors": "shadowserver" in sources,
        }

    def get_kev(self, limit: int | None = None) -> list[dict[str, Any]]:
        """CIRCL's full KEV catalog, one record per (CVE, upstream source).

        Held 5,693 records over 2,789 distinct CVEs on 2026-08-05 — a strict
        superset of CISA KEV plus 1,125 CVEs that neither CISA nor ENISA's EUVD
        lists. Unlike either, it records which source saw each entry, which is
        what lets curated catalogue timing be told apart from sensor telemetry.
        """
        out: list[dict[str, Any]] = []
        page = 1
        while True:
            data = self.get("/api/kev", params={"per_page": 1000, "page": page})
            batch = data.get("data", [])
            out.extend(r for r in (self._parse_kev_item(i) for i in batch) if r)
            if len(batch) < 1000:
                break
            if limit is not None and len(out) >= limit:
                break
            page += 1
        return out[:limit] if limit is not None else out

    @staticmethod
    def _parse_kev_item(item: dict) -> dict[str, Any] | None:
        """Normalise one KEV record. Returns None if it carries no CVE id."""
        cve_id = (item.get("vulnerability") or {}).get("vulnId")
        if not cve_id or not cve_id.startswith("CVE-"):
            # CIRCL also carries EDB-/SSV-/GCVE- identifiers, which have no CVE.
            return None
        timestamps = item.get("timestamps") or {}
        first_seen = timestamps.get("first_seen_at") or ""
        return {
            "cve_id": cve_id,
            "exploited_date": first_seen[:10] or None,
            "sources": sorted(
                {e.get("source") for e in item.get("evidence", []) if e.get("source")}
            ),
            "status_reason": (item.get("status") or {}).get("status_reason"),
        }

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
