"""Tests for Phase 3 T-model (technical severity classifier)."""

from unittest.mock import MagicMock, patch

import pytest


VALID_DISRUPTIONS = {"partial", "significant", "complete", "sustained"}
VALID_CASCADING = {"none", "limited", "cross_sector", "uncontrolled"}
VALID_DATA_COMPROMISE = {"none", "operational", "sensitive", "systemic"}
T_LABEL_MAP = {0: "T1", 1: "T2", 2: "T3", 3: "T4"}


class TestInputFormatting:
    def test_format_all_fields(self):
        from cyberscale.models.technical import TechnicalClassifier

        text = TechnicalClassifier.format_input(
            description="Ransomware encrypted hospital systems",
            service_disruption="complete",
            affected_entities=50,
            sectors_affected=3,
            cascading="cross_sector",
            data_compromise="sensitive",
        )
        assert "Ransomware encrypted hospital systems" in text
        assert "disruption: complete" in text
        assert "entities: 50" in text
        assert "sectors: 3" in text
        assert "cascading: cross_sector" in text
        assert "data_compromise: sensitive" in text

    def test_format_defaults(self):
        from cyberscale.models.technical import TechnicalClassifier

        text = TechnicalClassifier.format_input(
            description="Minor port scan detected",
        )
        assert "disruption: partial" in text
        assert "entities: 1" in text
        assert "sectors: 1" in text
        assert "cascading: none" in text
        assert "data_compromise: none" in text


class TestTLabelMap:
    def test_label_map(self):
        from cyberscale.models.technical import T_LABEL_MAP

        assert T_LABEL_MAP == {0: "T1", 1: "T2", 2: "T3", 3: "T4"}


class TestValidValues:
    def test_valid_disruptions(self):
        from cyberscale.models.technical import VALID_DISRUPTIONS

        assert VALID_DISRUPTIONS == {"partial", "significant", "complete", "sustained"}

    def test_valid_cascading(self):
        from cyberscale.models.technical import VALID_CASCADING

        assert VALID_CASCADING == {"none", "limited", "cross_sector", "uncontrolled"}

    def test_valid_data_compromise(self):
        from cyberscale.models.technical import VALID_DATA_COMPROMISE

        assert VALID_DATA_COMPROMISE == {"none", "operational", "sensitive", "systemic"}


class TestTechnicalResult:
    def test_to_dict(self):
        from cyberscale.models.technical import TechnicalResult

        r = TechnicalResult(level="T3", confidence="high", key_factors=["complete disruption"])
        d = r.to_dict()
        assert d["level"] == "T3"
        assert d["confidence"] == "high"
        assert "complete disruption" in d["key_factors"]
