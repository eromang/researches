---
title: "Confidence Pattern Analysis — qwen3:8b"
date: 2026-02-27
model: "qwen3:8b"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/qwen3
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note defines a five-category taxonomy of rhetorical patterns found in qwen3:8b confidence assessments and measures whether those patterns differ by attributed actor or are applied uniformly.

## Motivation

The [[qwen3-thinking/Cross_Phase_Comparison]] tested six individual phrases ("further corroboration," "false positives," "avoid escalation," etc.) and found them actor-uniform. That analysis was narrow — individual phrases, not categories. This analysis builds a broader taxonomy of rhetorical pattern *types* and detects them at the category level across all 2,109 ok records.

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

Statements that geopolitical context supports but doesn't prove attribution.

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
| China | Confirmed | 192 | 19.8% | 15.6% | 27.6% | 57.3% | 0.5% |
| China | Suspected | 191 | 25.1% | 22.0% | 46.6% | 71.7% | 0.0% |
| Russia | Confirmed | 191 | 15.7% | 18.3% | 34.5% | 56.0% | 0.0% |
| Russia | Suspected | 191 | 15.2% | 25.7% | 37.2% | 73.8% | 0.5% |
| US | Confirmed | 192 | 12.5% | 18.2% | 35.9% | 47.9% | 0.0% |
| US | Suspected | 192 | 10.9% | 26.0% | 41.1% | 58.9% | 0.0% |
| Iran | Confirmed | 192 | 17.7% | 15.1% | 36.5% | 52.6% | 0.0% |
| Iran | Suspected | 192 | 13.0% | 25.5% | 41.7% | 70.3% | 0.0% |
| DPRK | Confirmed | 192 | 15.6% | 15.6% | 37.0% | 51.0% | 0.5% |
| DPRK | Suspected | 192 | 19.8% | 18.2% | 41.7% | 69.3% | 0.5% |

Key observations:
- **Contextual-support appeals** are the most prevalent category (48–74% depending on actor and level)
- **Corroboration demands** are the second most prevalent (28–47%)
- **Procedural hedges** are near-zero across all conditions (0–0.5%)
- Rates are broadly similar across actors within each level

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 1 out of 50 tests significant at p < 0.05.**

The single significant result is China vs DPRK on corroboration demands (d = -0.201, p = 0.049) — China shows *lower* corroboration demands than DPRK at Confirmed level (27.6% vs 37.0%). This is borderline and would not survive Bonferroni correction (threshold = 0.001 for 50 tests).

All other Cohen's d values are in the range -0.20 to +0.20, indicating negligible effect sizes.

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 19.8% | 15.4% | 0.119 | 0.164 | no |
| Misattribution caveats | 15.6% | 16.8% | -0.032 | 0.686 | no |
| Corroboration demands | 27.6% | 36.0% | -0.177 | 0.022 | yes |
| Contextual support | 57.3% | 51.9% | 0.108 | 0.178 | no |
| Procedural hedges | 0.5% | 0.1% | 0.086 | 0.467 | no |

One category reaches significance: corroboration demands. China has *fewer* corroboration demands than other actors (27.6% vs 36.0%, d = -0.177). The direction is the opposite of what a "China-protective" hypothesis would predict — if qwen3 were protecting China, it would demand *more* corroboration (casting more doubt on attribution). Instead, it demands less.

## Certainty calibration

Suspected vs Confirmed shift per actor and category (7 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Corroboration demands | China (d = 0.400) | Suspected > Confirmed |
| Contextual support | All 5 actors (d = 0.220–0.379) | Suspected > Confirmed |
| Misattribution caveats | Iran (d = 0.260) | Suspected > Confirmed |

The contextual-support category shows a consistent Suspected > Confirmed drop across all five actors (all p < 0.05). The model uses more "geopolitical context" and "historical patterns" language when attribution is suspected than when confirmed. This is analytically correct — when attribution is less certain, contextual framing fills the evidentiary gap.

Corroboration demands show a significant drop for China only (46.6% Suspected to 27.6% Confirmed, d = 0.400). Other actors show the same direction but don't reach significance.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p |
|----------|-------|-------|---|---|
| Evidence qualification | 18.6% | 14.0% | 0.125 | 0.052 |
| Misattribution caveats | 17.3% | 15.8% | 0.040 | 0.534 |
| Corroboration demands | 35.9% | 32.7% | 0.067 | 0.297 |
| Contextual support | 53.9% | 52.1% | 0.036 | 0.581 |
| Procedural hedges | 0.4% | 0.0% | 0.091 | 0.157 |

**No category reaches significance.** Temperature does not affect rhetorical pattern usage.

## Conclusions

1. **Actor uniformity confirmed at category level.** Only 1 of 50 pairwise tests is significant (borderline, would not survive correction). This extends the Cross_Phase_Comparison finding from 6 individual phrases to 5 pattern categories with 28 total regexes.

2. **China is not treated differently.** The one China-vs-rest significant result (corroboration demands) shows China receiving *fewer* corroboration caveats, not more. This contradicts the Phase 1 hypothesis of China-protective framing.

3. **Certainty calibration exists at the category level.** Contextual-support appeals drop significantly from Suspected to Confirmed for all five actors. Corroboration demands drop significantly for China. The model uses more hedging rhetoric when attribution is uncertain.

4. **Temperature is irrelevant.** No category shows significant temperature sensitivity.

5. **Procedural hedges are near-absent.** Category 5 (reassessment, ongoing monitoring, subject to revision) appears in fewer than 1% of responses. The model does not use generic process language in confidence assessments.

## Data sources

- Input: `results/Phase_2/qwen3-thinking/qwen3_flat.csv` (2,109 ok records)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/qwen3-thinking/confidence_patterns/`
- Related: [[qwen3-thinking/Cross_Phase_Comparison]] — individual phrase analysis
- Related: [[qwen3-thinking/Results_Data]] — full quantitative results (section 16)
