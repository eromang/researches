# CyberScale — Enhancement Roadmap (v2)

Concrete enhancement paths for a second iteration of the project, prioritised by expected impact. Based on failure mode analysis from Phase 1 (60.5% accuracy), Phase 2 (88% predecessor / 80% test), and Phase 3 (T: 95.4% F1, O: 96.4% F1, matrix: 96.2% — synthetic only).

**Related:** CyberScale - Lessons Learned (Phase 1, 2 & 3), 2026-03-26-cyberscale-design, Progress-Tracker


## Phase 2 — Contextual Severity

**Current:** 88% on predecessor benchmark (+7.3pp vs Variant F), 80% on mixed test set. All NIS2 sectors >94%.

**Remaining gap:** `non_nis2` (65.3%) and `small-deployment` (51%). The model cannot distinguish deployment contexts within a sector.

### High-impact enhancements

#### 1. Deployment scale as input feature

Add a `deployment_scale` parameter: `individual` / `small_business` / `enterprise` / `critical_operator`. This directly addresses the small-deployment weakness without requiring a full retrain — add the field to the input format and fine-tune.

**Effort:** Low — input format change + fine-tuning.

#### 2. Entity type feature

The predecessor dataset has `entity_type` (MSP, Hospital, Cloud provider, Individual). Encoding this as an input feature would capture much of the deployment context the model currently misses.

**Effort:** Low — input format change + fine-tuning.

#### 3. Phase 1 → Phase 2 composable pipeline

Currently `score: <float>` is in the input format but comes from CVSS, not the Phase 1 model. Wiring Phase 1's predicted score (with confidence) as input to Phase 2 creates the composable pipeline the design envisioned. This enables scoring vulnerabilities that have no CVSS score yet.

**Effort:** Low — inference pipeline wiring, no model change.

#### 4. Generate more small-deployment/non\_nis2 scenarios

The 1,850 predecessor scenarios are dominated by regulated sectors. Use the `/cve-severity-batch-generate` skill to create 500+ additional small-deployment/enterprise scenarios with human-quality labels.

**Effort:** Medium — requires scenario generation sessions, but tooling exists.

#### 5. Calibrated escalation rules

Replace the binary trigger match (escalate/don't) with probability-weighted escalation per trigger type. "availability" in health should escalate more often than "integrity" in health. Mine the predecessor data for empirical escalation rates per trigger × sector combination.

**Effort:** Medium — requires statistical analysis of predecessor data, then regeneration.

### Lower-effort wins

#### 6. Richer cross-border encoding

Currently binary true/false. Replace with the predecessor's richer geography: `single_site` / `national` / `2_ms` / `3plus_ms`. More granular cross-border representation captures the difference between a company operating in 2 EU states vs 15.

**Effort:** Low — input format change + retrain.

#### 7. Confidence-weighted training loss

Weight training examples by provenance: predecessor data gets weight 1.0, synthetic trigger-matched gets 0.8, synthetic non-trigger gets 0.6. Teaches the model to trust human-curated labels more.

**Effort:** Low — modify training loop.


## Cross-phase infrastructure

| Enhancement | Impact | Effort |
|-------------|--------|--------|
| **Active learning loop** — deploy model, collect analyst corrections, retrain monthly | High — models improve with use | Medium |
| **EUVD enrichment** — cross-reference EU-specific severity assessments not in NVD | Medium — additional training signal | Low |
| **Explanation quality** — train auxiliary model or use attention weights for input-level explanations instead of rule-based `key_factors` | Medium — analyst trust | High |
| **Batch inference API** — add batch endpoint for analysts processing incident queues | Low — operational convenience | Low |

---

## Suggested v2 iteration priority

Based on impact/effort ratio:

| Priority | Enhancement | Phase | Expected gain |
|----------|-------------|-------|---------------|
| 1 | Human-curated incident benchmark | 3 | Validates real-world performance |
| 2 | Deployment scale + entity type features | 2 | +10–15pp on non_nis2 |
| 3 | Mix curated incidents into training | 3 | Expected +10–30pp on real data |
| 4 | CWE as first-class feature | 1 | +5–10pp overall |
| 5 | Phase 1 → Phase 2 → Phase 3 pipeline wiring | 1+2+3 | End-to-end composable assessment |
| 6 | Product/vendor signal | 1 | +3–5pp overall |
| 7 | Expand T1/O1 generation rules | 3 | Reduces oversampling dependence |
| 8 | Generate more small-deployment scenarios | 2 | +5–10pp on small-deployment |
| 9 | Active learning loop | All | Continuous improvement |
| 10 | CVSS vector multi-task | 1 | +5–10pp, new capability |
