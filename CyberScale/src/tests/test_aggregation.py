"""Tests for multi-entity incident aggregation layer.

All aggregation logic is deterministic — 100% pass rate required.
"""

import pytest

from cyberscale.aggregation import (
    aggregate_entity_notifications,
    derive_t_level,
    derive_o_level,
    propagate_cascading,
    AggregationResult,
    _worst_case,
    _derive_cascading_from_count,
    _derive_cross_border_pattern,
    _derive_capacity_exceeded,
    _SERVICE_IMPACT_ORDER,
    _DATA_IMPACT_ORDER,
    _FINANCIAL_IMPACT_ORDER,
    _SAFETY_IMPACT_ORDER,
)


# ---------------------------------------------------------------------------
# Worst-case helpers
# ---------------------------------------------------------------------------

class TestWorstCase:
    def test_service_impact_ordering(self):
        assert _worst_case(["partial", "unavailable", "degraded"], _SERVICE_IMPACT_ORDER) == "unavailable"

    def test_data_impact_ordering(self):
        assert _worst_case(["accessed", "systemic", "none"], _DATA_IMPACT_ORDER) == "systemic"

    def test_financial_impact_ordering(self):
        assert _worst_case(["minor", "severe"], _FINANCIAL_IMPACT_ORDER) == "severe"

    def test_safety_impact_ordering(self):
        assert _worst_case(["health_risk", "death", "none"], _SAFETY_IMPACT_ORDER) == "death"

    def test_empty_list_returns_none(self):
        assert _worst_case([], _SERVICE_IMPACT_ORDER) == "none"

    def test_single_value(self):
        assert _worst_case(["degraded"], _SERVICE_IMPACT_ORDER) == "degraded"

    def test_all_none(self):
        assert _worst_case(["none", "none"], _DATA_IMPACT_ORDER) == "none"


# ---------------------------------------------------------------------------
# Derived field helpers
# ---------------------------------------------------------------------------

class TestDeriveCascading:
    def test_1_sector(self):
        assert _derive_cascading_from_count(1) == "none"

    def test_2_sectors(self):
        assert _derive_cascading_from_count(2) == "limited"

    def test_3_sectors(self):
        assert _derive_cascading_from_count(3) == "cross_sector"

    def test_5_sectors(self):
        assert _derive_cascading_from_count(5) == "uncontrolled"

    def test_10_sectors(self):
        assert _derive_cascading_from_count(10) == "uncontrolled"


class TestPropagateCascading:
    def test_energy_unavailable_propagates_to_health(self):
        sectors = {"energy"}
        impacts = {"energy": "unavailable"}
        all_sectors, cascading = propagate_cascading(sectors, impacts)
        assert "health" in all_sectors
        assert "transport" in all_sectors
        assert "drinking_water" in all_sectors
        assert len(all_sectors) > 1

    def test_energy_partial_no_propagation(self):
        """Partial impact doesn't cascade to dependents."""
        sectors = {"energy"}
        impacts = {"energy": "partial"}
        all_sectors, cascading = propagate_cascading(sectors, impacts)
        assert all_sectors == {"energy"}
        assert cascading == "none"

    def test_energy_sustained_propagates_indirect(self):
        sectors = {"energy"}
        impacts = {"energy": "sustained"}
        all_sectors, _ = propagate_cascading(sectors, impacts)
        # Direct + indirect
        assert "health" in all_sectors
        assert "banking" in all_sectors  # indirect

    def test_postal_no_fan_out(self):
        """Postal has no dependencies defined — no propagation."""
        sectors = {"postal"}
        impacts = {"postal": "unavailable"}
        all_sectors, cascading = propagate_cascading(sectors, impacts)
        assert all_sectors == {"postal"}
        assert cascading == "none"

    def test_energy_vs_postal_different_cascading(self):
        """Energy unavailable should cascade more than postal unavailable."""
        e_sectors, e_cascading = propagate_cascading(
            {"energy"}, {"energy": "unavailable"},
        )
        p_sectors, p_cascading = propagate_cascading(
            {"postal"}, {"postal": "unavailable"},
        )
        assert len(e_sectors) > len(p_sectors)

    def test_multiple_sectors_combine(self):
        sectors = {"energy", "digital_infrastructure"}
        impacts = {"energy": "unavailable", "digital_infrastructure": "unavailable"}
        all_sectors, cascading = propagate_cascading(sectors, impacts)
        assert cascading == "uncontrolled"  # very high fan-out from both


class TestDeriveCrossBorderPattern:
    def test_1_ms(self):
        assert _derive_cross_border_pattern(1) == "none"

    def test_2_ms(self):
        assert _derive_cross_border_pattern(2) == "limited"

    def test_3_ms(self):
        assert _derive_cross_border_pattern(3) == "significant"

    def test_6_ms(self):
        assert _derive_cross_border_pattern(6) == "systemic"


class TestDeriveCapacityExceeded:
    def test_large_multi_sector(self):
        assert _derive_capacity_exceeded(50, 3, 2, "none") is True

    def test_many_ms(self):
        assert _derive_capacity_exceeded(5, 1, 5, "none") is True

    def test_safety_with_entities(self):
        assert _derive_capacity_exceeded(10, 1, 1, "death") is True

    def test_small_incident(self):
        assert _derive_capacity_exceeded(3, 1, 1, "none") is False

    def test_safety_few_entities(self):
        assert _derive_capacity_exceeded(5, 1, 1, "health_damage") is False


# ---------------------------------------------------------------------------
# T-level derivation
# ---------------------------------------------------------------------------

class TestDeriveTLevel:
    def test_sustained_is_t4(self):
        t, basis = derive_t_level("sustained", "none", "none", 1)
        assert t == "T4"
        assert any("sustained" in b for b in basis)

    def test_systemic_data_is_t4(self):
        t, _ = derive_t_level("none", "systemic", "none", 1)
        assert t == "T4"

    def test_unavailable_uncontrolled_is_t4(self):
        t, _ = derive_t_level("unavailable", "none", "uncontrolled", 1)
        assert t == "T4"

    def test_unavailable_is_t3(self):
        t, _ = derive_t_level("unavailable", "none", "none", 1)
        assert t == "T3"

    def test_exfiltrated_is_t3(self):
        t, _ = derive_t_level("none", "exfiltrated", "none", 1)
        assert t == "T3"

    def test_cross_sector_is_t3(self):
        t, _ = derive_t_level("none", "none", "cross_sector", 1)
        assert t == "T3"

    def test_many_entities_is_t3(self):
        t, _ = derive_t_level("none", "none", "none", 55)
        assert t == "T3"

    def test_degraded_is_t2(self):
        t, _ = derive_t_level("degraded", "none", "none", 1)
        assert t == "T2"

    def test_accessed_is_t2(self):
        t, _ = derive_t_level("none", "accessed", "none", 1)
        assert t == "T2"

    def test_compromised_is_t2(self):
        t, _ = derive_t_level("none", "compromised", "none", 1)
        assert t == "T2"

    def test_limited_cascading_is_t2(self):
        t, _ = derive_t_level("none", "none", "limited", 1)
        assert t == "T2"

    def test_moderate_entities_is_t2(self):
        t, _ = derive_t_level("none", "none", "none", 15)
        assert t == "T2"

    def test_minimal_is_t1(self):
        t, basis = derive_t_level("none", "none", "none", 1)
        assert t == "T1"
        assert any("below" in b for b in basis)

    def test_partial_is_t1(self):
        t, _ = derive_t_level("partial", "none", "none", 5)
        assert t == "T1"


# ---------------------------------------------------------------------------
# Full aggregation
# ---------------------------------------------------------------------------

class TestDeriveOLevel:
    def test_systemic_cross_border_capacity_is_o4(self):
        o, _ = derive_o_level("systemic", True, "essential", 6, 3)
        assert o == "O4"

    def test_systemic_entity_6ms_is_o4(self):
        o, _ = derive_o_level("none", False, "systemic", 6, 1)
        assert o == "O4"

    def test_significant_cross_border_is_o3(self):
        o, _ = derive_o_level("significant", False, "essential", 3, 1)
        assert o == "O3"

    def test_capacity_exceeded_is_o3(self):
        o, _ = derive_o_level("none", True, "essential", 1, 1)
        assert o == "O3"

    def test_limited_cross_border_is_o2(self):
        o, _ = derive_o_level("limited", False, "essential", 2, 1)
        assert o == "O2"

    def test_3_sectors_is_o2(self):
        o, _ = derive_o_level("none", False, "non_essential", 1, 3)
        assert o == "O2"

    def test_minimal_is_o1(self):
        o, basis = derive_o_level("none", False, "non_essential", 1, 1)
        assert o == "O1"

    def test_consequence_escalation_safety(self):
        """death safety_impact should escalate O2 → O3."""
        o_base, _ = derive_o_level("limited", False, "essential", 2, 1)
        o_esc, _ = derive_o_level("limited", False, "essential", 2, 1, safety_impact="death")
        assert int(o_esc[1]) > int(o_base[1])

    def test_consequence_escalation_persons(self):
        """100k+ persons should escalate."""
        o_base, _ = derive_o_level("limited", False, "essential", 2, 1)
        o_esc, _ = derive_o_level("limited", False, "essential", 2, 1, affected_persons_count=100000)
        assert int(o_esc[1]) > int(o_base[1])

    def test_consequence_capped_at_plus1(self):
        """Multiple consequences should still only add +1."""
        o, _ = derive_o_level(
            "limited", False, "essential", 2, 1,
            safety_impact="death", affected_persons_count=200000,
            financial_impact="severe", affected_entities=20,
        )
        # limited → O2, +1 consequence → O3 (not O4)
        assert o == "O3"

    def test_o4_not_escalated_further(self):
        """O4 base should stay O4 even with consequences."""
        o, _ = derive_o_level("systemic", True, "systemic", 8, 5, safety_impact="death")
        assert o == "O4"

    def test_basis_lists_reasons(self):
        _, basis = derive_o_level("significant", True, "high_relevance", 4, 2, safety_impact="death")
        assert any("significant" in b for b in basis)
        assert any("death" in b for b in basis)


class TestAggregateEntityNotifications:
    def test_single_entity(self):
        notifications = [{
            "sector": "health",
            "ms_established": "DE",
            "service_impact": "unavailable",
            "data_impact": "exfiltrated",
            "financial_impact": "significant",
            "safety_impact": "health_damage",
            "affected_persons_count": 50000,
        }]
        result = aggregate_entity_notifications(notifications)
        assert result.affected_entities == 1
        assert result.service_impact == "unavailable"
        assert result.data_impact == "exfiltrated"
        assert result.sectors_affected == 1
        assert result.ms_affected == 1
        assert result.affected_persons_count == 50000
        assert result.t_level == "T3"  # unavailable

    def test_multi_entity_worst_case(self):
        notifications = [
            {"sector": "health", "ms_established": "DE", "service_impact": "degraded",
             "data_impact": "none", "financial_impact": "minor", "safety_impact": "none",
             "affected_persons_count": 1000},
            {"sector": "energy", "ms_established": "FR", "service_impact": "unavailable",
             "data_impact": "exfiltrated", "financial_impact": "severe", "safety_impact": "death",
             "affected_persons_count": 5000, "ms_affected": ["DE", "NL"]},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.service_impact == "unavailable"  # worst-case
        assert result.data_impact == "exfiltrated"
        assert result.financial_impact == "severe"
        assert result.safety_impact == "death"
        assert result.affected_persons_count == 6000  # sum
        assert result.affected_entities == 2
        # energy unavailable cascades to 8 downstream sectors + health + energy = many
        assert result.sectors_affected >= 5
        assert result.ms_affected == 3  # DE, FR, NL
        # Energy unavailable + uncontrolled cascading → T4
        assert result.t_level == "T4"

    def test_crisis_scenario_t4(self):
        """WannaCry-style: sustained disruption, systemic data, 5+ sectors."""
        notifications = [
            {"sector": "health", "ms_established": "DE", "service_impact": "sustained",
             "data_impact": "systemic", "financial_impact": "severe", "safety_impact": "death",
             "affected_persons_count": 100000, "ms_affected": ["FR", "NL", "BE", "IT", "ES"]},
            {"sector": "energy", "ms_established": "FR", "service_impact": "unavailable",
             "data_impact": "compromised", "financial_impact": "severe", "safety_impact": "none",
             "affected_persons_count": 50000},
            {"sector": "transport", "ms_established": "NL", "service_impact": "degraded",
             "data_impact": "accessed", "financial_impact": "significant", "safety_impact": "none",
             "affected_persons_count": 20000},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.t_level == "T4"  # sustained
        assert result.cascading == "uncontrolled"  # 3 reported + propagated dependents
        assert result.capacity_exceeded is True
        assert result.affected_persons_count == 170000

    def test_below_threshold_t1(self):
        notifications = [
            {"sector": "research", "ms_established": "DE",
             "service_impact": "partial", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none",
             "affected_persons_count": 0},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.t_level == "T1"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            aggregate_entity_notifications([])

    def test_ms_list_dedup(self):
        notifications = [
            {"sector": "health", "ms_established": "DE", "ms_affected": ["FR"],
             "service_impact": "none", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none"},
            {"sector": "energy", "ms_established": "DE", "ms_affected": ["FR", "NL"],
             "service_impact": "none", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none"},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.ms_affected == 3  # DE, FR, NL (deduped)
        assert sorted(result.ms_list) == ["DE", "FR", "NL"]

    def test_o_level_computed(self):
        notifications = [
            {"sector": "health", "ms_established": "DE", "ms_affected": ["FR", "NL", "BE"],
             "service_impact": "unavailable", "data_impact": "exfiltrated",
             "financial_impact": "severe", "safety_impact": "death",
             "affected_persons_count": 100000},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.o_level in ("O3", "O4")
        assert len(result.o_basis) > 0

    def test_to_dict_has_all_keys(self):
        notifications = [
            {"sector": "banking", "ms_established": "LU",
             "service_impact": "degraded", "data_impact": "accessed",
             "financial_impact": "significant", "safety_impact": "none",
             "affected_persons_count": 5000},
        ]
        result = aggregate_entity_notifications(notifications)
        d = result.to_dict()
        expected_keys = {
            "service_impact", "data_impact", "financial_impact", "safety_impact",
            "affected_persons_count", "affected_entities", "sectors_affected",
            "ms_affected", "cascading", "cross_border_pattern", "capacity_exceeded",
            "t_level", "t_basis", "o_level", "o_basis", "sector_list", "ms_list",
        }
        assert set(d.keys()) == expected_keys

    def test_missing_optional_fields_default_none(self):
        """Entities that don't report impact fields should default to 'none'/0."""
        notifications = [
            {"sector": "health", "ms_established": "DE"},
            {"sector": "energy", "ms_established": "FR"},
        ]
        result = aggregate_entity_notifications(notifications)
        assert result.service_impact == "none"
        assert result.data_impact == "none"
        assert result.affected_persons_count == 0
        # 2 sectors → limited cascading → T2
        assert result.t_level == "T2"
