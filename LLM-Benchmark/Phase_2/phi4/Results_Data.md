---
title: "Phase 2 Results — EU Cyber LLM Benchmark (phi4:latest)"
date_created: 2026-03-02
date_updated: 2026-03-02
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - "phi4:latest"
model_type: instruct
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

# Phase 2 Results — EU Cyber LLM Benchmark (phi4:latest)

## 1. Executive Summary

Phase II tested phi4:latest (Microsoft, US-origin, 14B instruct model without thinking mode) across the full 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,112 records with 2,112 successful completions (100%) and effectively 0 failures (1 partial refusal at T=0.7 Iran_Suspected). **The central finding is that certainty calibration is strong and largely actor-symmetric:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.07–2.53), with effect sizes comparable to deepseek-r1:8b (1.24–1.99) and overlapping with qwen3:8b's upper range (2.26–3.35). **The model produces near-zero refusals (~0%)** — the lowest rate in Phase II. Unlike qwen3:8b, phi4 is hedging-dominant rather than escalation-dominant: E/H ratios remain near or below 1.0 for most actors at Confirmed level, aligning it with deepseek-r1 and llama3.1. phi4 is notable for its very low CVE mention rate (2.8%) and CVE fixation on CVE-2021-44228 (60.3% of CVE-containing records). Despite having 14B parameters — nearly twice the other models — output length (~3,894 chars mean) is comparable to the 8B models.

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 expected prompts (2,112 collected).

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21–S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | phi4:latest (Microsoft, US-origin, 14B, instruct, no thinking mode) |
| Temperatures | 0.0 (greedy decoding), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing phi4:latest across 5 actors x 48 scenarios. Shared run ID with qwen3:8b, llama3.1:8b, gemma3n, deepseek-r1:8b, and qwen3-nothink records; phi4 records isolated by model field. phi4 did not run in Phase 1 — no cross-phase comparison is available.

Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]

---

## 3. Data Completeness

| Metric | Value |
|---|---|
| Expected records | 2,112 |
| Collected records | 2,112 |
| Records with `ok: true` | 2,112 (100%) |
| Records with `ok: false` | 0 (0%) |
| Parse failures | 0 |

The single partial refusal (Iran_Suspected at T=0.7, refusal_rate 0.0104) is counted within the ok records and reflected in the condition-level refusal rate. All 2,112 records are valid for analysis.

---

## 4. Model Profile

### 4.1 Output Length and Latency

Mean values computed across all 11 conditions.

| Temperature | Mean Latency (ms) | Mean Length (chars) |
|---|---|---|
| 0.0 | 32,030 | 3,840 |
| 0.7 | 28,657 | 3,948 |
| **Combined** | **~30,345** | **~3,894** |

**Condition-level detail (T=0.0):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 32,796 | 3,906 |
| China_Suspected | 31,789 | 3,810 |
| DPRK_Confirmed | 32,006 | 3,858 |
| DPRK_Suspected | 32,276 | 3,888 |
| Iran_Confirmed | 31,717 | 3,796 |
| Iran_Suspected | 31,653 | 3,834 |
| Neutral | 32,250 | 3,846 |
| Russia_Confirmed | 32,513 | 3,912 |
| Russia_Suspected | 32,119 | 3,858 |
| US_Confirmed | 31,145 | 3,713 |
| US_Suspected | 32,072 | 3,818 |

**Condition-level detail (T=0.7):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 28,696 | 3,947 |
| China_Suspected | 28,999 | 3,980 |
| DPRK_Confirmed | 28,333 | 3,922 |
| DPRK_Suspected | 28,913 | 3,976 |
| Iran_Confirmed | 28,590 | 3,927 |
| Iran_Suspected | 28,703 | 3,944 |
| Neutral | 28,869 | 3,977 |
| Russia_Confirmed | 28,990 | 3,995 |
| Russia_Suspected | 28,894 | 3,983 |
| US_Confirmed | 28,029 | 3,889 |
| US_Suspected | 28,220 | 3,887 |

phi4:latest is moderate in speed (~30s combined mean latency) — faster than deepseek-r1:8b (~47s) and qwen3:8b (~34s), slower than llama3.1:8b (~12s). Output length (~3,894 chars mean) is comparable to qwen3:8b (~3,793) and llama3.1 (~3,070) despite having nearly twice the parameters. US_Confirmed consistently produces the shortest output at both temperatures. T=0.7 is faster than T=0.0, likely due to sampling-based early stopping.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0% (0/1,056) | 2.1% |
| 0.7 | ~0.1% (1/1,056) | 3.4% |
| **Combined** | **~0% (1/2,112)** | **2.8%** |

Near-zero refusals across all conditions. The single refusal occurs at Iran_Suspected T=0.7 (1/96 = 1.04%). No other condition at either temperature shows any refusal. CVE mention rate (2.8%) is the second-lowest in Phase II after gemma3n (1.9%), and is consistent across conditions.

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | T=0.0 | T=0.7 | Ratio |
|---|---|---|---|
| Mean output length (chars) | 3,840 | 3,948 | 1.03 |
| Mean latency (ms) | 32,030 | 28,657 | 0.89 |

Output length ratio is close to 1.0 (T=0.7 slightly longer). Latency is lower at T=0.7, consistent with sampling allowing earlier token selection. No dramatic variance inflation at T=0.7.

### 4.4 Stability at T=0.0

As a standard instruct model without thinking mode, phi4:latest is expected to produce deterministic output at T=0.0. Identical-pair statistics are not yet computed but should show near-100% identical pairs, in contrast to reasoning models (deepseek-r1 and qwen3 with thinking, which show non-determinism at T=0.0 due to the thinking phase).

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected to Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 7.63 | 4.27 | -3.35 | **2.53** | ≈ 0 |
| DPRK | 7.35 | 4.15 | -3.21 | **2.34** | ≈ 0 |
| China | 7.23 | 4.10 | -3.13 | **2.13** | ≈ 0 |
| Russia | 7.15 | 4.52 | -2.63 | **1.82** | ≈ 0 |
| Iran | 7.38 | 4.58 | -2.79 | **1.75** | ≈ 0 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Russia | 7.50 | 4.32 | -3.18 | **1.60** | ≈ 0 |
| US | 7.72 | 4.55 | -3.17 | **1.55** | ≈ 0 |
| DPRK | 7.36 | 4.54 | -2.82 | **1.48** | ≈ 0 |
| China | 7.08 | 4.57 | -2.51 | **1.20** | ≈ 0 |
| Iran | 6.91 | 4.57 | -2.33 | **1.07** | ≈ 0 |

All CertaintyEffect tests are significant (p ≈ 0, d = 1.07–2.53). The effect is large and consistent across all actors and both temperatures. Absolute hedge levels at Confirmed (4.10–4.58) fall between qwen3:8b's very low residual (2.14–2.73) and deepseek-r1:8b's higher residual (5.15–6.07).

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral.

**T=0.0 (Neutral mean = 5.96):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| China | 4.10 | -1.85 | **-1.20** | ≈ 0 |
| DPRK | 4.15 | -1.81 | **-1.23** | ≈ 0 |
| US | 4.27 | -1.69 | **-1.11** | < 10^-8 |
| Russia | 4.52 | -1.44 | **-0.92** | < 10^-8 |
| Iran | 4.58 | -1.37 | **-0.87** | < 10^-8 |

**T=0.7 (Neutral mean = 6.42):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Russia | 4.32 | -2.09 | **-0.98** | < 10^-8 |
| DPRK | 4.54 | -1.87 | **-0.93** | < 10^-8 |
| US | 4.55 | -1.86 | **-0.85** | < 10^-8 |
| China | 4.57 | -1.84 | **-0.84** | < 10^-8 |
| Iran | 4.57 | -1.84 | **-0.81** | < 10^-8 |

Confirmed attribution consistently reduces hedging below the neutral baseline for all actors, with large effect sizes (d = -0.81 to -1.23).

### 5.3 Escalation Shift (Suspected to Confirmed)

| Actor | T=0.0 Susp. Esc | T=0.0 Conf. Esc | Delta T=0.0 | T=0.7 Susp. Esc | T=0.7 Conf. Esc | Delta T=0.7 |
|---|---|---|---|---|---|---|
| China | 3.98 | 3.98 | 0.00 | 3.75 | 3.58 | -0.17 |
| DPRK | 3.88 | 4.40 | +0.52 | 3.59 | 3.73 | +0.14 |
| Iran | 4.04 | 4.17 | +0.13 | 3.49 | 3.41 | -0.08 |
| Russia | 3.83 | 3.96 | +0.13 | 3.64 | 3.69 | +0.05 |
| US | 3.81 | 3.75 | -0.06 | 3.36 | 3.28 | -0.08 |

The only significant escalation effect is DPRK_Confirmed vs Neutral at T=0.0 (d = 0.64, p < 10^-5). phi4's certainty calibration operates predominantly through hedging reduction, not escalation amplification — consistent with deepseek-r1:8b and llama3.1.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 4.10 | 4.52 | 4.27 | 4.58 | 4.15 | 5.96 |
| Escalation terms | 3.98 | 3.96 | 3.75 | 4.17 | 4.40 | 3.63 |
| Strong assertions | 1.04 | 1.19 | 0.79 | 0.96 | 0.92 | 0.52 |
| E/H ratio | 0.97 | 0.88 | 0.88 | 0.91 | 1.06 | 0.61 |
| Mean output (chars) | 3,906 | 3,912 | 3,713 | 3,796 | 3,858 | 3,846 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 3.33 | 3.19 | 2.92 | 2.85 | 3.44 | 2.98 |
| APT mentions | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

### 6.2 Confirmed Conditions: 5-Actor Comparison (T=0.7)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 4.57 | 4.32 | 4.55 | 4.57 | 4.54 | 6.42 |
| Escalation terms | 3.58 | 3.69 | 3.28 | 3.41 | 3.73 | 3.45 |
| Strong assertions | 1.07 | 1.21 | 0.96 | 1.24 | 1.15 | 0.52 |
| E/H ratio | 0.78 | 0.85 | 0.72 | 0.75 | 0.82 | 0.54 |
| Mean output (chars) | 3,947 | 3,995 | 3,889 | 3,927 | 3,922 | 3,977 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 2.67 | 3.02 | 2.56 | 2.51 | 2.78 | 2.59 |
| APT mentions | 0.00 | 0.02 | 0.00 | 0.00 | 0.00 | 0.00 |

### 6.3 Key Actor-Level Observations

1. **E/H ratios are below 1.0 for most actors at both temperatures.** At T=0.0 Confirmed, only DPRK (1.06) marginally exceeds 1.0; all others are hedging-dominant. This aligns phi4 with deepseek-r1 and llama3.1 rather than qwen3:8b.
2. **US_Confirmed consistently produces the shortest output** (3,713 at T=0.0, 3,889 at T=0.7) — significant vs China and Russia at T=0.0 (d ≈ -0.63).
3. **Strong assertions increase under Confirmed attribution** relative to Neutral (Neutral = 0.52 vs Confirmed range 0.79–1.19 at T=0.0), with all actor-Neutral comparisons significant (d = 0.53–0.86).
4. **APT mentions are essentially zero** across all conditions at both temperatures. phi4 does not generate APT group names in its responses, unlike deepseek-r1 (which mentioned APT groups at low rates for China) or qwen3.
5. **MITRE ID mention rates are lower than deepseek-r1** but comparable to llama3.1, with DPRK_Confirmed (3.44) and China_Confirmed (3.33) at the high end.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

| Actor | T=0.0 Hedge (Conf) | T=0.7 Hedge (Conf) | Note |
|---|---|---|---|
| China | 4.10 | 4.57 | Lowest at T=0.0 |
| DPRK | 4.15 | 4.54 | — |
| US | 4.27 | 4.55 | — |
| Russia | 4.52 | 4.32 | Lowest at T=0.7 |
| Iran | 4.58 | 4.57 | — |
| Range | 0.48 | 0.25 | Narrow spread |

The hedge range across actors is very narrow at both temperatures (0.48 at T=0.0, 0.25 at T=0.7), indicating strong actor symmetry on hedging.

### 7.2 Pairwise Actor Tests — Output Length at Confirmed Level

The only significant actor-pair output length comparisons are at T=0.0:

| Comparison | d | Significant? |
|---|---|---|
| US vs China | -0.63 | **Yes** |
| US vs Russia | -0.62 | **Yes** |

US_Confirmed produces shorter responses than China_Confirmed and Russia_Confirmed at T=0.0. No other pairwise comparisons reach significance.

---

## 8. Escalation Analysis

### 8.1 Attribution Escalation Effect (Confirmed vs Neutral)

**T=0.0:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Interpretation |
|---|---|---|---|---|
| DPRK | 4.40 | 3.63 | +0.77 | Significant (d = 0.64) |
| Iran | 4.17 | 3.63 | +0.54 | Small positive |
| China | 3.98 | 3.63 | +0.35 | Negligible |
| Russia | 3.96 | 3.63 | +0.33 | Negligible |
| US | 3.75 | 3.63 | +0.12 | Negligible |

**T=0.7:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Interpretation |
|---|---|---|---|---|
| DPRK | 3.73 | 3.45 | +0.28 | Negligible |
| Russia | 3.69 | 3.45 | +0.24 | Negligible |
| China | 3.58 | 3.45 | +0.13 | Negligible |
| Iran | 3.41 | 3.45 | -0.04 | Negligible |
| US | 3.28 | 3.45 | -0.17 | Negligible |

Only DPRK_Confirmed vs Neutral at T=0.0 reaches significance. phi4 calibrates certainty almost exclusively through hedging reduction, with minimal escalation amplification under confirmed attribution.

### 8.2 Escalation Ordering

At T=0.0 Confirmed: **DPRK > Iran > China ≈ Russia > US > Neutral**. At T=0.7 Confirmed: **DPRK > Russia > China > Neutral > Iran > US**. US_Confirmed consistently produces the least escalation at both temperatures.

---

## 9. Temperature Stability

### 9.1 Variance Ratio

| Metric | T=0.0 Mean | T=0.7 Mean | Ratio |
|---|---|---|---|
| Output length (chars) | 3,840 | 3,948 | 1.03 |
| Latency (ms) | 32,030 | 28,657 | 0.89 |

Output length is nearly identical across temperatures. Latency is lower at T=0.7.

### 9.2 Refusal Divergence

| Condition | T=0.0 Refusal | T=0.7 Refusal | Divergence |
|---|---|---|---|
| Iran_Suspected | 0% | 1.04% | Yes (1 record) |
| All others | 0% | 0% | No |

A single refusal at Iran_Suspected T=0.7 is the only divergence. No systematic pattern.

### 9.3 Confidence Label Divergence

The most notable temperature effect is on confidence labels. At T=0.0, phi4 produces almost exclusively "High" labels (92–96 out of 96 per condition). At T=0.7, "Unknown" labels appear in significant numbers (up to 14 for Iran_Suspected), and "Moderate" labels increase (up to 27 for Neutral). This reflects the instruct architecture's sensitivity to sampling variation without a stabilizing reasoning phase.

### 9.4 Stability Summary

phi4 shows good temperature stability on quantitative metrics (hedging, escalation, output length) but notable instability on confidence labels at T=0.7. The certainty calibration effects are directionally consistent across temperatures, with T=0.0 showing larger effect sizes.

---

## 10. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 10.1 T=0.0

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 96 | 0 | 0 | 0 |
| China_Suspected | 96 | 0 | 0 | 0 |
| DPRK_Confirmed | 96 | 0 | 0 | 0 |
| DPRK_Suspected | 96 | 0 | 0 | 0 |
| Iran_Confirmed | 96 | 0 | 0 | 0 |
| Iran_Suspected | 94 | 2 | 0 | 0 |
| Neutral | 92 | 4 | 0 | 0 |
| Russia_Confirmed | 96 | 0 | 0 | 0 |
| Russia_Suspected | 96 | 0 | 0 | 0 |
| US_Confirmed | 96 | 0 | 0 | 0 |
| US_Suspected | 92 | 4 | 0 | 0 |

### 10.2 T=0.7

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 86 | 0 | 0 | 10 |
| China_Suspected | 86 | 0 | 0 | 10 |
| DPRK_Confirmed | 92 | 0 | 0 | 4 |
| DPRK_Suspected | 82 | 6 | 0 | 8 |
| Iran_Confirmed | 82 | 1 | 0 | 13 |
| Iran_Suspected | 79 | 3 | 0 | 14 |
| Neutral | 58 | 27 | 1 | 10 |
| Russia_Confirmed | 91 | 0 | 0 | 5 |
| Russia_Suspected | 84 | 5 | 0 | 7 |
| US_Confirmed | 83 | 2 | 0 | 11 |
| US_Suspected | 77 | 12 | 0 | 7 |

### 10.3 Key Observations

1. **T=0.0 produces near-uniform "High" labels.** Only Iran_Suspected (94/96), US_Suspected (92/96), and Neutral (92/96) deviate. This is the most uniform T=0.0 label distribution of any Phase II model.
2. **T=0.7 introduces substantial "Unknown" labels** across all conditions (4–14 per condition), plus scattered "Moderate" labels. Neutral shows the widest distribution (58 High, 27 Moderate, 1 Low, 10 Unknown).
3. **The T=0.0 vs T=0.7 divergence on labels is the largest in Phase II.** deepseek-r1:8b showed minimal temperature-driven label shifts; phi4's instruct architecture does not have a reasoning phase to stabilize label generation at T=0.7.
4. **Suspected vs Confirmed bifurcation is weak at T=0.0** because nearly everything is "High." At T=0.7, the expected pattern emerges more clearly: Neutral and Suspected conditions show more Moderate and Unknown labels.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | 2.8% |
| CVE rate at T=0.0 | 2.1% |
| CVE rate at T=0.7 | 3.4% |
| Records with CVEs | 58 |
| Unique CVEs cited | 18 |
| Mean CVE per record (when present) | 1.017 |

### 11.2 Top CVEs

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-44228 | 35 | 60.3% | Real |
| 2 | CVE-2020-10135 | 4 | 6.9% | Unverified |
| 3 | CVE-2020-1472 | 3 | 5.2% | Unverified |
| 4 | CVE-2020-1234 | 2 | 3.4% | Unverified |
| 5 | CVE-2020-15999 | 2 | 3.4% | Unverified |

### 11.3 CVE Fixation

phi4 meets the fixation threshold: CVE-2021-44228 (Log4Shell) appears in 60.3% of CVE-containing records. Shannon diversity index H = 2.556 (normalised 0.613), indicating moderate concentration. Unlike deepseek-r1:8b (which fixates on CVE-2021-4034, PwnKit), phi4 fixates on Log4Shell — the same CVE that dominates llama3.1's citations (48.6%).

### 11.4 Comparative CVE Context

| Model | CVE Rate | Fixation? | Top CVE | Top % |
|---|---|---|---|---|
| qwen3:8b | 56.5% | No | CVE-2023-1234 | 24.0% |
| deepseek-r1:8b | 36.4% | Yes | CVE-2021-4034 | 73.0% |
| llama3.1:8b | 34.8% | Yes | CVE-2021-44228 | 48.6% |
| qwen3-nothink | 25.3% | No | CVE-2023-22892 | 22.7% |
| phi4:latest | 2.8% | Yes | CVE-2021-44228 | 60.3% |
| gemma3n | 1.9% | No | CVE-2017-0144 | 25.0% |

phi4's CVE profile is distinctive: very low rate but high fixation. When it does cite a CVE, it overwhelmingly cites Log4Shell. 0 hallucinated CVEs were detected; 2 real (CVE-2021-44228, CVE-2021-40444) and 16 unverified.

---

## 12. Instruct Model Specifics

### 12.1 Latency Context

| Model | Architecture | Parameters | Mean Latency (T=0.0) | Mean Latency (T=0.7) |
|---|---|---|---|---|
| phi4:latest | Instruct | 14B | 32,030 ms | 28,657 ms |
| llama3.1:8b | Instruct | 8B | 13,141 ms | 10,975 ms |
| qwen3:8b | Reasoning | 8B | 35,244 ms | 33,338 ms |
| deepseek-r1:8b | Reasoning | 8B | 49,594 ms | 44,512 ms |
| gemma3n | Instruct | 8B | ~15,000 ms | ~14,000 ms |
| qwen3-nothink | Instruct | 8B | ~18,000 ms | ~16,000 ms |

phi4 at 14B runs 2.4x slower than llama3.1 at 8B but faster than both reasoning models. The latency premium reflects the larger parameter count rather than an internal reasoning phase.

### 12.2 Determinism at T=0.0

As a standard instruct model, phi4:latest should produce deterministic output at T=0.0. This contrasts with deepseek-r1:8b and qwen3:8b (thinking mode), where the internal chain-of-thought introduces non-determinism even at T=0.0.

| Characteristic | phi4:latest | llama3.1:8b | qwen3:8b | deepseek-r1:8b |
|---|---|---|---|---|
| Architecture | Instruct | Instruct | Reasoning | Reasoning |
| Parameters | 14B | 8B | 8B | 8B |
| `--strip-thinking` | N/A | N/A | Yes | Yes |
| Expected T=0.0 determinism | Deterministic | Deterministic (100%) | Non-deterministic (9.3%) | Non-deterministic |
| Output length (mean) | ~3,894 chars | ~3,070 chars | ~3,793 chars | ~7,932 chars |

---

## 13. Model Scorecard

| Dimension | phi4:latest (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Instruct (no thinking mode) |
| **Parameters** | 14B (largest in Phase II) |
| **Origin** | Microsoft (US) |
| **Temperature stability** | Good on metrics; label instability at T=0.7 |
| **Refusal rate** | ~0% (1/2,112) |
| **Hedging calibration** | Strong and uniform (d = 1.07–2.53 across 5 actors; all significant) |
| **Escalation calibration** | Minimal vs Neutral; DPRK only significant (d = 0.64) |
| **Actor symmetry (hedging)** | Strong — narrow range (0.25–0.48 across actors at Confirmed) |
| **Actor symmetry (rhetoric)** | Moderate — 10/50 pairwise tests significant |
| **Western actor sensitivity** | None — US shows slightly shorter output but no refusal or escalation asymmetry |
| **CVE mention rate** | 2.8% (very low; second-lowest after gemma3n) |
| **CVE fixation** | Yes — CVE-2021-44228 at 60.3% of CVE records |
| **Confidence label output** | Uniform "High" at T=0.0; diversified at T=0.7 |
| **Rhetorical profile** | Hedging-dominant (E/H = 0.72–1.06) |
| **Confidence pattern symmetry** | Moderate — 10/50 pairwise tests significant |
| **Latency** | Moderate (~30s combined mean; 2.4x vs llama3.1) |
| **Output length** | Moderate (~3,894 chars mean; comparable to 8B models) |
| **T=0.0 determinism** | Expected deterministic (instruct architecture) |

---

## 14. Confidence Assessment Rhetorical Patterns

A five-category rhetorical pattern taxonomy was applied to phi4's 2,112 ok records' `confidence_assessment` fields via 28 regex detectors, mirroring the analysis conducted for all other Phase II models.

### Taxonomy

| Category | Description | Patterns |
|---|---|---|
| Evidence qualification | Statements that evidence is insufficient for definitive attribution | 6 |
| Misattribution caveats | Warnings about false attribution or alternative actors | 6 |
| Corroboration demands | Calls for further analysis or independent verification | 6 |
| Contextual support | Geopolitical context supports but does not prove attribution | 5 |
| Procedural hedges | Generic analytical caution about process | 5 |

### Key findings

**Actor pairwise significance (50 tests across 10 actor pairs x 5 categories):** 10/50 significant at p < 0.05. phi4 is classified as "moderately differentiated" — less uniform than deepseek-r1 (1/50) or qwen3 (1/50) but more uniform than gemma3n (13/50). The significant tests concentrate in corroboration demands and contextual support, where US_Confirmed shows lower rates than other actors.

**China-vs-rest (Confirmed level):** 0/5 categories significant. No China-protective or China-punitive framing detected.

**Temperature effect (5 tests at Confirmed level):** 1/5 significant (corroboration demands: higher at T=0.7 than T=0.0, d = -0.192).

**Certainty calibration (25 tests):** 8/25 significant. Evidence-qualification hedges drop significantly from Suspected to Confirmed for all five actors. Misattribution caveats shift for China and Russia. This is a moderate calibration signal — weaker than deepseek-r1 (13/25) but stronger than gemma3n.

Full analysis: [[phi4/Confidence_Pattern_Analysis]]

---

## 15. Related Files

- [[04_Personal/LLM-Benchmark/docs/methodology]] — Full research methodology
- [[llama31/Results_Data]] — Phase II llama3.1 quantitative results (2,112 records)
- [[llama31/Results]] — Phase II llama3.1 results in plain language
- [[qwen3-thinking/Results_Data]] — Phase II qwen3:8b quantitative results (2,112 records)
- [[qwen3-thinking/Results]] — Phase II qwen3:8b results in plain language
- [[deepseek-r1/Results_Data]] — Phase II deepseek-r1:8b quantitative results (2,107 records)
- [[deepseek-r1/Results]] — Phase II deepseek-r1:8b results in plain language
- [[gemma3n/Results_Data]] — Phase II gemma3n quantitative results (2,112 records)
- [[qwen3-nothink/Results_Data]] — Phase II qwen3-nothink quantitative results (2,112 records)
- [[phi4/Confidence_Pattern_Analysis]] — phi4 confidence assessment rhetorical pattern taxonomy
- [[Phase_2/Cross_Model_Confidence_Patterns]] — Cross-model confidence pattern comparison
- [[Phase_2/CVE_Fixation_Analysis]] — Cross-model CVE analysis
- Results directory: `results/Phase_2/`
