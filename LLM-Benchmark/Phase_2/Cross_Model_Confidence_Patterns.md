---
title: "Cross-Model Confidence Pattern Comparison"
date: 2026-02-27
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/confidence-patterns
  - benchmark/cross-model
---

# Cross-model confidence pattern comparison

Side-by-side comparison of rhetorical pattern usage in confidence assessments across four 8B-parameter models: qwen3:8b, llama3.1:8b, gemma3n:e4b, and deepseek-r1:8b.

## Overall detection rates at Confirmed level

All actors pooled, binary detection (at least one pattern in category matched).

| Category | qwen3:8b | llama3.1:8b | gemma3n:e4b | deepseek-r1:8b |
|----------|----------|-------------|-------------|----------------|
| Evidence qualification | 16.3% | 6.7% | 13.4% | 1.6% |
| Misattribution caveats | 16.6% | 13.9% | 13.2% | 6.6% |
| Corroboration demands | 34.3% | 12.6% | 66.2% | 6.2% |
| Contextual support | 53.0% | 1.7% | 36.7% | 46.5% |
| Procedural hedges | 0.2% | 0.5% | 0.1% | 0.4% |

Each model has a distinctive rhetorical profile:
- **qwen3** is contextual-support dominant (53% at Confirmed) -- it frames attribution in terms of geopolitical context and historical patterns
- **gemma3n** is corroboration-demand dominant (66% at Confirmed) -- it systematically asks for further evidence
- **llama3.1** is the most rhetorically sparse -- all categories below 14% at Confirmed, with near-zero contextual support (1.7%)
- **deepseek-r1** is contextual-support dominant like qwen3 (47% at Confirmed) but with the lowest rates in all other categories -- it relies almost exclusively on geopolitical framing, rarely qualifying evidence (1.6%) or demanding corroboration (6.2%)

## Model pairwise significance

Two-proportion z-tests per category (Confirmed level, all actors pooled):

| Model pair | Category | Rate 1 | Rate 2 | h | p | Sig? |
|---|---|---|---|---|---|---|
| deepseek-r1 vs gemma3n | Evid. qual. | 1.6% | 13.4% | -0.500 | 0.000 | yes |
| deepseek-r1 vs gemma3n | Misattr. | 6.6% | 13.2% | -0.226 | 0.000 | yes |
| deepseek-r1 vs gemma3n | Corroboration | 6.2% | 66.2% | -1.401 | 0.000 | yes |
| deepseek-r1 vs gemma3n | Contextual | 46.5% | 36.7% | 0.200 | 0.000 | yes |
| deepseek-r1 vs gemma3n | Procedural | 0.4% | 0.1% | 0.065 | 0.179 | no |
| deepseek-r1 vs llama31 | Evid. qual. | 1.6% | 6.7% | -0.272 | 0.000 | yes |
| deepseek-r1 vs llama31 | Misattr. | 6.6% | 13.9% | -0.244 | 0.000 | yes |
| deepseek-r1 vs llama31 | Corroboration | 6.2% | 12.6% | -0.225 | 0.000 | yes |
| deepseek-r1 vs llama31 | Contextual | 46.5% | 1.7% | 1.242 | 0.000 | yes |
| deepseek-r1 vs llama31 | Procedural | 0.4% | 0.5% | -0.015 | 0.740 | no |
| deepseek-r1 vs qwen3 | Evid. qual. | 1.6% | 16.3% | -0.580 | 0.000 | yes |
| deepseek-r1 vs qwen3 | Misattr. | 6.6% | 16.6% | -0.320 | 0.000 | yes |
| deepseek-r1 vs qwen3 | Corroboration | 6.2% | 34.3% | -0.750 | 0.000 | yes |
| deepseek-r1 vs qwen3 | Contextual | 46.5% | 53.0% | -0.129 | 0.005 | yes |
| deepseek-r1 vs qwen3 | Procedural | 0.4% | 0.2% | 0.038 | 0.414 | no |
| gemma3n vs llama31 | Evid. qual. | 13.4% | 6.7% | 0.228 | 0.000 | yes |
| gemma3n vs llama31 | Corroboration | 66.2% | 12.6% | 1.176 | 0.000 | yes |
| gemma3n vs llama31 | Contextual | 36.7% | 1.7% | 1.042 | 0.000 | yes |
| gemma3n vs qwen3 | Misattribution | 13.2% | 16.6% | -0.094 | 0.039 | yes |
| gemma3n vs qwen3 | Corroboration | 66.2% | 34.3% | 0.650 | 0.000 | yes |
| gemma3n vs qwen3 | Contextual | 36.7% | 53.0% | -0.329 | 0.000 | yes |
| llama31 vs qwen3 | Evid. qual. | 6.7% | 16.3% | -0.308 | 0.000 | yes |
| llama31 vs qwen3 | Corroboration | 12.6% | 34.3% | -0.526 | 0.000 | yes |
| llama31 vs qwen3 | Contextual | 1.7% | 53.0% | -1.371 | 0.000 | yes |

**21 out of 30 tests significant.** All four models differ significantly from each other on corroboration demands and contextual support. Procedural hedges remain the only category where models converge universally.

deepseek-r1 differs significantly from all other models on 4 of 5 categories (all except procedural hedges). The largest new effect is deepseek-r1 vs gemma3n on corroboration (h = -1.401) -- deepseek-r1 almost never demands corroboration (6.2%) while gemma3n does so two-thirds of the time (66.2%). The deepseek-r1 vs llama31 contextual support gap (h = 1.242) is nearly as large as the original llama31 vs qwen3 gap (h = -1.371).

## Actor uniformity comparison

| Model | Pairwise sig. (p<0.05) | Total tests | Characterisation |
|---|---|---|---|
| qwen3:8b | 1/50 | 50 | Actor-uniform |
| llama3.1:8b | 3/50 | 50 | Mostly uniform |
| gemma3n:e4b | 13/50 | 50 | Actor-differentiated |
| deepseek-r1:8b | 1/50 | 50 | Actor-uniform |

Gemma3n remains the only model that shows significant actor differentiation in rhetorical patterns. Its 13 significant tests concentrate in corroboration demands (7 pairs) and contextual support (4 pairs). Both Chinese-origin reasoning models (qwen3 and deepseek-r1) are actor-uniform with only 1/50 significant tests each, reinforcing that actor uniformity is not model-origin-dependent.

## Certainty calibration comparison

All three models show correct directional calibration (hedging increases from Confirmed to Suspected), but through different mechanisms:

| Model | Primary calibration mechanism | Significant tests |
|-------|-------------------------------|-------------------|
| qwen3:8b | Contextual-support drop (all 5 actors) | 7/25 |
| llama3.1:8b | Corroboration-demand drop + evidence-qual increase | 12/25 |
| gemma3n:e4b | Corroboration-demand drop (all 5 actors) + contextual-support drop (3 actors) | 10/25 |
| deepseek-r1:8b | Evidence-qual drop (all 5) + corroboration drop (all 5) + contextual-support drop (3) | 13/25 |

deepseek-r1 shows the broadest certainty calibration of all four models, with significant Suspected-to-Confirmed drops across three categories (evidence qualification, corroboration demands, and contextual support) for most or all actors. This contrasts with qwen3, which calibrates exclusively through contextual support. Both Chinese-origin reasoning models achieve strong calibration, but through different rhetorical mechanisms.

## Temperature sensitivity comparison

| Model | Significant categories | Pattern |
|-------|----------------------|---------|
| qwen3:8b | 0/5 | Temperature-invariant |
| llama3.1:8b | 2/5 (evidence qual., misattribution) | Rhetorical degradation at T=0.7 |
| gemma3n:e4b | 0/5 | Temperature-invariant |
| deepseek-r1:8b | 1/5 (procedural hedges, marginal) | Effectively temperature-invariant |

Only llama3.1 shows meaningful temperature effects on rhetorical patterns. deepseek-r1's single marginal result (procedural hedges, p = 0.045) reflects the near-zero baseline (0.8% to 0.0%) and has no practical significance.

## Model-specific vocabulary

Top 5 distinctive n-grams per model (not captured by the taxonomy):

**qwen3:8b** -- analytical-intelligence vocabulary
- "linked actors" (62%), "confidence level" (47%), "strong technical" (40%), "intelligence evidence" (38%), "state sponsored" (35%)

**llama3.1:8b** -- geopolitical-framing vocabulary
- "geopolitical implications" (80%), "attribution confidence" (78%), "escalation risks" (69%), "confidence moderate" (64%), "linked actors" (61%)

**gemma3n:e4b** -- evidence-demands vocabulary
- "linked actors" (65%), "definitive attribution" (49%), "moderate rationale" (51%), "state sponsored" (40%), "preliminary intelligence" (35%)

**deepseek-r1:8b** -- structured-assessment vocabulary
- "attribution confidence" (72%), "geopolitical implications" (67%), "e g" (61%), "escalation risk" (59%), "confidence moderate" (54%), "definitive proof" (51%), "state sponsored" (52%)

The vocabulary differences reflect each model's rhetorical profile: llama3.1 uses geopolitical framing language even though it rarely triggers the taxonomy's contextual-support patterns; gemma3n emphasises evidence demands; qwen3 uses intelligence-community terminology. deepseek-r1 shares vocabulary elements with both llama3.1 ("attribution confidence," "geopolitical implications") and qwen3 ("e g," "state sponsored"), but its distinctive marker is "definitive proof" (51%) -- its primary hedging mechanism identified in the [[deepseek-r1/Cross_Phase_Comparison]].

## Key findings

1. **Each model has a distinct rhetorical fingerprint.** The same prompt set produces dramatically different confidence-assessment rhetoric depending on the model. Corroboration demands range from 6% (deepseek-r1) to 66% (gemma3n). Contextual support ranges from 2% (llama3.1) to 53% (qwen3). Evidence qualification ranges from 2% (deepseek-r1) to 16% (qwen3).

2. **Actor uniformity varies by model.** Qwen3 and deepseek-r1 are actor-uniform (1/50 each), llama3.1 is mostly uniform (3/50), and gemma3n is actor-differentiated (13/50). Both Chinese-origin reasoning models achieve the highest actor uniformity, though this likely reflects their reasoning architecture rather than national origin.

3. **No model shows China-protective framing.** All four models' China-vs-rest tests either show no difference or show China receiving *less* hedging. The consistency across four different models (Alibaba, DeepSeek, Meta, Google) -- including two Chinese-origin models -- strengthens the conclusion that China-protective bias is not a feature of current 8B models.

4. **Temperature stability predicts rhetorical stability.** Three temperature-stable models (qwen3, gemma3n, deepseek-r1) show no meaningful temperature effect on rhetorical patterns. The temperature-unstable model (llama3.1) shows significant rhetorical degradation at T=0.7.

5. **Procedural hedges are universally absent.** All four models produce less than 1% procedural-hedge usage. Generic process language ("reassessment," "subject to revision," "ongoing monitoring") is not part of any model's rhetorical repertoire for confidence assessments.

6. **Chinese-origin reasoning models share contextual-support dominance but differ on everything else.** Both qwen3 and deepseek-r1 rely heavily on contextual-support appeals (47-53%), but qwen3 also uses substantial evidence qualification (16%) and corroboration demands (34%), while deepseek-r1 uses almost none (2% and 6% respectively). Shared national origin does not produce shared rhetorical strategy.

## Data sources

- [[qwen3-thinking/Confidence_Pattern_Analysis]] -- qwen3:8b standalone analysis
- [[llama31/Confidence_Pattern_Analysis]] -- llama3.1:8b standalone analysis
- [[gemma3n/Confidence_Pattern_Analysis]] -- gemma3n:e4b standalone analysis
- [[deepseek-r1/Confidence_Pattern_Analysis]] -- deepseek-r1:8b standalone analysis
- Comparison script: `scripts/compare_confidence_patterns.py`
- Output directory: `results/Phase_2/cross_model_confidence_patterns/`
