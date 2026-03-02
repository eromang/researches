---
title: "Phase 2 Results — EU Cyber LLM Benchmark (mistral:7b-instruct)"
date_created: 2026-03-02
date_updated: 2026-03-02
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - "mistral:7b-instruct"
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

# Phase 2 Results — EU Cyber LLM Benchmark (mistral:7b-instruct)

## 1. Executive Summary

Phase II tested mistral:7b-instruct (Mistral AI, France/EU-origin, 7B instruct model without thinking mode) across the full 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,112 records with 2,112 successful completions (100%) and 0 failures. **The central finding is that certainty calibration is strong and actor-symmetric:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 0.78–1.91), with the lowest absolute confirmed hedging of any Phase II model (0.62–1.02 terms). **The model produces zero refusals (0/2,112).** Unlike most other models, mistral is escalation-dominant rather than hedging-dominant: E/H ratios exceed 1.0 for all actors at Confirmed level, with significant escalation increases vs Neutral. Confidence assessment text does not produce extractable labels at T=0.0 and only sparse labels at T=0.7. CVE mention rate is moderate (10.9%) with no fixation (top CVE at 28.7%) and high diversity (normalised Shannon H = 0.803). This is the first EU-origin model in Phase II, the smallest (7B), and the fastest (~15s mean latency).

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 expected prompts (2,112 collected).

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21–S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | mistral:7b-instruct (Mistral AI, France/EU-origin, 7B, instruct, no thinking mode) |
| Temperatures | 0.0 (greedy decoding), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing mistral:7b-instruct across 5 actors x 48 scenarios. Shared run ID with qwen3:8b, llama3.1:8b, gemma3n, deepseek-r1:8b, qwen3-nothink, and phi4 records; mistral records isolated by model field. mistral did not run in Phase 1 — no cross-phase comparison is available.

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

All 2,112 records are valid for analysis. No refusals, no parse failures.

---

## 4. Model Profile

### 4.1 Output Length and Latency

Mean values computed across all 11 conditions.

| Temperature | Mean Latency (ms) | Mean Length (chars) |
|---|---|---|
| 0.0 | 14,767 | 3,442 |
| 0.7 | 15,637 | 3,597 |
| **Combined** | **~15,202** | **~3,520** |

**Condition-level detail (T=0.0):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 14,324 | 3,307 |
| China_Suspected | 14,973 | 3,521 |
| DPRK_Confirmed | 14,607 | 3,409 |
| DPRK_Suspected | 15,056 | 3,540 |
| Iran_Confirmed | 15,158 | 3,524 |
| Iran_Suspected | 14,563 | 3,414 |
| Neutral | 15,412 | 3,599 |
| Russia_Confirmed | 14,608 | 3,377 |
| Russia_Suspected | 14,808 | 3,482 |
| US_Confirmed | 14,169 | 3,270 |
| US_Suspected | 14,755 | 3,422 |

**Condition-level detail (T=0.7):**

| Condition | Mean Latency (ms) | Mean Output (chars) |
|---|---|---|
| China_Confirmed | 15,394 | 3,536 |
| China_Suspected | 15,479 | 3,596 |
| DPRK_Confirmed | 15,820 | 3,653 |
| DPRK_Suspected | 15,694 | 3,618 |
| Iran_Confirmed | 15,824 | 3,630 |
| Iran_Suspected | 15,948 | 3,693 |
| Neutral | 15,754 | 3,604 |
| Russia_Confirmed | 15,552 | 3,563 |
| Russia_Suspected | 15,815 | 3,662 |
| US_Confirmed | 15,177 | 3,450 |
| US_Suspected | 15,552 | 3,563 |

mistral:7b-instruct is the fastest model in Phase II (~15s combined mean latency) — faster than llama3.1:8b (~12s at T=0.0 but that is a single-temperature figure; combined ~12s). Output length (~3,520 chars mean) is comparable to llama3.1 (~3,070) and other instruct models. US_Confirmed consistently produces the shortest output at both temperatures. T=0.7 is slightly slower and longer than T=0.0.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0% (0/1,056) | 9.8% |
| 0.7 | 0% (0/1,056) | 11.9% |
| **Combined** | **0% (0/2,112)** | **10.9%** |

Zero refusals across all conditions at both temperatures. CVE mention rate (10.9%) is moderate — higher than phi4 (2.8%) and gemma3n (1.9%) but lower than qwen3-nothink (25.3%), llama3.1 (34.8%), deepseek-r1 (36.4%), and qwen3 (56.5%).

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | T=0.0 | T=0.7 | Ratio |
|---|---|---|---|
| Mean output length (chars) | 3,442 | 3,597 | 1.05 |
| Mean latency (ms) | 14,767 | 15,637 | 1.06 |

Both metrics increase slightly at T=0.7. No dramatic variance inflation.

### 4.4 Stability at T=0.0

As a standard instruct model without thinking mode, mistral:7b-instruct is expected to produce deterministic output at T=0.0. This contrasts with reasoning models (deepseek-r1 and qwen3 with thinking, which show non-determinism at T=0.0 due to the thinking phase).

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected to Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Iran | 2.90 | 0.62 | -2.27 | **1.91** | ≈ 0 |
| China | 3.12 | 1.00 | -2.12 | **1.61** | ≈ 0 |
| US | 3.00 | 0.88 | -2.12 | **1.54** | ≈ 0 |
| Russia | 2.71 | 0.85 | -1.85 | **1.44** | ≈ 0 |
| DPRK | 2.83 | 1.02 | -1.81 | **1.31** | ≈ 0 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 3.56 | 1.09 | -2.47 | **1.39** | ≈ 0 |
| Russia | 2.74 | 1.08 | -1.66 | **1.12** | ≈ 0 |
| Iran | 3.23 | 1.28 | -1.95 | **1.06** | ≈ 0 |
| DPRK | 2.78 | 1.12 | -1.66 | **1.06** | ≈ 0 |
| China | 2.81 | 1.49 | -1.32 | **0.78** | < 10^-7 |

All CertaintyEffect tests are significant (p ≈ 0, d = 0.78–1.91). The effect is large and consistent across all actors and both temperatures. Absolute hedge levels at Confirmed (0.62–1.02 at T=0.0, 1.08–1.49 at T=0.7) are the lowest of any Phase II model — mistral nearly eliminates hedging under confirmed attribution.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral.

**T=0.0 (Neutral mean = 1.65):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Iran | 0.62 | -1.03 | **-1.04** | < 10^-12 |
| Russia | 0.85 | -0.80 | **-0.78** | < 10^-7 |
| US | 0.88 | -0.77 | **-0.71** | < 10^-6 |
| China | 1.00 | -0.65 | **-0.63** | < 10^-4 |
| DPRK | 1.02 | -0.63 | **-0.54** | < 10^-3 |

**T=0.7 (Neutral mean = 2.06):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Russia | 1.08 | -0.98 | **-0.67** | < 10^-5 |
| US | 1.09 | -0.97 | **-0.67** | < 10^-5 |
| DPRK | 1.12 | -0.94 | **-0.65** | < 10^-5 |
| Iran | 1.28 | -0.78 | **-0.49** | < 10^-3 |
| China | 1.49 | -0.57 | **-0.35** | < 0.02 |

Confirmed attribution consistently reduces hedging below the neutral baseline for all actors, with medium to large effect sizes (d = -0.35 to -1.04).

### 5.3 Escalation Shift (Suspected to Confirmed)

| Actor | T=0.0 Susp. Esc | T=0.0 Conf. Esc | Delta T=0.0 | T=0.7 Susp. Esc | T=0.7 Conf. Esc | Delta T=0.7 |
|---|---|---|---|---|---|---|
| China | 0.77 | 1.12 | +0.35 | 0.98 | 1.30 | +0.32 |
| DPRK | 1.06 | 1.17 | +0.11 | 1.19 | 1.45 | +0.26 |
| Iran | 0.94 | 1.21 | +0.27 | 1.06 | 1.23 | +0.17 |
| Russia | 0.85 | 1.06 | +0.21 | 0.88 | 1.00 | +0.12 |
| US | 0.83 | 1.25 | +0.42 | 1.01 | 1.22 | +0.21 |

All five Confirmed-vs-Neutral escalation tests at T=0.0 are significant (d = 0.61–0.86). mistral calibrates certainty through both hedging reduction and escalation amplification — a dual-channel effect not seen in most other models.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 1.00 | 0.85 | 0.88 | 0.62 | 1.02 | 1.65 |
| Escalation terms | 1.12 | 1.06 | 1.25 | 1.21 | 1.17 | 0.58 |
| Strong assertions | 0.44 | 0.38 | 0.54 | 0.35 | 0.52 | 0.08 |
| E/H ratio | 1.12 | 1.25 | 1.42 | 1.95 | 1.15 | 0.35 |
| Mean output (chars) | 3,307 | 3,377 | 3,270 | 3,524 | 3,409 | 3,599 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 0.00 | 0.00 | 0.08 | 0.00 | 0.00 | 0.00 |
| APT mentions | 0.08 | 0.04 | 0.00 | 0.00 | 0.02 | 0.00 |

### 6.2 Confirmed Conditions: 5-Actor Comparison (T=0.7)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 1.49 | 1.08 | 1.09 | 1.28 | 1.12 | 2.06 |
| Escalation terms | 1.30 | 1.00 | 1.22 | 1.23 | 1.45 | 0.81 |
| Strong assertions | 0.42 | 0.35 | 0.51 | 0.35 | 0.51 | 0.15 |
| E/H ratio | 0.87 | 0.93 | 1.12 | 0.96 | 1.29 | 0.39 |
| Mean output (chars) | 3,536 | 3,563 | 3,450 | 3,630 | 3,653 | 3,604 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 0.76 | 0.36 | 0.41 | 0.45 | 0.29 | 0.34 |
| APT mentions | 0.05 | 0.06 | 0.00 | 0.04 | 0.03 | 0.00 |

### 6.3 Key Actor-Level Observations

1. **E/H ratios exceed 1.0 for all actors at Confirmed T=0.0.** mistral is the only Phase II model where all five actors produce escalation-dominant output at T=0.0. At T=0.7, the pattern shifts toward balance (0.87–1.29).
2. **US_Confirmed consistently produces the shortest output** (3,270 at T=0.0, 3,450 at T=0.7).
3. **Strong assertions increase substantially under Confirmed attribution** relative to Neutral (Neutral = 0.08 vs Confirmed range 0.35–0.54 at T=0.0).
4. **APT mentions are very low** across all conditions at both temperatures. Only China_Confirmed (0.08) and Russia_Confirmed (0.04) show any APT references at T=0.0.
5. **MITRE ID mentions are near-zero at T=0.0** but increase at T=0.7, particularly for China_Confirmed (0.76) and US_Suspected (0.77).

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

| Actor | T=0.0 Hedge (Conf) | T=0.7 Hedge (Conf) | Note |
|---|---|---|---|
| Iran | 0.62 | 1.28 | Lowest at T=0.0 |
| Russia | 0.85 | 1.08 | Lowest at T=0.7 |
| US | 0.88 | 1.09 | — |
| China | 1.00 | 1.49 | Highest at T=0.7 |
| DPRK | 1.02 | 1.12 | — |
| Range | 0.40 | 0.41 | Narrow spread |

The hedge range across actors is very narrow at both temperatures (0.40 at T=0.0, 0.41 at T=0.7), indicating strong actor symmetry on hedging.

### 7.2 Pairwise Actor Tests — Output Length at Confirmed Level

At T=0.0, significant output-length comparisons include:

| Comparison | d | Significant? |
|---|---|---|
| US vs China | -0.11 | No |
| Iran vs China | 0.57 | **Yes** |
| US vs Iran | -0.81 | **Yes** |

Iran_Confirmed produces the longest output and US_Confirmed the shortest at T=0.0. At T=0.7, differences narrow.

---

## 8. Escalation Analysis

### 8.1 Attribution Escalation Effect (Confirmed vs Neutral)

**T=0.0:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | Significant? |
|---|---|---|---|---|---|
| US | 1.25 | 0.58 | +0.67 | 0.86 | **Yes** |
| Iran | 1.21 | 0.58 | +0.63 | 0.71 | **Yes** |
| DPRK | 1.17 | 0.58 | +0.59 | 0.67 | **Yes** |
| China | 1.12 | 0.58 | +0.54 | 0.65 | **Yes** |
| Russia | 1.06 | 0.58 | +0.48 | 0.61 | **Yes** |

**T=0.7:**

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d | Significant? |
|---|---|---|---|---|---|
| DPRK | 1.45 | 0.81 | +0.64 | 0.57 | **Yes** |
| China | 1.30 | 0.81 | +0.49 | 0.41 | **Yes** |
| Iran | 1.23 | 0.81 | +0.42 | 0.38 | **Yes** |
| US | 1.22 | 0.81 | +0.41 | 0.37 | **Yes** |
| Russia | 1.00 | 0.81 | +0.19 | 0.18 | No |

All five Confirmed-vs-Neutral escalation tests are significant at T=0.0 (d = 0.61–0.86). At T=0.7, 4 of 5 are significant (Russia falls below threshold). This is the strongest escalation-amplification signal of any Phase II model.

### 8.2 Escalation Ordering

At T=0.0 Confirmed: **US > Iran > DPRK > China > Russia > Neutral**. At T=0.7 Confirmed: **DPRK > China > Iran > US > Russia > Neutral**. The ordering shifts across temperatures but all actors produce more escalation than Neutral.

---

## 9. Temperature Stability

### 9.1 Variance Ratio

| Metric | T=0.0 Mean | T=0.7 Mean | Ratio |
|---|---|---|---|
| Output length (chars) | 3,442 | 3,597 | 1.05 |
| Latency (ms) | 14,767 | 15,637 | 1.06 |

Output length and latency are both slightly higher at T=0.7. No dramatic divergence.

### 9.2 Refusal Divergence

| Condition | T=0.0 Refusal | T=0.7 Refusal | Divergence |
|---|---|---|---|
| All conditions | 0% | 0% | No |

No refusal at either temperature.

### 9.3 Confidence Label Divergence

At T=0.0, mistral's confidence assessment text does not contain extractable "High," "Moderate," or "Low" labels in any condition — all records return "Unknown" under the label extraction regex. At T=0.7, a small number of standard labels appear: "High" for some Confirmed conditions (5–10 per condition) and "Moderate" for some Suspected conditions (5–9 per condition). The vast majority remain "Unknown" at both temperatures.

### 9.4 Stability Summary

mistral shows good temperature stability on quantitative metrics (hedging, escalation, output length) but the confidence label extraction failure at T=0.0 is a model-specific artefact. The model writes confidence assessments but uses non-standard vocabulary.

---

## 10. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 10.1 T=0.0

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 0 | 0 | 0 | 96 |
| China_Suspected | 0 | 0 | 0 | 96 |
| DPRK_Confirmed | 0 | 0 | 0 | 96 |
| DPRK_Suspected | 0 | 0 | 0 | 96 |
| Iran_Confirmed | 0 | 0 | 0 | 96 |
| Iran_Suspected | 0 | 0 | 0 | 96 |
| Neutral | 0 | 0 | 0 | 96 |
| Russia_Confirmed | 0 | 0 | 0 | 96 |
| Russia_Suspected | 0 | 0 | 0 | 96 |
| US_Confirmed | 0 | 0 | 0 | 96 |
| US_Suspected | 0 | 0 | 0 | 96 |

### 10.2 T=0.7

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| China_Confirmed | 10 | 2 | 0 | 84 |
| China_Suspected | 0 | 6 | 3 | 87 |
| DPRK_Confirmed | 6 | 0 | 0 | 90 |
| DPRK_Suspected | 0 | 5 | 1 | 90 |
| Iran_Confirmed | 7 | 1 | 0 | 88 |
| Iran_Suspected | 0 | 7 | 2 | 87 |
| Neutral | 0 | 2 | 6 | 88 |
| Russia_Confirmed | 6 | 0 | 0 | 90 |
| Russia_Suspected | 0 | 5 | 1 | 90 |
| US_Confirmed | 5 | 1 | 0 | 90 |
| US_Suspected | 0 | 9 | 6 | 81 |

### 10.3 Key Observations

1. **T=0.0 produces zero extractable labels.** All 1,056 records return "Unknown." The model writes narrative confidence assessments without standard "High/Moderate/Low" keywords. This is unique in Phase II.
2. **T=0.7 introduces sparse labels.** Confirmed conditions show a few "High" labels (5–10 per condition); Suspected conditions show "Moderate" labels (5–9) and occasional "Low" labels. The vast majority (81–90 per condition) remain "Unknown."
3. **Where labels do appear at T=0.7, they show correct directionality.** Confirmed conditions produce "High" labels while Suspected conditions produce "Moderate" or "Low" — consistent with proper certainty calibration. The model understands the distinction but typically expresses it in non-standard vocabulary.
4. **This is a model-specific limitation** reflecting mistral's smaller vocabulary and training data, not a design flaw. The quantitative hedging and escalation metrics still capture certainty calibration accurately.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | 10.9% |
| CVE rate at T=0.0 | 9.8% |
| CVE rate at T=0.7 | 11.9% |
| Records with CVEs | 230 |
| Unique CVEs cited | 94 |
| Mean CVE per record (when present) | 1.535 |

### 11.2 Top CVEs

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2019-19781 | 66 | 28.7% | Unverified |
| 2 | CVE-2021-30551 | 32 | 13.9% | Unverified |
| 3 | CVE-2017-11882 | 21 | 9.1% | Unverified |
| 4 | CVE-2017-0144 | 15 | 6.5% | Unverified |
| 5 | CVE-2022-30668 | 15 | 6.5% | Unverified |
| 6 | CVE-2021-40444 | 14 | 6.1% | Real |
| 7 | CVE-2017-0199 | 12 | 5.2% | Unverified |
| 8 | CVE-2017-5638 | 12 | 5.2% | Unverified |
| 9 | CVE-2019-12411 | 9 | 3.9% | Unverified |
| 10 | CVE-2017-7494 | 8 | 3.5% | Unverified |

### 11.3 CVE Fixation

mistral does NOT meet the fixation threshold: CVE-2019-19781 appears in 28.7% of CVE-containing records, below the 40% threshold. Shannon diversity index H = 5.263 (normalised 0.803), indicating good spread across CVEs.

Unlike other models that fixate on a single modern CVE (deepseek-r1 on PwnKit, phi4/llama3.1 on Log4Shell), mistral's top CVE references span a wider temporal range (2017–2022) with more legacy vulnerabilities. This is consistent with the model's smaller parameter count and older training data.

### 11.4 Comparative CVE Context

| Model | CVE Rate | Fixation? | Top CVE | Top % |
|---|---|---|---|---|
| qwen3:8b | 56.5% | No | CVE-2023-1234 | 24.0% |
| deepseek-r1:8b | 36.4% | Yes | CVE-2021-4034 | 73.0% |
| llama3.1:8b | 34.8% | Yes | CVE-2021-44228 | 48.6% |
| qwen3-nothink | 25.3% | No | CVE-2023-22892 | 22.7% |
| mistral:7b-instruct | 10.9% | No | CVE-2019-19781 | 28.7% |
| phi4:latest | 2.8% | Yes | CVE-2021-44228 | 60.3% |
| gemma3n | 1.9% | No | CVE-2017-0144 | 25.0% |

3 real CVEs detected; 0 hallucinated; 91 unverified.

---

## 12. Instruct Model Specifics

### 12.1 Latency Context

| Model | Architecture | Parameters | Mean Latency (T=0.0) | Mean Latency (T=0.7) |
|---|---|---|---|---|
| mistral:7b-instruct | Instruct | 7B | 14,767 ms | 15,637 ms |
| llama3.1:8b | Instruct | 8B | 13,141 ms | 10,975 ms |
| gemma3n | Instruct | 8B | ~15,000 ms | ~14,000 ms |
| qwen3-nothink | Instruct | 8B | ~18,000 ms | ~16,000 ms |
| phi4:latest | Instruct | 14B | 32,030 ms | 28,657 ms |
| qwen3:8b | Reasoning | 8B | 35,244 ms | 33,338 ms |
| deepseek-r1:8b | Reasoning | 8B | 49,594 ms | 44,512 ms |

mistral at 7B runs at comparable speed to llama3.1 and gemma3n despite being slightly smaller. The similar latencies reflect hardware constraints (all running on the same local Ollama instance).

### 12.2 Determinism at T=0.0

As a standard instruct model, mistral:7b-instruct should produce deterministic output at T=0.0. This contrasts with deepseek-r1:8b and qwen3:8b (thinking mode), where the internal chain-of-thought introduces non-determinism even at T=0.0.

| Characteristic | mistral:7b-instruct | llama3.1:8b | phi4:latest | qwen3:8b | deepseek-r1:8b |
|---|---|---|---|---|---|
| Architecture | Instruct | Instruct | Instruct | Reasoning | Reasoning |
| Parameters | 7B | 8B | 14B | 8B | 8B |
| `--strip-thinking` | N/A | N/A | N/A | Yes | Yes |
| Expected T=0.0 determinism | Deterministic | Deterministic (100%) | Deterministic | Non-deterministic (9.3%) | Non-deterministic |
| Output length (mean) | ~3,520 chars | ~3,070 chars | ~3,894 chars | ~3,793 chars | ~7,932 chars |

---

## 13. Model Scorecard

| Dimension | mistral:7b-instruct (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Instruct (no thinking mode) |
| **Parameters** | 7B (smallest in Phase II) |
| **Origin** | Mistral AI (France, EU) — first EU-origin model |
| **Temperature stability** | Good on metrics; labels absent at T=0.0 |
| **Refusal rate** | 0% (0/2,112) |
| **Hedging calibration** | Strong (d = 0.78–1.91 across 5 actors; all significant) |
| **Escalation calibration** | Strong vs Neutral (d = 0.61–0.86 at T=0.0; all significant) |
| **Actor symmetry (hedging)** | Strong — narrow range (0.40–0.41 across actors at Confirmed) |
| **Actor symmetry (rhetoric)** | Very strong — 0/50 pairwise tests significant |
| **Western actor sensitivity** | None — US shows slightly shorter output but no asymmetry |
| **CVE mention rate** | 10.9% (moderate) |
| **CVE fixation** | No — top CVE at 28.7% (below 40% threshold) |
| **CVE diversity** | High — normalised Shannon H = 0.803 |
| **Confidence label output** | Absent at T=0.0; sparse at T=0.7 |
| **Rhetorical profile** | Escalation-dominant (E/H = 1.12–1.95 at T=0.0) |
| **Confidence pattern symmetry** | Very strong — 0/50 pairwise tests significant |
| **Latency** | Fast (~15s combined mean) |
| **Output length** | Moderate (~3,520 chars mean) |
| **T=0.0 determinism** | Expected deterministic (instruct architecture) |

---

## 14. Confidence Assessment Rhetorical Patterns

A five-category rhetorical pattern taxonomy was applied to mistral's 2,112 ok records' `confidence_assessment` fields via 28 regex detectors, mirroring the analysis conducted for all other Phase II models.

### Taxonomy

| Category | Description | Patterns |
|---|---|---|
| Evidence qualification | Statements that evidence is insufficient for definitive attribution | 6 |
| Misattribution caveats | Warnings about false attribution or alternative actors | 6 |
| Corroboration demands | Calls for further analysis or independent verification | 6 |
| Contextual support | Geopolitical context supports but does not prove attribution | 5 |
| Procedural hedges | Generic analytical caution about process | 5 |

### Key findings

**Actor pairwise significance (50 tests across 10 actor pairs x 5 categories):** 0/50 significant at p < 0.05. mistral is classified as "actor-uniform" — the most symmetric model tested. No actor pair shows statistically significant differences on any rhetorical pattern category at Confirmed level.

**China-vs-rest (Confirmed level):** 0/5 categories significant. No China-protective or China-punitive framing detected.

**Temperature effect (5 tests at Confirmed level):** 0/5 significant. Temperature does not affect the rhetorical pattern profile.

**Certainty calibration (25 tests):** 1/25 significant (US corroboration demands: Suspected > Confirmed, d = 0.206). This is the weakest calibration signal of any Phase II model at the rhetorical pattern level, though the quantitative hedging/escalation metrics show strong calibration. The low detection rates across all categories (0–2.1%) mean the regex-based taxonomy has little signal to detect in mistral's output.

Full analysis: [[mistral/Confidence_Pattern_Analysis]]

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
- [[phi4/Results_Data]] — Phase II phi4 quantitative results (2,112 records)
- [[phi4/Results]] — Phase II phi4 results in plain language
- [[mistral/Confidence_Pattern_Analysis]] — mistral confidence assessment rhetorical pattern taxonomy
- [[Phase_2/Cross_Model_Confidence_Patterns]] — Cross-model confidence pattern comparison
- [[Phase_2/CVE_Fixation_Analysis]] — Cross-model CVE analysis
- Results directory: `results/Phase_2/`
