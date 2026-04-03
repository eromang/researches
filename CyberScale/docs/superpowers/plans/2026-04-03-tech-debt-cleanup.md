# Tech Debt Cleanup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Centralize hardcoded values, add structured logging at decision points, and eliminate duplicated validation across the CyberScale codebase.

**Architecture:** Create a `config.py` module that loads valid enums from reference JSON and centralizes model defaults. Add Python `logging` at key routing and classification decision points. Remove duplicated VALID_SECTORS from `tools/contextual.py`. Keep changes backward-compatible — no interface changes to MCP tools.

**Tech Stack:** Python 3.11+, standard library `logging`, existing JSON reference data

**Non-goals:** Pydantic input validation (deferred — FastMCP doesn't use it, adding it would change tool signatures and require significant testing). Consistent error handling refactoring (deferred — current dict-based error returns work and are consumed by MCP clients).

---

## File Structure

| File | Responsibility |
|------|---------------|
| `src/cyberscale/config.py` (create) | Centralized constants: VALID_SECTORS, VALID_ENTITY_TYPES (loaded from JSON), VALID_*_IMPACT, MC_PASSES, MAX_LENGTH, confidence thresholds |
| `src/tests/test_config.py` (create) | Tests that config loads correctly from reference data |
| `src/cyberscale/models/contextual.py` (modify) | Import from config instead of hardcoding VALID_* |
| `src/cyberscale/tools/contextual.py` (modify) | Remove duplicate VALID_SECTORS, import from config |
| `src/cyberscale/tools/entity_incident.py` (modify) | Import from config, add logging |
| `src/cyberscale/national/lu_crisis.py` (modify) | Add logging at criterion evaluation points |
| `src/cyberscale/aggregation.py` (modify) | Add logging at T/O level derivation |

---

## Tasks

### Task 1: Config module with reference-loaded enums

**Files:**
- Create: `src/cyberscale/config.py`
- Create: `src/tests/test_config.py`

- [ ] **Step 1: Write failing tests**

```python
"""Tests for centralized config module."""

from __future__ import annotations

import pytest

from cyberscale.config import (
    VALID_SECTORS,
    VALID_ENTITY_TYPES,
    VALID_SERVICE_IMPACT,
    VALID_DATA_IMPACT,
    VALID_FINANCIAL_IMPACT,
    VALID_SAFETY_IMPACT,
    DEFAULT_MC_PASSES,
    DEFAULT_MAX_LENGTH_SCORER,
    DEFAULT_MAX_LENGTH_CONTEXTUAL,
    CONFIDENCE_HIGH_THRESHOLD,
    CONFIDENCE_MEDIUM_THRESHOLD,
)


class TestValidSectors:
    def test_loaded_from_reference(self):
        """Sectors should include all NIS2 sectors."""
        assert "energy" in VALID_SECTORS
        assert "transport" in VALID_SECTORS
        assert "health" in VALID_SECTORS
        assert "digital_infrastructure" in VALID_SECTORS
        assert "public_administration" in VALID_SECTORS
        assert "non_nis2" in VALID_SECTORS

    def test_is_set(self):
        assert isinstance(VALID_SECTORS, set)

    def test_has_expected_count(self):
        """Should have 19 sectors (18 NIS2 + non_nis2)."""
        assert len(VALID_SECTORS) == 19


class TestValidEntityTypes:
    def test_loaded_from_reference_json(self):
        """Entity types should be loaded from nis2_entity_types.json."""
        assert "electricity_undertaking" in VALID_ENTITY_TYPES
        assert "trust_service_provider" in VALID_ENTITY_TYPES
        assert "generic_enterprise" in VALID_ENTITY_TYPES

    def test_is_set(self):
        assert isinstance(VALID_ENTITY_TYPES, set)

    def test_has_expected_count(self):
        """Should have 56 entity types from nis2_entity_types.json."""
        assert len(VALID_ENTITY_TYPES) == 56


class TestImpactEnums:
    def test_service_impact_values(self):
        assert VALID_SERVICE_IMPACT == {"none", "partial", "degraded", "unavailable", "sustained"}

    def test_data_impact_values(self):
        assert VALID_DATA_IMPACT == {"none", "accessed", "exfiltrated", "compromised", "systemic"}

    def test_financial_impact_values(self):
        assert VALID_FINANCIAL_IMPACT == {"none", "minor", "significant", "severe"}

    def test_safety_impact_values(self):
        assert VALID_SAFETY_IMPACT == {"none", "health_risk", "health_damage", "death"}


class TestModelDefaults:
    def test_mc_passes(self):
        assert DEFAULT_MC_PASSES == 5

    def test_max_length_scorer(self):
        assert DEFAULT_MAX_LENGTH_SCORER == 192

    def test_max_length_contextual(self):
        assert DEFAULT_MAX_LENGTH_CONTEXTUAL == 256

    def test_confidence_thresholds(self):
        assert CONFIDENCE_HIGH_THRESHOLD == 0.7
        assert CONFIDENCE_MEDIUM_THRESHOLD == 0.4
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/test_config.py -v 2>&1 | head -10`
Expected: FAIL — `ModuleNotFoundError: No module named 'cyberscale.config'`

- [ ] **Step 3: Implement config module**

```python
"""Centralized configuration for CyberScale.

Loads valid enums from reference JSON where possible. Centralizes model
defaults that were previously scattered across 5+ modules.

Import from here instead of hardcoding values in individual modules.
"""

from __future__ import annotations

import json
from pathlib import Path


_REF_DIR = Path(__file__).parent.parent.parent / "data" / "reference"


# ---------------------------------------------------------------------------
# Valid enums — loaded from reference data
# ---------------------------------------------------------------------------

def _load_entity_types() -> set[str]:
    """Load entity type IDs from nis2_entity_types.json."""
    path = _REF_DIR / "nis2_entity_types.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    ids = {et["id"] for et in data["entity_types"]}
    # Add non-NIS2 types not in the JSON
    ids.update({"generic_enterprise", "generic_sme", "generic_individual"})
    return ids


def _load_sectors() -> set[str]:
    """Load sector IDs from nis2_entity_types.json (unique sectors + non_nis2)."""
    path = _REF_DIR / "nis2_entity_types.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    sectors = {et["sector"] for et in data["entity_types"]}
    sectors.add("non_nis2")
    return sectors


VALID_ENTITY_TYPES: set[str] = _load_entity_types()
VALID_SECTORS: set[str] = _load_sectors()

# Impact taxonomy — these are small fixed enums, not worth externalizing to JSON
VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}
VALID_FINANCIAL_IMPACT = {"none", "minor", "significant", "severe"}
VALID_SAFETY_IMPACT = {"none", "health_risk", "health_damage", "death"}


# ---------------------------------------------------------------------------
# Model defaults — previously scattered across 5 model classes
# ---------------------------------------------------------------------------

DEFAULT_MC_PASSES = 5
DEFAULT_MAX_LENGTH_SCORER = 192
DEFAULT_MAX_LENGTH_CONTEXTUAL = 256

# Confidence thresholds (max_prob → confidence label)
CONFIDENCE_HIGH_THRESHOLD = 0.7
CONFIDENCE_MEDIUM_THRESHOLD = 0.4


def max_prob_to_confidence(max_prob: float) -> str:
    """Convert max probability to confidence label.

    Previously duplicated in scorer.py, contextual.py, technical.py,
    operational.py, scorer_multitask.py with identical logic.
    """
    if max_prob >= CONFIDENCE_HIGH_THRESHOLD:
        return "high"
    if max_prob >= CONFIDENCE_MEDIUM_THRESHOLD:
        return "medium"
    return "low"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/test_config.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/config.py src/tests/test_config.py
git commit -m "refactor(cyberscale): centralized config module with reference-loaded enums"
```

---

### Task 2: Migrate VALID_* imports across codebase

**Files:**
- Modify: `src/cyberscale/models/contextual.py`
- Modify: `src/cyberscale/tools/contextual.py`
- Modify: `src/cyberscale/tools/entity_incident.py`

- [ ] **Step 1: Update `src/cyberscale/models/contextual.py`**

Replace the hardcoded VALID_* sets (lines 17-60) with imports from config. Keep the sets as re-exports for backward compatibility (other modules import from here).

Replace:
```python
VALID_SECTORS = {
    "energy", "transport", "banking", "financial_market", "health",
    ...
}

VALID_ENTITY_TYPES = {
    ...
}

VALID_SERVICE_IMPACT = {"none", "partial", "degraded", "unavailable", "sustained"}
VALID_DATA_IMPACT = {"none", "accessed", "exfiltrated", "compromised", "systemic"}
VALID_FINANCIAL_IMPACT = {"none", "minor", "significant", "severe"}
VALID_SAFETY_IMPACT = {"none", "health_risk", "health_damage", "death"}
```

With:
```python
from cyberscale.config import (
    VALID_SECTORS,
    VALID_ENTITY_TYPES,
    VALID_SERVICE_IMPACT,
    VALID_DATA_IMPACT,
    VALID_FINANCIAL_IMPACT,
    VALID_SAFETY_IMPACT,
    max_prob_to_confidence,
)
```

Also update the `_max_prob_to_confidence` method in `ContextualClassifier` (around line 321) to use the centralized function:

Replace:
```python
    @staticmethod
    def _max_prob_to_confidence(max_prob: float) -> str:
        if max_prob >= 0.7:
            return "high"
        if max_prob >= 0.4:
            return "medium"
        return "low"
```

With:
```python
    @staticmethod
    def _max_prob_to_confidence(max_prob: float) -> str:
        return max_prob_to_confidence(max_prob)
```

- [ ] **Step 2: Remove duplicate VALID_SECTORS from `src/cyberscale/tools/contextual.py`**

Remove the duplicate VALID_SECTORS definition (lines 32-38) and replace with:
```python
from cyberscale.config import VALID_SECTORS
```

- [ ] **Step 3: Update `src/cyberscale/tools/entity_incident.py`**

The import at line 202 already does:
```python
from cyberscale.models.contextual import VALID_SECTORS, VALID_ENTITY_TYPES
```

This still works because `models/contextual.py` re-exports from config. No change needed here — the re-export chain is: `config.py` → `models/contextual.py` → `tools/entity_incident.py`.

- [ ] **Step 4: Run full test suite to verify no regressions**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/ -v --tb=short 2>&1 | tail -20`
Expected: All tests still pass (441+)

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/models/contextual.py src/cyberscale/tools/contextual.py
git commit -m "refactor(cyberscale): migrate VALID_* enums to centralized config"
```

---

### Task 3: Structured logging at decision points

**Files:**
- Modify: `src/cyberscale/tools/entity_incident.py`
- Modify: `src/cyberscale/national/lu_crisis.py`
- Modify: `src/cyberscale/aggregation.py`

- [ ] **Step 1: Add logging to `src/cyberscale/tools/entity_incident.py`**

Add at top of file:
```python
import logging

logger = logging.getLogger("cyberscale.tools.entity_incident")
```

Add logging in `_assess_entity_incident()` at each routing decision:

After the IR check (line ~109):
```python
        logger.info(
            "entity_incident routing: tier=IR entity_type=%s significant=%s",
            entity_type, ir_result.significant_incident,
        )
```

After the national check (line ~131):
```python
                logger.info(
                    "entity_incident routing: tier=national_%s sector=%s entity_type=%s significant=%s",
                    ms_established.lower(), sector, entity_type, nat_result.significant_incident,
                )
```

After the NIS2 ML fallback (line ~139):
```python
        logger.info(
            "entity_incident routing: tier=nis2_ml sector=%s entity_type=%s significant=%s",
            sector, entity_type, nis2_result.significant_incident,
        )
```

- [ ] **Step 2: Add logging to `src/cyberscale/national/lu_crisis.py`**

Add at top of file:
```python
import logging

logger = logging.getLogger("cyberscale.national.lu_crisis")
```

Add logging in `qualify_hcpn_incident()`:

After criterion evaluations, before the qualification determination:
```python
    logger.info(
        "hcpn_incident: c1=%s c2=%s c3=%s fast_track=%s",
        criteria["criterion_1"].status,
        criteria["criterion_2"].status,
        criteria["criterion_3"].status,
        fast_tracked,
    )
```

After qualification determination:
```python
    logger.info(
        "hcpn_incident result: qualifies=%s level=%s mode=%s consult=%s",
        all_satisfied, level, mode, any_undetermined,
    )
```

Add similar logging in `qualify_hcpn_threat()`:

```python
    logger.info(
        "hcpn_threat: c1=%s c2_prob=%s c3_prejudice=%s c4_urgency=%s",
        criteria["criterion_1"].status,
        criteria["criterion_2_probability"].status,
        criteria["criterion_3_prejudice"].status,
        criteria["criterion_4_urgency"].status,
    )
    logger.info(
        "hcpn_threat result: qualifies=%s level=%s mode=%s consult=%s",
        all_met, level, mode, any_undetermined,
    )
```

- [ ] **Step 3: Add logging to `src/cyberscale/aggregation.py`**

Add at top of file:
```python
import logging

logger = logging.getLogger("cyberscale.aggregation")
```

Add logging in `derive_t_level()` (after the level is determined):
```python
    logger.info("derive_t_level: %s basis=%s", level, basis)
```

Add logging in `derive_o_level()` (after the level is determined):
```python
    logger.info("derive_o_level: %s basis=%s", level, basis)
```

Add logging in `propagate_cascading()` (when sectors propagate):
```python
    if all_sectors - impacted_sectors:
        logger.info(
            "cascading propagation: %s -> %s (level=%s)",
            impacted_sectors, all_sectors - impacted_sectors, cascading_level,
        )
```

- [ ] **Step 4: Run full test suite to verify no regressions**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/ -v --tb=short 2>&1 | tail -20`
Expected: All tests still pass. Logging is NOP by default (no handlers configured).

- [ ] **Step 5: Commit**

```bash
git add src/cyberscale/tools/entity_incident.py src/cyberscale/national/lu_crisis.py src/cyberscale/aggregation.py
git commit -m "refactor(cyberscale): structured logging at routing and classification decision points"
```

---

### Task 4: Verify and update roadmap

**Files:**
- Modify: `docs/enhancement-roadmap.md`

- [ ] **Step 1: Run full test suite one final time**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python -m pytest src/tests/ -v --tb=short 2>&1 | tail -10`
Expected: All tests pass, no regressions

- [ ] **Step 2: Run benchmarks to verify no changes**

Run: `cd /Users/ericromang/Documents/GitHub/researches/CyberScale && python evaluation/benchmark_lu_crisis.py && python evaluation/validate_real_incidents.py`
Expected: 15/15 curated + 10/10 real incidents pass

- [ ] **Step 3: Mark tech debt items as completed in roadmap**

Update `docs/enhancement-roadmap.md`:

Replace:
```markdown
#### 11. Input validation at MCP boundaries
```
With:
```markdown
#### ~~11. Input validation at MCP boundaries~~ → deferred
```

Add note: "Deferred — FastMCP doesn't use Pydantic; adding it would change tool signatures. Current manual validation in tools is sufficient."

Replace:
```markdown
#### 12. Centralize hardcoded values
```
With:
```markdown
#### ~~12. Centralize hardcoded values~~ → completed
```

Add note: "Completed — `config.py` loads VALID_SECTORS and VALID_ENTITY_TYPES from reference JSON. VALID_*_IMPACT, MC_PASSES, MAX_LENGTH, confidence thresholds centralized. Duplicate VALID_SECTORS in tools/contextual.py removed."

Replace:
```markdown
#### 13. Structured logging at decision points
```
With:
```markdown
#### ~~13. Structured logging at decision points~~ → completed
```

Add note: "Completed — `logging.getLogger('cyberscale.*')` at entity_incident routing, HCPN criterion evaluation, T/O level derivation, and cascading propagation."

- [ ] **Step 4: Commit**

```bash
git add docs/enhancement-roadmap.md
git commit -m "docs(cyberscale): mark tech debt items 12-13 completed, 11 deferred"
```

---

## Dependency graph

```
Task 1 (config module) -> Task 2 (migrate imports) -> Task 3 (logging) -> Task 4 (docs)
```

All tasks are sequential.

## Success criteria

| Metric | Target |
|---|---|
| VALID_SECTORS loaded from JSON | Yes (not hardcoded) |
| VALID_ENTITY_TYPES loaded from JSON | Yes (not hardcoded) |
| Duplicate VALID_SECTORS removed | Yes (tools/contextual.py) |
| Confidence thresholds centralized | Yes (config.py) |
| Logging at routing decisions | Yes (entity_incident.py) |
| Logging at HCPN criteria | Yes (lu_crisis.py) |
| Logging at T/O derivation | Yes (aggregation.py) |
| Existing tests | No regressions |
| Benchmarks | No changes |

## Estimated effort

1 session. Pure refactoring — no new features, no interface changes.
