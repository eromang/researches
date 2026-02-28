---
title: "Confidence Pattern Analysis — deepseek-r1:8b"
date: 2026-02-28
model: "deepseek-r1:8b"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/deepseek-r1
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note defines a five-category taxonomy of rhetorical patterns found in deepseek-r1:8b confidence assessments and measures whether those patterns differ by attributed actor or are applied uniformly.

## Motivation

The [[deepseek-r1/Results_Data]] tested quantitative performance metrics across actors and certainty levels. That analysis focused on accuracy scores and calibration, not on the rhetorical structure of confidence assessments. This analysis builds a broader taxonomy of rhetorical pattern *types* and detects them at the category level across all 2,107 ok records, enabling direct comparison with [[qwen3-thinking/Confidence_Pattern_Analysis]] and the [[Cross_Model_Confidence_Patterns]] synthesis.

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
| China | Confirmed | 192 | 2.6% | 5.7% | 5.2% | 45.8% | 1.0% |
| China | Suspected | 191 | 16.8% | 7.3% | 15.7% | 52.4% | 1.1% |
| DPRK | Confirmed | 191 | 2.1% | 6.3% | 6.8% | 40.3% | 0.0% |
| DPRK | Suspected | 192 | 21.3% | 5.7% | 20.8% | 59.4% | 0.0% |
| Iran | Confirmed | 192 | 2.1% | 4.7% | 7.8% | 47.9% | 0.0% |
| Iran | Suspected | 191 | 7.8% | 7.3% | 27.2% | 63.3% | 0.5% |
| Russia | Confirmed | 192 | 0.5% | 8.3% | 6.2% | 51.6% | 1.0% |
| Russia | Suspected | 190 | 20.0% | 7.4% | 19.5% | 65.3% | 2.1% |
| US | Confirmed | 192 | 0.5% | 7.8% | 4.7% | 46.9% | 0.0% |
| US | Suspected | 192 | 7.8% | 9.9% | 22.9% | 50.5% | 0.0% |

Key observations:

- **Contextual-support appeals** are the dominant category (40–65% depending on actor and level), consistent with qwen3:8b
- **Evidence-qualification hedges** and **corroboration demands** are markedly lower at Confirmed level (0.5–2.6% and 4.7–7.8%) than at Suspected level (7.8–21.3% and 15.7–27.2%)
- **Procedural hedges** are near-zero across all conditions (0–2.1%), slightly higher than qwen3:8b (0–0.5%)
- **Misattribution caveats** are low and stable across actors and levels (4.7–9.9%)

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 1 out of 50 tests significant at p < 0.05.**

The single significant result is Russia vs DPRK on contextual support (d = 0.227, p = 0.0266) — Russia shows higher contextual-support appeal rates than DPRK at Confirmed level (51.6% vs 40.3%). This is borderline and would not survive Bonferroni correction (threshold = 0.001 for 50 tests).

All other Cohen's d values indicate small effect sizes.

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 2.6% | 1.3% | 0.105 | 0.2877 | no |
| Misattribution caveats | 5.7% | 6.8% | -0.042 | 0.5826 | no |
| Corroboration demands | 5.2% | 6.4% | -0.049 | 0.5200 | no |
| Contextual support | 45.8% | 46.7% | -0.017 | 0.8345 | no |
| Procedural hedges | 1.0% | 0.3% | 0.121 | 0.3025 | no |

**0 out of 5 significant. No China-protective framing detected.**

No category reaches significance. Effect sizes are negligible across all five categories. China is treated identically to other actors at the rhetorical pattern level when attribution is confirmed.

## Certainty calibration

Suspected vs Confirmed shift per actor and category (13 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Evidence qualification | China (d = 0.492), Russia (d = 0.678), US (d = 0.370), Iran (d = 0.267), DPRK (d = 0.625) | Suspected > Confirmed |
| Corroboration demands | China (d = 0.347), Russia (d = 0.402), US (d = 0.547), Iran (d = 0.527), DPRK (d = 0.414) | Suspected > Confirmed |
| Contextual support | Russia (d = 0.280), DPRK (d = 0.387), Iran (d = 0.314) | Suspected > Confirmed |

Evidence-qualification hedges drop significantly from Suspected to Confirmed for **all five actors**. The same holds for corroboration demands. This is a stronger calibration signal than qwen3:8b, where only contextual support was significant across all actors and corroboration demands shifted significantly for China alone.

Contextual-support appeals show a Suspected > Confirmed shift for three actors (Russia, DPRK, Iran) but not for China or US at significance threshold.

The model uses substantially more hedging rhetoric when attribution is uncertain, and this pattern is consistent across all actors for the two most evidentiary categories.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p | Sig? |
|----------|-------|-------|---|---|------|
| Evidence qualification | 1.7% | 1.5% | 0.017 | 0.7980 | no |
| Misattribution caveats | 7.1% | 6.0% | 0.042 | 0.5204 | no |
| Corroboration demands | 6.7% | 5.6% | 0.043 | 0.5072 | no |
| Contextual support | 48.8% | 44.3% | 0.090 | 0.1633 | no |
| Procedural hedges | 0.8% | 0.0% | 0.129 | 0.0448 | yes |

1 out of 5 significant: procedural hedges at T=0.0 vs T=0.7 (d = 0.129, p = 0.0448). This is marginal and reflects the near-zero base rate of procedural hedges — a handful of responses at T=0.0 drive the difference. Temperature does not meaningfully affect rhetorical pattern usage.

## Conclusions

1. **Actor uniformity confirmed.** Only 1 of 50 pairwise tests is significant (borderline, would not survive correction). deepseek-r1:8b applies rhetorical patterns uniformly across all five actor groups at the Confirmed certainty level.

2. **China is not treated differently.** 0 of 5 China-vs-rest tests are significant. There is no evidence of China-protective or China-punitive framing at the rhetorical pattern level.

3. **Strong certainty calibration at the category level.** 13 of 25 Suspected vs Confirmed tests are significant. Evidence-qualification hedges and corroboration demands shift significantly for all five actors — a stronger result than qwen3:8b (13/25 vs 7/25 significant tests). deepseek-r1 shows more consistent rhetorical differentiation between certain and uncertain attribution than qwen3.

4. **Temperature is nearly irrelevant.** Only 1 of 5 temperature comparisons reaches significance, and the effect is marginal and driven by the near-zero base rate of procedural hedges.

5. **Contextual support is the dominant category.** Detection rates of 40–65% make contextual-support appeals the primary rhetorical structure in deepseek-r1 confidence assessments, consistent with qwen3:8b.

6. **Procedural hedges are near-zero but slightly elevated relative to qwen3:8b.** Range of 0–2.1% vs 0–0.5% for qwen3. The difference is small but consistent with deepseek-r1's chain-of-thought architecture producing occasional process-oriented language.

See [[Cross_Model_Confidence_Patterns]] for cross-model comparison across deepseek-r1:8b, qwen3:8b, gemma3n, and llama3.1.

## Data sources

- Input: `results/Phase_2/deepseek-r1/deepseek-r1_flat.csv` (2,107 ok records)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/deepseek-r1/confidence_patterns/`
- Related: [[deepseek-r1/Results_Data]] — full quantitative results
- Related: [[Cross_Model_Confidence_Patterns]] — cross-model comparison
