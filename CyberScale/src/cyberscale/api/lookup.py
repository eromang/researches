"""Unified multi-source vulnerability lookup facade."""

from datetime import date
from typing import Any

from cyberscale.api.nvd import NVDClient
from cyberscale.api.euvd import EUVDClient
from cyberscale.api.circl import CIRCLClient


def _as_date(value: Any) -> date | None:
    """Parse the leading YYYY-MM-DD of an ISO timestamp, or None."""
    if not isinstance(value, str) or len(value) < 10:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


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

        merged = self._merge(cve_id, results, sources)
        self._attach_exploitation(cve_id, merged)
        return merged

    def _attach_exploitation(self, cve_id: str, merged: dict[str, Any]) -> None:
        """Add exploitation status and timing from CIRCL's KEV catalog.

        `exploited` is deliberately three-valued. True and False are answers from
        the catalog; None means the lookup failed and we do not know. Collapsing
        the last case into False would report "not exploited" for every network
        error, which is the wrong direction to be wrong in.
        """
        kev = self._safe_call(self.circl.get_kev_status, cve_id)
        if kev is None:
            merged["exploited"] = None
            merged["exploitation_lookup"] = "failed"
            return

        merged["exploited"] = kev["exploited"]
        merged["exploited_date"] = kev["exploited_date"]
        merged["exploit_sources"] = kev["exploit_sources"]
        merged["in_cisa_kev"] = kev["in_cisa_kev"]
        merged["exploitation_lookup"] = "ok"

        published = _as_date(merged.get("published"))
        exploited = _as_date(kev["exploited_date"])
        if published and exploited:
            # Negative values are real: some CVEs are exploited before the
            # record is published. Left signed rather than clamped.
            merged["time_to_exploit_days"] = (exploited - published).days
        else:
            merged["time_to_exploit_days"] = None

    def age_days(self, merged: dict[str, Any], as_of: date | None = None) -> int | None:
        """Vulnerability age in days at `as_of` (default today).

        Kept out of the merged record on purpose: age depends on when you ask,
        and a field whose value silently changes between calls does not belong
        in something callers may cache or store.
        """
        published = _as_date(merged.get("published"))
        if published is None:
            return None
        return ((as_of or date.today()) - published).days

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

        # Publication date: NVD and CIRCL call it `published`, EUVD
        # `date_published`. Needed for time-to-exploit and for age.
        for result in results:
            published = result.get("published") or result.get("date_published")
            if published:
                merged["published"] = published
                break
        else:
            merged["published"] = None

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
