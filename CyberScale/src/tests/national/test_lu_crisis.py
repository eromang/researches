"""Tests for Luxembourg HCPN national crisis qualification."""

from __future__ import annotations

import pytest

from cyberscale.national.lu_crisis import (
    CriterionResult,
    HcpnQualificationResult,
    evaluate_criterion_1,
    evaluate_criterion_2,
    evaluate_criterion_3,
    qualify_hcpn_incident,
    evaluate_threat_probability,
    qualify_hcpn_threat,
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


class TestQualifyHcpnIncident:
    """Full incident qualification: all 3 criteria must be met (or C2 bypassed via fast-track)."""

    def test_all_criteria_met_national_crisis(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"], entity_types=["electricity_undertaking"],
            safety_impact="death", service_impact="unavailable",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "national_major_incident"
        assert result.cooperation_mode == "crise"
        assert result.criteria["criterion_1"].status == "met"
        assert result.criteria["criterion_2"].status == "met"
        assert result.criteria["criterion_3"].status == "met"

    def test_all_criteria_met_potential_prejudice_alerte(self):
        result = qualify_hcpn_incident(
            sectors_affected=["health"], entity_types=[],
            safety_impact="health_damage", service_impact="unavailable",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=False,
        )
        assert result.qualifies is True
        assert result.cooperation_mode == "alerte_cerc"

    def test_cross_border_qualifies_large_scale(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"], entity_types=[],
            safety_impact="death", service_impact="unavailable",
            cross_border=True,
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cybersecurity_incident"
        assert result.cooperation_mode == "crise"

    def test_capacity_exceeded_qualifies_large_scale(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"], entity_types=[],
            safety_impact="death", service_impact="unavailable",
            capacity_exceeded=True,
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cybersecurity_incident"

    def test_criterion_1_not_met_does_not_qualify(self):
        result = qualify_hcpn_incident(
            sectors_affected=["food"], entity_types=[],
            safety_impact="death", service_impact="unavailable",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is False
        assert result.qualification_level == "none"
        assert result.cooperation_mode == "permanent"

    def test_criterion_3_not_met_does_not_qualify(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"], entity_types=[],
            safety_impact="death", service_impact="unavailable",
            coordination_required=False, urgent_decisions_required=False, prejudice_actual=True,
        )
        assert result.qualifies is False

    def test_undetermined_criterion_recommends_consultation(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"], entity_types=[],
            service_impact="degraded",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=False,
        )
        assert result.recommend_consultation is True
        assert len(result.consultation_reasons) > 0

    def test_fast_track_bypasses_criterion_2(self):
        result = qualify_hcpn_incident(
            sectors_affected=["digital_infrastructure"], entity_types=[],
            service_impact="unavailable", data_impact="accessed",
            suspected_malicious=True,
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.fast_tracked is True
        assert result.qualifies is True
        assert result.criteria["criterion_2"].status == "bypassed"
        assert any("fast-track" in d.lower() for d in result.criteria["criterion_2"].details)


class TestThreatProbability:
    """Criterion 2 (threats): Only High and Imminent qualify."""

    def test_high_qualifies(self):
        result = evaluate_threat_probability("high")
        assert result.status == "met"

    def test_imminent_qualifies(self):
        result = evaluate_threat_probability("imminent")
        assert result.status == "met"

    def test_moderate_does_not_qualify(self):
        result = evaluate_threat_probability("moderate")
        assert result.status == "not_met"

    def test_low_does_not_qualify(self):
        result = evaluate_threat_probability("low")
        assert result.status == "not_met"

    def test_unknown_does_not_qualify(self):
        result = evaluate_threat_probability("unknown")
        assert result.status == "not_met"


class TestQualifyHcpnThreat:
    """Full threat qualification: all 4 criteria must be met."""

    def test_all_criteria_met_national_threat(self):
        result = qualify_hcpn_threat(
            sectors_affected=["energy"], entity_types=[],
            threat_probability="high",
            safety_impact="death", service_impact="unavailable",
            threat_actor_type="state_actor",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=False,
        )
        assert result.qualifies is True
        assert result.qualification_level == "national_major_cyber_threat"
        assert result.cooperation_mode == "alerte_cerc"
        assert result.event_type == "threat"

    def test_low_probability_does_not_qualify(self):
        result = qualify_hcpn_threat(
            sectors_affected=["energy"], entity_types=[],
            threat_probability="low",
            safety_impact="death", service_impact="unavailable",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=False,
        )
        assert result.qualifies is False

    def test_cross_border_threat_large_scale(self):
        result = qualify_hcpn_threat(
            sectors_affected=["digital_infrastructure"], entity_types=[],
            threat_probability="imminent",
            service_impact="unavailable", data_impact="compromised", financial_impact="severe",
            cross_border=True,
            threat_actor_type="state_actor", sensitive_data_type="government_data",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cyber_threat"
        assert result.cooperation_mode == "crise"

    def test_capacity_exceeded_threat_large_scale(self):
        result = qualify_hcpn_threat(
            sectors_affected=["energy"], entity_types=[],
            threat_probability="imminent",
            safety_impact="death", service_impact="unavailable",
            capacity_exceeded=True,
            threat_actor_type="state_actor",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cyber_threat"

    def test_moderate_probability_does_not_qualify(self):
        result = qualify_hcpn_threat(
            sectors_affected=["health"], entity_types=[],
            threat_probability="moderate",
            safety_impact="health_damage", service_impact="unavailable", financial_impact="significant",
            coordination_required=True, urgent_decisions_required=True, prejudice_actual=False,
        )
        assert result.qualifies is False
