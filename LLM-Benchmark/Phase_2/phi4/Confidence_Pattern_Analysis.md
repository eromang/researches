---
title: "Confidence Pattern Analysis — phi4:latest"
date: 2026-03-02
model: "phi4:latest"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/phi4
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note defines a five-category taxonomy of rhetorical patterns found in phi4:latest confidence assessments and measures whether those patterns differ by attributed actor or are applied uniformly.

## Motivation

The [[phi4/Results_Data]] tested quantitative performance metrics across actors and certainty levels. That analysis focused on accuracy scores and calibration, not on the rhetorical structure of confidence assessments. This analysis builds a broader taxonomy of rhetorical pattern *types* and detects them at the category level across all 2,112 ok records, enabling direct comparison with [[qwen3-thinking/Confidence_Pattern_Analysis]], [[deepseek-r1/Confidence_Pattern_Analysis]], and the [[Cross_Model_Confidence_Patterns]] synthesis.

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
| China | Confirmed | 192 | 0.0% | 4.2% | 13.0% | 20.8% | 0.0% |
| China | Suspected | 192 | 20.3% | 14.6% | 11.5% | 17.2% | 0.5% |
| DPRK | Confirmed | 192 | 0.0% | 6.8% | 13.5% | 18.8% | 0.0% |
| DPRK | Suspected | 192 | 18.8% | 8.8% | 12.0% | 24.0% | 1.0% |
| Iran | Confirmed | 192 | 0.0% | 7.3% | 6.8% | 22.9% | 0.0% |
| Iran | Suspected | 192 | 17.7% | 8.8% | 10.9% | 21.9% | 1.0% |
| Russia | Confirmed | 192 | 0.5% | 4.2% | 13.0% | 19.8% | 1.0% |
| Russia | Suspected | 192 | 21.3% | 12.5% | 12.5% | 18.8% | 1.0% |
| US | Confirmed | 192 | 0.0% | 5.2% | 5.7% | 9.9% | 0.0% |
| US | Suspected | 192 | 7.3% | 10.4% | 15.6% | 13.0% | 0.0% |

Key observations:

- **Contextual-support appeals** are the dominant category at Confirmed level (9.9–22.9%), though substantially lower than deepseek-r1:8b (40–65%) and qwen3:8b (~53%)
- **Evidence-qualification hedges** drop sharply from Suspected (7.3–21.3%) to Confirmed (0.0–0.5%) for all actors
- **US_Confirmed shows the lowest contextual-support rate** (9.9%) — roughly half the rate of other actors (18.8–22.9%), driving significant pairwise comparisons
- **Procedural hedges** are near-zero across all conditions (0–1.0%)

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 10 out of 50 tests significant at p < 0.05.**

The significant results concentrate in two categories:

- **Corroboration demands:** China vs US (d = 0.252), Russia vs US (d = 0.252), China vs Iran (d = 0.210), Russia vs Iran (d = 0.210), US vs DPRK (d = -0.266), Iran vs DPRK (d = -0.225)
- **Contextual support:** China vs US (d = 0.306), Russia vs US (d = 0.280), US vs Iran (d = -0.356), US vs DPRK (d = -0.254)

The pattern is clear: **US_Confirmed stands apart** from other actors on corroboration demands and contextual-support appeals. US produces fewer contextual-support references and lower corroboration demand rates. This is not China-specific differentiation — it is a US-specific rhetorical posture.

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 0.0% | 0.1% | -0.040 | 0.3173 | no |
| Misattribution caveats | 4.2% | 5.9% | -0.074 | 0.3126 | no |
| Corroboration demands | 13.0% | 9.8% | 0.106 | 0.2211 | no |
| Contextual support | 20.8% | 17.8% | 0.077 | 0.3564 | no |
| Procedural hedges | 0.0% | 0.3% | -0.057 | 0.1570 | no |

**0 out of 5 significant. No China-protective framing detected.**

No category reaches significance. China is treated identically to the non-US actor average at the rhetorical pattern level.

## Certainty calibration

Suspected vs Confirmed shift per actor and category (8 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Evidence qualification | China (d = 0.712), Russia (d = 0.706), US (d = 0.396), Iran (d = 0.654), DPRK (d = 0.678) | Suspected > Confirmed |
| Misattribution caveats | China (d = 0.362), Russia (d = 0.304) | Suspected > Confirmed |
| Corroboration demands | US (d = 0.324) | Suspected > Confirmed |
| Contextual support | None | — |
| Procedural hedges | None | — |

Evidence-qualification hedges drop significantly from Suspected to Confirmed for **all five actors** — the strongest certainty-calibration signal. Misattribution caveats shift for China and Russia but not for other actors. Overall calibration signal (8/25 significant) is moderate — weaker than deepseek-r1:8b (13/25) but comparable to qwen3:8b.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p | Sig? |
|----------|-------|-------|---|---|------|
| Evidence qualification | 0.0% | 0.2% | -0.065 | 0.3173 | no |
| Misattribution caveats | 5.4% | 5.6% | -0.009 | 0.8877 | no |
| Corroboration demands | 7.5% | 13.3% | -0.192 | 0.0030 | yes |
| Contextual support | 17.5% | 19.4% | -0.048 | 0.4542 | no |
| Procedural hedges | 0.0% | 0.4% | -0.091 | 0.1569 | no |

1 out of 5 significant: corroboration demands increase at T=0.7 (7.5% to 13.3%, d = -0.192). This is a small effect driven by sampling variation introducing more hedging-type language. Temperature does not meaningfully affect the overall rhetorical pattern profile.

## Conclusions

1. **Moderate actor differentiation.** 10 of 50 pairwise tests are significant. phi4 is less uniform than deepseek-r1 (1/50) and qwen3 (1/50) but more uniform than gemma3n (13/50). The differentiation is driven by US_Confirmed producing fewer contextual-support and corroboration-demand references.

2. **China is not treated differently.** 0 of 5 China-vs-rest tests are significant. The asymmetry is a US-specific pattern, not a China-protective or China-punitive one.

3. **Strong evidence-qualification calibration.** Evidence-qualification hedges shift from Suspected to Confirmed for all five actors — the most consistent calibration signal. Overall calibration (8/25) is moderate.

4. **Temperature effect is minimal.** 1 of 5 temperature comparisons reaches significance, with a small effect on corroboration demands.

5. **Contextual support rates are moderate.** Detection rates of 9.9–22.9% at Confirmed level are substantially lower than deepseek-r1 (40–65%) and qwen3 (~53%), suggesting phi4 relies less on geopolitical framing in confidence assessments.

6. **US_Confirmed is the outlier.** The model produces fewer contextual-support appeals and corroboration demands for US-attributed scenarios. This could reflect training data patterns (more concise treatment of US-attributed incidents in training data) or the model's tendency to write shorter US_Confirmed responses overall.

See [[Cross_Model_Confidence_Patterns]] for cross-model comparison across all seven Phase II models.

## Data sources

- Input: `results/Phase_2/phi4/phi4_flat.csv` (2,112 ok records)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/phi4/confidence_patterns/`
- Related: [[phi4/Results_Data]] — full quantitative results
- Related: [[Cross_Model_Confidence_Patterns]] — cross-model comparison
