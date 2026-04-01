# CyberScale — Design Specification

Multi-phase cyber severity assessment MCP server. Three independent, composable phases covering the full spectrum from raw vulnerability description to EU-level incident classification.

**Version:** 5.0
**Status:** v5 complete — fully deterministic Phase 3, sector dependencies, multi-tier (3a/3b), authority feedback
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

### 4.6 National layer

Not included in v1. Designed to be addable as a future extension (e.g., Luxembourg HCPN thresholds) without changing the core architecture. The model takes sector + cross-border only; a national layer addon would add a `jurisdiction` parameter.

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
| `assess_entity_incident` | 2 | Entity incident: description + sector + entity_type + impact fields | Severity + significance (IR/NIS2) + early warning |
| `classify_incident_operational` | 3 | Incident description + operational fields + consequences | O1–O4 + key factors |
| `classify_incident` | 3 | Full incident input | Deterministic T-level + O-level + matrix |
| `assess_incident` | 3 | Entity notification dicts | Aggregation + T-level + O-level + matrix classification |
| `assess_national_incident` | 3a | Entity notifications from single MS | National T/O/matrix + cross-border flag |
| `assess_eu_incident` | 3b | National classifications + CyCLONe Officer inputs | EU-level classification + coordination level |
| `assess_full_pipeline` | 1+2 | Description + sector + MS geography | Phase 1 score + Phase 2 severity |
| `refresh_store` | Infra | Optional: date range, source filter | Updated vector store entries |

### 6.2 Four models

| Model | Task | Architecture | Training data |
|-------|------|--------------|---------------|
| Phase 1: Severity scorer | Classification (4-class bands) | ModernBERT-base, classification head | ~45k CVEs with CVSS scores |
| Phase 2: Contextual classifier | Classification (4-class) | ModernBERT-base, all-as-text | 32k scenarios (CVEs x sectors x impact) |
| Phase 3 T-level | Deterministic rules | No ML — `derive_t_level()` | Rules from impact taxonomy |
| Phase 3 O-level | Deterministic rules | No ML — `derive_o_level()` | Rules from consequence dimensions |
| IR thresholds | Deterministic per-entity-type | No ML — `assess_ir_significance()` | Arts. 5-14 thresholds |
| Phase 3 T-model (deprecated) | Was classification (T1–T4) | ModernBERT-base | Kept for reference, not used in inference |

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
|   +-- matrix/
|   |   +-- dual_scale.py              # Blueprint matrix lookup
|   +-- tools/
|       +-- vulnerability.py            # Phase 1 MCP tools
|       +-- contextual.py              # Phase 2 MCP tools
|       +-- incident.py                # Phase 3 MCP tools
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

| Repo | Content | Script |
|------|---------|--------|
| `CyberScale/cyberscale-scorer-v1` | Model weights, tokenizer, config, metrics, model card | `publish_hf.py` |
| `CyberScale/cyberscale-training-cves` | Training CSV, pre-analysis report, dataset card | `publish_hf.py --dataset-only` |

Token via `HF_TOKEN` environment variable (never committed). Supports `--dry-run`.


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
