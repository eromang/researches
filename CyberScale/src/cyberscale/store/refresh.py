"""Store refresh mechanism — populates ChromaDB from live API data."""

from typing import Any

from cyberscale.api.lookup import UnifiedLookup
from cyberscale.store.client import VulnStore


class StoreRefresher:
    """Fetch vulnerability data from APIs and update the vector store."""

    def __init__(
        self,
        lookup: UnifiedLookup | None = None,
        store: VulnStore | None = None,
    ):
        self.lookup = lookup or UnifiedLookup()
        self.store = store or VulnStore()

    def refresh_cve(self, cve_id: str) -> bool:
        """Fetch a single CVE and add/update in store. Returns True if stored."""
        result = self.lookup.lookup_cve(cve_id)
        if result is None:
            return False

        self.store.add(
            cve_id=result["id"],
            description=result.get("description", ""),
            cvss_score=result.get("cvss_score"),
            cvss_version=result.get("cvss_version"),
            cwe=result.get("cwe"),
            source=result.get("sources", ["unknown"])[0],
        )
        return True

    def refresh_batch(self, cve_ids: list[str]) -> dict[str, Any]:
        """Refresh multiple CVEs. Returns summary."""
        added = 0
        failed = 0
        for cve_id in cve_ids:
            if self.refresh_cve(cve_id):
                added += 1
            else:
                failed += 1
        return {"added": added, "failed": failed, "total": len(cve_ids)}
