"""Tests for multi-entity incident aggregation layer.

All aggregation logic is deterministic — 100% pass rate required.
"""

import pytest

from cyberscale.aggregation import (
    aggregate_entity_notifications,
    derive_t_level,
    AggregationResult,
    _worst_case,
    _derive_cascading,
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
        assert _derive_cascading(1) == "none"

    def test_2_sectors(self):
        assert _derive_cascading(2) == "limited"

    def test_3_sectors(self):
        assert _derive_cascading(3) == "cross_sector"

    def test_5_sectors(self):
        assert _derive_cascading(5) == "uncontrolled"

    def test_10_sectors(self):
        assert _derive_cascading(10) == "uncontrolled"


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
        assert result.sectors_affected == 2
        assert result.ms_affected == 3  # DE, FR, NL
        assert result.t_level == "T3"  # unavailable

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
        assert result.cascading == "cross_sector"  # 3 sectors
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
            "t_level", "t_basis", "sector_list", "ms_list",
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
