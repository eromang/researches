# CyberScale — Lessons Learned (Phase 1, 2 & 3)

Retrospective on all three phases of CyberScale, distilled for future iterations and model training work.

**Related:** 2026-03-26-cyberscale-design, Progress-Tracker, 2026-03-29-cyberscale-plan-3-incident-classification


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
