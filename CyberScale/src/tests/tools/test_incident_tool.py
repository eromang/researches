"""Tests for Phase 3 incident classification MCP tool helpers.

v4: T-level is deterministic (no T-model). classify_incident_technical removed.
"""

from unittest.mock import MagicMock

from cyberscale.models.operational import OperationalResult


class TestClassifyOperational:
    def test_model_prediction_returned(self):
        from cyberscale.tools.incident import _classify_operational

        mock_clf = MagicMock()
        mock_clf.predict.return_value = OperationalResult(
            level="O3", confidence="medium", key_factors=["5 MS affected"],
        )
        result = _classify_operational(
            mock_clf,
            description="Ransomware across hospital network",
            sectors_affected=2,
            entity_relevance="high_relevance",
            ms_affected=5,
            cross_border_pattern="significant",
            capacity_exceeded=True,
        )
        assert result["level"] == "O3"
        assert result["confidence"] == "medium"


class TestClassifyFull:
    def test_full_classification_deterministic_t(self):
        from cyberscale.tools.incident import _classify_full

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O3", confidence="medium", key_factors=["5 MS affected"],
        )
        result = _classify_full(
            mock_o,
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
        # T-level is now deterministic: unavailable → T3
        assert result["technical"]["level"] == "T3"
        assert result["technical"]["source"] == "deterministic"
        assert result["operational"]["level"] == "O3"
        assert result["classification"] == "large_scale"
        assert result["label"] == "Large-scale"
        assert result["provision"] == "7(c)"

    def test_t4_deterministic(self):
        from cyberscale.tools.incident import _classify_full

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O4", confidence="high", key_factors=[],
        )
        result = _classify_full(
            mock_o,
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
        )
        assert result["technical"]["level"] == "T4"
        assert result["classification"] == "cyber_crisis"

    def test_t1_deterministic(self):
        from cyberscale.tools.incident import _classify_full

        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O1", confidence="high", key_factors=[],
        )
        result = _classify_full(
            mock_o,
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
        assert result["classification"] == "below_threshold"

    def test_no_t_model_needed(self):
        """classify_incident_technical tool was removed in v4."""
        from cyberscale.tools.incident import register
        import inspect
        # The module should not have _get_t_classifier or _classify_technical
        from cyberscale.tools import incident
        assert not hasattr(incident, '_get_t_classifier')
        assert not hasattr(incident, '_classify_technical')
