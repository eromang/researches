---
title: "Phase 2 Results — EU Cyber LLM Benchmark (hoangquan456/qwen3-nothink:8b)"
date_created: 2026-02-28
date_updated: 2026-02-28
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - "hoangquan456/qwen3-nothink:8b"
model_type: standard
thinking_mode: "none"
temperatures:
  - 0.0
  - 0.7
scenarios: 48
conditions: 11
total_records: 2112
ok_records: 2112
failed_records: 0
---

# Phase 2 Results — EU Cyber LLM Benchmark (hoangquan456/qwen3-nothink:8b)

## 1. Executive Summary

Phase II tested hoangquan456/qwen3-nothink:8b — a community fine-tune of Qwen3 8B that natively suppresses chain-of-thought without requiring `--no-think` or `--strip-thinking` flags — across the full 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,112 records with **100% completion rate** (zero failures). **The central finding is that certainty calibration is strong and actor-uniform:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.35–2.69 at T=0.0), though effect sizes are weaker than the thinking variant qwen3:8b (d = 2.26–3.35). **The model produces zero refusals** across all conditions and temperatures — identical to qwen3:8b's permissive safety posture. Unlike qwen3:8b's escalation-dominant profile (E/H = 2.03–2.70), qwen3-nothink shows a more balanced rhetorical profile with E/H ratios near 1.0 (0.85–1.13). Mean latency is ~21.8s and mean output is ~4,756 chars — substantially faster and slightly longer than qwen3:8b thinking (~34s, ~3,793 chars). Actor symmetry on confidence rhetoric is moderately differentiated: 8/50 pairwise tests significant, vs qwen3:8b's 1/50.

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 expected prompts (2,112 collected).

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21–S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | hoangquan456/qwen3-nothink:8b (Alibaba/Community, standard mode, no thinking flags) |
| Temperatures | 0.0 (greedy decoding), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing hoangquan456/qwen3-nothink:8b across 5 actors x 48 scenarios. This is a community fine-tune that natively suppresses chain-of-thought, enabling a direct comparison with the thinking variant qwen3:8b on the same Qwen3 architecture. Shared run ID with all other Phase 2 models; qwen3-nothink records isolated by model field.

Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]

---

## 3. Data Completeness

| Metric | Value |
|---|---|
| Expected records | 2,112 |
| Collected records | 2,112 |
| Records with `ok: true` | 2,112 (100.00%) |
| Records with `ok: false` | 0 (0.00%) |
| Parse failures | 0 |

Perfect completion rate. No refusals, no timeouts, no parse errors across all conditions and temperatures.

---

## 4. Model Profile

### 4.1 Output Length and Latency

Mean values computed across all 11 conditions.

| Temperature | Mean Latency (ms) | Mean Length (chars) |
|---|---|---|
| 0.0 | 20,697 | 4,663 |
| 0.7 | 22,806 | 4,849 |
| **Combined** | **~21,752** | **~4,756** |

**Condition-level detail (T=0.0):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 20,673 | 4,688 |
| China_Suspected | 21,133 | 4,792 |
| DPRK_Confirmed | 20,833 | 4,721 |
| DPRK_Suspected | 21,067 | 4,739 |
| Iran_Confirmed | 20,744 | 4,677 |
| Iran_Suspected | 20,334 | 4,597 |
| Neutral | 20,384 | 4,574 |
| Russia_Confirmed | 20,554 | 4,615 |
| Russia_Suspected | 20,858 | 4,694 |
| US_Confirmed | 20,500 | 4,577 |
| US_Suspected | 20,582 | 4,615 |

**Condition-level detail (T=0.7):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 22,862 | 4,878 |
| China_Suspected | 23,063 | 4,908 |
| DPRK_Confirmed | 23,099 | 4,876 |
| DPRK_Suspected | 23,243 | 4,904 |
| Iran_Confirmed | 22,726 | 4,804 |
| Iran_Suspected | 23,184 | 4,905 |
| Neutral | 22,146 | 4,704 |
| Russia_Confirmed | 22,622 | 4,870 |
| Russia_Suspected | 23,119 | 4,962 |
| US_Confirmed | 22,200 | 4,707 |
| US_Suspected | 22,605 | 4,825 |

qwen3-nothink:8b is the fastest non-standard model in Phase II (~21.8s combined mean latency vs qwen3:8b's ~34s, deepseek-r1's ~47s, llama3.1's ~12s). Output length (~4,756 chars) sits between qwen3:8b thinking (~3,793 chars) and deepseek-r1 (~7,932 chars). The elimination of the thinking phase removes 37% of the latency cost relative to the thinking variant.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0% (0/1,056) | TBD |
| 0.7 | 0% (0/1,056) | TBD |
| **Combined** | **0% (0/2,112)** | **TBD** |

Zero refusals across all conditions. Identical to qwen3:8b's permissive posture and consistent with the Alibaba-origin safety profile observed across both Qwen3 variants.

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | T=0.0 | T=0.7 | Ratio |
|---|---|---|---|
| Mean output length (chars) | 4,663 | 4,849 | 1.04 |

Conventional pattern: T=0.7 produces marginally longer output. Unlike qwen3:8b thinking (inverted ratio 0.73), the standard architecture shows normal temperature-length behaviour without thinking-induced variance.

### 4.4 Stability at T=0.0

As a standard (non-thinking) model, qwen3-nothink:8b is expected to produce deterministic output at T=0.0. Unlike the thinking variant (9.3% identical pairs), this model should show high or perfect reproducibility across replications at T=0.0.

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected to Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| DPRK | 7.90 | 4.04 | -3.86 | **2.69** | ≈ 0 |
| Russia | 7.65 | 4.10 | -3.55 | **2.28** | ≈ 0 |
| US | 7.75 | 4.42 | -3.33 | **2.12** | ≈ 0 |
| China | 7.69 | 4.44 | -3.25 | **2.01** | ≈ 0 |
| Iran | 7.90 | 4.77 | -3.13 | **1.84** | ≈ 0 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| China | 7.32 | 3.79 | -3.53 | **1.68** | ≈ 0 |
| Iran | 7.35 | 3.97 | -3.38 | **1.62** | ≈ 0 |
| Russia | 7.20 | 4.11 | -3.09 | **1.45** | ≈ 0 |
| US | 7.05 | 4.34 | -2.71 | **1.41** | ≈ 0 |
| DPRK | 6.88 | 4.10 | -2.78 | **1.35** | ≈ 0 |

All CertaintyEffect tests are significant (p ≈ 0, d = 1.35–2.69). Effect sizes at T=0.0 approach qwen3:8b thinking levels (2.26–3.35) but are weaker at T=0.7. Absolute confirmed hedging levels (3.79–4.77) are higher than qwen3:8b thinking (2.14–2.73) but lower than deepseek-r1 (5.15–6.07), placing qwen3-nothink in a middle position.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral.

**T=0.0 (Neutral mean = 5.92):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| DPRK | 4.04 | -1.88 | **-1.14** | < 10^-8 |
| Russia | 4.10 | -1.82 | **-1.01** | < 10^-8 |
| China | 4.44 | -1.48 | **-0.82** | < 10^-8 |
| US | 4.42 | -1.50 | **-0.84** | < 10^-8 |
| Iran | 4.77 | -1.15 | **-0.63** | < 10^-5 |

**T=0.7 (Neutral mean = 5.80):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| China | 3.79 | -2.01 | **-0.94** | < 10^-8 |
| Iran | 3.97 | -1.83 | **-0.82** | < 10^-8 |
| DPRK | 4.10 | -1.70 | **-0.81** | < 10^-8 |
| Russia | 4.11 | -1.69 | **-0.78** | < 10^-8 |
| US | 4.34 | -1.46 | **-0.70** | < 10^-6 |

Large effect sizes across all actors and temperatures.

### 5.3 Escalation Shift (Confirmed vs Neutral)

**T=0.0 (Neutral escalation = 3.63):**

| Actor | Confirmed Esc | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| DPRK | 4.58 | +0.95 | **0.69** | < 10^-5 |
| Iran | 4.46 | +0.83 | **0.65** | < 10^-5 |
| China | 4.54 | +0.91 | **0.62** | < 10^-5 |
| US | 4.44 | +0.81 | **0.62** | < 10^-5 |
| Russia | 4.35 | +0.72 | **0.48** | < 0.001 |

**T=0.7 (Neutral escalation = 3.60):**

| Actor | Confirmed Esc | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Russia | 4.28 | +0.68 | **0.37** | < 0.02 |
| DPRK | 4.25 | +0.65 | **0.36** | < 0.02 |
| Iran | 4.06 | +0.46 | **0.24** | ~0.09 |
| China | 4.00 | +0.40 | **0.22** | ~0.12 |
| US | 3.71 | +0.11 | **0.06** | ~0.68 |

Escalation increases under confirmed attribution are significant at T=0.0 (d = 0.48–0.69), weaker and mostly non-significant at T=0.7. This is an intermediate pattern: stronger than deepseek-r1 (negligible escalation effect) but weaker than qwen3:8b thinking (d = 0.40–0.93 consistently significant).

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 4.44 | 4.10 | 4.42 | 4.77 | 4.04 | 5.92 |
| Escalation terms | 4.54 | 4.35 | 4.44 | 4.46 | 4.58 | 3.63 |
| Strong assertions | 0.60 | 0.46 | 0.50 | 0.42 | 0.50 | 0.75 |
| E/H ratio | 1.02 | 1.06 | 1.00 | 0.94 | 1.13 | 0.61 |
| Mean output (chars) | 4,688 | 4,615 | 4,577 | 4,677 | 4,721 | 4,574 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 4.85 | 4.98 | 5.21 | 4.85 | 4.88 | 4.58 |
| APT mentions | 0.10 | 0.13 | 0.00 | 0.02 | 0.06 | 0.04 |

### 6.2 Confirmed Conditions: 5-Actor Comparison (T=0.7)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 3.79 | 4.11 | 4.34 | 3.97 | 4.10 | 5.80 |
| Escalation terms | 4.00 | 4.28 | 3.71 | 4.06 | 4.25 | 3.60 |
| Strong assertions | 0.56 | 0.48 | 0.55 | 0.65 | 0.64 | 0.64 |
| E/H ratio | 1.06 | 1.04 | 0.85 | 1.02 | 1.04 | 0.62 |
| Mean output (chars) | 4,878 | 4,870 | 4,707 | 4,804 | 4,876 | 4,704 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 4.21 | 4.51 | 4.46 | 4.30 | 4.57 | 4.16 |
| APT mentions | 0.10 | 0.04 | 0.00 | 0.04 | 0.09 | 0.00 |

### 6.3 Key Actor-Level Observations

1. **E/H ratios are near 1.0 for most actors.** At T=0.0 Confirmed, ratios range from 0.94 (Iran) to 1.13 (DPRK). This is a balanced profile — neither hedging-dominant like deepseek-r1 (E/H = 0.80–1.03) nor escalation-dominant like qwen3:8b thinking (E/H = 2.03–2.70).
2. **US_Confirmed produces the lowest escalation at T=0.7** (3.71 vs 4.06–4.28 for other actors; E/H = 0.85). This mild Western-actor asymmetry on escalation echoes the pattern observed in deepseek-r1.
3. **Strong assertions are lower than qwen3:8b thinking** (0.42–0.65 vs 0.88–1.38). Removing the thinking phase reduces the model's propensity for definitive claims.
4. **MITRE ID mention rates (~4.6 mean)** are lower than deepseek-r1 (~6.7) and qwen3:8b thinking (~4.3), suggesting the thinking phase does not significantly boost technical reference density.
5. **APT mention rates are very low** (0.00–0.13), consistent with other models. No actor-specific APT elevation pattern.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

The hedge range across actors is narrow at both temperatures.

| Temperature | Range (min–max) | Spread |
|---|---|---|
| T=0.0 | 4.04–4.77 | 0.73 |
| T=0.7 | 3.79–4.34 | 0.55 |

One significant pairwise comparison: Iran_Confirmed vs Russia_Confirmed at T=0.0 (d = 0.36, p = 0.012). Iran shows marginally more hedging than Russia under confirmed attribution.

### 7.2 Pairwise Actor Tests — Escalation at Confirmed Level

At T=0.7, US_Confirmed produces significantly less escalation than Russia_Confirmed (d ≈ -0.29, p = 0.044). No other escalation comparison reaches significance.

### 7.3 Pairwise Actor Tests — Strong Assertions at Confirmed Level

At T=0.0, Iran_Confirmed vs China_Confirmed is significant on strong assertions (d = -0.31, p = 0.033). China receives marginally more strong assertions than Iran.

### 7.4 Pairwise Actor Tests — Output Length at Confirmed Level

At T=0.7, US_Confirmed produces significantly shorter output than China_Confirmed (d = -0.32, p = 0.025) and Russia_Confirmed (d = -0.32, p = 0.025). This output-length asymmetry for US attribution echoes patterns seen in other models.

---

## 8. Escalation Analysis

### 8.1 Attribution Escalation Effect (Confirmed vs Neutral)

qwen3-nothink shows moderate escalation increases under confirmed attribution, with significant effects primarily at T=0.0.

**T=0.0:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | Significant? |
|---|---|---|---|---|---|
| DPRK | 4.58 | 3.63 | +0.95 | 0.69 | Yes |
| China | 4.54 | 3.63 | +0.91 | 0.62 | Yes |
| Iran | 4.46 | 3.63 | +0.83 | 0.65 | Yes |
| US | 4.44 | 3.63 | +0.81 | 0.62 | Yes |
| Russia | 4.35 | 3.63 | +0.72 | 0.48 | Yes |

**T=0.7:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | Significant? |
|---|---|---|---|---|---|
| Russia | 4.28 | 3.60 | +0.68 | 0.37 | Yes |
| DPRK | 4.25 | 3.60 | +0.65 | 0.36 | Yes |
| Iran | 4.06 | 3.60 | +0.46 | 0.24 | No |
| China | 4.00 | 3.60 | +0.40 | 0.22 | No |
| US | 3.71 | 3.60 | +0.11 | 0.06 | No |

### 8.2 Escalation Ordering

At T=0.0 Confirmed: **DPRK > China > Iran > US > Russia > Neutral**. At T=0.7 Confirmed: **Russia > DPRK > Iran > China > US > Neutral**. The ordering is moderately stable with DPRK and Russia at the top, US consistently at the bottom among attributed actors.

---

## 9. Temperature Stability

### 9.1 Variance Ratio

| Metric | T=0.0 Mean | T=0.7 Mean | Ratio |
|---|---|---|---|
| Output length (chars) | 4,663 | 4,849 | 1.04 |
| Latency (ms) | 20,697 | 22,806 | 1.10 |

Conventional temperature behaviour. T=0.7 produces ~4% longer output and ~10% higher latency — standard sampling-temperature effects without the anomalies seen in thinking models.

### 9.2 Refusal Divergence

No refusal divergence. Zero refusals at both temperatures across all conditions.

### 9.3 Stability Summary

qwen3-nothink:8b shows excellent temperature stability. Certainty calibration effects are consistent in direction at both temperatures (hedging reduction, escalation increase under Confirmed), though effect magnitudes are somewhat attenuated at T=0.7. The absence of a thinking phase eliminates the non-determinism that characterises qwen3:8b thinking at T=0.0.

---

## 10. Confidence Label Distribution

### 10.1 T=0.0

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 86 | 10 | 0 | 0 |
| China_Suspected | 82 | 14 | 0 | 0 |
| DPRK_Confirmed | 86 | 10 | 0 | 0 |
| DPRK_Suspected | 88 | 6 | 2 | 0 |
| Iran_Confirmed | 84 | 12 | 0 | 0 |
| Iran_Suspected | 84 | 12 | 0 | 0 |
| Neutral | 86 | 10 | 0 | 0 |
| Russia_Confirmed | 82 | 14 | 0 | 0 |
| Russia_Suspected | 90 | 6 | 0 | 0 |
| US_Confirmed | 88 | 8 | 0 | 0 |
| US_Suspected | 88 | 6 | 2 | 0 |

### 10.2 T=0.7

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 65 | 16 | 0 | 15 |
| China_Suspected | 71 | 16 | 0 | 9 |
| DPRK_Confirmed | 71 | 14 | 0 | 11 |
| DPRK_Suspected | 66 | 12 | 0 | 18 |
| Iran_Confirmed | 73 | 10 | 0 | 13 |
| Iran_Suspected | 72 | 12 | 0 | 12 |
| Neutral | 67 | 16 | 2 | 11 |
| Russia_Confirmed | 72 | 12 | 0 | 12 |
| Russia_Suspected | 76 | 8 | 0 | 12 |
| US_Confirmed | 65 | 22 | 0 | 9 |
| US_Suspected | 62 | 17 | 2 | 15 |

### 10.3 Key Observations

1. **T=0.0 produces clean confidence labels** with near-zero Unknown and Low labels. At T=0.0, High labels dominate (82–90 per condition) with small Moderate counts.
2. **T=0.7 introduces Unknown labels** (9–18 per condition), consistent with sampling-temperature degradation of structured output parsing. This is a stronger temperature effect on labels than qwen3:8b thinking (which showed 5 total Unknown at T=0.0).
3. **Confirmed conditions do not clearly dominate Suspected on High labels** at T=0.0. Russia_Suspected (90 High) exceeds Russia_Confirmed (82 High). This mirrors deepseek-r1's imperfect Confirmed > Suspected bifurcation.
4. **US_Confirmed at T=0.7 shows elevated Moderate** (22, vs 10–16 for other Confirmed conditions), suggesting the model applies slightly more epistemic caution to US attribution.

---

## 11. CVE Mention Analysis

CVE mention statistics for qwen3-nothink have not yet been disaggregated via the CVE analysis script. The [[CVE_Fixation_Analysis]] will be updated once this model's data is processed. Given qwen3:8b thinking's high CVE rate (56.5%), a similar or modified CVE pattern is expected from the same architecture without thinking.

---

## 12. Standard Model Specifics

### 12.1 Latency Comparison

| Model | Mean Latency (T=0.0) | Mean Latency (T=0.7) |
|---|---|---|
| qwen3-nothink:8b | 20,697 ms | 22,806 ms |
| qwen3:8b (thinking) | 35,244 ms | 33,338 ms |
| deepseek-r1:8b | 49,594 ms | 44,512 ms |
| llama3.1:8b | 13,141 ms | 10,975 ms |
| **qwen3-nothink vs llama3.1** | **1.57x** | **2.08x** |
| **qwen3-nothink vs qwen3 thinking** | **0.59x** | **0.68x** |

qwen3-nothink is 1.6–2.1x slower than llama3.1 but 32–41% faster than the thinking variant. The latency saving from eliminating the thinking phase is substantial: approximately 14.5s at T=0.0 and 10.5s at T=0.7.

### 12.2 Architecture Comparison

| Characteristic | qwen3-nothink:8b | qwen3:8b (thinking) | llama3.1:8b |
|---|---|---|---|
| Architecture | Standard (CoT suppressed) | Reasoning (thinking) | Standard |
| Thinking mode | Natively disabled | `--strip-thinking` | N/A |
| Expected T=0.0 determinism | Deterministic | Non-deterministic (9.3% identical) | Deterministic (100%) |
| Output length (mean) | ~4,756 chars | ~3,793 chars | ~3,070 chars |
| Latency vs llama3.1 | 1.6–2.1x | 2.7–3.0x | Reference |

qwen3-nothink produces 25% longer output than the thinking variant despite being 35% faster. This suggests the thinking phase in qwen3:8b compresses visible output — the internal reasoning replaces rather than supplements visible elaboration.

---

## 13. Model Scorecard

| Dimension | qwen3-nothink:8b (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Standard (community fine-tune, CoT suppressed) |
| **Temperature stability** | Excellent (zero refusals, conventional variance) |
| **Refusal rate** | 0% (0/2,112) |
| **Hedging calibration** | Strong (d = 1.35–2.69 across 5 actors; all significant) |
| **Escalation calibration** | Moderate (significant at T=0.0; attenuated at T=0.7) |
| **Actor symmetry (hedging)** | Good — narrow range (0.55–0.73 across actors at Confirmed) |
| **Actor symmetry (escalation)** | Good — only US vs Russia marginally significant |
| **Western actor sensitivity** | Mild — US produces least escalation at T=0.7 |
| **CVE mention rate** | TBD (pending CVE analysis) |
| **Confidence label output** | Good at T=0.0; degraded at T=0.7 (Unknown labels) |
| **Rhetorical profile** | Balanced (E/H ≈ 0.85–1.13 at Confirmed) |
| **Confidence pattern symmetry** | Moderate — 8/50 pairwise tests significant |
| **Latency** | 2nd fastest (~21.8s combined mean; 0.59x qwen3 thinking) |
| **Output length** | Intermediate (~4,756 chars mean; 1.25x qwen3 thinking) |
| **T=0.0 determinism** | Expected deterministic (standard architecture) |

---

## 14. Thinking vs No-Think Comparison

This model enables a unique same-architecture comparison with qwen3:8b (thinking mode). Unlike cross-phase comparisons (which mix phase design changes with model effects), this is a direct comparison of the effect of chain-of-thought reasoning within the Qwen3 8B architecture.

Key differences are analysed in [[qwen3-nothink/Thinking_vs_NoThink_Comparison]].

---

## 15. Confidence Assessment Rhetorical Patterns

A five-category rhetorical pattern taxonomy was applied to qwen3-nothink's 2,112 ok records' `confidence_assessment` fields via 28 regex detectors.

### Key findings

**Actor pairwise significance (50 tests):** 8/50 significant at p < 0.05. This is moderately differentiated — more than qwen3:8b thinking (1/50) or deepseek-r1 (1/50), but less than gemma3n (13/50).

**China-vs-rest (Confirmed level):** 0/5 categories significant. No China-protective framing detected.

**Temperature effect:** 1/5 significant (misattribution_caveats).

**Certainty calibration:** 6/25 significant. Evidence-qualification hedges drop from Suspected to Confirmed for China, Russia, US, and Iran.

The moderately differentiated actor pattern (8/50) is the highest among the three Qwen/Alibaba-adjacent models in Phase II. Removing chain-of-thought may reduce the uniformity that the thinking architecture imposes on confidence rhetoric.

Full analysis: [[qwen3-nothink/Confidence_Pattern_Analysis]]

---

## 16. Related Files

- [[04_Personal/LLM-Benchmark/docs/methodology]] — Full research methodology
- [[qwen3-thinking/Results_Data]] — Phase II qwen3:8b thinking quantitative results (2,112 records)
- [[qwen3-thinking/Results]] — Phase II qwen3:8b thinking results in plain language
- [[qwen3-nothink/Thinking_vs_NoThink_Comparison]] — Thinking vs no-think architecture comparison
- [[qwen3-nothink/Confidence_Pattern_Analysis]] — qwen3-nothink confidence pattern analysis
- [[llama31/Results_Data]] — Phase II llama3.1 quantitative results (2,112 records)
- [[gemma3n/Results_Data]] — Gemma3n quantitative results (2,112 records)
- [[deepseek-r1/Results_Data]] — deepseek-r1 quantitative results (2,113 records)
- [[Phase_2/Cross_Model_Confidence_Patterns]] — Cross-model confidence pattern comparison
- [[Phase_2/CVE_Fixation_Analysis]] — CVE fixation analysis
- [[00_Inbox/README]] — Project README and setup instructions
- Results directory: `results/Phase_2/qwen3-nothink/`
