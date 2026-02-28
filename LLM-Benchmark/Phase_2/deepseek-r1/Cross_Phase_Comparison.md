---
title: "Cross-Phase Comparison — deepseek-r1:8b (Phase I vs Phase II)"
date_created: 2026-02-28
date_updated: 2026-02-28
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
models_tested:
  - "deepseek-r1:8b"
related:
  - "[[deepseek-r1/Results_Data]]"
  - "[[deepseek-r1/Results]]"
  - "[[Phase_1/Results_Data]]"
  - "[[qwen3-thinking/Cross_Phase_Comparison]]"
---

# Cross-Phase Comparison — deepseek-r1:8b (Phase I vs Phase II)

## 1. Context and Motivation

deepseek-r1:8b (DeepSeek, Chinese-origin) was included in both benchmark phases. Phase 1 (400 records, 2 actors) identified several model-specific characteristics that warranted replication testing at scale:

1. **Hedging calibration** — deepseek-r1 showed very large effect sizes (Cohen's d = −2.15 to −2.45) distinguishing Confirmed from Neutral conditions, the largest calibration signal observed in Phase 1 across all models.
2. **China-sensitivity** — a 2.0x "further corroboration" ratio (Suspected: China 17.5% vs Russia 8.8%) suggested deepseek-r1 might shift the evidence burden differently for Chinese-origin attribution under uncertainty.
3. **CVE-2021-4034 fixation** — the model repeatedly cited PwnKit as its canonical technical example regardless of scenario context, suggesting a training-data artifact.
4. **Zero refusals** — deepseek-r1 produced no refusals across all 400 Phase 1 records, making it the most permissive model in Phase 1.

Phase 2 expands the test to 2,113 records across 5 actors (China, Russia, US, Iran, DPRK) and 48 scenarios, providing substantially more stable estimates. This note documents which Phase 1 findings replicate, which do not, and how the expanded actor and scenario space changes interpretation.

The China-sensitivity question is addressed at length in [[qwen3-thinking/Cross_Phase_Comparison]], which covers all three models tested in Phase 1. This note focuses on the deepseek-r1-specific findings.

## 2. Design Comparison

| Dimension | Phase 1 | Phase 2 |
|---|---|---|
| Total records | 400 | 2,113 |
| Actors | China, Russia (2) | China, Russia, US, Iran, DPRK (5) |
| Scenarios | 20 | 48 |
| Conditions | 5 (Neutral, CN/RU × Suspected/Confirmed) | 11 (Neutral, 5 actors × Suspected/Confirmed) |
| Records per condition | 40 (T=0.0) + 40 (T=0.7) = 80 pooled | 96 per condition |
| Temperatures | T=0.0, T=0.7 | T=0.0, T=0.7 |
| Model mode | Thinking enabled, `<think>` tokens stripped | Thinking enabled, `<think>` tokens stripped |
| Model version | deepseek-r1:8b | deepseek-r1:8b |

The increase from 80 to 96 records per condition (T-pooled) is modest, but the expansion from 2 to 5 actors and 20 to 48 scenarios substantially reduces the risk that findings are scenario-specific artefacts.

## 3. Hedging Calibration Replication

### 3.1 Phase 1 baseline

Phase 1 measured hedging (mean hedge phrases per 1,000 characters) and escalation scores across five conditions. The core calibration signal was the distance between Confirmed and Neutral conditions.

| Condition | T=0.0 Hedge | T=0.7 Hedge | T=0.0 Escalation | T=0.7 Escalation |
|---|---|---|---|---|
| China_Confirmed | 4.35 | 4.78 | 4.15 | 4.15 |
| China_Suspected | 6.50 | 6.83 | 4.55 | 4.68 |
| Neutral | 7.90 | 7.28 | 3.75 | 3.90 |
| Russia_Confirmed | 4.20 | 4.33 | 4.65 | 5.20 |
| Russia_Suspected | 7.10 | 6.98 | 4.55 | 4.80 |

The Confirmed-vs-Neutral gap (China: −3.55, Russia: −3.70 at T=0.0) corresponds to effect sizes of d = −2.15 to −2.45 — exceptionally large by social science conventions. The model reliably produces less hedging language when attribution is confirmed than when no actor is named, which is the correct direction.

### 3.2 Phase 2 replication

Phase 2 findings (see [[deepseek-r1/Results_Data]] Section 5):

- Suspected vs Confirmed calibration: d = 1.24 to 1.99 — strong effect, correct direction (Suspected conditions carry more hedging than Confirmed conditions)
- Confirmed vs Neutral calibration: d = −0.82 to −1.15 — moderate-to-large effect, correct direction
- The calibration gradient (Neutral > Suspected > Confirmed for hedging) is preserved

### 3.3 Why are Phase 2 effect sizes smaller?

The Phase 2 estimates are smaller than Phase 1's d = −2.15 to −2.45. Three factors account for this:

1. **Scenario diversity.** Phase 1 used 20 scenarios; Phase 2 uses 48. Additional scenarios spanning more sectors introduce conditions where the Confirmed/Neutral distinction is less lexically salient, compressing the mean difference.
2. **Actor variance.** The 5-actor design introduces within-condition variance (e.g., China_Confirmed and DPRK_Confirmed have different rhetorical demands) that inflates the pooled standard deviation, reducing d.
3. **Regression to the mean.** Phase 1's extreme effect sizes at N=40/condition may partially reflect sampling variation. Phase 2's N=96/condition provides more stable estimates.

**Verdict: REPLICATES.** The calibration gradient is preserved in both phases. deepseek-r1 systematically reduces hedging language in confirmed attribution contexts. The effect is large in both phases, with Phase 2 providing the more reliable estimate.

## 4. China-Sensitivity Replication

### 4.1 Phase 1 signal

Phase 1 observed a 2.0x ratio for "further corroboration" under Suspected conditions:

| Condition | Phase 1 Rate | Phase 1 N |
|---|---|---|
| China_Suspected | 17.5% | 80 |
| Russia_Suspected | 8.8% | 80 |
| Ratio | 2.0x | — |

At Confirmed level, the pattern was absent: 0% China vs 2.5% Russia. This was interpreted as deepseek-r1 applying an asymmetric evidence burden specifically under uncertainty about Chinese-origin attribution.

### 4.2 Phase 2 results

| Condition | Phase 2 Rate | Phase 2 N | vs Phase 1 |
|---|---|---|---|
| China_Suspected | 10.0% | ~96 | −7.5pp |
| Russia_Suspected | 17.9% | ~96 | +9.1pp |
| Ratio (Suspected) | 0.6x | — | Inverted |
| China_Confirmed | 13.3% | ~96 | — |
| Russia_Confirmed | 10.3% | ~96 | — |
| Ratio (Confirmed) | 1.3x | — | Mild China lean |

The Suspected ratio inverts from 2.0x (Phase 1) to 0.6x (Phase 2). Russia_Suspected now shows a higher "further corroboration" rate than China_Suspected. The Confirmed ratio (1.3x) represents a mild China lean, but at N≈96, a difference of 3 percentage points is within sampling noise.

### 4.3 Confidence pattern analysis

The confidence pattern analysis script (see [[scripts/analyze_confidence_patterns.py]]) ran pairwise tests across all 5 actors. China-vs-rest tests: **0 of 5 significant**. No actor-specific concentration of the "further corroboration" phrase was detected.

### 4.4 Why did the pattern not replicate?

As documented in [[qwen3-thinking/Cross_Phase_Comparison]] Section 4 for the multi-model context, the most likely explanation is **small-sample instability in Phase 1**. With N=80 per condition (40 per temperature), a difference of 7 responses separates 8.8% from 17.5%. deepseek-r1's thinking-mode architecture introduces path-dependent non-determinism: at T=0.0, even identical prompts can produce different reasoning chains, leading to different phrase choices. The 2.0x ratio may have been a stochastic artifact of a specific batch of reasoning paths.

The expanded Phase 2 design (N=96, 5 actors, 48 scenarios) provides no support for China-targeted evidence-burden asymmetry in deepseek-r1.

**Verdict: DOES NOT REPLICATE.** The Phase 1 2.0x China/Russia ratio on "further corroboration" Suspected is not confirmed in Phase 2. The ratio inverts to 0.6x, and 0/5 China-vs-rest pairwise tests reach significance.

## 5. CVE-2021-4034 Fixation Persistence

### 5.1 Phase 1 observation

Phase 1 identified deepseek-r1's tendency to cite CVE-2021-4034 (PwnKit — Linux polkit privilege escalation vulnerability, disclosed January 2022) as its canonical technical example across a disproportionate range of scenarios. This appeared regardless of whether the scenario context involved Linux endpoints, privilege escalation, or supply chain vectors. It was flagged as a probable **training-data artifact**: if CVE-2021-4034 was over-represented in deepseek-r1's pre-training corpus (e.g., through analysis reports, CTI feeds, or security blog aggregation), the model's generative pathway would preferentially route to that CVE when asked to provide a technical exemplar.

### 5.2 Phase 2 CVE usage

Phase 2 data shows a CVE mention rate of approximately **36% overall** across all deepseek-r1 records. This rate is notable because:

- It is higher than llama3.1 (which avoids CVE identifiers in favour of technique descriptions) and qwen3:8b (which uses CVE identifiers selectively)
- The 36% rate reflects a general tendency to anchor technical content to specific vulnerability identifiers, not necessarily PwnKit specifically

Whether Phase 2 shows continued CVE-2021-4034 fixation or whether the model has diversified to other CVEs requires inspection of the raw output text (see [[deepseek-r1/Results_Data]] Section 8 for CVE frequency tables). The benchmark's Phase 2 scenario pool was designed to reduce single-CVE anchoring by spanning more sectors and attack types. If CVE-2021-4034 still dominates within the 36% CVE-mentioning records, the training-data artifact persists. If the distribution has broadened, the Phase 1 fixation was partially scenario-driven.

**Verdict: NEEDS EXAMINATION.** The overall CVE mention rate (~36%) is elevated and consistent with deepseek-r1's Phase 1 behaviour pattern. Whether CVE-2021-4034 remains the dominant specific identifier requires frequency analysis of Phase 2 output text.

## 6. Output Length and Latency Comparison

### 6.1 Phase 1 baseline

| Temperature | Condition | Mean Output (chars) | Mean Latency (ms) |
|---|---|---|---|
| T=0.0 | China_Confirmed | 7,783 | 41,487 |
| T=0.0 | China_Suspected | 8,270 | 44,242 |
| T=0.0 | Neutral | 7,804 | 40,380 |
| T=0.0 | Russia_Confirmed | 8,118 | 42,875 |
| T=0.0 | Russia_Suspected | 8,025 | 42,226 |
| T=0.7 | China_Confirmed | 8,392 | 43,028 |
| T=0.7 | China_Suspected | 8,301 | 42,355 |
| T=0.7 | Neutral | 8,244 | 41,096 |
| T=0.7 | Russia_Confirmed | 8,324 | 42,680 |
| T=0.7 | Russia_Suspected | 8,176 | 42,094 |
| **Pooled mean** | **—** | **~8,144** | **~42,246** |

### 6.2 Phase 2 baseline

| Metric | Phase 2 Value | Phase 1 Pooled | Delta |
|---|---|---|---|
| Mean output (chars) | ~7,932 | ~8,144 | −212 (−2.6%) |
| Mean latency (ms) | ~44,500 | ~42,246 | +2,254 (+5.3%) |

### 6.3 Interpretation

The output length decrease (−212 chars, −2.6%) is within the expected variation from scenario-pool effects. Phase 2's 48-scenario pool includes scenarios that elicit shorter responses (e.g., scenarios focused on a single technical indicator rather than a full threat narrative). The latency increase (+2.25s, +5.3%) likely reflects hardware load variation across the multi-day Phase 2 run rather than a model-level change.

Temperature effects remain consistent across phases: T=0.7 produces slightly longer outputs than T=0.0 in both phases (Phase 1: ~8,287 vs ~8,000; Phase 2: directionally similar).

**Verdict: REPLICATES.** deepseek-r1 produces long, high-latency outputs in both phases (~8,000 chars, ~42–45s). The differences between phases are small and consistent with scenario-pool and run-environment variation, not model-level change.

## 7. Refusal Behaviour

### 7.1 Phase 1 baseline

deepseek-r1 produced **zero refusals** across all 400 Phase 1 records (0.0%). This was the most permissive result observed in Phase 1 and was consistent across both temperatures and all five conditions.

### 7.2 Phase 2 baseline

| Metric | Phase 2 Value | Phase 1 Value |
|---|---|---|
| Total refusals | 6 of 2,113 (0.28%) | 0 of 400 (0.00%) |
| Refusal rate | 0.28% | 0.00% |
| Primary condition | Russia_Suspected T=0.0 (3 of 6) | — |

The 6 refusals in Phase 2 are spread across a corpus of 2,113 records. Russia_Suspected at T=0.0 accounts for 3 of the 6, which may reflect specific scenario phrasings that triggered a cautious response rather than a systematic change in model behaviour.

### 7.3 Interpretation

A jump from 0.00% to 0.28% is not operationally meaningful. deepseek-r1 remains **highly permissive** in Phase 2. The 6 refusals likely reflect edge cases in specific scenario-prompt combinations rather than a systematic refusal policy. No condition shows refusal rates above 3% (3 out of 96 records for Russia_Suspected T=0.0 is 3.1%, at the threshold of noise for a 96-record cell).

For comparison, llama3.1 showed a refusal pattern concentrated on US conditions in Phase 2 (documented in [[llama31/Results_Data]]). deepseek-r1 shows no condition-specific refusal concentration of similar magnitude.

**Verdict: REPLICATES.** deepseek-r1 remains near-zero-refusal in both phases. The 0.28% Phase 2 rate is consistent with the 0.00% Phase 1 rate given the 5x increase in total records.

## 8. Verdict Table

| Phase 1 Finding | Phase 1 Evidence | Phase 2 Result | Replication Status |
|---|---|---|---|
| Hedging calibration (Confirmed < Neutral) | d = −2.15 to −2.45 | d = −0.82 to −1.15; gradient preserved | REPLICATES |
| Suspected > Confirmed hedging | d = ~1.5–2.0 | d = 1.24–1.99 | REPLICATES |
| China evidence-burden asymmetry (Suspected) | 2.0x China/Russia "further corroboration" | 0.6x (inverted); 0/5 China-vs-rest significant | DOES NOT REPLICATE |
| Zero refusals | 0.00% (400 records) | 0.28% (2,113 records) | REPLICATES |
| Long output / high latency | ~8,144 chars; ~42.2s | ~7,932 chars; ~44.5s | REPLICATES |
| CVE-2021-4034 fixation | PwnKit cited across diverse scenarios | ~36% CVE mention rate; specific CVE distribution TBD | NEEDS EXAMINATION |

## 9. Data Sources

| Source | Path |
|---|---|
| Phase 1 JSONL | `results/Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl` |
| Phase 2 JSONL | `results/run_20260224T103518Z_51e859312629dea4.jsonl` |
| Phase 1 summary | `results/Phase_1/` (analysis_report.md, Results_Data) |
| Phase 2 deepseek-r1 data | `results/Phase_2/deepseek-r1/` |
| Confidence pattern script | `scripts/analyze_confidence_patterns.py` |
| Cross-model confidence patterns | [[Phase_2/Cross_Model_Confidence_Patterns]] |
| qwen3 cross-phase comparison | [[qwen3-thinking/Cross_Phase_Comparison]] |
| deepseek-r1 Phase 2 results | [[deepseek-r1/Results_Data]] |

### Models referenced

| Model | Origin | Phase 1 Records | Phase 2 Records |
|---|---|---|---|
| deepseek-r1:8b | DeepSeek (CN) | 400 | 2,113 |
| qwen3:8b | Alibaba (CN) | 400 | 2,109 |
| llama3.1:8b-instruct-q4_K_M | Meta (US) | 400 | 2,112 |

---

*Generated 2026-02-28. Cross-phase analysis based on Phase 1 condition-level summary statistics and Phase 2 full JSONL corpus.*
