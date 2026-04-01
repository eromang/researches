# v5 Implementation Plan — Deterministic Phase 3 + Multi-tier Architecture

**Goal:** Make Phase 3 fully deterministic (replace O-model with rules), add sector dependency-aware aggregation, split into national (3a) vs EU (3b) tiers with CyCLONe Officer inputs, and add authority feedback loop.

---

## Execution phases

### Phase A: Deterministic O-level + sector dependencies

**A1. Deterministic O-level derivation**
- Add `derive_o_level()` to `aggregation.py` (mirror `derive_t_level()`)
- Port rules from `generate_incidents.py::assign_o_level()` + add consequence escalation (financial, safety, persons)
- Returns `(o_level, basis)` with triggering rules for transparency
- Update `authority_incident.py` and `incident.py` to use `derive_o_level()` instead of O-model
- Remove O-model from inference pipeline (keep files for reference)
- Update all tests

**A2. Sector dependency graph**
- Create `data/reference/sector_dependencies.json` — directed graph from ENISA/CER sources
- Add `propagate_cascading()` to `aggregation.py`
- Replace `_derive_cascading(n_sectors)` with dependency-aware derivation
- Update aggregation tests

**A3. Tests + benchmarks**
- All aggregation tests must pass (deterministic)
- Re-run multi-entity benchmark with new rules
- Run full test suite
- Commit + tag `cyberscale-v5a`

### Phase B: Multi-tier national/EU split

**B1. Phase 3a — national incident assessment**
- Create `src/cyberscale/tools/national_incident.py` with `assess_national_incident`
- Input: entity notifications from a single MS
- Scoped aggregation (validates all entities share ms_established)
- Output: national T/O/matrix + cross_border flag

**B2. Phase 3b — EU incident assessment with CyCLONe Officers**
- Create `src/cyberscale/tools/eu_incident.py` with `assess_eu_incident`
- Input: national classification dicts (Phase 3a outputs) + CyCLONe Officer inputs
- Second-level aggregation across national assessments
- CyCLONe Officer escalation logic (escalate only, never de-escalate)
- Output: EU classification + coordination level

**B3. Authority feedback store**
- Create `data/feedback/` directory structure
- Create `src/cyberscale/feedback.py` — store/load authority decisions
- Create `evaluation/benchmark_authority_feedback.py` — regression test rules vs decisions

**B4. Tests + benchmarks**
- Unit tests for national scoping, EU aggregation, officer escalation
- Full test suite
- Commit + tag `cyberscale-v5b`

### Phase C: Cleanup + documentation

**C1. HuggingFace housekeeping**
- Deprecate T-model and O-model repos
- Publish contextual v4 model
- Publish sector dependencies dataset

**C2. Documentation updates**
- README.md, design-specification.md, enhancement-roadmap.md, lessons-learned.md
- Model READMEs
- New benchmark reports

**C3. Final tag**
- Run all tests + benchmarks
- Commit + tag `cyberscale-v5`

---

## Files created/modified

**New files:**
- `data/reference/sector_dependencies.json`
- `src/cyberscale/tools/national_incident.py`
- `src/cyberscale/tools/eu_incident.py`
- `src/cyberscale/feedback.py`
- `evaluation/benchmark_authority_feedback.py`

**Modified files:**
- `src/cyberscale/aggregation.py` (derive_o_level, sector dependencies)
- `src/cyberscale/tools/incident.py` (deterministic O-level)
- `src/cyberscale/tools/authority_incident.py` (deterministic O-level)
- `src/cyberscale/server.py` (register new tools)
- `src/cyberscale/pipeline.py` (deterministic O-level)
- All test files for modified modules
