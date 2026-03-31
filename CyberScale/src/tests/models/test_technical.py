"""Tests for Phase 3 T-model (technical severity classifier)."""

from unittest.mock import MagicMock, patch

import pytest


VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_CASCADING = {"none", "limited", "cross_sector", "uncontrolled"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}
T_LABEL_MAP = {0: "T1", 1: "T2", 2: "T3", 3: "T4"}


class TestInputFormatting:
    def test_format_all_fields(self):
        from cyberscale.models.technical import TechnicalClassifier

        text = TechnicalClassifier.format_input(
            description="Ransomware encrypted hospital systems",
            service_impact="unavailable",
            affected_entities=50,
            sectors_affected=3,
            cascading="cross_sector",
            data_impact="exfiltrated",
        )
        assert "Ransomware encrypted hospital systems" in text
        assert "service_impact: unavailable" in text
        assert "entities: 50" in text
        assert "sectors: 3" in text
        assert "cascading: cross_sector" in text
        assert "data_impact: exfiltrated" in text

    def test_format_defaults(self):
        from cyberscale.models.technical import TechnicalClassifier

        text = TechnicalClassifier.format_input(
            description="Minor port scan detected",
        )
        assert "service_impact: partial" in text
        assert "entities: 1" in text
        assert "sectors: 1" in text
        assert "cascading: none" in text
        assert "data_impact: none" in text


class TestTLabelMap:
    def test_label_map(self):
        from cyberscale.models.technical import T_LABEL_MAP

        assert T_LABEL_MAP == {0: "T1", 1: "T2", 2: "T3", 3: "T4"}


class TestValidValues:
    def test_valid_service_impact(self):
        from cyberscale.models.technical import VALID_SERVICE_IMPACT

        assert VALID_SERVICE_IMPACT == {"none", "partial", "degraded", "unavailable", "sustained"}

    def test_valid_cascading(self):
        from cyberscale.models.technical import VALID_CASCADING

        assert VALID_CASCADING == {"none", "limited", "cross_sector", "uncontrolled"}

    def test_valid_data_impact(self):
        from cyberscale.models.technical import VALID_DATA_IMPACT

        assert VALID_DATA_IMPACT == {"none", "accessed", "exfiltrated", "compromised", "systemic"}


class TestTechnicalResult:
    def test_to_dict(self):
        from cyberscale.models.technical import TechnicalResult

        r = TechnicalResult(level="T3", confidence="high", key_factors=["unavailable service impact"])
        d = r.to_dict()
        assert d["level"] == "T3"
        assert d["confidence"] == "high"
        assert "unavailable service impact" in d["key_factors"]
