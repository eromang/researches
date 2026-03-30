# CyberScale

**Multi-phase cyber severity assessment MCP server using fine-tuned ModernBERT classifiers.**

Severity assessment operates at three distinct levels — vulnerability, entity, and incident — each requiring different inputs and producing different outputs. Current tools (CVSS, NVD) address only the first level and ignore deployment context. CyberScale provides a unified [MCP](https://modelcontextprotocol.io/) server with three independent, composable phases that cover the full spectrum from raw vulnerability description to EU-level incident classification.

## Architecture

```
MCP Server (FastMCP)
  Phase 1: score_vulnerability, lookup_vulnerability, search_similar
  Phase 2: assess_contextual_severity
  Phase 3: classify_incident_technical, classify_incident_operational, classify_incident
  Infra:   refresh_store

Models: 4x ModernBERT-base (Phase 1 scorer + Phase 2 contextual + Phase 3 T/O classifiers)
Store:  ChromaDB vector store (vulnerability descriptions + embeddings)
Matrix: Blueprint dual-scale incident classification (deterministic, 16-cell)
APIs:   NVD v2.0 + EUVD (ENISA) + CIRCL VulnLookup
```

### Three phases

| Phase | Scope | Input | Output | Model |
|-------|-------|-------|--------|-------|
| 1 — Vulnerability | Raw severity | CVE description + CWE | Score 0-10 (4-class band) | ModernBERT-base classifier |
| 2 — Contextual | Deployment context | Description + NIS2 sector + cross-border | Contextual severity (Critical/High/Medium/Low) | ModernBERT-base classifier |
| 3 — Incident | Crisis classification | Incident description + structured fields | T-level (T1-T4) + O-level (O1-O4) + Blueprint matrix | 2x ModernBERT-base classifiers |

Each phase is independent and can be used standalone. Phase 3 combines two independent classifiers (technical severity + operational severity) with a deterministic matrix lookup based on the [EU Cyber Blueprint](https://eur-lex.europa.eu/eli/reco/2025/682/oj) Council Recommendation.

## Models

| Model | Task | HuggingFace | Key metric |
|-------|------|-------------|------------|
| `cyberscale-scorer-v1` | Vulnerability severity (0-10) | [eromang/cyberscale-scorer-v1](https://huggingface.co/eromang/cyberscale-scorer-v1) | 60.5% band accuracy |
| `cyberscale-contextual-v1` | NIS2 contextual severity | [eromang/cyberscale-contextual-v1](https://huggingface.co/eromang/cyberscale-contextual-v1) | 88.0% predecessor benchmark |
| `cyberscale-technical-v1` | Technical severity (T1-T4) | [eromang/cyberscale-technical-v1](https://huggingface.co/eromang/cyberscale-technical-v1) | 95.4% macro F1 |
| `cyberscale-operational-v1` | Operational severity (O1-O4) | [eromang/cyberscale-operational-v1](https://huggingface.co/eromang/cyberscale-operational-v1) | 96.4% macro F1 |

All models are ModernBERT-base (149M params) with Monte Carlo dropout confidence estimation.

## Quick start

### Install

```bash
cd CyberScale
pip install poetry
poetry install
```

Or with pip:

```bash
pip install -r requirements.txt
pip install -e .
```

### Run MCP server

```bash
poetry run cyberscale
```

### Run tests

```bash
poetry run pytest src/tests/ -v
```

## Training

All models can be reproduced from scratch. Training data is not committed (reproducible via scripts).

### Phase 1 — Vulnerability scorer

```bash
# Fetch CVEs from cvelistV5 (recommended, zero API calls)
poetry run python training/scripts/fetch_bulk_cves.py --output training/data/training_cves.csv

# Train classifier
poetry run python training/scripts/train_scorer.py \
    --data training/data/training_cves.csv \
    --config training/configs/scorer_cls.json \
    --output data/models/scorer
```

### Phase 2 — Contextual severity

```bash
# Generate contextual training data (CVEs x sectors x cross-border)
poetry run python training/scripts/generate_contextual.py \
    --cves training/data/training_cves.csv \
    --rules data/reference/sector_severity_rules.json \
    --config training/configs/contextual_cls.json \
    --output training/data/contextual_training.csv

# Train classifier
poetry run python training/scripts/train_contextual.py \
    --data training/data/contextual_training.csv \
    --config training/configs/contextual_cls.json \
    --output data/models/contextual
```

### Phase 3 — Incident classification

```bash
# Generate incident training data (parametric field combinations)
poetry run python training/scripts/generate_incidents.py \
    --output-t training/data/technical_training.csv \
    --output-o training/data/operational_training.csv

# Train T-model and O-model
poetry run python training/scripts/train_technical.py \
    --data training/data/technical_training.csv \
    --output data/models/technical

poetry run python training/scripts/train_operational.py \
    --data training/data/operational_training.csv \
    --output data/models/operational
```

### Publish to HuggingFace

```bash
export HF_TOKEN=hf_xxxxx
poetry run python training/scripts/publish_hf.py --dry-run  # Preview
poetry run python training/scripts/publish_hf.py             # Publish
```

## Evaluation

### v1 results

| Phase | Metric | Value | Target |
|-------|--------|-------|--------|
| 1 | Band accuracy | 60.5% | > 75% (not met) |
| 2 | Predecessor benchmark | 88.0% | > 80% |
| 2 | NIS2 sectors (all 19) | > 94% | > 75% |
| 3 | T-model macro F1 | 95.4% | > 75% |
| 3 | O-model macro F1 | 96.4% | > 75% |
| 3 | Matrix end-to-end | 96.2% | > 70% |

Phase 3 metrics are on synthetic data only — real-world benchmark pending (see [enhancement roadmap](docs/enhancement-roadmap.md)).

Detailed reports:
- [Phase 2 predecessor benchmark](evaluation/predecessor_benchmark.md)
- [Phase 3 incident benchmark](evaluation/incident_benchmark.md)

## Documentation

- [Design specification](docs/design-specification.md) — Full 3-phase architecture and MCP design
- [Lessons learned](docs/lessons-learned.md) — Retrospective on all 3 phases, validated against outcomes
- [Enhancement roadmap](docs/enhancement-roadmap.md) — Prioritised v2 improvements by impact/effort

## Project structure

```
CyberScale/
├── src/cyberscale/           # Core library
│   ├── server.py             # FastMCP entry point
│   ├── api/                  # NVD, EUVD, CIRCL API clients
│   ├── models/               # Classifier implementations (scorer, contextual, technical, operational)
│   ├── matrix/               # Blueprint dual-scale matrix
│   ├── store/                # ChromaDB vector store
│   └── tools/                # MCP tool definitions
├── src/tests/                # Test suite (84 tests)
├── training/
│   ├── scripts/              # Data fetch, generation, training, evaluation, HF publish
│   └── configs/              # Training hyperparameters (JSON)
├── evaluation/               # Benchmark scripts and reports
├── data/reference/           # Static reference data (NIS2 sectors, CVSS thresholds, matrix)
├── docs/                     # Design docs, lessons learned, roadmap
├── pyproject.toml            # Poetry dependency specification
└── requirements.txt          # Pip-compatible dependencies
```

**Not committed (reproducible):** `data/models/` (train), `data/chromadb/` (refresh), `training/data/` (fetch/generate).

## License

[MIT](LICENSE)
