"""Tests for HCPN crisis qualification MCP tool."""

from __future__ import annotations

import pytest

from cyberscale.tools.lu_crisis_assessment import (
    _assess_lu_crisis_incident,
    _assess_lu_crisis_threat,
)


class TestLuCrisisIncidentTool:
    def test_basic_national_crisis(self):
        result = _assess_lu_crisis_incident(
            description="Major cyberattack on Luxembourg energy grid",
            sectors_affected=["energy"],
            entity_types=["electricity_undertaking"],
            safety_impact="death",
            service_impact="unavailable",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result["qualifies"] is True
        assert result["qualification_level"] == "national_major_incident"
        assert result["cooperation_mode"] == "crise"

    def test_non_qualifying_incident(self):
        result = _assess_lu_crisis_incident(
            description="Minor incident at food processing plant",
            sectors_affected=["food"],
            entity_types=[],
            service_impact="partial",
            coordination_required=False,
            urgent_decisions_required=False,
        )
        assert result["qualifies"] is False
        assert result["cooperation_mode"] == "permanent"

    def test_empty_sectors(self):
        result = _assess_lu_crisis_incident(
            description="Incident with no sector info",
            sectors_affected=[],
            entity_types=[],
        )
        assert result["qualifies"] is False

    def test_large_scale_via_capacity(self):
        result = _assess_lu_crisis_incident(
            description="Massive attack exceeding LU response capacity",
            sectors_affected=["energy"],
            entity_types=[],
            safety_impact="death",
            service_impact="unavailable",
            capacity_exceeded=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result["qualifies"] is True
        assert result["qualification_level"] == "large_scale_cybersecurity_incident"


class TestLuCrisisThreatTool:
    def test_basic_national_threat(self):
        result = _assess_lu_crisis_threat(
            description="Imminent APT campaign targeting LU energy",
            sectors_affected=["energy"],
            entity_types=[],
            threat_probability="imminent",
            safety_impact="death",
            service_impact="unavailable",
            threat_actor_type="state_actor",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result["qualifies"] is True
        assert result["event_type"] == "threat"

    def test_low_probability_threat_does_not_qualify(self):
        result = _assess_lu_crisis_threat(
            description="Theoretical threat to banking sector",
            sectors_affected=["banking"],
            entity_types=[],
            threat_probability="low",
            safety_impact="death",
            service_impact="unavailable",
            coordination_required=True,
            urgent_decisions_required=True,
        )
        assert result["qualifies"] is False
