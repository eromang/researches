# CyberScale — Enhancement Roadmap

Concrete enhancement paths prioritised by expected impact. Updated after v5 implementation.

---

## v8 completed (2026-04-03)

| Enhancement | Layer | Result |
|-------------|-------|--------|
| HCPN national crisis qualification (incidents) | National | 3 cumulative criteria, fast-track provision, cooperation mode |
| HCPN national crisis qualification (threats) | National | 4 cumulative criteria (adds probability assessment) |
| Large-scale determination | National | cross_border OR capacity_exceeded -> large_scale level |
| Undetermined criteria handling | National | Explicit "undetermined"/"bypassed" for delegated thresholds, recommend_consultation |
| Sector dependency graph for interdependency check | National | Uses existing sector_dependencies.json for economic consequences sub-criterion |
| Curated HCPN scenarios (15) | National | 15/15 correct (10 incidents + 5 threats) |
| MCP tools: assess_lu_crisis_incident, assess_lu_crisis_threat | National | Authority-level tools scoped to impact on Luxembourg |

---

## v4 completed (2026-04-01)

| Enhancement | Phase | Result |
|-------------|-------|--------|
| Unified impact taxonomy (service_impact, data_impact, etc.) | All | Single source of truth across phases |
| Entity/authority separation | 2+3 | assess_entity_incident + assess_incident MCP tools |
| IR/NIS2 model split | 2 | Deterministic thresholds for 14 IR entity types |
| Early warning recommendation | 2 | Art. 23(4)(a) 24h deadline + structured guidance |
| Deterministic T-level | 3 | T-model deprecated; derive_t_level() from impact fields |
| O-model consequence dimensions | 3 | +financial_impact, safety_impact, persons, entities |
| Multi-entity aggregation | 3 | Worst-case + count/sum + deterministic cascading/cross-border |
| MS geography (ms_established + ms_affected) | 2 | Replaces cross_border bool |
| coordination_needs removed | 3 | Was output, not observable input |
| 50 curated multi-entity scenarios | 3 | 100% aggregation, 100% matrix accuracy |

---

## v3 completed (NIS2 entity types)

| Enhancement | Phase | Result |
|-------------|-------|--------|
| 55+ NIS2-aligned entity types (Annex I/II) | 2 | entity_type replaces deployment_scale |
| CER critical entity flag | 2 | +1 escalation for CER-eligible entities |
| Per-entity-type validation | 2 | ValueError for unknown types |

---

## v5 completed (2026-03-31)

| Enhancement | Phase | Result | Tag |
|-------------|-------|--------|-----|
| Deterministic O-level (`derive_o_level()`) — O-model replaced | 3 | Phase 3 fully deterministic, zero ML models | cyberscale-v5a |
| Sector dependency graph (`sector_dependencies.json`) | 3 | Cascading propagation based on inter-sector dependencies | cyberscale-v5a |
| Authority feedback store (`feedback.py`) + regression benchmark | 3 | Rule calibration from authority override decisions | cyberscale-v5a |
| Multi-tier: Phase 3a (`assess_national_incident`) + Phase 3b (`assess_eu_incident`) | 3 | National CSIRT (single MS) + EU-CyCLONe (Officers) | cyberscale-v5b |

---

## v5 remaining targets

### 5. HuggingFace housekeeping

v5 changes the model inventory. HuggingFace repos need to be updated accordingly:

| Action | Repo | Reason |
|--------|------|--------|
| **Deprecate** | `eromang/cyberscale-technical-v1` | T-model replaced by deterministic `derive_t_level()` in v4. Mark as deprecated, add README notice |
| **Update** | `eromang/cyberscale-operational-v1` → `v5` | Retrain not needed if O-model replaced by deterministic rules. If kept, publish v5 with consequence dimensions |
| **Remove or deprecate** | `eromang/cyberscale-operational-v1` | If O-model is replaced by deterministic rules, deprecate. Keep for reference |
| **Update** | `eromang/cyberscale-contextual-v1` → `v4` | Already retrained with impact inputs + MS geography. Publish v4 weights |
| **Publish** | `eromang/cyberscale-training-cves` | Update dataset card with CVSS vector columns if multi-task implemented |
| **New** | `eromang/cyberscale-sector-dependencies` | Publish sector dependency graph as a standalone reference dataset |

### 6. Documentation updates (v5 completion checklist)

After v5 implementation, update all documentation to reflect the final state:

| Document | Updates needed |
|----------|---------------|
| `README.md` | Phase 3a/3b split, deterministic O-level, sector dependencies, CyCLONe Officer inputs, updated MCP tools table, usage examples |
| `docs/design-specification.md` | Multi-tier architecture (3a/3b), updated models table (O-model deprecated or deterministic), new design decisions |
| `docs/enhancement-roadmap.md` | Move v5 targets to completed section, update model performance table |
| `docs/lessons-learned.md` | Add v5 lessons (deterministic O-model outcome, sector dependency calibration, multi-tier learnings) |
| `data/models/operational/README.md` | Deprecation notice if replaced, or v5 update if kept |
| `evaluation/*.md` | New benchmark reports for multi-tier pipeline |
| HuggingFace model cards | Deprecation/update notices per housekeeping table above |

### 7. Other v5 candidates

| Enhancement | Phase | Impact | Effort |
|-------------|-------|--------|--------|
| Real incident validation dataset | All | Validate against actual ENISA/CSIRT reports | High (data) |
| Phase 1 CVSS vector multi-task learning | 1 | Expected +5-10pp on band accuracy | Medium |
| National layer (per-MS thresholds) | 2 | On hold — only Luxembourg rules available; not generalizable to other MS yet | Medium |

### Future (v6+): Incident lifecycle management

| Enhancement | Phase | Impact | Effort |
|-------------|-------|--------|--------|
| Standardized Art. 23 notification schema | 2 | Structured input per notification stage (early warning/72h/final) — prerequisite for temporal tracking | Medium |
| Temporal incident tracking (initial→update→final) | 2+3 | Support evolving incidents with state between calls, incident timeline | High |

These form a natural group with the secure notification channel (documented below) — schema defines the format, temporal tracking manages the lifecycle, secure channel handles transport. Deferred until a CSIRT pilot or real user validates the need.

---

## v2 completed enhancements

| Enhancement | Phase | Result |
|-------------|-------|--------|
| Human-curated incident benchmark (40 incidents) | 3 | Matrix: 67.5% -> 97.5% |
| Low-severity calibration (T1/O1 rules + curated mix) | 3 | T1 F1: 0 -> 0.88, O1 F1: 0.09 -> 1.00 |
| Deployment scale + entity type features | 2 | non_nis2: 65.3% -> 76.5% (+11.2pp) |
| CWE as first-class feature | 1 | 60.2% (flat — confirmed bottleneck is data quality, not features) |
| Composable pipeline (Phase 1 -> 2 -> 3) | All | `assess_full_pipeline` MCP tool, automatic score forwarding |
| MC dropout reduction (20 -> 5 passes) | All | 4x inference speedup, no accuracy loss |
| Cross-model consistency warnings | 3 | T4/O1 and T1/O4 asymmetry flagged |

---

## Current model performance (v8)

| Phase | Model | Key metric | Target | Status |
|-------|-------|------------|--------|--------|
| 1 | Scorer v6 (multi-task) | 62.3% band accuracy | > 75% | Not met (ceiling) |
| 2 | Contextual (v4) | 81.5% macro F1 | > 75% | Met |
| 2 | IR thresholds (v4) | 100% | 100% | Met |
| 2 | LU national thresholds (v7) | 100% (20/20 curated) | 100% | Met |
| 2 | BE national thresholds | 100% (10/10 curated) | 100% | Met |
| 2 | Three-tier routing (v7) | 100% (20/20 curated) | 100% | Met |
| National | LU HCPN crisis qualification (v8) | 100% (15/15 curated) | 100% | Met |
| 3 | T-level (deterministic) | 100% | 100% | Met |
| 3 | O-level (deterministic) | 100% | 100% | Met |
| 3 | Matrix end-to-end (deterministic) | 100% | > 70% | Met |
| 3 | Multi-entity (50 curated) | 100% | > 70% | Met |
| 3 | Illustrative use cases | 6/6 | 6/6 | Met |

**Phase 1 is the weakest phase.** CWE (v2), multi-task (v6), and CPE (v6) all failed to break past 62%. The ceiling is CVE description quality — many CVE descriptions are formulaic regardless of actual severity. Further gains require different data sources, not architecture changes.

---

## Remaining enhancements

### High priority — Phase 1 accuracy (biggest gap)

#### ~~1. CVSS vector multi-task learning~~ → completed in v6

+1.8pp band accuracy (60.5% → 62.3%). Did not reach 70% target. The ceiling is description quality, not architecture.

#### ~~2. Product/vendor signal~~ → tested in v6 Task 5, rejected

CPE vendor/product added no improvement (62.7% ≈ 62.3%). CVSS scoring is product-agnostic; the model correctly ignores vendor/product.

#### 3. Contrastive pre-training

Before fine-tuning for classification, train a contrastive objective: CVEs in the same CVSS band should have similar embeddings. This gives ModernBERT better vulnerability-domain representations before the classification head sees them.

**Effort:** Medium — requires two-stage training pipeline.
**Expected gain:** +3-5pp — better feature space.

#### 4. Curriculum learning

Train on easy examples first (clear Critical vs clear Low), then progressively introduce boundary cases. The model currently struggles most at the 6.5-7.5 and 3.5-4.5 boundaries.

**Effort:** Low — modify training loop ordering.
**Expected gain:** +2-3pp on boundary cases.

### Medium priority — Phase 2 depth

#### 5. Generate more small-deployment/non_nis2 scenarios

non_nis2 improved to 76.5% but remains the weakest sector. Generate 500+ additional small-deployment/enterprise scenarios with human-quality labels.

**Effort:** Medium — requires scenario generation sessions.
**Expected gain:** +5-10pp on non_nis2/small-deployment.

#### 6. Calibrated escalation rules

Replace binary trigger match (escalate/don't) with probability-weighted escalation per trigger type. "availability" in health should escalate more often than "integrity" in health.

**Effort:** Medium — statistical analysis of predecessor data, then regeneration.
**Expected gain:** More realistic training distribution.

#### 7. Richer cross-border encoding

Currently binary true/false. Replace with 4-level: `single_site` / `national` / `2_ms` / `3plus_ms`. Captures the difference between operating in 2 EU states vs 15.

**Effort:** Low — input format change + retrain.
**Expected gain:** +2-3pp on cross-border scenarios.

### Medium priority — Phase 3 robustness

#### 8. LLM description augmentation

The 50 base templates with synonym substitution produce limited lexical diversity. Use an LLM to generate 200+ description templates from seed scenarios, producing richer paraphrase patterns.

**Effort:** Medium — LLM generation pipeline + quality filtering.
**Expected gain:** Reduces template memorisation risk.

#### 9. Temporal decay features

Real incidents evolve over time — a T2 at hour 0 may become T4 by hour 12. Add optional `hours_since_detection` input field that captures incident progression.

**Effort:** Medium — new input feature, generation rules, retrain.
**Expected gain:** New capability (incident progression modelling).

#### 10. Expand curated incident dataset

Current benchmark has 40 incidents. Expand to 100-200 from ENISA annual reports, EU-CERT-first advisories, and vault RETEX notes. More data = more reliable benchmark and better training signal when mixed.

**Effort:** High — manual curation and expert labelling.
**Expected gain:** More reliable real-world metrics.

### Low priority — Infrastructure

| Enhancement | Impact | Effort |
|-------------|--------|--------|
| **Active learning loop** — deploy MCP server, collect analyst corrections, retrain monthly | High (long-term) | Medium |
| **EUVD enrichment** — cross-reference EU-specific severity assessments not in NVD | Medium | Low |
| **Explanation quality** — attention weights or auxiliary model for input-level explanations | Medium | High |
| **Batch inference API** — batch endpoint for analysts processing incident queues | Low | Low |
| **Ensemble with rule-based baseline** — regex/keyword scorer ensembled with model | Low | Low |

### New — Technical debt (identified v8 review)

#### ~~11. Input validation at MCP boundaries~~ → deferred

Tools accept `list[dict]` without schema validation. Missing keys cause silent failures or AttributeErrors. Add Pydantic models for all MCP inputs with consistent `ErrorResponse` schema.

**Effort:** Medium — define models, update all tools.
**Expected gain:** Robustness, better error messages for users.

**Status:** Deferred — FastMCP doesn't use Pydantic; adding it would change tool signatures. Current manual validation in tools is sufficient.

#### ~~12. Centralize hardcoded values~~ → completed

MC passes (5), max length (192/256), confidence thresholds (0.3/0.7), `VALID_SECTORS`, `VALID_ENTITY_TYPES` are scattered across modules. Some are hardcoded in Python while the authoritative source is reference JSON.

**Effort:** Low — extract to config module, load from reference data.
**Expected gain:** Single source of truth, prevents drift.

**Status:** Completed — `config.py` loads VALID_SECTORS and VALID_ENTITY_TYPES from reference JSON. VALID_*_IMPACT, MC_PASSES, MAX_LENGTH, confidence thresholds centralized. Duplicate VALID_SECTORS removed.

#### ~~13. Structured logging at decision points~~ → completed

No debug logging in classification functions. Can't trace why an incident got T3 vs T2 without reading source. Add structured logging for routing decisions, criterion evaluations, escalation triggers.

**Effort:** Low — add logging at key decision points.
**Expected gain:** Operational observability for CSIRT analysts.

**Status:** Completed — `logging.getLogger('cyberscale.*')` at entity_incident routing, HCPN criterion evaluation, T/O level derivation, and cascading propagation.

### New — National layer expansion

#### ~~14. Second member state module~~ → completed

The pluggable national module architecture (v7) is proven for Luxembourg. Adding a second MS (DE, FR, BE) would validate the pattern and surface any hidden coupling. Requires per-MS regulatory threshold data.

**Effort:** Medium per MS — data curation is the bottleneck.
**Expected gain:** Validates multi-MS architecture, expands coverage.

**Status:** Completed — Belgium (CCB NIS2 v1.3) added as second national module. Horizontal thresholds: EUR 250K financial, 20% users/1h availability, malicious CIA compromise, third-party damage. DORA carve-out for banking. 10/10 curated scenarios passing.

#### 15. HCPN cyber threat intelligence integration

v8 threat qualification accepts probability as a bare analyst input. Could integrate with MISP or CIRCL threat intelligence feeds to suggest probability levels based on active indicators, TTPs, and threat actor attribution.

**Effort:** Medium — MISP API integration + probability mapping.
**Expected gain:** Evidence-based probability assessment vs pure analyst judgment.

### New — Operational readiness

#### 16. Real incident validation expansion

v8 introduced 10 RETEX incidents (5 LU concordant). Target 50+ incidents from ENISA annual reports, EU-CyCLONe exercise debriefs, and vault RETEX notes. Quarterly benchmarking against real data.

**Effort:** High — manual extraction + expert mapping.
**Expected gain:** Confidence in production accuracy; identifies systematic rule gaps.

#### 17. CSIRT operational pilot

All validation is synthetic or retrospective. Deploy with a real CSIRT (CIRCL or GOVCERT.LU) for operational feedback. Collect authority corrections on classifications via the existing feedback store.

**Effort:** High — deployment + partnership + feedback loops.
**Expected gain:** Production-validated classifications, active learning data.

#### 18. Temporal incident tracking

Incidents evolve: early warning (24h) → notification (72h) → intermediate → final (1 month). CyberScale has no state management. Implement incident state machine with update history and evolving assessments.

**Effort:** High — state machine + audit trail + schema design.
**Expected gain:** New capability (incident lifecycle management).

---

## v3 — NIS2-aligned entity types (in progress)

### Design decisions

**Replace generic entity types with NIS2 Annex I+II entity types (~59 types).** The 8 generic values (`individual`, `sme`, `msp`, `hospital`, `cloud_provider`, `utility`, `government`, `bank`) are replaced by specific entity types derived from NIS2 Directive Annexes (e.g., `healthcare_provider`, `transmission_system_operator`, `credit_institution`). Each entity type is sector-locked: a `healthcare_provider` only appears with `sector=health`.

**Remove `deployment_scale` — entity type encodes scale implicitly.** The 4 generic deployment scales (`individual`, `small_business`, `enterprise`, `critical_operator`) were a v2 proxy for what the entity type now captures directly. A `transmission_system_operator` is inherently critical-scale. A `generic_sme` is inherently small-scale. Keeping both would be redundant and add noise. NIS2 Article 2 size-cap thresholds (medium/large enterprise) and Article 3 essential/important classification are encoded in the entity type's annex and `nis2_status` metadata, not as a separate input feature.

**Add `cer_critical_entity` boolean for CER Directive essential-override.** Under NIS2 Article 3(1)(f), entities designated as critical under the CER Directive (EU 2022/2557) are automatically essential regardless of their Annex II status. This is modelled as an optional boolean input (`cer_critical_entity`) that triggers +1 escalation for Annex II entities. The reference JSON flags which entity types are `cer_eligible` (i.e., in sectors covered by CER). `cer_critical_entity` is distinct from `cer_eligible`: eligible means the entity type *could* be CER-designated; the boolean means it *has been* designated by a Member State.

**`cross_border` remains unchanged.** Cross-border impact is a runtime field provided by the entity during incident reporting (NIS2 Art. 23(3)), not a property of the entity type. It stays as a boolean input to Phase 2.

### Expected impact

| Change | Expected effect |
|--------|-----------------|
| NIS2 entity types | More realistic sector-entity combinations, better signal for model |
| Remove `deployment_scale` | Fewer features, less noise, cleaner input |
| CER critical entity | Captures essential-override pathway, ~10% of CER-eligible scenarios |
| Sector-locked entity selection | Eliminates impossible combinations (e.g., `hospital` in `energy`) |

### Implementation

Plan: `docs/superpowers/plans/2026-03-31-nis2-entity-types.md`

Reference data: `data/reference/nis2_entity_types.json`

---

## v4 — Entity/Authority Separation + NIS2 Incident Support

v4 reframes CyberScale around two distinct user perspectives aligned with NIS2 roles:

- **Entity perspective (Phase 1 + 2):** "Is this a significant incident? Should I send an early warning?"
- **Authority perspective (Phase 3 + Matrix):** "What is the EU-level classification? What coordination is needed?"

This addresses four architectural gaps:
1. Phase 2 has no awareness of whether the entity is actually affected
2. Phase 3 is used as an entity tool but is actually an authority tool (aggregates multiple entity reports)
3. `coordination_needs` is an input to Phase 3 O-model but is actually an **output** of the Blueprint Matrix
4. Impact taxonomy is inconsistent between Phase 2 and Phase 3

### Architecture: who uses what

| Stage | Timing | CyberScale tool | User | NIS2 role | Question |
|---|---|---|---|---|---|
| Pre-incident | Before exploitation | Phase 1 + Phase 2 (vulnerability mode) | Entity / analyst | Risk assessment | "How severe is this CVE in our deployment?" |
| Early warning | 0-24h | Phase 2 (incident mode) | **Entity** | Art. 23(4)(a) notifier | "Is this significant? Should I notify?" |
| Incident notification | 24-72h | Phase 2 (updated assessment) | **Entity** | Art. 23(4)(b) notifier | "Updated assessment with more data" |
| Crisis classification | 72h+ | **Phase 3 + Matrix** | **Authority / CSIRT** | NIS2 Art. 14-16 | "What is the EU-level response?" |

Phase 2 and Phase 3 do **not chain automatically**. The authority manually feeds entity reports into Phase 3.

### Design corrections

**1. Entity/authority separation.** Phase 2 is entity-facing (single entity, single incident, "should I report?"). Phase 3 is authority-facing (multiple entity notifications aggregated, "what coordination level?"). The `assess_incident` MCP tool is an authority tool, not an entity tool.

**2. Remove `coordination_needs` from Phase 3 O-model inputs.** Coordination is determined by the matrix output:

| Matrix result | Coordination (output, not input) |
|---|---|
| Below threshold | National CSIRT only |
| Significant | Art. 23 reporting to competent authority + CSIRT |
| Large-scale | EU-CyCLONe activated (NIS2 Art. 16) |
| Cyber crisis | IPCR activated (Council level) |

**3. Replace `cross_border` boolean with concrete MS geography.** Per entity: `ms_established` (str) + `ms_affected` (list[str]).

**4. Unified impact taxonomy across Phase 2 and Phase 3.** Same field names and values — no translation between phases.

**5. Phase 2 works in two modes** aligned with NIS2 reporting phases. Optional fields default to `none` — early warning mode has fewer fields populated.

### Entity-facing tools (Phase 1 + 2)

#### 1. Unified impact taxonomy

All phases use the same field names and values. Six impact dimensions aligned with NIS2 Art. 23(3) and Implementing Regulation (EU) 2024/2690:

| Dimension | Values | Phase 2 (per entity) | Phase 3T (aggregated) | Phase 3O (aggregated) | NIS2 source |
|---|---|---|---|---|---|
| `service_impact` | none / partial / degraded / unavailable / sustained | Input | Worst-case | — | Art. 23(3), IR Arts. 5-14 |
| `data_impact` | none / accessed / exfiltrated / compromised / systemic | Input | Worst-case | — | Art. 23(3), IR Arts. 5-14 |
| `financial_impact` | none / minor / significant / severe | Input | — | Worst-case | Art. 23(3), IR Art. 3(1)(a) |
| `safety_impact` | none / health_risk / health_damage / death | Input | — | Worst-case | Art. 23(3), IR Art. 3 |
| `physical_access_breach` | bool | Input (IR only) | — | — | IR Arts. 8, 14 |
| `affected_persons_count` | int | Input | — | Aggregated sum | IR Arts. 7-14, Art. 23(3) |

**Design principle:**
- **Phase 3T** (technical severity) uses: `service_impact` + `data_impact` — observable technical damage
- **Phase 3O** (operational severity) uses: `financial_impact` + `safety_impact` + `affected_persons_count` — societal/operational consequence
- **Phase 2** collects all dimensions per entity; aggregation routes each to the right Phase 3 model

**Sustained = unavailable + duration.** `sustained` means unavailable > 24h. Phase 2 also accepts `impact_duration_hours` (int) to determine whether `unavailable` should be escalated to `sustained` during aggregation.

**Effort:** Medium — define shared enums, update Phase 2 + Phase 3 inputs, regenerate training data.

### 2. Per-entity inputs for Phase 2

Each entity in an incident provides:

**Common inputs (all entities):**

| Input | Type | Values | Description |
|-------|------|--------|-------------|
| `entity_affected` | bool | true/false | Vulnerability confirmed exploited |
| `service_impact` | str | none / partial / degraded / unavailable / sustained | Service availability impact |
| `data_impact` | str | none / accessed / exfiltrated / compromised / systemic | Data confidentiality/integrity impact |
| `financial_impact` | str | none / minor / significant / severe | Financial loss assessment |
| `safety_impact` | str | none / health_risk / health_damage / death | Physical safety impact |
| `impact_duration_hours` | int | 0+ | Hours since impact started |
| `affected_persons_count` | int | 0+ | Number of affected users/persons |
| `ms_established` | str | ISO 3166-1 alpha-2 | MS where entity is established |
| `ms_affected` | list[str] | ISO 3166-1 alpha-2 | MS where services are impacted |

**Effort:** Medium — new input fields, training data generation, retrain.

### 2. IR/NIS2 model split with router

Split Phase 2 into two specialised models behind a deterministic router:

```
Phase 2 Router
  │
  ├── entity_type in IR_ENTITIES? ──→ Phase 2-IR model (quantitative)
  │     Additional inputs: unavailability_duration_min, affected_users_pct,
  │       affected_users_count, financial_loss_eur, malicious_access
  │     Output: severity + significant_incident (bool) + triggered_criteria
  │
  └── all other entities ──→ Phase 2-NIS2 model (qualitative)
        Inputs: common impact fields
        Output: severity + reporting_hint (advisory)
```

**IR entities (11 types):** `dns_service_provider`, `tld_registry`, `cloud_computing_provider`, `data_centre_operator`, `cdn_provider`, `managed_service_provider`, `managed_security_service_provider`, `online_marketplace_provider`, `search_engine_provider`, `social_network_provider`, `trust_service_provider`

**Why split:**
- IR model trained on precise Implementing Regulation (EU) 2024/2690 threshold rules (Arts. 5-14) → definitive `significant_incident` output
- NIS2 model not polluted by IR-specific numeric features irrelevant to hospitals or utilities
- Unified MCP interface — caller doesn't know which model runs

**Effort:** High — two models, new training data, threshold reference data, router logic.

### 3. Entity-specific threshold reference data

Create `data/reference/ir_incident_thresholds.json` with per-entity-type thresholds:

```json
{
  "dns_service_provider": {
    "article": 5,
    "complete_unavailability_min": 30,
    "degraded_response_sec": 10,
    "degraded_duration_min": 60,
    "data_scope_domains": 1000,
    "data_scope_pct": 1.0
  },
  "tld_registry": {
    "article": 6,
    "complete_unavailability_min": 0
  },
  "trust_service_provider": {
    "article": 14,
    "complete_unavailability_min": 20,
    "cumulative_unavailability_min_per_week": 60,
    "affected_users_pct": 1.0,
    "affected_users_count": 200000,
    "data_scope_pct": 0.1,
    "data_scope_count": 100
  }
}
```

**Effort:** Low — structured extraction from existing vault reference data.

#### 4. Phase 2 incident mode + early warning recommendation

Phase 2 operates in two modes based on available information:

| Mode | Timing | Minimum inputs | Output |
|---|---|---|---|
| **Vulnerability** | Pre-incident | description, sector, entity_type, score | Contextual severity |
| **Incident** | 0-24h+ | description, sector, entity_type, entity_affected=true, service_impact | Severity + significant_incident assessment + early warning recommendation |

Both modes use the same model — optional fields default to `none`. Incident mode simply has impact fields populated.

**Incident mode output:**

For IR entities (definitive — quantitative thresholds):
```json
{
  "severity": "Critical",
  "significant_incident": true,
  "basis": "IR Art. 7: cloud service unavailable > 30 min",
  "early_warning": {
    "recommended": true,
    "deadline": "24h from becoming aware",
    "required_content": {
      "suspected_malicious": true,
      "cross_border_impact": true,
      "cross_border_ms": ["LU", "DE", "BE"]
    },
    "next_step": "Incident notification within 72h with initial assessment + IoCs"
  }
}
```

For NIS2 entities (advisory — qualitative criteria):
```json
{
  "severity": "Critical",
  "significant_incident": "likely",
  "basis": "Art. 23(3)(a): service unavailable at essential entity",
  "early_warning": {
    "recommended": true,
    "deadline": "24h from becoming aware",
    "required_content": {
      "suspected_malicious": true,
      "cross_border_impact": false
    },
    "advisory": "Consult competent authority if uncertain"
  }
}
```

Key distinction:
- IR entities: `significant_incident: true/false` (definitive)
- NIS2 entities: `significant_incident: "likely"/"unlikely"/"uncertain"` (advisory — final determination by competent authority)

**`assess_entity_incident` MCP tool (entity-facing):**

Single entity assesses one incident. Input: entity context + observed impact. Output: significant_incident assessment + early warning recommendation.

**Effort:** Medium — incident mode training data, early warning output logic, new MCP tool.

---

### Authority-facing tools (Aggregation + O-model + Matrix)

The authority manually enters entity notification data received through national reporting channels and CSIRT Network communication. **Phase 3T is eliminated** — the T-level becomes a deterministic derivation from the entered data, because all T-level inputs (service_impact, data_impact, affected_entities, sectors, cascading) are observable facts that map mechanically to T1-T4. The authority reviews all suggested values before proceeding.

Phase 3O (operational severity) remains as an ML model because operational severity requires **judgment** — the same entity count and MS count can warrant different O-levels depending on entity relevance, financial impact, and safety consequences.

#### 5. Aggregation layer (replaces Phase 3T)

The authority feeds entity notifications into the aggregation layer, which:
1. Computes worst-case/counts/sums from entity reports
2. **Derives T-level deterministically** (no ML model)
3. Feeds O-model inputs

**T-level derivation rules (deterministic):**

| T-level | Condition |
|---|---|
| T4 | `service_impact` = sustained OR `data_impact` = systemic OR (unavailable + uncontrolled cascading) |
| T3 | `service_impact` = unavailable OR `data_impact` = exfiltrated OR cross_sector cascading OR entities > 50 |
| T2 | `service_impact` = degraded OR `data_impact` = accessed OR limited cascading OR entities > 10 |
| T1 | Everything else |

These are the same rules that were used to generate Phase 3T training data — the model simply learned them. A deterministic lookup is faster, 100% predictable, and has no model to maintain.

**Full aggregation output:**

| Field | Aggregation rule | Destination | Example |
|---|---|---|---|
| `service_impact` | Worst-case (+ duration → sustained) | T-level derivation | "unavailable" |
| `data_impact` | Worst-case | T-level derivation | "compromised" |
| `affected_entities` | Count where entity_affected=true | T-level + O-model | 2 |
| `sectors_affected` | Count distinct sectors | T-level + O-model | 2 |
| `cascading` | Derived from sectors count | T-level derivation | "cross_sector" |
| **`t_level`** | **Deterministic from above** | **Matrix** | **T3** |
| `entity_relevance` | Highest (from entity_type mapping) | O-model | "essential" |
| `ms_affected` | Count distinct MS from ms_affected[] union | O-model | 3 |
| `cross_border_pattern` | Derived from MS count | O-model | "significant" |
| `financial_impact` | Worst-case | O-model | "severe" |
| `safety_impact` | Worst-case | O-model | "health_risk" |
| `affected_persons_count` | Sum | O-model | 50500 |
| `capacity_exceeded` | Heuristic | O-model | false |

#### 6. O-model retrain

The O-model is the **only remaining ML model** in the authority pipeline. It predicts operational severity from consequence and scope indicators that require judgment.

**O-model inputs (v4):**

| Input | Source | Change from v3 |
|---|---|---|
| `description` | Enriched with entity summaries | Existing |
| `affected_entities` | Aggregated count | **New** (was only in T-model) |
| `sectors_affected` | Aggregated count (int, not str) | **Type fixed** |
| `entity_relevance` | From entity_type mapping | Existing |
| `ms_affected` | From ms_affected[] union | Existing |
| `cross_border_pattern` | Derived from ms_affected count | Existing |
| `capacity_exceeded` | Heuristic default | Existing |
| `financial_impact` | Aggregated worst-case | **New** |
| `safety_impact` | Aggregated worst-case | **New** |
| `affected_persons_count` | Aggregated sum | **New** |

**Removed:** `coordination_needs` (matrix output, not input).
**Added:** `financial_impact`, `safety_impact`, `affected_persons_count`, `affected_entities`.

**Effort:** Medium — retrain O-model with new fields, regenerate training data. T-model eliminated.

#### 7. `assess_incident` MCP tool (authority-facing)

Authority tool: entity notifications → aggregation (with deterministic T-level) → O-model → matrix → classification + coordination:

```
assess_incident(
    description="Supply chain compromise of cloud provider software update",
    entities=[
        {entity_type: "cloud_computing_provider", sector: "digital_infrastructure",
         entity_affected: true,
         service_impact: "unavailable", data_impact: "compromised",
         financial_impact: "severe", safety_impact: "none",
         impact_duration_hours: 2, affected_persons_count: 50000,
         ms_established: "LU", ms_affected: ["LU", "DE", "BE"]},
        {entity_type: "healthcare_provider", sector: "health",
         entity_affected: true,
         service_impact: "degraded", data_impact: "none",
         financial_impact: "minor", safety_impact: "health_risk",
         impact_duration_hours: 2, affected_persons_count: 500,
         ms_established: "DE", ms_affected: ["DE"]},
    ],
)
```

**Output:**

```json
{
  "phase2": {
    "entity_results": [
      {"entity_type": "cloud_computing_provider", "model": "IR",
       "severity": "Critical", "significant_incident": true,
       "triggered_criteria": ["Art. 7: unavailability > 30min"]},
      {"entity_type": "healthcare_provider", "model": "NIS2",
       "severity": "High",
       "reporting_hint": "Service degraded at essential entity, health risk"}
    ]
  },
  "aggregation": {
    "service_impact": "unavailable",
    "data_impact": "compromised",
    "affected_entities": 2,
    "sectors_affected": 2,
    "cascading": "cross_sector",
    "t_level": "T3",
    "t_level_basis": "unavailable + compromised + cross_sector cascading",
    "entity_relevance": "essential",
    "ms_affected": 3,
    "cross_border_pattern": "significant",
    "financial_impact": "severe",
    "safety_impact": "health_risk",
    "affected_persons_count": 50500,
    "capacity_exceeded": false
  },
  "operational": {
    "level": "O3",
    "key_factors": ["essential entity", "3 member states",
                    "significant cross-border", "severe financial impact",
                    "health_risk", "50500 persons affected"]
  },
  "matrix": {
    "classification": "large_scale",
    "label": "Large-scale",
    "provision": "7(c)",
    "coordination": "EU-CyCLONe activated (NIS2 Art. 16)"
  }
}
```

**Key design principles:**
- T-level is in `aggregation` (deterministic), not a separate `phase3.technical` section
- `coordination` is in the matrix output, not an input
- O-level is the only ML prediction in the authority pipeline

**Effort:** High — new MCP tool with multi-entity orchestration, aggregation, and O-model inference.

#### 8. Multi-entity aggregation benchmark

Before building the full `assess_incident` MCP tool, validate that multi-entity aggregation + O-model produces correct classifications.

**Benchmark dataset:** 50 curated multi-entity incident scenarios. Each scenario defines:
- 2-10 affected entities with individual Phase 2 outputs (impact fields, sector, MS)
- Expected aggregation results (worst-case, counts, derived fields)
- Expected T-level (from deterministic rules)
- Expected O-level
- Expected matrix classification + coordination level

**Validation steps:**

| Step | What | Type | Pass criteria |
|---|---|---|---|
| 1 | Single entity → Phase 2 → correct assessment | Already proven (v3) | Baseline |
| 2 | Multiple entities → aggregation → correct worst-case/counts | Deterministic (unit tests) | 100% (no ML, pure logic) |
| 3 | Aggregation → T-level derivation | Deterministic (unit tests) | 100% (rule lookup) |
| 4 | Aggregated inputs → O-model → correct O-level | ML model (benchmark) | > 70% on curated scenarios |
| 5 | T+O → matrix → correct classification | Deterministic | 100% (lookup table) |
| 6 | End-to-end: entities → aggregation → T+O → matrix | Full pipeline | > 70% end-to-end |

**Step 4 is the key validation.** The current O-model (v3) was trained on single-entity inputs. Running it on multi-entity aggregated inputs will reveal:
- If the O-model generalises to aggregated data → concept proven, proceed to MCP tool
- If not → O-model retrain with multi-entity training data needed first (priority #7)

**Scenario sources:** ENISA annual threat reports, EU-CyCLONe incident summaries, vault RETEX notes with multi-entity incidents (SolarWinds, NotPetya, WannaCry, MOVEit, etc.)

**Effort:** Medium — curated scenario creation + benchmark script + analysis.

---

## v6 completed (2026-04-02) — Phase 1 Multi-Task Learning

| Enhancement | Phase | Result | Tag |
|-------------|-------|--------|-----|
| CVSS vector multi-task learning (9 heads: 1 band + 8 components) | 1 | 62.3% band accuracy (+1.8pp vs v1), 58.4% macro F1 (+2.0pp) | cyberscale-v6 |
| CPE vendor/product signal (tested, rejected) | 1 | 62.7% — no improvement over 62.3% baseline, CPE is noise | — |
| `score_vulnerability` returns predicted CVSS vector | 1 | Additive output: `predicted_vector` dict with 8 components | cyberscale-v6 |

**Conclusion:** Three approaches failed to break Phase 1 past 62%: CWE (v2, flat), multi-task (v6, +1.8pp), CPE (v6, +0pp). The ceiling is CVE description quality, not model architecture or features. Future Phase 1 gains require fundamentally different data (exploit code, patch diffs, advisory cross-referencing) or methodology (contrastive pre-training, curriculum learning). See lessons 27-29 in `docs/lessons-learned.md`.

---

## v7 completed (2026-04-02) — Luxembourg National Layer

| Enhancement | Phase | Result | Tag |
|-------------|-------|--------|-----|
| Luxembourg ILR threshold reference data | 2 | `lu_thresholds.json` — 15 sector sub-types, common criteria, DORA coverage, notification deadlines | — |
| LU national threshold assessment module | 2 | Deterministic per-sector functions: electricity POD matrix, gas SCADA, rail, road, air, health, drinking water, digital services | — |
| Three-tier router (IR → LU → NIS2) | 2 | `entity_incident.py` routes IR entities to EU IR, LU-covered to national, rest to NIS2 ML | — |
| LU sector-specific input fields | 2 | `sector_specific` dict in MCP tool: pods_affected, voltage_level, trains_cancelled_pct, scada_unavailable_min, etc. | — |
| Pluggable national module registry | 2 | `national/registry.py` — register new MS modules without changing router | — |
| Luxembourg threshold benchmark | 2 | 20/20 curated scenarios, 100% routing + significance + criteria accuracy | — |
| Documentation + tag | — | Design spec, roadmap, architecture updated | cyberscale-v7 |

**Key decisions:**
- IR thresholds take precedence over LU for digital infrastructure entities (ILR/N22/6 superseded)
- DORA included for LU banking/financial market (CSSF as competent authority)
- POST/LuxTrust use sector thresholds, no entity-specific overrides
- Road transport material damage threshold EUR 200,000 (correct, higher than other sectors)
- HCPN national crisis qualification deferred to v8

---

## v7 remaining targets (v8 candidates)

| Priority | Enhancement | Description |
|---|---|---|
| 1 | **HCPN Cadre national** | Luxembourg national crisis qualification — 3 cumulative criteria for incidents, 4 for threats. Cooperation mode determination (Alerte/CERC vs Crise). |
| 2 | **Notification export schema** | Structured JSON export from Phase 2 incident mode for submission to national CSIRT portals. Art. 23 field mapping. |
| 3 | **Temporal incident tracking** | Incidents evolve over NIS2 reporting timeline: early warning (24h) → notification (72h) → intermediate → final (1 month). |
| 4 | **Real incident validation** | Validate full pipeline against 20+ actual post-incident reports (ENISA annual, EU-CyCLONe public summaries). |
| 5 | **Active learning loop** | Deploy MCP server, collect analyst corrections on assessments, retrain with feedback. v5 feedback store is the foundation. |
| 6 | **Secure notification channel** | Secure transmission of Phase 2 outputs to CSIRTs. CSIRT Network ingestion format. Authentication, TLP marking, integrity. |
| 7 | **CSIRT pilot** | Deploy with a real CSIRT (CIRCL/LU) to validate entity-facing and authority-facing tools in operational context. |

---

## Key lessons informing priorities

1. **Phase 1 has a hard ceiling at ~62% with description-only input** — CWE (v2, flat), multi-task (v6, +1.8pp), and CPE (v6, +0pp) all failed to break through. Three successive interventions produced diminishing returns. Future Phase 1 work requires different data (exploit code, patch diffs) or methodology (contrastive pre-training), not more features or heads.
2. **Human-curated data is the highest-leverage input** — Phase 2 went from 32% to 88% with predecessor data; Phase 3 went from 67.5% to 97.5% with 40 curated incidents.
3. **Synthetic-on-synthetic metrics inflate** — Phase 3 v1 showed 96% on synthetic but only 67.5% on curated. Always benchmark on human-curated data.
4. **Low-severity classes need explicit attention** — T1/O1/non_nis2 are consistently the weakest. Oversampling helps but curated examples help more.
