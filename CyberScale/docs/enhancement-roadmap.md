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
| 2 | Contextual (v3) | 80.5% accuracy, 80.5% macro F1 | > 75% | Met |
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

## v4 — Incident-Aware Multi-Entity Pipeline

v4 addresses three architectural gaps:
1. Phase 2 has no awareness of whether the entity is actually affected
2. Phase 3 has no automated link from Phase 2
3. `coordination_needs` is an input to Phase 3 O-model but is actually an **output** of the Blueprint Matrix — a circular dependency

### Design corrections

**Remove `coordination_needs` from Phase 3 O-model inputs.** Coordination level is determined by the matrix classification, not the other way around:

| Matrix result | Coordination (output, not input) |
|---|---|
| Below threshold | National CSIRT only |
| Significant | Art. 23 reporting to competent authority + CSIRT |
| Large-scale | EU-CyCLONe activated (NIS2 Art. 16) |
| Cyber crisis | IPCR activated (Council level) |

**Replace `cross_border` boolean with concrete MS geography.** Per entity:
- `ms_established` (str) — where entity is established
- `ms_affected` (list[str]) — where entity's services are impacted

This enables deriving `cross_border_pattern` and `ms_affected` count from data rather than analyst judgment.

### 1. Impact inputs for Phase 2

Add incident impact fields per entity:

**Common inputs (all entities):**

| Input | Type | Values | Description |
|-------|------|--------|-------------|
| `entity_affected` | bool | true/false | Vulnerability confirmed exploited at this entity |
| `service_impact` | str | none / degraded / unavailable | Impact on entity's services |
| `data_impact` | str | none / accessed / exfiltrated / compromised | Impact on entity's data |
| `financial_impact` | str | none / minor / significant / severe | Financial loss assessment |
| `safety_impact` | str | none / health_risk / health_damage / death | Physical safety impact |
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

### 4. Multi-entity incident model

A single incident can affect multiple entities with different impact levels. Phase 2 runs **once per entity** (routed IR/NIS2). Phase 3 inputs are **fully derived** from Phase 2 results — no analyst input required for structured fields.

**Phase 2 input: list of entity assessments**

```json
{
  "description": "Supply chain compromise of cloud provider software update",
  "entities": [
    {
      "entity_type": "cloud_computing_provider",
      "sector": "digital_infrastructure",
      "entity_affected": true,
      "service_impact": "unavailable",
      "data_impact": "compromised",
      "unavailability_duration_min": 45,
      "ms_established": "LU",
      "ms_affected": ["LU", "DE", "BE"]
    },
    {
      "entity_type": "healthcare_provider",
      "sector": "health",
      "entity_affected": true,
      "service_impact": "degraded",
      "data_impact": "none",
      "ms_established": "DE",
      "ms_affected": ["DE"]
    },
    {
      "entity_type": "credit_institution",
      "sector": "banking",
      "entity_affected": false,
      "service_impact": "none",
      "data_impact": "none",
      "ms_established": "FR",
      "ms_affected": []
    }
  ]
}
```

**Phase 2 output: per-entity results**

```json
{
  "entity_results": [
    {
      "entity_type": "cloud_computing_provider",
      "model": "IR",
      "severity": "Critical",
      "significant_incident": true,
      "triggered_criteria": ["Art. 7: unavailability > 30min"]
    },
    {
      "entity_type": "healthcare_provider",
      "model": "NIS2",
      "severity": "High",
      "reporting_hint": "Monitor — service degraded at essential entity"
    },
    {
      "entity_type": "credit_institution",
      "model": "NIS2",
      "severity": "Low",
      "reporting_hint": null
    }
  ]
}
```

**Phase 3 inputs: fully derived from Phase 2 aggregation**

| Phase 3 field | Aggregation rule | Example |
|---|---|---|
| `affected_entities` | Count entities where entity_affected=true | 2 |
| `sectors_affected` | Count distinct sectors where entity_affected=true | 2 (digital_infrastructure + health) |
| `service_disruption` | Worst-case service_impact across affected entities | "complete" (from unavailable) |
| `data_compromise` | Worst-case data_impact across affected entities | "operational" (from compromised) |
| `entity_relevance` | Highest relevance among affected entities (from entity_type mapping) | "essential" (healthcare_provider) |
| `ms_affected` | Count distinct MS in union of all ms_affected lists | 3 (LU + DE + BE) |
| `cross_border_pattern` | Derived: 1 MS=none, 2=limited, 3-5=significant, 6+=systemic | "significant" (3 MS) |
| `cascading` | Derived: 1 sector=none/limited, 2+=cross_sector | "cross_sector" (2 sectors) |
| `capacity_exceeded` | Heuristic: affected_entities>50 AND ms_affected>=3 → true | false |

**Note:** `coordination_needs` is NOT an input — it's an output of the Blueprint Matrix.

**Zero mandatory analyst inputs.** Everything is derived. Analyst can override any field if the defaults are wrong.

**Effort:** High — multi-entity schema, aggregation logic, entity_type → entity_relevance mapping, per-entity routing.

### 5. Phase 3 O-model retrain

Remove `coordination_needs` from O-model inputs. The O-model predicts operational severity from observable indicators only:

| O-model input | Source |
|---|---|
| `description` | Incident description (enriched with entity impact summaries) |
| `sectors_affected` | Aggregated from Phase 2 |
| `entity_relevance` | Aggregated from Phase 2 |
| `ms_affected` | Aggregated from Phase 2 |
| `cross_border_pattern` | Derived from ms_affected |
| `capacity_exceeded` | Heuristic default or analyst override |

Removed: `coordination_needs` (was circular — is a matrix output, not an input).

**Effort:** Medium — retrain O-model with updated input schema + regenerate training data.

### 6. `assess_incident` MCP tool

Single MCP tool: vulnerability description + entity list → full pipeline → matrix classification + coordination level:

```
assess_incident(
    description="Supply chain compromise of cloud provider",
    cwe="CWE-494",
    entities=[
        {entity_type: "cloud_computing_provider", sector: "digital_infrastructure",
         entity_affected: true, service_impact: "unavailable",
         unavailability_duration_min: 45,
         ms_established: "LU", ms_affected: ["LU", "DE", "BE"]},
        {entity_type: "healthcare_provider", sector: "health",
         entity_affected: true, service_impact: "degraded",
         ms_established: "DE", ms_affected: ["DE"]},
    ],
)
```

**Output:**

```json
{
  "phase1": {"score": 8.5, "band": "High"},
  "phase2": {
    "entity_results": [
      {"entity_type": "cloud_computing_provider", "model": "IR",
       "severity": "Critical", "significant_incident": true,
       "triggered_criteria": ["Art. 7: unavailability > 30min"]},
      {"entity_type": "healthcare_provider", "model": "NIS2",
       "severity": "High",
       "reporting_hint": "Service degraded at essential entity"}
    ]
  },
  "aggregation": {
    "affected_entities": 2,
    "sectors_affected": 2,
    "ms_affected": 3,
    "ms_with_service_impact": ["LU", "DE", "BE"],
    "service_disruption": "complete",
    "data_compromise": "operational",
    "entity_relevance": "essential",
    "cross_border_pattern": "significant",
    "cascading": "cross_sector",
    "capacity_exceeded": false
  },
  "phase3": {
    "technical": {"level": "T3", "key_factors": ["2 entities affected",
                  "2 sectors affected", "cross_sector cascading",
                  "operational data compromise"]},
    "operational": {"level": "O3", "key_factors": ["essential entity",
                    "3 member states affected",
                    "significant cross-border pattern"]}
  },
  "matrix": {
    "classification": "large_scale",
    "label": "Large-scale",
    "provision": "7(c)",
    "coordination": "EU-CyCLONe activated (NIS2 Art. 16)"
  }
}
```

**Key design principle:** `coordination` is in the matrix output, not the input. The pipeline determines coordination needs — the analyst doesn't pre-select them.

**Effort:** High — new MCP tool with multi-entity orchestration, aggregation, and full pipeline chaining.

---

## Suggested next iteration priority

Based on impact/effort ratio and the Phase 1 accuracy gap:

| Priority | Enhancement | Phase | Expected gain |
|----------|-------------|-------|---------------|
| 1 | Remove coordination_needs from O-model + retrain | 3 | Fixes circular dependency |
| 2 | Replace cross_border bool with ms_established + ms_affected | 2 | Concrete geography, derived cross_border_pattern |
| 3 | Impact inputs + IR/NIS2 model split + router | 2 | Incident-aware Phase 2, regulatory-aligned |
| 4 | IR threshold reference data | 2 | Quantitative significant_incident for digital entities |
| 5 | Multi-entity aggregation | 2+3 | Per-entity assessment, fully derived Phase 3 inputs |
| 6 | `assess_incident` MCP tool | All | Multi-entity end-to-end pipeline |
| 7 | CVSS vector multi-task | 1 | +5-10pp (biggest accuracy gap) |
| 8 | Product/vendor signal | 1 | +3-5pp |
| 9 | LLM description augmentation | 3 | Robustness |
| 10 | Expand curated incidents to 100+ | 3 | Benchmark reliability |

---

## Key lessons informing priorities

1. **Feature additions have diminishing returns on Phase 1** — CWE didn't help; the problem is description quality, not feature coverage. Architectural changes (multi-task, contrastive) are more likely to break through.
2. **Human-curated data is the highest-leverage input** — Phase 2 went from 32% to 88% with predecessor data; Phase 3 went from 67.5% to 97.5% with 40 curated incidents.
3. **Synthetic-on-synthetic metrics inflate** — Phase 3 v1 showed 96% on synthetic but only 67.5% on curated. Always benchmark on human-curated data.
4. **Low-severity classes need explicit attention** — T1/O1/non_nis2 are consistently the weakest. Oversampling helps but curated examples help more.
