---
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
            value: 1.0
          - name: Macro F1
            type: f1
            value: 1.0
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
| Accuracy | 1.0 | > 75% |
| Macro F1 | 1.0 | > 75% |

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
