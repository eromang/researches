"""Tests for Luxembourg HCPN national crisis qualification."""

from __future__ import annotations

import pytest

from cyberscale.national.lu_crisis import (
    CriterionResult,
    HcpnQualificationResult,
    evaluate_criterion_1,
)


class TestCriterionResult:
    def test_met(self):
        r = CriterionResult(status="met", details=["energy sector"])
        assert r.is_met is True
        assert r.is_undetermined is False
        assert r.is_bypassed is False

    def test_not_met(self):
        r = CriterionResult(status="not_met", details=[])
        assert r.is_met is False

    def test_undetermined(self):
        r = CriterionResult(status="undetermined", details=["threshold delegated"])
        assert r.is_undetermined is True
        assert r.is_met is False

    def test_bypassed(self):
        r = CriterionResult(status="bypassed", details=["fast-track"])
        assert r.is_bypassed is True
        assert r.is_met is False
        assert r.is_undetermined is False


class TestCriterion1EssentialService:
    """Criterion 1: The incident must affect at least one essential service."""

    def test_energy_sector_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["energy"], entity_types=[])
        assert result.status == "met"
        assert "energy" in result.details[0]

    def test_transport_sector_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["transport"], entity_types=[])
        assert result.status == "met"

    def test_health_sector_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["health"], entity_types=[])
        assert result.status == "met"

    def test_non_essential_sector(self):
        result = evaluate_criterion_1(sectors_affected=["food"], entity_types=[])
        assert result.status == "not_met"

    def test_multiple_sectors_one_essential(self):
        result = evaluate_criterion_1(sectors_affected=["food", "energy"], entity_types=[])
        assert result.status == "met"

    def test_empty_sectors(self):
        result = evaluate_criterion_1(sectors_affected=[], entity_types=[])
        assert result.status == "not_met"

    def test_digital_infrastructure_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["digital_infrastructure"], entity_types=[])
        assert result.status == "met"

    def test_public_administration_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["public_administration"], entity_types=[])
        assert result.status == "met"

    def test_banking_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["banking"], entity_types=[])
        assert result.status == "met"

    def test_space_is_essential(self):
        result = evaluate_criterion_1(sectors_affected=["space"], entity_types=[])
        assert result.status == "met"
