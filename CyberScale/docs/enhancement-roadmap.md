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

The authority receives entity notifications and classifies the incident at EU level. **Phase 3T is eliminated** — the T-level becomes a deterministic derivation in the aggregation layer, because all T-level inputs (service_impact, data_impact, affected_entities, sectors, cascading) are observable facts that map mechanically to T1-T4.

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

---

## Suggested next iteration priority

Based on impact/effort ratio and the Phase 1 accuracy gap:

| Priority | Enhancement | User | Expected gain |
|----------|-------------|------|---------------|
| 1 | Unified impact taxonomy (6 dimensions) | Both | Coherent data flow between phases |
| 2 | Phase 2 incident mode + early warning recommendation | Entity | NIS2 Art. 23 compliance support |
| 3 | IR/NIS2 model split + router | Entity | Regulatory-aligned, quantitative for IR entities |
| 4 | IR threshold reference data | Entity | Definitive significant_incident for digital entities |
| 5 | `assess_entity_incident` MCP tool | Entity | Single-entity incident assessment + early warning |
| 6 | Eliminate T-model → deterministic T-level in aggregation | Authority | Simpler, faster, 100% predictable |
| 7 | O-model retrain (remove coordination_needs, add consequence dims) | Authority | Fixes circularity + adds financial/safety/persons |
| 8 | `assess_incident` MCP tool | Authority | Multi-notification → aggregation → O-model → matrix |
| 9 | CVSS vector multi-task | Entity | +5-10pp Phase 1 accuracy |
| 10 | Expand curated incidents to 100+ | Authority | Phase 3 benchmark reliability |

---

## Future: Secure notification channel (beyond v4)

CyberScale is an assessment tool, not a notification platform. However, future versions should conceptualise the **secure transmission of Phase 2 outputs to concerned CSIRTs** and the **ingestion of entity notifications by the authority pipeline (Phase 3)**. This includes:

- Structured notification export format (aligned with any harmonised EU format that emerges)
- Secure communication channel to national CSIRT (each MS has its own: CIRCL in LU, BSI in DE, ANSSI in FR, etc.)
- CSIRT Network information sharing format for cross-border incidents (NIS2 Art. 15)
- Authentication and integrity of entity notifications
- TLP marking and handling restrictions

This is not scoped for v4 but should inform architectural decisions — Phase 2 output format and Phase 3 input format should be designed with future interoperability in mind.

---

## Key lessons informing priorities

1. **Feature additions have diminishing returns on Phase 1** — CWE didn't help; the problem is description quality, not feature coverage. Architectural changes (multi-task, contrastive) are more likely to break through.
2. **Human-curated data is the highest-leverage input** — Phase 2 went from 32% to 88% with predecessor data; Phase 3 went from 67.5% to 97.5% with 40 curated incidents.
3. **Synthetic-on-synthetic metrics inflate** — Phase 3 v1 showed 96% on synthetic but only 67.5% on curated. Always benchmark on human-curated data.
4. **Low-severity classes need explicit attention** — T1/O1/non_nis2 are consistently the weakest. Oversampling helps but curated examples help more.
