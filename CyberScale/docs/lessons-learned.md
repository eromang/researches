# CyberScale — Lessons Learned (Phase 1, 2, 3, v4 & v6)

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


## 24. Phase 3 conflates national and EU authority levels

v4's `assess_incident` takes any list of entity notifications regardless of member state origin. In reality, NIS2 defines a multi-tier governance structure: entities report to their national CSIRT (Art. 23), national CSIRTs share cross-border information via the CSIRT Network (Art. 15), and EU-CyCLONe coordinates large-scale/crisis incidents (Art. 16). A national CSIRT in Luxembourg only receives notifications from entities established in Luxembourg — they don't aggregate German hospital data.

> [!warning] v5 target
> Split Phase 3 into Phase 3a (national: single-MS aggregation, deterministic) and Phase 3b (EU: aggregation across national assessments + CyCLONe Officer situational inputs). Phase 3b is not purely mechanical — each MS's CyCLONe Officer provides political sensitivity, capacity status, and coordination needs that can escalate the classification beyond what the structured data alone would produce.


## 25. Sector dependency graph captures systemic risk that sector counting misses

v4 derived cascading from sector count alone. v5 adds a directed dependency graph where energy/digital_infrastructure outages propagate to downstream sectors. Energy unavailable now correctly produces "uncontrolled" cascading even with just 2 reported sectors (because energy's 8 direct dependents are affected). This changed T-levels in 8/50 curated scenarios — showing the old sector-count approach systematically under-escalated energy and digital_infrastructure incidents.

> [!tip] Future implication
> The dependency graph needs periodic review as sector interdependencies evolve. ENISA's annual NIS Investments reports are the best calibration source.


## 26. CyCLONe Officer inputs are the correct abstraction for human judgment in Phase 3b

Phase 3b could have been pure worst-case aggregation of national classifications. Adding structured officer inputs (political_sensitivity, capacity_status, escalation_recommendation) provides a clean interface for human judgment that integrates with the deterministic pipeline. The key design decision was "escalate only, never de-escalate" — officers can raise the mechanical result but not lower it.

> [!tip] Future implication
> The officer input schema should be validated against actual EU-CyCLONe exercise procedures when available. The current fields are based on the Blueprint and Art. 16 but may need refinement.


## v5 outcome: fully deterministic Phase 3

v5 achieved fully deterministic Phase 3:
1. Aggregation (deterministic) → worst-case impacts, sector dependency propagation
2. T-level (deterministic) → `derive_t_level()` from impact fields
3. O-level (deterministic) → `derive_o_level()` from operational fields + consequences
4. Matrix (deterministic) → Blueprint 4x4 lookup
5. Multi-tier: Phase 3a (national, single MS) + Phase 3b (EU, CyCLONe Officers)

Phase 3 requires zero ML models, zero training, zero GPU — pure rules. The only ML models remaining are Phase 1 (vulnerability scoring) and Phase 2 (contextual severity), both operating on free-text descriptions where ML genuinely adds value over rules.

Authority feedback store provides the calibration mechanism: authority overrides accumulate, periodic regression benchmarks identify systematic rule gaps, rules are manually adjusted. No ML in the loop.


## v6 lessons (Phase 1 multi-task learning + CPE)


## 27. Multi-task CVSS vector decomposition provides modest gains, not breakthroughs

v6 decomposed the single band prediction into 9 heads (1 band + 8 CVSS vector components). This improved band accuracy from 60.5% (v1 baseline) to 62.3% (+1.8pp) and macro F1 from 56.4% to 58.4% (+2.0pp). The auxiliary component heads learned well (avg ~77% accuracy), confirming that CVE descriptions contain more signal for individual components than for the composite band. However, the improvement is incremental — the 70% target was not met.

> [!warning] Future implication
> Multi-task learning helps the encoder learn better representations, but the improvement ceiling is set by the input data quality. CVE descriptions are formulaic regardless of severity — the same phrasing patterns appear across all CVSS bands. Architecture changes alone cannot overcome this fundamental data limitation.


## 28. CPE vendor/product signal adds no value to vulnerability scoring

v6 Task 5 tested whether CPE vendor/product (e.g., "openssl", "linux kernel") improves band accuracy. Training data had 85% vendor coverage and 90% product coverage. The retrained model with CPE signal reached 62.7% val_band accuracy — statistically indistinguishable from the 62.3% baseline without CPE. The CPE signal is noise for severity prediction.

This disproves the hypothesis that "OpenSSL vulnerabilities are systematically higher severity than WordPress plugin vulnerabilities." While intuitively plausible, the CVSS scoring methodology is product-agnostic — a buffer overflow is scored the same regardless of which product contains it. The model correctly learns to ignore vendor/product.

> [!tip] Future implication
> Do not invest in product/vendor enrichment for Phase 1 scoring. The 62% ceiling is a property of CVE description quality and CVSS methodology, not missing features. Three approaches have now failed to break it: CWE (v2, flat), multi-task (v6, +1.8pp), CPE (v6 Task 5, +0pp). Future improvements require fundamentally different data (e.g., exploit code, patch diffs, advisory text) or fundamentally different methodology (e.g., contrastive pre-training, curriculum learning).


## 29. Phase 1 has a hard accuracy ceiling around 62% with description-only input

Three successive architectural and feature interventions produced diminishing returns:

| Version | Change | Band accuracy | Delta |
|---------|--------|---------------|-------|
| v1 | ModernBERT-base, single head | 60.5% | baseline |
| v2 | + CWE as input feature | 60.2% | -0.3pp (noise) |
| v6 | Multi-task (9 heads, CVSS decomposition) | 62.3% | +1.8pp |
| v6+CPE | + vendor/product signal | 62.7% | +0.4pp (noise) |

The pattern is clear: each intervention yields less. The 62% ceiling is structural — CVE descriptions do not contain enough discriminative signal to reliably distinguish Medium from High or High from Critical. This is not a model problem; it is a data problem.

> [!check] v6 outcome
> v6 is the final architecture-focused attempt on Phase 1. The multi-task model (without CPE) is kept as the v6 scorer. Future Phase 1 work should focus on data enrichment (exploit availability, patch analysis, advisory cross-referencing) rather than model architecture.


## v7 lessons (Luxembourg national layer)


## 30. Pluggable national module pattern scales without code changes

v7 introduced `national/registry.py` with lazy-loading per member state. Adding Luxembourg required: (1) a JSON threshold file, (2) a Python assessment module, (3) one line in the registry. The three-tier router in `entity_incident.py` consumes it generically — no router code changes needed. This pattern is ready for other MS when their thresholds become available.

> [!tip] Future implication
> Adding a new member state (DE, FR, etc.) requires only data curation and a module implementing `is_covered()` + `assess_significance()`. The router, tests, and benchmarks are reusable. The bottleneck is regulatory data availability, not architecture.


## 31. IR thresholds must take precedence over national thresholds

LuxTrust is established in Luxembourg but is a trust service provider — an IR entity type (Art. 14). IR thresholds (EU-wide, 20-minute unavailability) take precedence over LU ILR thresholds. The three-tier router enforces this: IR → National → NIS2 ML. Getting this precedence wrong would under-escalate incidents at entities covered by the Implementing Regulation.

> [!tip] Future implication
> When adding national modules for new MS, the IR precedence check must remain the first tier. National thresholds only apply to entities NOT covered by the IR.


## 32. Sector-specific input fields are essential for quantitative thresholds

LU ILR thresholds are highly sector-specific: electricity uses points-of-delivery × duration matrices, rail uses train cancellation percentages, health uses reversible/irreversible person counts. The unified impact taxonomy (service_impact, data_impact, etc.) is necessary but insufficient — sector-specific fields via `sector_specific` dict are required for quantitative threshold evaluation.

> [!tip] Future implication
> Each national module may introduce new sector-specific fields. The `sector_specific` dict pattern accommodates this without changing the MCP tool signature. Document new fields in the threshold JSON.


## 33. DORA entities require explicit routing, not fallback

Luxembourg banking/financial entities fall under DORA (CSSF as competent authority), not ILR thresholds. Initially this was a fallback to NIS2 ML — v7 made it explicit: `is_lu_dora()` returns a result indicating DORA applicability with CSSF notification timeline, rather than silently falling through to the qualitative model.

> [!check] v7 outcome
> 20/20 curated LU scenarios correct. Three-tier routing 100%. 379 tests passing. The national layer is production-ready for Luxembourg.


## v8 lessons (HCPN national crisis qualification)


## 34. Crisis qualification scope is impact-on-country, not entity establishment

The HCPN framework protects Luxembourg's vital interests regardless of where the entity is established. A cloud provider established in Ireland (`ms_established=IE`) with a major outage affecting Luxembourg banking is in scope. This is fundamentally different from v7 entity significance, which correctly uses `ms_established=LU` for ILR thresholds. The initial plan incorrectly scoped to `ms_established=LU` — design review caught this before implementation.

> [!warning] Future implication
> When building national crisis qualification for other MS, always scope to "impact on the country" not "entities established in the country." These are different populations of incidents.


## 35. Delegated thresholds must return "undetermined", never invented values

The HCPN Cadre national delegates several quantitative thresholds to sectoral authorities ("substantial portion of population", "significant duration", "critical financial threshold"). These are genuinely undefined — no numeric values exist. The initial plan invented a `_AFFECTED_PERSONS_CONSULTATION_FLOOR = 1000` heuristic. Design review rejected this: inventing thresholds the framework explicitly delegates violates the principle that the module evaluates what it can and flags what it can't.

> [!tip] Future implication
> When a regulatory framework delegates a threshold to another authority, return `undetermined` and recommend consultation. Never substitute an arbitrary value — that creates false precision and liability.


## 36. Fast-track bypasses a criterion, it does not auto-satisfy it

The HCPN fast-track provision (malicious unauthorized access with grave disruption) says "proceed directly to Criterion 3" — it skips Criterion 2, it does not satisfy it. The initial plan set Criterion 2 to `status="met"` with a fast-track label. Design review corrected this to `status="bypassed"` — semantically different for an analyst reading the output. The qualification check is `all(cr.is_met or cr.is_bypassed)`, not `all(cr.is_met)`.

> [!check] v8 outcome
> `CriterionResult` now has four states: met, not_met, undetermined, bypassed. This captures the full decision space of the framework. 15/15 curated scenarios correct, 5/5 real incidents concordant with actual outcomes.


## 37. Real incident validation reveals the gap between synthetic and actual outcomes

v8 introduced validation against 10 real RETEX incidents (5 LU, 5 international). All 5 Luxembourg incidents matched actual crisis activation outcomes. Key insight: the authority judgment inputs (`coordination_required`, `urgent_decisions_required`) are the decisive factors — when set to `null` (uncertain), the module correctly recommends consultation rather than guessing. LuxTrust (29h national outage, no crisis activation) and CTIE Malware (MDM compromise, investigation ongoing) both matched as "recommend consultation" — borderline cases where the framework cannot be applied mechanically.

> [!tip] Future implication
> Synthetic benchmarks validate deterministic logic. Real incident validation validates the mapping between framework criteria and actual outcomes. Both are necessary. Expand real incident dataset quarterly from RETEX analyses.


## 38. Interdependent sector disruption should use the dependency graph, not simple counting

The HCPN Criterion 2 "economic consequences" sub-criterion includes "major disruption of interdependent sectors." The initial plan used `len(essential_sectors_affected) >= 2`. Design review pointed to the existing `sector_dependencies.json` graph (v5) as the correct tool — it checks whether affected sectors actually have dependency relationships, not just whether multiple sectors happen to be affected. `energy + food` is different from `energy + transport` (which are interdependent).

> [!check] v8 outcome
> `_check_interdependent_sectors()` uses `_load_sector_dependencies()` from `aggregation.py` to check actual graph edges. The same reference data serves both Phase 3 cascading propagation and HCPN economic consequences evaluation.


## 39. Large-scale cybersecurity incident = cross-border OR capacity exceeded

The HCPN framework defines "incident transfrontalier majeur" as disruptions exceeding Luxembourg's response capacity OR significant impact on another MS. The initial plan only checked `cross_border`. Design review identified that capacity exceeded is a separate trigger — an incident can be large-scale without cross-border impact if Luxembourg simply can't handle it alone. Both `cross_border` and `capacity_exceeded` already exist in the CyberScale taxonomy (Phase 3 O-level derivation), so no new fields were needed.

> [!tip] Future implication
> Reuse existing taxonomy fields where possible. The unified impact taxonomy prevents field proliferation across layers.
