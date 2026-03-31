# CyberScale — Enhancement Roadmap

Concrete enhancement paths prioritised by expected impact. Updated after v2 implementation.

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

## Current model performance

| Phase | Model | Key metric | Target | Status |
|-------|-------|------------|--------|--------|
| 1 | Scorer | 60.2% band accuracy | > 75% | Not met |
| 2 | Contextual | 80.5% accuracy, non_nis2 76.5% | > 75% | Met |
| 3 | Technical (T) | 97.5% curated accuracy | > 75% | Met |
| 3 | Operational (O) | 100% curated accuracy | > 75% | Met |
| 3 | Matrix (end-to-end) | 97.5% curated accuracy | > 70% | Met |

**Phase 1 is the weakest phase.** CWE didn't help. The bottleneck is description quality — many CVE descriptions are formulaic regardless of actual severity.

---

## Remaining enhancements

### High priority — Phase 1 accuracy (biggest gap)

#### 1. CVSS vector multi-task learning

Instead of predicting the composite score, predict individual CVSS vector components (Attack Vector, Complexity, Privileges Required, User Interaction, Scope, C/I/A Impact) as auxiliary outputs. Multi-task learning where each head predicts one component. The composite score falls out deterministically from the predicted vector.

**Effort:** Medium — new model architecture, but training data already contains CVSS vectors.
**Expected gain:** +5-10pp — decomposes the hard problem into easier sub-problems.

#### 2. Product/vendor signal

"OpenSSL" or "Linux kernel" vulnerabilities are systematically higher severity than "WordPress plugin" vulnerabilities at the same CWE. CPE vendor/product from the CVE data could be encoded as an input feature.

**Effort:** Low — add to input format, retrain. CPE data available in cvelistV5.
**Expected gain:** +3-5pp overall.

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

## v4 — Incident-Aware Phase 2 + Vulnerability-to-Incident Bridge

Phase 2 currently assesses vulnerability severity in deployment context but has no awareness of whether the entity is actually affected. Phase 3 classifies incidents but has no automated link from Phase 2. v4 addresses both gaps by making Phase 2 incident-aware and splitting it into two regulatory-aligned models.

### 1. Impact inputs for Phase 2

Add incident impact fields to Phase 2 so it can assess both vulnerability severity and early incident indicators:

**Common inputs (all entities):**

| Input | Type | Values | Source |
|-------|------|--------|--------|
| `entity_affected` | bool | true/false | Has the vulnerability been exploited? |
| `service_impact` | str | none / degraded / unavailable | Impact on entity's services |
| `data_impact` | str | none / accessed / exfiltrated / compromised | Impact on entity's data |
| `financial_impact` | str | none / minor / significant / severe | Caller's assessment against applicable threshold |
| `safety_impact` | str | none / health_risk / health_damage / death | Physical safety impact |

All optional, default to `none`. When provided, they escalate severity and trigger reporting hints.

**Effort:** Medium — new input fields, training data generation, retrain.

### 2. IR/NIS2 model split with router

Split Phase 2 into two specialised models behind a deterministic router:

```
Phase 2 Router (MCP tool)
  │
  ├── entity_type in IR_ENTITIES? ──→ Phase 2-IR model (quantitative)
  │                                    Additional inputs: unavailability_duration_min,
  │                                      affected_users_pct, affected_users_count,
  │                                      financial_loss_eur
  │                                    Output: severity + significant_incident (bool)
  │
  └── all other entities ──→ Phase 2-NIS2 model (qualitative)
                              Inputs: common impact fields above
                              Output: severity + reporting_hint (advisory)
```

**IR entities (11 types):** `dns_service_provider`, `tld_registry`, `cloud_computing_provider`, `data_centre_operator`, `cdn_provider`, `managed_service_provider`, `managed_security_service_provider`, `online_marketplace_provider`, `search_engine_provider`, `social_network_provider`, `trust_service_provider`

**Why split:**
- IR model can be trained on precise threshold rules from Implementing Regulation (EU) 2024/2690 Arts. 5-14 → higher accuracy, definitive significant_incident output
- NIS2 model is not polluted by IR-specific numeric features irrelevant to hospitals or utilities
- Each model has a focused input schema matching its regulatory framework
- The MCP tool interface stays unified — the caller doesn't know which model runs

**IR model additional inputs:**

| Input | Type | Values | Used by |
|-------|------|--------|---------|
| `unavailability_duration_min` | int | Minutes of complete unavailability | Arts. 5-14 (thresholds: 20-30 min) |
| `affected_users_pct` | float | % of EU users affected | Arts. 7-13 (threshold: 5%) |
| `affected_users_count` | int | Absolute EU user count | Arts. 7-13 (threshold: 1M, 200K for trust) |
| `financial_loss_eur` | int | Financial loss in EUR | Art. 3(1)(a) (threshold: EUR 500,000) |
| `malicious_access` | bool | Suspectedly malicious? | Arts. 5-14 (any malicious → significant) |

**IR model output includes:**
- `significant_incident` (bool) — definitive, based on threshold rules
- `triggered_criteria` (list) — which IR article/threshold was exceeded

**NIS2 model output includes:**
- `reporting_hint` (str) — advisory, based on qualitative assessment
- `phase3_recommended` (bool) — whether Phase 3 assessment is warranted

**Effort:** High — two models, new training data, threshold reference data, router logic.

### 3. Entity-specific threshold reference data

Create `data/reference/ir_incident_thresholds.json` with per-entity-type thresholds from the Implementing Regulation:

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
    "complete_unavailability_min": 0,
    ...
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

### 4. Phase 2 → Phase 3 field mapping

When Phase 2 recommends Phase 3 assessment, provide suggested default values:

| Phase 2 field | Phase 3 field | Mapping |
|--------------|---------------|---------|
| `sector` | `sectors_affected` | Direct pass-through |
| `entity_type` | `entity_relevance` | healthcare_provider → essential, generic_sme → non_essential |
| `cross_border` | `cross_border_pattern` | true → "limited" (minimum), false → "none" |
| `cer_critical_entity` | `entity_relevance` | true → "high_relevance" |
| `service_impact` | `service_disruption` | unavailable → "complete", degraded → "significant" |
| `data_impact` | `data_compromise` | exfiltrated → "sensitive", compromised → "operational" |

Suggestions, not overrides — the analyst confirms or adjusts before Phase 3 runs.

**Effort:** Medium — entity_type → entity_relevance mapping table, pipeline wiring.

### 5. `assess_full_incident_pipeline` MCP tool

A single MCP tool that chains Phase 1 → Phase 2 (routed) → (if incident warranted) → Phase 3, using the field mapping above:

```
Phase 1 (score=7.8)
  → Phase 2-NIS2 (severity=Critical, entity_affected=true,
                   service_impact=unavailable)
      phase3_recommended: true
      suggested Phase 3 defaults: sectors=health, relevance=essential,
        service_disruption=complete, cross_border=limited
    → Analyst confirms/adjusts
      → Phase 3 (T3+O2)
        → Matrix: Large-scale — 7(c) EU-CyCLONe
```

For IR entities:
```
Phase 1 (score=8.5)
  → Phase 2-IR (severity=Critical, significant_incident=true,
                triggered_criteria=["Art. 7: unavailability > 30min",
                                    "Art. 3(1)(a): financial > EUR 500K"])
      → Phase 3 auto-triggered with mapped defaults
        → Matrix: Large-scale — 7(c)
```

**Effort:** Medium — new MCP tool combining router + existing tools + field mapping.

---

## Suggested next iteration priority

Based on impact/effort ratio and the Phase 1 accuracy gap:

| Priority | Enhancement | Phase | Expected gain |
|----------|-------------|-------|---------------|
| 1 | Impact inputs + IR/NIS2 model split + router | 2 | Incident-aware Phase 2, regulatory-aligned |
| 2 | IR threshold reference data | 2 | Quantitative significant_incident for digital entities |
| 3 | Phase 2 → Phase 3 field mapping | 2+3 | Automated handoff with suggested defaults |
| 4 | `assess_full_incident_pipeline` MCP tool | All | End-to-end single-call assessment |
| 5 | CVSS vector multi-task | 1 | +5-10pp (biggest accuracy gap) |
| 6 | Product/vendor signal | 1 | +3-5pp |
| 7 | LLM description augmentation | 3 | Robustness |
| 8 | Expand curated incidents to 100+ | 3 | Benchmark reliability |
| 9 | Richer cross-border encoding | 2 | +2-3pp |
| 10 | Active learning loop | All | Continuous improvement |

---

## Key lessons informing priorities

1. **Feature additions have diminishing returns on Phase 1** — CWE didn't help; the problem is description quality, not feature coverage. Architectural changes (multi-task, contrastive) are more likely to break through.
2. **Human-curated data is the highest-leverage input** — Phase 2 went from 32% to 88% with predecessor data; Phase 3 went from 67.5% to 97.5% with 40 curated incidents.
3. **Synthetic-on-synthetic metrics inflate** — Phase 3 v1 showed 96% on synthetic but only 67.5% on curated. Always benchmark on human-curated data.
4. **Low-severity classes need explicit attention** — T1/O1/non_nis2 are consistently the weakest. Oversampling helps but curated examples help more.
