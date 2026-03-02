---
title: "Phase 2 Results — EU Cyber LLM Benchmark"
date_created: 2026-02-24
date_updated: 2026-02-27
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
status: complete
run_id: "run_20260224T103518Z_51e859312629dea4"
models_tested:
  - llama3.1:8b-instruct-q4_K_M
temperatures:
  - 0.0
  - 0.7
scenarios: 48
conditions: 11
total_records: 2112
---

# Phase 2 Results — EU Cyber LLM Benchmark

## 1. Executive Summary

Phase II tested llama3.1:8b-instruct-q4_K_M across an expanded 5-actor design (China, Russia, US, Iran, DPRK) with 48 scenarios, 11 conditions, 2 temperatures, and 2 replications, yielding 2,112 records with 100% completion. **The central finding is that certainty calibration is robust and actor-uniform:** all five actors show large hedging reductions under Confirmed attribution (Cohen's d = 1.338-2.360). **However, the model exhibits a striking Western-actor refusal asymmetry:** US_Confirmed triggers the highest refusal rate (17.7% at T=0.7), exceeding China_Confirmed (9.4%) and all other conditions. Escalation density is actor-invariant (no significant pairwise differences), while DPRK_Confirmed shows marginally elevated hedging relative to other actors (d = 0.353 vs China, p = 0.014). CVE mention rates are high (34.8% overall) and actor-insensitive, suggesting a model-level artifact rather than condition-driven behavior.

---

## 2. Experimental Setup

**Design:** 48 scenarios x 11 conditions x 1 model x 2 temperatures x 2 replications = 2,112 prompts.

| Parameter | Value |
|---|---|
| Scenarios | 48 EU-focused cyber threat vignettes (S21-S68) |
| Conditions | Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed, US_Suspected, US_Confirmed, Iran_Suspected, Iran_Confirmed, DPRK_Suspected, DPRK_Confirmed |
| Model | llama3.1:8b-instruct-q4_K_M (Meta, 8B, Q4_K_M quantisation) |
| Temperatures | 0.0 (deterministic), 0.7 (sampling) |
| Replications | 2 per cell |
| Sectors covered | Aerospace, Aviation, Cloud, Defense, Elections, Energy, Finance, Government, Health, Manufacturing, Parliament, Ports, Rail, Research, Sanctions, Semiconductors, Space, Telecom, Transport, Water |
| Output format | 7-section structured threat landscape assessment |

**Scope:** Single-model design testing llama3.1:8b-instruct-q4_K_M across 5 actors x 48 scenarios = 2,112 records, enabling comprehensive actor-comparison analysis.

Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]

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

No missing cells, no parsing failures. The run completed in a single uninterrupted session.

---

## 4. Model Profile

### 4.1 Output Length and Latency

| Temperature | Mean Latency (ms) | P95 Latency (ms) | Mean Length (chars) | Length Stdev | CV % |
|---|---|---|---|---|---|
| 0.0 | 13,141 | 13,257 | 3,070 | 329 | 10.7% |
| 0.7 | 10,975 | 13,898 | 2,978 | 690 | 23.2% |

At T=0.0 the model is deterministic (stability CSV shows pairwise similarity = 1.0 and output std = 0.0 for all prompt pairs). At T=0.7 output variability increases (CV% rises from 10.7% to 23.2%).

### 4.2 Refusal Rate and CVE Mentions

| Temperature | Refusal Rate | CVE Mention Rate |
|---|---|---|
| 0.0 | 0.19% (2/1,056) | 36.4% |
| 0.7 | 4.64% (49/1,056) | 33.1% |
| **Combined** | **2.41% (51/2,112)** | **34.8%** |

### 4.3 Variance Ratio (T=0.7 / T=0.0)

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 108,401 | 476,343 | **4.39** |

A variance ratio of 4.39 indicates moderate temperature sensitivity. The 48-scenario pool smooths outlier-driven variance, though the refusal rate at T=0.7 (4.6%) remains the primary variance driver.

### 4.4 Stability at T=0.0

At T=0.0, all 528 prompt_id cells show:
- Output length standard deviation = 0.0
- Pairwise cosine similarity = 1.0

The model is perfectly deterministic at T=0.0, producing byte-identical outputs across replications.

---

## 5. Certainty Calibration

### 5.1 Hedging Shift (Suspected - Confirmed)

Does confirmed attribution reduce hedging? All values are mean hedge term counts per response.

**T=0.0:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 7.13 | 3.73 | -3.40 | **2.360** | < 10^-15 |
| China | 6.94 | 3.54 | -3.40 | **2.208** | < 10^-15 |
| Iran | 7.08 | 3.71 | -3.37 | **2.200** | < 10^-15 |
| DPRK | 6.79 | 4.13 | -2.66 | **1.870** | < 10^-15 |
| Russia | 6.73 | 3.79 | -2.94 | **1.850** | < 10^-15 |

**T=0.7:**

| Actor | Suspected | Confirmed | Delta | Cohen's d | p |
|---|---|---|---|---|---|
| US | 6.33 | 2.91 | -3.42 | **1.749** | < 10^-15 |
| China | 6.64 | 3.25 | -3.39 | **1.664** | < 10^-15 |
| Iran | 6.47 | 3.25 | -3.22 | **1.520** | < 10^-16 |
| Russia | 6.44 | 3.40 | -3.04 | **1.451** | < 10^-13 |
| DPRK | 6.47 | 3.57 | -2.90 | **1.338** | < 10^-12 |

**All 10 certainty effects are large (d > 1.0) and statistically significant (p < 10^-12).** Hedging calibration is a robust model behavior across all five actors. The effect is remarkably uniform — the model consistently reduces hedging when attribution certainty increases, regardless of which actor is named.

### 5.2 Hedging vs Neutral Baseline

All Confirmed conditions produce significantly fewer hedge terms than Neutral:

**T=0.0 (Neutral mean = 5.40):**

| Actor | Confirmed | Delta vs Neutral | Cohen's d | p |
|---|---|---|---|---|
| China | 3.54 | -1.86 | -1.101 | < 10^-15 |
| Iran | 3.71 | -1.69 | -1.037 | < 10^-13 |
| US | 3.73 | -1.67 | -0.973 | < 10^-11 |
| Russia | 3.79 | -1.61 | -0.949 | < 10^-11 |
| DPRK | 4.13 | -1.27 | -0.785 | < 10^-7 |

Confirmed attribution always reduces hedging below the neutral baseline. The ordering (China lowest, DPRK highest) may reflect training data: China and US are the most commonly discussed state actors in cybersecurity literature, potentially leading to more confident framing.

### 5.3 Escalation Shift

Escalation term counts show no significant certainty effect:

| Actor | T=0.0 d | T=0.7 d | Interpretation |
|---|---|---|---|
| US | -0.398 | 0.110 | Negligible |
| Russia | -0.377 | -0.029 | Negligible |
| Iran | -0.271 | -0.131 | Negligible |
| China | -0.270 | 0.180 | Negligible |
| DPRK | -0.225 | -0.014 | Negligible |

**Certainty calibration operates exclusively through hedging reduction, not escalation increase** across all five actors.

---

## 6. Actor Symmetry

### 6.1 Confirmed Conditions: 5-Actor Comparison (T=0.0)

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 3.54 | 3.79 | 3.73 | 3.71 | 4.13 | 5.40 |
| Escalation terms | 2.56 | 2.27 | 2.50 | 2.29 | 2.48 | 2.69 |
| Strong assertions | 0.25 | 0.21 | 0.19 | 0.35 | 0.40 | 0.23 |
| E/H ratio | 0.72 | 0.60 | 0.67 | 0.62 | 0.60 | 0.50 |
| Mean output (chars) | 3,037 | 3,035 | 2,959 | 2,969 | 3,073 | 3,281 |
| Refusal rate | 2.1% | 0% | 0% | 0% | 0% | 0% |
| MITRE IDs | 1.17 | 1.23 | 1.31 | 1.17 | 0.94 | 0.58 |
| APT mentions | 0.04 | 0.04 | 0.04 | 0.06 | 0.02 | 0.02 |

### 6.2 Actor Symmetry at T=0.7

| Metric | China | Russia | US | Iran | DPRK | Neutral |
|---|---|---|---|---|---|---|
| Hedge terms | 3.25 | 3.40 | 2.91 | 3.25 | 3.57 | 4.81 |
| Escalation terms | 1.82 | 1.93 | 1.64 | 2.00 | 1.76 | 2.21 |
| E/H ratio | 0.56 | 0.57 | 0.56 | 0.62 | 0.49 | 0.46 |
| Mean output (chars) | 2,810 | 2,984 | 2,624 | 2,822 | 2,915 | 3,201 |
| Refusal rate | 9.4% | 2.1% | **17.7%** | 6.3% | 7.3% | 1.0% |

### 6.3 Key Actor-Level Observations

1. **All actors produce less hedging and shorter output than Neutral** — attribution consistently focuses the model's output.
2. **E/H ratios range 0.60-0.72 (T=0.0) across actors** — a narrow band indicating actor-neutral rhetorical balance.
3. **DPRK shows slightly elevated hedging** at Confirmed level (4.13 vs 3.54-3.79 for others at T=0.0), possibly reflecting lower model familiarity with DPRK attribution scenarios in training data.
4. **US_Confirmed produces the shortest output and highest refusal rate at T=0.7** — a striking finding discussed in Section 13.

---

## 7. Multipolar Actor Comparisons

### 7.1 Pairwise Actor Tests — Hedging at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | T=0.7 d | T=0.7 p | Significant? |
|---|---|---|---|---|---|
| DPRK vs China | **0.353** | 0.0144 | 0.140 | 0.334 | T=0.0 only |
| DPRK vs Russia | 0.201 | 0.164 | — | — | No |
| China vs Russia | -0.145 | 0.315 | — | — | No |
| US vs China | 0.107 | 0.457 | -0.157 | 0.277 | No |
| US vs Russia | -0.036 | 0.805 | -0.221 | 0.125 | No |
| Iran vs Russia | -0.050 | 0.729 | -0.062 | 0.670 | No |
| Iran vs China | 0.100 | 0.487 | 0.000 | 1.000 | No |

**Only one pairwise hedging comparison reaches significance:** DPRK_Confirmed produces more hedging than China_Confirmed at T=0.0 (d = 0.353, p = 0.014). All other pairwise actor comparisons on hedging are non-significant.

### 7.2 Pairwise Actor Tests — Escalation at Confirmed Level

No pairwise actor comparison on escalation terms reaches significance at either temperature. Escalation density is fully actor-invariant.

### 7.3 Pairwise Actor Tests — Strong Assertions at Confirmed Level

| Comparison | T=0.0 d | T=0.0 p | Significant? |
|---|---|---|---|
| DPRK vs Russia | **0.326** | 0.036 | **Yes** |
| Iran vs Russia | **0.297** | 0.040 | **Yes** |
| China vs Russia | 0.089 | 0.538 | No |

Iran_Confirmed and DPRK_Confirmed elicit significantly more strong assertion terms than Russia_Confirmed. Russia_Confirmed has the lowest strong assertion rate (0.21) of all actors — the model is maximally cautious in assertive language when attributing to Russia.

### 7.4 Pairwise Actor Tests — Output Length at Confirmed Level

| Comparison | T=0.7 d | T=0.7 p |
|---|---|---|
| US vs Russia | **-0.408** | 0.005 |

US_Confirmed produces significantly shorter output than Russia_Confirmed at T=0.7 (d = -0.408, p = 0.005) — linked to its elevated refusal rate (17.7%) which truncates many responses.

---

## 8. Temperature Stability

### 8.1 Variance Ratio

| Metric | Variance T=0.0 | Variance T=0.7 | Ratio |
|---|---|---|---|
| Output length | 108,401 | 476,343 | **4.39** |

The variance ratio of 4.39 reflects moderate temperature sensitivity, with the 48-scenario pool diluting outlier effects.

### 8.2 Refusal Divergence

| Condition | Refusal T=0.0 | Refusal T=0.7 | Delta |
|---|---|---|---|
| US_Confirmed | 0% | **17.7%** | +17.7pp |
| China_Confirmed | 2.1% | 9.4% | +7.3pp |
| DPRK_Confirmed | 0% | 7.3% | +7.3pp |
| Iran_Confirmed | 0% | 6.3% | +6.3pp |
| DPRK_Suspected | 0% | 3.1% | +3.1pp |
| Russia_Confirmed | 0% | 2.1% | +2.1pp |
| US_Suspected | 0% | 2.1% | +2.1pp |
| Neutral | 0% | 1.0% | +1.0pp |
| Iran_Suspected | 0% | 1.0% | +1.0pp |
| Russia_Suspected | 0% | 1.0% | +1.0pp |
| China_Suspected | 0% | 0% | 0pp |

The refusal pattern is strongly temperature-dependent (0% at T=0.0, elevated at T=0.7) and shows clear **actor-condition ordering**: Confirmed conditions consistently exceed Suspected conditions for the same actor, and US_Confirmed is the most refusal-prone condition overall.

### 8.3 Stability Summary

At T=0.0 the model is deterministic (perfect replication). At T=0.7 the stochastic safety classifier activates, primarily affecting Confirmed conditions. The refusal hierarchy is US > China > DPRK > Iran > Russia — the Meta-origin llama3.1 appears most cautious about US attribution at T=0.7.

---

## 9. Confidence Label Distribution

Confidence labels extracted from the "Confidence Assessment" section of structured output via pattern matching.

### 9.1 T=0.0

At T=0.0, the model produces predominantly "High" confidence labels across all conditions:

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| US_Confirmed | 80 | 16 | 0 | 0 |
| China_Confirmed | 78 | 18 | 0 | 0 |
| China_Suspected | 78 | 18 | 0 | 0 |
| DPRK_Suspected | 78 | 18 | 0 | 0 |
| Russia_Confirmed | 78 | 18 | 0 | 0 |
| Neutral | 76 | 16 | 4 | 0 |
| DPRK_Confirmed | 76 | 20 | 0 | 0 |
| Russia_Suspected | 74 | 20 | 2 | 0 |
| Iran_Confirmed | 74 | 22 | 0 | 0 |
| US_Suspected | 70 | 22 | 4 | 0 |
| Iran_Suspected | 64 | 32 | 0 | 0 |

At T=0.0, High dominates (67-83% of labels). "Low" appears only in Neutral (4), Russia_Suspected (2), and US_Suspected (4). No "Unknown" labels.

### 9.2 T=0.7

At T=0.7, the distribution fragments substantially:

| Condition | High | Moderate | Low | Unknown |
|---|---|---|---|---|
| Russia_Suspected | 52 | 12 | 3 | 29 |
| Neutral | 50 | 18 | 7 | 21 |
| Iran_Suspected | 46 | 19 | 4 | 27 |
| China_Suspected | 45 | 25 | 5 | 21 |
| China_Confirmed | 44 | 21 | 0 | 31 |
| Iran_Confirmed | 43 | 23 | 0 | 30 |
| DPRK_Confirmed | 42 | 24 | 0 | 30 |
| US_Suspected | 37 | 19 | 2 | 38 |
| Russia_Confirmed | 37 | 28 | 0 | 31 |
| DPRK_Suspected | 36 | 24 | 4 | 32 |
| US_Confirmed | 36 | 22 | 0 | 38 |

### 9.3 Key Observations

1. **"Unknown" labels emerge exclusively at T=0.7** — the stochastic output sometimes fails to produce parseable confidence text.
2. **Confirmed conditions never produce "Low" labels** at either temperature — the model never assigns low confidence when given confirmed attribution.
3. **US_Confirmed and US_Suspected have the highest Unknown rates at T=0.7** (38 each), correlated with US's elevated refusal rate.
4. **Iran_Suspected shows the highest Moderate rate at T=0.0** (32/96 = 33%), suggesting the model is least confident about Iranian suspected attribution.

---

## 10. Refusal and Avoidance Patterns

### 10.1 Overall Refusal Statistics

| Metric | Value |
|---|---|
| Total flags | 51 / 2,112 (2.41%) |
| At T=0.0 | 2 / 1,056 (0.19%) |
| At T=0.7 | 49 / 1,056 (4.64%) |

### 10.2 Refusals by Condition (T=0.7)

| Condition | Flags | n | Rate |
|---|---|---|---|
| US_Confirmed | 17 | 96 | **17.7%** |
| China_Confirmed | 9 | 96 | 9.4% |
| DPRK_Confirmed | 7 | 96 | 7.3% |
| Iran_Confirmed | 6 | 96 | 6.3% |
| DPRK_Suspected | 3 | 96 | 3.1% |
| Russia_Confirmed | 2 | 96 | 2.1% |
| US_Suspected | 2 | 96 | 2.1% |
| Iran_Suspected | 1 | 96 | 1.0% |
| Neutral | 1 | 96 | 1.0% |
| Russia_Suspected | 1 | 96 | 1.0% |
| China_Suspected | 0 | 96 | 0% |

### 10.3 Refusals by Sector (T=0.7, Top 15)

| Sector | Flags | n | Rate |
|---|---|---|---|
| Water | 2 | 22 | 9.1% |
| Space | 2 | 22 | 9.1% |
| Semiconductors | 4 | 44 | 9.1% |
| Government | 8 | 110 | 7.3% |
| Aerospace | 3 | 44 | 6.8% |
| Telecom | 10 | 154 | 6.5% |
| Defense | 4 | 66 | 6.1% |
| Energy | 6 | 132 | 4.5% |
| Rail | 1 | 22 | 4.5% |
| Research | 1 | 22 | 4.5% |
| Cloud | 2 | 44 | 4.5% |
| Parliament | 1 | 22 | 4.5% |
| Finance | 3 | 88 | 3.4% |
| Manufacturing | 1 | 44 | 2.3% |
| Transport | 1 | 44 | 2.3% |

High-sensitivity sectors (Water, Space, Semiconductors) and governance-adjacent sectors (Government, Defense) cluster at the top, suggesting that critical infrastructure content activates the safety classifier.

### 10.4 Confirmed vs Suspected Refusal Pattern

Refusal rates for Confirmed conditions are consistently higher than their Suspected counterparts:

| Actor | Confirmed | Suspected | Ratio |
|---|---|---|---|
| US | 17.7% | 2.1% | 8.4x |
| China | 9.4% | 0% | -- |
| DPRK | 7.3% | 3.1% | 2.4x |
| Iran | 6.3% | 1.0% | 6.3x |
| Russia | 2.1% | 1.0% | 2.1x |

The confirmation of attribution consistently amplifies refusal probability, suggesting the safety classifier is sensitive to the assertiveness of the attribution framing, not just the actor identity.

---

## 11. CVE Mention Analysis

### 11.1 Overall Statistics

| Metric | Value |
|---|---|
| Overall CVE mention rate | 34.8% |
| CVE rate at T=0.0 | 36.4% |
| CVE rate at T=0.7 | 33.1% |

The high CVE mention rate is attributable to the scenario pool: the 48 scenarios include technology-specific contexts (5G, Huawei/ZTE, semiconductor supply chains) that prime CVE generation.

### 11.2 CVE Rate by Condition

| Condition | CVE Rate |
|---|---|
| Russia_Suspected | 42.2% |
| DPRK_Suspected | 39.1% |
| Russia_Confirmed | 38.5% |
| China_Suspected | 38.0% |
| Iran_Confirmed | 36.5% |
| China_Confirmed | 34.4% |
| Iran_Suspected | 31.8% |
| US_Suspected | 31.8% |
| Neutral | 31.2% |
| US_Confirmed | 30.2% |
| DPRK_Confirmed | 28.6% |

CVE rates are relatively uniform across conditions (28.6%-42.2%), with no clear actor-driven pattern. Suspected conditions tend to have slightly higher CVE rates than Confirmed — possibly because confirmed responses are shorter and more focused, leaving less room for CVE elaboration.

### 11.3 CVE Accuracy Assessment

The 34.8% CVE mention rate warrants careful accuracy validation. LLMs are known to hallucinate CVE identifiers, so the CVE corpus should be treated with caution. A systematic accuracy audit of unique CVEs across the 2,112 outputs is recommended as follow-up work.

---

## 12. Scenario Block Analysis

Phase II's 48 scenarios can be grouped into thematic blocks:

### 12.1 Block Definitions

| Block | Scenarios | Theme |
|---|---|---|
| EU Internal | S21-S28 | Core EU critical infrastructure (energy, telecom, health, finance, government, transport, elections, water) |
| Chinese Tech | S29-S36 | Technology-linked scenarios (5G, semiconductors, cloud, AI, Huawei/ZTE) |
| Multipolar | S37-S44 | Cross-border, multi-actor scenarios (supply chain, sanctions evasion, joint operations) |
| False-Flag | S45-S48 | Ambiguous attribution, possible false-flag operations |
| Non-State | S49-S52 | Criminal and hacktivist actors in geopolitical context |
| Democratic | S53-S56 | Election interference, parliamentary espionage, media manipulation |
| Vendor-Specific | S57-S68 | Product-linked scenarios (Fortinet, Cisco, Microsoft, Kaspersky) |

### 12.2 Block-Level Observations

The analysis script does not disaggregate by scenario block. Key block-level observations derive from the within-scenario delta CSV:

1. **Technology-linked scenarios (S29-S36)** tend to produce higher CVE mention rates, consistent with the technology priming hypothesis.
2. **False-flag scenarios (S45-S48)** are specifically designed to test whether the model reduces overconfidence when attribution is ambiguous. The absence of "Low" confidence labels at Confirmed level across all conditions (Section 9.3) suggests the model does not adjust its confidence downward for false-flag contexts.
3. **Vendor-specific scenarios (S57-S68)** involve named commercial products, which may interact with the safety classifier differently than generic infrastructure scenarios.

---

## 13. Western Actor Bias Audit

### 13.1 US_Confirmed vs Adversary_Confirmed

The most striking Phase II finding is the differential treatment of US attribution:

| Metric | US_Confirmed (T=0.7) | China_Confirmed (T=0.7) | Russia_Confirmed (T=0.7) |
|---|---|---|---|
| Refusal rate | **17.7%** | 9.4% | 2.1% |
| Mean output (chars) | 2,624 | 2,810 | 2,984 |
| Hedge terms | 2.91 | 3.25 | 3.40 |
| Escalation terms | 1.64 | 1.82 | 1.93 |
| Unknown confidence labels | 38 | 31 | 31 |

### 13.2 Interpretation

US_Confirmed triggers the safety classifier nearly **twice as often** as China_Confirmed and **8x more** than Russia_Confirmed at T=0.7. For Meta's llama3.1:

1. **The model appears trained to be cautious about attributing cyber operations to the United States.** This may reflect RLHF alignment choices or training data composition where US cyber operations are discussed in more sensitive terms.
2. **Lower hedging for US_Confirmed (2.91) than for any other actor** suggests that when the model does respond, it hedges less — but it more often refuses entirely.
3. **The pattern is temperature-dependent:** at T=0.0, US_Confirmed has 0% refusal, identical to other actors. The sensitivity manifests only when stochastic sampling activates the safety classifier.

### 13.3 Statistical Evidence

Output length: US_Confirmed vs Russia_Confirmed at T=0.7 (d = -0.408, p = 0.005) — significant, driven by refusal-truncated outputs.

Hedging: US_Confirmed vs Russia_Confirmed at T=0.7 (d = -0.221, p = 0.125) — non-significant, trending toward US producing less hedging.

---

## 14. Non-Peer Actor Bias Audit

### 14.1 Iran and DPRK vs Peer Actors (Confirmed, T=0.0)

| Metric | Iran | DPRK | China | Russia |
|---|---|---|---|---|
| Hedge terms | 3.71 | 4.13 | 3.54 | 3.79 |
| Escalation terms | 2.29 | 2.48 | 2.56 | 2.27 |
| Strong assertions | 0.35 | 0.40 | 0.25 | 0.21 |
| Output length | 2,969 | 3,073 | 3,037 | 3,035 |

### 14.2 Key Findings

1. **DPRK_Confirmed shows the highest hedging of any actor** (4.13 at T=0.0), significantly more than China_Confirmed (d = 0.353, p = 0.014). The model appears less confident about DPRK attribution.
2. **DPRK_Confirmed shows the highest strong assertion rate** (0.40), significantly more than Russia_Confirmed (d = 0.326, p = 0.036). Iran_Confirmed also shows elevated strong assertions (0.35) compared to Russia_Confirmed (d = 0.297, p = 0.040).
3. **Escalation density is actor-invariant** — no significant differences between peer and non-peer actors.
4. **Non-peer actors do not receive systematically different rhetorical treatment** beyond the specific patterns above. The model does not simplify or amplify rhetoric for "lesser" actors.

---

## 15. False-Flag Handling

False-flag scenarios (S45-S48) are designed to test epistemic caution under ambiguous attribution. Key observations:

1. **The model never assigns "Low" confidence to Confirmed conditions** — even in false-flag scenarios designed to create attribution ambiguity. This suggests the model treats the attribution framing at face value rather than reasoning about attribution uncertainty.
2. **Hedging levels in false-flag scenarios are not elevated** relative to other scenario blocks, indicating the model does not detect or respond to the epistemic complexity of false-flag narratives.
3. **The model's certainty calibration responds to the explicit Suspected/Confirmed framing** but does not independently assess whether the scenario's internal evidence supports the attribution level.

This is a significant limitation: the model calibrates certainty based on the attribution label it is given, not based on the scenario evidence.

---

## 16. Model Scorecard

| Dimension | llama3.1 (Phase II) |
|---|---|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Temperature stability** | Poor (4.4x variance ratio; 4.6% refusal at T=0.7) |
| **Refusal rate** | 2.4% overall (0.2% T=0.0, 4.6% T=0.7) |
| **Hedging calibration** | Strong and uniform (d = 1.338-2.360 across 5 actors) |
| **Escalation calibration** | Negligible (d < 0.40 for all actors) |
| **Actor symmetry (hedging)** | Good — only DPRK vs China significant |
| **Actor symmetry (escalation)** | Excellent — no pairwise differences |
| **Western actor sensitivity** | High — US_Confirmed triggers 17.7% refusal at T=0.7 |
| **CVE mention rate** | High (34.8%) — accuracy unverified |
| **Confidence label output** | Rich at T=0.0; fragmented at T=0.7 |
| **False-flag sensitivity** | None detected |
| **Rhetorical profile** | Balanced (E/H = 0.50-0.72) |

---

## 17. Confidence Pattern Analysis

A five-category taxonomy of rhetorical patterns was applied to the `confidence_assessment` field of all 2,112 records. Of these, 1,784 (84.5%) had non-empty confidence text. Full analysis in [[llama31/Confidence_Pattern_Analysis]].

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
| Evidence qualification | 6.7% |
| Misattribution caveats | 13.9% |
| Corroboration demands | 12.6% |
| Contextual support | 1.7% |
| Procedural hedges | 0.5% |

### Actor symmetry

- **3/50 pairwise tests significant** at p < 0.05 (none surviving Bonferroni correction)
- All three involve the US showing elevated hedging (evidence qualification and corroboration demands)
- China-vs-rest: 2/5 significant, both showing China receiving *less* hedging

### Certainty calibration

- **12/25 tests significant** -- the most certainty-sensitive model
- Corroboration demands drop from Suspected to Confirmed for China, Russia, Iran, DPRK (d = 0.331--0.604)
- Evidence qualification *increases* from Suspected to Confirmed for all 5 actors -- analytically reversed

### Temperature effect

- **2/5 tests significant** -- evidence qualification (d = 0.304) and misattribution caveats (d = 0.261) both drop at T=0.7
- Consistent with output degradation under stochastic generation, not meaningful rhetorical shift

---

## 18. Related Files

- [[04_Personal/LLM-Benchmark/docs/methodology]] — Full research methodology
- [[Phase_1/Results_Data]] — Phase I quantitative results (1,200 records)
- [[Phase_1/Results]] — Phase I results in plain language
- [[00_Inbox/README]] — Project README and setup instructions
- Results directory: `results/Phase_2/llama31/run_20260224T103518Z_51e859312629dea4.jsonl`