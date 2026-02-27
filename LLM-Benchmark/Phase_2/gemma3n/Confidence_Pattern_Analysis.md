---
title: "Confidence Pattern Analysis — gemma3n:e4b"
date: 2026-02-27
model: "gemma3n:e4b"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/gemma3n
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note applies the five-category taxonomy of rhetorical patterns (defined in [[qwen3-thinking/Confidence_Pattern_Analysis]]) to gemma3n:e4b confidence assessments and measures whether those patterns differ by attributed actor.

## Motivation

The qwen3:8b analysis found all five categories actor-uniform (1/50 pairwise tests significant). Llama3.1 was mostly uniform (3/50). This analysis tests whether gemma3n -- a Google model with known US hedging elevation but no US refusal asymmetry -- shows the same uniformity or a different pattern.

## Data characteristics

- 2,112 records total (all ok==True)
- 2,112 records with non-empty `confidence_assessment` (100%)
- No missing data -- gemma3n produced parseable confidence sections for every prompt
- Note: the flat CSV required a patched section extractor to handle gemma3n's `**7) Confidence Assessment:**` format

## Detection rates by actor and certainty level

All temperatures combined, binary detection (at least one pattern in category matched).

| Actor | Level | N | Evidence qual. | Misattribution | Corroboration | Contextual | Procedural |
|-------|-------|---|---|---|---|---|---|
| China | Confirmed | 192 | 13.0% | 13.5% | 53.1% | 34.9% | 0.0% |
| China | Suspected | 192 | 16.7% | 16.2% | 84.9% | 55.2% | 0.0% |
| DPRK | Confirmed | 192 | 15.6% | 13.5% | 63.0% | 37.0% | 0.0% |
| DPRK | Suspected | 192 | 17.2% | 18.8% | 85.9% | 45.8% | 0.0% |
| Iran | Confirmed | 192 | 16.2% | 11.5% | 76.0% | 41.7% | 0.0% |
| Iran | Suspected | 192 | 14.6% | 16.7% | 87.5% | 65.1% | 1.6% |
| Russia | Confirmed | 192 | 13.0% | 11.5% | 64.6% | 44.3% | 0.5% |
| Russia | Suspected | 192 | 14.1% | 20.8% | 89.1% | 60.9% | 1.0% |
| US | Confirmed | 192 | 9.4% | 16.2% | 74.5% | 25.5% | 0.0% |
| US | Suspected | 192 | 15.1% | 26.0% | 91.7% | 33.9% | 0.5% |

Key observations:
- **Corroboration demands dominate** -- the most prevalent category across all conditions (53--92%)
- **Contextual-support appeals** are second (25--65%), much higher than llama3.1 but lower than qwen3
- **Evidence qualification** and **misattribution caveats** are moderate (9--26%)
- **Procedural hedges** are near-zero (0--1.6%)
- **US_Confirmed has the lowest contextual-support rate** (25.5%) but the highest corroboration demand (74.5%) among Confirmed conditions

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 13 out of 50 tests significant at p < 0.05.**

This is the most actor-differentiated model in the study. The significant results cluster in two categories:

**Corroboration demands (7 significant pairs):**
- China vs Russia (d = -0.234, p = 0.022)
- China vs US (d = -0.455, p = 0.000)
- China vs Iran (d = -0.492, p = 0.000)
- China vs DPRK (d = -0.201, p = 0.049)
- Russia vs US (d = -0.216, p = 0.035)
- Russia vs Iran (d = -0.252, p = 0.014)
- Iran vs DPRK (d = 0.285, p = 0.005)

Pattern: China has the *lowest* corroboration demand rate (53.1%) while Iran has the highest (76.0%). The ordering is: China < DPRK < Russia < US < Iran. This is not geopolitically aligned -- if gemma3n were protecting any state, it would demand *more* corroboration for that state.

**Contextual support (4 significant pairs):**
- China vs US (d = 0.205, p = 0.045)
- Russia vs US (d = 0.400, p = 0.000)
- US vs Iran (d = -0.346, p = 0.001)
- US vs DPRK (d = -0.248, p = 0.015)

Pattern: US_Confirmed has the lowest contextual-support rate (25.5%) while Russia has the highest (44.3%). The US stands out as receiving less "geopolitical context supports this" language.

### China-vs-rest test

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 13.0% | 13.5% | -0.015 | 0.849 | no |
| Misattribution caveats | 13.5% | 13.2% | 0.011 | 0.888 | no |
| Corroboration demands | 53.1% | 69.5% | -0.350 | 0.000 | yes |
| Contextual support | 34.9% | 37.1% | -0.046 | 0.567 | no |
| Procedural hedges | 0.0% | 0.1% | -0.040 | 0.317 | no |

One significant result: corroboration demands. China receives *fewer* corroboration demands than other actors (53.1% vs 69.5%, d = -0.350). This is the opposite of China-protective framing.

## Certainty calibration

Suspected vs Confirmed shift (10 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Corroboration demands | All 5 actors (d = 0.299--0.730) | Suspected > Confirmed |
| Contextual support | China, Russia, Iran (d = 0.338--0.482) | Suspected > Confirmed |
| Misattribution caveats | Russia, US (d = 0.244--0.256) | Suspected > Confirmed |

The dominant calibration mechanism is a **corroboration-demand drop** from Suspected to Confirmed for all five actors -- the same direction as llama3.1 and analytically correct (less need to demand further evidence when attribution is confirmed). The contextual-support drop from Suspected to Confirmed for 3 actors mirrors qwen3's pattern.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p |
|----------|-------|-------|---|---|
| Evidence qualification | 14.2% | 12.7% | 0.043 | 0.508 |
| Misattribution caveats | 14.2% | 12.3% | 0.055 | 0.392 |
| Corroboration demands | 67.9% | 64.6% | 0.070 | 0.275 |
| Contextual support | 39.6% | 33.8% | 0.121 | 0.061 |
| Procedural hedges | 0.0% | 0.2% | -0.065 | 0.317 |

**No category reaches significance.** Temperature does not affect rhetorical pattern usage. This is consistent with gemma3n's excellent temperature stability (variance ratio = 0.98).

## Conclusions

1. **Actor-differentiated rhetorical patterns.** 13/50 pairwise tests significant -- the most differentiated model tested. The differentiation concentrates in corroboration demands (7 pairs) and contextual support (4 pairs).

2. **China is not treated differently in a protective direction.** The one China-vs-rest significant result shows China receiving *fewer* corroboration demands. The corroboration ordering (China < DPRK < Russia < US < Iran) does not follow geopolitical alignment.

3. **US stands out on contextual support.** US_Confirmed has the lowest contextual-support rate (25.5%) and the highest corroboration-demand rate among Confirmed conditions. Gemma3n appears less willing to invoke "geopolitical context" when attributing to the US, consistent with its known US hedging elevation.

4. **Strong certainty calibration.** All five actors show significant corroboration-demand drops from Suspected to Confirmed. Three actors also show contextual-support drops. The model adjusts rhetoric appropriately to certainty level.

5. **Temperature irrelevant.** No significant temperature effects, consistent with gemma3n's overall stability.

6. **Corroboration-dominant rhetorical profile.** Gemma3n's confidence assessments are dominated by corroboration demands (53--92%), far exceeding qwen3 (28--47%) and llama3.1 (10--34%). The model's default mode is to ask for further evidence.

## Data sources

- Input: `results/Phase_2/gemma3n/gemma3n_flat.csv` (2,112 records, 2,112 with non-empty CA)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/gemma3n/confidence_patterns/`
- Related: [[gemma3n/Results_Data]] -- full quantitative results (section 17)
- Related: [[qwen3-thinking/Confidence_Pattern_Analysis]] -- taxonomy definition and qwen3 results
