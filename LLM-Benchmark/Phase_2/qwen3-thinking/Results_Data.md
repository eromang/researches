---
title: "Phase 2 Results — EU Cyber LLM Benchmark (qwen3:8b Thinking)"
date_created: 2026-02-26
date_updated: 2026-02-27
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - qwen3:8b
model_type: reasoning
thinking_mode: "strip_thinking (no_think: false)"
temperatures:
  - 0.0
  - 0.7
scenarios: 48
conditions: 11
total_records: 2112
ok_records: 2109
failed_records: 3
---

# Phase 2 Results — EU Cyber LLM Benchmark (qwen3:8b Thinking)

## 1. Executive Summary

Phase II tested qwen3:8b (Alibaba, reasoning mode with `--strip-thinking`) across an expanded 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,112 records with 2,109 successful completions (99.86%) and 3 timeout failures. **The central finding is that certainty calibration is exceptionally strong and actor-uniform:** all five actors show very large hedging reductions under Confirmed attribution (Cohen's d = 2.255–3.349). **The model produces zero refusals across all conditions and temperatures** — a stark contrast to llama3.1's 2.4% overall refusal rate and its US_Confirmed refusal asymmetry. Unlike llama3.1, qwen3:8b shows significant escalation increases when any actor is attributed (vs Neutral), though the Suspected-to-Confirmed escalation shift remains small. Actor symmetry on hedging is excellent (no significant pairwise differences at T=0.0). The model is non-deterministic at T=0.0 due to its internal thinking process, with only 9.3% of prompt pairs producing identical output across replications. CVE mention rates are very high (56.5% overall).

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 prompts.

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21–S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | qwen3:8b (Alibaba, 8B, reasoning mode, `--strip-thinking`) |
| Temperatures | 0.0 (greedy decoding), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing qwen3:8b across 5 actors x 48 scenarios = 2,112 records, enabling comprehensive actor-comparison analysis.

Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]

---

## 3. Data Completeness

| Metric | Value |
|---|---|
| Expected records | 2,112 |
| Collected records | 2,112 |
| Records with `ok: true` | 2,109 (99.86%) |
| Records with `ok: false` | 3 (0.14%) — all timeout failures |
| Factorial coverage | 3 cells missing rep=2 (S38_Russia_Confirmed, S46_China_Suspected, S47_Russia_Suspected) |
| Parse failures | 0 |

The 3 timeout failures are all at T=0.0, rep=2 only, with 600-second timeout and 0 characters of output. They are attributed to degenerate thinking loops in qwen3's reasoning architecture. See [[qwen3-thinking/Greedy_Decoding_Failure_Note]] for detailed analysis.

---

## 4. Model Profile

### 4.1 Output Length and Latency

| Temperature | Mean Latency (ms) | P95 Latency (ms) | Mean Length (chars) | Length Stdev | CV % |
|---|---|---|---|---|---|
| 0.0 | 35,244 | 46,786 | 3,817 | 378 | 9.9% |
| 0.7 | 33,338 | 44,241 | 3,768 | 324 | 8.6% |

qwen3:8b produces longer output than llama3.1 (3,817 vs 3,070 chars at T=0.0) at significantly higher latency (35.2s vs 13.1s). The latency premium reflects the internal thinking phase that runs before visible output generation.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0% (0/1,053) | 56.4% |
| 0.7 | 0% (0/1,056) | 56.6% |
| **Combined** | **0% (0/2,109)** | **56.5%** |

Zero refusals across all conditions and temperatures. This is the most permissive safety posture observed in Phase II testing. The CVE mention rate (56.5%) is substantially higher than llama3.1 (34.8%).

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 142,922 | 104,721 | **0.73** |

A variance ratio below 1.0 is anomalous — T=0.7 is less variable than T=0.0. This inverted pattern is unique to the reasoning model: the internal thinking phase introduces substantial non-determinism at T=0.0, inflating variance to levels that exceed sampling noise at T=0.7.

### 4.4 Stability at T=0.0

At T=0.0, only 49 of 525 prompt_id pairs (9.3%) produced identical output across rep=1 and rep=2. The remaining 476 pairs (90.7%) show length differences.

**qwen3:8b is not deterministic at T=0.0.** This is a direct consequence of its thinking architecture: the internal chain-of-thought reasoning introduces path-dependent variation even under greedy decoding. This contrasts sharply with llama3.1, which is perfectly deterministic at T=0.0 (100% identical pairs).

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected to Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 7.22 | 2.47 | -4.75 | **3.349** | < 10^-15 |
| Russia | 7.24 | 2.33 | -4.92 | **2.921** | < 10^-15 |
| China | 6.63 | 2.20 | -4.43 | **2.869** | < 10^-15 |
| Iran | 7.05 | 2.50 | -4.55 | **2.815** | < 10^-15 |
| DPRK | 6.49 | 2.21 | -4.28 | **2.459** | < 10^-15 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Iran | 6.95 | 2.40 | -4.55 | **3.078** | < 10^-15 |
| China | 7.09 | 2.14 | -4.96 | **3.052** | < 10^-15 |
| Russia | 7.08 | 2.58 | -4.50 | **2.871** | < 10^-15 |
| US | 7.35 | 2.73 | -4.63 | **2.721** | < 10^-15 |
| DPRK | 6.50 | 2.60 | -3.90 | **2.255** | < 10^-15 |

**All 10 certainty effects are very large (d > 2.25) and statistically significant (p < 10^-15).** qwen3:8b's hedging calibration is substantially stronger than llama3.1's (d = 2.255–3.349 vs d = 1.338–2.360), indicating more aggressive certainty response to the Suspected/Confirmed framing.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral:

**T=0.0 (Neutral mean = 5.10):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| China | 2.20 | -2.90 | -1.884 | < 10^-15 |
| DPRK | 2.21 | -2.90 | -1.746 | < 10^-15 |
| US | 2.47 | -2.63 | -1.738 | < 10^-15 |
| Russia | 2.33 | -2.78 | -1.715 | < 10^-15 |
| Iran | 2.50 | -2.60 | -1.567 | < 10^-15 |

**T=0.7 (Neutral mean = 5.63):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Iran | 2.40 | -3.23 | -2.200 | < 10^-15 |
| China | 2.14 | -3.49 | -2.187 | < 10^-15 |
| Russia | 2.58 | -3.04 | -1.926 | < 10^-15 |
| DPRK | 2.60 | -3.02 | -1.898 | < 10^-15 |
| US | 2.73 | -2.90 | -1.706 | < 10^-15 |

Confirmed attribution always reduces hedging far below the neutral baseline, with uniformly large effect sizes across all actors.

### 5.3 Escalation Shift (Suspected to Confirmed)

Unlike llama3.1, qwen3:8b shows **significant escalation increases from Neutral to Confirmed** for all actors (Section 8). However, the Suspected-to-Confirmed escalation shift remains modest:

| Actor | T=0.0 d | T=0.7 d | Interpretation |
|---|---|---|---|
| China | -0.042 | -0.238 | Negligible |
| Russia | -0.071 | -0.341 | Small at T=0.7 |
| US | -0.228 | -0.103 | Small at T=0.0 |
| Iran | -0.181 | -0.183 | Negligible |
| DPRK | **-0.296** | **-0.438** | Small to medium |

Certainty calibration operates primarily through hedging reduction, though DPRK shows a notable escalation increase from Suspected to Confirmed, especially at T=0.7 (d = -0.438).

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 2.20 | 2.33 | 2.47 | 2.50 | 2.21 | 5.10 |
| Escalation terms | 5.50 | 5.86 | 5.31 | 5.82 | 5.96 | 4.11 |
| Strong assertions | 0.93 | 1.02 | 0.88 | 1.04 | 1.38 | 0.36 |
| E/H ratio | 2.50 | 2.52 | 2.15 | 2.33 | 2.70 | 0.81 |
| Mean output (chars) | 3,790 | 3,857 | 3,784 | 3,823 | 3,796 | 3,671 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 4.43 | 4.39 | 4.33 | 4.55 | 4.11 | 4.33 |
| APT mentions | 0.92 | 0.37 | 0.07 | 0.88 | 0.06 | 0.29 |

### 6.2 Actor Symmetry at T=0.7

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 2.14 | 2.58 | 2.73 | 2.40 | 2.60 | 5.63 |
| Escalation terms | 5.46 | 6.13 | 5.55 | 5.58 | 6.40 | 4.65 |
| E/H ratio | 2.56 | 2.37 | 2.03 | 2.33 | 2.46 | 0.83 |
| Mean output (chars) | 3,744 | 3,829 | 3,775 | 3,746 | 3,802 | 3,670 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |

### 6.3 Key Actor-Level Observations

1. **All actors produce substantially less hedging and more escalation than Neutral** — attribution both reduces caution and increases conflict-related language.
2. **E/H ratios exceed 1.0 for all actors at both temperatures** (range 2.03–2.70), meaning qwen3:8b produces more escalation terms than hedge terms under attribution. This is the opposite of llama3.1 (E/H = 0.50–0.72).
3. **Hedging at Confirmed level is tightly clustered** (2.20–2.50 at T=0.0, 2.14–2.73 at T=0.7) — a narrow range indicating strong actor symmetry.
4. **APT mention rates are actor-sensitive:** China (0.92) and Iran (0.88) receive far more APT references than US (0.07) or DPRK (0.06), reflecting training data patterns about known threat actor groups.
5. **Zero refusals for all actors** — no Western-actor sensitivity, no safety classifier activation.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| US vs China | 0.190 | 0.189 | **0.349** | 0.016 | T=0.7 only |
| US vs Russia | 0.094 | 0.515 | 0.086 | 0.549 | No |
| Iran vs Russia | 0.105 | 0.469 | -0.129 | 0.372 | No |
| Iran vs China | 0.191 | 0.169 | 0.177 | 0.221 | No |
| DPRK vs China | 0.007 | 0.964 | 0.294 | 0.042 | T=0.7 marginal |
| DPRK vs Russia | -0.071 | 0.622 | 0.013 | 0.927 | No |
| China vs Russia | -0.084 | 0.564 | -0.190 | 0.189 | No |

**No pairwise hedging comparison reaches significance at T=0.0.** At T=0.7, US vs China (d = 0.349, p = 0.016) and DPRK vs China (d = 0.294, p = 0.042) reach significance, both showing marginally more hedging relative to China. This is stronger actor symmetry than llama3.1 at T=0.0 (which had one significant DPRK vs China comparison).

### 7.2 Pairwise Actor Tests — Escalation at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| DPRK vs China | 0.238 | 0.099 | **0.467** | 0.001 | **T=0.7 Yes** |
| US vs Russia | -0.255 | 0.077 | -0.280 | 0.053 | Marginal |
| DPRK vs Russia | 0.048 | 0.740 | 0.136 | 0.347 | No |
| Iran vs China | 0.184 | 0.204 | 0.064 | 0.660 | No |
| Iran vs Russia | -0.022 | 0.879 | -0.278 | 0.055 | Marginal at T=0.7 |
| US vs China | -0.089 | 0.537 | 0.045 | 0.753 | No |

DPRK_Confirmed produces significantly more escalation language than China_Confirmed at T=0.7 (d = 0.467, p = 0.001). At T=0.0, the same comparison is marginal (d = 0.238, p = 0.099). US vs Russia trends toward US producing less escalation at both temperatures but does not reach significance.

### 7.3 Pairwise Actor Tests — Strong Assertions at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| DPRK vs China (T=0.0) | **0.536** | 0.0002 | 0.045 | 0.757 | **T=0.0 Yes** |
| DPRK vs Russia (T=0.0) | **0.423** | 0.003 | 0.011 | 0.937 | **T=0.0 Yes** |
| US vs Russia | -0.186 | 0.199 | **-0.358** | 0.013 | **T=0.7 Yes** |
| US vs China | -0.066 | 0.646 | **-0.313** | 0.030 | **T=0.7 Yes** |
| Iran vs China | 0.130 | 0.348 | 0.134 | 0.354 | No |
| Iran vs Russia | 0.023 | 0.872 | 0.099 | 0.491 | No |

At T=0.0, DPRK_Confirmed produces significantly more strong assertion terms than both China_Confirmed (d = 0.536, p = 0.0002) and Russia_Confirmed (d = 0.423, p = 0.003). At T=0.7, US_Confirmed produces significantly fewer strong assertion terms than Russia_Confirmed (d = -0.358, p = 0.013) and China_Confirmed (d = -0.313, p = 0.030). The model is less assertive when attributing to the US at the sampling temperature.

### 7.4 Pairwise Actor Tests — Output Length at Confirmed Level

No pairwise actor comparison on output length reaches significance at either temperature. The largest effect is Russia vs Neutral at both temperatures (d = 0.53, p < 0.001), reflecting Russia_Confirmed's slightly longer output rather than actor asymmetry.

---

## 8. Escalation Analysis

### 8.1 Attribution Escalation Effect (Confirmed vs Neutral)

Unlike llama3.1 where escalation calibration was negligible (d < 0.40), qwen3:8b shows **significant escalation increases** when any actor is attributed:

**T=0.0:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Russia | 5.86 | 4.11 | +1.75 | **0.931** | < 10^-10 |
| Iran | 5.82 | 4.11 | +1.71 | **0.925** | < 10^-10 |
| DPRK | 5.96 | 4.11 | +1.84 | **0.920** | < 10^-10 |
| China | 5.50 | 4.11 | +1.39 | **0.762** | < 10^-7 |
| US | 5.31 | 4.11 | +1.20 | **0.550** | < 10^-4 |

**T=0.7:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| DPRK | 6.40 | 4.65 | +1.75 | **0.902** | < 10^-9 |
| Russia | 6.13 | 4.65 | +1.48 | **0.737** | < 10^-6 |
| Iran | 5.58 | 4.65 | +0.93 | **0.494** | < 10^-3 |
| US | 5.55 | 4.65 | +0.91 | **0.454** | < 10^-3 |
| China | 5.46 | 4.65 | +0.81 | **0.402** | < 10^-2 |

**This is a distinctive qwen3:8b behavior:** confirmed attribution simultaneously reduces hedging AND increases escalation language. The dual-channel calibration is a key differentiator from llama3.1, which only calibrated through hedging. Effect sizes range from medium (d = 0.402) to large (d = 0.931), with DPRK and Russia consistently receiving the highest escalation increases.

### 8.2 Escalation Ordering

The escalation ordering at T=0.0 is: **DPRK > Russia > Iran > China > US > Neutral**. At T=0.7: **DPRK > Russia > Iran > US > China > Neutral**. DPRK and Russia receive the most escalation language; China and US receive the least. This ordering may reflect training data patterns: DPRK and Russian cyber operations are frequently described in conflict-laden terms, while US and Chinese operations are framed more neutrally.

---

## 9. Temperature Stability

### 9.1 Variance Ratio

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 142,922 | 104,721 | **0.73** |

The inverted variance ratio (T=0.7 < T=0.0) is unique to the reasoning model. The thinking phase introduces stochastic variation even under greedy decoding, making T=0.0 noisier than expected.

### 9.2 Refusal Divergence

No refusal divergence exists — all conditions produce 0% refusal at both temperatures.

### 9.3 CV% Comparison

| Temperature | CV% (Output Length) |
|---|---|
| 0.0 | 9.9% |
| 0.7 | 8.6% |

Unlike llama3.1 (where CV% doubled from 10.7% to 23.2% at T=0.7), qwen3:8b shows remarkably stable output variability across temperatures, with T=0.7 actually producing slightly less variability than T=0.0.

### 9.4 Stability Summary

qwen3:8b is not deterministic at T=0.0 (only 9.3% identical replication pairs). The thinking architecture overrides the greedy decoding guarantee. At T=0.7, the model remains stable, with no refusal activation and similar output distributions. Temperature has minimal practical effect on qwen3:8b's behavior.

---

## 10. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 10.1 T=0.0

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| DPRK_Confirmed | 85 | 9 | 0 | 2 |
| China_Confirmed | 78 | 18 | 0 | 0 |
| Russia_Confirmed | 78 | 17 | 0 | 0 |
| Iran_Confirmed | 77 | 19 | 0 | 0 |
| US_Confirmed | 70 | 24 | 0 | 2 |
| DPRK_Suspected | 29 | 67 | 0 | 0 |
| Iran_Suspected | 24 | 72 | 0 | 0 |
| Russia_Suspected | 19 | 76 | 0 | 0 |
| US_Suspected | 18 | 76 | 2 | 0 |
| China_Suspected | 17 | 77 | 1 | 0 |
| Neutral | 17 | 70 | 9 | 0 |

### 10.2 T=0.7

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| Russia_Confirmed | 84 | 12 | 0 | 0 |
| DPRK_Confirmed | 82 | 14 | 0 | 0 |
| Iran_Confirmed | 82 | 14 | 0 | 0 |
| China_Confirmed | 81 | 15 | 0 | 0 |
| US_Confirmed | 73 | 23 | 0 | 0 |
| Russia_Suspected | 25 | 71 | 0 | 0 |
| Iran_Suspected | 25 | 70 | 0 | 1 |
| China_Suspected | 25 | 69 | 2 | 0 |
| DPRK_Suspected | 20 | 75 | 1 | 0 |
| US_Suspected | 18 | 76 | 2 | 0 |
| Neutral | 19 | 63 | 14 | 0 |

### 10.3 Key Observations

1. **Confirmed conditions produce predominantly High labels** (70–85 out of 96), while Suspected conditions produce predominantly Moderate labels (67–77 out of 96). This clean bifurcation indicates strong confidence calibration aligned with the attribution framing.
2. **"Low" labels appear almost exclusively in Neutral and Suspected conditions** — only Neutral produces substantial Low counts (9 at T=0.0, 14 at T=0.7). Confirmed conditions never produce Low labels.
3. **"Unknown" labels are rare** (only 4 total at T=0.0, 1 at T=0.7) — far fewer than llama3.1 at T=0.7, indicating qwen3:8b produces parseable confidence text more reliably.
4. **US_Confirmed has the lowest High rate** among Confirmed conditions at both temperatures (70–73 out of 96 vs 77–85 for others), suggesting marginally less confidence when attributing to the US.
5. **Confidence label distribution is stable across temperatures** — unlike llama3.1, where T=0.7 produced massive fragmentation, qwen3:8b's distribution barely changes.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | 56.5% |
| CVE rate at T=0.0 | 56.4% |
| CVE rate at T=0.7 | 56.6% |

The CVE mention rate is substantially higher than llama3.1 (56.5% vs 34.8%).

### 11.2 CVE Rate by Condition

| Condition | CVE Rate |
|---|---|
| China_Suspected | 62.8% |
| Neutral | 62.5% |
| DPRK_Confirmed | 60.4% |
| US_Suspected | 58.9% |
| Iran_Suspected | 58.3% |
| Russia_Suspected | 58.1% |
| DPRK_Suspected | 57.3% |
| US_Confirmed | 55.2% |
| China_Confirmed | 51.0% |
| Iran_Confirmed | 50.0% |
| Russia_Confirmed | 47.1% |

CVE rates cluster around 47–63%, with Confirmed conditions generally producing lower rates than Suspected conditions. This is consistent with the observation that confirmed attribution focuses the model's output, leaving less room for CVE elaboration.

### 11.3 CVE Accuracy Assessment

The 56.5% rate is notably high and warrants careful accuracy validation. Given that qwen3:8b produces more CVE references per response than llama3.1, the hallucination risk is commensurately higher. A systematic CVE accuracy audit is recommended as follow-up work.

---

## 12. Reasoning Model Specifics

### 12.1 Latency Premium

| Model | Mean Latency (T=0.0) | Mean Latency (T=0.7) |
|---|---|---|
| qwen3:8b | 35,244 ms | 33,338 ms |
| llama3.1:8b | 13,141 ms | 10,975 ms |
| **Ratio** | **2.68x** | **3.04x** |

qwen3:8b runs 2.7–3.0x slower than llama3.1, reflecting the computational cost of internal chain-of-thought reasoning before visible output generation. The thinking phase is invisible in the output (`--strip-thinking`) but consumes substantial inference time.

### 12.2 Thinking-Induced Non-Determinism

The qwen3:8b thinking process creates non-determinism at T=0.0:

| Metric | qwen3:8b | llama3.1:8b |
|---|---|---|
| Identical rep pairs at T=0.0 | 49/525 (9.3%) | 528/528 (100%) |
| Output length CV% at T=0.0 | 9.9% | 10.7% |
| Variance ratio (T=0.7 / T=0.0) | 0.73 | 4.39 |

Despite non-identical outputs, overall variability (CV%) is comparable between the two models at T=0.0. The key difference is the source: llama3.1's variability at T=0.0 comes from the scenario pool (output varies between scenarios but not within); qwen3:8b has additional within-prompt variability from the thinking process.

### 12.3 Timeout Failures

3 records (0.14%) failed with 600-second timeout and 0 output characters. All three are T=0.0, rep=2 only:

| prompt_id | Sector | Latency |
|---|---|---|
| S38_Russia_Confirmed | Semiconductors | 600,010 ms |
| S46_China_Suspected | Finance | 599,999 ms |
| S47_Russia_Suspected | Telecom | 599,998 ms |

These are attributed to degenerate thinking loops where the model's internal reasoning never converges to visible output. The near-timeout latency of S38_DPRK_Confirmed rep=1 (420,680 ms, yet producing 3,429 chars) supports this hypothesis.

No other model in Phase II (llama3.1, gemma3n) produced any timeout failures.

---

## 13. Model Scorecard

| Dimension | qwen3:8b (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Reasoning (thinking mode) |
| **Temperature stability** | Inverted (variance ratio 0.73; no refusals at any T) |
| **Refusal rate** | 0% (zero refusals across all conditions) |
| **Hedging calibration** | Very strong and uniform (d = 2.255–3.349 across 5 actors) |
| **Escalation calibration** | Significant vs Neutral (d = 0.402–0.931); small Suspected-to-Confirmed |
| **Actor symmetry (hedging)** | Excellent — no pairwise differences at T=0.0; two small effects at T=0.7 |
| **Actor symmetry (escalation)** | Good — DPRK vs China significant at T=0.7 |
| **Western actor sensitivity** | None — zero refusals; US shows mild assertion reduction at T=0.7 |
| **CVE mention rate** | Very high (56.5%) — accuracy unverified |
| **Confidence label output** | Strong and stable across temperatures |
| **Rhetorical profile** | Escalation-dominant (E/H = 2.03–2.70 at Confirmed) |
| **Confidence pattern symmetry** | Excellent — 1/50 pairwise tests significant (borderline, fails Bonferroni) |
| **Timeout failures** | 3/2,112 (0.14%) — thinking-loop degeneration |
| **Latency premium** | 2.7–3.0x vs llama3.1 |
| **T=0.0 determinism** | Non-deterministic (9.3% identical pairs) |

---

## 14. Cross-Phase Comparison — Finding 4 Replication

Phase 1 Finding 4 reported that qwen3:8b uses China-specific diplomatic framing ("further corroboration required" at 6x China/Russia ratio, China-exclusive "false positives" and "avoid escalation" warnings). A systematic phrase-search across Phase 2's 2,109 records and 5 actors **does not replicate this pattern.** The China/Russia ratio for "further corroboration" collapses from 3.6x (Phase 1) to 0.8x (Phase 2), and previously China-exclusive phrases distribute uniformly across all actors.

The analysis now covers **three models** (qwen3:8b, llama3.1:8b, deepseek-r1:8b) and **five actor pairings** (China/Russia, China/US, China/DPRK, US/Russia, DPRK/Russia). llama3.1 (Meta, US-origin, 2,112 Phase 2 records) does not use the Finding 4 indicator phrases at all — they are qwen3-specific vocabulary. deepseek-r1 (DeepSeek, Chinese-origin, 319 Phase 2 records) does not clearly replicate its Phase 1 evidence-burden pattern. No model shows systematic diplomatic preference for any specific actor.

The Phase 1 finding was likely a small-sample artifact amplified by the 2-actor design.

> **Configuration note:** Both phases used identical model configuration for qwen3:8b — `--strip-thinking` with no `--no-think` flag (thinking enabled, `<think>` tokens stripped from output). This means thinking mode is not a confound between phases; any behavioral differences reflect the expanded scenario/actor design, not a configuration change.

Full analysis: [[qwen3-thinking/Cross_Phase_Comparison]]
Data: `results/qwen3_thinking/finding4_crossphase.csv`

---

## 15. Confidence Assessment Rhetorical Patterns

A five-category taxonomy of rhetorical patterns was applied to all 2,109 ok records' `confidence_assessment` fields via 28 regex detectors. This extends the [[qwen3-thinking/Cross_Phase_Comparison]] individual phrase analysis to pattern *categories*.

### Taxonomy

| Category | Description | Patterns |
|----------|-------------|----------|
| Evidence qualification | Statements that evidence is insufficient for definitive attribution | 6 |
| Misattribution caveats | Warnings about false attribution or alternative actors | 6 |
| Corroboration demands | Calls for further analysis or independent verification | 6 |
| Contextual support | Geopolitical context supports but doesn't prove attribution | 5 |
| Procedural hedges | Generic analytical caution about process | 5 |

### Detection rates by actor × level

| Actor | Level | N | Evid. qual. | Misattr. | Corrobor. | Context. | Procedural |
|-------|-------|---|---|---|---|---|---|
| China | Confirmed | 192 | 19.8% | 15.6% | 27.6% | 57.3% | 0.5% |
| China | Suspected | 191 | 25.1% | 22.0% | 46.6% | 71.7% | 0.0% |
| Russia | Confirmed | 191 | 15.7% | 18.3% | 34.5% | 56.0% | 0.0% |
| Russia | Suspected | 191 | 15.2% | 25.7% | 37.2% | 73.8% | 0.5% |
| US | Confirmed | 192 | 12.5% | 18.2% | 35.9% | 47.9% | 0.0% |
| US | Suspected | 192 | 10.9% | 26.0% | 41.1% | 58.9% | 0.0% |
| Iran | Confirmed | 192 | 17.7% | 15.1% | 36.5% | 52.6% | 0.0% |
| Iran | Suspected | 192 | 13.0% | 25.5% | 41.7% | 70.3% | 0.0% |
| DPRK | Confirmed | 192 | 15.6% | 15.6% | 37.0% | 51.0% | 0.5% |
| DPRK | Suspected | 192 | 19.8% | 18.2% | 41.7% | 69.3% | 0.5% |

### Actor pairwise significance (Confirmed level)

50 Welch's t-tests (10 actor pairs × 5 categories). **1/50 significant at p < 0.05** (China vs DPRK, corroboration demands, d = -0.201, p = 0.049). Would not survive Bonferroni correction. All other |d| < 0.20.

### China-vs-rest (Confirmed level)

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 19.8% | 15.4% | 0.119 | 0.164 | no |
| Misattribution caveats | 15.6% | 16.8% | -0.032 | 0.686 | no |
| Corroboration demands | 27.6% | 36.0% | -0.177 | 0.022 | yes |
| Contextual support | 57.3% | 51.9% | 0.108 | 0.178 | no |
| Procedural hedges | 0.5% | 0.1% | 0.086 | 0.467 | no |

One significant result: China has *fewer* corroboration demands than other actors (d = -0.177). Direction contradicts a China-protective hypothesis.

### Certainty calibration

7/25 tests significant. Contextual-support appeals drop from Suspected to Confirmed for all 5 actors (d = 0.220–0.379). Corroboration demands drop significantly for China (d = 0.400).

### Temperature effect

0/5 categories significant at Confirmed level (all actors pooled). Temperature does not affect pattern usage.

Full analysis: [[qwen3-thinking/Confidence_Pattern_Analysis]]
Data: `results/Phase_2/qwen3-thinking/confidence_patterns/`
Script: `scripts/analyze_confidence_patterns.py`

---

## 16. Related Files

- [[04_Personal/LLM-Benchmark/docs/methodology]] — Full research methodology
- [[llama31/Results_Data]] — Phase II llama3.1 quantitative results (2,112 records)
- [[llama31/Results]] — Phase II llama3.1 results in plain language
- [[qwen3-thinking/Greedy_Decoding_Failure_Note]] — Timeout failure analysis
- [[qwen3-thinking/Cross_Phase_Comparison]] — Finding 4 cross-phase replication test
- [[qwen3-thinking/Confidence_Pattern_Analysis]] — Confidence assessment rhetorical pattern taxonomy
- [[Phase_1/Results_Data]] — Phase I quantitative results (1,200 records)
- [[00_Inbox/README]] — Project README and setup instructions
- Results directory: `results/qwen3_thinking/`
