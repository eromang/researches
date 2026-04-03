"""Tests for Luxembourg HCPN national crisis qualification."""

from __future__ import annotations

import pytest

from cyberscale.national.lu_crisis import (
    CriterionResult,
    HcpnQualificationResult,
    evaluate_criterion_1,
    evaluate_criterion_2,
    evaluate_criterion_3,
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


class TestCriterion2PrejudiceVitalInterests:
    """Criterion 2: At least one of seven sub-criteria must be satisfied."""

    def test_death_triggers_human_impact(self):
        result = evaluate_criterion_2(safety_impact="death")
        assert result.status == "met"
        assert any("death" in d.lower() or "human impact" in d.lower() for d in result.details)

    def test_health_damage_triggers_human_impact(self):
        result = evaluate_criterion_2(safety_impact="health_damage")
        assert result.status == "met"

    def test_no_safety_impact_no_human_impact(self):
        result = evaluate_criterion_2()
        assert result.status == "not_met"

    def test_state_actor_triggers_national_security(self):
        result = evaluate_criterion_2(threat_actor_type="state_actor")
        assert result.status == "met"
        assert any("national security" in d.lower() for d in result.details)

    def test_terrorist_group_triggers_national_security(self):
        result = evaluate_criterion_2(threat_actor_type="terrorist_group")
        assert result.status == "met"

    def test_public_admin_sector_triggers_national_security(self):
        result = evaluate_criterion_2(sectors_affected=["public_administration"])
        assert result.status == "met"

    def test_government_data_loss_triggers(self):
        result = evaluate_criterion_2(data_impact="exfiltrated", sensitive_data_type="government_data")
        assert result.status == "met"
        assert any("sensitive data" in d.lower() for d in result.details)

    def test_industrial_secrets_loss_triggers(self):
        result = evaluate_criterion_2(data_impact="compromised", sensitive_data_type="industrial_secrets")
        assert result.status == "met"

    def test_data_impact_without_sensitive_type_does_not_trigger(self):
        result = evaluate_criterion_2(data_impact="exfiltrated")
        assert result.status == "not_met"

    def test_total_service_interruption_essential_sector_met(self):
        result = evaluate_criterion_2(service_impact="unavailable", sectors_affected=["energy"])
        assert result.status == "met"
        assert any("service interruption" in d.lower() for d in result.details)

    def test_total_service_interruption_non_essential_does_not_trigger(self):
        result = evaluate_criterion_2(service_impact="unavailable", sectors_affected=["food"])
        assert result.status == "not_met"

    def test_degraded_service_undetermined(self):
        result = evaluate_criterion_2(service_impact="degraded", sectors_affected=["energy"])
        assert result.status == "undetermined"
        assert any("significant duration" in d.lower() for d in result.details)

    def test_cross_border_undetermined(self):
        result = evaluate_criterion_2(cross_border=True)
        assert result.status == "undetermined"
        assert any("geographic" in d.lower() for d in result.details)

    def test_any_affected_persons_undetermined(self):
        result = evaluate_criterion_2(affected_persons_count=1)
        assert result.status == "undetermined"
        assert any("users affected" in d.lower() for d in result.details)

    def test_zero_affected_persons_no_trigger(self):
        result = evaluate_criterion_2(affected_persons_count=0)
        assert result.status == "not_met"

    def test_severe_financial_impact_undetermined(self):
        result = evaluate_criterion_2(financial_impact="severe")
        assert result.status == "undetermined"
        assert any("economic" in d.lower() for d in result.details)

    def test_interdependent_sector_disruption_met(self):
        result = evaluate_criterion_2(service_impact="unavailable", sectors_affected=["energy", "transport"])
        assert result.status == "met"
        assert any("interdependent" in d.lower() or "economic" in d.lower() for d in result.details)


class TestCriterion3CoordinationUrgency:
    """Criterion 3: Both coordination AND urgency must be true."""

    def test_both_true_met(self):
        result = evaluate_criterion_3(coordination_required=True, urgent_decisions_required=True)
        assert result.status == "met"

    def test_coordination_only_not_met(self):
        result = evaluate_criterion_3(coordination_required=True, urgent_decisions_required=False)
        assert result.status == "not_met"

    def test_urgency_only_not_met(self):
        result = evaluate_criterion_3(coordination_required=False, urgent_decisions_required=True)
        assert result.status == "not_met"

    def test_neither_not_met(self):
        result = evaluate_criterion_3(coordination_required=False, urgent_decisions_required=False)
        assert result.status == "not_met"

    def test_coordination_uncertain_undetermined(self):
        result = evaluate_criterion_3(coordination_required=None, urgent_decisions_required=True)
        assert result.status == "undetermined"

    def test_urgency_uncertain_undetermined(self):
        result = evaluate_criterion_3(coordination_required=True, urgent_decisions_required=None)
        assert result.status == "undetermined"

    def test_both_uncertain_undetermined(self):
        result = evaluate_criterion_3(coordination_required=None, urgent_decisions_required=None)
        assert result.status == "undetermined"
