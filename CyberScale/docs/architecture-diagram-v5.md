# CyberScale v5 Architecture Diagram — Text Specification

Use this to recreate the Excalidraw and Pipeline Reference.

---

## Top-level layout (left to right)

```
[Entity Layer]  →  [National Layer]  →  [EU Layer]
  Phase 1+2          Phase 3a             Phase 3b
```

---

## Entity Layer (left column)

### Box: Phase 1 — Vulnerability Scoring
- Label: "Phase 1: Vulnerability Scoring"
- Subtitle: "ModernBERT-base (ML)"
- Inputs: CVE description, CWE (optional)
- Output arrow: "score (0-10), band, confidence"
- Color: Blue (ML model)

### Box: Phase 2 — Contextual Severity
- Label: "Phase 2: Contextual Severity"
- Subtitle: "ModernBERT-base (ML)"
- Inputs: Description, sector, ms_established, ms_affected, entity_type, score (from P1)
- Output arrow: "severity (C/H/M/L), confidence, key_factors"
- Color: Blue (ML model)
- Note: "Phase 1 score feeds in automatically"

### Box: Phase 2 — Entity Incident Mode
- Label: "Phase 2: Entity Incident"
- Subtitle: "assess_entity_incident"
- Inputs: All Phase 2 inputs + impact fields (service_impact, data_impact, financial_impact, safety_impact, affected_persons_count, suspected_malicious, impact_duration_hours)
- Inside: Decision diamond "IR entity?" → Yes: "IR Thresholds (Arts. 5-14)" / No: "NIS2 ML Model"
- Output arrow: "severity + significance + early_warning"
- Color: Blue (ML) + Green (deterministic IR)

### Box: Early Warning
- Label: "Early Warning Recommendation"
- Subtitle: "Art. 23(4)(a)"
- Content: "recommended, deadline: 24h, required_content, next_step"
- Color: Orange (recommendation output)

### Arrow: Entity notification
- From: Entity Incident Mode output
- To: National Layer input
- Label: "entity notification dict"
- Style: Thick, dashed (crosses layer boundary)

---

## National Layer (center column)

### Box: Phase 3a — National CSIRT
- Label: "Phase 3a: National Classification"
- Subtitle: "assess_national_incident — DETERMINISTIC"
- Inside (stacked):
  1. "MS Scoping: validate single ms_established"
  2. "Aggregation: worst-case impacts, sum persons, count sectors/MS"
  3. "Sector Dependencies: propagate cascading via dependency graph"
  4. "derive_t_level() → T1-T4"
  5. "derive_o_level() → O1-O4"
  6. "Blueprint Matrix 4x4 → classification"
- Output arrow (right): "national T/O/classification"
- Output arrow (right, conditional): "cross_border=true → CSIRT Network sharing (Art. 15)"
- Color: Green (fully deterministic)

### Reference data boxes (attached to Phase 3a):
- Small box: "sector_dependencies.json" (directed graph)
- Small box: "impact_taxonomy.json" (field values)
- Small box: "blueprint_matrix.json" (4x4 lookup)
- Color: Gray (reference data)

### Arrow: To EU Layer
- From: Phase 3a output
- To: Phase 3b input
- Label: "national classification dict"
- Condition: "only if cross_border=true"
- Style: Thick, dashed

---

## EU Layer (right column)

### Box: Phase 3b — EU-CyCLONe
- Label: "Phase 3b: EU Classification"
- Subtitle: "assess_eu_incident — DETERMINISTIC + HUMAN"
- Inside (stacked):
  1. "National Aggregation: worst-case T/O across MS"
  2. "EU Escalation: significant in 3+ MS → O3 minimum"
  3. "CyCLONe Officer Inputs (per MS):"
  4. "  - political_sensitivity"
  5. "  - national_capacity_status"
  6. "  - coordination_needs"
  7. "  - intelligence_context"
  8. "  - escalation_recommendation"
  9. "Officer Escalation: +1/+2 O-level (escalate only, never de-escalate)"
  10. "Blueprint Matrix → EU classification"
- Output: "EU classification + coordination level"
- Color: Green (deterministic) + Yellow border (human input)

### Box: Coordination Level
- Label: "Coordination Output"
- Content:
  - "O1 → national"
  - "O2 → eu_info"
  - "O3 → eu_active"
  - "O4 → full_ipcr"
- Color: Red (crisis coordination)

---

## Feedback Loop (bottom, spans full width)

### Arrow: Authority Feedback
- From: Phase 3a/3b output
- Through: "Authority Decision" box (authority overrides suggested classification)
- To: "Feedback Store" box (data/feedback/authority_decisions.json)
- To: "Regression Benchmark" box (benchmark_authority_feedback.py)
- Back to: "Rule Calibration" arrow pointing at derive_t_level / derive_o_level
- Label: "suggested vs actual → override patterns → rule adjustment"
- Style: Dotted (not automated, periodic manual process)
- Color: Gray

---

## Legend (bottom-right corner)

| Color | Meaning |
|-------|---------|
| Blue | ML model (ModernBERT) — Phase 1+2 only |
| Green | Fully deterministic (rules + matrix) |
| Yellow border | Human input (CyCLONe Officers) |
| Orange | Recommendation output |
| Red | Crisis coordination |
| Gray | Reference data / feedback loop |

---

## Blueprint Matrix (inset, attached to Phase 3a/3b)

```
        O1              O2              O3              O4
T4  large_scale     large_scale     cyber_crisis    cyber_crisis
T3  significant     large_scale     large_scale     cyber_crisis
T2  significant     significant     large_scale     large_scale
T1  below_threshold significant     significant     large_scale
```

Map: below_threshold→7(a), significant→7(b), large_scale→7(c), cyber_crisis→7(d)

---

## Key annotations

- "ML only where free text needs interpretation (Phase 1+2)"
- "Phase 3 = zero ML, zero GPU, zero training"
- "Entity reports → National classifies → EU coordinates"
- "279 tests, all deterministic logic at 100%"
