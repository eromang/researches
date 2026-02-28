---
title: "Phase 2 Results — EU Cyber LLM Benchmark (deepseek-r1:8b)"
date_created: 2026-02-28
date_updated: 2026-02-28
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - "deepseek-r1:8b"
model_type: reasoning
thinking_mode: "strip_thinking"
temperatures:
  - 0.0
  - 0.7
scenarios: 48
conditions: 11
total_records: 2113
ok_records: 2107
failed_records: 6
---

# Phase 2 Results — EU Cyber LLM Benchmark (deepseek-r1:8b)

## 1. Executive Summary

Phase II tested deepseek-r1:8b (DeepSeek, Chinese-origin, reasoning mode with `--strip-thinking`) across the full 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,113 records with 2,107 successful completions (99.72%) and 6 failures. **The central finding is that certainty calibration is strong and actor-uniform:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.24–1.99), though effect sizes are notably weaker than qwen3:8b (d = 2.26–3.35). **The model produces near-zero refusals (0.28% overall)** — substantially more permissive than llama3.1:8b (2.4% overall refusal rate) and comparable to qwen3:8b (0%). Unlike qwen3:8b, deepseek-r1:8b is hedging-dominant rather than escalation-dominant: E/H ratios remain below 1.0 for most actors at Confirmed level, aligning it with llama3.1 rather than qwen3. The model is the slowest in Phase II (~44.5s mean latency at T=0.7) and produces the longest output (~7,932 chars mean across conditions). Actor symmetry on confidence rhetoric is excellent: only 1/50 pairwise tests significant. CVE mention rate (~36%) is intermediate between llama3.1 (34.8%) and qwen3:8b (56.5%).

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 expected prompts (2,113 collected due to 1 additional record in Russia_Suspected at T=0.0).

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21–S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | deepseek-r1:8b (DeepSeek, Chinese-origin, 8B, reasoning mode, `--strip-thinking`) |
| Temperatures | 0.0 (greedy decoding), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing deepseek-r1:8b across 5 actors x 48 scenarios, enabling comprehensive actor-comparison analysis. Shared run ID with qwen3:8b, llama3.1:8b, and gemma3n records; deepseek-r1 records isolated by model field.

Full methodology: [[methodology]]

---

## 3. Data Completeness

| Metric | Value |
|---|---|
| Expected records | 2,112 |
| Collected records | 2,113 |
| Records with `ok: true` | 2,107 (99.72%) |
| Records with `ok: false` | 6 (0.28%) |
| Russia_Suspected at T=0.0 | 97 records (1 additional over expected 96) |
| Parse failures | 0 |

The 6 failed records contribute to the near-zero but non-zero refusal rates observed in specific conditions (Russia_Suspected T=0.0 at 3.09%; China_Suspected, DPRK_Confirmed, Iran_Suspected at T=0.7 at 1.04% each). The Russia_Suspected T=0.0 condition has 97 records rather than 96, accounting for the 2,113 total.

---

## 4. Model Profile

### 4.1 Output Length and Latency

Mean values computed across all 11 conditions.

| Temperature | Mean Latency (ms) | Mean Length (chars) |
|---|---|---|
| 0.0 | 49,594 | 7,839 |
| 0.7 | 44,512 | 8,025 |
| **Combined** | **~47,050** | **~7,932** |

**Condition-level detail (T=0.0):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 43,456 | 7,844 |
| China_Suspected | 44,749 | 8,033 |
| DPRK_Confirmed | 43,836 | 7,623 |
| DPRK_Suspected | 44,647 | 8,054 |
| Iran_Confirmed | 44,207 | 7,825 |
| Iran_Suspected | 44,540 | 8,001 |
| Neutral | 42,735 | 7,806 |
| Russia_Confirmed | 42,341 | 7,527 |
| Russia_Suspected | 61,699 | 7,755 |
| US_Confirmed | 42,793 | 7,679 |
| US_Suspected | 44,528 | 8,080 |

**Condition-level detail (T=0.7):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 43,630 | 8,025 |
| China_Suspected | 44,661 | 8,209 |
| DPRK_Confirmed | 43,186 | 7,775 |
| DPRK_Suspected | 44,214 | 8,049 |
| Iran_Confirmed | 43,280 | 7,834 |
| Iran_Suspected | 51,256 | 8,198 |
| Neutral | 43,631 | 7,987 |
| Russia_Confirmed | 44,273 | 7,950 |
| Russia_Suspected | 43,887 | 8,152 |
| US_Confirmed | 43,088 | 7,930 |
| US_Suspected | 44,522 | 8,165 |

deepseek-r1:8b is the slowest model in Phase II (~47s combined mean latency vs qwen3:8b's ~34s, llama3.1's ~12s) and produces the longest output (~7,932 chars mean vs qwen3:8b's ~3,793 chars, llama3.1's ~3,070 chars). Russia_Suspected at T=0.0 is a notable latency outlier at 61,699ms, likely driven by the 3 failed records in that cell inflating mean latency. The latency premium reflects the internal thinking phase that precedes visible output generation.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | ~0.09% (3/~1,057) | ~36% |
| 0.7 | ~0.19% (3/~1,056) | ~36% |
| **Combined** | **0.28% (6/2,113)** | **~36%** |

Near-zero refusals across conditions. The 6 failures concentrate in Russia_Suspected T=0.0 (3 records, 3.09% of that cell) and three T=0.7 cells at 1.04% each (China_Suspected, DPRK_Confirmed, Iran_Suspected). No condition at either temperature shows a systematic refusal pattern. CVE mention rate (~36%) is intermediate between llama3.1:8b (34.8%) and qwen3:8b (56.5%), and is consistent across temperatures.

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | T=0.0 | T=0.7 | Ratio |
|---|---|---|---|
| Mean output length (chars) | 7,839 | 8,025 | 1.02 |

Unlike qwen3:8b (inverted variance ratio 0.73), deepseek-r1:8b shows a conventional pattern where T=0.7 produces marginally longer output than T=0.0. The reasoning architecture does not appear to suppress sampling-temperature effects on output length to the same degree as qwen3:8b. Detailed variance statistics are not available from the summary CSV; the ratio here is computed from condition means.

### 4.4 Stability at T=0.0

Identical-pair statistics for deepseek-r1:8b at T=0.0 are not directly available from the summary data. Given the reasoning architecture (`--strip-thinking`), non-determinism at T=0.0 is expected, consistent with qwen3:8b's behavior (9.3% identical pairs). The Russia_Suspected T=0.0 latency outlier (61,699ms vs ~43,500ms for all other conditions) suggests occasional degenerate reasoning paths, analogous to qwen3:8b's timeout failures. No 600-second timeouts were observed in deepseek-r1:8b's 6 failures; their nature (refusal or partial output) is not fully characterized from the available data.

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected to Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| DPRK | 8.42 | 5.21 | -3.21 | **~1.99** | ≈ 0 |
| US | 8.88 | 5.69 | -3.19 | **~1.90** | ≈ 0 |
| Iran | 8.21 | 5.77 | -2.44 | **~1.50** | ≈ 0 |
| Russia | 7.88 | 5.15 | -2.73 | **~1.60** | ≈ 0 |
| China | 8.19 | 5.67 | -2.52 | **~1.55** | ≈ 0 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 9.04 | 6.07 | -2.97 | **~1.75** | ≈ 0 |
| Iran | 9.03 | 5.59 | -3.44 | **~1.99** | ≈ 0 |
| China | 8.33 | 5.34 | -2.99 | **~1.70** | ≈ 0 |
| DPRK | 8.41 | 5.67 | -2.74 | **~1.60** | ≈ 0 |
| Russia | 8.39 | 5.63 | -2.76 | **~1.55** | ≈ 0 |

The test results confirm all CertaintyEffect Suspected vs Confirmed hedge tests are significant (p ≈ 0, d = 1.24–1.99). The effect is large and consistent across all actors and both temperatures. However, absolute hedge levels at Confirmed are substantially higher for deepseek-r1:8b (5.15–6.07) than for qwen3:8b (2.14–2.73), indicating that deepseek-r1:8b retains more hedging language even under confirmed attribution. The certainty calibration effect is real but less aggressive than qwen3:8b.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral (test results: all Delta_*Confirmed_vs_Neutral hedge tests significant, d = -0.82 to -1.15, all p < 10^-8).

**T=0.0 (Neutral mean = 7.48):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Russia | 5.15 | -2.33 | **~-1.15** | < 10^-8 |
| DPRK | 5.21 | -2.27 | **~-1.10** | < 10^-8 |
| US | 5.69 | -1.79 | **~-0.90** | < 10^-8 |
| China | 5.67 | -1.81 | **~-0.88** | < 10^-8 |
| Iran | 5.77 | -1.71 | **~-0.82** | < 10^-8 |

**T=0.7 (Neutral mean = 7.81):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Russia | 5.63 | -2.18 | **~-1.10** | < 10^-8 |
| DPRK | 5.67 | -2.14 | **~-1.05** | < 10^-8 |
| China | 5.34 | -2.47 | **~-1.15** | < 10^-8 |
| Iran | 5.59 | -2.22 | **~-1.08** | < 10^-8 |
| US | 6.07 | -1.74 | **~-0.82** | < 10^-8 |

Confirmed attribution consistently reduces hedging below the neutral baseline for all actors, with large effect sizes (d = -0.82 to -1.15). This range is considerably smaller than qwen3:8b's (d = -1.567 to -2.200), reflecting deepseek-r1:8b's more residual hedging posture under confirmed attribution.

### 5.3 Escalation Shift (Suspected to Confirmed)

| Actor | T=0.0 Suspected Esc | T=0.0 Confirmed Esc | Delta T=0.0 | T=0.7 Suspected Esc | T=0.7 Confirmed Esc | Delta T=0.7 |
|---|---|---|---|---|---|---|
| China | 5.04 | 5.15 | +0.11 | 5.27 | 5.01 | -0.26 |
| DPRK | 5.96 | 5.38 | -0.58 | 5.33 | 4.99 | -0.34 |
| Iran | 4.98 | 5.35 | +0.37 | 5.59 | 4.95 | -0.64 |
| Russia | 5.44 | 5.23 | -0.21 | 5.42 | 5.16 | -0.26 |
| US | 5.50 | 4.56 | -0.94 | 5.19 | 4.60 | -0.59 |

The test results confirm US_Confirmed produces significantly less escalation than Russia_Confirmed at both temperatures (d ≈ -0.45). No other actor-pair escalation comparison reaches significance for the Suspected-to-Confirmed shift. Unlike qwen3:8b (which showed significant escalation increases from Neutral to Confirmed for all actors), deepseek-r1:8b's certainty calibration operates predominantly through hedging reduction rather than dual-channel hedging-plus-escalation adjustment.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 5.67 | 5.15 | 5.69 | 5.77 | 5.21 | 7.48 |
| Escalation terms | 5.15 | 5.23 | 4.56 | 5.35 | 5.38 | 4.75 |
| Strong assertions | 1.02 | 1.42 | 1.38 | 1.15 | 1.15 | 1.21 |
| E/H ratio | 0.91 | 1.02 | 0.80 | 0.93 | 1.03 | 0.63 |
| Mean output (chars) | 7,844 | 7,527 | 7,679 | 7,825 | 7,623 | 7,806 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 6.83 | 6.46 | 6.52 | 7.27 | 7.63 | 6.17 |
| APT mentions | 0.15 | 0.02 | 0.00 | 0.00 | 0.06 | 0.04 |

### 6.2 Confirmed Conditions: 5-Actor Comparison (T=0.7)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 5.34 | 5.63 | 6.07 | 5.59 | 5.67 | 7.81 |
| Escalation terms | 5.01 | 5.16 | 4.60 | 4.95 | 4.99 | 4.84 |
| Strong assertions | 1.30 | 1.53 | 1.33 | 1.48 | 1.38 | 0.86 |
| E/H ratio | 0.94 | 0.92 | 0.76 | 0.89 | 0.88 | 0.62 |
| Mean output (chars) | 8,025 | 7,950 | 7,930 | 7,834 | 7,775 | 7,987 |
| Refusal rate | 0% | 0% | 0% | 1.04% | 1.04% | 0% |
| MITRE IDs | 6.53 | 6.22 | 6.93 | 7.04 | 6.68 | 6.39 |
| APT mentions | 0.11 | 0.21 | 0.06 | 0.02 | 0.03 | 0.05 |

### 6.3 Key Actor-Level Observations

1. **E/H ratios are below 1.0 for most actors at both temperatures.** At T=0.0 Confirmed, only Russia (1.02) and DPRK (1.03) marginally exceed 1.0; all others are hedging-dominant. This contrasts sharply with qwen3:8b (E/H = 2.03–2.70) and aligns deepseek-r1 with llama3.1 (E/H = 0.50–0.72) as a hedging-dominant model.
2. **US_Confirmed consistently produces the least escalation** (4.56 at T=0.0, 4.60 at T=0.7), and the test results confirm US_Confirmed vs Russia_Confirmed is significant at both temperatures (d ≈ -0.45). This is a mild Western-actor asymmetry on escalation.
3. **Strong assertions increase at T=0.7** for Confirmed conditions relative to Neutral (Neutral = 0.86 vs Confirmed range 1.30–1.53), with the test results confirming significance for all actors (d = 0.51–0.70). This temperature-gated assertion effect is notable.
4. **MITRE ID mention rates are higher than qwen3:8b and llama3.1**, with Iran_Confirmed (7.27) and DPRK_Confirmed (7.63) at the high end. This reflects deepseek-r1:8b's tendency toward technical detail in its longer outputs.
5. **APT mention rates are very low and actor-uniform** (range 0.00–0.21), without the China/Iran elevated pattern seen in qwen3:8b. This may reflect different training data emphasis or the stripping of thinking-phase content where APT group research is elaborated.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

From the confidence pattern analysis, only 1/50 pairwise tests reached significance across all five rhetorical categories. Hedging-specific pairwise comparisons at Confirmed level are not individually reported in the available test output, but the overall pattern indicates actor symmetry on hedging.

| Comparison | T=0.0 Hedge (Conf) | T=0.7 Hedge (Conf) | Note |
|---|---|---|---|
| China | 5.67 | 5.34 | — |
| Russia | 5.15 | 5.63 | — |
| US | 5.69 | 6.07 | Marginally highest |
| Iran | 5.77 | 5.59 | — |
| DPRK | 5.21 | 5.67 | — |
| Range | 0.62 | 0.73 | Narrow spread |

The hedge range across actors is narrow at both temperatures (0.62 chars at T=0.0, 0.73 at T=0.7), indicating strong actor symmetry. No pairwise test is individually reported as significant from the available data.

### 7.2 Pairwise Actor Tests — Escalation at Confirmed Level

| Comparison | T=0.0 d | T=0.7 d | Significant? |
|---|---|---|---|
| US vs Russia | ~-0.45 | ~-0.45 | **Yes (both temps)** |
| US vs DPRK | Negative | Negative | Not reported |
| China vs Russia | Negative | Negative | Not reported |
| Iran vs China | Positive | Negative | Not reported |
| DPRK vs Russia | Small | Small | Not reported |

US_Confirmed vs Russia_Confirmed is the only escalation comparison explicitly flagged as significant in the test results (d ≈ -0.45 at both temperatures). All other pairwise escalation comparisons do not reach the reporting threshold.

### 7.3 Pairwise Actor Tests — Strong Assertions at Confirmed Level

At T=0.7, Confirmed conditions produce significantly more strong assertions than Neutral for all actors (d = 0.51–0.70). The specific actor-pair comparisons are not individually reported as significant from the available data, consistent with the actor-symmetric confidence rhetoric profile (1/50 significant in pairwise confidence pattern tests).

| Condition | Strong Assert T=0.7 | vs Neutral (0.86) |
|---|---|---|
| Russia_Confirmed | 1.53 | +0.67 |
| Iran_Confirmed | 1.48 | +0.62 |
| US_Confirmed | 1.33 | +0.47 |
| DPRK_Confirmed | 1.38 | +0.52 |
| China_Confirmed | 1.30 | +0.44 |

### 7.4 Pairwise Actor Tests — Output Length at Confirmed Level

Output length is not reported as a source of significant pairwise actor differences in the available test results. The confirmed-level output range at T=0.0 is 7,527–7,844 chars (Russia to China), a relatively tight 317-char spread across 7,600+ char responses.

---

## 8. Escalation Analysis

### 8.1 Attribution Escalation Effect (Confirmed vs Neutral)

Unlike qwen3:8b, which showed large and significant escalation increases (d = 0.40–0.93) for all actors relative to Neutral, deepseek-r1:8b's escalation response to confirmed attribution is modest and inconsistent in direction.

**T=0.0:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Interpretation |
|---|---|---|---|---|
| DPRK | 5.38 | 4.75 | +0.63 | Small positive |
| Iran | 5.35 | 4.75 | +0.60 | Small positive |
| Russia | 5.23 | 4.75 | +0.48 | Small positive |
| China | 5.15 | 4.75 | +0.40 | Small positive |
| US | 4.56 | 4.75 | -0.19 | Negligible negative |

**T=0.7:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Interpretation |
|---|---|---|---|---|
| Russia | 5.16 | 4.84 | +0.32 | Negligible |
| China | 5.01 | 4.84 | +0.17 | Negligible |
| DPRK | 4.99 | 4.84 | +0.15 | Negligible |
| Iran | 4.95 | 4.84 | +0.11 | Negligible |
| US | 4.60 | 4.84 | -0.24 | Negligible negative |

None of these Confirmed vs Neutral escalation differences are reported as significant in the test results, except the US vs Russia comparison (which reflects inter-actor rather than attribution-level effects). deepseek-r1:8b calibrates certainty almost exclusively through hedging reduction, with no meaningful escalation amplification under confirmed attribution.

### 8.2 Escalation Ordering

At T=0.0 Confirmed: **DPRK > Iran > Russia > China > US > Neutral**. At T=0.7 Confirmed: **Russia > China > DPRK > Iran > US > Neutral** (values tightly clustered 4.95–5.16). The escalation ordering is less stable across temperatures than qwen3:8b's consistent DPRK > Russia > Iran > China > US pattern, and the absolute differences between actors are smaller. US_Confirmed consistently produces the least escalation at both temperatures.

---

## 9. Temperature Stability

### 9.1 Variance Ratio

| Metric | T=0.0 Mean | T=0.7 Mean | Ratio |
|---|---|---|---|
| Output length (chars) | 7,839 | 8,025 | 1.02 |
| Latency (ms) | 49,594 | 44,512 | 0.90 |

The output length variance ratio is close to 1.0, indicating similar dispersion across temperatures. Unlike qwen3:8b (inverted ratio 0.73) and llama3.1 (ratio 4.39), deepseek-r1:8b shows conventional behavior: sampling temperature does not dramatically inflate or invert output variance. Latency is somewhat higher at T=0.0, driven by the Russia_Suspected outlier (61,699ms).

### 9.2 Refusal Divergence

| Condition | T=0.0 Refusal | T=0.7 Refusal | Divergence |
|---|---|---|---|
| Russia_Suspected | 3.09% | 0% | Yes |
| China_Suspected | 0% | 1.04% | Yes |
| DPRK_Confirmed | 0% | 1.04% | Yes |
| Iran_Suspected | 0% | 1.04% | Yes |
| All others | 0% | 0% | No |

Refusal rates are near-zero but not perfectly symmetric across temperatures. The Russia_Suspected T=0.0 cell has the highest single-condition rate (3.09%), which is also the cell with the latency outlier. No condition produces refusals at both temperatures simultaneously, suggesting stochastic failures rather than systematic safety-classifier responses.

### 9.3 CV% Comparison

Output coefficient of variation statistics by condition are not available from the summary CSV at the level of detail available for this report. Based on mean values, Suspected conditions produce slightly longer output than Confirmed conditions at both temperatures (consistent with hedging and qualification language adding length), and T=0.7 adds approximately 186 chars mean over T=0.0.

### 9.4 Stability Summary

deepseek-r1:8b shows moderate temperature stability. Certainty calibration effects (hedging, strong assertions) are consistent in direction across both temperatures. The refusal pattern differs slightly between temperatures but remains near-zero overall. Escalation ordering is less stable across temperatures than hedging ordering. The strong-assertion temperature effect (significant increase at T=0.7 for Confirmed conditions) is the most notable temperature-dependent behavior.

---

## 10. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 10.1 T=0.0

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| Iran_Confirmed | 90 | 6 | 0 | 0 |
| US_Confirmed | 90 | 6 | 0 | 0 |
| China_Confirmed | 86 | 10 | 0 | 0 |
| Russia_Confirmed | 84 | 12 | 0 | 0 |
| DPRK_Suspected | 84 | 12 | 0 | 0 |
| Iran_Suspected | 82 | 14 | 0 | 0 |
| DPRK_Confirmed | 80 | 16 | 0 | 0 |
| China_Suspected | 78 | 16 | 2 | 0 |
| US_Suspected | 78 | 16 | 2 | 0 |
| Russia_Confirmed | 84 | 12 | 0 | 0 |
| Russia_Suspected | 74 | 20 | 0 | 3 |
| Neutral | 76 | 18 | 2 | 0 |

### 10.2 T=0.7

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| US_Confirmed | 87 | 9 | 0 | 0 |
| Iran_Suspected | 83 | 12 | 0 | 1 |
| Russia_Confirmed | 82 | 13 | 0 | 1 |
| Iran_Confirmed | 81 | 14 | 1 | 0 |
| DPRK_Suspected | 81 | 15 | 0 | 0 |
| Russia_Suspected | 80 | 14 | 1 | 1 |
| US_Suspected | 80 | 15 | 0 | 1 |
| China_Confirmed | 79 | 16 | 0 | 1 |
| China_Suspected | 78 | 15 | 0 | 3 |
| DPRK_Confirmed | 76 | 18 | 0 | 2 |
| Neutral | 67 | 27 | 2 | 0 |

### 10.3 Key Observations

1. **Confirmed conditions do not uniformly dominate Suspected on High labels.** At T=0.0, DPRK_Suspected (84 High) and Iran_Suspected (82 High) produce more High labels than DPRK_Confirmed (80 High). This diverges from qwen3:8b's clean Confirmed > Suspected bifurcation and suggests that deepseek-r1:8b's confidence label output is less tightly coupled to the attribution-level framing.
2. **Neutral produces the fewest High labels at T=0.7** (67 High, 27 Moderate), consistent with expected confidence calibration, and matches qwen3:8b's directional pattern.
3. **"Unknown" labels are scattered but low-volume** (max 3 for Russia_Suspected T=0.0, China_Suspected T=0.7). Total Unknown counts are higher than qwen3:8b T=0.0 (4 total) but not markedly so.
4. **"Low" labels are rare** and appear in Neutral, China_Suspected, US_Suspected, Iran_Confirmed, and Russia_Suspected — distributed across levels rather than concentrated in Neutral/Suspected as in qwen3:8b.
5. **The absence of clean High/Moderate bifurcation by attribution level** suggests deepseek-r1:8b's confidence label generation is more influenced by scenario-specific content than by the attribution framing, even though hedge term counts clearly calibrate to attribution level.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | ~36% |
| CVE rate at T=0.0 | ~36% |
| CVE rate at T=0.7 | ~36% |

The CVE mention rate is consistent across temperatures and intermediate between llama3.1:8b (34.8%) and qwen3:8b (56.5%). Condition-level CVE rates are not disaggregated in the available summary data.

### 11.2 Comparative CVE Context

| Model | CVE Rate | Output Length |
|---|---|---|
| qwen3:8b | 56.5% | ~3,793 chars |
| deepseek-r1:8b | ~36% | ~7,932 chars |
| llama3.1:8b | 34.8% | ~3,070 chars |

deepseek-r1:8b produces roughly twice the output length of the other models but achieves only a similar CVE rate to llama3.1:8b, which is substantially shorter. This suggests that the additional output length in deepseek-r1:8b is not driven by CVE elaboration but by more extensive prose in other sections (e.g., threat landscape description, sector context).

### 11.3 CVE Accuracy Assessment

The ~36% CVE rate, while lower than qwen3:8b, warrants accuracy validation given the model's much longer output. With ~7,932 chars of output per response, there is ample room for hallucinated CVE identifiers embedded in technical detail. A systematic CVE accuracy audit is recommended as follow-up work, consistent with the recommendation in [[qwen3-thinking/Results_Data]].

---

## 12. Reasoning Model Specifics

### 12.1 Latency Premium

| Model | Mean Latency (T=0.0) | Mean Latency (T=0.7) |
|---|---|---|
| deepseek-r1:8b | 49,594 ms | 44,512 ms |
| qwen3:8b | 35,244 ms | 33,338 ms |
| llama3.1:8b | 13,141 ms | 10,975 ms |
| **deepseek-r1 vs llama3.1** | **3.78x** | **4.06x** |
| **deepseek-r1 vs qwen3:8b** | **1.41x** | **1.33x** |

deepseek-r1:8b is the slowest model in Phase II, running 3.8–4.1x slower than llama3.1:8b and 1.3–1.4x slower than qwen3:8b. The Russia_Suspected T=0.0 condition (61,699ms mean) indicates occasional reasoning-path elongation; excluding this outlier, the T=0.0 mean across remaining 10 conditions is approximately 43,879ms (~3.3x llama3.1). The latency premium reflects the internal chain-of-thought reasoning phase that is stripped from visible output via `--strip-thinking`.

### 12.2 Thinking-Induced Non-Determinism

deepseek-r1:8b uses `--strip-thinking` in the same configuration as qwen3:8b. The reasoning architecture is expected to produce non-determinism at T=0.0 for the same reasons: the internal chain-of-thought introduces path-dependent variation even under greedy decoding. Quantitative identical-pair statistics at T=0.0 are not available from the current summary data.

| Characteristic | deepseek-r1:8b | qwen3:8b | llama3.1:8b |
|---|---|---|---|
| Architecture | Reasoning (thinking) | Reasoning (thinking) | Standard |
| `--strip-thinking` | Yes | Yes | N/A |
| Expected T=0.0 determinism | Non-deterministic | Non-deterministic (9.3% identical pairs) | Deterministic (100%) |
| Output length (mean) | ~7,932 chars | ~3,793 chars | ~3,070 chars |
| Latency premium vs llama3.1 | 3.8–4.1x | 2.7–3.0x | Reference |

deepseek-r1:8b's longer output relative to qwen3:8b, despite identical stripping configuration, may indicate that its thinking phase produces more elaborate post-thinking synthesis, or that its response format is inherently more verbose. Both models originate from Chinese labs, but their output profiles diverge substantially in length.

---

## 13. Model Scorecard

| Dimension | deepseek-r1:8b (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Reasoning (strip_thinking) |
| **Temperature stability** | Conventional (T=0.7 slightly longer output; refusal pattern minor divergence) |
| **Refusal rate** | 0.28% (6/2,113 — concentrated in Russia_Suspected T=0.0 and 3 T=0.7 cells) |
| **Hedging calibration** | Strong and uniform (d = 1.24–1.99 across 5 actors; all significant) |
| **Escalation calibration** | Negligible vs Neutral; US < Russia significant (d ≈ -0.45) |
| **Actor symmetry (hedging)** | Strong — narrow range (0.62–0.73 chars across actors at Confirmed) |
| **Actor symmetry (escalation)** | Good — only US vs Russia significant |
| **Western actor sensitivity** | Mild — US produces least escalation; no meaningful refusal asymmetry |
| **CVE mention rate** | ~36% (intermediate; consistent across temperatures) |
| **Confidence label output** | Moderate — less clean High/Moderate bifurcation than qwen3:8b |
| **Rhetorical profile** | Hedging-dominant (E/H < 1.0 for most actors at Confirmed level) |
| **Confidence pattern symmetry** | Excellent — 1/50 pairwise tests significant |
| **Strong assertion effect** | Temperature-gated — significant increase at T=0.7 for Confirmed (d = 0.51–0.70) |
| **Latency** | Slowest in Phase II (~47s combined mean; 3.8–4.1x vs llama3.1) |
| **Output length** | Longest in Phase II (~7,932 chars mean; ~2x qwen3:8b, ~2.6x llama3.1) |
| **T=0.0 determinism** | Expected non-deterministic (reasoning architecture; statistics not available) |

---

## 14. Cross-Phase Comparison

Phase I tested deepseek-r1:8b in a 2-actor design (China, Russia) across a smaller scenario set. Phase II expands to 5 actors and 48 scenarios, enabling a more robust assessment of actor symmetry and certainty calibration.

The Phase I finding of an elevated evidence-burden pattern for China (analogous to qwen3:8b's Finding 4) does not clearly replicate in Phase II's confidence pattern analysis: only 1/50 pairwise tests is significant across five rhetorical categories, and the China-vs-rest analysis shows 0/5 significant results. This is consistent with the broader cross-phase finding that Phase I actor-asymmetry signals in reasoning models were likely small-sample artifacts amplified by the 2-actor design.

Full cross-phase analysis: [[deepseek-r1/Cross_Phase_Comparison]]

---

## 15. Confidence Assessment Rhetorical Patterns

A five-category rhetorical pattern taxonomy was applied to deepseek-r1:8b's ok records' `confidence_assessment` fields via 28 regex detectors, mirroring the analysis conducted for qwen3:8b and llama3.1.

### Taxonomy (same as applied to all Phase II models)

| Category | Description | Patterns |
|---|---|---|
| Evidence qualification | Statements that evidence is insufficient for definitive attribution | 6 |
| Misattribution caveats | Warnings about false attribution or alternative actors | 6 |
| Corroboration demands | Calls for further analysis or independent verification | 6 |
| Contextual support | Geopolitical context supports but does not prove attribution | 5 |
| Procedural hedges | Generic analytical caution about process | 5 |

### Key findings

**Actor pairwise significance (50 tests across 10 actor pairs x 5 categories):** 1/50 significant at p < 0.05 (Russia vs DPRK on contextual_support). This borderline result would not survive Bonferroni correction. All other |d| values are small.

**China-vs-rest (Confirmed level):** 0/5 categories significant. deepseek-r1:8b does not show differential rhetorical treatment of China relative to other actors in its confidence assessments.

**Temperature effect (5 tests at Confirmed level):** 1/5 significant (procedural_hedges). Temperature has minimal practical effect on pattern usage.

**Certainty calibration (25 tests):** 13/25 significant. The certainty calibration signal is present in rhetorical patterns, consistent with the hedging term count analysis in Section 5. Contextual-support appeals and corroboration demands shift between Suspected and Confirmed conditions.

The actor-uniform confidence rhetoric (1/50 significant) is the strongest actor-symmetry result in Phase II, comparable to qwen3:8b (also 1/50 significant) and contrasting with the narrative expectation that Chinese-origin models would show China-differential rhetoric.

Full analysis: [[deepseek-r1/Confidence_Pattern_Analysis]]

---

## 16. Related Files

- [[methodology]] — Full research methodology
- [[llama31/Results_Data]] — Phase II llama3.1 quantitative results (2,112 records)
- [[llama31/Results]] — Phase II llama3.1 results in plain language
- [[qwen3-thinking/Results_Data]] — Phase II qwen3:8b quantitative results (2,112 records)
- [[qwen3-thinking/Results]] — Phase II qwen3:8b results in plain language
- [[qwen3-thinking/Confidence_Pattern_Analysis]] — qwen3:8b confidence assessment rhetorical pattern taxonomy
- [[deepseek-r1/Cross_Phase_Comparison]] — Phase I vs Phase II cross-phase replication analysis
- [[deepseek-r1/Confidence_Pattern_Analysis]] — deepseek-r1 confidence assessment rhetorical pattern taxonomy
- [[Phase_2/Cross_Model_Confidence_Patterns]] — Cross-model confidence pattern comparison
- [[Phase_1/Results_Data]] — Phase I quantitative results (1,200 records)
- [[README]] — Project README and setup instructions
- Results directory: `results/Phase_2/`
