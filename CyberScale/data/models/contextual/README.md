---
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
            value: 0.8049
          - name: Macro F1
            type: f1
            value: 0.8054
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
| Accuracy | 0.8049 |
| Macro F1 | 0.8054 |
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

model = AutoModelForSequenceClassification.from_pretrained("eromang/cyberscale-contextual-v1", num_labels=4)
tokenizer = AutoTokenizer.from_pretrained("eromang/cyberscale-contextual-v1")

text = "SQL injection in login form [SEP] sector: health cross_border: true score: 7.5"
inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=192)

with torch.no_grad():
    logits = model(**inputs).logits
    probs = torch.softmax(logits, dim=-1)
    label = ["Low", "Medium", "High", "Critical"][probs.argmax().item()]
    print(f"Contextual severity: {label}")
```

## Limitations

- Small-deployment / non-NIS2 scenarios are the weakest (51% accuracy)
- Trained on English descriptions only
- Does not capture sub-sector deployment context (e.g., clinical vs billing system in healthcare)

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
