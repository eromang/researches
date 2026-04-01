"""Tests for assess_incident authority-facing MCP tool."""

from unittest.mock import MagicMock

from cyberscale.models.operational import OperationalResult


class TestAssessIncident:
    def test_full_pipeline(self):
        from cyberscale.tools.authority_incident import _assess_incident

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O3", confidence="high",
            key_factors=["significant cross-border pattern", "3 sectors affected"],
        )
        notifications = [
            {"sector": "health", "ms_established": "DE", "ms_affected": ["FR"],
             "service_impact": "unavailable", "data_impact": "exfiltrated",
             "financial_impact": "significant", "safety_impact": "health_damage",
             "affected_persons_count": 50000},
            {"sector": "energy", "ms_established": "FR",
             "service_impact": "degraded", "data_impact": "accessed",
             "financial_impact": "minor", "safety_impact": "none",
             "affected_persons_count": 5000},
        ]
        result = _assess_incident(
            mock_o,
            description="Cross-sector ransomware affecting health and energy",
            entity_notifications=notifications,
        )
        # Aggregation checks
        assert result["aggregation"]["service_impact"] == "unavailable"
        assert result["aggregation"]["affected_entities"] == 2
        assert result["aggregation"]["affected_persons_count"] == 55000
        # T-level is deterministic
        assert result["technical"]["level"] == "T3"
        assert result["technical"]["source"] == "deterministic_aggregation"
        # O-level from mock
        assert result["operational"]["level"] == "O3"
        # Matrix: T3/O3 = large_scale
        assert result["classification"] == "large_scale"
        assert result["label"] == "Large-scale"
        assert result["provision"] == "7(c)"
        assert result["entity_count"] == 2

    def test_crisis_scenario(self):
        from cyberscale.tools.authority_incident import _assess_incident

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O4", confidence="high",
            key_factors=["systemic cross-border", "capacity exceeded"],
        )
        notifications = [
            {"sector": "health", "ms_established": "DE", "ms_affected": ["FR", "NL", "BE", "IT", "ES"],
             "service_impact": "sustained", "data_impact": "systemic",
             "financial_impact": "severe", "safety_impact": "death",
             "affected_persons_count": 100000},
            {"sector": "energy", "ms_established": "FR",
             "service_impact": "unavailable", "data_impact": "compromised",
             "financial_impact": "severe", "safety_impact": "none",
             "affected_persons_count": 50000},
            {"sector": "transport", "ms_established": "NL",
             "service_impact": "degraded", "data_impact": "none",
             "financial_impact": "significant", "safety_impact": "none",
             "affected_persons_count": 20000},
        ]
        result = _assess_incident(
            mock_o,
            description="Supply chain attack across critical infrastructure",
            entity_notifications=notifications,
        )
        assert result["technical"]["level"] == "T4"
        assert result["classification"] == "cyber_crisis"

    def test_below_threshold(self):
        from cyberscale.tools.authority_incident import _assess_incident

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O1", confidence="high",
            key_factors=[],
        )
        notifications = [
            {"sector": "research", "ms_established": "DE",
             "service_impact": "partial", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none",
             "affected_persons_count": 0},
        ]
        result = _assess_incident(
            mock_o,
            description="Minor port scan at research lab",
            entity_notifications=notifications,
        )
        assert result["technical"]["level"] == "T1"
        assert result["classification"] == "below_threshold"

    def test_output_structure_keys(self):
        from cyberscale.tools.authority_incident import _assess_incident

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O2", confidence="medium", key_factors=["2 sectors"],
        )
        notifications = [
            {"sector": "banking", "ms_established": "LU",
             "service_impact": "degraded", "data_impact": "accessed",
             "financial_impact": "significant", "safety_impact": "none",
             "affected_persons_count": 5000},
        ]
        result = _assess_incident(mock_o, "Banking incident", notifications)
        assert set(result.keys()) == {
            "aggregation", "technical", "operational",
            "classification", "label", "provision", "entity_count",
        }
