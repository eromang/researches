# v7 Implementation Plan — Luxembourg National Layer

**Goal:** Add Luxembourg-specific incident significance thresholds (ILR sector rules) as the first national layer, proving the pluggable national module pattern.

**Architecture:** Three-tier threshold routing in Phase 2 incident mode:

```
Entity in Luxembourg (ms_established=LU)
  │
  ├── IR entity type? → IR thresholds (EU-wide, Arts. 5-14) [existing v4]
  │
  ├── LU-covered sector? → LU ILR thresholds (v7 new)
  │     Output: significant_incident (bool) + triggered_criteria
  │
  └── Neither? → NIS2 ML model (qualitative) [existing v4]
```

**Key decisions:**
- NIS1 ILR thresholds reused as LU-NIS2 thresholds (best available until Luxembourg publishes NIS2-specific rules)
- IR thresholds take precedence over LU thresholds (EU regulation > national transposition)
- New NIS2 sectors not covered by NIS1 fall back to generic EU qualitative model
- Pluggable pattern: `data/reference/{ms}_thresholds.json` for future MS

---

## LU ILR Sectors and Threshold Summary

From vault `INCIDENT_CLASSIFICATION_THRESHOLDS.md`:

| ILR Reference | Sector | Key thresholds |
|---|---|---|
| Common (all) | All NIS1 sectors | Safety risk (any), material damage ≥ EUR 50K, data loss > 50 LU users |
| ILR/N21/1 | Digital Service Providers | > 5M user-hours, > 100K EU users, > EUR 1M |
| ILR/N22/1 | Rail Transport | ≥ 5% trains cancelled, ≥ 100 slots impacted, infrastructure unavail ≥ 4h |
| ILR/N22/2 | Road Transport | Service unavail ≥ 2h, > 50 users, ≥ EUR 200K |
| ILR/N22/3 | Gas | Valve control loss, SCADA unavail ≥ 30 min, any transmission incident |
| ILR/N22/4 | Electricity | Points of delivery × duration matrix (LV/MV), any HV/EHV or SCADA incident |
| ILR/N22/5 | Health | Hospitals: ≥ 10 reversible / ≥ 1 irreversible. Labs: % analyses × duration. Emergency: delay thresholds |
| ILR/N22/6 | Digital Infrastructure | IXP: members × duration. DNS: domains × traffic × duration. .LU registry: zone/DNSSEC/availability |
| ILR/N23/1 | Air Transport | > 4 flights cancelled, ops unavail > 4h, cargo ≥ 2 flights > 24h |

**Not covered by LU NIS1 (fallback to EU qualitative):**
- Banking/financial market (DORA applies separately)
- Drinking water (ILR/N21/2 exists — include)
- Waste water (not in NIS1)
- ICT service management (not in NIS1 — IR may cover MSP/MSSP)
- Public administration, space, postal, waste, manufacturing, chemicals, food, digital providers, research (all Annex II, new in NIS2)

---

## Tasks

### Task 1: Extract LU thresholds to JSON

**Files:**
- Create: `data/reference/lu_thresholds.json`

Extract all ILR sector-specific thresholds from vault into structured JSON. Format:

```json
{
  "ms": "LU",
  "source": "ILR NIS1 transposition",
  "common_criteria": {
    "safety_risk": true,
    "material_damage_eur": 50000,
    "data_loss_users_lu": 50
  },
  "sectors": {
    "energy_electricity": {
      "reference": "ILR/N22/4",
      "thresholds": [
        {"type": "lv_pod", "pods": 100, "duration_min": 60},
        {"type": "lv_pod", "pods": 500, "duration_min": 30},
        ...
        {"type": "automatic", "condition": "hv_ehv_transmission"},
        {"type": "automatic", "condition": "scada_impact"},
        {"type": "automatic", "condition": "cross_border"}
      ]
    },
    "energy_gas": { "reference": "ILR/N22/3", ... },
    "transport_rail": { "reference": "ILR/N22/1", ... },
    "transport_road": { "reference": "ILR/N22/2", ... },
    "transport_air": { "reference": "ILR/N23/1", ... },
    "health_hospital": { "reference": "ILR/N22/5", ... },
    "health_laboratory": { "reference": "ILR/N22/5", ... },
    "health_emergency": { "reference": "ILR/N22/5", ... },
    "digital_infrastructure_ixp": { "reference": "ILR/N22/6", ... },
    "digital_infrastructure_dns": { "reference": "ILR/N22/6", ... },
    "digital_infrastructure_lu_registry": { "reference": "ILR/N22/6", ... },
    "digital_service_providers": { "reference": "ILR/N21/1", ... },
    "drinking_water": { "reference": "ILR/N21/2", ... }
  }
}
```

**Commit:** `feat(cyberscale): v7 LU ILR threshold reference data`

---

### Task 2: LU threshold assessment module

**Files:**
- Create: `src/cyberscale/national/lu.py`
- Create: `src/cyberscale/national/__init__.py`
- Create: `src/tests/national/__init__.py`
- Create: `src/tests/national/test_lu.py`

**Functions:**

```python
def is_lu_covered(sector: str, entity_type: str) -> bool:
    """Check if entity falls under LU ILR thresholds."""

def assess_lu_significance(
    sector: str,
    entity_type: str,
    service_impact: str,
    data_impact: str,
    affected_persons_count: int,
    financial_impact: str,
    safety_impact: str,
    impact_duration_hours: float,
    # Sector-specific fields (optional, used when applicable):
    pods_affected: int = 0,           # Electricity
    trains_cancelled_pct: float = 0,  # Rail
    scada_unavailable_min: int = 0,   # Gas/electricity
    members_impacted_pct: float = 0,  # IXP
    domains_unresolved_pct: float = 0, # DNS
    ...
) -> LuSignificanceResult:
    """Assess incident significance against LU ILR thresholds."""
```

**Output:**
```python
@dataclass
class LuSignificanceResult:
    significant_incident: bool
    triggered_criteria: list[str]  # e.g., ["ILR/N22/4: ≥500 LV-POD for ≥30 min"]
    ilr_reference: str             # e.g., "ILR/N22/4"
    common_criteria_met: list[str] # e.g., ["material_damage ≥ 50K EUR"]
```

**Tests:** Unit tests for each ILR sector with boundary cases (just below / at / just above threshold).

**Commit:** `feat(cyberscale): v7 LU national threshold assessment module`

---

### Task 3: Three-tier router integration

**Files:**
- Modify: `src/cyberscale/tools/entity_incident.py`

Update the `_assess_entity_incident` function to add the LU tier:

```python
if entity_type in IR_ENTITIES:
    result = assess_ir_significance(...)       # EU-wide (v4)
elif ms_established == "LU" and is_lu_covered(sector, entity_type):
    result = assess_lu_significance(...)       # LU national (v7)
else:
    result = assess_nis2_significance(...)     # EU qualitative (v4)
```

**Key design:** The router is deterministic. The LU module accepts the same unified impact taxonomy fields as IR/NIS2 plus optional sector-specific fields.

**Commit:** `feat(cyberscale): v7 three-tier router (IR → LU → NIS2)`

---

### Task 4: Sector-specific input fields for LU

**Files:**
- Modify: `src/cyberscale/tools/entity_incident.py` (MCP tool signature)

Some LU thresholds require sector-specific inputs not in the unified taxonomy:

| LU sector | Additional input | Type | Example |
|---|---|---|---|
| Electricity | `pods_affected` | int | 500 LV-POD |
| Electricity | `voltage_level` | str | lv / mv / hv_ehv |
| Rail | `trains_cancelled_pct` | float | 5.0 |
| Rail | `slots_impacted` | int | 100 |
| Gas | `scada_unavailable_min` | int | 30 |
| Health | `persons_health_impact` | int | 10 (reversible) |
| Health | `analyses_affected_pct` | float | 50 |
| IXP | `members_impacted_pct` | float | 50 |
| DNS | `domains_unresolved_pct` | float | 25 |
| Air | `flights_cancelled` | int | 4 |

These are passed as an optional `sector_specific` dict in the MCP tool — only relevant when `ms_established=LU` and the sector matches.

**Commit:** `feat(cyberscale): v7 LU sector-specific input fields`

---

### Task 5: Pluggable national module pattern

**Files:**
- Create: `src/cyberscale/national/registry.py`

```python
NATIONAL_MODULES = {
    "LU": ("cyberscale.national.lu", "assess_lu_significance", "is_lu_covered"),
    # Future: "DE": ("cyberscale.national.de", ...),
}

def get_national_module(ms: str):
    """Return national assessment function if available, None otherwise."""
```

The router in Task 3 uses this registry instead of hardcoding `ms == "LU"`.

**Commit:** `feat(cyberscale): v7 pluggable national module registry`

---

### Task 6: Tests + benchmark

**Files:**
- Create: `src/tests/national/test_lu.py` (detailed per-sector)
- Create: `evaluation/benchmark_lu.py`
- Create: `data/reference/curated_lu_incidents.json` (20 curated LU scenarios)

**Curated LU scenarios:** Real or realistic incidents at Luxembourg entities, each with expected ILR threshold outcome:
- POST Luxembourg electricity (LV-POD threshold)
- LuxTrust (trust services — IR, not LU)
- CFL rail (train cancellation threshold)
- Luxembourg hospital (health impact threshold)
- .LU registry (DNS/DNSSEC threshold)
- LU-IX IXP (member impact threshold)
- Luxair (flight cancellation threshold)

**Benchmark criteria:**
- LU threshold assessment: 100% (deterministic)
- Three-tier routing correctness: 100%
- IR entities in LU correctly bypass LU thresholds: 100%
- Non-covered sectors correctly fall back to NIS2 ML: 100%

**Commit:** `bench(cyberscale): v7 Luxembourg threshold benchmark`

---

### Task 7: Documentation + tag

- Update roadmap with v7 completed
- Update design specification with national layer architecture
- Update Pipeline Reference with three-tier routing
- Tag `cyberscale-v7`

**Commit:** `docs(cyberscale): v7 Luxembourg national layer complete`

---

## Dependency graph

```
Task 1 (JSON) → Task 2 (LU module) → Task 3 (router) → Task 6 (tests)
                Task 2 → Task 4 (sector fields)
                Task 2 → Task 5 (registry)
                Task 3, 4, 5 → Task 6 → Task 7
```

Tasks 4 and 5 can run in parallel after Task 2.

## Success criteria

| Metric | Target |
|---|---|
| LU threshold assessment accuracy | 100% (deterministic) |
| Three-tier routing correctness | 100% |
| Curated LU scenarios (20) | 20/20 correct |
| Existing tests | No regressions |
| IR entities in LU | Correctly use IR, not LU thresholds |
| Non-covered LU sectors | Correctly fall back to NIS2 ML |

## Estimated effort

2-3 sessions. No ML training — entirely deterministic threshold logic.
