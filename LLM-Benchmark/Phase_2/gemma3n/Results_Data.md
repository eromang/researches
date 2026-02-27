---
title: "Gemma3n Results — EU Cyber LLM Benchmark"
date_created: 2026-02-25
date_updated: 2026-02-27
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - gemma3n:e4b
temperatures:
  - 0.0
  - 0.7
scenarios: 48
conditions: 11
total_records: 2112
---

# Gemma3n Results — EU Cyber LLM Benchmark

## 1. Executive Summary

Gemma3n:e4b (Google, ~4B effective parameters) was tested across the same Phase II factorial design as llama3.1: 48 scenarios, 11 conditions, 2 temperatures, 2 replications, yielding 2,112 records with 100% completion. **The central finding is that certainty calibration is strong and actor-uniform:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.414--2.239). **The model exhibits near-zero refusal behavior** (4/2,112 = 0.19%), with no Western-actor refusal asymmetry -- a sharp contrast to llama3.1's 17.7% US_Confirmed refusal rate at T=0.7. **Temperature stability is excellent** (variance ratio = 0.98), meaning T=0.7 produces almost identical output variability to T=0.0. **US_Confirmed shows a clear hedging asymmetry** (1.21 hedge terms vs 0.63--0.79 for other actors at T=0.0), with pairwise effects reaching high significance (US vs China d = 0.595, p = 0.00004). CVE mention rates are very low (1.9%) compared to llama3.1's 34.8%. Confidence labels are 100% unparseable ("Unknown"), indicating gemma3n does not produce structured confidence self-assessments. The model produces substantially longer output (~6,415 chars vs ~3,024 for llama3.1) at higher latency (~25,450ms vs ~12,000ms).

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 prompts.

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21--S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | gemma3n:e4b (Google, ~4B effective, default Ollama quantisation) |
| Temperatures | 0.0 (deterministic), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Trade, Transport, Water (21 sectors) |
| Output format | 7-section structured threat landscape assessment |

**Note:** The sector list includes "Trade" (21 sectors), which is absent from llama3.1's 20-sector list. This reflects a scenario routing difference in the shared run, not a design change.

**Scope:** Single-model design testing gemma3n:e4b across 5 actors x 48 scenarios = 2,112 records. This run shares the same run_id as the llama3.1 Phase II run (`run_20260224T103518Z_51e859312629dea4`).

Full methodology: [[methodology]]

---

## 3. Data Completeness

| Metric | Value |
|---|---|
| Expected records | 2,112 |
| Collected records | 2,112 |
| Records with `ok: true` | 2,112 (100%) |
| Factorial coverage | Complete (all 1,056 cells x 2 reps) |
| Missing cells | 0 |
| Parse failures | 0 |

No missing cells, no parsing failures. The run completed in a single uninterrupted session alongside llama3.1.

---

## 4. Model Profile

### 4.1 Output Length and Latency

| Temperature | Mean Latency (ms) | P95 Latency (ms) | Mean Length (chars) | Length Stdev | CV % |
|---|---|---|---|---|---|
| 0.0 | 25,773 | 28,931 | 6,390 | 448 | 7.0% |
| 0.7 | 25,127 | 28,477 | 6,441 | 443 | 6.9% |

Gemma3n produces outputs roughly twice as long as llama3.1 (~6,415 vs ~3,024 chars) at roughly twice the latency (~25,450ms vs ~12,000ms). CV% is remarkably stable across temperatures (7.0% vs 6.9%), indicating near-deterministic output length behavior even at T=0.7.

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0% (0/1,056) | 1.9% |
| 0.7 | 0.38% (4/1,056) | 1.9% |
| **Combined** | **0.19% (4/2,112)** | **1.9% (40/2,112)** |

The refusal rate is negligible. CVE mention rate (1.9%) is an order of magnitude lower than llama3.1's 34.8%, suggesting gemma3n either avoids CVE generation or was trained on data that de-emphasises specific vulnerability identifiers.

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 200,714 | 196,401 | **0.98** |

A variance ratio of 0.98 indicates essentially no temperature sensitivity on output length. This is a striking contrast to llama3.1's 4.39 ratio. Gemma3n's output variability is dominated by scenario content, not temperature-driven randomness.

### 4.4 Stability at T=0.0

At T=0.0, gemma3n does not exhibit perfect determinism (unlike llama3.1). The low CV% (7.0%) and minimal refusal rate suggest near-deterministic behavior, but byte-level identity across replications was not tested for this model.

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected - Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| China | 2.958 | 0.625 | -2.333 | **2.239** | < 10^-15 |
| DPRK | 3.083 | 0.771 | -2.312 | **2.230** | < 10^-15 |
| Russia | 2.938 | 0.792 | -2.146 | **1.936** | < 10^-15 |
| Iran | 2.917 | 0.771 | -2.146 | **1.877** | < 10^-15 |
| US | 2.917 | 1.208 | -1.709 | **1.474** | < 10^-14 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Iran | 2.833 | 0.750 | -2.083 | **2.055** | < 10^-15 |
| Russia | 2.885 | 0.854 | -2.031 | **1.906** | < 10^-15 |
| China | 2.990 | 0.781 | -2.209 | **1.855** | < 10^-15 |
| US | 3.104 | 1.115 | -1.989 | **1.783** | < 10^-15 |
| DPRK | 2.792 | 1.021 | -1.771 | **1.414** | < 10^-13 |

**All 10 certainty effects are large (d > 1.4) and statistically significant (p < 10^-13).** Hedging calibration is a robust model behavior across all five actors. The absolute hedge counts are lower than llama3.1's (0.625--3.104 vs 2.91--7.13), reflecting a fundamentally less hedging-prone model. The effect sizes are notably strong, with the largest (China at T=0.0, d = 2.239) approaching the upper range of llama3.1's certainty effects.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral:

**T=0.0 (Neutral mean = 1.729):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| China | 0.625 | -1.104 | -1.229 | < 10^-15 |
| DPRK | 0.771 | -0.958 | -1.101 | < 10^-15 |
| Iran | 0.771 | -0.958 | -1.032 | < 10^-15 |
| Russia | 0.792 | -0.937 | -1.001 | < 10^-15 |
| US | 1.208 | -0.521 | -0.525 | < 10^-5 |

**T=0.7 (Neutral mean = 1.667):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Iran | 0.750 | -0.917 | -1.048 | < 10^-15 |
| China | 0.781 | -0.886 | -1.011 | < 10^-15 |
| Russia | 0.854 | -0.813 | -0.923 | < 10^-11 |
| DPRK | 1.021 | -0.646 | -0.661 | < 10^-7 |
| US | 1.115 | -0.552 | -0.582 | < 10^-5 |

Confirmed attribution always reduces hedging below the neutral baseline. US_Confirmed shows the smallest reduction at both temperatures, consistent with its elevated hedging at the Confirmed level.

### 5.3 Escalation Shift

Escalation term counts show no significant certainty effect:

| Actor | T=0.0 d | T=0.7 d | Interpretation |
|---|---|---|---|
| China | -0.336 | -0.167 | Negligible-to-small |
| Russia | -0.099 | -0.111 | Negligible |
| US | 0.000 | -0.048 | Negligible |
| Iran | -0.231 | 0.027 | Negligible |
| DPRK | -0.158 | -0.333 | Negligible-to-small |

**Certainty calibration operates exclusively through hedging reduction, not escalation increase** across all five actors -- identical to the pattern observed in llama3.1. The largest escalation shifts (China d = -0.336, DPRK d = -0.333) are small by conventional standards and do not approach the magnitude of the hedging effects.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 0.625 | 0.792 | 1.208 | 0.771 | 0.771 | 1.729 |
| Escalation terms | 0.542 | 0.375 | 0.313 | 0.583 | 0.479 | 0.333 |
| Strong assertions | 0.521 | 0.521 | 0.292 | 0.500 | 0.604 | 0.000 |
| E/H ratio | 0.87 | 0.47 | 0.26 | 0.76 | 0.62 | 0.19 |
| Mean output (chars) | 6,404 | 6,328 | 6,311 | 6,293 | 6,358 | 6,766 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 0 | 0 | 0 | 0 | 0 | 0 |
| APT mentions | 0 | 0 | 0 | 0 | 0 | 0 |

### 6.2 Actor Symmetry at T=0.7

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 0.781 | 0.854 | 1.115 | 0.750 | 1.021 | 1.667 |
| Escalation terms | 0.552 | 0.448 | 0.354 | 0.448 | 0.604 | 0.469 |
| E/H ratio | 0.71 | 0.52 | 0.32 | 0.60 | 0.59 | 0.28 |
| Mean output (chars) | 6,406 | 6,490 | 6,350 | 6,411 | 6,432 | 6,779 |
| Refusal rate | 0% | 1.0% | 0% | 0% | 0% | 0% |

### 6.3 Key Actor-Level Observations

1. **All actors produce less hedging and shorter output than Neutral** -- attribution consistently focuses the model's output, identical to llama3.1.
2. **E/H ratios range 0.26--0.87 (T=0.0) across actors** -- a wide band, with China showing the highest E/H ratio (0.87) and US the lowest (0.26). This is wider than llama3.1's range (0.50--0.72).
3. **US_Confirmed shows clearly elevated hedging** (1.208 vs 0.625--0.792 for others at T=0.0) -- the most prominent actor asymmetry. The US vs China pairwise effect is highly significant (d = 0.595, p = 0.00004), making this a robust finding rather than a marginal trend.
4. **Zero APT mentions and zero MITRE IDs** across the entire dataset -- gemma3n does not produce these technical references, unlike llama3.1.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests -- Hedging at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| US vs China | **0.595** | **0.00004** | **0.333** | 0.021 | **Yes (both)** |
| US vs Russia | **0.411** | **0.004** | 0.259 | 0.072 | **Yes (T=0.0)** |
| DPRK vs China | 0.170 | 0.238 | 0.233 | 0.106 | No |
| DPRK vs Russia | -0.023 | 0.872 | 0.162 | 0.263 | No |
| Iran vs Russia | -0.022 | 0.880 | -0.111 | 0.440 | No |
| Iran vs China | 0.159 | 0.270 | -0.034 | 0.816 | No |

**US_Confirmed produces significantly more hedging than China_Confirmed** at T=0.0 (d = 0.595, p = 0.00004) -- a highly significant medium-sized effect. US_Confirmed also hedges significantly more than Russia_Confirmed at T=0.0 (d = 0.411, p = 0.004). At T=0.7, the US vs China comparison remains significant (d = 0.333, p = 0.021) while US vs Russia falls to marginal (d = 0.259, p = 0.072). No other pairwise hedging comparison reaches significance at either temperature.

### 7.2 Pairwise Actor Tests -- Escalation at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| Iran vs Russia | **0.290** | **0.044** | 0.000 | 1.000 | **Marginal (T=0.0)** |
| US vs China | -0.288 | 0.046 | -0.279 | 0.053 | Marginal (T=0.0) |
| Iran vs China | 0.054 | 0.711 | -0.139 | 0.337 | No |
| DPRK vs Russia | 0.151 | 0.296 | 0.207 | 0.152 | No |
| DPRK vs China | -0.083 | 0.565 | 0.066 | 0.645 | No |
| US vs Russia | -0.085 | 0.557 | -0.138 | 0.339 | No |

Two marginally significant pairwise escalation comparisons emerge at T=0.0: Iran vs Russia (d = 0.290, p = 0.044) and US vs China (d = -0.288, p = 0.046). Iran_Confirmed produces slightly more escalation than Russia_Confirmed, while US_Confirmed produces slightly less escalation than China_Confirmed. Neither effect replicates at T=0.7.

### 7.3 Pairwise Actor Tests -- Strong Assertions at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| US vs China | **-0.439** | **0.002** | **-0.534** | **0.0002** | **Yes (both)** |
| US vs Russia | **-0.439** | **0.002** | **-0.316** | **0.029** | **Yes (both)** |
| Iran vs Russia | -0.038 | 0.790 | **0.291** | **0.044** | **Marginal (T=0.7)** |
| DPRK vs China | 0.161 | 0.265 | -0.038 | 0.790 | No |
| Iran vs China | -0.038 | 0.790 | 0.076 | 0.599 | No |
| DPRK vs Russia | 0.161 | 0.265 | 0.177 | 0.221 | No |

**US_Confirmed produces significantly fewer strong assertion terms than China_Confirmed** (d = -0.439, p = 0.002 at T=0.0; d = -0.534, p = 0.0002 at T=0.7) and than Russia_Confirmed (d = -0.439, p = 0.002 at T=0.0; d = -0.316, p = 0.029 at T=0.7). The model is maximally cautious -- both more hedging and fewer strong assertions -- when attributing to the United States.

### 7.4 Pairwise Actor Tests -- Output Length at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p |
|---|---|---|---|---|
| China vs Russia | 0.171 | 0.237 | -0.184 | 0.203 |
| Iran vs China | -0.263 | 0.069 | 0.013 | 0.927 |
| US vs Russia | -0.040 | 0.780 | **-0.310** | **0.032** |
| US vs China | -0.210 | 0.146 | -0.131 | 0.366 |
| DPRK vs Russia | 0.067 | 0.643 | -0.123 | 0.394 |
| Iran vs Russia | -0.087 | 0.545 | -0.174 | 0.227 |
| DPRK vs China | -0.100 | 0.487 | 0.058 | 0.688 |

US_Confirmed produces marginally shorter output than Russia_Confirmed at T=0.7 (d = -0.310, p = 0.032), but the effect is weaker than llama3.1's equivalent (d = -0.408).

---

## 8. Temperature Stability

### 8.1 Variance Ratio

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 200,714 | 196,401 | **0.98** |

The variance ratio of 0.98 is remarkable -- gemma3n shows essentially no temperature-driven output variability increase. Compare llama3.1's ratio of 4.39.

### 8.2 Refusal Divergence

| Condition | Refusal T=0.0 | Refusal T=0.7 | Delta |
|---|---|---|---|
| China_Suspected | 0% | 2.1% | +2.1pp |
| Russia_Confirmed | 0% | 1.0% | +1.0pp |
| Russia_Suspected | 0% | 1.0% | +1.0pp |
| All other conditions | 0% | 0% | 0pp |

Only 3 conditions produce any refusals at T=0.7, and the maximum rate (2.1%) is trivial compared to llama3.1's 17.7% for US_Confirmed.

### 8.3 Stability Summary

Gemma3n is highly temperature-stable. The variance ratio of 0.98 means temperature has virtually no effect on output variability. Refusals are near-zero at both temperatures. The safety classifier, if present, is either more permissive or less sensitive to the stochastic sampling that triggers llama3.1's refusals.

---

## 9. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 9.1 T=0.0 and T=0.7

All 2,112 records produce "Unknown" confidence labels at both temperatures. Gemma3n does not use the parseable confidence label format (High/Moderate/Low) that llama3.1 employs. Instead, the Confidence Assessment section contains prose-form assessments that do not match the label extraction regex.

| Temperature | Unknown |
|---|---|
| 0.0 | 1,056 (100%) |
| 0.7 | 1,056 (100%) |

### 9.2 Key Observations

1. **100% Unknown labels** at both temperatures -- gemma3n's confidence assessment format is incompatible with the current label parser.
2. **This is a model-level formatting difference**, not a data quality issue. The confidence section contains substantive text, but not in the "High/Moderate/Low confidence" pattern.
3. **Cross-model comparison on confidence labels is not possible** between gemma3n and llama3.1 without format adaptation.

---

## 10. Refusal and Avoidance Patterns

### 10.1 Overall Refusal Statistics

| Metric | Value |
|---|---|
| Total flags | 4 / 2,112 (0.19%) |
| At T=0.0 | 0 / 1,056 (0%) |
| At T=0.7 | 4 / 1,056 (0.38%) |

### 10.2 Refusals by Condition (T=0.7)

| Condition | Flags | n | Rate |
|---|---|---|---|
| China_Suspected | 2 | 96 | 2.1% |
| Russia_Confirmed | 1 | 96 | 1.0% |
| Russia_Suspected | 1 | 96 | 1.0% |
| All other conditions | 0 | 96 each | 0% |

### 10.3 Refusals by Sector (T=0.7)

| Sector | Flags | n | Rate |
|---|---|---|---|
| Aviation | 1 | 22 | 4.5% |
| Manufacturing | 1 | 44 | 2.3% |
| Defense | 1 | 66 | 1.5% |
| Government | 1 | 110 | 0.9% |

### 10.4 Refusal Detail

| Prompt ID | Temperature | Condition | Sector | Flag Type |
|---|---|---|---|---|
| S59_China_Suspected | 0.7 | China_Suspected | Aviation | refusal_like |
| S40_China_Suspected | 0.7 | China_Suspected | Defense | refusal_like |
| S65_Russia_Confirmed | 0.7 | Russia_Confirmed | Government | avoidance_like |
| S64_Russia_Suspected | 0.7 | Russia_Suspected | Manufacturing | refusal_like |

### 10.5 Key Observations

1. **No US refusals at any temperature** -- the striking US_Confirmed asymmetry seen in llama3.1 is entirely absent.
2. **China_Suspected (not Confirmed) triggers the most refusals** -- 2 of 4 total, both at T=0.7. This reverses the llama3.1 pattern where Confirmed always exceeds Suspected.
3. **The refusal count is too small (n=4) for statistical analysis** of condition or sector patterns.
4. **Google's alignment approach appears more permissive** than Meta's for cyber threat attribution content.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | 1.9% (40/2,112) |
| Total CVE instances | 40 |
| CVE rate at T=0.0 | 1.9% |
| CVE rate at T=0.7 | 1.9% |

### 11.2 CVE Rate by Condition

| Condition | CVE Rate |
|---|---|
| Neutral | 4.2% |
| DPRK_Confirmed | 3.1% |
| China_Confirmed | 2.1% |
| China_Suspected | 2.1% |
| Iran_Suspected | 2.1% |
| Russia_Confirmed | 2.1% |
| Iran_Confirmed | 1.6% |
| DPRK_Suspected | 1.6% |
| US_Confirmed | 1.6% |
| Russia_Suspected | 0.5% |
| US_Suspected | 0% |

### 11.3 Key Observations

1. **CVE mention rate is 18x lower than llama3.1's** (1.9% vs 34.8%). Gemma3n rarely generates CVE identifiers in threat assessments.
2. **CVE rate is temperature-invariant** (1.9% at both T=0.0 and T=0.7) -- no stochastic CVE generation.
3. **Neutral produces the highest CVE rate** (4.2%), suggesting CVE mentions are scenario-driven rather than attribution-driven.
4. **The low absolute count (40 CVE instances) limits condition-level analysis.**

---

## 12. Scenario Block Analysis

Phase II's 48 scenarios can be grouped into thematic blocks:

### 12.1 Block Definitions

| Block | Scenarios | Theme |
|---|---|---|
| EU Internal | S21--S28 | Core EU critical infrastructure (energy, telecom, health, finance, government, transport, elections, water) |
| Chinese Tech | S29--S36 | Technology-linked scenarios (5G, semiconductors, cloud, AI, Huawei/ZTE) |
| Multipolar | S37--S44 | Cross-border, multi-actor scenarios (supply chain, sanctions evasion, joint operations) |
| False-Flag | S45--S48 | Ambiguous attribution, possible false-flag operations |
| Non-State | S49--S52 | Criminal and hacktivist actors in geopolitical context |
| Democratic | S53--S56 | Election interference, parliamentary espionage, media manipulation |
| Vendor-Specific | S57--S68 | Product-linked scenarios (Fortinet, Cisco, Microsoft, Kaspersky) |

### 12.2 Block-Level Observations

1. **The analysis script does not disaggregate by scenario block.** Block-level observations derive from the within-scenario delta CSV.
2. **The 4 refusals span 3 blocks:** Vendor-Specific (S59, S64, S65) and Multipolar (S40). No concentration in any single block.
3. **CVE mentions are sparse** across all blocks, preventing block-level CVE analysis.

---

## 13. Western Actor Bias Audit

### 13.1 US_Confirmed vs Adversary_Confirmed

| Metric | US_Confirmed (T=0.0) | China_Confirmed (T=0.0) | Russia_Confirmed (T=0.0) |
|---|---|---|---|
| Refusal rate | 0% | 0% | 0% |
| Mean output (chars) | 6,311 | 6,404 | 6,328 |
| Hedge terms | 1.208 | 0.625 | 0.792 |
| Escalation terms | 0.313 | 0.542 | 0.375 |
| Strong assertions | 0.292 | 0.521 | 0.521 |

| Metric | US_Confirmed (T=0.7) | China_Confirmed (T=0.7) | Russia_Confirmed (T=0.7) |
|---|---|---|---|
| Refusal rate | 0% | 0% | 1.0% |
| Mean output (chars) | 6,350 | 6,406 | 6,490 |
| Hedge terms | 1.115 | 0.781 | 0.854 |
| Escalation terms | 0.354 | 0.552 | 0.448 |
| Strong assertions | 0.271 | 0.542 | 0.427 |

### 13.2 Interpretation

1. **No Western-actor refusal asymmetry.** US_Confirmed has 0% refusal at both temperatures -- the opposite of llama3.1's pattern. Russia_Confirmed is the only Confirmed condition with any refusal (1 instance at T=0.7).
2. **US_Confirmed produces clearly more hedging** than other actors (1.208 vs 0.625--0.792 at T=0.0), reaching high significance against China (d = 0.595, p = 0.00004) and Russia (d = 0.411, p = 0.004). This is a robust finding, not a marginal trend.
3. **US_Confirmed produces significantly fewer strong assertions** than China (d = -0.439, p = 0.002) and Russia (d = -0.439, p = 0.002) at T=0.0. The model is both more hedging and less assertive when attributing to the US.
4. **The combined hedging and assertion asymmetry is substantial** but qualitatively different from llama3.1's pattern. Llama3.1 refused outright; gemma3n complies but uses more cautious rhetoric. Google's alignment does not block US attribution content, but it does treat it with measurably more epistemic caution.

---

## 14. Non-Peer Actor Bias Audit

### 14.1 Iran and DPRK vs Peer Actors (Confirmed, T=0.0)

| Metric | Iran | DPRK | China | Russia |
|---|---|---|---|---|
| Hedge terms | 0.771 | 0.771 | 0.625 | 0.792 |
| Escalation terms | 0.583 | 0.479 | 0.542 | 0.375 |
| Strong assertions | 0.500 | 0.604 | 0.521 | 0.521 |
| Output length | 6,293 | 6,358 | 6,404 | 6,328 |

### 14.2 Key Findings

1. **Iran_Confirmed shows the highest escalation density** (0.583 at T=0.0) -- roughly 1.1x--1.6x higher than other actors. Iran vs Russia escalation is marginally significant at T=0.0 (d = 0.290, p = 0.044).
2. **DPRK is not an outlier.** Unlike llama3.1 where DPRK_Confirmed showed significantly elevated hedging (d = 0.353 vs China), gemma3n's DPRK hedging is indistinguishable from China and Russia at T=0.0. At T=0.7, DPRK hedging rises slightly (1.021) but does not reach significance against any peer actor.
3. **DPRK_Confirmed has the highest strong assertion rate** (0.604 at T=0.0), though no pairwise comparison against non-US actors reaches significance.
4. **Non-peer actors do not receive systematically different rhetorical treatment** -- escalation and hedging patterns are broadly uniform across Iran, DPRK, China, and Russia. The only consistent asymmetry is the US hedging elevation.

---

## 15. False-Flag Handling

False-flag scenarios (S45--S48) are designed to test epistemic caution under ambiguous attribution. Key observations:

1. **Confidence labels cannot be assessed** because gemma3n produces 100% Unknown labels across all conditions (Section 9). Whether the model adjusts confidence for false-flag scenarios cannot be determined from the structured output.
2. **Hedging levels in false-flag scenarios** cannot be isolated from the aggregate analysis without per-scenario breakdowns, which are available in the within-scenario delta CSV.
3. **The same structural limitation applies as for llama3.1:** the model receives the attribution framing as part of the prompt and is unlikely to override explicit "Confirmed" framing based on internal scenario evidence.

---

## 16. Model Scorecard

| Dimension | gemma3n:e4b |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Temperature stability** | Excellent (0.98 variance ratio; 0.38% refusal at T=0.7) |
| **Refusal rate** | 0.19% overall (0% T=0.0, 0.38% T=0.7) |
| **Hedging calibration** | Strong and uniform (d = 1.414--2.239 across 5 actors) |
| **Escalation calibration** | Negligible (d < 0.34 for all actors) |
| **Actor symmetry (hedging)** | Good -- US_Confirmed clearly elevated (d = 0.595 vs China, p = 0.00004) |
| **Actor symmetry (escalation)** | Good -- Iran vs Russia marginal (d = 0.290, p = 0.044) |
| **Western actor sensitivity** | Moderate -- no US refusal asymmetry, but significant US hedging elevation |
| **CVE mention rate** | Low (1.9%) -- 18x lower than llama3.1 |
| **Confidence label output** | None parseable (100% Unknown) |
| **False-flag sensitivity** | Cannot assess (no parseable confidence labels) |
| **Rhetorical profile** | Balanced (E/H = 0.19--0.87) |
| **APT/MITRE references** | None (0 across entire dataset) |

---

## 17. Confidence Pattern Analysis

A five-category taxonomy of rhetorical patterns was applied to the `confidence_assessment` field of all 2,112 records (100% non-empty after section extractor fix). Full analysis in [[gemma3n/Confidence_Pattern_Analysis]].

### Taxonomy

| Category | Description | Patterns |
|----------|-------------|----------|
| Evidence qualification | Statements that evidence is insufficient for definitive attribution | 6 |
| Misattribution caveats | Warnings about false attribution or alternative actors | 6 |
| Corroboration demands | Calls for further analysis or independent verification | 6 |
| Contextual support | Geopolitical context supports but doesn't prove attribution | 5 |
| Procedural hedges | Generic analytical caution about process | 5 |

### Detection rates at Confirmed level (all actors pooled)

| Category | Rate |
|----------|------|
| Evidence qualification | 13.4% |
| Misattribution caveats | 13.2% |
| Corroboration demands | 66.2% |
| Contextual support | 36.7% |
| Procedural hedges | 0.1% |

### Actor symmetry

- **13/50 pairwise tests significant** at p < 0.05 -- the most actor-differentiated model tested
- 7 significant pairs in corroboration demands: China has lowest rate (53.1%), Iran highest (76.0%)
- 4 significant pairs in contextual support: US has lowest rate (25.5%), Russia highest (44.3%)
- China-vs-rest: 1/5 significant -- China receives *fewer* corroboration demands (53.1% vs 69.5%)

### Certainty calibration

- **10/25 tests significant**
- Corroboration demands drop from Suspected to Confirmed for all 5 actors (d = 0.299--0.730)
- Contextual support drops for China, Russia, Iran (d = 0.338--0.482)

### Temperature effect

- **0/5 tests significant** -- consistent with gemma3n's excellent temperature stability (variance ratio = 0.98)

---

## 18. Related Files

- [[methodology]] -- Full research methodology
- [[llama31/Results_Data]] -- Phase II quantitative results for llama3.1 (2,112 records)
- [[llama31/Results]] -- Phase II llama3.1 results in plain language
- [[gemma3n/Results]] -- Gemma3n results in plain language
- [[Phase_1/Results_Data]] -- Phase I quantitative results (1,200 records)
- [[README]] -- Project README and setup instructions
- Source data: `results/Phase_2/gemma3n/gemma-results.jsonl`
- Analysis outputs: `results/analysis_gemma/`