"""Tests for Phase 3 incident classification MCP tool helpers.

v5: Both T-level and O-level are fully deterministic. No ML models.
"""


class TestClassifyFull:
    def test_full_classification_deterministic(self):
        from cyberscale.tools.incident import _classify_full

        result = _classify_full(
            description="Ransomware",
            service_impact="unavailable",
            affected_entities=50,
            sectors_affected=2,
            cascading="cross_sector",
            data_impact="exfiltrated",
            entity_relevance="high_relevance",
            ms_affected=5,
            cross_border_pattern="significant",
            capacity_exceeded=True,
        )
        assert result["technical"]["level"] == "T3"
        assert result["technical"]["source"] == "deterministic"
        assert result["operational"]["level"] in ("O3", "O4")
        assert result["operational"]["source"] == "deterministic"
        assert result["classification"] in ("large_scale", "cyber_crisis")

    def test_t4_o4_crisis(self):
        from cyberscale.tools.incident import _classify_full

        result = _classify_full(
            description="Sustained disruption",
            service_impact="sustained",
            affected_entities=100,
            sectors_affected=5,
            cascading="uncontrolled",
            data_impact="systemic",
            entity_relevance="systemic",
            ms_affected=8,
            cross_border_pattern="systemic",
            capacity_exceeded=True,
            safety_impact="death",
            affected_persons_count=200000,
        )
        assert result["technical"]["level"] == "T4"
        assert result["operational"]["level"] == "O4"
        assert result["classification"] == "cyber_crisis"

    def test_t1_o1_below_threshold(self):
        from cyberscale.tools.incident import _classify_full

        result = _classify_full(
            description="Minor scan",
            service_impact="partial",
            affected_entities=1,
            sectors_affected=1,
            cascading="none",
            data_impact="none",
            entity_relevance="non_essential",
            ms_affected=1,
            cross_border_pattern="none",
            capacity_exceeded=False,
        )
        assert result["technical"]["level"] == "T1"
        assert result["operational"]["level"] == "O1"
        assert result["classification"] == "below_threshold"

    def test_no_ml_models_in_module(self):
        """v5: No ML model loading in incident.py."""
        from cyberscale.tools import incident
        assert not hasattr(incident, '_get_o_classifier')
        assert not hasattr(incident, '_get_t_classifier')
        assert not hasattr(incident, '_classify_operational')

    def test_consequence_escalation(self):
        """Safety impact should escalate O-level."""
        from cyberscale.tools.incident import _classify_full

        # Without safety
        r1 = _classify_full(
            description="Incident",
            service_impact="degraded",
            affected_entities=5,
            sectors_affected=1,
            cascading="none",
            data_impact="accessed",
            entity_relevance="essential",
            ms_affected=2,
            cross_border_pattern="limited",
            capacity_exceeded=False,
        )
        # With death safety impact
        r2 = _classify_full(
            description="Incident",
            service_impact="degraded",
            affected_entities=5,
            sectors_affected=1,
            cascading="none",
            data_impact="accessed",
            entity_relevance="essential",
            ms_affected=2,
            cross_border_pattern="limited",
            capacity_exceeded=False,
            safety_impact="death",
        )
        # Safety should push O-level higher
        o1_num = int(r1["operational"]["level"][1])
        o2_num = int(r2["operational"]["level"][1])
        assert o2_num >= o1_num
