---
title: "Confidence Pattern Analysis — llama3.1:8b"
date: 2026-02-27
model: "llama3.1:8b-instruct-q4_K_M"
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/llama31
  - benchmark/confidence-patterns
---

# Confidence assessment rhetorical pattern analysis

This note applies the five-category taxonomy of rhetorical patterns (defined in [[qwen3-thinking/Confidence_Pattern_Analysis]]) to llama3.1:8b confidence assessments and measures whether those patterns differ by attributed actor.

## Motivation

The qwen3:8b analysis found all five categories actor-uniform (1/50 pairwise tests significant). This analysis tests whether the same taxonomy produces a different picture on a Meta model with a known US refusal asymmetry and stochastic safety classifier at T=0.7.

## Data characteristics

- 2,112 records total (all ok==True)
- 1,784 records with non-empty `confidence_assessment` (84.5%)
- 328 records with empty confidence assessment (refusals and truncated outputs)
- Empty records are excluded from pattern analysis but included in record count

## Detection rates by actor and certainty level

All temperatures combined, binary detection (at least one pattern in category matched).

| Actor | Level | N | Evidence qual. | Misattribution | Corroboration | Contextual | Procedural |
|-------|-------|---|---|---|---|---|---|
| China | Confirmed | 192 | 6.8% | 16.7% | 10.4% | 0.5% | 0.0% |
| China | Suspected | 192 | 0.0% | 8.8% | 32.3% | 0.5% | 4.2% |
| Russia | Confirmed | 192 | 3.6% | 13.5% | 15.1% | 3.1% | 0.0% |
| Russia | Suspected | 192 | 0.0% | 9.9% | 28.6% | 2.1% | 1.0% |
| US | Confirmed | 192 | 10.9% | 13.5% | 17.2% | 1.0% | 1.6% |
| US | Suspected | 192 | 0.0% | 7.8% | 22.9% | 1.0% | 0.5% |
| Iran | Confirmed | 192 | 4.7% | 15.6% | 10.4% | 1.0% | 0.0% |
| Iran | Suspected | 192 | 0.0% | 8.8% | 24.0% | 3.6% | 1.6% |
| DPRK | Confirmed | 192 | 7.3% | 9.9% | 9.9% | 2.6% | 1.0% |
| DPRK | Suspected | 192 | 1.0% | 9.9% | 33.9% | 4.7% | 2.1% |

Key observations:
- **Corroboration demands** are the most prevalent category at Suspected level (23--34%)
- **Misattribution caveats** are the most prevalent at Confirmed level (10--17%)
- **Contextual-support appeals** are near-zero (0.5--4.7%) -- dramatically lower than qwen3 (48--74%)
- **Procedural hedges** are rare but non-zero (0--4.2%), slightly more than qwen3's near-zero
- Overall pattern rates are much lower than qwen3 and gemma3n

## Actor symmetry at Confirmed level

Pairwise Welch's t-tests across all 10 actor pairs for each of the 5 categories (50 tests total).

**Result: 3 out of 50 tests significant at p < 0.05.**

Significant results:
- Russia vs US on evidence qualification (d = -0.282, p = 0.006) -- US shows higher evidence-qualification hedging
- US vs Iran on evidence qualification (d = 0.234, p = 0.022) -- same direction
- US vs DPRK on corroboration demands (d = 0.214, p = 0.036) -- US shows higher corroboration demands

All three involve the US showing elevated hedging, consistent with llama3.1's known Western-actor sensitivity. None would survive Bonferroni correction (threshold = 0.001 for 50 tests).

### China-vs-rest test

One-vs-rest comparison (China at Confirmed vs all other actors pooled at Confirmed):

| Category | China | Rest | d | p | Sig? |
|----------|-------|------|---|---|------|
| Evidence qualification | 6.8% | 6.6% | 0.005 | 0.949 | no |
| Misattribution caveats | 16.7% | 13.2% | 0.102 | 0.235 | no |
| Corroboration demands | 10.4% | 13.2% | -0.082 | 0.279 | no |
| Contextual support | 0.5% | 1.9% | -0.112 | 0.047 | yes |
| Procedural hedges | 0.0% | 0.7% | -0.090 | 0.025 | yes |

Two marginal results, both showing China receiving *less* hedging than others. Neither is practically significant (contextual support: 0.5% vs 1.9%; procedural hedges: 0.0% vs 0.7%).

## Certainty calibration

Suspected vs Confirmed shift (12 of 25 tests significant):

| Pattern | Significant actors | Direction |
|---------|-------------------|-----------|
| Evidence qualification | China, Russia, US, Iran, DPRK (all 5) | Confirmed > Suspected |
| Misattribution caveats | China, Iran | Suspected < Confirmed |
| Corroboration demands | China (d = 0.552), Russia, Iran, DPRK | Suspected > Confirmed |
| Procedural hedges | China (d = 0.294) | Suspected > Confirmed |

The dominant pattern is a **corroboration-demand drop** from Suspected to Confirmed -- the opposite direction from qwen3's contextual-support drop. When attribution becomes confirmed, llama3.1 stops asking for further corroboration (expected). However, evidence-qualification hedging *increases* under Confirmed -- the model adds "definitive attribution requires" language even when attribution is confirmed, which is analytically backwards.

## Temperature effect

T=0.0 vs T=0.7 at Confirmed level (all actors pooled):

| Category | T=0.0 | T=0.7 | d | p |
|----------|-------|-------|---|---|
| Evidence qualification | 10.4% | 2.9% | 0.304 | 0.000 |
| Misattribution caveats | 18.3% | 9.4% | 0.261 | 0.000 |
| Corroboration demands | 12.5% | 12.7% | -0.006 | 0.923 |
| Contextual support | 1.7% | 1.7% | 0.000 | 1.000 |
| Procedural hedges | 0.8% | 0.2% | 0.087 | 0.179 |

**Two categories show significant temperature effects.** Evidence qualification and misattribution caveats both drop at T=0.7. This is consistent with llama3.1's known temperature instability -- at T=0.7 the model produces shorter, more fragmented outputs that include fewer structured hedging phrases. The drop is a side-effect of output degradation, not a meaningful rhetorical shift.

## Conclusions

1. **Mostly actor-uniform.** 3/50 pairwise tests significant (none surviving correction). The three significant results all involve the US showing elevated hedging, consistent with the previously identified Western-actor sensitivity.

2. **China is not treated differently.** The two China-vs-rest significant results show China receiving *less* hedging, not more. No evidence of China-protective framing.

3. **Very low contextual-support usage.** Unlike qwen3 (48--74%) and gemma3n (25--45%), llama3.1 rarely uses geopolitical context or historical pattern language in confidence assessments (0.5--4.7%). The model's rhetorical profile is dominated by corroboration demands and misattribution caveats.

4. **Temperature matters.** Unlike qwen3 (no temperature effect), llama3.1 shows significant drops in evidence qualification and misattribution caveats at T=0.7. This reflects output degradation under stochastic generation, not a meaningful rhetorical shift.

5. **Reversed certainty calibration pattern.** Where qwen3 shows contextual-support dropping from Suspected to Confirmed, llama3.1 shows corroboration-demands dropping and evidence-qualification *increasing*. Different models fill the certainty gap with different rhetorical strategies.

## Data sources

- Input: `results/Phase_2/llama31/llama31_flat.csv` (2,112 records, 1,784 with non-empty CA)
- Script: `scripts/analyze_confidence_patterns.py`
- Output directory: `results/Phase_2/llama31/confidence_patterns/`
- Related: [[llama31/Results_Data]] -- full quantitative results (section 17)
- Related: [[qwen3-thinking/Confidence_Pattern_Analysis]] -- taxonomy definition and qwen3 results
