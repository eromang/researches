"""Publish CyberScale model and dataset to Hugging Face Hub.

Publishes:
  1. Model repo: CyberScale/cyberscale-scorer-v1 (weights, tokenizer, config, metrics)
  2. Dataset repo: CyberScale/cyberscale-training-cves (CSV, pre-analysis report)

Token is read from HF_TOKEN env var (never committed).

Usage:
    export HF_TOKEN=hf_xxxxx

    # Publish both model and dataset:
    cd CyberScale
    poetry run python training/scripts/publish_hf.py

    # Publish model only:
    poetry run python training/scripts/publish_hf.py --model-only

    # Publish dataset only:
    poetry run python training/scripts/publish_hf.py --dataset-only

    # Dry run (show what would be published):
    poetry run python training/scripts/publish_hf.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from huggingface_hub import HfApi, create_repo

PROJECT_ROOT = Path(__file__).resolve().parents[2]

HF_ORG = "eromang"
MODEL_REPO = f"{HF_ORG}/cyberscale-scorer-v1"
CONTEXTUAL_REPO = f"{HF_ORG}/cyberscale-contextual-v1"
TECHNICAL_REPO = f"{HF_ORG}/cyberscale-technical-v1"
OPERATIONAL_REPO = f"{HF_ORG}/cyberscale-operational-v1"
DATASET_REPO = f"{HF_ORG}/cyberscale-training-cves"
CONTEXTUAL_DATASET_REPO = f"{HF_ORG}/cyberscale-contextual-training"
TECHNICAL_DATASET_REPO = f"{HF_ORG}/cyberscale-technical-training"
OPERATIONAL_DATASET_REPO = f"{HF_ORG}/cyberscale-operational-training"
CURATED_DATASET_REPO = f"{HF_ORG}/cyberscale-curated-incidents"

MODEL_DIR = PROJECT_ROOT / "data" / "models" / "scorer"
CONTEXTUAL_DIR = PROJECT_ROOT / "data" / "models" / "contextual"
TECHNICAL_DIR = PROJECT_ROOT / "data" / "models" / "technical"
OPERATIONAL_DIR = PROJECT_ROOT / "data" / "models" / "operational"
DATASET_DIR = PROJECT_ROOT / "training" / "data"
CURATED_SOURCE = PROJECT_ROOT / "data" / "reference" / "curated_incidents.json"


# ---------------------------------------------------------------------------
# Model card
# ---------------------------------------------------------------------------

def generate_model_card(metrics: dict) -> str:
    """Generate README.md for the model repo."""
    return f"""---
language: en
license: apache-2.0
library_name: transformers
tags:
  - cybersecurity
  - vulnerability
  - cvss
  - severity-scoring
  - modernbert
pipeline_tag: text-classification
model-index:
  - name: cyberscale-scorer-v1
    results:
      - task:
          type: regression
          name: CVSS Score Prediction
        metrics:
          - name: MAE
            type: mae
            value: {metrics.get('mae', 'N/A')}
          - name: RMSE
            type: rmse
            value: {metrics.get('rmse', 'N/A')}
          - name: Pearson r
            type: pearsonr
            value: {metrics.get('pearson_r', 'N/A')}
          - name: Band Accuracy
            type: accuracy
            value: {metrics.get('band_accuracy', 'N/A')}
---

# CyberScale Scorer v1

**Vulnerability severity scorer (0-10)** based on ModernBERT-base. Predicts CVSS-compatible severity scores from vulnerability descriptions, with Monte Carlo dropout confidence estimation.

## Model Description

- **Architecture:** ModernBERT-base with regression head (sigmoid x 10)
- **Training:** Huber loss with boundary-aware weighting, early stopping
- **Confidence:** Monte Carlo dropout (20 forward passes) maps variance to high/medium/low
- **Post-hoc calibration:** Predictions near band boundaries (4.0, 7.0, 9.0) are nudged away to reduce band-flip errors

## Intended Use

Score vulnerability severity from text descriptions when authoritative CVSS scores are unavailable. Part of the CyberScale multi-phase cyber severity assessment system.

**Input format:** `<description> [SEP] cwe: <CWE-ID>` (CWE optional)

## Training Data

- **Source:** cvelistV5 (CVE.org), quality-filtered and deduplicated
- **Size:** 12,000 CVEs (3,000 per CVSS band)
- **CVSS version:** 88% v3.1, 12% v3.0
- **Selection:** Boundary-enriched sampling (33% from +/-1.0 of band edges)
- **Quality filters:** RESERVED/REJECTED rejection, min 10 tokens, SHA-256 description dedup

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| MAE | {metrics.get('mae', 'N/A')} | < 1.0 |
| RMSE | {metrics.get('rmse', 'N/A')} | - |
| Pearson r | {metrics.get('pearson_r', 'N/A')} | - |
| Band Accuracy | {metrics.get('band_accuracy', 'N/A')} | > 0.75 |

## CVSS Bands

| Band | Range |
|------|-------|
| Critical | 9.0 - 10.0 |
| High | 7.0 - 8.9 |
| Medium | 4.0 - 6.9 |
| Low | 0.0 - 3.9 |

## Usage

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model = AutoModelForSequenceClassification.from_pretrained("{MODEL_REPO}", num_labels=1)
tokenizer = AutoTokenizer.from_pretrained("{MODEL_REPO}")

text = "Buffer overflow in libpng allows remote code execution via crafted PNG file [SEP] cwe: CWE-119"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=192)

with torch.no_grad():
    score = torch.sigmoid(model(**inputs).logits).item() * 10.0
    print(f"Severity: {{score:.1f}}/10")
```

## Limitations

- Trained on English descriptions only
- Band accuracy (~70%) limited by regression-to-classification boundary effects
- Confidence estimation requires dropout layers (set classifier_dropout > 0)

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


# ---------------------------------------------------------------------------
# Dataset card
# ---------------------------------------------------------------------------

def generate_dataset_card(csv_path: Path) -> str:
    """Generate README.md for the dataset repo."""
    import pandas as pd
    df = pd.read_csv(csv_path)

    return f"""---
language: en
license: apache-2.0
task_categories:
  - text-classification
task_ids:
  - multi-class-classification
tags:
  - cybersecurity
  - vulnerability
  - cvss
  - cve
size_categories:
  - 10K<n<100K
---

# CyberScale Training CVEs

Training dataset for the CyberScale vulnerability severity scorer. Contains {len(df):,} CVEs with CVSS v3.x scores, descriptions, and CWE classifications.

## Dataset Description

- **Source:** cvelistV5 (CVE.org GitHub repository)
- **Quality filters:** RESERVED/REJECTED rejection, min 10 tokens, SHA-256 description dedup
- **Selection:** Boundary-enriched sampling (33% from +/-1.0 of CVSS band edges)
- **Balance:** Equal samples per CVSS band (Critical/High/Medium/Low)

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `cve_id` | string | CVE identifier (e.g., CVE-2024-1234) |
| `description` | string | Vulnerability description (English) |
| `cvss_score` | float | CVSS v3.x base score (0.0-10.0) |
| `cvss_version` | string | CVSS version (3.0 or 3.1) |
| `cwe` | string | CWE identifier (e.g., CWE-79), may be null |
| `source` | string | Data source (cvelistV5) |

## Statistics

- **Total CVEs:** {len(df):,}
- **CVSS version:** {(df.cvss_version==3.1).mean()*100:.0f}% v3.1
- **CWE coverage:** {df.cwe.notna().mean()*100:.0f}%
- **Unique CWEs:** {df.cwe.nunique()}

### Band Distribution

| Band | Count | Score Range |
|------|-------|-------------|
| Critical | {len(df[df.cvss_score >= 9.0]):,} | 9.0 - 10.0 |
| High | {len(df[(df.cvss_score >= 7.0) & (df.cvss_score < 9.0)]):,} | 7.0 - 8.9 |
| Medium | {len(df[(df.cvss_score >= 4.0) & (df.cvss_score < 7.0)]):,} | 4.0 - 6.9 |
| Low | {len(df[df.cvss_score < 4.0]):,} | 0.0 - 3.9 |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("{DATASET_REPO}")
```

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


# ---------------------------------------------------------------------------
# Contextual model card
# ---------------------------------------------------------------------------

def generate_contextual_model_card(metrics: dict) -> str:
    """Generate README.md for the contextual model repo."""
    return f"""---
language: en
license: apache-2.0
library_name: transformers
tags:
  - cybersecurity
  - vulnerability
  - nis2
  - contextual-severity
  - modernbert
pipeline_tag: text-classification
model-index:
  - name: cyberscale-contextual-v1
    results:
      - task:
          type: text-classification
          name: Contextual Severity Classification
        metrics:
          - name: Accuracy
            type: accuracy
            value: {metrics.get('accuracy', 'N/A')}
          - name: Macro F1
            type: f1
            value: {metrics.get('macro_f1', 'N/A')}
          - name: Predecessor Benchmark
            type: accuracy
            value: 0.880
---

# CyberScale Contextual Severity v1

**NIS2 context-aware vulnerability severity classifier.** Takes a CVE description, deployment sector, cross-border status, and CVSS score — produces a contextual severity (Critical/High/Medium/Low) that accounts for regulatory sector impact.

## Model Description

- **Architecture:** ModernBERT-base with 4-class classification head
- **Training:** Mixed synthetic rules + 1,850 human-curated predecessor scenarios (30% weight)
- **Confidence:** Monte Carlo dropout (20 passes) maps variance to high/medium/low
- **Sectors:** 19 NIS2 sectors (18 regulated + non-NIS2)

## Intended Use

Assess contextual severity of vulnerabilities in specific deployment contexts. A Critical CVSS vulnerability in a non-regulated small business may be Medium contextually, while a Medium CVSS vulnerability in cross-border healthcare infrastructure may be High.

**Input format:** `<description> [SEP] sector: <sector_id> cross_border: <true|false> score: <cvss_score>`

## Training Data

- **Synthetic:** 32,000 scenarios from deterministic NIS2 escalation rules (CVEs x sectors x cross-border)
- **Predecessor:** 1,850 human-curated scenarios from CVE-Severity-Context project (7x oversampled, 30% weight)
- **Balance:** 8,000 per severity class after balancing

## Metrics

### Test set (synthetic + predecessor mix)

| Metric | Value |
|--------|-------|
| Accuracy | {metrics.get('accuracy', 'N/A')} |
| Macro F1 | {metrics.get('macro_f1', 'N/A')} |
| All 19 sectors | > 71% |

### Predecessor benchmark (1,833 human-curated scenarios)

| Metric | Value |
|--------|-------|
| Accuracy | **88.0%** |
| Delta vs Variant F (80.7%) | **+7.3pp** |
| NIS2 sectors | > 94% |
| Non-NIS2 | 65.3% |

## Valid Sectors

`banking`, `chemicals`, `digital_infrastructure`, `digital_providers`, `drinking_water`, `energy`, `financial_market`, `food`, `health`, `ict_service_management`, `manufacturing`, `non_nis2`, `postal`, `public_administration`, `research`, `space`, `transport`, `waste_management`, `waste_water`

## Usage

```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

model = AutoModelForSequenceClassification.from_pretrained("{CONTEXTUAL_REPO}", num_labels=4)
tokenizer = AutoTokenizer.from_pretrained("{CONTEXTUAL_REPO}")

text = "SQL injection in login form [SEP] sector: health cross_border: true score: 7.5"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=192)

with torch.no_grad():
    logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    label = ["Low", "Medium", "High", "Critical"][probs.argmax().item()]
    print(f"Contextual severity: {{label}}")
```

## Limitations

- Small-deployment / non-NIS2 scenarios are the weakest (51% accuracy)
- Trained on English descriptions only
- Does not capture sub-sector deployment context (e.g., clinical vs billing system in healthcare)

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------

def publish_model(api: HfApi, dry_run: bool = False) -> None:
    """Publish model weights, tokenizer, config, and metrics."""
    if not MODEL_DIR.exists():
        print(f"ERROR: Model not found at {MODEL_DIR}")
        return

    metrics = {}
    metrics_path = MODEL_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())

    # Generate model card
    card = generate_model_card(metrics)
    card_path = MODEL_DIR / "README.md"
    card_path.write_text(card)

    files = list(MODEL_DIR.glob("*"))
    print(f"\n--- Model: {MODEL_REPO} ---")
    print(f"Files to upload ({len(files)}):")
    for f in sorted(files):
        size = f.stat().st_size
        print(f"  {f.name} ({size / 1024:.0f} KB)" if size < 1024 * 1024
              else f"  {f.name} ({size / 1024 / 1024:.0f} MB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(MODEL_REPO, repo_type="model", exist_ok=True, token=api.token)
    api.upload_folder(
        folder_path=str(MODEL_DIR),
        repo_id=MODEL_REPO,
        repo_type="model",
        commit_message="Upload CyberScale scorer v1 model",
        ignore_patterns=["training_state.pt"],  # Resume state is local-only
    )
    print(f"Published: https://huggingface.co/{MODEL_REPO}")


def publish_contextual(api: HfApi, dry_run: bool = False) -> None:
    """Publish contextual severity model weights, tokenizer, config, and metrics."""
    if not CONTEXTUAL_DIR.exists():
        print(f"ERROR: Contextual model not found at {CONTEXTUAL_DIR}")
        return

    metrics = {}
    metrics_path = CONTEXTUAL_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())

    card = generate_contextual_model_card(metrics)
    card_path = CONTEXTUAL_DIR / "README.md"
    card_path.write_text(card)

    files = list(CONTEXTUAL_DIR.glob("*"))
    print(f"\n--- Contextual Model: {CONTEXTUAL_REPO} ---")
    print(f"Files to upload ({len(files)}):")
    for f in sorted(files):
        size = f.stat().st_size
        print(f"  {f.name} ({size / 1024:.0f} KB)" if size < 1024 * 1024
              else f"  {f.name} ({size / 1024 / 1024:.0f} MB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(CONTEXTUAL_REPO, repo_type="model", exist_ok=True, token=api.token)
    api.upload_folder(
        folder_path=str(CONTEXTUAL_DIR),
        repo_id=CONTEXTUAL_REPO,
        repo_type="model",
        commit_message="Upload CyberScale contextual severity v1 model (88% predecessor benchmark)",
        ignore_patterns=["training_state.pt"],
    )
    print(f"Published: https://huggingface.co/{CONTEXTUAL_REPO}")


def generate_technical_model_card(metrics: dict) -> str:
    """Generate README.md for the technical severity model repo."""
    return f"""---
language: en
license: apache-2.0
library_name: transformers
tags:
  - cybersecurity
  - incident-classification
  - technical-severity
  - modernbert
  - nis2
  - cyber-blueprint
pipeline_tag: text-classification
model-index:
  - name: cyberscale-technical-v1
    results:
      - task:
          type: text-classification
          name: Technical Severity Classification (T1-T4)
        metrics:
          - name: Accuracy
            type: accuracy
            value: {metrics.get('accuracy', 'N/A')}
          - name: Macro F1
            type: f1
            value: {metrics.get('macro_f1', 'N/A')}
---

# CyberScale Technical Severity v1

**Incident technical severity classifier (T1-T4).** Assesses observable technical impact from a CSIRT perspective based on structured incident fields.

## Model Description

- **Architecture:** ModernBERT-base with 4-class classification head
- **Training:** 8,000 parametric incident scenarios (50 templates × field combinations)
- **Confidence:** Monte Carlo dropout (20 passes) maps variance to high/medium/low
- **Labels:** T1 (minor) → T4 (catastrophic)

## Intended Use

Classify the technical severity of cyber incidents based on service disruption, affected entities, cascading effects, and data compromise. Part of the CyberScale dual-scale incident classification system (T-level + O-level → Blueprint matrix).

**Input format:** `<description> [SEP] disruption: <level> entities: <N> sectors: <N> cascading: <level> data_compromise: <level>`

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Accuracy | {metrics.get('accuracy', 'N/A')} | > 75% |
| Macro F1 | {metrics.get('macro_f1', 'N/A')} | > 75% |

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


def generate_operational_model_card(metrics: dict) -> str:
    """Generate README.md for the operational severity model repo."""
    return f"""---
language: en
license: apache-2.0
library_name: transformers
tags:
  - cybersecurity
  - incident-classification
  - operational-severity
  - modernbert
  - nis2
  - cyber-blueprint
pipeline_tag: text-classification
model-index:
  - name: cyberscale-operational-v1
    results:
      - task:
          type: text-classification
          name: Operational Severity Classification (O1-O4)
        metrics:
          - name: Accuracy
            type: accuracy
            value: {metrics.get('accuracy', 'N/A')}
          - name: Macro F1
            type: f1
            value: {metrics.get('macro_f1', 'N/A')}
---

# CyberScale Operational Severity v1

**Incident operational severity classifier (O1-O4).** Assesses consequence and coordination needs from a crisis management perspective.

## Model Description

- **Architecture:** ModernBERT-base with 4-class classification head
- **Training:** 8,000 parametric incident scenarios (50 templates × field combinations)
- **Confidence:** Monte Carlo dropout (20 passes) maps variance to high/medium/low
- **Labels:** O1 (local) → O4 (EU-wide crisis)

## Intended Use

Classify the operational severity of cyber incidents based on entity relevance, cross-border impact, member states affected, and coordination needs. Part of the CyberScale dual-scale incident classification system (T-level + O-level → Blueprint matrix).

**Input format:** `<description> [SEP] sectors: <list> relevance: <level> ms_affected: <N> cross_border: <level> coordination: <level> capacity_exceeded: <bool>`

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Accuracy | {metrics.get('accuracy', 'N/A')} | > 75% |
| Macro F1 | {metrics.get('macro_f1', 'N/A')} | > 75% |

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


def publish_technical(api: HfApi, dry_run: bool = False) -> None:
    """Publish technical severity model."""
    if not TECHNICAL_DIR.exists():
        print(f"ERROR: Technical model not found at {TECHNICAL_DIR}")
        return

    metrics = {}
    metrics_path = TECHNICAL_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())

    card = generate_technical_model_card(metrics)
    card_path = TECHNICAL_DIR / "README.md"
    card_path.write_text(card)

    files = list(TECHNICAL_DIR.glob("*"))
    print(f"\n--- Technical Model: {TECHNICAL_REPO} ---")
    print(f"Files to upload ({len(files)}):")
    for f in sorted(files):
        size = f.stat().st_size
        print(f"  {f.name} ({size / 1024:.0f} KB)" if size < 1024 * 1024
              else f"  {f.name} ({size / 1024 / 1024:.0f} MB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(TECHNICAL_REPO, repo_type="model", exist_ok=True, token=api.token)
    api.upload_folder(
        folder_path=str(TECHNICAL_DIR),
        repo_id=TECHNICAL_REPO,
        repo_type="model",
        commit_message="Upload CyberScale technical severity v1 model",
        ignore_patterns=["training_state.pt"],
    )
    print(f"Published: https://huggingface.co/{TECHNICAL_REPO}")


def publish_operational(api: HfApi, dry_run: bool = False) -> None:
    """Publish operational severity model."""
    if not OPERATIONAL_DIR.exists():
        print(f"ERROR: Operational model not found at {OPERATIONAL_DIR}")
        return

    metrics = {}
    metrics_path = OPERATIONAL_DIR / "metrics.json"
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text())

    card = generate_operational_model_card(metrics)
    card_path = OPERATIONAL_DIR / "README.md"
    card_path.write_text(card)

    files = list(OPERATIONAL_DIR.glob("*"))
    print(f"\n--- Operational Model: {OPERATIONAL_REPO} ---")
    print(f"Files to upload ({len(files)}):")
    for f in sorted(files):
        size = f.stat().st_size
        print(f"  {f.name} ({size / 1024:.0f} KB)" if size < 1024 * 1024
              else f"  {f.name} ({size / 1024 / 1024:.0f} MB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(OPERATIONAL_REPO, repo_type="model", exist_ok=True, token=api.token)
    api.upload_folder(
        folder_path=str(OPERATIONAL_DIR),
        repo_id=OPERATIONAL_REPO,
        repo_type="model",
        commit_message="Upload CyberScale operational severity v1 model",
        ignore_patterns=["training_state.pt"],
    )
    print(f"Published: https://huggingface.co/{OPERATIONAL_REPO}")


def publish_dataset(api: HfApi, csv_path: Path, dry_run: bool = False) -> None:
    """Publish training CSV and pre-analysis report."""
    if not csv_path.exists():
        print(f"ERROR: Dataset not found at {csv_path}")
        return

    # Generate dataset card
    card = generate_dataset_card(csv_path)
    card_path = csv_path.parent / "dataset_README.md"
    card_path.write_text(card)

    print(f"\n--- Dataset: {DATASET_REPO} ---")
    print(f"CSV: {csv_path.name} ({csv_path.stat().st_size / 1024:.0f} KB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(DATASET_REPO, repo_type="dataset", exist_ok=True, token=api.token)

    # Upload CSV
    api.upload_file(
        path_or_fileobj=str(csv_path),
        path_in_repo="training_cves.csv",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload training CVEs",
    )

    # Upload README
    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload dataset card",
    )

    # Upload pre-analysis report if exists
    report_path = csv_path.parent / "pre_analysis_v2.md"
    if report_path.exists():
        api.upload_file(
            path_or_fileobj=str(report_path),
            path_in_repo="pre_analysis_report.md",
            repo_id=DATASET_REPO,
            repo_type="dataset",
            commit_message="Upload pre-analysis report",
        )

    print(f"Published: https://huggingface.co/datasets/{DATASET_REPO}")


def generate_contextual_dataset_card(csv_path: Path) -> str:
    """Generate README.md for the contextual training dataset."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    label_map = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
    dist = df["label"].value_counts().sort_index()

    return f"""---
language: en
license: apache-2.0
task_categories:
  - text-classification
tags:
  - cybersecurity
  - vulnerability
  - nis2
  - contextual-severity
size_categories:
  - 1K<n<10K
---

# CyberScale Contextual Severity Training Data

Training dataset for the CyberScale contextual severity classifier (Phase 2). Contains {len(df):,} scenarios combining CVE descriptions with NIS2 sector deployment contexts and cross-border exposure.

## Dataset Description

- **Source:** Parametrically generated from CVEs x 19 NIS2 sectors x cross-border conditions
- **Generation:** `training/scripts/generate_contextual.py` with `data/reference/sector_severity_rules.json`
- **Labels:** 4-class (Low=0, Medium=1, High=2, Critical=3)

## Schema

| Column | Type | Description |
|--------|------|-------------|
| `input_text` | string | Formatted input: `<description> [SEP] sector: <id> cross_border: <bool> score: <float>` |
| `label` | int | Severity class (0-3) |
| `sector` | string | NIS2 sector identifier |
| `cross_border` | bool | Cross-border exposure |
| `cvss_score` | float | CVSS v3.x base score |
| `base_severity` | string | CVSS-derived severity |
| `contextual_severity` | string | Context-adjusted severity |

## Class Distribution

| Label | Name | Count |
|-------|------|-------|
{chr(10).join(f"| {i} | {label_map[i]} | {dist.get(i, 0):,} |" for i in range(4))}

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


def generate_incident_dataset_card(csv_path: Path, model_type: str) -> str:
    """Generate README.md for incident training datasets (T or O)."""
    import pandas as pd
    df = pd.read_csv(csv_path)
    label_col = "label"
    dist = df[label_col].value_counts().sort_index()

    if model_type == "technical":
        title = "CyberScale Technical Severity Training Data"
        desc = "incident technical severity classifier (Phase 3 T-model)"
        labels = "T1-T4"
        fields = """| `text` | string | Formatted input: `<description> [SEP] disruption: <level> entities: <N> sectors: <N> cascading: <level> data_compromise: <level>` |
| `label` | string | Technical severity level (T1/T2/T3/T4) |"""
    else:
        title = "CyberScale Operational Severity Training Data"
        desc = "incident operational severity classifier (Phase 3 O-model)"
        labels = "O1-O4"
        fields = """| `text` | string | Formatted input: `<description> [SEP] sectors: <list> relevance: <level> ms_affected: <N> cross_border: <level> coordination: <level> capacity_exceeded: <bool>` |
| `label` | string | Operational severity level (O1/O2/O3/O4) |"""

    return f"""---
language: en
license: apache-2.0
task_categories:
  - text-classification
tags:
  - cybersecurity
  - incident-classification
  - {model_type}-severity
  - nis2
  - cyber-blueprint
size_categories:
  - 1K<n<10K
---

# {title}

Training dataset for the CyberScale {desc}. Contains {len(df):,} parametric incident scenarios with deterministic {labels} labels.

## Dataset Description

- **Source:** Parametrically generated from structured field combinations (50 templates x paraphrase variants)
- **Generation:** `training/scripts/generate_incidents.py`
- **Labels:** 4-class ({labels})
- **Balance:** {len(df) // 4:,} per class after balancing

## Schema

| Column | Type | Description |
|--------|------|-------------|
{fields}

## Class Distribution

| Label | Count |
|-------|-------|
{chr(10).join(f"| {label} | {count:,} |" for label, count in dist.items())}

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


def publish_contextual_dataset(api: HfApi, dry_run: bool = False) -> None:
    """Publish contextual severity training dataset."""
    csv_path = DATASET_DIR / "contextual_training.csv"
    # Try versioned names
    for name in ["contextual_training_v3.csv", "contextual_training_v2.csv", "contextual_training.csv"]:
        candidate = DATASET_DIR / name
        if candidate.exists():
            csv_path = candidate
            break

    if not csv_path.exists():
        print(f"ERROR: Contextual dataset not found in {DATASET_DIR}")
        return

    card = generate_contextual_dataset_card(csv_path)
    card_path = DATASET_DIR / "contextual_dataset_README.md"
    card_path.write_text(card)

    print(f"\n--- Contextual Dataset: {CONTEXTUAL_DATASET_REPO} ---")
    print(f"CSV: {csv_path.name} ({csv_path.stat().st_size / 1024:.0f} KB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(CONTEXTUAL_DATASET_REPO, repo_type="dataset", exist_ok=True, token=api.token)
    api.upload_file(
        path_or_fileobj=str(csv_path),
        path_in_repo="contextual_training.csv",
        repo_id=CONTEXTUAL_DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload contextual severity training data",
    )
    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=CONTEXTUAL_DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload dataset card",
    )
    print(f"Published: https://huggingface.co/datasets/{CONTEXTUAL_DATASET_REPO}")


def publish_incident_dataset(api: HfApi, model_type: str, dry_run: bool = False) -> None:
    """Publish incident training dataset (technical or operational)."""
    csv_path = DATASET_DIR / f"{model_type}_training.csv"
    repo = TECHNICAL_DATASET_REPO if model_type == "technical" else OPERATIONAL_DATASET_REPO

    if not csv_path.exists():
        print(f"ERROR: {model_type} dataset not found at {csv_path}")
        return

    card = generate_incident_dataset_card(csv_path, model_type)
    card_path = DATASET_DIR / f"{model_type}_dataset_README.md"
    card_path.write_text(card)

    print(f"\n--- {model_type.title()} Dataset: {repo} ---")
    print(f"CSV: {csv_path.name} ({csv_path.stat().st_size / 1024:.0f} KB)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(repo, repo_type="dataset", exist_ok=True, token=api.token)
    api.upload_file(
        path_or_fileobj=str(csv_path),
        path_in_repo=f"{model_type}_training.csv",
        repo_id=repo,
        repo_type="dataset",
        commit_message=f"Upload {model_type} severity training data",
    )
    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=repo,
        repo_type="dataset",
        commit_message="Upload dataset card",
    )
    print(f"Published: https://huggingface.co/datasets/{repo}")


# ---------------------------------------------------------------------------
# Curated incidents dataset
# ---------------------------------------------------------------------------

def generate_curated_dataset_card(source_path: Path) -> str:
    """Generate README.md for the curated incidents benchmark dataset."""
    data = json.loads(source_path.read_text())
    incidents = data.get("incidents", [])
    t_dist: dict = {}
    o_dist: dict = {}
    for inc in incidents:
        t = inc.get("expected_t", "?")
        o = inc.get("expected_o", "?")
        t_dist[t] = t_dist.get(t, 0) + 1
        o_dist[o] = o_dist.get(o, 0) + 1

    t_rows = "\n".join(
        f"| {k} | {v} |" for k, v in sorted(t_dist.items())
    )
    o_rows = "\n".join(
        f"| {k} | {v} |" for k, v in sorted(o_dist.items())
    )

    return f"""---
language: en
license: apache-2.0
task_categories:
  - text-classification
tags:
  - cybersecurity
  - incident-classification
  - technical-severity
  - operational-severity
  - nis2
  - cyber-blueprint
  - benchmark
size_categories:
  - n<1K
---

# CyberScale Curated Incidents Benchmark

Human-curated benchmark of **{len(incidents)} real-world cyber incidents** with Blueprint T/O ground-truth labels. Used to validate the Phase 3 T-model and O-model against documented, authoritative incident data.

## Dataset Description

- **Source:** Manually curated from ENISA, NCSC, CERT reports, and academic references
- **Coverage:** High-profile cyber incidents from 2007 to 2024
- **Labels:** Blueprint Technical (T1–T4) and Operational (O1–O4) severity levels with per-incident rationale
- **Version:** {data.get("version", "1.0")}

## Schema

Each entry in `curated_incidents.json` contains:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Incident identifier (e.g., INC-001) |
| `name` | string | Incident name and year |
| `date` | string | Incident date (ISO 8601) |
| `sources` | list[string] | Authoritative reference URLs |
| `description` | string | Narrative description of the incident |
| `t_fields` | object | Technical severity input fields (disruption, entities, sectors, cascading, data_compromise) |
| `o_fields` | object | Operational severity input fields (sectors, relevance, ms_affected, cross_border, coordination, capacity_exceeded) |
| `expected_t` | string | Ground-truth Technical severity (T1–T4) |
| `expected_o` | string | Ground-truth Operational severity (O1–O4) |
| `rationale` | object | Human-written justification for each label |

## Label Distribution

### Technical Severity

| Label | Count |
|-------|-------|
{t_rows}

### Operational Severity

| Label | Count |
|-------|-------|
{o_rows}

## Usage

```python
from datasets import load_dataset

ds = load_dataset("{CURATED_DATASET_REPO}")
```

Or load directly:

```python
import json, urllib.request

url = "https://huggingface.co/datasets/{CURATED_DATASET_REPO}/resolve/main/curated_incidents.json"
with urllib.request.urlopen(url) as r:
    data = json.load(r)
incidents = data["incidents"]
```

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
"""


def publish_curated_dataset(api: HfApi, dry_run: bool = False) -> None:
    """Publish the human-curated incidents benchmark dataset."""
    if not CURATED_SOURCE.exists():
        print(f"ERROR: Curated incidents not found at {CURATED_SOURCE}")
        return

    card = generate_curated_dataset_card(CURATED_SOURCE)
    card_path = CURATED_SOURCE.parent / "curated_incidents_README.md"
    card_path.write_text(card)

    data = json.loads(CURATED_SOURCE.read_text())
    n = len(data.get("incidents", []))
    print(f"\n--- Curated Dataset: {CURATED_DATASET_REPO} ---")
    print(f"Source: {CURATED_SOURCE.name} ({CURATED_SOURCE.stat().st_size / 1024:.0f} KB, {n} incidents)")

    if dry_run:
        print("DRY RUN — skipping upload")
        return

    create_repo(CURATED_DATASET_REPO, repo_type="dataset", exist_ok=True, token=api.token)
    api.upload_file(
        path_or_fileobj=str(CURATED_SOURCE),
        path_in_repo="curated_incidents.json",
        repo_id=CURATED_DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload curated incidents benchmark (40 real-world incidents)",
    )
    api.upload_file(
        path_or_fileobj=str(card_path),
        path_in_repo="README.md",
        repo_id=CURATED_DATASET_REPO,
        repo_type="dataset",
        commit_message="Upload dataset card",
    )
    print(f"Published: https://huggingface.co/datasets/{CURATED_DATASET_REPO}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Publish CyberScale to Hugging Face")
    parser.add_argument("--model-only", action="store_true", help="Publish scorer model only")
    parser.add_argument("--contextual-only", action="store_true", help="Publish contextual model only")
    parser.add_argument("--technical-only", action="store_true", help="Publish technical model only")
    parser.add_argument("--operational-only", action="store_true", help="Publish operational model only")
    parser.add_argument("--dataset-only", action="store_true", help="Publish Phase 1 dataset only")
    parser.add_argument("--contextual-dataset-only", action="store_true", help="Publish contextual dataset only")
    parser.add_argument("--technical-dataset-only", action="store_true", help="Publish technical dataset only")
    parser.add_argument("--operational-dataset-only", action="store_true", help="Publish operational dataset only")
    parser.add_argument("--curated-dataset-only", action="store_true", help="Publish curated incidents dataset only")
    parser.add_argument("--all-datasets", action="store_true", help="Publish all datasets")
    parser.add_argument("--dataset-csv", type=str,
                        default=str(DATASET_DIR / "training_cves_v2.csv"),
                        help="Path to training CSV (default: training_cves_v2.csv)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be published")
    args = parser.parse_args()

    token = os.environ.get("HF_TOKEN")
    if not token and not args.dry_run:
        print("ERROR: Set HF_TOKEN environment variable")
        print("  export HF_TOKEN=hf_xxxxx")
        sys.exit(1)

    api = HfApi(token=token)

    # Selective publish based on flags
    any_flag = (args.model_only or args.contextual_only or args.technical_only
                or args.operational_only or args.dataset_only
                or args.contextual_dataset_only or args.technical_dataset_only
                or args.operational_dataset_only or args.curated_dataset_only
                or args.all_datasets)
    publish_all = not any_flag

    if args.model_only or publish_all:
        publish_model(api, dry_run=args.dry_run)
    if args.contextual_only or publish_all:
        publish_contextual(api, dry_run=args.dry_run)
    if args.technical_only or publish_all:
        publish_technical(api, dry_run=args.dry_run)
    if args.operational_only or publish_all:
        publish_operational(api, dry_run=args.dry_run)
    if args.dataset_only or args.all_datasets or publish_all:
        publish_dataset(api, Path(args.dataset_csv), dry_run=args.dry_run)
    if args.contextual_dataset_only or args.all_datasets or publish_all:
        publish_contextual_dataset(api, dry_run=args.dry_run)
    if args.technical_dataset_only or args.all_datasets or publish_all:
        publish_incident_dataset(api, "technical", dry_run=args.dry_run)
    if args.operational_dataset_only or args.all_datasets or publish_all:
        publish_incident_dataset(api, "operational", dry_run=args.dry_run)
    if args.curated_dataset_only or args.all_datasets or publish_all:
        publish_curated_dataset(api, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
