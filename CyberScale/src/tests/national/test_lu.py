"""Tests for Luxembourg national-layer threshold assessment."""

from __future__ import annotations

import pytest

from cyberscale.national.lu import (
    is_lu_covered,
    get_lu_sector_key,
    is_lu_dora,
    assess_lu_significance,
    LuSignificanceResult,
)


class TestLuCoverage:
    def test_electricity_entity_covered(self):
        assert is_lu_covered("energy", "electricity_undertaking") is True

    def test_gas_entity_covered(self):
        assert is_lu_covered("energy", "gas_undertaking") is True

    def test_rail_entity_covered(self):
        assert is_lu_covered("transport", "railway_undertaking") is True

    def test_road_entity_covered(self):
        assert is_lu_covered("transport", "road_transport_operator") is True

    def test_air_entity_covered(self):
        assert is_lu_covered("transport", "air_carrier") is True

    def test_hospital_covered(self):
        assert is_lu_covered("health", "healthcare_provider") is True

    def test_laboratory_covered(self):
        assert is_lu_covered("health", "eu_reference_laboratory") is True

    def test_drinking_water_covered(self):
        assert is_lu_covered("drinking_water", "drinking_water_supplier") is True

    def test_digital_service_provider_covered(self):
        assert is_lu_covered("digital_providers", "digital_service_provider") is True

    def test_ir_entity_not_covered(self):
        """IR entities bypass LU thresholds even in Luxembourg."""
        assert is_lu_covered("digital_infrastructure", "cloud_computing_provider") is False
        assert is_lu_covered("digital_infrastructure", "dns_service_provider") is False
        assert is_lu_covered("digital_infrastructure", "ixp_operator") is False
        assert is_lu_covered("digital_infrastructure", "trust_service_provider") is False

    def test_non_covered_sector_not_covered(self):
        assert is_lu_covered("waste_water", "waste_water_operator") is False
        assert is_lu_covered("space", "space_operator") is False

    def test_banking_not_covered_dora_applies(self):
        assert is_lu_covered("banking", "credit_institution") is False
        assert is_lu_dora("banking") is True

    def test_financial_market_not_covered_dora_applies(self):
        assert is_lu_covered("financial_market_infrastructure", "trading_venue") is False
        assert is_lu_dora("financial_market_infrastructure") is True

    def test_sector_key_mapping(self):
        assert get_lu_sector_key("electricity_undertaking") == "energy_electricity"
        assert get_lu_sector_key("gas_undertaking") == "energy_gas"
        assert get_lu_sector_key("railway_undertaking") == "transport_rail"
        assert get_lu_sector_key("healthcare_provider") == "health_hospital"
        assert get_lu_sector_key("cloud_computing_provider") is None


class TestCommonCriteria:
    def test_safety_risk_triggers(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            safety_impact="health_damage",
        )
        assert result.significant_incident is True
        assert any("safety" in c for c in result.common_criteria_met)

    def test_material_damage_triggers(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            financial_impact="significant",
        )
        assert result.significant_incident is True
        assert any("material damage" in c for c in result.common_criteria_met)

    def test_data_loss_over_50_users(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            affected_persons_count=51,
        )
        assert result.significant_incident is True
        assert any("50 LU users" in c for c in result.common_criteria_met)

    def test_data_loss_at_50_not_triggered(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            affected_persons_count=50,
        )
        # 50 is not > 50
        assert not any("50 LU users" in c for c in result.common_criteria_met)

    def test_road_transport_higher_damage_threshold(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="road_transport_operator",
            financial_impact="significant",
        )
        assert result.significant_incident is True
        assert any("200,000" in c for c in result.common_criteria_met)


class TestElectricity:
    def test_lv_pod_100_60min(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            impact_duration_hours=1.0,
            sector_specific={"pods_affected": 100, "voltage_level": "lv"},
        )
        assert result.significant_incident is True
        assert any("100 LV-POD" in c for c in result.triggered_criteria)

    def test_lv_pod_100_below_60min(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            impact_duration_hours=0.9,
            sector_specific={"pods_affected": 100, "voltage_level": "lv"},
        )
        # 54 min < 60 min, and 100 POD < 500 for 30 min
        assert not any("LV-POD" in c for c in result.triggered_criteria)

    def test_lv_pod_500_30min(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            impact_duration_hours=0.5,
            sector_specific={"pods_affected": 500, "voltage_level": "lv"},
        )
        assert result.significant_incident is True
        assert any("500 LV-POD" in c for c in result.triggered_criteria)

    def test_lv_pod_100000_any_duration(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            impact_duration_hours=0,
            sector_specific={"pods_affected": 100000, "voltage_level": "lv"},
        )
        assert result.significant_incident is True

    def test_mv_pod_10_30min(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            impact_duration_hours=0.5,
            sector_specific={"pods_affected": 10, "voltage_level": "mv"},
        )
        assert result.significant_incident is True
        assert any("MV-POD" in c for c in result.triggered_criteria)

    def test_hv_ehv_automatic(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            sector_specific={"voltage_level": "hv_ehv"},
        )
        assert result.significant_incident is True
        assert any("HV/EHV" in c for c in result.triggered_criteria)

    def test_scada_automatic(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            sector_specific={"scada_unavailable_min": 1},
        )
        assert result.significant_incident is True
        assert any("SCADA" in c for c in result.triggered_criteria)

    def test_cross_border_automatic(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            cross_border=True,
        )
        assert result.significant_incident is True
        assert any("cross-border" in c for c in result.triggered_criteria)

    def test_no_criteria_met(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
        )
        assert result.significant_incident is False
        assert result.ilr_reference == "ILR/N22/4"


class TestGas:
    def test_scada_30min(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="gas_undertaking",
            sector_specific={"scada_unavailable_min": 30},
        )
        assert result.significant_incident is True
        assert any("SCADA" in c for c in result.triggered_criteria)

    def test_scada_29min_not_triggered(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="gas_undertaking",
            sector_specific={"scada_unavailable_min": 29},
        )
        assert not any("SCADA" in c for c in result.triggered_criteria)

    def test_valve_control_loss(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="gas_undertaking",
            sector_specific={"valve_control_loss": True},
        )
        assert result.significant_incident is True
        assert any("valve" in c for c in result.triggered_criteria)

    def test_transmission_network(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="gas_undertaking",
            sector_specific={"transmission_network_incident": True},
        )
        assert result.significant_incident is True


class TestTransportRail:
    def test_trains_cancelled_5pct(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="railway_undertaking",
            sector_specific={"trains_cancelled_pct": 5.0},
        )
        assert result.significant_incident is True
        assert any("5% trains" in c for c in result.triggered_criteria)

    def test_trains_cancelled_below_threshold(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="railway_undertaking",
            sector_specific={"trains_cancelled_pct": 4.9},
        )
        assert not any("trains" in c for c in result.triggered_criteria)

    def test_slots_impacted_100(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="railway_undertaking",
            sector_specific={"slots_impacted": 100},
        )
        assert result.significant_incident is True
        assert any("100 slots" in c for c in result.triggered_criteria)

    def test_infrastructure_unavailable_4h(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="railway_undertaking",
            impact_duration_hours=4,
        )
        assert result.significant_incident is True
        assert any("4h" in c for c in result.triggered_criteria)


class TestTransportRoad:
    def test_service_unavailable_2h(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="road_transport_operator",
            impact_duration_hours=2,
        )
        assert result.significant_incident is True
        assert any("2 hours" in c for c in result.triggered_criteria)

    def test_service_unavailable_below_2h(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="road_transport_operator",
            impact_duration_hours=1.9,
        )
        assert not any("2 hours" in c for c in result.triggered_criteria)

    def test_data_loss_over_50(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="road_transport_operator",
            affected_persons_count=51,
        )
        assert result.significant_incident is True


class TestTransportAir:
    def test_flights_cancelled_over_4(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="air_carrier",
            sector_specific={"flights_cancelled": 5},
        )
        assert result.significant_incident is True
        assert any("4 flights" in c for c in result.triggered_criteria)

    def test_flights_cancelled_at_4_not_triggered(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="air_carrier",
            sector_specific={"flights_cancelled": 4},
        )
        assert not any("flights" in c for c in result.triggered_criteria)

    def test_ops_unavailable_over_4h(self):
        result = assess_lu_significance(
            sector="transport",
            entity_type="air_carrier",
            impact_duration_hours=5,
        )
        assert result.significant_incident is True
        assert any("4 hours" in c for c in result.triggered_criteria)


class TestHealthHospital:
    def test_reversible_10_persons(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="healthcare_provider",
            sector_specific={"persons_health_impact": 10},
        )
        assert result.significant_incident is True
        assert any("10 persons" in c for c in result.triggered_criteria)

    def test_reversible_9_persons_not_triggered(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="healthcare_provider",
            sector_specific={"persons_health_impact": 9},
        )
        assert not any("10 persons" in c for c in result.triggered_criteria)

    def test_irreversible_1_person(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="healthcare_provider",
            safety_impact="health_damage",
            sector_specific={"persons_health_impact": 1},
        )
        assert result.significant_incident is True
        assert any("irreversible" in c for c in result.triggered_criteria)

    def test_death(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="healthcare_provider",
            safety_impact="death",
            sector_specific={"persons_health_impact": 1},
        )
        assert result.significant_incident is True
        assert any("death" in c for c in result.triggered_criteria)


class TestHealthLaboratory:
    def test_100pct_2h(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="eu_reference_laboratory",
            impact_duration_hours=2,
            sector_specific={"analyses_affected_pct": 100},
        )
        assert result.significant_incident is True
        assert any("100%" in c for c in result.triggered_criteria)

    def test_50pct_4h(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="eu_reference_laboratory",
            impact_duration_hours=4,
            sector_specific={"analyses_affected_pct": 50},
        )
        assert result.significant_incident is True
        assert any("50-100%" in c for c in result.triggered_criteria)

    def test_50pct_3h_not_triggered(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="eu_reference_laboratory",
            impact_duration_hours=3,
            sector_specific={"analyses_affected_pct": 50},
        )
        assert not any("analyses" in c for c in result.triggered_criteria)

    def test_person_endangered(self):
        result = assess_lu_significance(
            sector="health",
            entity_type="eu_reference_laboratory",
            sector_specific={"persons_health_impact": 1},
        )
        assert result.significant_incident is True
        assert any("endangered" in c for c in result.triggered_criteria)


class TestDrinkingWater:
    def test_25pct_50000_any_duration(self):
        result = assess_lu_significance(
            sector="drinking_water",
            entity_type="drinking_water_supplier",
            affected_persons_count=50000,
            sector_specific={"users_pct": 25},
        )
        assert result.significant_incident is True

    def test_cross_border(self):
        result = assess_lu_significance(
            sector="drinking_water",
            entity_type="drinking_water_supplier",
            cross_border=True,
        )
        assert result.significant_incident is True
        assert any("cross-border" in c for c in result.triggered_criteria)


class TestDigitalServiceProviders:
    def test_user_hours_over_5m(self):
        result = assess_lu_significance(
            sector="digital_providers",
            entity_type="digital_service_provider",
            affected_persons_count=1000000,
            impact_duration_hours=6,
        )
        assert result.significant_incident is True
        assert any("5,000,000 user-hours" in c for c in result.triggered_criteria)

    def test_user_hours_at_5m_not_triggered(self):
        result = assess_lu_significance(
            sector="digital_providers",
            entity_type="digital_service_provider",
            affected_persons_count=1000000,
            impact_duration_hours=5,
        )
        assert not any("user-hours" in c for c in result.triggered_criteria)

    def test_eu_users_over_100k(self):
        result = assess_lu_significance(
            sector="digital_providers",
            entity_type="digital_service_provider",
            affected_persons_count=100001,
        )
        assert result.significant_incident is True
        assert any("100,000 EU users" in c for c in result.triggered_criteria)


class TestDORA:
    def test_banking_returns_dora_framework(self):
        result = assess_lu_significance(
            sector="banking",
            entity_type="credit_institution",
        )
        assert result.ilr_reference == "DORA"
        assert result.competent_authority == "CSSF"
        assert len(result.applicable_frameworks) == 1
        assert result.applicable_frameworks[0]["framework"] == "DORA"
        assert result.applicable_frameworks[0]["initial_notification_hours"] == 4


class TestResultStructure:
    def test_result_to_dict(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            sector_specific={"voltage_level": "hv_ehv"},
        )
        d = result.to_dict()
        assert "significant_incident" in d
        assert "triggered_criteria" in d
        assert "ilr_reference" in d
        assert "common_criteria_met" in d
        assert "competent_authority" in d
        assert "applicable_frameworks" in d

    def test_applicable_frameworks_present(self):
        result = assess_lu_significance(
            sector="energy",
            entity_type="electricity_undertaking",
        )
        assert len(result.applicable_frameworks) >= 1
        fw = result.applicable_frameworks[0]
        assert fw["framework"] == "NIS1-LU (ILR)"
        assert fw["ilr_reference"] == "ILR/N22/4"
        assert fw["pre_notification_hours"] == 24
        assert fw["full_notification_days"] == 15
