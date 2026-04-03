---
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

Human-curated benchmark of **40 real-world cyber incidents** with Blueprint T/O ground-truth labels. Used to validate the Phase 3 T-model and O-model against documented, authoritative incident data.

## Dataset Description

- **Source:** Manually curated from ENISA, NCSC, CERT reports, and academic references
- **Coverage:** High-profile cyber incidents from 2007 to 2024
- **Labels:** Blueprint Technical (T1–T4) and Operational (O1–O4) severity levels with per-incident rationale
- **Version:** 1.0

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
| T1 | 4 |
| T2 | 12 |
| T3 | 18 |
| T4 | 6 |

### Operational Severity

| Label | Count |
|-------|-------|
| O1 | 20 |
| O2 | 11 |
| O3 | 7 |
| O4 | 2 |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("eromang/cyberscale-curated-incidents")
```

Or load directly:

```python
import json, urllib.request

url = "https://huggingface.co/datasets/eromang/cyberscale-curated-incidents/resolve/main/curated_incidents.json"
with urllib.request.urlopen(url) as r:
    data = json.load(r)
incidents = data["incidents"]
```

## Citation

Part of the CyberScale project — multi-phase cyber severity assessment MCP server.
