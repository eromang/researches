---
title: "Confidence Pattern Analysis — mistral:7b-instruct"
date: 2026-03-02
model: "mistral:7b-instruct"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/mistral
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note defines a five-category taxonomy of rhetorical patterns found in mistral:7b-instruct confidence assessments and measures whether those patterns differ by attributed actor or are applied uniformly.

## Motivation

The [[mistral/Results_Data]] tested quantitative performance metrics across actors and certainty levels. That analysis focused on accuracy scores and calibration, not on the rhetorical structure of confidence assessments. This analysis builds a broader taxonomy of rhetorical pattern *types* and detects them at the category level across all 2,112 ok records, enabling direct comparison with [[qwen3-thinking/Confidence_Pattern_Analysis]], [[deepseek-r1/Confidence_Pattern_Analysis]], [[phi4/Confidence_Pattern_Analysis]], and the [[Cross_Model_Confidence_Patterns]] synthesis.

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
| China | Confirmed | 192 | 0.5% | 0.0% | 0.5% | 0.0% | 0.0% |
| China | Suspected | 192 | 0.0% | 0.0% | 2.1% | 1.0% | 0.0% |
| DPRK | Confirmed | 192 | 0.0% | 0.0% | 0.0% | 0.5% | 0.0% |
| DPRK | Suspected | 192 | 0.0% | 0.0% | 1.6% | 0.5% | 0.0% |
| Iran | Confirmed | 192 | 0.0% | 0.5% | 0.0% | 0.0% | 0.0% |
| Iran | Suspected | 192 | 0.0% | 0.5% | 1.6% | 0.5% | 0.0% |
| Russia | Confirmed | 192 | 0.0% | 0.0% | 0.5% | 1.0% | 0.0% |
| Russia | Suspected | 192 | 0.0% | 0.0% | 1.0% | 0.5% | 0.0% |
| US | Confirmed | 192 | 0.0% | 0.0% | 0.0% | 0.0% | 0.0% |
| US | Suspected | 192 | 0.0% | 0.0% | 2.1% | 0.0% | 0.0% |

Key observations:

- **All detection rates are extremely low** (0–2.1%). mistral's confidence assessments use non-standard vocabulary that does not match the rhetorical pattern regex taxonomy well
- **Corroboration demands** are the most frequently detected category, concentrated at Suspected level (1.0–2.1%)
- **Evidence-qualification hedges** are near-zero — only China_Confirmed shows 0.5%
- **Procedural hedges** are zero across all conditions
- The low detection rates limit the statistical power of all downstream tests

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 0 out of 50 tests significant at p < 0.05.**

No actor pair shows any statistically significant difference on any rhetorical pattern category. mistral is the most actor-uniform model in the Phase II benchmark at the confidence pattern level.

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 0.5% | 0.0% | 0.162 | 0.3173 | no |
| Misattribution caveats | 0.0% | 0.1% | -0.040 | 0.3173 | no |
| Corroboration demands | 0.5% | 0.1% | 0.086 | 0.4669 | no |
| Contextual support | 0.0% | 0.4% | -0.070 | 0.0829 | no |
| Procedural hedges | 0.0% | 0.0% | — | — | no |

**0 out of 5 significant. No China-protective framing detected.**

No category reaches significance. China is treated identically to the non-China actor average.

## Certainty calibration

Suspected vs Confirmed shift per actor and category (1 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Evidence qualification | None | — |
| Misattribution caveats | None | — |
| Corroboration demands | US (d = 0.206, p = 0.044) | Suspected > Confirmed |
| Contextual support | None | — |
| Procedural hedges | None | — |

Only US corroboration demands show a significant shift from Suspected to Confirmed. This is the weakest certainty-calibration signal of any Phase II model at the rhetorical pattern level — but the low baseline detection rates (0–2.1%) mean the taxonomy has limited discriminative power for mistral's output. The quantitative hedging and escalation metrics (Section 5 of Results_Data) demonstrate strong calibration through other channels.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p | Sig? |
|----------|-------|-------|---|---|------|
| Evidence qualification | 0.0% | 0.2% | -0.065 | 0.3173 | no |
| Misattribution caveats | 0.0% | 0.2% | -0.065 | 0.3173 | no |
| Corroboration demands | 0.0% | 0.4% | -0.091 | 0.1569 | no |
| Contextual support | 0.0% | 0.6% | -0.112 | 0.0826 | no |
| Procedural hedges | 0.0% | 0.0% | — | — | no |

0 out of 5 significant. Temperature does not meaningfully affect the rhetorical pattern profile. The slight increases at T=0.7 reflect sampling variation introducing occasional pattern-matching vocabulary.

## Conclusions

1. **Near-perfect actor uniformity.** 0 of 50 pairwise tests are significant. mistral is the most actor-uniform model in Phase II (vs deepseek-r1: 1/50, qwen3: 1/50, phi4: 10/50, gemma3n: 13/50).

2. **China is not treated differently.** 0 of 5 China-vs-rest tests are significant.

3. **Weak certainty calibration at the rhetorical pattern level.** Only 1 of 25 certainty-calibration tests reaches significance. However, this reflects the taxonomy's poor fit with mistral's output vocabulary rather than a genuine absence of calibration — the quantitative metrics show strong certainty calibration (d = 0.78–1.91 on hedging).

4. **No temperature effect.** 0 of 5 temperature comparisons reaches significance.

5. **Extremely low detection rates across all categories.** Maximum detection rate is 2.1%. mistral's confidence assessments use concise, non-standard vocabulary that rarely triggers the rhetorical pattern regexes. This is a model-specific limitation of the taxonomy, not evidence of missing analysis.

6. **No actor outlier.** Unlike phi4 (where US_Confirmed was an outlier on contextual support and corroboration demands), mistral shows no actor-specific asymmetries on any category.

See [[Cross_Model_Confidence_Patterns]] for cross-model comparison across all seven Phase II models.

## Data sources

- Input: `results/Phase_2/mistral/mistral_flat.csv` (2,112 ok records)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/mistral/confidence_patterns/`
- Related: [[mistral/Results_Data]] — full quantitative results
- Related: [[Cross_Model_Confidence_Patterns]] — cross-model comparison
