# Gemma3n Results — EU Cyber LLM Benchmark

## 1. Executive Summary

Gemma3n:e4b (Google, ~4B effective parameters) was tested across the same Phase II factorial design as llama3.1: 48 scenarios, 11 conditions, 2 temperatures, 2 replications, yielding 2,112 records with 100% completion. **The central finding is that certainty calibration is strong and actor-uniform:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.08--1.66). **The model exhibits near-zero refusal behavior** (4/2,112 = 0.19%), with no Western-actor refusal asymmetry -- a sharp contrast to llama3.1's 17.7% US_Confirmed refusal rate at T=0.7. **Temperature stability is excellent** (variance ratio = 0.98), meaning T=0.7 produces almost identical output variability to T=0.0. CVE mention rates are very low (1.9%) compared to llama3.1's 34.8%. Confidence labels are 100% unparseable ("Unknown"), indicating gemma3n does not produce structured confidence self-assessments. The model produces substantially longer output (~6,415 chars vs ~3,024 for llama3.1) at higher latency (~25,450ms vs ~12,000ms).

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

Full methodology: [Full Research Methodology](../../docs/methodology.md)

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
| 0.0 | 25,773 | 28,941 | 6,390 | 448 | 7.0% |
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
| China | 2.00 | 0.50 | -1.50 | **1.655** | < 10^-15 |
| Russia | 1.92 | 0.50 | -1.42 | **1.567** | < 10^-15 |
| DPRK | 2.02 | 0.54 | -1.48 | **1.565** | < 10^-15 |
| Iran | 1.90 | 0.48 | -1.42 | **1.485** | < 10^-15 |
| US | 1.90 | 0.79 | -1.10 | **1.132** | < 10^-14 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| Russia | 1.91 | 0.51 | -1.40 | **1.560** | < 10^-15 |
| Iran | 1.79 | 0.49 | -1.30 | **1.529** | < 10^-15 |
| China | 2.02 | 0.57 | -1.45 | **1.474** | < 10^-15 |
| US | 2.04 | 0.82 | -1.22 | **1.282** | < 10^-15 |
| DPRK | 1.84 | 0.69 | -1.16 | **1.081** | < 10^-13 |

**All 10 certainty effects are large (d > 1.0) and statistically significant (p < 10^-13).** Hedging calibration is a robust model behavior across all five actors. The absolute hedge counts are much lower than llama3.1's (0.48--2.04 vs 2.50--5.65), reflecting a fundamentally less hedging-prone model.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral:

**T=0.0 (Neutral mean = 1.58):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| Iran | 0.48 | -1.10 | -1.371 | < 10^-15 |
| China | 0.50 | -1.08 | -1.345 | < 10^-15 |
| Russia | 0.50 | -1.08 | -1.390 | < 10^-15 |
| DPRK | 0.54 | -1.04 | -1.338 | < 10^-15 |
| US | 0.79 | -0.79 | -0.888 | < 10^-9 |

Confirmed attribution always reduces hedging below the neutral baseline. US_Confirmed shows the smallest reduction, consistent with its slightly elevated hedging at the Confirmed level.

### 5.3 Escalation Shift

Escalation term counts show no significant certainty effect:

| Actor | T=0.0 d | T=0.7 d | Interpretation |
|---|---|---|---|
| China | -0.081 | -0.061 | Negligible |
| Russia | -0.160 | -0.108 | Negligible |
| US | -0.036 | -0.091 | Negligible |
| Iran | -0.185 | 0.035 | Negligible |
| DPRK | -0.043 | -0.222 | Negligible |

**Certainty calibration operates exclusively through hedging reduction, not escalation increase** across all five actors -- identical to the pattern observed in llama3.1.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 0.50 | 0.50 | 0.79 | 0.48 | 0.54 | 1.58 |
| Escalation terms | 0.19 | 0.25 | 0.27 | 0.35 | 0.23 | 0.19 |
| Strong assertions | 0.10 | 0.08 | 0.06 | 0.04 | 0.02 | 0.02 |
| E/H ratio | 0.38 | 0.50 | 0.34 | 0.74 | 0.42 | 0.12 |
| Mean output (chars) | 6,404 | 6,328 | 6,311 | 6,293 | 6,358 | 6,766 |
| Refusal rate | 0% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 0 | 0 | 0 | 0 | 0 | 0 |
| APT mentions | 0 | 0 | 0 | 0 | 0 | 0 |

### 6.2 Actor Symmetry at T=0.7

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 0.57 | 0.51 | 0.82 | 0.49 | 0.69 | 1.53 |
| Escalation terms | 0.24 | 0.24 | 0.28 | 0.25 | 0.30 | 0.22 |
| E/H ratio | 0.42 | 0.47 | 0.34 | 0.51 | 0.44 | 0.14 |
| Mean output (chars) | 6,406 | 6,490 | 6,350 | 6,411 | 6,432 | 6,779 |
| Refusal rate | 0% | 1.0% | 0% | 0% | 0% | 0% |

### 6.3 Key Actor-Level Observations

1. **All actors produce less hedging and shorter output than Neutral** -- attribution consistently focuses the model's output, identical to llama3.1.
2. **E/H ratios range 0.34--0.74 (T=0.0) across actors** -- a wider band than llama3.1 (0.40--0.55), with Iran showing the highest E/H ratio.
3. **US_Confirmed shows slightly elevated hedging** (0.79 vs 0.48--0.54 for others at T=0.0) -- the one consistent actor asymmetry, though in the opposite direction from llama3.1's US refusal pattern.
4. **Zero APT mentions and zero MITRE IDs** across the entire dataset -- gemma3n does not produce these technical references, unlike llama3.1.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests -- Hedging at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| US vs China | 0.331 | 0.022 | 0.294 | 0.042 | Marginal (both) |
| US vs Russia | **0.340** | 0.018 | **0.372** | 0.010 | **Yes (T=0.7)** |
| DPRK vs China | 0.054 | 0.71 | 0.133 | 0.36 | No |
| DPRK vs Russia | 0.056 | 0.70 | 0.209 | 0.15 | No |
| Iran vs Russia | -0.027 | 0.85 | -0.028 | 0.84 | No |
| Iran vs China | -0.026 | 0.86 | -0.112 | 0.44 | No |

**US_Confirmed produces more hedging than Russia_Confirmed** at T=0.7 (d = 0.37, p = 0.01). This is the only pairwise hedging comparison that reaches significance. US_Confirmed also trends higher than China_Confirmed (d = 0.29--0.33, p = 0.02--0.04) at marginal significance.

### 7.2 Pairwise Actor Tests -- Escalation at Confirmed Level

No pairwise actor comparison on escalation terms reaches significance at either temperature. The largest effect is Iran vs China at T=0.0 (d = 0.29, p = 0.048) -- marginal at best.

### 7.3 Pairwise Actor Tests -- Strong Assertions at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | Significant? |
|---|---|---|---|
| DPRK vs China | -0.348 | 0.016 | Marginal |
| China vs Russia | 0.071 | 0.62 | No |
| US vs Russia | -0.080 | 0.58 | No |
| Iran vs Russia | -0.172 | 0.23 | No |

No strong assertion pairwise comparison reaches clear significance. China_Confirmed has the highest strong assertion rate (0.10) and DPRK_Confirmed the lowest (0.02).

### 7.4 Pairwise Actor Tests -- Output Length at Confirmed Level

| Comparison | T=0.0 d | T=0.7 d | T=0.7 p |
|---|---|---|---|
| US vs Russia | -0.040 | -0.310 | 0.032 |
| Iran vs China | -0.263 | 0.013 | 0.93 |
| US vs China | -0.210 | -0.131 | 0.37 |

US_Confirmed produces marginally shorter output than Russia_Confirmed at T=0.7 (d = -0.31, p = 0.032), but the effect is weaker than llama3.1's equivalent (d = -0.41).

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
| Total CVE instances | 64 |
| CVE rate at T=0.0 | 1.9% (20/1,056) |
| CVE rate at T=0.7 | 1.9% (20/1,056) |

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
4. **The low absolute count (64 CVE instances) limits condition-level analysis.**

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

| Metric | US_Confirmed (T=0.7) | China_Confirmed (T=0.7) | Russia_Confirmed (T=0.7) |
|---|---|---|---|
| Refusal rate | 0% | 0% | 1.0% |
| Mean output (chars) | 6,350 | 6,406 | 6,490 |
| Hedge terms | 0.82 | 0.57 | 0.51 |
| Escalation terms | 0.28 | 0.24 | 0.24 |

### 13.2 Interpretation

1. **No Western-actor refusal asymmetry.** US_Confirmed has 0% refusal at both temperatures -- the opposite of llama3.1's pattern. Russia_Confirmed is the only Confirmed condition with any refusal (1 instance).
2. **US_Confirmed produces slightly more hedging** than other actors (0.82 vs 0.49--0.69 at T=0.7), reaching marginal-to-significant pairwise effects against Russia (d = 0.37, p = 0.01) and China (d = 0.29, p = 0.04).
3. **The hedging elevation is modest** (d < 0.4) compared to the certainty calibration effects (d > 1.0). The model hedges slightly more when attributing to the US but does not refuse, avoid, or truncate.
4. **Google's alignment does not exhibit the strong US-attribution sensitivity** seen in Meta's llama3.1. The hedging asymmetry may reflect training data composition rather than explicit alignment choices.

---

## 14. Non-Peer Actor Bias Audit

### 14.1 Iran and DPRK vs Peer Actors (Confirmed, T=0.0)

| Metric | Iran | DPRK | China | Russia |
|---|---|---|---|---|
| Hedge terms | 0.48 | 0.54 | 0.50 | 0.50 |
| Escalation terms | 0.35 | 0.23 | 0.19 | 0.25 |
| Strong assertions | 0.04 | 0.02 | 0.10 | 0.08 |
| Output length | 6,293 | 6,358 | 6,404 | 6,328 |

### 14.2 Key Findings

1. **Iran_Confirmed shows the highest escalation density** (0.35 at T=0.0) -- roughly 1.4x--1.8x higher than peer actors. Iran vs China escalation is marginally significant (d = 0.29, p = 0.048).
2. **DPRK is not an outlier.** Unlike llama3.1 where DPRK_Confirmed showed significantly elevated hedging (d = 0.54 vs China), gemma3n's DPRK hedging is indistinguishable from China and Russia.
3. **China_Confirmed has the highest strong assertion rate** (0.10), significantly more than DPRK_Confirmed (d = 0.35, p = 0.016). This may reflect training data composition.
4. **Non-peer actors do not receive systematically different rhetorical treatment** -- escalation and hedging patterns are broadly uniform.

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
| **Hedging calibration** | Strong and uniform (d = 1.08--1.66 across 5 actors) |
| **Escalation calibration** | Negligible (d < 0.22 for all actors) |
| **Actor symmetry (hedging)** | Good -- US_Confirmed slightly elevated (d = 0.34--0.37 vs Russia) |
| **Actor symmetry (escalation)** | Excellent -- no pairwise differences |
| **Western actor sensitivity** | Low -- no US refusal asymmetry |
| **CVE mention rate** | Low (1.9%) -- 18x lower than llama3.1 |
| **Confidence label output** | None parseable (100% Unknown) |
| **False-flag sensitivity** | Cannot assess (no parseable confidence labels) |
| **Rhetorical profile** | Balanced (E/H = 0.12--0.74) |
| **APT/MITRE references** | None (0 across entire dataset) |

---

## 17. Related Files

- [Full Research Methodology](../../docs/methodology.md) -- Full research methodology
- [Phase 2 Results (Data)](../llama31/Results_Data.md) -- Phase II quantitative results for llama3.1 (2,112 records)
- [Phase 2 Results](../llama31/Results.md) -- Phase II llama3.1 results in plain language
- [Gemma3n Results](Results.md) -- Gemma3n results in plain language
- [Phase 1 Results (Data)](../../Phase_1/Results_Data.md) -- Phase I quantitative results (1,200 records)
- [README](../../README.md) -- Project README and setup instructions
- Source data: `../../results/Phase_2/gemma3n/gemma-results.jsonl`
- Flat CSV: `../../results/Phase_2/gemma3n/gemma_results_flat.csv`
- Analysis outputs: `../../results/Phase_2/gemma3n/analysis/`
