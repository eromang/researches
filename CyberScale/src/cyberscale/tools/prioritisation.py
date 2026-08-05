"""Phase 0 MCP tool — remediation prioritisation.

Deliberately outside the NIS2 classification path. This tool answers "what do I
fix first" (NIS2 Art. 21 risk management). It is not an input to significance
determination (Art. 23), which is impact-based: an incident does not become
notifiable because the underlying vulnerability was likely to be exploited.

That separation is the same kind as the Entity/Authority split in v4, and it is
asserted in the tests rather than left to convention.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

_lookup_instance = None


def _get_lookup():
    """Lazily construct the multi-source lookup facade."""
    global _lookup_instance
    if _lookup_instance is None:
        from cyberscale.api.lookup import UnifiedLookup
        _lookup_instance = UnifiedLookup()
    return _lookup_instance


def _prioritise_vulnerabilities(
    vulnerabilities: list[dict[str, Any]] | None = None,
    cve_ids: list[str] | None = None,
    k: float | None = None,
    as_of: str | None = None,
    top_n: int | None = None,
    lookup=None,
) -> dict[str, Any]:
    """Rank vulnerabilities by age-adjusted exploit likelihood.

    Either supply `vulnerabilities` already carrying `epss` and `published`, or
    `cve_ids` to be resolved through the multi-source lookup.
    """
    from cyberscale.prioritisation import DEFAULT_K, rank

    if not vulnerabilities and not cve_ids:
        return {"error": "Supply either `vulnerabilities` or `cve_ids`."}

    items: list[dict[str, Any]] = list(vulnerabilities or [])
    unresolved: list[dict[str, str]] = []

    if cve_ids:
        client = lookup if lookup is not None else _get_lookup()
        for cve_id in cve_ids:
            record = client.lookup_cve(cve_id)
            if record is None:
                # Not found is distinct from not urgent. Report it.
                unresolved.append({"cve_id": cve_id, "reason": "not found in any source"})
                continue
            items.append({
                "cve_id": record.get("id", cve_id),
                "epss": record.get("epss"),
                "published": record.get("published"),
                "exploited": record.get("exploited"),
                "exploit_sources": record.get("exploit_sources", []),
            })

    try:
        as_of_date = date.fromisoformat(as_of) if as_of else date.today()
    except ValueError:
        return {"error": f"as_of must be an ISO date (YYYY-MM-DD), got {as_of!r}"}

    result = rank(items, k=k if k is not None else DEFAULT_K,
                  as_of=as_of_date, top_n=top_n)
    payload = result.to_dict()
    if unresolved:
        payload["unresolved"] = unresolved
        payload["guidance"].append(
            f"{len(unresolved)} CVE(s) could not be resolved in any source and are "
            "listed in `unresolved`. They are absent from the queue, not last in it."
        )
    logger.info("prioritise_vulnerabilities: %d ranked, %d skipped, %d unresolved",
                len(payload["ranked"]), len(payload["skipped"]), len(unresolved))
    return payload


def register(mcp: FastMCP) -> None:
    """Register the Phase 0 prioritisation tool."""

    @mcp.tool
    def prioritise_vulnerabilities(
        vulnerabilities: list[dict] | None = None,
        cve_ids: list[str] | None = None,
        k: float | None = None,
        as_of: str | None = None,
        top_n: int | None = None,
    ) -> dict:
        """Rank vulnerabilities for remediation by age-adjusted exploit likelihood.

        Answers "what should I fix first" under finite capacity. This is NIS2
        Art. 21 risk management, and is NOT an input to Art. 23 significance
        determination, which is impact-based.

        vulnerabilities: records carrying at least `cve_id`, `epss` and
            `published`. The shape returned by the unified CVE lookup works
            directly, and adds exploitation status.
        cve_ids: alternatively, CVE identifiers to resolve through NVD, EUVD
            and CIRCL before ranking.
        k: Weibull shape. Defaults to 0.55, chosen for ranking performance
            rather than as a calibration claim — properly estimated values are
            0.52 for curated catalogues and 0.72 for sensor telemetry, and the
            best-fitting value is not the best-ranking one.
        as_of: reference date for computing vulnerability age (default today).
        top_n: return only the first N.

        Returns a ranked list with the inputs behind each position. It returns
        no exploit rate, event count, or probability of at least one event:
        the underlying model's rate output is denominated in third-party sensor
        detections and runs about 55x above any observable feed.

        Measured against observed exploitation, this ordering beats ranking on
        raw EPSS on AUC-ROC in 11 of 11 test cells. At the top 100 and top 1,000
        it is a wash — if your remediation capacity is in that range, expect no
        measurable gain over EPSS alone.
        """
        return _prioritise_vulnerabilities(
            vulnerabilities=vulnerabilities, cve_ids=cve_ids,
            k=k, as_of=as_of, top_n=top_n,
        )
