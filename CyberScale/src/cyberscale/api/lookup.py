"""Unified multi-source vulnerability lookup facade."""

from typing import Any

from cyberscale.api.nvd import NVDClient
from cyberscale.api.euvd import EUVDClient
from cyberscale.api.circl import CIRCLClient


class UnifiedLookup:
    """Query NVD, EUVD, and CIRCL, merge results into a single record."""

    def __init__(
        self,
        nvd: NVDClient | None = None,
        euvd: EUVDClient | None = None,
        circl: CIRCLClient | None = None,
    ):
        self.nvd = nvd or NVDClient()
        self.euvd = euvd or EUVDClient()
        self.circl = circl or CIRCLClient()

    def lookup_cve(self, cve_id: str) -> dict[str, Any] | None:
        """Lookup a CVE across all sources and merge."""
        results = []
        sources = []

        nvd_result = self._safe_call(self.nvd.get_cve, cve_id)
        if nvd_result:
            results.append(nvd_result)
            sources.append("nvd")

        euvd_results = self._safe_call(self.euvd.search, text=cve_id, size=1)
        if euvd_results:
            for r in euvd_results:
                if cve_id in r.get("cve_ids", []):
                    results.append(r)
                    sources.append("euvd")
                    break

        circl_result = self._safe_call(self.circl.get_vulnerability, cve_id)
        if circl_result:
            results.append(circl_result)
            sources.append("circl")

        if not results:
            return None

        return self._merge(cve_id, results, sources)

    def _merge(
        self, cve_id: str, results: list[dict], sources: list[str]
    ) -> dict[str, Any]:
        """Merge results with NVD priority for CVSS, richest description."""
        merged: dict[str, Any] = {
            "id": cve_id,
            "sources": sources,
        }

        # CVSS: prefer NVD, then EUVD, then CIRCL
        for result in results:
            score = result.get("cvss_score")
            if score is not None:
                merged["cvss_score"] = score
                merged["cvss_version"] = result.get("cvss_version")
                merged["cvss_vector"] = result.get("cvss_vector")
                break
        else:
            merged["cvss_score"] = None
            merged["cvss_version"] = None
            merged["cvss_vector"] = None

        # Description: longest available
        descriptions = [
            r.get("description", "") for r in results if r.get("description")
        ]
        merged["description"] = max(descriptions, key=len) if descriptions else None

        # CWE: first available
        for result in results:
            cwe = result.get("cwe")
            if cwe:
                merged["cwe"] = cwe
                break
        else:
            merged["cwe"] = None

        # EUVD-specific enrichment
        for result in results:
            if result.get("source") == "euvd":
                merged["euvd_id"] = result.get("euvd_id")
                merged["epss"] = result.get("epss")
                merged["products"] = result.get("products", [])
                merged["vendors"] = result.get("vendors", [])
                break

        return merged

    @staticmethod
    def _safe_call(func, *args, **kwargs) -> Any:
        """Call a function, return None on any exception."""
        try:
            return func(*args, **kwargs)
        except Exception:
            return None
