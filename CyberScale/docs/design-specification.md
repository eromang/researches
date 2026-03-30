# CyberScale — Design Specification

Multi-phase cyber severity assessment MCP server. Three independent, composable phases covering the full spectrum from raw vulnerability description to EU-level incident classification.

**Version:** 0.1.0
**Status:** Draft
**Lineage:** Builds on the closed CVE-Severity-Context project (ModernBERT classifier, 80.7% accuracy, 1,890 scenarios). Replaces VulnMCP severity tools.


## 2. Three phases

| Phase | Scope | Input | Output | Novel contribution |
|-------|-------|-------|--------|-------------------|
| **1 — Vulnerability Scoring** | Single vulnerability | Description (any quality) + optional CVE ID | 0–10 score (CVSS-compatible) + confidence | Severity estimation without CVSS dependency |
| **2 — Contextual Severity** | Vulnerability in deployment context | Description + NIS2 sector (19 values) + cross-border + optional 0–10 score | Critical/High/Medium/Low + key factors | Context-dependent severity per NIS2 sector |
| **3 — Incident Classification** | Incident (multi-entity, multi-MS) | Incident description + structured impact fields | T-level (T1–T4) + O-level (O1–O4) + Blueprint matrix classification | Cyber Blueprint dual-scale taxonomy implementation |

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
| Cross-border | Yes | true / false |
| Severity score (0–10) | Optional | From Phase 1, CVSS, EUVD, or manual |

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
| `assess_contextual_severity` | 2 | Description + sector + cross-border (+ optional score) | C/H/M/L + key factors |
| `classify_incident_technical` | 3 | Incident description + structured fields | T1–T4 + key factors |
| `classify_incident_operational` | 3 | Incident description + structured fields | O1–O4 + key factors |
| `classify_incident` | 3 | Full incident input | T-level + O-level + matrix classification |
| `refresh_store` | Infra | Optional: date range, source filter | Updated vector store entries |

### 6.2 Four models

| Model | Task | Architecture | Training data |
|-------|------|--------------|---------------|
| Phase 1: Severity scorer | Regression (0–10) | ModernBERT-base, regression head | 10–15k CVEs with CVSS scores |
| Phase 2: Contextual classifier | Classification (4-class) | ModernBERT-base, all-as-text | Script-generated, 18+1 sectors, balanced |
| Phase 3 T-model | Classification (4-class: T1–T4) | ModernBERT-base, all-as-text | 5–8k parametric scenarios |
| Phase 3 O-model | Classification (4-class: O1–O4) | ModernBERT-base, all-as-text | 5–8k parametric scenarios |

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
| ModernBERT-base for all 4 models | Proven on vulnerability text in closed project | Transfer learning from Variant F encoder |
| All-as-text input encoding | Concatenate structured fields as text tokens | Proven approach (closed project 80.7%), simpler than multi-tower |
| ChromaDB vector store | Not QMD | Different data domain (structured vuln records vs analytical notes), typed metadata, portable |
| Dedicated MCP server | Not extending VulnMCP | Clean separation, replaces VulnMCP severity tools |
| 19 sectors (18 NIS2 + 1 non-NIS2) | Full NIS2 coverage | No blind spots for any regulated entity |
| Sector + cross-border as Phase 2 context | Not entity_type | Entity type is too granular; severity thresholds don't vary at that level |
| Two Phase 3 models + deterministic matrix | Not single model | T and O are fundamentally different assessments; matrix is regulatory logic |
| EU-level only for Phase 3 v1 | No per-MS reconciliation | Task Force reconciliation rules not finalised |
| No national layer in v1 | Designed as future addon | Keep EU-generic, national layers (e.g., HCPN) plug in later |
| Script-generated training data | No LLM or skill dependency | Deterministic, fast, auditable, scalable |
| cvelistV5 bulk download | Not NVD API pagination | Zero API calls, 132k CVE pool, no rate limiting |
| Boundary-enriched sampling | 33% of each band from ±1.0 of band edges | Directly targets regression-to-classification weakness |
| Post-hoc boundary calibration | Push predictions ±0.4 away from boundaries | Reduces band-flip errors without retraining |
| Quality filters + description dedup | SHA-256 dedup, RESERVED/REJECTED rejection, min tokens | Cleaner training signal, no data leakage |
| Retrainable Phase 3 | Versioned alongside taxonomy | Taxonomy v0.1 will evolve before June 2027 |


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
