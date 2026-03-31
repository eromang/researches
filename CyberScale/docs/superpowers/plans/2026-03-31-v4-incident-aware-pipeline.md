# v4 Implementation Plan — Incident-Aware Pipeline with Entity/Authority Separation

**Goal:** Transform CyberScale from a vulnerability assessment tool into a NIS2 incident support system with entity-facing (Phase 2 incident mode) and authority-facing (aggregation + O-model + matrix) capabilities.

**Key architecture changes:**
- Unified impact taxonomy across all phases (6 dimensions, same field names/values)
- Phase 2 gains incident mode with early warning recommendation
- IR/NIS2 model split for Phase 2
- T-model eliminated — deterministic T-level in aggregation layer
- O-model gains consequence dimensions (financial, safety, persons)
- `coordination_needs` removed from O-model (matrix output)
- `cross_border` boolean replaced with MS geography
- New MCP tools: `assess_entity_incident` (entity) + `assess_incident` (authority)

---

## Execution phases

v4 is split into 3 implementation phases to allow validation at each stage.

### Phase A: Foundation (unified taxonomy + field renames)

No new features — align existing code with v4 taxonomy. Non-breaking if done with backwards-compatible defaults.

**A1. Unified impact taxonomy reference**
- Create `data/reference/impact_taxonomy.json` with all 6 dimensions, values, and per-phase routing
- This becomes the single source of truth for field validation

**A2. Phase 3T field renames**
- `service_disruption` → `service_impact` (partial/degraded/unavailable/sustained + none)
- `data_compromise` → `data_impact` (none/accessed/exfiltrated/compromised/systemic)
- Update `technical.py`, `generate_incidents.py`, `incident.py` MCP tool, tests
- Regenerate T-model training data with new field names
- Retrain T-model

**A3. Phase 3O field fixes**
- `sectors_affected` type: str → int (match Phase 3T)
- Remove `coordination_needs` from O-model inputs
- Update `operational.py`, `generate_incidents.py`, `incident.py` MCP tool, tests
- Regenerate O-model training data
- Retrain O-model

**A4. Phase 2 field renames**
- Replace `cross_border` (bool) with `ms_established` (str) + `ms_affected` (list[str])
- Keep `cross_border` as derived for backwards compatibility during transition
- Update `contextual.py`, `generate_contextual.py`, MCP tools, tests
- Regenerate Phase 2 training data
- Retrain Phase 2 model

**A5. Run full test suite + benchmarks**
- All existing benchmarks must pass (no regressions)
- Commit + tag `cyberscale-v4a`

**Estimated effort:** 1-2 sessions

---

### Phase B: Entity-facing incident mode

New features for entity self-assessment.

**B1. Phase 2 impact inputs**
- Add to `contextual.py` predict/format_input:
  - `entity_affected` (bool)
  - `service_impact` (unified taxonomy values)
  - `data_impact` (unified taxonomy values)
  - `financial_impact` (none/minor/significant/severe)
  - `safety_impact` (none/health_risk/health_damage/death)
  - `affected_persons_count` (int)
  - `suspected_malicious` (bool)
  - `impact_duration_hours` (int)
- All optional, default to `none`/`false`/`0`
- Update generation script with impact scenarios
- Retrain Phase 2 model with impact-aware data

**B2. IR/NIS2 model split**
- Create `src/cyberscale/models/contextual_ir.py` — quantitative threshold model
- Create `data/reference/ir_incident_thresholds.json` — per-entity-type thresholds from IR Arts. 5-14
- Router logic in MCP tool: `entity_type in IR_ENTITIES → IR model, else → NIS2 model`
- IR model outputs: `significant_incident` (bool), `triggered_criteria` (list)
- NIS2 model outputs: `significant_incident` ("likely"/"unlikely"/"uncertain"), `reporting_hint` (str)
- Tests for both models + router

**B3. Early warning recommendation**
- Add `early_warning` output to Phase 2 incident mode
- Content: `recommended` (bool), `deadline` ("24h"), `required_content` (suspected_malicious, cross_border_impact), `next_step` (Art. 23(4)(b) guidance)
- Logic: if significant_incident → recommend early warning

**B4. `assess_entity_incident` MCP tool**
- Entity-facing tool: single entity, incident context → severity + significant_incident + early warning
- Wraps Phase 2 incident mode with structured output

**B5. Tests + benchmark**
- Unit tests for impact inputs, IR/NIS2 routing, early warning logic
- Curated entity incident scenarios (extend existing 40 to include impact fields)
- Commit + tag `cyberscale-v4b`

**Estimated effort:** 2-3 sessions

---

### Phase C: Authority-facing classification

New features for CSIRT Network and EU-CyCLONe.

**C1. Aggregation layer**
- Create `src/cyberscale/aggregation.py`
- Input: list of entity notification dicts (Phase 2 incident mode outputs)
- Output: aggregated fields + deterministic T-level
- Worst-case for service_impact, data_impact, financial_impact, safety_impact
- Sum for affected_persons_count
- Count for affected_entities, sectors_affected, ms_affected
- Derived: cascading (from sectors), cross_border_pattern (from MS count), capacity_exceeded (heuristic)
- T-level derivation: deterministic rules (sustained/systemic→T4, unavailable/exfiltrated→T3, etc.)
- Unit tests: 100% pass (deterministic logic)

**C2. O-model retrain with consequence dimensions**
- Add to `operational.py`:
  - `financial_impact` (none/minor/significant/severe)
  - `safety_impact` (none/health_risk/health_damage/death)
  - `affected_persons_count` (int)
  - `affected_entities` (int) — was only in T-model
- Update `generate_incidents.py` with consequence-aware scenarios
- Regenerate + retrain O-model
- Benchmark against curated scenarios

**C3. Multi-entity aggregation benchmark**
- Create 50 curated multi-entity incident scenarios
- Sources: ENISA annual reports, EU-CyCLONe summaries, vault RETEX (SolarWinds, NotPetya, WannaCry, MOVEit)
- Each scenario: 2-10 entities, expected aggregation, expected T-level, expected O-level, expected classification
- Run benchmark: aggregation (deterministic) + O-model + matrix
- Pass criteria: aggregation 100%, O-model >70%, end-to-end >70%

**C4. `assess_incident` MCP tool (authority-facing)**
- Input: incident description + list of entity notification dicts
- Runs: aggregation → T-level (deterministic) → O-model → matrix
- Output: per-entity results, aggregation, T-level with basis, O-level with key factors, matrix classification + coordination level
- Authority reviews all suggested values before final classification

**C5. Phase 3T model deprecation**
- Remove `TechnicalClassifier` from inference pipeline
- Keep model files for reference but mark as deprecated
- Update `classify_incident` MCP tool to use aggregation T-level instead
- Update all tests

**C6. Final benchmark + documentation**
- Full pipeline benchmark: entity → Phase 2 → authority → aggregation → O-model → matrix
- Update roadmap, Pipeline Reference, Excalidraw with final v4 architecture
- Commit + tag `cyberscale-v4`

**Estimated effort:** 3-4 sessions

---

## Dependency graph

```
Phase A (foundation):
  A1 (taxonomy) → A2 (3T renames) → A5 (tests)
  A1 (taxonomy) → A3 (3O fixes) → A5 (tests)
  A1 (taxonomy) → A4 (P2 renames) → A5 (tests)
  A2, A3, A4 can run in parallel after A1

Phase B (entity-facing):
  A5 → B1 (P2 impact inputs) → B2 (IR/NIS2 split) → B3 (early warning) → B4 (MCP tool) → B5 (tests)

Phase C (authority-facing):
  B5 → C1 (aggregation) → C2 (O-model retrain) → C3 (benchmark)
  C3 → C4 (MCP tool) → C5 (deprecate T-model) → C6 (final)
```

## Success criteria

| Metric | Target |
|---|---|
| Phase 2 incident mode: significant_incident accuracy (IR entities) | 100% (deterministic thresholds) |
| Phase 2 incident mode: severity accuracy (NIS2 entities) | > 75% |
| Aggregation + T-level derivation | 100% (deterministic) |
| O-model accuracy on curated multi-entity scenarios | > 70% |
| End-to-end: entities → aggregation → classification | > 70% |
| Full test suite | All pass, no regressions |
| Existing v3 benchmarks | No regressions |

## Files created/modified

**New files:**
- `data/reference/impact_taxonomy.json`
- `data/reference/ir_incident_thresholds.json`
- `src/cyberscale/models/contextual_ir.py`
- `src/cyberscale/aggregation.py`
- `evaluation/benchmark_multi_entity.py`
- `data/reference/curated_multi_entity_incidents.json`

**Modified files:**
- `src/cyberscale/models/technical.py` (field renames)
- `src/cyberscale/models/operational.py` (field renames + new fields + remove coordination_needs)
- `src/cyberscale/models/contextual.py` (impact inputs + MS geography)
- `src/cyberscale/tools/incident.py` (aggregation integration, T-model deprecation)
- `src/cyberscale/tools/vulnerability.py` (assess_entity_incident tool)
- `training/scripts/generate_incidents.py` (unified taxonomy + consequence scenarios)
- `training/scripts/generate_contextual.py` (impact scenarios + MS geography)
- All test files for modified modules
