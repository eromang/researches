---
title: "Confidence Pattern Analysis — hoangquan456/qwen3-nothink:8b"
date: 2026-02-28
model: "hoangquan456/qwen3-nothink:8b"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/qwen3-nothink
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note defines a five-category taxonomy of rhetorical patterns found in hoangquan456/qwen3-nothink:8b confidence assessments and measures whether those patterns differ by attributed actor or are applied uniformly.

## Motivation

The [[qwen3-nothink/Results_Data]] tested quantitative performance metrics across actors and certainty levels. That analysis focused on accuracy scores and calibration, not on the rhetorical structure of confidence assessments. This analysis builds a broader taxonomy of rhetorical pattern *types* and detects them at the category level across all 2,112 ok records, enabling direct comparison with [[qwen3-thinking/Confidence_Pattern_Analysis]], [[deepseek-r1/Confidence_Pattern_Analysis]], and the [[Cross_Model_Confidence_Patterns]] synthesis.

## Pattern taxonomy

Five categories of rhetorical patterns, each detected via regex over the `confidence_assessment` field:

### Category 1: Evidence-qualification hedges

Statements that the evidence is insufficient for definitive attribution.

| Pattern | Example |
|---------|---------|
| definitive attribution requires... | "definitive attribution requires further corroboration" |
| attribution remains probabilistic | "attribution remains probabilistic" |
| absence of direct attribution | "the absence of direct attribution sources..." |
| reliance on indirect indicators | "reliance on indirect indicators" |
| circumstantial evidence | "circumstantial evidence" |
| definitive proof remains... | "definitive proof remains elusive" |

### Category 2: Misattribution / alternative-explanation caveats

Warnings about false attribution or alternative actors.

| Pattern | Example |
|---------|---------|
| potential for misattribution | "potential for misattribution" |
| alternative explanations | "alternative explanations cannot be excluded" |
| cannot be ruled out | "cannot be ruled out" |
| false flag | "false flag operations" |
| false positive | "false positives in attribution" |
| planted evidence | "planted evidence" |

### Category 3: Corroboration demands

Calls for further analysis or independent verification.

| Pattern | Example |
|---------|---------|
| further corroboration | "further corroboration is required" |
| further analysis | "further analysis of digital artifacts" |
| further investigation | "further investigation needed" |
| independent verification | "independent verification" |
| additional intelligence | "additional intelligence sources" |
| corroborated by | "corroborated by multiple sources" |

### Category 4: Contextual-support appeals

Statements that geopolitical context supports but does not prove attribution.

| Pattern | Example |
|---------|---------|
| geopolitical context | "geopolitical context supports the assessment" |
| historical patterns | "historical patterns of state-sponsored activity" |
| consistent with known... | "consistent with known TTPs" |
| aligns with capabilities | "aligns with known capabilities" |
| does not replace concrete | "does not replace concrete evidence" |

### Category 5: Procedural hedges

Generic analytical caution about process.

| Pattern | Example |
|---------|---------|
| further analysis to rule out | "further analysis to rule out alternative actors" |
| ongoing monitoring | "ongoing monitoring recommended" |
| reassessment | "reassessment may be needed" |
| pending additional | "pending additional intelligence" |
| subject to revision | "subject to revision" |

## Detection rates by actor and certainty level

All temperatures combined, binary detection (at least one pattern in category matched).

| Actor | Level | N | Evidence qual. | Misattribution | Corroboration | Contextual | Procedural |
|-------|-------|---|---|---|---|---|---|
| China | Confirmed | 192 | 12.0% | 8.3% | 20.8% | 24.0% | 0.0% |
| China | Suspected | 192 | 5.2% | 6.2% | 25.0% | 19.3% | 0.0% |
| DPRK | Confirmed | 192 | 7.3% | 4.7% | 16.7% | 25.0% | 0.0% |
| DPRK | Suspected | 192 | 5.2% | 7.8% | 24.5% | 10.4% | 0.0% |
| Iran | Confirmed | 192 | 12.5% | 7.3% | 20.3% | 13.0% | 0.0% |
| Iran | Suspected | 192 | 3.1% | 5.7% | 26.6% | 14.1% | 0.0% |
| Russia | Confirmed | 192 | 10.4% | 9.4% | 13.0% | 21.9% | 0.0% |
| Russia | Suspected | 192 | 3.6% | 6.2% | 28.1% | 15.6% | 0.0% |
| US | Confirmed | 192 | 5.2% | 6.2% | 19.3% | 15.6% | 0.0% |
| US | Suspected | 192 | 1.0% | 11.5% | 27.1% | 17.7% | 0.0% |

Key observations:

- **Corroboration demands** are the dominant category (13–28% depending on actor and level), replacing the contextual-support dominance seen in deepseek-r1 and qwen3-thinking
- **Contextual-support appeals** are notably lower than other models (10–25% vs 40–65% in deepseek-r1), indicating a different rhetorical profile
- **Evidence-qualification hedges** are higher at Confirmed level than Suspected for most actors — an inverted pattern relative to deepseek-r1 and qwen3-thinking
- **Procedural hedges** are exactly 0.0% across all conditions — the most extreme absence of any model tested
- **Misattribution caveats** are low and stable across actors and levels (4.7–11.5%)

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 8 out of 50 tests significant at p < 0.05.**

Significant pairs:

| Actor pair | Category | d | p |
|------------|----------|---|---|
| China vs Russia | Corroboration demands | 0.209 | 0.0406 |
| China vs US | Evidence qualification | 0.243 | 0.0174 |
| China vs US | Contextual support | 0.210 | 0.0399 |
| China vs Iran | Contextual support | 0.284 | 0.0054 |
| Russia vs Iran | Contextual support | 0.234 | 0.0217 |
| US vs Iran | Evidence qualification | -0.258 | 0.0114 |
| US vs DPRK | Contextual support | -0.234 | 0.0219 |
| Iran vs DPRK | Contextual support | -0.308 | 0.0025 |

This is a substantially higher rate of actor differentiation than deepseek-r1 (1/50) and qwen3-thinking (1/50). The significant pairs cluster around contextual support (4 pairs) and evidence qualification (2 pairs), suggesting the model applies these two categories with moderate actor-sensitivity. However, most effect sizes are in the small-to-medium range (d = 0.209–0.308), and several would not survive Bonferroni correction (threshold = 0.001 for 50 tests). The Iran vs DPRK contextual-support pair (d = -0.308, p = 0.0025) is the strongest result and would survive correction.

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

**0 out of 5 significant. No China-protective framing detected.**

Despite China appearing in 3 of the 8 significant pairwise results, the one-vs-rest test shows no systematic China-specific treatment. China's pairwise differences are distributed across multiple categories and reflect general inter-actor variance rather than a targeted bias pattern.

## Certainty calibration

Suspected vs Confirmed shift per actor and category (6 of 25 tests significant):

| Pattern | Significant actors | Direction | d | p |
|---------|-------------------|-----------|---|---|
| Evidence qualification | China | Confirmed > Suspected | -0.243 | significant |
| Evidence qualification | Russia | Confirmed > Suspected | -0.267 | significant |
| Evidence qualification | US | Confirmed > Suspected | -0.241 | significant |
| Evidence qualification | Iran | Confirmed > Suspected | -0.354 | significant |
| Corroboration demands | Russia | Suspected > Confirmed | 0.379 | 0.0002 |
| Contextual support | DPRK | Confirmed > Suspected | -0.388 | 0.0001 |

This is a weaker calibration signal than deepseek-r1 (13/25 significant) and comparable to qwen3-thinking (7/25 significant).

Notably, the **evidence-qualification hedges show an inverted direction** for four actors: they are *higher* at Confirmed than Suspected. This is the opposite of deepseek-r1 and qwen3-thinking, where evidence hedging consistently increases with uncertainty. The model applies more evidence-qualifying language when attribution is confirmed, which may reflect a rhetorical pattern of emphasizing evidentiary rigor even at higher certainty rather than genuine uncertainty calibration.

Russia's corroboration demand shift (d = 0.379) is the only category showing the expected Suspected > Confirmed direction. DPRK's contextual-support shift is inverted (Confirmed > Suspected, d = -0.388).

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

**1 out of 5 significant: misattribution caveats (d = 0.153, p = 0.0174).**

Temperature has minimal effect on rhetorical patterns, consistent with all other models tested. The single significant result on misattribution caveats reflects a modest increase at one temperature setting, but the effect size is small.

## N-gram discovery

The top distinctive n-grams in qwen3-nothink confidence assessments reveal a characteristic vocabulary:

| N-gram | Detection rate |
|--------|---------------|
| geopolitical implications | 83.5% |
| defensive priorities | 79.5% |
| attribution confidence | 78.5% |
| confidence moderate | 74.6% |
| confidence high | 74.4% |
| priorities confidence | 71.3% |
| defensive priorities confidence | 71.3% |
| linked actors | 68.5% |

The **"defensive priorities" cluster** (defensive priorities, priorities confidence, defensive priorities confidence) is distinctive to qwen3-nothink and does not appear in other models' top n-grams. This suggests a model-specific rhetorical tendency to frame confidence assessments in terms of defensive posture rather than pure analytical hedging.

## Conclusions

1. **Moderate actor differentiation.** 8 of 50 pairwise tests are significant — substantially higher than qwen3-thinking (1/50) and deepseek-r1 (1/50). Removing the thinking/reasoning layer appears to reduce the uniformity of confidence rhetoric across actors. The model applies contextual support and evidence qualification with measurable actor-sensitivity, though most effects are small.

2. **No China-protective framing.** 0 of 5 China-vs-rest tests are significant. Despite China appearing in several pairwise results, there is no systematic pattern of differential treatment for China at the one-vs-rest level.

3. **Weaker certainty calibration at category level.** 6 of 25 Suspected vs Confirmed tests are significant, compared to deepseek-r1's 13/25 and qwen3-thinking's 7/25. More critically, the direction of evidence-qualification shifts is inverted (Confirmed > Suspected for four actors), suggesting the model does not consistently increase hedging with uncertainty. This is a qualitative calibration deficit.

4. **Procedural hedges are zero across all conditions.** This is the most extreme absence of procedural hedging in any model tested. The 0.0% rate across all 20 actor-level cells (compared to 0–2.1% in deepseek-r1 and 0–0.5% in qwen3-thinking) suggests the model's vocabulary entirely lacks process-oriented analytical language.

5. **"Defensive priorities" n-gram cluster is distinctive.** The model's unique vocabulary marker is the "defensive priorities" family of n-grams (79.5% detection rate), which does not appear in the top n-grams of any other tested model. This reflects a model-specific tendency to frame assessments through a defensive-posture lens.

6. **Removing thinking reduces actor uniformity in confidence rhetoric.** Comparing qwen3-nothink (8/50 significant pairwise) to qwen3-thinking (1/50 significant pairwise), the removal of the thinking/chain-of-thought layer correlates with increased inter-actor variance in rhetorical patterns. The thinking layer appears to act as a normalizing mechanism that produces more uniform rhetoric across actors.

See [[Cross_Model_Confidence_Patterns]] for cross-model comparison across deepseek-r1:8b, qwen3:8b, gemma3n, and llama3.1.

## Data sources

- Input: `results/Phase_2/qwen3-nothink/qwen3-nothink_flat.csv` (2,112 ok records)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/qwen3-nothink/confidence_patterns/`
- Related: [[qwen3-nothink/Results_Data]] -- full quantitative results
- Related: [[Cross_Model_Confidence_Patterns]] -- cross-model comparison
