"""EUVD API client (ENISA European Vulnerability Database)."""

from typing import Any

from cyberscale.api.base import APIClient


class EUVDClient(APIClient):
    """Client for EUVD API at euvdservices.enisa.europa.eu."""

    def __init__(self):
        super().__init__(
            base_url="https://euvdservices.enisa.europa.eu/api",
            timeout=15,
            min_interval=1.0,
        )

    def search(
        self,
        from_score: float | None = None,
        to_score: float | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        product: str | None = None,
        vendor: str | None = None,
        exploited: bool | None = None,
        text: str | None = None,
        page: int = 0,
        size: int = 100,
    ) -> list[dict[str, Any]]:
        """Search EUVD vulnerabilities."""
        params: dict[str, Any] = {"page": page, "size": min(size, 100)}
        if from_score is not None:
            params["fromScore"] = from_score
        if to_score is not None:
            params["toScore"] = to_score
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date
        if product:
            params["product"] = product
        if vendor:
            params["vendor"] = vendor
        if exploited is not None:
            params["exploited"] = str(exploited).lower()
        if text:
            params["text"] = text

        data = self.get("/search", params=params)
        items = data.get("items", [])
        return [self._parse_item(item) for item in items]

    def get_by_euvd_id(self, euvd_id: str) -> dict[str, Any] | None:
        """Lookup a single vulnerability by EUVD ID."""
        data = self.get("/enisaid", params={"id": euvd_id})
        if not data:
            return None
        return self._parse_item(data)

    def get_by_advisory(self, advisory_id: str) -> dict[str, Any] | None:
        """Lookup by vendor advisory ID."""
        return self.get("/advisory", params={"id": advisory_id})

    def get_exploited(self) -> list[dict[str, Any]]:
        """Get latest exploited vulnerabilities (max 8)."""
        items = self.get("/exploitedvulnerabilities")
        return [self._parse_item(item) for item in items]

    def _parse_item(self, item: dict) -> dict[str, Any]:
        """Normalise EUVD vulnerability record."""
        raw_score = item.get("baseScore")
        cvss_score = raw_score if raw_score is not None and raw_score >= 0 else None

        aliases = item.get("aliases", "") or ""
        alias_list = [a.strip() for a in aliases.split("\n") if a.strip()]
        cve_ids = [a for a in alias_list if a.startswith("CVE-")]

        products = [
            p["product"]["name"]
            for p in item.get("enisaIdProduct", [])
            if p.get("product", {}).get("name")
        ]
        vendors = [
            v["vendor"]["name"]
            for v in item.get("enisaIdVendor", [])
            if v.get("vendor", {}).get("name")
        ]

        return {
            "euvd_id": item.get("id"),
            "description": item.get("description"),
            "cvss_score": cvss_score,
            "cvss_version": item.get("baseScoreVersion") or None,
            "cvss_vector": item.get("baseScoreVector") or None,
            "cve_ids": cve_ids,
            "aliases": alias_list,
            "epss": item.get("epss"),
            "products": products,
            "vendors": vendors,
            "date_published": item.get("datePublished"),
            "date_updated": item.get("dateUpdated"),
            "source": "euvd",
        }
