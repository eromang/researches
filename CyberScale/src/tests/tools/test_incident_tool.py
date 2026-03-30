"""Tests for Phase 3 incident classification MCP tool helpers."""

from unittest.mock import MagicMock

from cyberscale.models.technical import TechnicalResult
from cyberscale.models.operational import OperationalResult


class TestClassifyTechnical:
    def test_model_prediction_returned(self):
        from cyberscale.tools.incident import _classify_technical

        mock_clf = MagicMock()
        mock_clf.predict.return_value = TechnicalResult(
            level="T3", confidence="high", key_factors=["complete disruption"],
        )
        result = _classify_technical(
            mock_clf,
            description="Ransomware across hospital network",
            service_disruption="complete",
            affected_entities=50,
            sectors_affected=3,
            cascading="cross_sector",
            data_compromise="sensitive",
        )
        assert result["level"] == "T3"
        assert result["confidence"] == "high"


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
            sectors_affected="health,energy",
            entity_relevance="high_relevance",
            ms_affected=5,
            cross_border_pattern="significant",
            coordination_needs="eu_active",
            capacity_exceeded=True,
        )
        assert result["level"] == "O3"
        assert result["confidence"] == "medium"


class TestClassifyFull:
    def test_full_classification(self):
        from cyberscale.tools.incident import _classify_full

        mock_t = MagicMock()
        mock_t.predict.return_value = TechnicalResult(
            level="T3", confidence="high", key_factors=["complete disruption"],
        )
        mock_o = MagicMock()
        mock_o.predict.return_value = OperationalResult(
            level="O3", confidence="medium", key_factors=["5 MS affected"],
        )
        result = _classify_full(
            mock_t, mock_o,
            description="Ransomware",
            service_disruption="complete",
            affected_entities=50,
            sectors_affected="health,energy",
            cascading="cross_sector",
            data_compromise="sensitive",
            entity_relevance="high_relevance",
            ms_affected=5,
            cross_border_pattern="significant",
            coordination_needs="eu_active",
            capacity_exceeded=True,
        )
        assert result["technical"]["level"] == "T3"
        assert result["operational"]["level"] == "O3"
        assert result["classification"] == "large_scale"
        assert result["label"] == "Large-scale"
        assert result["provision"] == "7(c)"
