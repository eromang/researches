"""Tests for assess_incident authority-facing MCP tool.

v5: Fully deterministic — no ML models needed.
"""


class TestAssessIncident:
    def test_full_pipeline_deterministic(self):
        from cyberscale.tools.authority_incident import _assess_incident

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
            description="Cross-sector ransomware affecting health and energy",
            entity_notifications=notifications,
        )
        # Aggregation
        assert result["aggregation"]["service_impact"] == "unavailable"
        assert result["aggregation"]["affected_entities"] == 2
        assert result["aggregation"]["affected_persons_count"] == 55000
        # Both T and O are deterministic
        assert result["technical"]["source"] == "deterministic"
        assert result["operational"]["source"] == "deterministic"
        # T3: unavailable service impact
        assert result["technical"]["level"] == "T3"
        # Classification from matrix
        assert result["classification"] in ("significant", "large_scale", "cyber_crisis")
        assert result["entity_count"] == 2

    def test_crisis_scenario(self):
        from cyberscale.tools.authority_incident import _assess_incident

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
            description="Supply chain attack across critical infrastructure",
            entity_notifications=notifications,
        )
        assert result["technical"]["level"] == "T4"
        assert result["operational"]["level"] == "O4"
        assert result["classification"] == "cyber_crisis"

    def test_below_threshold(self):
        from cyberscale.tools.authority_incident import _assess_incident

        notifications = [
            {"sector": "research", "ms_established": "DE",
             "service_impact": "partial", "data_impact": "none",
             "financial_impact": "none", "safety_impact": "none",
             "affected_persons_count": 0},
        ]
        result = _assess_incident(
            description="Minor port scan at research lab",
            entity_notifications=notifications,
        )
        assert result["technical"]["level"] == "T1"
        assert result["operational"]["level"] == "O1"
        assert result["classification"] == "below_threshold"

    def test_no_ml_model_needed(self):
        """v5: authority_incident.py has no model loading."""
        from cyberscale.tools import authority_incident
        assert not hasattr(authority_incident, '_get_o_classifier')
        assert not hasattr(authority_incident, '_o_classifier')

    def test_output_structure_keys(self):
        from cyberscale.tools.authority_incident import _assess_incident

        notifications = [
            {"sector": "banking", "ms_established": "LU",
             "service_impact": "degraded", "data_impact": "accessed",
             "financial_impact": "significant", "safety_impact": "none",
             "affected_persons_count": 5000},
        ]
        result = _assess_incident("Banking incident", notifications)
        assert set(result.keys()) == {
            "aggregation", "technical", "operational",
            "classification", "label", "provision", "entity_count",
        }
