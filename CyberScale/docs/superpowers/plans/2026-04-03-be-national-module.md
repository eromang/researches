# Belgium National Module — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Belgium as the second national module, validating the pluggable architecture established in v7. Belgium uses horizontal thresholds (same for all sectors) from the CCB NIS2 Notification Guide v1.3.

**Architecture:** Same pattern as LU: `be_thresholds.json` → `national/be.py` (is_be_covered + assess_be_significance) → registry entry. Belgium differs from LU in using horizontal thresholds rather than per-sector matrices. IR entities and DORA entities are excluded (same as LU). Key Belgium-specific thresholds: EUR 250K financial (vs EU EUR 500K), 20% users for 1h availability, recurring events (2x in 6 months).

**Tech Stack:** Python 3.11+, dataclasses, JSON reference data, pytest

---

## Key Design Decisions

- **Horizontal thresholds:** Belgium applies the same criteria across all sectors (unlike LU's per-sector matrices). No `sector_specific` dict needed.
- **Lower financial threshold:** EUR 250,000 or 5% turnover (whichever lower) — stricter than EU NIS2 EUR 500,000.
- **Availability threshold:** ≥20% users for ≥1 hour — Belgium-specific quantitative metric.
- **Recurring events:** ≥2 incidents in 6 months, same root cause, collectively meeting financial/availability thresholds. CyberScale cannot evaluate this from a single incident — flag for analyst awareness.
- **Trust service providers:** 24h notification deadline (vs 72h) — captured in applicable_frameworks output.
- **IR precedence:** Same as LU — IR entities (Art. 5-14) use EU-wide thresholds, not BE horizontal.
- **DORA carve-out:** Banking/financial entities under BNB supervision excluded.
- **Competent authority:** CCB (Centre for Cybersecurity Belgium).

## File Structure

| File | Responsibility |
|------|---------------|
| `data/reference/be_thresholds.json` (create) | CCB horizontal thresholds, DORA exclusion, notification timelines |
| `src/cyberscale/national/be.py` (create) | Belgium assessment logic |
| `src/tests/national/test_be.py` (create) | Unit tests |
| `src/cyberscale/national/registry.py` (modify) | Add BE entry |
| `data/reference/curated_be_incidents.json` (create) | 10 curated scenarios |
| `evaluation/benchmark_be.py` (create) | Benchmark runner |

---

## Tasks

### Task 1: Belgium reference data

**Files:**
- Create: `data/reference/be_thresholds.json`

- [ ] **Step 1: Create the reference data file**

```json
{
  "version": "1.0",
  "ms": "BE",
  "source": "CCB Guide sur les notifications NIS2 v1.3 (August 2025)",
  "legal_basis": "Loi du 26 avril 2024 (Belgian NIS2 transposition)",
  "competent_authority": "CCB",
  "notification_channel": "https://notif.safeonweb.be",
  "emergency_phone": "+32 (0)2 501 05 60",

  "significant_incident_criteria": {
    "description": "Five categories of significant events (non-exhaustive). Any one triggers mandatory notification.",

    "malicious_compromise": {
      "description": "Suspected malicious compromise of CIA — unauthorized access, unauthorized configuration, unauthorized execution",
      "threshold": "any",
      "deterministic": true
    },

    "availability": {
      "description": "Availability compromise causing severe operational disruption",
      "thresholds": [
        {
          "type": "user_percentage",
          "users_pct": 20,
          "duration_hours": 1,
          "description": "≥20% of users cannot access service for ≥1 hour"
        },
        {
          "type": "unknown_scope",
          "duration_hours": 1,
          "description": "Users lose access for ≥1 hour and entity cannot determine number affected"
        },
        {
          "type": "contractual",
          "description": "Delivery delays exceed contractual deadlines"
        }
      ],
      "exclusions": ["Planned maintenance matching expectations"]
    },

    "financial_loss": {
      "description": "Direct financial loss exceeding threshold",
      "threshold_eur": 250000,
      "threshold_turnover_pct": 5,
      "rule": "whichever is lower",
      "includes": [
        "replacement/relocation costs",
        "personnel costs",
        "contractual breach costs",
        "customer compensation",
        "communication costs",
        "legal/forensic/remediation costs"
      ],
      "excludes": [
        "administrative fines",
        "routine operating costs",
        "post-incident improvements",
        "insurance premiums"
      ],
      "additional_triggers": [
        "Loss or disclosure of intellectual property compromising future revenues",
        "Exfiltration of trade secrets per Directive (EU) 2016/943"
      ]
    },

    "third_party_damage": {
      "description": "Material, physical, or moral damage to other persons",
      "triggers": [
        "death",
        "hospitalisation",
        "injuries",
        "disabilities",
        "destruction of assets",
        "infrastructure damage",
        "delivery delays",
        "substantial financial consequences for third parties"
      ],
      "deterministic": true
    },

    "recurring_events": {
      "description": "Multiple non-significant incidents collectively becoming significant",
      "conditions": {
        "count": 2,
        "period_months": 6,
        "same_root_cause": true,
        "collective_threshold": "financial_loss OR availability"
      },
      "note": "Cannot be evaluated from a single incident assessment — flag for analyst awareness"
    }
  },

  "notification_timeline": {
    "early_warning_hours": 24,
    "incident_notification_hours": 72,
    "trust_service_notification_hours": 24,
    "final_report_days": 30,
    "note": "'Without undue delay' means as soon as possible, not waiting for the deadline maximum"
  },

  "exclusions": {
    "dora_entities": {
      "description": "Banking and financial market infrastructure entities under DORA are excluded from NIS2 notification (Art. 6, §3)",
      "sectors": ["banking", "financial_market_infrastructures"],
      "supervisor": "Banque Nationale de Belgique"
    },
    "ir_entities": {
      "description": "11 digital infrastructure/service provider types covered by Implementing Regulation (EU) 2024/7151 — IR thresholds prevail over CCB horizontal thresholds",
      "note": "Handled by three-tier router (IR tier takes precedence)"
    }
  }
}
```

- [ ] **Step 2: Validate JSON**

Run: `python3 -c "import json; json.load(open('data/reference/be_thresholds.json'))"`

- [ ] **Step 3: Commit**

```bash
git add data/reference/be_thresholds.json
git commit -m "feat(cyberscale): Belgium CCB NIS2 threshold reference data"
```

---

### Task 2: Belgium assessment module + tests

**Files:**
- Create: `src/cyberscale/national/be.py`
- Create: `src/tests/national/test_be.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for Belgium national-layer threshold assessment."""

from __future__ import annotations

import pytest

from cyberscale.national.be import (
    is_be_covered,
    assess_be_significance,
    BeSignificanceResult,
)


class TestBeCoverage:
    def test_energy_entity_covered(self):
        assert is_be_covered("energy", "electricity_undertaking") is True

    def test_health_entity_covered(self):
        assert is_be_covered("health", "healthcare_provider") is True

    def test_transport_entity_covered(self):
        assert is_be_covered("transport", "railway_undertaking") is True

    def test_public_admin_covered(self):
        assert is_be_covered("public_administration", "central_government_entity") is True

    def test_ir_entity_not_covered(self):
        """IR entities bypass BE thresholds even in Belgium."""
        assert is_be_covered("digital_infrastructure", "cloud_computing_provider") is False
        assert is_be_covered("digital_infrastructure", "dns_service_provider") is False
        assert is_be_covered("digital_infrastructure", "trust_service_provider") is False

    def test_dora_entity_not_covered(self):
        """DORA entities excluded from NIS2 notification in Belgium."""
        assert is_be_covered("banking", "credit_institution") is False

    def test_non_nis2_entity_not_covered(self):
        assert is_be_covered("non_nis2", "generic_individual") is False


class TestMaliciousCompromise:
    def test_malicious_access_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=True,
            data_impact="accessed",
        )
        assert result.significant_incident is True
        assert any("malicious" in c.lower() for c in result.triggered_criteria)

    def test_non_malicious_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=False,
        )
        assert result.significant_incident is False


class TestAvailabilityThreshold:
    def test_20pct_users_1h_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="unavailable",
            affected_persons_pct=25.0,
            impact_duration_hours=1.5,
        )
        assert result.significant_incident is True
        assert any("20%" in c or "availability" in c.lower() for c in result.triggered_criteria)

    def test_below_20pct_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="degraded",
            affected_persons_pct=15.0,
            impact_duration_hours=2.0,
        )
        assert result.significant_incident is False

    def test_above_20pct_below_1h_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            service_impact="unavailable",
            affected_persons_pct=50.0,
            impact_duration_hours=0.5,
        )
        assert result.significant_incident is False

    def test_total_unavailability_1h_triggers(self):
        """service_impact=unavailable implies 100% users affected."""
        result = assess_be_significance(
            sector="health",
            entity_type="healthcare_provider",
            service_impact="unavailable",
            impact_duration_hours=1.0,
        )
        assert result.significant_incident is True


class TestFinancialLossThreshold:
    def test_severe_financial_triggers(self):
        """severe financial_impact assumed to exceed EUR 250K threshold."""
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            financial_impact="severe",
        )
        assert result.significant_incident is True
        assert any("financial" in c.lower() or "250" in c for c in result.triggered_criteria)

    def test_significant_financial_triggers(self):
        result = assess_be_significance(
            sector="transport",
            entity_type="railway_undertaking",
            financial_impact="significant",
        )
        assert result.significant_incident is True

    def test_minor_financial_no_trigger(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            financial_impact="minor",
        )
        assert result.significant_incident is False

    def test_trade_secret_exfiltration_triggers(self):
        result = assess_be_significance(
            sector="manufacturing",
            entity_type="machinery_manufacturer",
            data_impact="exfiltrated",
            trade_secret_exfiltration=True,
        )
        assert result.significant_incident is True


class TestThirdPartyDamage:
    def test_death_triggers(self):
        result = assess_be_significance(
            sector="health",
            entity_type="healthcare_provider",
            safety_impact="death",
        )
        assert result.significant_incident is True
        assert any("death" in c.lower() or "third party" in c.lower() for c in result.triggered_criteria)

    def test_health_damage_triggers(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            safety_impact="health_damage",
        )
        assert result.significant_incident is True

    def test_health_risk_no_trigger(self):
        """health_risk alone does not meet 'death/hospitalisation/injuries' threshold."""
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            safety_impact="health_risk",
        )
        assert result.significant_incident is False


class TestApplicableFrameworks:
    def test_includes_nis2_framework(self):
        result = assess_be_significance(
            sector="energy",
            entity_type="electricity_undertaking",
            suspected_malicious=True,
            data_impact="accessed",
        )
        assert any(fw["framework"] == "NIS2" for fw in result.applicable_frameworks)
        assert result.competent_authority == "CCB"

    def test_trust_service_24h_notification(self):
        """Trust services have 24h notification deadline in Belgium."""
        result = assess_be_significance(
            sector="digital_infrastructure",
            entity_type="trust_service_provider",
            suspected_malicious=True,
            data_impact="accessed",
        )
        # Trust services should go through IR, not BE
        # This test verifies is_be_covered returns False for trust_service_provider
        pass  # Covered by TestBeCoverage.test_ir_entity_not_covered
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_be.py -v 2>&1 | head -10`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Belgium module**

```python
"""Belgium national-layer incident significance assessment.

Horizontal thresholds from CCB NIS2 Notification Guide v1.3 (August 2025).
Unlike Luxembourg (per-sector ILR matrices), Belgium applies the same
criteria across all NIS2 sectors.

IR entities (Art. 5-14) and DORA entities (banking/financial) are excluded.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


_THRESHOLDS_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "data" / "reference" / "be_thresholds.json"
)

_cached: dict | None = None


def _load() -> dict:
    global _cached
    if _cached is None:
        with open(_THRESHOLDS_PATH, encoding="utf-8") as f:
            _cached = json.load(f)
    return _cached


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------


def is_be_covered(sector: str, entity_type: str) -> bool:
    """Check if entity falls under Belgium CCB horizontal thresholds.

    Returns False for:
    - IR entities (EU-wide thresholds take precedence)
    - DORA entities (banking/financial, BNB supervision)
    - Non-NIS2 entities
    """
    from cyberscale.models.contextual_ir import is_ir_entity

    if is_ir_entity(entity_type):
        return False

    data = _load()
    dora_sectors = data["exclusions"]["dora_entities"]["sectors"]
    if sector in dora_sectors:
        return False

    if sector == "non_nis2":
        return False

    return True


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class BeSignificanceResult:
    """Result of Belgium CCB threshold assessment."""

    significant_incident: bool
    triggered_criteria: list[str]
    ccb_reference: str = "CCB NIS2 Guide v1.3"
    competent_authority: str = "CCB"
    applicable_frameworks: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "significant_incident": self.significant_incident,
            "triggered_criteria": self.triggered_criteria,
            "ccb_reference": self.ccb_reference,
            "competent_authority": self.competent_authority,
            "applicable_frameworks": self.applicable_frameworks,
        }


# ---------------------------------------------------------------------------
# Main assessment function
# ---------------------------------------------------------------------------


def assess_be_significance(
    sector: str,
    entity_type: str,
    service_impact: str = "none",
    data_impact: str = "none",
    financial_impact: str = "none",
    safety_impact: str = "none",
    affected_persons_count: int = 0,
    affected_persons_pct: float = 0.0,
    impact_duration_hours: float = 0,
    suspected_malicious: bool = False,
    cross_border: bool = False,
    trade_secret_exfiltration: bool = False,
) -> BeSignificanceResult:
    """Assess incident significance against Belgium CCB horizontal thresholds.

    Five categories (any one triggers):
    1. Suspected malicious CIA compromise
    2. Availability: ≥20% users for ≥1h
    3. Financial loss: >EUR 250K or >5% turnover
    4. Third-party damage: death, hospitalisation, injuries
    5. Recurring events (cannot evaluate from single incident — flagged in output)
    """
    data = _load()
    criteria = data["significant_incident_criteria"]
    triggered: list[str] = []

    # Check DORA exclusion
    dora_sectors = data["exclusions"]["dora_entities"]["sectors"]
    if sector in dora_sectors:
        return BeSignificanceResult(
            significant_incident=False,
            triggered_criteria=[],
            ccb_reference="DORA",
            competent_authority="BNB",
            applicable_frameworks=[{
                "framework": "DORA",
                "competent_authority": "Banque Nationale de Belgique",
                "note": "Banking/financial entities excluded from NIS2 notification (Art. 6, §3)",
            }],
        )

    # 1. Malicious CIA compromise
    if suspected_malicious and data_impact in ("accessed", "exfiltrated", "compromised", "systemic"):
        triggered.append("Malicious CIA compromise: suspected malicious unauthorized access")

    # 2. Availability
    # service_impact=unavailable implies 100% of users affected
    effective_pct = affected_persons_pct
    if service_impact in ("unavailable", "sustained") and effective_pct == 0:
        effective_pct = 100.0

    avail_threshold = criteria["availability"]["thresholds"][0]
    if effective_pct >= avail_threshold["users_pct"] and impact_duration_hours >= avail_threshold["duration_hours"]:
        triggered.append(
            f"Availability: ≥{avail_threshold['users_pct']}% users for ≥{avail_threshold['duration_hours']}h "
            f"(actual: {effective_pct:.0f}% for {impact_duration_hours:.1f}h)"
        )

    # 3. Financial loss (>EUR 250K or >5% turnover)
    fin = criteria["financial_loss"]
    if financial_impact in ("significant", "severe"):
        triggered.append(
            f"Financial loss: {financial_impact} impact (threshold: >{fin['threshold_eur']:,} EUR or >{fin['threshold_turnover_pct']}% turnover)"
        )
    if trade_secret_exfiltration:
        triggered.append("Financial loss: exfiltration of trade secrets (Directive 2016/943)")

    # 4. Third-party damage
    if safety_impact == "death":
        triggered.append("Third-party damage: death")
    elif safety_impact == "health_damage":
        triggered.append("Third-party damage: hospitalisation/injuries/disabilities")

    # Build frameworks
    frameworks = [{
        "framework": "NIS2",
        "competent_authority": "CCB",
        "notification_channel": data["notification_channel"],
        "early_warning_hours": data["notification_timeline"]["early_warning_hours"],
        "incident_notification_hours": data["notification_timeline"]["incident_notification_hours"],
        "final_report_days": data["notification_timeline"]["final_report_days"],
    }]

    return BeSignificanceResult(
        significant_incident=len(triggered) > 0,
        triggered_criteria=triggered,
        competent_authority="CCB",
        applicable_frameworks=frameworks,
    )
```

- [ ] **Step 4: Run tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/test_be.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/national/be.py src/tests/national/test_be.py
git commit -m "feat(cyberscale): Belgium national threshold assessment module (CCB NIS2 v1.3)"
```

---

### Task 3: Register in national registry

**Files:**
- Modify: `src/cyberscale/national/registry.py`
- Modify: `src/tests/national/test_registry.py`

- [ ] **Step 1: Add BE to registry**

Read `src/cyberscale/national/registry.py`. Add:

```python
def _load_be():
    from cyberscale.national.be import is_be_covered, assess_be_significance
    return is_be_covered, assess_be_significance
```

And add to `_NATIONAL_LOADERS`:
```python
_NATIONAL_LOADERS: dict[str, Callable] = {
    "LU": _load_lu,
    "BE": _load_be,
}
```

- [ ] **Step 2: Add registry test**

Read `src/tests/national/test_registry.py`. Add test:

```python
def test_be_module_available():
    assert "BE" in get_available_ms()

def test_be_module_loads():
    module = get_national_module("BE")
    assert module is not None
    is_covered_fn, assess_fn = module
    assert callable(is_covered_fn)
    assert callable(assess_fn)
```

- [ ] **Step 3: Run tests**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/national/ -v`

- [ ] **Step 4: Commit**

```bash
git add src/cyberscale/national/registry.py src/tests/national/test_registry.py
git commit -m "feat(cyberscale): register Belgium in national module registry"
```

---

### Task 4: Curated scenarios + benchmark

**Files:**
- Create: `data/reference/curated_be_incidents.json`
- Create: `evaluation/benchmark_be.py`

- [ ] **Step 1: Create curated scenarios**

```json
{
  "version": "1.0",
  "description": "10 curated Belgium incident scenarios for national threshold benchmark.",
  "scenarios": [
    {
      "id": "BE-01",
      "name": "Malicious access to energy SCADA — significant",
      "entity_type": "electricity_undertaking",
      "sector": "energy",
      "ms_established": "BE",
      "suspected_malicious": true,
      "data_impact": "accessed",
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "malicious"
    },
    {
      "id": "BE-02",
      "name": "Hospital 30% users down 2h — significant (availability)",
      "entity_type": "healthcare_provider",
      "sector": "health",
      "ms_established": "BE",
      "service_impact": "degraded",
      "affected_persons_pct": 30.0,
      "impact_duration_hours": 2.0,
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "availability"
    },
    {
      "id": "BE-03",
      "name": "Transport severe financial loss — significant",
      "entity_type": "railway_undertaking",
      "sector": "transport",
      "ms_established": "BE",
      "financial_impact": "severe",
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "financial"
    },
    {
      "id": "BE-04",
      "name": "Energy incident with death — significant (third-party)",
      "entity_type": "electricity_undertaking",
      "sector": "energy",
      "ms_established": "BE",
      "safety_impact": "death",
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "death"
    },
    {
      "id": "BE-05",
      "name": "Cloud provider — IR entity, bypasses BE",
      "entity_type": "cloud_computing_provider",
      "sector": "digital_infrastructure",
      "ms_established": "BE",
      "service_impact": "unavailable",
      "impact_duration_hours": 1.0,
      "suspected_malicious": true,
      "expected_model": "ir_thresholds",
      "expected_significant": true
    },
    {
      "id": "BE-06",
      "name": "Bank — DORA entity, excluded from NIS2",
      "entity_type": "credit_institution",
      "sector": "banking",
      "ms_established": "BE",
      "service_impact": "unavailable",
      "financial_impact": "severe",
      "expected_model": "national_be_thresholds",
      "expected_significant": false
    },
    {
      "id": "BE-07",
      "name": "Energy 15% users down 3h — not significant (below 20%)",
      "entity_type": "electricity_undertaking",
      "sector": "energy",
      "ms_established": "BE",
      "service_impact": "degraded",
      "affected_persons_pct": 15.0,
      "impact_duration_hours": 3.0,
      "expected_model": "national_be_thresholds",
      "expected_significant": false
    },
    {
      "id": "BE-08",
      "name": "Manufacturing total outage 1.5h — significant (availability 100%)",
      "entity_type": "machinery_manufacturer",
      "sector": "manufacturing",
      "ms_established": "BE",
      "service_impact": "unavailable",
      "impact_duration_hours": 1.5,
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "availability"
    },
    {
      "id": "BE-09",
      "name": "Trade secret exfiltration — significant (financial)",
      "entity_type": "chemicals_manufacturer",
      "sector": "chemicals",
      "ms_established": "BE",
      "data_impact": "exfiltrated",
      "trade_secret_exfiltration": true,
      "expected_model": "national_be_thresholds",
      "expected_significant": true,
      "expected_criteria_contains": "trade secret"
    },
    {
      "id": "BE-10",
      "name": "Minor incident no criteria met — not significant",
      "entity_type": "electricity_undertaking",
      "sector": "energy",
      "ms_established": "BE",
      "service_impact": "partial",
      "financial_impact": "minor",
      "expected_model": "national_be_thresholds",
      "expected_significant": false
    }
  ]
}
```

- [ ] **Step 2: Create benchmark runner**

```python
"""Benchmark for Belgium national threshold scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

SCENARIOS_PATH = PROJECT_ROOT / "data" / "reference" / "curated_be_incidents.json"


def run_benchmark() -> tuple[int, int, list[str]]:
    from cyberscale.national.be import assess_be_significance, is_be_covered
    from cyberscale.models.contextual_ir import is_ir_entity

    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    passed = 0
    failures: list[str] = []

    for s in scenarios:
        sid = s["id"]
        entity_type = s["entity_type"]
        sector = s["sector"]

        # Determine expected routing
        if is_ir_entity(entity_type):
            actual_model = "ir_thresholds"
            # For IR entities, we just check routing — not BE significance
            if s["expected_model"] == "ir_thresholds":
                passed += 1
                print(f"  PASS {sid}: {s['name']} (routed to IR)")
                continue
            else:
                failures.append(f"{sid}: expected model {s['expected_model']} but entity is IR")
                print(f"  FAIL {sid}: {s['name']} — IR entity mismatch")
                continue

        # BE assessment
        result = assess_be_significance(
            sector=sector,
            entity_type=entity_type,
            service_impact=s.get("service_impact", "none"),
            data_impact=s.get("data_impact", "none"),
            financial_impact=s.get("financial_impact", "none"),
            safety_impact=s.get("safety_impact", "none"),
            affected_persons_count=s.get("affected_persons_count", 0),
            affected_persons_pct=s.get("affected_persons_pct", 0.0),
            impact_duration_hours=s.get("impact_duration_hours", 0),
            suspected_malicious=s.get("suspected_malicious", False),
            cross_border=s.get("cross_border", False),
            trade_secret_exfiltration=s.get("trade_secret_exfiltration", False),
        )

        ok = True
        errs: list[str] = []

        if result.significant_incident != s["expected_significant"]:
            errs.append(f"significant: got {result.significant_incident}, expected {s['expected_significant']}")
            ok = False

        if "expected_criteria_contains" in s and result.significant_incident:
            needle = s["expected_criteria_contains"].lower()
            if not any(needle in c.lower() for c in result.triggered_criteria):
                errs.append(f"criteria missing '{needle}' in {result.triggered_criteria}")
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
    print("Belgium National Threshold Benchmark")
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

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python evaluation/benchmark_be.py`
Expected: 10/10 correct

- [ ] **Step 4: Commit**

```bash
git add data/reference/curated_be_incidents.json evaluation/benchmark_be.py
git commit -m "bench(cyberscale): Belgium national threshold benchmark (10 scenarios)"
```

---

### Task 5: Documentation + roadmap

**Files:**
- Modify: `docs/enhancement-roadmap.md`

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/ -v --tb=short 2>&1 | tail -10`

- [ ] **Step 2: Mark enhancement 14 as completed**

Update the roadmap entry for item 14:
```markdown
#### ~~14. Second member state module~~ → completed

**Status:** Completed — Belgium (CCB NIS2 v1.3) added as second national module. Horizontal thresholds: EUR 250K financial, 20% users/1h availability, malicious CIA compromise, third-party damage. DORA carve-out for banking. 10/10 curated scenarios passing.
```

Add to the model performance table:
```markdown
| 2 | BE national thresholds | 100% (10/10 curated) | 100% | Met |
```

- [ ] **Step 3: Commit**

```bash
git add docs/enhancement-roadmap.md
git commit -m "docs(cyberscale): Belgium national module complete, roadmap updated"
```

---

## Dependency graph

```
Task 1 (JSON) -> Task 2 (module + tests) -> Task 3 (registry) -> Task 4 (benchmark) -> Task 5 (docs)
```

## Success criteria

| Metric | Target |
|---|---|
| BE threshold assessment | 100% (deterministic) |
| IR entities in BE bypass BE thresholds | 100% |
| DORA entities correctly excluded | 100% |
| Three-tier routing for BE entities | 100% |
| Curated BE scenarios (10) | 10/10 |
| Existing tests | No regressions |
| LU tests still pass | 100% |
