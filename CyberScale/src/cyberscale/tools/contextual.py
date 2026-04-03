"""Phase 2 MCP tools — Contextual severity with model integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from cyberscale.config import VALID_SECTORS


# ---------------------------------------------------------------------------
# Lazy model loading
# ---------------------------------------------------------------------------

_classifier_instance = None
_model_path = Path("data/models/contextual")


def _get_classifier():
    global _classifier_instance
    if _classifier_instance is None:
        if not _model_path.exists():
            return None
        from cyberscale.models.contextual import ContextualClassifier
        _classifier_instance = ContextualClassifier(model_path=_model_path)
    return _classifier_instance


# ---------------------------------------------------------------------------
# Sector validation
# ---------------------------------------------------------------------------


def _validate_sector(sector: str) -> tuple[bool, str]:
    """Validate that sector is in the allowed NIS2 sector list."""
    if sector not in VALID_SECTORS:
        return False, f"Unknown sector: {sector}. Valid sectors: {sorted(VALID_SECTORS)}"
    return True, ""


# ---------------------------------------------------------------------------
# Internal helper functions (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_with_model(
    clf,
    description: str,
    sector: str,
    ms_established: str = "EU",
    ms_affected: list[str] | None = None,
    score: float | None = None,
    entity_type: str | None = None,
    cer_critical_entity: bool | None = None,
) -> dict:
    """Assess contextual severity using the classifier model."""
    result = clf.predict(
        description, sector,
        ms_established=ms_established, ms_affected=ms_affected,
        score=score, entity_type=entity_type,
        cer_critical_entity=cer_critical_entity,
    )
    cross_border = bool(
        ms_affected and any(ms != ms_established for ms in ms_affected)
    )
    out = {
        "severity": result.severity,
        "confidence": result.confidence,
        "key_factors": result.key_factors,
        "sector": sector,
        "ms_established": ms_established,
        "cross_border": cross_border,
    }
    if ms_affected:
        out["ms_affected"] = ms_affected
    if entity_type is not None:
        out["entity_type"] = entity_type
    if cer_critical_entity:
        out["cer_critical_entity"] = cer_critical_entity
    return out


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_contextual_severity(
        description: str,
        sector: str,
        ms_established: str = "EU",
        ms_affected: list[str] | None = None,
        severity_score: float | None = None,
        entity_type: str | None = None,
        cer_critical_entity: bool | None = None,
    ) -> dict:
        """Assess context-dependent severity for a vulnerability given NIS2 sector, member state geography, and deployment context."""
        # 1. Validate sector
        ok, err = _validate_sector(sector)
        if not ok:
            return {"error": err}

        # 2. Get classifier
        clf = _get_classifier()
        if clf is None:
            return {"error": "No trained model available. Deploy a model to data/models/contextual/."}

        # 3. Assess with model
        return _assess_with_model(
            clf, description, sector,
            ms_established=ms_established, ms_affected=ms_affected,
            score=severity_score, entity_type=entity_type,
            cer_critical_entity=cer_critical_entity,
        )
