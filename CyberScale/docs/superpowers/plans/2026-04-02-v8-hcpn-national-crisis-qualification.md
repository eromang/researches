# v8 HCPN National Crisis Qualification — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the HCPN national crisis qualification layer (Cadre national de qualification v1.0) — a separate assessment ABOVE entity significance that determines whether an event triggers the PGGCCN national crisis plan and which cooperation mode applies (Alerte/CERC vs Crise).

**Architecture:** Three cumulative criteria (essential service affected + prejudice to vital interests + coordination urgency) evaluated deterministically where possible, with explicit `undetermined` signals for criteria that require sectoral authority judgment. The qualifier is a standalone authority-level tool scoped to **impact on Luxembourg** (not entity establishment) — an incident from an entity established in Ireland that affects Luxembourg banking is in scope. Uncertainty triggers escalation, not delay — matching the framework's explicit guidance.

**Tech Stack:** Python 3.11+, dataclasses, JSON reference data, pytest

---

## Design Decisions

### Scope trigger: impact on Luxembourg, not entity establishment

The HCPN framework protects Luxembourg's vital interests regardless of entity origin. The qualifier accepts `sectors_affected` and impact data describing the effect on Luxembourg, NOT `ms_established=LU`. This is fundamentally different from v7 entity significance (which correctly uses `ms_established=LU` for ILR thresholds).

### Standalone tool, not wired into Phase 3a

Phase 3a (`assess_national_incident`) scopes to entities established in a single MS. HCPN crisis qualification is a higher-level authority decision that may draw on Phase 3a output but also on intelligence, political context, and analyst judgment. The tools are separate; Phase 3a output can feed into the HCPN qualifier manually.

### Fast-track: Criterion 2 bypassed, not auto-met

The framework says "procéder immédiatement à l'évaluation des critères de coordination et d'urgence" — skip to Criterion 3. Criterion 2 is **bypassed**, not satisfied. An analyst reading the output should see `status="bypassed"`, and qualification requires only C1 + C3.

### No invented thresholds for delegated criteria

Several Criterion 2 sub-criteria delegate thresholds to sectoral authorities. The module returns `undetermined` for these — never guesses. `affected_persons_count > 0` → undetermined for the "users affected" sub-criterion. No arbitrary consultation floor.

### Multi-sector disruption uses sector dependency graph

The "major disruption of interdependent sectors" sub-criterion uses `sector_dependencies.json` (existing v5 reference data) to check actual interdependency, not a simple count.

### English-only keys

| Qualification | Key |
|---|---|
| National major incident | `national_major_incident` |
| Large-scale cybersecurity incident | `large_scale_cybersecurity_incident` |
| National major cyber threat | `national_major_cyber_threat` |
| Large-scale cyber threat | `large_scale_cyber_threat` |
| No qualification | `none` |

### Large-scale determination

`cross_border OR capacity_exceeded` → large-scale. Both fields already exist in the CyberScale taxonomy.

### New analyst judgment inputs

These are authority-level inputs not derivable from entity data:

| Field | Type | Source |
|---|---|---|
| `coordination_required` | `bool \| None` | Authority assessment |
| `urgent_decisions_required` | `bool \| None` | Authority assessment |
| `prejudice_actual` | `bool` | Authority assessment (actual vs potential) |
| `threat_actor_type` | `str \| None` | Intelligence (SRE, GOVCERT.LU, CIRCL) |
| `sensitive_data_type` | `str \| None` | Authority assessment |
| `capacity_exceeded` | `bool` | Authority assessment (existing taxonomy) |

---

## Conceptual Model

```
Entity-level assessment (v7, existing)
  │
  │  Impact data on Luxembourg (from any entity origin)
  │
  ▼
HCPN Crisis Qualifier (v8, new)
  │
  ├─ Criterion 1: Essential service affected? (CER reference list + extensible)
  │     Fast-track: malicious unauthorized access → skip to Criterion 3
  │
  ├─ Criterion 2: Prejudice to vital interests? (7 sub-criteria, at least 1)
  │     Some thresholds undefined → "undetermined" + recommend_consultation
  │
  ├─ Criterion 3: Coordination + decision urgency? (both must be true)
  │
  └─ All criteria satisfied → Qualification level + Cooperation mode
        ├─ cross_border OR capacity_exceeded → large_scale_cybersecurity_incident
        ├─ otherwise → national_major_incident
        ├─ actual prejudice → Crise
        └─ potential prejudice → Alerte/CERC
```

## File Structure

| File | Responsibility |
|------|---------------|
| `data/reference/hcpn_crisis_qualification.json` | CER essential services list, cooperation mode mapping, sub-criteria metadata |
| `src/cyberscale/national/lu_crisis.py` | HCPN crisis qualification logic — criteria evaluation, cooperation mode |
| `src/tests/national/test_lu_crisis.py` | Unit tests for all criteria, boundary cases, fast-track, undetermined paths |
| `src/cyberscale/tools/lu_crisis_assessment.py` | MCP tool wrapping the qualifier for national-scope use |
| `src/tests/tools/test_lu_crisis_tool.py` | MCP tool integration tests |
| `data/reference/curated_lu_crisis_scenarios.json` | 15 curated scenarios for benchmark |
| `evaluation/benchmark_lu_crisis.py` | Benchmark runner for curated scenarios |

Existing files modified:

| File | Change |
|------|--------|
| `docs/enhancement-roadmap.md` | Add v8 completed section |

---

## Tasks

### Task 1: HCPN reference data

**Files:**
- Create: `data/reference/hcpn_crisis_qualification.json`

- [ ] **Step 1: Create the reference data file**

```json
{
  "version": "1.0",
  "source": "Cadre national de qualification des incidents de cybersecurite et de cybermenaces nationales majeures (HCPN v1.0, 22.08.2025)",
  "legal_basis": "Article 2(2), Loi du 23 juillet 2016",

  "essential_services": {
    "description": "CER essential services (EU Delegated Regulation 2023/2450) — Criterion 1 reference list. Extensible by competent authorities, CERC, or CC.",
    "source": "EU Delegated Regulation (EU) 2023/2450",
    "sectors": [
      "energy",
      "transport",
      "banking",
      "financial_market_infrastructures",
      "health",
      "drinking_water",
      "waste_water",
      "digital_infrastructure",
      "public_administration",
      "space"
    ],
    "note": "Scope is extensible — competent authorities, CERC, or CC may extend to any service whose disruption would harm vital interests, national security, public order, economic stability, or country continuity."
  },

  "incident_levels": [
    {
      "level": "large_scale_cybersecurity_incident",
      "label": "Large-scale cybersecurity incident",
      "activates_plan": true,
      "description": "Disruptions exceeding Luxembourg's response capacity OR significant impact on at least one other Member State/third country"
    },
    {
      "level": "national_major_incident",
      "label": "National major incident",
      "activates_plan": true,
      "description": "Disruptions prejudicial to vital interests or essential needs of all or part of the country/population, requiring urgent decisions and coordination"
    },
    {
      "level": "important_incident",
      "label": "Important incident",
      "activates_plan": false,
      "description": "Serious operational disruption or financial losses for the entity; may affect other persons causing material/physical/moral damage"
    },
    {
      "level": "incident",
      "label": "Incident",
      "activates_plan": false,
      "description": "Compromise of CIA+A of data or services"
    }
  ],

  "threat_levels": [
    {
      "level": "large_scale_cyber_threat",
      "label": "Large-scale cyber threat",
      "activates_plan": true,
      "description": "Threat that could cause disruptions exceeding Luxembourg's response capacity OR significant potential impact on another Member State/third country"
    },
    {
      "level": "national_major_cyber_threat",
      "label": "National major cyber threat",
      "activates_plan": true,
      "description": "Threat that could cause disruptions prejudicial to vital interests or essential needs"
    },
    {
      "level": "important_cyber_threat",
      "label": "Important cyber threat",
      "activates_plan": false,
      "description": "Technical characteristics suggest grave potential impact"
    },
    {
      "level": "cyber_threat",
      "label": "Cyber threat",
      "activates_plan": false,
      "description": "Any potential circumstance/event/action capable of harming networks/information systems"
    }
  ],

  "threat_probability_levels": {
    "description": "Criterion 2 for threats — only High and Imminent qualify",
    "levels": [
      {"level": "low", "label": "Low", "qualifies": false, "description": "Theoretically possible, no active indicators"},
      {"level": "moderate", "label": "Moderate", "qualifies": false, "description": "Some probability, not imminent"},
      {"level": "high", "label": "High", "qualifies": true, "description": "Highly probable, could materialise short-term"},
      {"level": "imminent", "label": "Imminent", "qualifies": true, "description": "About to materialise, immediate response required"}
    ]
  },

  "criterion_2_sub_criteria": {
    "description": "Prejudice to vital interests — at least one must be satisfied",
    "sub_criteria": [
      {
        "id": "users_affected",
        "label": "Users affected",
        "description": "Affects substantial portion of national population or significant number of critical entities",
        "threshold_defined": false,
        "note": "Defined by sectoral authorities — no quantitative value in framework"
      },
      {
        "id": "geographic_spread",
        "label": "Geographic spread",
        "description": "Simultaneous effects across significant geographic area, or cross-border propagation potential",
        "threshold_defined": false,
        "note": "Not explicitly quantified in framework"
      },
      {
        "id": "service_interruption",
        "label": "Service interruption",
        "description": "Total interruption of essential service, OR severe degradation over significant duration",
        "threshold_defined": "partial",
        "note": "Total interruption is deterministic; 'significant duration' defined by sectoral authorities"
      },
      {
        "id": "human_impact",
        "label": "Human impact",
        "description": "At least one death, OR serious injuries/health harm to multiple individuals",
        "threshold_defined": true,
        "thresholds": {"death": 1, "serious_injuries_multiple": true}
      },
      {
        "id": "economic_consequences",
        "label": "Economic consequences",
        "description": "Direct financial losses exceeding critical threshold, OR major disruption of one/multiple interdependent sectors",
        "threshold_defined": "partial",
        "note": "Critical financial threshold defined by sectoral authorities; interdependent sector disruption evaluated via sector_dependencies.json"
      },
      {
        "id": "national_security",
        "label": "National security",
        "description": "Affects defence/intelligence/sensitive government systems, OR involves state actor/terrorist group/hybrid operation",
        "threshold_defined": true,
        "trigger_sectors": ["public_administration"],
        "trigger_actor_types": ["state_actor", "terrorist_group", "hybrid_operation"]
      },
      {
        "id": "sensitive_data_loss",
        "label": "Sensitive data loss",
        "description": "Exfiltration, destruction, or alteration of sensitive government data, industrial secrets, or critical strategic data",
        "threshold_defined": true,
        "trigger_data_types": ["government_data", "industrial_secrets", "critical_strategic_data"]
      }
    ]
  },

  "cooperation_modes": {
    "description": "Distinction rests on whether prejudice is actual (Crise) or potential (Alerte/CERC)",
    "modes": [
      {
        "mode": "crise",
        "label": "Crise",
        "condition": "Event causes prejudice to vital interests",
        "prejudice": "actual"
      },
      {
        "mode": "alerte_cerc",
        "label": "Alerte/CERC",
        "condition": "Event could cause prejudice to vital interests",
        "prejudice": "potential"
      },
      {
        "mode": "permanent",
        "label": "Permanent",
        "condition": "Default state — no crisis qualification",
        "prejudice": "none"
      }
    ]
  },

  "fast_track": {
    "description": "If the incident constitutes unauthorised access, suspected malicious, likely to cause grave operational disruptions — skip Criterion 2 entirely, proceed directly to Criterion 3 (coordination and urgency)",
    "conditions": ["suspected_malicious", "unauthorized_access", "grave_operational_disruption_likely"],
    "criterion_2_status": "bypassed"
  }
}
```

- [ ] **Step 2: Validate JSON**

Run: `python -c "import json; json.load(open('data/reference/hcpn_crisis_qualification.json'))"`
Expected: No output (valid JSON)

- [ ] **Step 3: Commit**

```bash
git add data/reference/hcpn_crisis_qualification.json
git commit -m "feat(cyberscale): v8 HCPN crisis qualification reference data"
```

---

### Task 2: Crisis qualification result types and Criterion 1

**Files:**
- Create: `src/cyberscale/national/lu_crisis.py`
- Create: `src/tests/national/test_lu_crisis.py`

- [ ] **Step 1: Write failing tests for result types and Criterion 1**

```python
"""Tests for Luxembourg HCPN national crisis qualification."""

from __future__ import annotations

import pytest

from cyberscale.national.lu_crisis import (
    CriterionResult,
    HcpnQualificationResult,
    evaluate_criterion_1,
)


class TestCriterionResult:
    def test_met(self):
        r = CriterionResult(status="met", details=["energy sector"])
        assert r.is_met is True
        assert r.is_undetermined is False
        assert r.is_bypassed is False

    def test_not_met(self):
        r = CriterionResult(status="not_met", details=[])
        assert r.is_met is False

    def test_undetermined(self):
        r = CriterionResult(status="undetermined", details=["threshold delegated"])
        assert r.is_undetermined is True
        assert r.is_met is False

    def test_bypassed(self):
        r = CriterionResult(status="bypassed", details=["fast-track"])
        assert r.is_bypassed is True
        assert r.is_met is False
        assert r.is_undetermined is False


class TestCriterion1EssentialService:
    """Criterion 1: The incident must affect at least one essential service."""

    def test_energy_sector_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["energy"],
            entity_types=[],
        )
        assert result.status == "met"
        assert "energy" in result.details[0]

    def test_transport_sector_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["transport"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_health_sector_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["health"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_non_essential_sector(self):
        """Annex II sectors (food, chemicals, etc.) are not essential by default."""
        result = evaluate_criterion_1(
            sectors_affected=["food"],
            entity_types=[],
        )
        assert result.status == "not_met"

    def test_multiple_sectors_one_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["food", "energy"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_empty_sectors(self):
        result = evaluate_criterion_1(
            sectors_affected=[],
            entity_types=[],
        )
        assert result.status == "not_met"

    def test_digital_infrastructure_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["digital_infrastructure"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_public_administration_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["public_administration"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_banking_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["banking"],
            entity_types=[],
        )
        assert result.status == "met"

    def test_space_is_essential(self):
        result = evaluate_criterion_1(
            sectors_affected=["space"],
            entity_types=[],
        )
        assert result.status == "met"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v 2>&1 | head -30`
Expected: FAIL — `ModuleNotFoundError: No module named 'cyberscale.national.lu_crisis'`

- [ ] **Step 3: Implement result types and Criterion 1**

```python
"""Luxembourg HCPN national crisis qualification.

Implements the Cadre national de qualification (HCPN v1.0, 22.08.2025).
Three cumulative criteria for incidents, four for threats.

Scoped to IMPACT ON LUXEMBOURG regardless of entity establishment.
An entity established in IE with impact on LU banking is in scope.

Several sub-criteria have undefined quantitative thresholds (delegated to
sectoral authorities). The module returns 'undetermined' for these — it
evaluates what it can, flags what it can't, and recommends consultation
when uncertain.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


_REF_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data" / "reference" / "hcpn_crisis_qualification.json"
)

_cached: dict | None = None


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_REF_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass
class CriterionResult:
    """Result of evaluating a single qualification criterion.

    status: "met" | "not_met" | "undetermined" | "bypassed"
    """
    status: str
    details: list[str] = field(default_factory=list)

    @property
    def is_met(self) -> bool:
        return self.status == "met"

    @property
    def is_undetermined(self) -> bool:
        return self.status == "undetermined"

    @property
    def is_bypassed(self) -> bool:
        return self.status == "bypassed"


@dataclass
class HcpnQualificationResult:
    """Full HCPN qualification result."""

    qualifies: bool
    qualification_level: str  # e.g., "national_major_incident" or "none"
    cooperation_mode: str  # "crise" | "alerte_cerc" | "permanent"
    criteria: dict[str, CriterionResult] = field(default_factory=dict)
    fast_tracked: bool = False
    recommend_consultation: bool = False
    consultation_reasons: list[str] = field(default_factory=list)
    event_type: str = "incident"  # "incident" | "threat"

    def to_dict(self) -> dict:
        return {
            "qualifies": self.qualifies,
            "qualification_level": self.qualification_level,
            "cooperation_mode": self.cooperation_mode,
            "criteria": {
                k: {"status": v.status, "details": v.details}
                for k, v in self.criteria.items()
            },
            "fast_tracked": self.fast_tracked,
            "recommend_consultation": self.recommend_consultation,
            "consultation_reasons": self.consultation_reasons,
            "event_type": self.event_type,
        }


# ---------------------------------------------------------------------------
# Criterion 1 — Essential service affected
# ---------------------------------------------------------------------------


def evaluate_criterion_1(
    sectors_affected: list[str],
    entity_types: list[str],
) -> CriterionResult:
    """Check if at least one essential service is affected.

    Reference list: CER essential services (EU Delegated Regulation 2023/2450).
    Scope is extensible by competent authorities.
    """
    data = _load()
    essential_sectors = set(data["essential_services"]["sectors"])

    matched = [s for s in sectors_affected if s in essential_sectors]
    if matched:
        return CriterionResult(
            status="met",
            details=[f"Essential service(s) affected: {', '.join(matched)}"],
        )

    return CriterionResult(
        status="not_met",
        details=[f"No essential service affected. Sectors: {sectors_affected}"],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/lu_crisis.py src/tests/national/test_lu_crisis.py
git commit -m "feat(cyberscale): v8 HCPN result types and Criterion 1 (essential service)"
```

---

### Task 3: Criterion 2 — Prejudice to vital interests

**Files:**
- Modify: `src/cyberscale/national/lu_crisis.py`
- Modify: `src/tests/national/test_lu_crisis.py`

- [ ] **Step 1: Write failing tests for Criterion 2**

Add to `test_lu_crisis.py`:

```python
from cyberscale.national.lu_crisis import evaluate_criterion_2


class TestCriterion2PrejudiceVitalInterests:
    """Criterion 2: At least one of seven sub-criteria must be satisfied."""

    # --- human_impact (fully deterministic) ---

    def test_death_triggers_human_impact(self):
        result = evaluate_criterion_2(
            safety_impact="death",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "met"
        assert any("death" in d.lower() or "human impact" in d.lower() for d in result.details)

    def test_health_damage_triggers_human_impact(self):
        result = evaluate_criterion_2(
            safety_impact="health_damage",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "met"

    def test_no_safety_impact_no_human_impact(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "not_met"

    # --- national_security (fully deterministic) ---

    def test_state_actor_triggers_national_security(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type="state_actor",
            sensitive_data_type=None,
        )
        assert result.status == "met"
        assert any("national security" in d.lower() for d in result.details)

    def test_terrorist_group_triggers_national_security(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type="terrorist_group",
            sensitive_data_type=None,
        )
        assert result.status == "met"

    def test_public_admin_sector_triggers_national_security(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=["public_administration"],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "met"

    # --- sensitive_data_loss (fully deterministic) ---

    def test_government_data_loss_triggers(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="exfiltrated",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type="government_data",
        )
        assert result.status == "met"
        assert any("sensitive data" in d.lower() for d in result.details)

    def test_industrial_secrets_loss_triggers(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="compromised",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type="industrial_secrets",
        )
        assert result.status == "met"

    def test_data_impact_without_sensitive_type_does_not_trigger(self):
        """Exfiltrated data alone is not enough — needs to be sensitive type."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="exfiltrated",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "not_met"

    # --- service_interruption (partially deterministic) ---

    def test_total_service_interruption_essential_sector_met(self):
        """Total interruption of essential service is deterministic."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            sectors_affected=["energy"],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "met"
        assert any("service interruption" in d.lower() for d in result.details)

    def test_total_service_interruption_non_essential_does_not_trigger(self):
        """Total interruption of non-essential service does not trigger."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            sectors_affected=["food"],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "not_met"

    def test_degraded_service_undetermined(self):
        """Severe degradation over 'significant duration' — threshold undefined."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="degraded",
            data_impact="none",
            financial_impact="none",
            sectors_affected=["energy"],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "undetermined"
        assert any("significant duration" in d.lower() for d in result.details)

    # --- geographic_spread (undetermined) ---

    def test_cross_border_undetermined(self):
        """Cross-border is an indicator but 'significant geographic area' is undefined."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=True,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "undetermined"
        assert any("geographic" in d.lower() for d in result.details)

    # --- users_affected (always undetermined when > 0) ---

    def test_any_affected_persons_undetermined(self):
        """'Substantial portion' of population is undefined — always undetermined when > 0."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=1,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "undetermined"
        assert any("users affected" in d.lower() for d in result.details)

    def test_zero_affected_persons_no_trigger(self):
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="none",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "not_met"

    # --- economic_consequences (partially deterministic) ---

    def test_severe_financial_impact_undetermined(self):
        """'Critical threshold' is undefined — flag for consultation."""
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="none",
            data_impact="none",
            financial_impact="severe",
            sectors_affected=[],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "undetermined"
        assert any("economic" in d.lower() for d in result.details)

    def test_interdependent_sector_disruption_met(self):
        """Disruption of interdependent sectors (via dependency graph) is deterministic."""
        # energy and transport are interdependent in sector_dependencies.json
        result = evaluate_criterion_2(
            safety_impact="none",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            sectors_affected=["energy", "transport"],
            affected_persons_count=0,
            cross_border=False,
            threat_actor_type=None,
            sensitive_data_type=None,
        )
        assert result.status == "met"
        assert any("interdependent" in d.lower() or "economic" in d.lower() for d in result.details)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py::TestCriterion2PrejudiceVitalInterests -v 2>&1 | head -30`
Expected: FAIL — `ImportError: cannot import name 'evaluate_criterion_2'`

- [ ] **Step 3: Implement Criterion 2**

Add to `src/cyberscale/national/lu_crisis.py`:

```python
# ---------------------------------------------------------------------------
# Criterion 2 — Prejudice to vital interests or essential needs
# ---------------------------------------------------------------------------


def _check_interdependent_sectors(
    sectors_affected: list[str],
    service_impact: str,
) -> bool:
    """Check if disrupted sectors are interdependent via sector_dependencies.json.

    Uses the existing propagate_cascading logic from the aggregation module
    to determine if affected sectors have dependency relationships.
    """
    from cyberscale.aggregation import _load_sector_dependencies

    if service_impact not in ("unavailable", "sustained"):
        return False

    deps = _load_sector_dependencies().get("dependencies", {})
    affected = set(sectors_affected)

    # Check if any affected sector has a dependency on another affected sector
    for sector in affected:
        sector_deps = deps.get(sector, {})
        direct = set(sector_deps.get("direct", []))
        if direct & affected:
            return True
    return False


def evaluate_criterion_2(
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    sectors_affected: list[str] | None = None,
    affected_persons_count: int = 0,
    cross_border: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
) -> CriterionResult:
    """Evaluate Criterion 2: prejudice to vital interests.

    At least one of seven sub-criteria must be satisfied.
    Returns "met" for deterministic sub-criteria, "undetermined" when
    thresholds are delegated to sectoral authorities.
    """
    sectors = sectors_affected or []
    data = _load()
    sub_criteria_ref = data["criterion_2_sub_criteria"]["sub_criteria"]
    essential_sectors = set(data["essential_services"]["sectors"])

    met_details: list[str] = []
    undetermined_details: list[str] = []

    # --- Sub-criterion: human_impact (fully deterministic) ---
    if safety_impact == "death":
        met_details.append("Human impact: at least one death")
    elif safety_impact == "health_damage":
        met_details.append("Human impact: serious injuries/health harm to multiple individuals")

    # --- Sub-criterion: national_security (fully deterministic) ---
    ns_ref = next(sc for sc in sub_criteria_ref if sc["id"] == "national_security")
    if threat_actor_type in ns_ref["trigger_actor_types"]:
        met_details.append(f"National security: threat actor type '{threat_actor_type}'")
    if any(s in ns_ref.get("trigger_sectors", []) for s in sectors):
        met_details.append("National security: affects defence/intelligence/sensitive government systems")

    # --- Sub-criterion: sensitive_data_loss (fully deterministic) ---
    sd_ref = next(sc for sc in sub_criteria_ref if sc["id"] == "sensitive_data_loss")
    if (
        data_impact in ("exfiltrated", "compromised", "systemic")
        and sensitive_data_type in sd_ref["trigger_data_types"]
    ):
        met_details.append(f"Sensitive data loss: {sensitive_data_type} — {data_impact}")

    # --- Sub-criterion: service_interruption (partially deterministic) ---
    essential_affected = [s for s in sectors if s in essential_sectors]
    if service_impact == "unavailable" and essential_affected:
        met_details.append(
            f"Service interruption: total interruption of essential service(s) {essential_affected}"
        )
    elif service_impact in ("degraded", "partial") and essential_affected:
        undetermined_details.append(
            "Service interruption: degraded essential service — 'significant duration' threshold defined by sectoral authorities"
        )

    # --- Sub-criterion: economic_consequences (partially deterministic) ---
    if _check_interdependent_sectors(sectors, service_impact):
        met_details.append(
            f"Economic consequences: major disruption of interdependent sectors {sectors}"
        )
    elif financial_impact in ("significant", "severe"):
        undetermined_details.append(
            "Economic consequences: significant/severe financial impact — 'critical threshold' defined by sectoral authorities"
        )

    # --- Sub-criterion: geographic_spread (undetermined) ---
    if cross_border:
        undetermined_details.append(
            "Geographic spread: cross-border propagation potential — 'significant geographic area' not explicitly quantified"
        )

    # --- Sub-criterion: users_affected (always undetermined when > 0) ---
    if affected_persons_count > 0:
        undetermined_details.append(
            f"Users affected: {affected_persons_count:,} persons — 'substantial portion' of population defined by sectoral authorities"
        )

    # Determine overall status
    if met_details:
        return CriterionResult(status="met", details=met_details)
    if undetermined_details:
        return CriterionResult(status="undetermined", details=undetermined_details)
    return CriterionResult(status="not_met", details=[
        "No Criterion 2 sub-criteria met or indicated"
    ])
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v`
Expected: All tests PASS (Task 2 + Task 3)

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/lu_crisis.py src/tests/national/test_lu_crisis.py
git commit -m "feat(cyberscale): v8 HCPN Criterion 2 (prejudice to vital interests)"
```

---

### Task 4: Criterion 3 — Coordination and decision urgency

**Files:**
- Modify: `src/cyberscale/national/lu_crisis.py`
- Modify: `src/tests/national/test_lu_crisis.py`

- [ ] **Step 1: Write failing tests for Criterion 3**

Add to `test_lu_crisis.py`:

```python
from cyberscale.national.lu_crisis import evaluate_criterion_3


class TestCriterion3CoordinationUrgency:
    """Criterion 3: Both coordination AND urgency must be true."""

    def test_both_true_met(self):
        result = evaluate_criterion_3(
            coordination_required=True,
            urgent_decisions_required=True,
        )
        assert result.status == "met"

    def test_coordination_only_not_met(self):
        result = evaluate_criterion_3(
            coordination_required=True,
            urgent_decisions_required=False,
        )
        assert result.status == "not_met"

    def test_urgency_only_not_met(self):
        result = evaluate_criterion_3(
            coordination_required=False,
            urgent_decisions_required=True,
        )
        assert result.status == "not_met"

    def test_neither_not_met(self):
        result = evaluate_criterion_3(
            coordination_required=False,
            urgent_decisions_required=False,
        )
        assert result.status == "not_met"

    def test_coordination_uncertain_undetermined(self):
        """Uncertainty triggers escalation per framework guidance."""
        result = evaluate_criterion_3(
            coordination_required=None,
            urgent_decisions_required=True,
        )
        assert result.status == "undetermined"

    def test_urgency_uncertain_undetermined(self):
        result = evaluate_criterion_3(
            coordination_required=True,
            urgent_decisions_required=None,
        )
        assert result.status == "undetermined"

    def test_both_uncertain_undetermined(self):
        result = evaluate_criterion_3(
            coordination_required=None,
            urgent_decisions_required=None,
        )
        assert result.status == "undetermined"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py::TestCriterion3CoordinationUrgency -v 2>&1 | head -20`
Expected: FAIL — `ImportError: cannot import name 'evaluate_criterion_3'`

- [ ] **Step 3: Implement Criterion 3**

Add to `src/cyberscale/national/lu_crisis.py`:

```python
# ---------------------------------------------------------------------------
# Criterion 3 — Coordination and decision urgency
# ---------------------------------------------------------------------------


def evaluate_criterion_3(
    coordination_required: bool | None,
    urgent_decisions_required: bool | None,
) -> CriterionResult:
    """Evaluate Criterion 3: both coordination AND urgency must be true.

    None values represent uncertainty. Per framework guidance:
    "If answers are affirmative or uncertain, rapid consultation should be
    initiated." Uncertainty -> undetermined (not not_met).
    """
    coord_uncertain = coordination_required is None
    urgent_uncertain = urgent_decisions_required is None

    if coord_uncertain or urgent_uncertain:
        reasons = []
        if coord_uncertain:
            reasons.append("coordination requirement uncertain")
        if urgent_uncertain:
            reasons.append("decision urgency uncertain")
        return CriterionResult(
            status="undetermined",
            details=[
                f"Criterion 3: {', '.join(reasons)} — "
                "framework guidance: uncertainty triggers consultation"
            ],
        )

    if coordination_required and urgent_decisions_required:
        return CriterionResult(
            status="met",
            details=["Coordination required AND urgent decisions required"],
        )

    reasons = []
    if not coordination_required:
        reasons.append("interministerial coordination not required")
    if not urgent_decisions_required:
        reasons.append("no immediate executive decisions needed")
    return CriterionResult(
        status="not_met",
        details=[f"Criterion 3 not met: {', '.join(reasons)}"],
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/lu_crisis.py src/tests/national/test_lu_crisis.py
git commit -m "feat(cyberscale): v8 HCPN Criterion 3 (coordination and urgency)"
```

---

### Task 5: Main qualification function (incidents)

**Files:**
- Modify: `src/cyberscale/national/lu_crisis.py`
- Modify: `src/tests/national/test_lu_crisis.py`

- [ ] **Step 1: Write failing tests for incident qualification**

Add to `test_lu_crisis.py`:

```python
from cyberscale.national.lu_crisis import qualify_hcpn_incident


class TestQualifyHcpnIncident:
    """Full incident qualification: all 3 criteria must be met (or C2 bypassed via fast-track)."""

    def test_all_criteria_met_national_crisis(self):
        """Clear national major incident — all criteria deterministically met."""
        result = qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=["electricity_undertaking"],
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "national_major_incident"
        assert result.cooperation_mode == "crise"
        assert result.criteria["criterion_1"].status == "met"
        assert result.criteria["criterion_2"].status == "met"
        assert result.criteria["criterion_3"].status == "met"

    def test_all_criteria_met_potential_prejudice_alerte(self):
        """Prejudice is potential, not actual -> Alerte/CERC mode."""
        result = qualify_hcpn_incident(
            sectors_affected=["health"],
            entity_types=[],
            safety_impact="health_damage",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        )
        assert result.qualifies is True
        assert result.cooperation_mode == "alerte_cerc"

    def test_cross_border_qualifies_large_scale(self):
        """Cross-border + all criteria -> large-scale cybersecurity incident."""
        result = qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=[],
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=True,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cybersecurity_incident"
        assert result.cooperation_mode == "crise"

    def test_capacity_exceeded_qualifies_large_scale(self):
        """Capacity exceeded + all criteria -> large-scale cybersecurity incident."""
        result = qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=[],
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=True,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cybersecurity_incident"

    def test_criterion_1_not_met_does_not_qualify(self):
        """Non-essential sector -> criterion 1 fails -> no qualification."""
        result = qualify_hcpn_incident(
            sectors_affected=["food"],
            entity_types=[],
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is False
        assert result.qualification_level == "none"
        assert result.cooperation_mode == "permanent"

    def test_criterion_3_not_met_does_not_qualify(self):
        result = qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=[],
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=False,
            urgent_decisions_required=False,
            prejudice_actual=True,
        )
        assert result.qualifies is False

    def test_undetermined_criterion_recommends_consultation(self):
        """Any undetermined criterion -> recommend_consultation=True."""
        result = qualify_hcpn_incident(
            sectors_affected=["energy"],
            entity_types=[],
            safety_impact="none",
            service_impact="degraded",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=False,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        )
        # Criterion 2 is undetermined (degraded service, duration undefined)
        assert result.recommend_consultation is True
        assert len(result.consultation_reasons) > 0

    def test_fast_track_bypasses_criterion_2(self):
        """Malicious unauthorized access with grave disruption -> fast-track bypasses Criterion 2."""
        result = qualify_hcpn_incident(
            sectors_affected=["digital_infrastructure"],
            entity_types=[],
            safety_impact="none",
            service_impact="unavailable",
            data_impact="accessed",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            suspected_malicious=True,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.fast_tracked is True
        assert result.qualifies is True
        assert result.criteria["criterion_2"].status == "bypassed"
        assert any("fast-track" in d.lower() for d in result.criteria["criterion_2"].details)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py::TestQualifyHcpnIncident -v 2>&1 | head -20`
Expected: FAIL — `ImportError: cannot import name 'qualify_hcpn_incident'`

- [ ] **Step 3: Implement the main qualification function**

Add to `src/cyberscale/national/lu_crisis.py`:

```python
# ---------------------------------------------------------------------------
# Fast-track check
# ---------------------------------------------------------------------------


def _check_fast_track(
    suspected_malicious: bool,
    data_impact: str,
    service_impact: str,
) -> bool:
    """Check if fast-track provision applies.

    Fast-track: unauthorised access, suspected malicious, likely to cause
    grave operational disruptions -> skip Criterion 2, go directly to Criterion 3.
    """
    return (
        suspected_malicious
        and data_impact in ("accessed", "exfiltrated", "compromised", "systemic")
        and service_impact in ("unavailable", "sustained")
    )


# ---------------------------------------------------------------------------
# Main incident qualification
# ---------------------------------------------------------------------------


def qualify_hcpn_incident(
    sectors_affected: list[str],
    entity_types: list[str],
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    suspected_malicious: bool = False,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> HcpnQualificationResult:
    """Qualify an incident against HCPN crisis criteria.

    Three cumulative criteria must be met:
    1. Essential service affected
    2. Prejudice to vital interests (at least one sub-criterion) — bypassed on fast-track
    3. Coordination and decision urgency (both conditions)

    Fast-track: malicious unauthorized access with grave disruption
    bypasses Criterion 2 and goes directly to Criterion 3.

    prejudice_actual: True if prejudice has already occurred (-> Crise),
    False if prejudice is potential (-> Alerte/CERC).
    """
    criteria: dict[str, CriterionResult] = {}
    consultation_reasons: list[str] = []

    # Criterion 1
    c1 = evaluate_criterion_1(sectors_affected, entity_types)
    criteria["criterion_1"] = c1

    # Fast-track check
    fast_tracked = False
    if c1.is_met and _check_fast_track(suspected_malicious, data_impact, service_impact):
        fast_tracked = True
        criteria["criterion_2"] = CriterionResult(
            status="bypassed",
            details=["Fast-track: malicious unauthorized access with grave operational disruption — Criterion 2 bypassed per framework provision, proceeding directly to Criterion 3"],
        )
    else:
        # Criterion 2
        c2 = evaluate_criterion_2(
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            sectors_affected=sectors_affected,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
        )
        criteria["criterion_2"] = c2

    # Criterion 3
    c3 = evaluate_criterion_3(coordination_required, urgent_decisions_required)
    criteria["criterion_3"] = c3

    # Collect undetermined criteria for consultation recommendation
    for name, cr in criteria.items():
        if cr.is_undetermined:
            consultation_reasons.extend(
                f"{name}: {d}" for d in cr.details
            )

    # Determine qualification: all criteria must be met or bypassed
    all_satisfied = all(
        cr.is_met or cr.is_bypassed for cr in criteria.values()
    )
    any_undetermined = any(cr.is_undetermined for cr in criteria.values())

    if all_satisfied:
        if cross_border or capacity_exceeded:
            level = "large_scale_cybersecurity_incident"
        else:
            level = "national_major_incident"
        mode = "crise" if prejudice_actual else "alerte_cerc"
    else:
        level = "none"
        mode = "permanent"

    return HcpnQualificationResult(
        qualifies=all_satisfied,
        qualification_level=level,
        cooperation_mode=mode,
        criteria=criteria,
        fast_tracked=fast_tracked,
        recommend_consultation=any_undetermined,
        consultation_reasons=consultation_reasons,
        event_type="incident",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/lu_crisis.py src/tests/national/test_lu_crisis.py
git commit -m "feat(cyberscale): v8 HCPN incident qualification (3 criteria + fast-track + large-scale)"
```

---

### Task 6: Cyber threat qualification (4 criteria)

**Files:**
- Modify: `src/cyberscale/national/lu_crisis.py`
- Modify: `src/tests/national/test_lu_crisis.py`

- [ ] **Step 1: Write failing tests for threat qualification**

Add to `test_lu_crisis.py`:

```python
from cyberscale.national.lu_crisis import evaluate_threat_probability, qualify_hcpn_threat


class TestThreatProbability:
    """Criterion 2 (threats): Only High and Imminent qualify."""

    def test_high_qualifies(self):
        result = evaluate_threat_probability("high")
        assert result.status == "met"

    def test_imminent_qualifies(self):
        result = evaluate_threat_probability("imminent")
        assert result.status == "met"

    def test_moderate_does_not_qualify(self):
        result = evaluate_threat_probability("moderate")
        assert result.status == "not_met"

    def test_low_does_not_qualify(self):
        result = evaluate_threat_probability("low")
        assert result.status == "not_met"

    def test_unknown_does_not_qualify(self):
        result = evaluate_threat_probability("unknown")
        assert result.status == "not_met"


class TestQualifyHcpnThreat:
    """Full threat qualification: all 4 criteria must be met."""

    def test_all_criteria_met_national_threat(self):
        result = qualify_hcpn_threat(
            sectors_affected=["energy"],
            entity_types=[],
            threat_probability="high",
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type="state_actor",
            sensitive_data_type=None,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        )
        assert result.qualifies is True
        assert result.qualification_level == "national_major_cyber_threat"
        assert result.cooperation_mode == "alerte_cerc"
        assert result.event_type == "threat"

    def test_low_probability_does_not_qualify(self):
        """Probability too low -> criterion 2 (probability) fails."""
        result = qualify_hcpn_threat(
            sectors_affected=["energy"],
            entity_types=[],
            threat_probability="low",
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        )
        assert result.qualifies is False

    def test_cross_border_threat_large_scale(self):
        result = qualify_hcpn_threat(
            sectors_affected=["digital_infrastructure"],
            entity_types=[],
            threat_probability="imminent",
            safety_impact="none",
            service_impact="unavailable",
            data_impact="compromised",
            financial_impact="severe",
            affected_persons_count=0,
            cross_border=True,
            capacity_exceeded=False,
            threat_actor_type="state_actor",
            sensitive_data_type="government_data",
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cyber_threat"
        assert result.cooperation_mode == "crise"

    def test_capacity_exceeded_threat_large_scale(self):
        result = qualify_hcpn_threat(
            sectors_affected=["energy"],
            entity_types=[],
            threat_probability="imminent",
            safety_impact="death",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="none",
            affected_persons_count=0,
            cross_border=False,
            capacity_exceeded=True,
            threat_actor_type="state_actor",
            sensitive_data_type=None,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=True,
        )
        assert result.qualifies is True
        assert result.qualification_level == "large_scale_cyber_threat"

    def test_moderate_probability_does_not_qualify(self):
        result = qualify_hcpn_threat(
            sectors_affected=["health"],
            entity_types=[],
            threat_probability="moderate",
            safety_impact="health_damage",
            service_impact="unavailable",
            data_impact="none",
            financial_impact="significant",
            affected_persons_count=10000,
            cross_border=False,
            capacity_exceeded=False,
            threat_actor_type=None,
            sensitive_data_type=None,
            coordination_required=True,
            urgent_decisions_required=True,
            prejudice_actual=False,
        )
        assert result.qualifies is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py::TestThreatProbability -v 2>&1 | head -10`
Expected: FAIL — `ImportError`

- [ ] **Step 3: Implement threat probability and qualification**

Add to `src/cyberscale/national/lu_crisis.py`:

```python
# ---------------------------------------------------------------------------
# Threat probability assessment (Criterion 2 for threats)
# ---------------------------------------------------------------------------


def evaluate_threat_probability(probability: str) -> CriterionResult:
    """Evaluate threat probability — only High and Imminent qualify."""
    data = _load()
    levels = data["threat_probability_levels"]["levels"]
    level_map = {lv["level"]: lv for lv in levels}

    if probability not in level_map:
        return CriterionResult(
            status="not_met",
            details=[f"Unknown probability level: {probability}"],
        )

    lv = level_map[probability]
    if lv["qualifies"]:
        return CriterionResult(
            status="met",
            details=[f"Threat probability: {lv['label']} ({probability}) — qualifies"],
        )
    return CriterionResult(
        status="not_met",
        details=[f"Threat probability: {lv['label']} ({probability}) — does not qualify (only High/Imminent qualify)"],
    )


# ---------------------------------------------------------------------------
# Main threat qualification
# ---------------------------------------------------------------------------


def qualify_hcpn_threat(
    sectors_affected: list[str],
    entity_types: list[str],
    threat_probability: str,
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> HcpnQualificationResult:
    """Qualify a cyber threat against HCPN crisis criteria.

    Four cumulative criteria (same three as incidents + probability):
    1. Essential service targeted
    2. Probability of materialisation (High or Imminent)
    3. Potential prejudice to vital interests (same 7 sub-criteria)
    4. Coordination and decision urgency
    """
    criteria: dict[str, CriterionResult] = {}
    consultation_reasons: list[str] = []

    # Criterion 1: Essential service targeted
    c1 = evaluate_criterion_1(sectors_affected, entity_types)
    criteria["criterion_1"] = c1

    # Criterion 2 (threat-specific): Probability
    c2_prob = evaluate_threat_probability(threat_probability)
    criteria["criterion_2_probability"] = c2_prob

    # Criterion 3: Potential prejudice to vital interests
    c3 = evaluate_criterion_2(
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        sectors_affected=sectors_affected,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
    )
    criteria["criterion_3_prejudice"] = c3

    # Criterion 4: Coordination and decision urgency
    c4 = evaluate_criterion_3(coordination_required, urgent_decisions_required)
    criteria["criterion_4_urgency"] = c4

    # Collect undetermined
    for name, cr in criteria.items():
        if cr.is_undetermined:
            consultation_reasons.extend(f"{name}: {d}" for d in cr.details)

    all_met = all(cr.is_met for cr in criteria.values())
    any_undetermined = any(cr.is_undetermined for cr in criteria.values())

    if all_met:
        if cross_border or capacity_exceeded:
            level = "large_scale_cyber_threat"
        else:
            level = "national_major_cyber_threat"
        mode = "crise" if prejudice_actual else "alerte_cerc"
    else:
        level = "none"
        mode = "permanent"

    return HcpnQualificationResult(
        qualifies=all_met,
        qualification_level=level,
        cooperation_mode=mode,
        criteria=criteria,
        fast_tracked=False,
        recommend_consultation=any_undetermined,
        consultation_reasons=consultation_reasons,
        event_type="threat",
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_lu_crisis.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/lu_crisis.py src/tests/national/test_lu_crisis.py
git commit -m "feat(cyberscale): v8 HCPN cyber threat qualification (4 cumulative criteria)"
```

---

### Task 7: MCP tool

**Files:**
- Create: `src/cyberscale/tools/lu_crisis_assessment.py`
- Create: `src/tests/tools/test_lu_crisis_tool.py`

- [ ] **Step 1: Write failing tests for MCP tool**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/tools/test_lu_crisis_tool.py -v 2>&1 | head -10`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement MCP tool**

```python
"""HCPN national crisis qualification MCP tools.

Provides two tools:
- assess_lu_crisis_incident: Qualify incident against HCPN criteria
- assess_lu_crisis_threat: Qualify cyber threat against HCPN criteria

These are authority-level tools scoped to IMPACT ON LUXEMBOURG regardless
of entity establishment. They operate ABOVE entity significance — an event
may meet NIS2 notification thresholds without qualifying for the national
crisis plan, and vice versa.
"""

from __future__ import annotations

from fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Internal helpers (testable without MCP)
# ---------------------------------------------------------------------------


def _assess_lu_crisis_incident(
    description: str,
    sectors_affected: list[str],
    entity_types: list[str],
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    suspected_malicious: bool = False,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> dict:
    """Assess incident against HCPN national crisis qualification criteria."""
    from cyberscale.national.lu_crisis import qualify_hcpn_incident

    result = qualify_hcpn_incident(
        sectors_affected=sectors_affected,
        entity_types=entity_types,
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        capacity_exceeded=capacity_exceeded,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
        suspected_malicious=suspected_malicious,
        coordination_required=coordination_required,
        urgent_decisions_required=urgent_decisions_required,
        prejudice_actual=prejudice_actual,
    )
    return result.to_dict()


def _assess_lu_crisis_threat(
    description: str,
    sectors_affected: list[str],
    entity_types: list[str],
    threat_probability: str,
    safety_impact: str = "none",
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    affected_persons_count: int = 0,
    cross_border: bool = False,
    capacity_exceeded: bool = False,
    threat_actor_type: str | None = None,
    sensitive_data_type: str | None = None,
    coordination_required: bool | None = None,
    urgent_decisions_required: bool | None = None,
    prejudice_actual: bool = False,
) -> dict:
    """Assess cyber threat against HCPN national crisis qualification criteria."""
    from cyberscale.national.lu_crisis import qualify_hcpn_threat

    result = qualify_hcpn_threat(
        sectors_affected=sectors_affected,
        entity_types=entity_types,
        threat_probability=threat_probability,
        safety_impact=safety_impact,
        service_impact=service_impact,
        data_impact=data_impact,
        financial_impact=financial_impact,
        affected_persons_count=affected_persons_count,
        cross_border=cross_border,
        capacity_exceeded=capacity_exceeded,
        threat_actor_type=threat_actor_type,
        sensitive_data_type=sensitive_data_type,
        coordination_required=coordination_required,
        urgent_decisions_required=urgent_decisions_required,
        prejudice_actual=prejudice_actual,
    )
    return result.to_dict()


# ---------------------------------------------------------------------------
# MCP tool registration
# ---------------------------------------------------------------------------


def register(mcp: FastMCP) -> None:

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_lu_crisis_incident(
        description: str,
        sectors_affected: list[str],
        entity_types: list[str],
        safety_impact: str = "none",
        service_impact: str = "none",
        data_impact: str = "none",
        financial_impact: str = "none",
        affected_persons_count: int = 0,
        cross_border: bool = False,
        capacity_exceeded: bool = False,
        threat_actor_type: str | None = None,
        sensitive_data_type: str | None = None,
        suspected_malicious: bool = False,
        coordination_required: bool | None = None,
        urgent_decisions_required: bool | None = None,
        prejudice_actual: bool = False,
    ) -> dict:
        """HCPN national crisis qualification for incidents (Luxembourg).

        Determines whether a cyber incident triggers the PGGCCN national
        crisis plan and which cooperation mode applies.

        Scoped to IMPACT ON LUXEMBOURG — the entity causing the incident
        may be established in any Member State.

        Three cumulative criteria must be met:
        1. At least one essential service affected (CER reference list)
        2. Prejudice to vital interests (7 sub-criteria, at least 1)
        3. Coordination AND decision urgency (both required)

        Fast-track: malicious unauthorized access with grave operational
        disruption bypasses Criterion 2.

        Some sub-criteria have thresholds delegated to sectoral authorities.
        When these are triggered but cannot be evaluated deterministically,
        recommend_consultation=true with specific reasons.

        Qualification level:
        - cross_border OR capacity_exceeded -> large_scale_cybersecurity_incident
        - otherwise -> national_major_incident

        Cooperation mode:
        - prejudice_actual=true -> Crise
        - prejudice_actual=false -> Alerte/CERC

        This is an authority-level tool operating ABOVE entity significance.
        """
        return _assess_lu_crisis_incident(
            description=description,
            sectors_affected=sectors_affected,
            entity_types=entity_types,
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            capacity_exceeded=capacity_exceeded,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
            suspected_malicious=suspected_malicious,
            coordination_required=coordination_required,
            urgent_decisions_required=urgent_decisions_required,
            prejudice_actual=prejudice_actual,
        )

    @mcp.tool(annotations={"readOnlyHint": True})
    def assess_lu_crisis_threat(
        description: str,
        sectors_affected: list[str],
        entity_types: list[str],
        threat_probability: str,
        safety_impact: str = "none",
        service_impact: str = "none",
        data_impact: str = "none",
        financial_impact: str = "none",
        affected_persons_count: int = 0,
        cross_border: bool = False,
        capacity_exceeded: bool = False,
        threat_actor_type: str | None = None,
        sensitive_data_type: str | None = None,
        coordination_required: bool | None = None,
        urgent_decisions_required: bool | None = None,
        prejudice_actual: bool = False,
    ) -> dict:
        """HCPN national crisis qualification for cyber threats (Luxembourg).

        Same as assess_lu_crisis_incident but with an additional mandatory
        probability criterion. Only High and Imminent probability qualify.

        Four cumulative criteria:
        1. Essential service targeted
        2. Probability of materialisation (High or Imminent only)
        3. Potential prejudice to vital interests (7 sub-criteria)
        4. Coordination AND decision urgency

        threat_probability: "low" | "moderate" | "high" | "imminent"
        """
        return _assess_lu_crisis_threat(
            description=description,
            sectors_affected=sectors_affected,
            entity_types=entity_types,
            threat_probability=threat_probability,
            safety_impact=safety_impact,
            service_impact=service_impact,
            data_impact=data_impact,
            financial_impact=financial_impact,
            affected_persons_count=affected_persons_count,
            cross_border=cross_border,
            capacity_exceeded=capacity_exceeded,
            threat_actor_type=threat_actor_type,
            sensitive_data_type=sensitive_data_type,
            coordination_required=coordination_required,
            urgent_decisions_required=urgent_decisions_required,
            prejudice_actual=prejudice_actual,
        )
```

- [ ] **Step 4: Register the tools in the MCP server**

Check how existing tools are registered (look at the main server file) and add:

```python
from cyberscale.tools import lu_crisis_assessment
lu_crisis_assessment.register(mcp)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/tools/test_lu_crisis_tool.py -v`
Expected: All tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/cyberscale/tools/lu_crisis_assessment.py src/tests/tools/test_lu_crisis_tool.py
git commit -m "feat(cyberscale): v8 HCPN crisis qualification MCP tools"
```

---

### Task 8: Curated scenarios + benchmark

**Files:**
- Create: `data/reference/curated_lu_crisis_scenarios.json`
- Create: `evaluation/benchmark_lu_crisis.py`

- [ ] **Step 1: Create curated scenarios**

```json
{
  "version": "1.0",
  "description": "15 curated Luxembourg HCPN national crisis qualification scenarios. Covers incidents and threats across qualification levels, cooperation modes, fast-track, undetermined criteria, and non-qualifying events.",
  "scenarios": [
    {
      "id": "HCPN-I-01",
      "name": "Energy grid attack — national crisis (Crise)",
      "description": "State-sponsored attack takes down Luxembourg HV/EHV electricity grid. Multiple deaths reported. Interministerial coordination activated.",
      "event_type": "incident",
      "sectors_affected": ["energy"],
      "entity_types": ["electricity_undertaking"],
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": null,
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "national_major_incident",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-I-02",
      "name": "Hospital ransomware — national crisis (Alerte/CERC)",
      "description": "Ransomware hits Luxembourg's main hospital. Health services unavailable, serious injuries. Coordination being mobilised.",
      "event_type": "incident",
      "sectors_affected": ["health"],
      "entity_types": ["healthcare_provider"],
      "safety_impact": "health_damage",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "significant",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": true,
      "expected_level": "national_major_incident",
      "expected_mode": "alerte_cerc"
    },
    {
      "id": "HCPN-I-03",
      "name": "Cross-border transport + energy — large-scale (Crise)",
      "description": "Coordinated attack on CFL rail and energy grid with cross-border impact to Belgium/Germany. Deaths confirmed.",
      "event_type": "incident",
      "sectors_affected": ["transport", "energy"],
      "entity_types": ["railway_undertaking", "electricity_undertaking"],
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": true,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": null,
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "large_scale_cybersecurity_incident",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-I-04",
      "name": "Government data exfiltration — national security",
      "description": "APT exfiltrates sensitive government data from public administration systems.",
      "event_type": "incident",
      "sectors_affected": ["public_administration"],
      "entity_types": [],
      "safety_impact": "none",
      "service_impact": "none",
      "data_impact": "exfiltrated",
      "financial_impact": "none",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": "government_data",
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "national_major_incident",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-I-05",
      "name": "Fast-track — malicious access to digital infrastructure",
      "description": "Suspected malicious unauthorized access to Luxembourg DNS infrastructure with complete service disruption.",
      "event_type": "incident",
      "sectors_affected": ["digital_infrastructure"],
      "entity_types": ["dns_service_provider"],
      "safety_impact": "none",
      "service_impact": "unavailable",
      "data_impact": "accessed",
      "financial_impact": "significant",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "national_major_incident",
      "expected_mode": "crise",
      "expected_fast_tracked": true
    },
    {
      "id": "HCPN-I-06",
      "name": "Food sector incident — non-essential, does not qualify",
      "description": "Cyberattack on Luxembourg food distribution company. Service disrupted.",
      "event_type": "incident",
      "sectors_affected": ["food"],
      "entity_types": [],
      "safety_impact": "none",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "significant",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": false,
      "expected_level": "none",
      "expected_mode": "permanent"
    },
    {
      "id": "HCPN-I-07",
      "name": "Energy incident — no coordination needed, does not qualify",
      "description": "Cyberattack on energy entity. Essential service affected but handled locally.",
      "event_type": "incident",
      "sectors_affected": ["energy"],
      "entity_types": ["electricity_undertaking"],
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "none",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "suspected_malicious": false,
      "coordination_required": false,
      "urgent_decisions_required": false,
      "prejudice_actual": true,
      "expected_qualifies": false,
      "expected_level": "none",
      "expected_mode": "permanent"
    },
    {
      "id": "HCPN-I-08",
      "name": "Drinking water degradation — undetermined, recommend consultation",
      "description": "Degraded water supply in Luxembourg. Duration unknown, severity unclear.",
      "event_type": "incident",
      "sectors_affected": ["drinking_water"],
      "entity_types": ["drinking_water_supplier"],
      "safety_impact": "health_risk",
      "service_impact": "degraded",
      "data_impact": "none",
      "financial_impact": "none",
      "affected_persons_count": 50000,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "suspected_malicious": false,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": false,
      "expected_level": "none",
      "expected_mode": "permanent",
      "expected_recommend_consultation": true
    },
    {
      "id": "HCPN-I-09",
      "name": "Banking sector — essential, all criteria met",
      "description": "Major disruption to Luxembourg banking infrastructure. Coordination required.",
      "event_type": "incident",
      "sectors_affected": ["banking"],
      "entity_types": ["credit_institution"],
      "safety_impact": "none",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": "industrial_secrets",
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "national_major_incident",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-I-10",
      "name": "Capacity exceeded — large-scale cybersecurity incident",
      "description": "Massive attack on Luxembourg digital infrastructure exceeding national response capacity.",
      "event_type": "incident",
      "sectors_affected": ["digital_infrastructure"],
      "entity_types": [],
      "safety_impact": "none",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": true,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": "critical_strategic_data",
      "suspected_malicious": true,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "large_scale_cybersecurity_incident",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-T-01",
      "name": "Imminent APT on energy — national threat (Alerte/CERC)",
      "description": "Intelligence confirms imminent state-sponsored attack on Luxembourg energy grid.",
      "event_type": "threat",
      "sectors_affected": ["energy"],
      "entity_types": ["electricity_undertaking"],
      "threat_probability": "imminent",
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": null,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": true,
      "expected_level": "national_major_cyber_threat",
      "expected_mode": "alerte_cerc"
    },
    {
      "id": "HCPN-T-02",
      "name": "Cross-border threat — large-scale (Crise)",
      "description": "Coordinated threat targeting Luxembourg and EU digital infrastructure. Attack materialised.",
      "event_type": "threat",
      "sectors_affected": ["digital_infrastructure"],
      "entity_types": [],
      "threat_probability": "high",
      "safety_impact": "none",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": true,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": "government_data",
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": true,
      "expected_qualifies": true,
      "expected_level": "large_scale_cyber_threat",
      "expected_mode": "crise"
    },
    {
      "id": "HCPN-T-03",
      "name": "Low probability threat — does not qualify",
      "description": "Theoretical vulnerability in banking systems. No active exploitation.",
      "event_type": "threat",
      "sectors_affected": ["banking"],
      "entity_types": [],
      "threat_probability": "low",
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "state_actor",
      "sensitive_data_type": null,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": false,
      "expected_level": "none",
      "expected_mode": "permanent"
    },
    {
      "id": "HCPN-T-04",
      "name": "Moderate probability threat — does not qualify",
      "description": "Reconnaissance activity detected against health sector. Exploitation possible but not imminent.",
      "event_type": "threat",
      "sectors_affected": ["health"],
      "entity_types": [],
      "threat_probability": "moderate",
      "safety_impact": "health_damage",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "significant",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": null,
      "sensitive_data_type": null,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": false,
      "expected_level": "none",
      "expected_mode": "permanent"
    },
    {
      "id": "HCPN-T-05",
      "name": "High probability threat on transport — national (Alerte/CERC)",
      "description": "High probability of coordinated attack on Luxembourg rail and air transport.",
      "event_type": "threat",
      "sectors_affected": ["transport"],
      "entity_types": ["railway_undertaking", "air_carrier"],
      "threat_probability": "high",
      "safety_impact": "death",
      "service_impact": "unavailable",
      "data_impact": "none",
      "financial_impact": "severe",
      "affected_persons_count": 0,
      "cross_border": false,
      "capacity_exceeded": false,
      "threat_actor_type": "terrorist_group",
      "sensitive_data_type": null,
      "coordination_required": true,
      "urgent_decisions_required": true,
      "prejudice_actual": false,
      "expected_qualifies": true,
      "expected_level": "national_major_cyber_threat",
      "expected_mode": "alerte_cerc"
    }
  ]
}
```

- [ ] **Step 2: Create benchmark runner**

```python
"""Benchmark for HCPN national crisis qualification scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCENARIOS_PATH = (
    Path(__file__).parent.parent / "data" / "reference" / "curated_lu_crisis_scenarios.json"
)


def run_benchmark() -> tuple[int, int, list[str]]:
    """Run all curated HCPN scenarios, return (passed, total, failures)."""
    from cyberscale.national.lu_crisis import qualify_hcpn_incident, qualify_hcpn_threat

    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    passed = 0
    failures: list[str] = []

    for s in scenarios:
        sid = s["id"]

        if s["event_type"] == "incident":
            result = qualify_hcpn_incident(
                sectors_affected=s["sectors_affected"],
                entity_types=s.get("entity_types", []),
                safety_impact=s.get("safety_impact", "none"),
                service_impact=s.get("service_impact", "none"),
                data_impact=s.get("data_impact", "none"),
                financial_impact=s.get("financial_impact", "none"),
                affected_persons_count=s.get("affected_persons_count", 0),
                cross_border=s.get("cross_border", False),
                capacity_exceeded=s.get("capacity_exceeded", False),
                threat_actor_type=s.get("threat_actor_type"),
                sensitive_data_type=s.get("sensitive_data_type"),
                suspected_malicious=s.get("suspected_malicious", False),
                coordination_required=s.get("coordination_required"),
                urgent_decisions_required=s.get("urgent_decisions_required"),
                prejudice_actual=s.get("prejudice_actual", False),
            )
        elif s["event_type"] == "threat":
            result = qualify_hcpn_threat(
                sectors_affected=s["sectors_affected"],
                entity_types=s.get("entity_types", []),
                threat_probability=s["threat_probability"],
                safety_impact=s.get("safety_impact", "none"),
                service_impact=s.get("service_impact", "none"),
                data_impact=s.get("data_impact", "none"),
                financial_impact=s.get("financial_impact", "none"),
                affected_persons_count=s.get("affected_persons_count", 0),
                cross_border=s.get("cross_border", False),
                capacity_exceeded=s.get("capacity_exceeded", False),
                threat_actor_type=s.get("threat_actor_type"),
                sensitive_data_type=s.get("sensitive_data_type"),
                coordination_required=s.get("coordination_required"),
                urgent_decisions_required=s.get("urgent_decisions_required"),
                prejudice_actual=s.get("prejudice_actual", False),
            )
        else:
            failures.append(f"{sid}: unknown event_type '{s['event_type']}'")
            continue

        ok = True
        errs: list[str] = []

        if result.qualifies != s["expected_qualifies"]:
            errs.append(f"qualifies: got {result.qualifies}, expected {s['expected_qualifies']}")
            ok = False
        if result.qualification_level != s["expected_level"]:
            errs.append(f"level: got {result.qualification_level}, expected {s['expected_level']}")
            ok = False
        if result.cooperation_mode != s["expected_mode"]:
            errs.append(f"mode: got {result.cooperation_mode}, expected {s['expected_mode']}")
            ok = False

        if "expected_fast_tracked" in s and result.fast_tracked != s["expected_fast_tracked"]:
            errs.append(f"fast_tracked: got {result.fast_tracked}, expected {s['expected_fast_tracked']}")
            ok = False

        if "expected_recommend_consultation" in s and result.recommend_consultation != s["expected_recommend_consultation"]:
            errs.append(f"recommend_consultation: got {result.recommend_consultation}, expected {s['expected_recommend_consultation']}")
            ok = False

        if ok:
            passed += 1
            print(f"  PASS {sid}: {s['name']}")
        else:
            failures.append(f"{sid}: {'; '.join(errs)}")
            print(f"  FAIL {sid}: {s['name']} -- {'; '.join(errs)}")

    return passed, len(scenarios), failures


def main():
    print("=" * 60)
    print("HCPN National Crisis Qualification Benchmark")
    print("=" * 60)

    passed, total, failures = run_benchmark()

    print(f"\n{'=' * 60}")
    print(f"Result: {passed}/{total} scenarios correct")
    if failures:
        print(f"\nFailures:")
        for f in failures:
            print(f"  - {f}")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Run benchmark**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python evaluation/benchmark_lu_crisis.py`
Expected: 15/15 scenarios correct

- [ ] **Step 4: Commit**

```bash
git add data/reference/curated_lu_crisis_scenarios.json evaluation/benchmark_lu_crisis.py
git commit -m "bench(cyberscale): v8 HCPN crisis qualification benchmark (15 scenarios)"
```

---

### Task 9: Documentation + roadmap update

**Files:**
- Modify: `docs/enhancement-roadmap.md`

- [ ] **Step 1: Add v8 completed section to roadmap**

Add after the v7 section in the roadmap:

```markdown
## v8 completed (2026-04-02)

| Enhancement | Layer | Result |
|-------------|-------|--------|
| HCPN national crisis qualification (incidents) | National | 3 cumulative criteria, fast-track provision, cooperation mode |
| HCPN national crisis qualification (threats) | National | 4 cumulative criteria (adds probability assessment) |
| Large-scale determination | National | cross_border OR capacity_exceeded -> large_scale level |
| Undetermined criteria handling | National | Explicit "undetermined"/"bypassed" for delegated thresholds, recommend_consultation |
| Sector dependency graph for interdependency check | National | Uses existing sector_dependencies.json for economic consequences sub-criterion |
| Curated HCPN scenarios (15) | National | 15/15 correct (10 incidents + 5 threats) |
| MCP tools: assess_lu_crisis_incident, assess_lu_crisis_threat | National | Authority-level tools scoped to impact on Luxembourg |
```

Update the model performance table to add:

```markdown
| National | LU HCPN crisis qualification (v8) | 100% (15/15 curated) | 100% | Met |
```

- [ ] **Step 2: Run existing tests to verify no regressions**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/ -v --tb=short 2>&1 | tail -30`
Expected: All existing tests still pass

- [ ] **Step 3: Commit**

```bash
git add docs/enhancement-roadmap.md
git commit -m "docs(cyberscale): v8 HCPN national crisis qualification complete"
```

---

## Dependency graph

```
Task 1 (reference data) -> Task 2 (result types + C1) -> Task 3 (C2) -> Task 4 (C3) -> Task 5 (main qualifier)
                            Task 2 -> Task 3 -> Task 4 -> Task 5 -> Task 6 (threats)
                            Task 5 + Task 6 -> Task 7 (MCP tool) -> Task 8 (benchmark) -> Task 9 (docs)
```

All tasks are sequential — each builds on the previous.

## Success criteria

| Metric | Target |
|---|---|
| Criterion 1 evaluation (essential service) | 100% deterministic |
| Criterion 2 evaluation (deterministic sub-criteria) | 100% correct |
| Criterion 2 evaluation (delegated thresholds) | Returns "undetermined" — never guesses |
| Criterion 2 (interdependent sectors) | Uses sector_dependencies.json graph |
| Criterion 3 evaluation | 100% deterministic |
| Fast-track provision | Correctly bypasses Criterion 2 (status="bypassed") |
| Cooperation mode (Crise vs Alerte/CERC) | Correctly maps from prejudice_actual |
| Large-scale determination | cross_border OR capacity_exceeded -> large_scale level |
| Threat probability gating | Low/Moderate rejected, High/Imminent accepted |
| Curated HCPN scenarios (15) | 15/15 correct |
| Existing tests | No regressions |

## Estimated effort

1 session. No ML — entirely deterministic qualification logic. 9 tasks, all sequential.
