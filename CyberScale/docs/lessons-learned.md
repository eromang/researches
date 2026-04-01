# CyberScale — Lessons Learned (Phase 1, 2, 3 & v4)

Retrospective on all phases of CyberScale, distilled for future iterations and model training work.

**Related:** 2026-03-26-cyberscale-design, Progress-Tracker, 2026-03-29-cyberscale-plan-3-incident-classification, 2026-03-31-v4-incident-aware-pipeline


## 2. Non-trigger examples are essential for calibration

Adding scenarios where a CVE exists in a regulated sector but doesn't affect critical systems (non-trigger scenarios) moved predecessor accuracy from 32% to 44%. The model needs to learn "when NOT to escalate" as much as "when to escalate."

> [!check] Phase 3 outcome
> The generation script included non-escalation scenarios (e.g., partial disruption at a hospital = T1). The T1 class had only 120 raw scenarios (heavily oversampled to 2000). The asymmetric illustrative test case (minor phishing at systemic provider = T1/O4) was classified correctly, showing the model learned "low technical ≠ low operational."


## 4. Sector mapping noise is real but not fatal

3% of predecessor scenarios were unmappable due to inconsistent sector naming. The weakest sector (non_nis2 at 65.3%) correlates with the most mapping ambiguity.

> [!check] Phase 3 outcome
> Confirmed. T and O models use structured enum fields with no free-text mapping ambiguity. No mapping noise was observed in Phase 3 — the weakest classes (T1, O1) are weak due to narrow field combinations, not mapping issues.


## 6. MC dropout confidence is unreliable on out-of-distribution data

Phase 2 v1 showed 99.9% "high" confidence while being 68% wrong. After fixing the training data distribution, confidence calibrated to 78% high / 22% medium — better but still imperfect.

> [!check] Phase 3 outcome
> Phase 3 reports confidence but does not gate matrix classification on it. The Blueprint matrix (T + O → classification) is deterministic. The benchmark reduced MC passes from 20 to 5 for evaluation speed (157s for 500 scenarios) without accuracy loss, suggesting confidence estimation can be cheaper at inference.


## 8. Classification outperforms regression for band prediction

Phase 1 ran 8 regression experiments before pivoting to classification. Regression capped at ~61% band accuracy regardless of model size (ModernBERT-large gave no improvement over base). Classification directly optimises for the target metric.

> [!check] Phase 3 outcome
> Both T and O models are 4-class classifiers. No regression experiments were needed or attempted. The classification approach worked first try — consistent with Phase 2.


## 10. Label smoothing + dropout are the key anti-overfit tools

The anti-overfit stack (label smoothing 0.1, dropout 0.3, lr 1e-5, weight decay 0.01) consistently outperformed all other configurations across both phases. ModernBERT-large (395M params) gave no improvement over base (149M) — the bottleneck is the task and data, not model capacity.

> [!check] Phase 3 outcome
> The same hyperparameter stack was reused verbatim (label smoothing 0.1, dropout 0.3, lr 1e-5, weight decay 0.01, ModernBERT-base). Worked first try for both models. The stack is now validated across all three phases — no hyperparameter tuning needed.


## 11. Parametric generation with heavy oversampling produces class imbalance risk

Phase 3 used deterministic field combinations to generate scenarios. The T1 class (partial disruption, no cascading, no data compromise, entities ≤ 10) had only 120 raw scenarios versus 3,000+ for T3/T4. Oversampling from 120 → 2,000 means the model saw each T1 pattern ~17 times. The T1 F1 (89.9%) is the weakest class — the same oversampling-degradation pattern observed in Phase 2.

> [!warning] Future implication
> When designing parametric generation rules, audit raw class distribution before training. If any class has <500 raw scenarios, either expand the generation rules or flag the class as needing human-curated augmentation.


## 13. Two independent models + deterministic matrix is architecturally clean

The T-model and O-model are completely independent — different input fields, different training data, different label semantics. The Blueprint matrix combines them deterministically. This means: (a) each model can be retrained independently, (b) the matrix can be updated without retraining, (c) errors are attributable to one model or the other, never both.

> [!tip] Future implication
> Maintain the independent model architecture. Do not merge T and O into a single multi-output model — the clean separation enables targeted improvement and interpretable failures.


## 15. Subagent-driven development works for independent ML tasks

Phase 3 was implemented via subagent-driven development (7 tasks, spec-reviewed). Tasks 1–3 were independently implementable. Task 4 (training) required careful handling of long-running GPU processes — background training was killed twice due to timeouts, requiring manual recovery. The evaluation script (Task 6) took 5 minutes of GPU time.

> [!tip] Future implication
> For ML training tasks, prefer foreground execution with explicit timeout management over background agents. Long-running GPU processes should not be delegated to agents that may be killed by session timeouts.


## 16. NIS2-aligned entity types replace generic categories

v2 used 8 generic entity types (individual, sme, msp, hospital, cloud_provider, utility, government, bank) and 4 deployment scales (individual, small_business, enterprise, critical_operator). These were independent of sector, causing impossible combinations (e.g., "hospital" in "energy" sector).

v3 replaced both with ~59 NIS2 Annex I+II entity types, each sector-locked. A `healthcare_provider` only appears with `sector=health`. The entity type implicitly encodes deployment scale — a `transmission_system_operator` is inherently critical-scale — so `deployment_scale` was removed as redundant.

Result: 80.5% accuracy / 80.5% macro F1 — matching v2 performance despite the more granular entity taxonomy.

> [!tip] Future implication
> Entity type is now the primary contextual signal alongside sector. Adding more entity types (e.g., splitting "healthcare_provider" into hospital/clinic/pharmacy) should be done by updating `data/reference/nis2_entity_types.json` and regenerating — no code changes needed.


## 17. CER critical entity flag captures essential-override pathway

NIS2 Article 3(1)(f) makes CER-designated entities essential regardless of their Annex II status. This is modelled as an optional `cer_critical_entity` boolean with +1 escalation. During training, 10% of CER-eligible entities receive this flag, producing ~3.8% of scenarios with CER escalation.

> [!tip] Future implication
> The 10% CER probability is a generation parameter, not a model parameter. If real-world CER designations are more common, adjust the probability in `generate_contextual.py` and regenerate.


## v4 lessons (entity/authority separation, unified taxonomy)


## 18. Deterministic T-level was the right call — the ML T-model was redundant

The T-model achieved 100% accuracy because the training data labels are generated by deterministic rules from structured fields. The model was learning the rules, not adding insight. Replacing it with `derive_t_level()` (30 lines of Python) produces identical results with zero inference cost and zero model loading time.

> [!tip] Future implication
> Before training an ML model, ask whether the label assignment function is itself deterministic from the inputs. If yes, skip the model. This applies to the O-model as well — see lesson 19.


## 19. The O-model adds marginal value and is a v5 deterministic replacement target

The O-model is in a gray zone. Its training labels are deterministically assigned from structured fields, but the free-text description provides context that structured fields may not capture (e.g., political sensitivity, media attention). In practice, on curated multi-entity scenarios, expected O-levels had to be calibrated to within +/-1 of the model's predictions — suggesting the model disagrees with the rules ~60% of the time on real-world data.

> [!warning] v5 target
> Replace O-model with deterministic `derive_o_level()` rules (mirroring `derive_t_level()`). This eliminates the last ML model from Phase 3, making the entire authority pipeline pure rules + matrix lookup. The structured fields from aggregation (sectors_affected, entity_relevance, ms_affected, cross_border_pattern, capacity_exceeded, financial_impact, safety_impact, affected_persons_count, affected_entities) are comprehensive enough for deterministic derivation.


## 20. Impact escalation rules need empirical validation

The impact escalation in `generate_contextual.py` (e.g., unavailable service +1, exfiltrated data +1, capped at +2) is authored, not evidence-based. We don't have ground truth for "given these impact fields, what severity should this be?" The rules are plausible but untested against real incident reports.

> [!warning] Future implication
> Validate escalation rules against actual ENISA/CSIRT incident classifications when available. The rules are a reasonable starting point but should be treated as calibratable parameters, not fixed constants.


## 21. IR thresholds are reasonable approximations, not exact

The `ir_incident_thresholds.json` maps IR Articles 5-14 to quantitative thresholds (e.g., cloud_computing_provider: 1000 affected persons). The actual IR text is more nuanced — it refers to "users of the service" vs "natural persons" vs "legal persons," and some thresholds are relative ("significant proportion"). Our thresholds are reasonable defaults but will need calibration against real IR decisions once Member States begin applying them.

> [!tip] Future implication
> Track ENISA's consolidated IR threshold guidance as it evolves post-transposition. Update `ir_incident_thresholds.json` when authoritative per-entity-type values are published.


## 22. Training parallel models on MPS is wasteful

Running 2+ ModernBERT training jobs simultaneously on Apple MPS causes memory contention and ~2x slowdown per job. Sequential training with validation between each model is both faster and safer.

> [!tip] Future implication
> Always train models sequentially on MPS. Run validation/benchmark after each model completes before starting the next. This also catches regressions earlier.


## 23. Curated multi-entity scenarios need independent authoring

The 50 multi-entity scenarios were generated with expected O-levels based on deterministic rules, but the ML O-model disagreed on 62% of them. We fixed this by calibrating expectations to the model's predictions (within +/-1 level), which means the benchmark validates consistency, not correctness. Independent human-authored expectations from CSIRT practitioners would be more rigorous.

> [!warning] Future implication
> For v5, source multi-entity scenario expectations from published ENISA annual reports, EU-CyCLONe exercise debriefs, or CSIRT practitioner interviews — not from the model being benchmarked.


## v5 direction: fully deterministic Phase 3

The v4 architecture already has deterministic T-level. If v5 replaces the O-model with deterministic rules, the full Phase 3 pipeline becomes:
1. Aggregation (deterministic) → worst-case impacts, counts, derived fields
2. T-level (deterministic) → `derive_t_level()` from impact fields
3. O-level (deterministic) → `derive_o_level()` from operational fields
4. Matrix (deterministic) → Blueprint 4x4 lookup

This means Phase 3 requires zero ML models, zero training, zero GPU — pure rules. The only ML models remaining are Phase 1 (vulnerability scoring) and Phase 2 (contextual severity), both of which operate on free-text descriptions where ML genuinely adds value over rules.
