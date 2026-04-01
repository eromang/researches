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
  - name: cyberscale-operational-v4
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

# CyberScale Operational Severity v4

**Incident operational severity classifier (O1-O4).** Assesses consequence and coordination needs from a crisis management perspective.

## v4 changes

- **Added:** financial_impact, safety_impact, affected_persons_count, affected_entities as input fields
- **Removed:** coordination_needs (was an output, not an observable input)
- **Changed:** sectors_affected is now int (count), not comma-separated string

## Model Description

- **Architecture:** ModernBERT-base with 4-class classification head
- **Training:** 8,000 parametric incident scenarios with consequence dimensions
- **Confidence:** Monte Carlo dropout (5 passes) maps variance to high/medium/low
- **Labels:** O1 (local) → O4 (EU-wide crisis)

## Intended Use

Classify the operational severity of cyber incidents based on entity relevance, cross-border impact, member states affected, capacity exceeded, plus consequence dimensions (financial impact, safety impact, persons affected, entities affected).

Used in the authority-facing `assess_incident` pipeline: aggregation → deterministic T-level → **O-model** → Blueprint matrix.

**v4 input format:** `<description> [SEP] sectors: <N> relevance: <level> ms_affected: <N> cross_border: <level> capacity_exceeded: <bool> [financial: <level>] [safety: <level>] [persons: <N>] [entities: <N>]`

## Metrics

| Metric | Value | Target |
|--------|-------|--------|
| Accuracy (synthetic test) | 1.00 | > 75% |
| Macro F1 (synthetic test) | 1.00 | > 75% |
| Multi-entity benchmark | 100% | > 70% |

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
