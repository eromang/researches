"""Phase 2 MCP tools — Contextual severity with model integration."""

from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP


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

VALID_SECTORS = {
    "energy", "transport", "banking", "financial_market", "health",
    "drinking_water", "waste_water", "digital_infrastructure",
    "ict_service_management", "public_administration", "space",
    "postal", "waste_management", "manufacturing", "chemicals",
    "food", "digital_providers", "research", "non_nis2",
}


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
    cross_border: bool,
    score: float | None = None,
    deployment_scale: str | None = None,
    entity_type: str | None = None,
) -> dict:
    """Assess contextual severity using the classifier model."""
    result = clf.predict(
        description, sector, cross_border, score,
        deployment_scale=deployment_scale, entity_type=entity_type,
    )
    out = {
        "severity": result.severity,
        "confidence": result.confidence,
        "key_factors": result.key_factors,
        "sector": sector,
        "cross_border": cross_border,
    }
    if deployment_scale is not None:
        out["deployment_scale"] = deployment_scale
    if entity_type is not None:
        out["entity_type"] = entity_type
    return out


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_contextual_severity(
        description: str,
        sector: str,
        cross_border: bool,
        severity_score: float | None = None,
        deployment_scale: str | None = None,
        entity_type: str | None = None,
    ) -> dict:
        """Assess context-dependent severity for a vulnerability given NIS2 sector, cross-border exposure, and deployment context."""
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
            clf, description, sector, cross_border,
            score=severity_score, deployment_scale=deployment_scale,
            entity_type=entity_type,
        )
