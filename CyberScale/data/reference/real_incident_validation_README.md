# CyberScale Real Incident Validation Dataset

Validation dataset of **real cyber incidents** extracted from RETEX (Retour d'Experience) analyses. Each incident has documented actual outcomes (crisis activation, notification status) that serve as ground truth for validating the CyberScale pipeline.

## Purpose

CyberScale's curated scenarios (benchmark datasets) are synthetic. This dataset provides **real-world validation** — did the pipeline reach the same conclusion as the actual crisis management response?

The dataset currently covers the HCPN national crisis qualification layer (v8). Future extensions may cover entity significance (v7) and Phase 3 authority classification.

## Dataset

**File:** `data/reference/real_incident_validation.json`

### Schema

Each incident contains:

| Section | Fields | Description |
|---------|--------|-------------|
| Identity | `id`, `name`, `date`, `country`, `source` | Incident metadata and vault RETEX path |
| `incident_data` | CyberScale input fields | Parameters extracted from RETEX: sectors, impacts, duration, etc. |
| `actual_outcomes` | `crisis_activated`, `pggccn_mode`, `significant_nis2`, etc. | What actually happened — ground truth |
| `expected_cyberscale` | Expected outputs per pipeline layer | What CyberScale should produce |
| `notes` | Free text | Analyst notes on mapping decisions or ambiguities |

### HCPN expected values

For Luxembourg-scoped incidents, `expected_cyberscale.hcpn_crisis` contains:

| Field | Description |
|-------|-------------|
| `sectors_affected`, `service_impact`, etc. | Inputs to `qualify_hcpn_incident()` |
| `coordination_required`, `urgent_decisions_required` | Authority judgment inputs (bool or null for uncertain) |
| `prejudice_actual` | Whether prejudice has occurred (Crise) or is potential (Alerte/CERC) |
| `expected_qualifies` | Should the pipeline say this qualifies? |
| `expected_level` | `national_major_incident`, `large_scale_cybersecurity_incident`, or `none` |
| `expected_mode` | `crise`, `alerte_cerc`, or `permanent` |
| `expected_recommend_consultation` | Optional — should the pipeline recommend consultation? |

For non-Luxembourg incidents, `hcpn_crisis.not_applicable = true` (skipped during validation).

### Current incidents

| ID | Date | Country | Sector | Significant | Crisis | Concordance |
|----|------|---------|--------|-------------|--------|-------------|
| RETEX-LU-2025-POST | 2025-07-23 | LU | Digital Infra | Yes | Yes (Crise) | Match |
| RETEX-LU-2025-LUXTRUST | 2025-12-16 | LU | Digital Infra | Yes | No | Match |
| RETEX-LU-2025-TANGO | 2025-08-05 | LU | Digital Infra | No | No | Match |
| RETEX-LU-2026-CTIE-DDOS | 2026-01-20 | LU | Public Admin | No | No | Match |
| RETEX-LU-2026-CTIE-MALWARE | 2026-02-26 | LU | Public Admin | Likely | No | Match |
| RETEX-NL-2026-IVANTI | 2026-02-05 | NL | Public Admin | Yes | No | Skip (non-LU) |
| RETEX-PL-2025-ENERGY | 2025-12-29 | PL | Energy | Yes | Yes | Skip (non-LU) |
| RETEX-EU-2026-EC-AWS | 2026-03-19 | EU | Public Admin | Yes | No | Skip (non-LU) |

---

## Scripts

### 1. Validate: `evaluation/validate_real_incidents.py`

Runs all incidents through the CyberScale HCPN qualifier and compares against expected values and actual outcomes.

**Run all incidents:**

```bash
poetry run python evaluation/validate_real_incidents.py
```

**Verbose output** (shows criteria details, concordance analysis, consultation reasons):

```bash
poetry run python evaluation/validate_real_incidents.py --verbose
```

**Validate a single incident:**

```bash
poetry run python evaluation/validate_real_incidents.py --incident RETEX-LU-2025-POST -v
```

**Output explained:**

- **PASS** — CyberScale output matches expected values
- **FAIL** — CyberScale output differs from expected (bug or incorrect expectation)
- **SKIP** — Non-LU incident, HCPN not applicable
- **CONCORDANCE** — CyberScale agrees with what actually happened in reality
- **DIVERGENCE** — CyberScale disagrees with actual outcome (expected when authority judgment inputs are approximations)
- **RECOMMEND CONSULTATION** — CyberScale cannot evaluate some criteria deterministically (delegated thresholds)

**Exit codes:** 0 if all pass, 1 if any fail.

### 2. Add incident: `evaluation/add_real_incident.py`

Interactive script to add a new incident to the validation dataset.

**Add a new incident:**

```bash
poetry run python evaluation/add_real_incident.py
```

**Preview without saving:**

```bash
poetry run python evaluation/add_real_incident.py --dry-run
```

**Workflow:**

1. Enter incident identity (ID, name, date, country, vault source path)
2. Enter CyberScale input parameters:
   - Sectors affected (from CyberScale taxonomy)
   - Entity types (from `nis2_entity_types.json`)
   - Impact fields: service, data, safety, financial
   - Affected persons, duration, cross-border, capacity exceeded
   - Malicious intent, threat actor type, sensitive data type
3. Enter actual outcomes (crisis activated, PGGCCN mode, notification frameworks)
4. For Luxembourg-scoped incidents:
   - Enter authority judgment inputs (coordination required, urgency, prejudice actual/potential)
   - The script **runs the HCPN qualifier live** and shows the result
   - Accept the CyberScale output as expected, or override manually
5. Review the full JSON preview
6. Confirm to save

**After adding, validate:**

```bash
poetry run python evaluation/validate_real_incidents.py --incident RETEX-LU-2026-NEW -v
```

**ID convention:** `RETEX-{country}-{year}-{short_name}` (e.g., `RETEX-LU-2026-CTIE-DDOS`)

---

## Adding incidents from RETEX files

When a new RETEX analysis is added to the Obsidian vault:

1. Read the RETEX file and extract the incident parameters
2. Run `poetry run python evaluation/add_real_incident.py`
3. Map RETEX fields to CyberScale taxonomy:
   - Sector names must match `data/reference/nis2_sectors.json`
   - Entity types must match `data/reference/nis2_entity_types.json`
   - Impact values must be from the unified taxonomy: `none/partial/degraded/unavailable/sustained` (service), `none/accessed/exfiltrated/compromised/systemic` (data), etc.
4. For authority judgment inputs (`coordination_required`, `urgent_decisions_required`):
   - Use the actual crisis response as a guide
   - If a crisis cell was convened → `coordination_required=yes`, `urgent_decisions_required=yes`
   - If unclear → use `unknown` (maps to `null`, triggers `undetermined`)
5. Validate and check concordance with actual outcome
6. Commit the updated JSON

## Design notes

- **Authority judgment inputs are approximations.** The HCPN framework requires human judgment for coordination/urgency assessment. When mapping from RETEX data, we infer these from the actual response. This means the validation tests whether CyberScale *would have reached the same conclusion given the same judgment calls*, not whether CyberScale can replace the judgment.

- **Undetermined is correct behavior.** Several Criterion 2 sub-criteria have thresholds delegated to sectoral authorities. When the module returns `undetermined` and recommends consultation, that IS the correct output — it means the framework cannot be applied mechanically for those criteria.

- **Non-LU incidents are included for context.** The NL, PL, and EU incidents provide cross-reference data (same CVEs, same attack patterns) and can be used for entity significance validation when that layer is added.
