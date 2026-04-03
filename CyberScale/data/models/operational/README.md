---
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
            value: 1.0
          - name: Macro F1
            type: f1
            value: 1.0
---

> **DEPRECATED in v5** — This model is superseded by deterministic `derive_o_level()` rules in Phase 3. O-level inference uses no ML models. Retained for reference only.

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
| Accuracy | 1.0 | > 75% |
| Macro F1 | 1.0 | > 75% |

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
