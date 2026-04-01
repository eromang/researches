# CyberScale

**Multi-phase cyber severity assessment MCP server using fine-tuned ModernBERT classifiers.**

Severity assessment operates at three distinct levels — vulnerability, entity, and incident — each requiring different inputs and producing different outputs. Current tools (CVSS, NVD) address only the first level and ignore deployment context. CyberScale provides a unified [MCP](https://modelcontextprotocol.io/) server with three independent, composable phases that cover the full spectrum from raw vulnerability description to EU-level incident classification.

## Architecture

```
MCP Server (FastMCP)
  Phase 1: score_vulnerability, lookup_vulnerability, search_similar
  Phase 2: assess_contextual_severity (vulnerability mode)
           assess_entity_incident    (incident mode — entity-facing)
  Phase 3: classify_incident, classify_incident_operational
           assess_incident           (authority-facing, multi-entity)
           assess_national_incident  (Phase 3a — single MS)
           assess_eu_incident        (Phase 3b — CyCLONe Officers)
  Infra:   refresh_store

Models: 2x ModernBERT-base (Phase 1 scorer + Phase 2 contextual only)
        + deterministic T-level (aggregation rules, no ML)
        + deterministic O-level (derive_o_level(), no ML)
        + IR threshold logic (per-entity-type, Arts. 5-14)
        Phase 3 is fully deterministic — zero ML models.
Store:  ChromaDB vector store (vulnerability descriptions + embeddings)
Matrix: Blueprint dual-scale incident classification (deterministic, 16-cell)
APIs:   NVD v2.0 + EUVD (ENISA) + CIRCL VulnLookup
Ref:    impact_taxonomy.json, ir_incident_thresholds.json, nis2_entity_types.json,
        sector_dependencies.json
```

### Three phases

| Phase | Scope | Input | Output | Model |
|-------|-------|-------|--------|-------|
| 1 — Vulnerability | Raw severity | CVE description + CWE | Score 0-10 (4-class band) | ModernBERT-base classifier |
| 2 — Contextual | Deployment context | Description + NIS2 sector + MS geography | Contextual severity (Critical/High/Medium/Low) | ModernBERT-base classifier |
| 2 — Entity Incident | Entity self-assessment | Above + impact fields + entity_type | Severity + significant_incident + early warning | ML model + IR thresholds |
| 3 — Incident | Authority classification | Entity notifications list | T-level + O-level + Blueprint matrix | Fully deterministic (rules + matrix) |

Each phase is independent and can be used standalone. Phase 3 uses deterministic T-level derivation (`derive_t_level()`) and deterministic O-level derivation (`derive_o_level()`) from aggregated impact fields, combined via a [EU Cyber Blueprint](https://eur-lex.europa.eu/eli/reco/2025/682/oj) matrix lookup. Zero ML models in Phase 3.

### Entity vs Authority separation (v4)

```
Entity path:  assess_entity_incident → IR/NIS2 significance → early warning
                ↓ (notifications)
Authority path: assess_incident → aggregation → T-level (deterministic) → O-level (deterministic) → matrix
```

- **Entity-facing:** Single entity assesses its own incident. Routes to IR quantitative thresholds (14 entity types from Implementing Regulation Arts. 5-14) or NIS2 ML model. Recommends early warning per Art. 23(4)(a).
- **Authority-facing:** CSIRT/EU-CyCLONe aggregates entity notifications. Deterministic T-level from worst-case impacts. Deterministic O-level from consequence dimensions. Matrix produces final classification. Multi-tier: Phase 3a (national, single MS) + Phase 3b (EU, CyCLONe Officers).

## Models

| Model | Task | Key metric | HuggingFace |
|-------|------|------------|-------------|
| Scorer v6 | Vulnerability severity (0-10) + CVSS vector | 62.3% band accuracy | [eromang/cyberscale-scorer-v6](https://huggingface.co/eromang/cyberscale-scorer-v6) |
| Scorer v1 | Vulnerability severity (0-10) | 60.5% band accuracy | [eromang/cyberscale-scorer-v1](https://huggingface.co/eromang/cyberscale-scorer-v1) |
| Contextual v1 | NIS2 contextual severity + incident mode | 81.5% macro F1 | [eromang/cyberscale-contextual-v1](https://huggingface.co/eromang/cyberscale-contextual-v1) |
| T-level | Deterministic from impact fields | 100% (rules-based) | — |
| O-level | Deterministic from consequence dimensions | 100% (rules-based) | — |
| IR thresholds | Per-entity-type significance | 100% (deterministic) | [eromang/cyberscale-ir-thresholds](https://huggingface.co/datasets/eromang/cyberscale-ir-thresholds) |

ML models (Phase 1+2 only) are ModernBERT-base (149M params) with Monte Carlo dropout confidence estimation (5 passes). Phase 3 is fully deterministic.

### Reference datasets on HuggingFace

| Dataset | Content |
|---------|---------|
| [cyberscale-curated-incidents](https://huggingface.co/datasets/eromang/cyberscale-curated-incidents) | 40 real-world single-entity incident scenarios |
| [cyberscale-curated-multi-entity](https://huggingface.co/datasets/eromang/cyberscale-curated-multi-entity) | 50 multi-entity incident scenarios |
| [cyberscale-impact-taxonomy](https://huggingface.co/datasets/eromang/cyberscale-impact-taxonomy) | Unified impact field names/values (NIS2 Art. 23) |
| [cyberscale-ir-thresholds](https://huggingface.co/datasets/eromang/cyberscale-ir-thresholds) | IR Arts. 5-14 per-entity-type significance thresholds |
| [cyberscale-sector-dependencies](https://huggingface.co/datasets/eromang/cyberscale-sector-dependencies) | Directed sector dependency graph (ENISA/CER) |

Deprecated models (kept for reference): [cyberscale-technical-v1](https://huggingface.co/eromang/cyberscale-technical-v1), [cyberscale-operational-v1](https://huggingface.co/eromang/cyberscale-operational-v1) — replaced by `derive_t_level()` / `derive_o_level()` in v5.

## Quick start

### Install

```bash
cd CyberScale
pip install poetry
poetry install
```

### Run MCP server

```bash
poetry run cyberscale
```

### Run tests

```bash
poetry run pytest src/tests/ -v   # 279 tests
```

## Usage

### Phase 1: Vulnerability scoring

Predicts a CVSS-compatible severity score (0-10) from a vulnerability description.

```python
import sys; sys.path.insert(0, 'src')
from cyberscale.models.scorer import SeverityScorer

scorer = SeverityScorer('data/models/scorer')
result = scorer.predict('Buffer overflow in OpenSSL allows remote code execution via crafted certificate')

print(f'Score: {result.score:.1f}/10')  # 7.8
print(f'Band: {result.band}')           # High
print(f'Confidence: {result.confidence}') # high
```

### Phase 2: Contextual severity (vulnerability mode)

Adjusts severity based on NIS2 sector, member state geography, and deployment context. Optionally accepts Phase 1 score.

```python
from cyberscale.models.contextual import ContextualClassifier

ctx = ContextualClassifier('data/models/contextual')
result = ctx.predict(
    description='SQL injection in patient records system',
    sector='health',
    ms_established='DE',         # ISO 3166-1 alpha-2
    ms_affected=['FR', 'NL'],    # Cross-border MS (derived: cross_border=True)
    score=7.8,                   # Optional — from Phase 1 or CVSS
    entity_type='healthcare_provider',
)

print(f'Severity: {result.severity}')       # Critical
print(f'Key factors: {result.key_factors}') # ['health sector', 'cross-border exposure (2 MS affected)', ...]
```

### Phase 2: Entity incident assessment (incident mode)

When `entity_affected=True`, adds impact fields for incident significance determination.

```python
# Uses the same ContextualClassifier, but with incident impact fields
result = ctx.predict(
    description='Ransomware encrypted hospital systems',
    sector='health',
    ms_established='DE',
    ms_affected=['FR'],
    entity_type='healthcare_provider',
    entity_affected=True,
    service_impact='unavailable',      # none|partial|degraded|unavailable|sustained
    data_impact='exfiltrated',         # none|accessed|exfiltrated|compromised|systemic
    financial_impact='severe',         # none|minor|significant|severe
    safety_impact='health_damage',     # none|health_risk|health_damage|death
    affected_persons_count=50000,
    suspected_malicious=True,
    impact_duration_hours=72,
)
```

### Phase 2: IR/NIS2 significance routing

IR entity types (cloud, DNS, MSP, etc.) use deterministic thresholds from Implementing Regulation Arts. 5-14:

```python
from cyberscale.models.contextual_ir import is_ir_entity, assess_ir_significance

# Check routing
is_ir_entity('cloud_computing_provider')  # True
is_ir_entity('healthcare_provider')        # False

# IR assessment (deterministic)
result = assess_ir_significance(
    entity_type='cloud_computing_provider',
    service_impact='unavailable',
    affected_persons_count=5000,  # threshold for cloud: 1000
)
print(result.significant_incident)   # True
print(result.triggered_criteria)     # ['service_unavailability', 'affected_persons >= 1000']
```

### Phase 2: Early warning recommendation

```python
from cyberscale.models.early_warning import recommend_early_warning

ew = recommend_early_warning(
    significant_incident=True,
    suspected_malicious=True,
    cross_border=True,
)
print(f'Recommended: {ew.recommended}')   # True
print(f'Deadline: {ew.deadline}')         # 24h
print(f'Next step: {ew.next_step}')       # Submit early warning per Art. 23(4)(a)...
```

### Phase 3: Incident classification (authority pipeline)

Aggregates entity notifications, derives deterministic T-level and O-level, looks up Blueprint matrix. Fully deterministic — zero ML models.

```python
from cyberscale.aggregation import aggregate_entity_notifications, derive_o_level
from cyberscale.matrix.dual_scale import classify_incident

# Entity notifications (from assess_entity_incident outputs)
notifications = [
    {"sector": "health", "ms_established": "DE", "ms_affected": ["FR"],
     "service_impact": "unavailable", "data_impact": "exfiltrated",
     "financial_impact": "severe", "safety_impact": "health_damage",
     "affected_persons_count": 50000},
    {"sector": "energy", "ms_established": "FR",
     "service_impact": "degraded", "data_impact": "accessed",
     "financial_impact": "minor", "safety_impact": "none",
     "affected_persons_count": 5000},
]

# Step 1: Aggregate
agg = aggregate_entity_notifications(notifications)
print(f'T-level: {agg.t_level}')           # T3 (unavailable service impact)
print(f'Sectors: {agg.sector_list}')       # ['energy', 'health']
print(f'Cascading: {agg.cascading}')       # limited (2 sectors)

# Step 2: Deterministic O-level
o_level, o_basis = derive_o_level(
    sectors_affected=agg.sectors_affected,
    entity_relevance='essential',
    ms_affected=agg.ms_affected,
    cross_border_pattern=agg.cross_border_pattern,
    capacity_exceeded=agg.capacity_exceeded,
    financial_impact=agg.financial_impact,
    safety_impact=agg.safety_impact,
    affected_persons_count=agg.affected_persons_count,
    affected_entities=agg.affected_entities,
)

# Step 3: Matrix
matrix = classify_incident(agg.t_level, o_level)
print(f'Classification: {matrix.label}')  # Large-scale
print(f'Provision: {matrix.provision}')   # 7(c)
```

### MCP tools

When running as an MCP server (`poetry run cyberscale`), the following tools are available:

| Tool | Phase | Description |
|------|-------|-------------|
| `score_vulnerability` | 1 | Score a CVE description (0-10) |
| `lookup_vulnerability` | 1 | Look up a CVE by ID from NVD/EUVD/CIRCL |
| `search_similar` | 1 | Find similar vulnerabilities in ChromaDB |
| `assess_contextual_severity` | 2 | Contextual severity with NIS2 sector + MS geography |
| `assess_entity_incident` | 2 | Entity incident: severity + significance + early warning |
| `classify_incident_operational` | 3 | Operational severity (O1-O4) with consequence dimensions |
| `classify_incident` | 3 | Deterministic T-level + O-level + Blueprint matrix |
| `assess_incident` | 3 | Authority pipeline: entity notifications → aggregation → classification |
| `assess_national_incident` | 3a | National CSIRT: single-MS entity notifications → national classification |
| `assess_eu_incident` | 3b | EU-CyCLONe: national classifications + CyCLONe Officer inputs → EU classification |
| `assess_full_pipeline` | All | Phase 1 -> 2 in one call |
| `refresh_store` | Infra | Refresh ChromaDB vector store |

### Unified impact taxonomy

All impact fields use consistent values across phases (defined in `data/reference/impact_taxonomy.json`):

| Dimension | Values | Phases |
|-----------|--------|--------|
| `service_impact` | none, partial, degraded, unavailable, sustained | 2, 3T |
| `data_impact` | none, accessed, exfiltrated, compromised, systemic | 2, 3T |
| `financial_impact` | none, minor, significant, severe | 2, 3O |
| `safety_impact` | none, health_risk, health_damage, death | 2, 3O |
| `affected_persons_count` | int | 2, 3O |
| `cascading` | none, limited, cross_sector, uncontrolled | 3T |

## Training

All models can be reproduced from scratch. Training data is not committed (reproducible via scripts).

### Phase 1 — Vulnerability scorer (v6 multi-task)

```bash
# Fetch training data with CVSS vectors + CPE vendor/product
poetry run python training/scripts/fetch_bulk_cves.py \
    --output training/data/training_cves_v6.csv \
    --config training/configs/scorer_multitask.json \
    --cache-dir training/data/cvelistV5 \
    --cap-per-band 15000 --no-store

# Train multi-task model (9 heads: 1 band + 8 CVSS components)
poetry run python training/scripts/train_scorer_multitask.py \
    --data training/data/training_cves_v6.csv \
    --config training/configs/scorer_multitask.json \
    --output data/models/scorer_v6
```

### Phase 1 — Vulnerability scorer (v1 baseline)

```bash
poetry run python training/scripts/fetch_bulk_cves.py --output training/data/training_cves.csv
poetry run python training/scripts/train_scorer.py \
    --data training/data/training_cves.csv \
    --config training/configs/scorer_cls.json \
    --output data/models/scorer
```

### Phase 2 — Contextual severity

```bash
poetry run python training/scripts/generate_contextual.py \
    --cves training/data/training_cves.csv \
    --rules data/reference/sector_severity_rules.json \
    --config training/configs/contextual_cls.json \
    --output training/data/contextual_training.csv

poetry run python training/scripts/train_contextual.py \
    --data training/data/contextual_training.csv \
    --config training/configs/contextual_cls.json \
    --output data/models/contextual
```

### Phase 3 — Incident classification (fully deterministic in v5)

Phase 3 no longer requires ML model training. Both T-level and O-level are derived
deterministically via `derive_t_level()` and `derive_o_level()`. The training scripts
below are kept for reference only:

```bash
# Reference only — Phase 3 is fully deterministic in v5
poetry run python training/scripts/generate_incidents.py \
    --output-t training/data/technical_training.csv \
    --output-o training/data/operational_training.csv
```

## Evaluation

### v6 results (Phase 1 multi-task)

| Metric | v1 baseline | v6 multi-task | Target |
|--------|-------------|---------------|--------|
| Band accuracy | 60.5% | 62.3% (+1.8pp) | > 70% |
| Macro F1 | 56.4% | 58.4% (+2.0pp) | > 65% |

v6 uses multi-task learning with 8 CVSS vector component heads as auxiliary tasks. CPE vendor/product enrichment is implemented but pending full retrain.

### v5 results

| Phase | Metric | Value | Target |
|-------|--------|-------|--------|
| 1 | Band accuracy | 60.5% | > 75% (not met) |
| 2 | Contextual macro F1 | 81.5% | > 75% |
| 3 | Aggregation T-level (deterministic) | 100% | 100% |
| 3 | O-level (deterministic) | 100% | 100% |
| 3 | Matrix end-to-end (deterministic) | 100% | > 70% |
| 3 | Multi-entity benchmark (50 curated) | 100% | > 70% |
| 3 | Illustrative use cases | 6/6 | 6/6 |

Detailed reports:
- [Phase 3 synthetic benchmark](evaluation/incident_benchmark.md)
- [Multi-entity aggregation benchmark](evaluation/multi_entity_benchmark.md)
- [Phase 2 predecessor benchmark](evaluation/predecessor_benchmark.md)

## Documentation

- [Design specification](docs/design-specification.md) — Full 3-phase architecture and MCP design
- [Lessons learned](docs/lessons-learned.md) — Retrospective on all phases
- [Enhancement roadmap](docs/enhancement-roadmap.md) — Prioritised improvements by impact/effort
- [v4 implementation plan](docs/superpowers/plans/2026-03-31-v4-incident-aware-pipeline.md) — Phase A/B/C task breakdown

## Project structure

```
CyberScale/
├── src/cyberscale/           # Core library
│   ├── server.py             # FastMCP entry point
│   ├── api/                  # NVD, EUVD, CIRCL API clients
│   ├── models/               # Classifier implementations
│   │   ├── scorer.py         # Phase 1 vulnerability scoring (v1)
│   │   ├── scorer_multitask.py # Phase 1 multi-task scorer (v6)
│   │   ├── contextual.py     # Phase 2 contextual + incident mode
│   │   ├── contextual_ir.py  # Phase 2 IR threshold logic
│   │   ├── early_warning.py  # Phase 2 early warning recommendation
│   │   ├── technical.py      # Phase 3 T-model (deprecated for inference)
│   │   └── operational.py    # Phase 3 O-model (deprecated — replaced by derive_o_level)
│   ├── aggregation.py        # Multi-entity aggregation + T-level + O-level
│   ├── feedback.py           # Authority feedback store + regression benchmark
│   ├── matrix/               # Blueprint dual-scale matrix
│   ├── pipeline.py           # Composable Phase 1→2→3 pipeline
│   ├── store/                # ChromaDB vector store
│   └── tools/                # MCP tool definitions
│       ├── vulnerability.py      # Phase 1 tools
│       ├── contextual.py         # Phase 2 vulnerability mode
│       ├── entity_incident.py    # Phase 2 entity incident mode
│       ├── incident.py           # Phase 3 classification
│       ├── authority_incident.py  # Phase 3 authority pipeline
│       ├── national_incident.py  # Phase 3a national CSIRT tool
│       ├── eu_incident.py        # Phase 3b EU-CyCLONe tool
│       └── store_tools.py        # ChromaDB tools
├── src/tests/                # Test suite (279 tests)
├── training/
│   ├── scripts/              # Data generation, training, evaluation
│   └── configs/              # Training hyperparameters (JSON)
├── evaluation/               # Benchmark scripts and reports
├── data/reference/           # Static reference data
│   ├── impact_taxonomy.json      # Unified impact field names/values
│   ├── ir_incident_thresholds.json # IR per-entity-type thresholds
│   ├── nis2_entity_types.json    # 55+ NIS2 entity types
│   ├── blueprint_matrix.json     # 4x4 T/O matrix
│   ├── sector_severity_rules.json # NIS2 escalation rules
│   ├── curated_incidents.json    # 40 curated single-entity incidents
│   ├── curated_multi_entity_incidents.json # 50 multi-entity scenarios
│   └── sector_dependencies.json  # Sector dependency graph for cascading propagation
├── docs/                     # Design docs, lessons learned, roadmap
├── pyproject.toml            # Poetry dependency specification
└── requirements.txt          # Pip-compatible dependencies
```

**Not committed (reproducible):** `data/models/` (train), `data/chromadb/` (refresh), `training/data/` (fetch/generate).

## License

[MIT](LICENSE)
