# CyberScale — Design Specification

Multi-phase cyber severity assessment MCP server. Three independent, composable phases covering the full spectrum from raw vulnerability description to EU-level incident classification.

**Version:** 8.0
**Status:** v8 complete — HCPN crisis qualification, Belgium national module, fully deterministic Phase 3, sector dependencies, multi-tier (3a/3b/HCPN), authority feedback, real incident validation
**Lineage:** Builds on the closed CVE-Severity-Context project (ModernBERT classifier, 80.7% accuracy, 1,890 scenarios). Replaces VulnMCP severity tools.


## 2. Three phases

| Phase | Scope | Input | Output | Novel contribution |
|-------|-------|-------|--------|-------------------|
| **1 — Vulnerability Scoring** | Single vulnerability | Description (any quality) + optional CVE ID | 0–10 score (CVSS-compatible) + confidence | Severity estimation without CVSS dependency |
| **2 — Contextual Severity** | Vulnerability/incident in deployment context | Description + NIS2 sector + MS geography + optional impact fields | Critical/High/Medium/Low + key factors | Context-dependent severity per NIS2 sector |
| **2 — Entity Incident** | Entity self-assessment | Above + entity_type + impact fields | Significance (IR/NIS2) + early warning recommendation | IR thresholds (Arts. 5-14) or NIS2 ML model |
| **3a — National Incident** | National CSIRT classification | Entity notifications from single MS | National T/O/matrix + cross-border flag | Deterministic aggregation + rules + matrix |
| **3b — EU Incident** | EU-CyCLONe classification | National classifications + CyCLONe Officer inputs | EU-level classification + coordination level | Deterministic aggregation + escalation rules |
| **3 — Incident Classification** | Authority multi-entity classification | Entity notification dicts | Deterministic T-level + deterministic O-level + Blueprint matrix | Fully deterministic (rules + matrix) |
| **National — LU Crisis** | HCPN crisis qualification | Sectors affected + impact data + authority judgment inputs | qualification_level + cooperation_mode + recommend_consultation | National crisis plan activation (PGGCCN) |
| **National — LU/BE Significance** | Entity significance thresholds | Entity incident data (from Phase 2) | significant_incident (bool) + triggered_criteria + competent_authority | Per-MS deterministic thresholds |

### Independence principle

Each phase is standalone — usable without the others. Phase 1 enriches Phase 2, Phase 2 enriches Phase 3, but none requires the previous as a prerequisite. An analyst can enter at any phase with whatever information they have.


## 4. Phase 2 — Contextual Severity

### 4.1 Purpose

Assess how severe a vulnerability is for a specific organisation based on its NIS2 sector and cross-border exposure. Works with or without a Phase 1 score.

### 4.2 Input

| Field | Required | Values |
|-------|----------|--------|
| Vulnerability description | Yes | Any format (CVE, advisory, raw report) |
| Sector | Yes | 18 NIS2 sectors + 1 non-NIS2 category (19 total) |
| ms_established | Yes | ISO 3166-1 alpha-2 (default: "EU") |
| ms_affected | Optional | List of ISO 3166-1 alpha-2 codes (cross_border derived) |
| Severity score (0–10) | Optional | From Phase 1, CVSS, EUVD, or manual |
| entity_type | Optional | One of 55+ NIS2 entity type IDs |
| cer_critical_entity | Optional | true / false |

**Incident mode (v4)** — when `entity_affected=True`, additional fields:

| Field | Required | Values |
|-------|----------|--------|
| service_impact | Optional | none / partial / degraded / unavailable / sustained |
| data_impact | Optional | none / accessed / exfiltrated / compromised / systemic |
| financial_impact | Optional | none / minor / significant / severe |
| safety_impact | Optional | none / health_risk / health_damage / death |
| affected_persons_count | Optional | int (0+) |
| suspected_malicious | Optional | true / false |
| impact_duration_hours | Optional | int (0+) |

### 4.3 The 19 sector values

**Annex I — Essential (11):** Energy, Transport, Banking, Financial market infrastructures, Health, Drinking water, Waste water, Digital infrastructure, ICT service management, Public administration, Space

**Annex II — Important (7):** Postal and courier, Waste management, Manufacturing, Chemicals, Food, Digital providers, Research

**Non-NIS2 (1):** Organisations outside NIS2 scope

### 4.4 Model

| Aspect | Design |
|--------|--------|
| Architecture | ModernBERT-base, classification head (4-class) |
| Input format | All-as-text: `[CLS] <description> [SEP] sector: <sector> cross_border: <bool> score: <score or absent>` |
| Output | Severity label (Critical/High/Medium/Low) + key factors |
| Key factors | Top contributing features (e.g., "health sector + RCE + cross-border") |

### 4.5 Training data generation

Fully scripted — no Claude skills, no LLM. The script implements codified NIS2 regulatory threshold logic:

1. For each CVE in the Phase 1 training set (~10–15k CVEs)
2. Determine relevant sectors using CPE product category to sector mapping
3. Skip irrelevant (CVE, sector) combinations
4. For each relevant sector x cross-border (true/false), apply sector-specific severity rules deterministically

**Sector-specific rules (examples):**

| Sector | Rule |
|--------|------|
| Health | RCE/availability impact on clinical systems escalates to Critical |
| Energy | SCADA/ICS impact escalates; IT-only no change |
| Digital infrastructure | Availability impact amplified (DNS, cloud, CDN) |
| Non-NIS2 | No regulatory escalation, severity tracks CVSS band |
| Any + cross-border=true | Multi-state cascading escalates by one level |

All 18 NIS2 sectors + non-NIS2 covered in training data, with balanced class distribution. Irrelevant (CVE, sector) combinations are skipped based on CPE product category to sector mapping.

### 4.6 National layer (v7)

Three-tier significance routing in Phase 2 entity incident mode:

```
Entity in MS X
  │
  ├── IR entity type? → IR thresholds (EU-wide, Arts. 5-14) [v4]
  │
  ├── National module for MS X? + sector covered?
  │   → National deterministic thresholds [v7]
  │   Output: significant_incident (bool) + triggered_criteria + ILR reference
  │
  └── Neither? → NIS2 ML model (qualitative) [v4]
```

**Luxembourg (LU)** — first national module (v7):
- Source: ILR NIS1 transposition regulations (best available until LU publishes NIS2-specific rules)
- Covers: energy (electricity POD matrix, gas SCADA), transport (rail, road, air), health (hospital, laboratory), drinking water, digital service providers
- IR entities in LU use IR thresholds (EU regulation > national transposition)
- Digital infrastructure ILR/N22/6 superseded by IR thresholds
- DORA applies separately for banking/financial market (CSSF as competent authority)
- POST/LuxTrust use sector thresholds — no entity-specific overrides
- HCPN national crisis qualification — see section 4.8

**Pluggable pattern:** `data/reference/{ms}_thresholds.json` + `src/cyberscale/national/{ms}.py`. Registry at `national/registry.py` — new MS modules register without changing router logic.

**Output includes:** applicable frameworks with per-framework notification deadline and competent authority.

**Belgium (BE)** — second national module (v8):
- Source: CCB NIS2 Notification Guide v1.3 (August 2025)
- Horizontal thresholds (same for all sectors, unlike LU per-sector matrices):
  - Malicious CIA compromise: any suspected malicious unauthorized access
  - Availability: ≥20% users for ≥1 hour (total unavailability implies 100%)
  - Financial loss: >EUR 250,000 or >5% annual turnover (whichever lower)
  - Third-party damage: death, hospitalisation, injuries, disabilities
  - Recurring events: ≥2 in 6 months, same root cause (flagged but not evaluable from single incident)
- DORA entities (banking/financial) excluded — BNB supervision
- IR entities use EU-wide IR thresholds (same as LU)
- Competent authority: CCB
- Notification channel: notif.safeonweb.be

### 4.8 HCPN National Crisis Qualification (v8)

Separate assessment layer ABOVE entity significance — determines whether an event triggers Luxembourg's PGGCCN national crisis plan and which cooperation mode applies (Alerte/CERC vs Crise).

**Scope:** Impact on Luxembourg regardless of entity establishment. An entity established in Ireland with impact on Luxembourg banking is in scope.

**Incident qualification — three cumulative criteria:**

| Criterion | Description | Deterministic? |
|-----------|-------------|---------------|
| 1. Essential service | At least one CER essential service affected | Yes — lookup against reference list |
| 2. Prejudice to vital interests | At least one of seven sub-criteria: human impact, national security, sensitive data loss, service interruption, economic consequences, geographic spread, users affected | Partially — some thresholds delegated to sectoral authorities → "undetermined" |
| 3. Coordination + urgency | Both interministerial coordination AND urgent executive decisions required | Yes (bool), but None → "undetermined" |

**Fast-track provision:** Malicious unauthorized access with grave disruption → Criterion 2 bypassed (status="bypassed"), proceed directly to Criterion 3.

**Threat qualification — four cumulative criteria:** Same three plus probability assessment (only High/Imminent qualify).

**Cooperation mode:**
- Actual prejudice → Crise (CC activated at CNC Senningen)
- Potential prejudice → Alerte/CERC

**Large-scale determination:** `cross_border OR capacity_exceeded` → `large_scale_cybersecurity_incident`

**Design principles:**
- Returns "undetermined" for delegated thresholds — never guesses
- Uncertainty triggers consultation recommendation, not delay
- Uses `sector_dependencies.json` for interdependent sector disruption check
- `CriterionResult` has four states: met, not_met, undetermined, bypassed

**Validation:** 15/15 curated scenarios, 5/5 real RETEX incidents concordant with actual crisis activation outcomes.

### 4.7 Evaluation

| Metric | Purpose |
|--------|---------|
| Accuracy + macro F1 | Overall and per-class performance |
| Per-sector accuracy | Ensure no sector is a blind spot |
| Closed project benchmark | Evaluate on 1,890 scenarios — compare simplified context vs original richer context |
| Cross-border impact | Measure accuracy with/without cross-border to quantify its contribution |


## 6. Infrastructure

### 6.1 MCP server

Single FastMCP server exposing all three phases as independent tools:

| Tool | Phase | Input | Output |
|------|-------|-------|--------|
| `score_vulnerability` | 1 | CVE ID or raw description | 0–10 score + confidence |
| `lookup_vulnerability` | 1 | CVE ID | Merged NVD/EUVD/CIRCL data |
| `search_similar` | 1 | Raw description | Top-N similar known vulnerabilities |
| `assess_contextual_severity` | 2 | Description + sector + MS geography | C/H/M/L + key factors |
| `assess_entity_incident` | 2 | Entity incident: description + sector + entity_type + impact fields + optional sector_specific | Severity + significance (IR/LU/NIS2 three-tier) + early warning + applicable frameworks |
| `classify_incident` | 3 | Full incident input | Deterministic T-level + O-level + matrix |
| `assess_incident` | 3 | Entity notification dicts | Aggregation + T-level + O-level + matrix classification |
| `assess_national_incident` | 3a | Entity notifications from single MS | National T/O/matrix + cross-border flag |
| `assess_eu_incident` | 3b | National classifications + CyCLONe Officer inputs | EU-level classification + coordination level |
| `assess_lu_crisis_incident` | National (HCPN) | Sectors affected + impact data + authority judgment | HCPN qualification level + cooperation mode |
| `assess_lu_crisis_threat` | National (HCPN) | Above + threat probability | HCPN threat qualification + cooperation mode |
| `assess_full_pipeline` | 1+2 | Description + sector + MS geography | Phase 1 score + Phase 2 severity |
| `refresh_store` | Infra | Optional: date range, source filter | Updated vector store entries |

### 6.2 Models and rules

| Model | Task | Architecture | Training data | Key metric |
|-------|------|--------------|---------------|------------|
| Phase 1: Severity scorer (v6) | Multi-task classification (4-class bands + 8 CVSS vector components) | ModernBERT-base, shared encoder + 9 heads (2-layer MLP band head + 8 component heads) | ~30k CVEs with CVSS v3.1 scores and vectors | 62.3% band accuracy |
| Phase 2: Contextual classifier | Classification (4-class) | ModernBERT-base, all-as-text | 32k scenarios (CVEs x sectors x impact fields) | 81.7% accuracy |
| Phase 3 T-level | Deterministic rules | No ML — `derive_t_level()` | Rules from impact taxonomy | 100% |
| Phase 3 O-level | Deterministic rules | No ML — `derive_o_level()` | Rules from consequence dimensions | 100% |
| IR thresholds | Deterministic per-entity-type | No ML — `assess_ir_significance()` | Arts. 5-14 thresholds | 100% |
| LU national thresholds (v7) | Deterministic per-sector | No ML — `assess_lu_significance()` | ILR NIS1 transposition | 100% (20/20 curated) |
| BE national thresholds (v8) | Deterministic horizontal | No ML — `assess_be_significance()` | CCB NIS2 Guide v1.3 | 100% (10/10 curated) |
| HCPN crisis qualification (v8) | Deterministic criteria | No ML — `qualify_hcpn_incident()` / `qualify_hcpn_threat()` | Cadre national v1.0 | 100% (15/15 curated) |
| Phase 1 scorer (v1, deprecated) | Single-head classification (4-class) | ModernBERT-base, single classification head | ~45k CVEs | 60.5% (superseded by v6) |
| Phase 3 T-model (deprecated) | Was classification (T1–T4) | ModernBERT-base | Kept for reference, not used in inference | — |

#### Phase 1 v6 multi-task architecture

The v6 scorer decomposes severity prediction into 9 parallel classification tasks sharing a single ModernBERT encoder:

| Head | Classes | What it predicts |
|------|---------|-----------------|
| **Band (primary)** | 4 (Critical/High/Medium/Low) | Overall severity band — primary metric |
| Attack Vector (AV) | 4 (Network/Adjacent/Local/Physical) | How the vulnerability is exploited |
| Attack Complexity (AC) | 2 (Low/High) | Conditions beyond attacker's control |
| Privileges Required (PR) | 3 (None/Low/High) | Authentication needed |
| User Interaction (UI) | 2 (None/Required) | Does a user need to act? |
| Scope (S) | 2 (Unchanged/Changed) | Does it affect other components? |
| Confidentiality (C) | 3 (None/Low/High) | Data disclosure impact |
| Integrity (I) | 3 (None/Low/High) | Data modification impact |
| Availability (A) | 3 (None/Low/High) | Service disruption impact |

**Loss:** `total_loss = band_loss + 0.3 * weighted_sum(component_losses)`

**Output:** The `score_vulnerability` MCP tool returns both the band prediction and the predicted CVSS vector components, enabling analysts to understand which aspects of the vulnerability the model considers most severe.

**Ceiling finding (v6):** Three interventions failed to break past ~62%: CWE features (v2, +0pp), multi-task (v6, +1.8pp), CPE vendor/product (v6, +0pp). The ceiling is structural — CVE descriptions lack sufficient discriminative signal between adjacent bands. Future gains require different data sources (exploit code, patch diffs, advisory text), not architecture changes.

### 6.3 Project structure

```
CyberScale/
+-- CyberScale.md                       # Project thesis, goals, success criteria, log
+-- CyberScale - Master Index.md        # Entry point, all links, artifact inventory
+-- Progress-Tracker.md                 # Session-by-session work log
+-- src/
|   +-- server.py                       # MCP server entry point
|   +-- api/
|   |   +-- nvd.py
|   |   +-- euvd.py
|   |   +-- circl.py
|   +-- store/
|   |   +-- client.py
|   |   +-- refresh.py
|   +-- models/
|   |   +-- scorer.py                   # Phase 1 inference
|   |   +-- contextual.py              # Phase 2 inference
|   |   +-- technical.py               # Phase 3 T-model inference
|   |   +-- operational.py             # Phase 3 O-model inference
|   |   +-- config.py                    # Centralized configuration (reference-loaded enums)
|   |   +-- contextual_ir.py            # IR threshold assessment
|   |   +-- early_warning.py            # Early warning recommendation
|   +-- national/
|   |   +-- registry.py             # Pluggable national module registry
|   |   +-- lu.py                   # Luxembourg ILR thresholds
|   |   +-- lu_crisis.py           # Luxembourg HCPN crisis qualification
|   |   +-- be.py                   # Belgium CCB thresholds
|   +-- matrix/
|   |   +-- dual_scale.py              # Blueprint matrix lookup
|   +-- tools/
|       +-- vulnerability.py            # Phase 1 MCP tools
|       +-- contextual.py              # Phase 2 MCP tools
|       +-- incident.py                # Phase 3 MCP tools
|       +-- entity_incident.py         # Phase 2 entity incident (three-tier routing)
|       +-- authority_incident.py       # Phase 3 authority classification
|       +-- national_incident.py        # Phase 3a national CSIRT
|       +-- eu_incident.py              # Phase 3b EU-CyCLONe
|       +-- lu_crisis_assessment.py     # HCPN crisis MCP tools
+-- training/
|   +-- data/                           # Generated training data (gitignored)
|   +-- scripts/
|   |   +-- fetch_bulk_cves.py        # Bulk CVE fetch from cvelistV5 (preferred)
|   |   +-- fetch_training_cves.py     # Phase 1 data from NVD/EUVD APIs (fallback)
|   |   +-- train_scorer.py            # Phase 1 training
|   |   +-- evaluate_scorer.py        # Phase 1 evaluation suite
|   |   +-- publish_hf.py            # Publish model + dataset to Hugging Face Hub
|   |   +-- generate_contextual.py     # Phase 2 scenario generation
|   |   +-- generate_incidents.py      # Phase 3 scenario generation
|   |   +-- train_contextual.py        # Phase 2 training
|   |   +-- train_technical.py         # Phase 3 T-model training
|   |   +-- train_operational.py       # Phase 3 O-model training
|   +-- configs/                        # Training hyperparameters
+-- evaluation/
|   +-- reconciliation_analysis.py     # NVD vs EUVD comparison
|   +-- closed_project_benchmark.py    # Phase 2 vs closed project
|   +-- adversarial_tests.py           # Robustness tests
|   +-- degradation_tests.py          # Input quality degradation
+-- data/
    +-- chromadb/                        # Vector store (gitignored)
    +-- models/                          # Trained models (gitignored)
    +-- reference/
        +-- nis2_sectors.json           # Sector to annex mapping
        +-- blueprint_matrix.json       # T x O to classification
        +-- cvss_thresholds.json        # Score to band mapping
        +-- lu_thresholds.json
        +-- be_thresholds.json
        +-- hcpn_crisis_qualification.json
        +-- real_incident_validation.json
```

### 6.4 Gitignored artifacts

| Artifact | Reproduce with |
|----------|---------------|
| `training/data/` | `fetch_bulk_cves.py` (preferred) or `fetch_training_cves.py` (API fallback) |
| `training/data/cvelistV5/` | `fetch_bulk_cves.py --cache-dir` (cvelistV5 clone, ~2GB) |
| `data/chromadb/` | `fetch_training_cves.py` (auto) or `fetch_bulk_cves.py` (default, with dedup) |
| `data/models/` | `train_*.py` scripts |

All large artifacts are reproducible from scripts. Secrets (`.env`, `*.token`) are gitignored.

### 6.5 Hugging Face Hub

**Active models (ML, Phase 1+2 only):**

| Repo | Content |
|------|---------|
| `eromang/cyberscale-scorer-v1` | Phase 1 model weights, tokenizer, config, metrics |
| `eromang/cyberscale-contextual-v1` | Phase 2 model weights (v4: impact inputs + MS geography) |

**Deprecated models (Phase 3, replaced by deterministic rules in v5):**

| Repo | Status |
|------|--------|
| `eromang/cyberscale-technical-v1` | Deprecated — replaced by `derive_t_level()` |
| `eromang/cyberscale-operational-v1` | Deprecated — replaced by `derive_o_level()` |

**Reference datasets:**

| Repo | Content |
|------|---------|
| `eromang/cyberscale-curated-incidents` | 40 real-world single-entity benchmark scenarios |
| `eromang/cyberscale-curated-multi-entity` | 50 multi-entity incident scenarios |
| `eromang/cyberscale-impact-taxonomy` | Unified impact taxonomy (field names/values) |
| `eromang/cyberscale-ir-thresholds` | IR Arts. 5-14 per-entity-type thresholds |
| `eromang/cyberscale-sector-dependencies` | Directed sector dependency graph |
| `eromang/cyberscale-training-cves` | Phase 1 training CVEs |

Token via `HF_TOKEN` environment variable (never committed). Publish with `publish_hf.py`.


## 8. Key design decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| No Claude skills in pipeline | Scripts + models only | Fully self-contained, reproducible, no LLM dependency at runtime |
| ModernBERT-base for 2 ML models (Phase 1+2) | Proven on vulnerability text in closed project | Transfer learning from Variant F encoder; Phase 3 fully deterministic in v5 |
| All-as-text input encoding | Concatenate structured fields as text tokens | Proven approach (closed project 80.7%), simpler than multi-tower |
| ChromaDB vector store | Not QMD | Different data domain (structured vuln records vs analytical notes), typed metadata, portable |
| Dedicated MCP server | Not extending VulnMCP | Clean separation, replaces VulnMCP severity tools |
| 19 sectors (18 NIS2 + 1 non-NIS2) | Full NIS2 coverage | No blind spots for any regulated entity |
| Sector + cross-border as Phase 2 context | Not entity_type | Entity type is too granular; severity thresholds don't vary at that level |
| Fully deterministic Phase 3 (v5) | No ML models | T and O map deterministically from structured fields; ML added no value over rules |
| EU-level only for Phase 3 v1 | No per-MS reconciliation | Task Force reconciliation rules not finalised |
| No national layer in v1 | Designed as future addon | Keep EU-generic, national layers (e.g., HCPN) plug in later |
| Script-generated training data | No LLM or skill dependency | Deterministic, fast, auditable, scalable |
| cvelistV5 bulk download | Not NVD API pagination | Zero API calls, 132k CVE pool, no rate limiting |
| Boundary-enriched sampling | 33% of each band from ±1.0 of band edges | Directly targets regression-to-classification weakness |
| Post-hoc boundary calibration | Push predictions ±0.4 away from boundaries | Reduces band-flip errors without retraining |
| Quality filters + description dedup | SHA-256 dedup, RESERVED/REJECTED rejection, min tokens | Cleaner training signal, no data leakage |
| Retrainable Phase 3 | Versioned alongside taxonomy | Taxonomy v0.1 will evolve before June 2027 |
| Entity/authority separation (v4) | Two MCP tools: entity-facing + authority-facing | Different users need different interfaces and outputs |
| Deterministic T-level (v4) | Replace T-model with rules | T-level maps deterministically from impact fields; ML adds no value |
| Unified impact taxonomy (v4) | Same field names/values across phases | Prevents translation errors between phases |
| IR/NIS2 model split (v4) | Quantitative thresholds for IR entities, ML for others | IR entities have per-sector thresholds in Arts. 5-14 |
| MS geography replaces cross_border (v4) | ms_established + ms_affected list | Richer than bool; cross_border derived |
| Coordination_needs removed from O-model (v4) | Was output, not input | Coordination is a consequence, not an observable input |
| Early warning recommendation (v4) | Structured output with Art. 23(4) guidance | Entities need actionable next steps, not just severity |
| Pluggable national modules (v7) | Registry pattern + per-MS JSON | New MS modules register without changing router logic |
| Three-tier routing (v7) | IR → National → NIS2 ML | EU regulation > national transposition > qualitative fallback |
| HCPN scope: impact on LU (v8) | Not ms_established=LU | Crisis plan protects Luxembourg interests regardless of entity origin |
| Delegated thresholds: undetermined (v8) | Never invent values | Return undetermined + recommend consultation for framework-delegated thresholds |
| Fast-track: bypassed not met (v8) | Criterion 2 status="bypassed" | Analyst sees bypass, not auto-satisfaction |
| Training in separate repo | CyberScale-Training | Different release cycle; inference repo stays lightweight |
| Centralized config (v8) | config.py loads from JSON | Single source of truth for VALID_SECTORS, VALID_ENTITY_TYPES |


## 9. Relationship to prior work

| Project | Relationship |
|---------|-------------|
| CVE-Severity-Context (closed) | Lineage — Phase 2 extends the proven context-dependent approach; Variant F encoder weights seed Phase 1; 1,890 scenarios serve as Phase 2 benchmark; reusable scripts inform training pipeline design |
| VulnMCP | Supersedes severity tools — CyberScale replaces `classify_severity` and `classify_contextual_severity`; VulnMCP API integration patterns inform the multi-source API layer |
| Taxonomy Concept - Incident Severity Dual-Scale Matrix v0.1 - Public | Phase 3 foundation — the dual-scale taxonomy, matrix, and use cases define Phase 3's classification target |

---

## 10. Project tracking

| Document | Purpose |
|----------|---------|
| `CyberScale.md` | Project thesis, goals, success criteria, session log |
| `CyberScale - Master Index.md` | Single entry point — structure, links, scripts, artifacts, status |
| `Progress-Tracker.md` | Session-by-session work log for session resumption |
