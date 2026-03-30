"""Tests for Phase 3 O-model (operational severity classifier)."""

from unittest.mock import MagicMock, patch

import pytest


VALID_ENTITY_RELEVANCE = {"non_essential", "essential", "high_relevance", "systemic"}
VALID_CROSS_BORDER = {"none", "limited", "significant", "systemic"}
VALID_COORDINATION = {"national", "eu_info", "eu_active", "full_ipcr"}
O_LABEL_MAP = {0: "O1", 1: "O2", 2: "O3", 3: "O4"}


class TestInputFormatting:
    def test_format_all_fields(self):
        from cyberscale.models.operational import OperationalClassifier

        text = OperationalClassifier.format_input(
            description="Ransomware disrupts 3 EU hospitals",
            sectors_affected="health,energy",
            entity_relevance="systemic",
            ms_affected=5,
            cross_border_pattern="significant",
            coordination_needs="eu_active",
            capacity_exceeded=True,
        )
        assert "Ransomware disrupts 3 EU hospitals" in text
        assert "sectors: health,energy" in text
        assert "relevance: systemic" in text
        assert "ms_affected: 5" in text
        assert "cross_border: significant" in text
        assert "coordination: eu_active" in text
        assert "capacity_exceeded: true" in text

    def test_format_defaults(self):
        from cyberscale.models.operational import OperationalClassifier

        text = OperationalClassifier.format_input(
            description="Minor phishing campaign",
        )
        assert "relevance: non_essential" in text
        assert "ms_affected: 1" in text
        assert "cross_border: none" in text
        assert "coordination: national" in text
        assert "capacity_exceeded: false" in text


class TestOLabelMap:
    def test_label_map(self):
        from cyberscale.models.operational import O_LABEL_MAP

        assert O_LABEL_MAP == {0: "O1", 1: "O2", 2: "O3", 3: "O4"}


class TestOperationalResult:
    def test_to_dict(self):
        from cyberscale.models.operational import OperationalResult

        r = OperationalResult(level="O3", confidence="medium", key_factors=["5 MS affected"])
        d = r.to_dict()
        assert d["level"] == "O3"
        assert d["confidence"] == "medium"
        assert "5 MS affected" in d["key_factors"]
