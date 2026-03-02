---
title: "Cross-Model Confidence Pattern Comparison"
date: 2026-03-02
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/confidence-patterns
  - benchmark/cross-model
---

# Cross-model confidence pattern comparison

Side-by-side comparison of rhetorical pattern usage in confidence assessments across seven Phase II models: qwen3:8b, llama3.1:8b, gemma3n:e4b, deepseek-r1:8b, hoangquan456/qwen3-nothink:8b, phi4:latest (14B), and mistral:7b-instruct (7B, Mistral AI France — first EU-origin model).

## Overall detection rates at Confirmed level

All actors pooled, binary detection (at least one pattern in category matched).

| Category | qwen3:8b | llama3.1:8b | gemma3n:e4b | deepseek-r1:8b | qwen3-nothink:8b | phi4:latest | mistral:7b-instruct |
|----------|----------|-------------|-------------|----------------|------------------|-------------|---------------------|
| Evidence qualification | 16.3% | 6.7% | 13.4% | 1.6% | 9.5% | 0.1% | 0.1% |
| Misattribution caveats | 16.6% | 13.9% | 13.2% | 6.6% | 7.2% | 5.5% | 0.1% |
| Corroboration demands | 34.3% | 12.6% | 66.2% | 6.2% | 18.0% | 10.4% | 0.2% |
| Contextual support | 53.0% | 1.7% | 36.7% | 46.5% | 19.9% | 18.4% | 0.3% |
| Procedural hedges | 0.2% | 0.5% | 0.1% | 0.4% | 0.0% | 0.2% | 0.0% |

Each model has a distinctive rhetorical profile:
- **qwen3** is contextual-support dominant (53% at Confirmed) -- it frames attribution in terms of geopolitical context and historical patterns
- **gemma3n** is corroboration-demand dominant (66% at Confirmed) -- it systematically asks for further evidence
- **llama3.1** is the most rhetorically sparse among the larger models -- all categories below 14% at Confirmed, with near-zero contextual support (1.7%)
- **deepseek-r1** is contextual-support dominant like qwen3 (47% at Confirmed) but with the lowest rates in all other categories -- it relies almost exclusively on geopolitical framing, rarely qualifying evidence (1.6%) or demanding corroboration (6.2%)
- **qwen3-nothink** is the most balanced model -- no single category dominates, with corroboration demands (18%) and contextual support (20%) roughly equal; removing chain-of-thought from the Qwen3 architecture flattens the rhetorical profile
- **phi4** has the lowest evidence-qualification rate (0.1%) and moderate corroboration demands (10.4%) and contextual support (18.4%) -- a sparse profile similar to deepseek-r1 but with less contextual-support reliance; the 14B parameter count does not produce richer rhetorical scaffolding
- **mistral** is the most rhetorically sparse model overall -- all categories at or below 0.3% at Confirmed level, meaning its confidence assessments use non-standard vocabulary that falls outside the taxonomy's regex patterns; this is a vocabulary-fit limitation rather than an analytical absence

## Model pairwise significance

Two-proportion z-tests per category (Confirmed level, all actors pooled):

Due to the large number of pairwise tests (105 = C(7,2) × 5 categories), only significant results and a summary are shown here. The full table is in `results/Phase_2/cross_model_confidence_patterns/cross_model_pairwise.csv`.

**79 out of 105 tests significant at p < 0.05.**

Key patterns from the pairwise tests:

- **mistral differs from all other models on 3–5 categories** due to its near-zero detection rates. The strongest contrasts are mistral vs gemma3n (corroboration: h = 1.810) and mistral vs qwen3 (contextual: h = -1.518).
- **mistral is most similar to phi4** (3/5 significant — identical on evidence qualification at 0.1%, but phi4 has higher misattribution, corroboration, and contextual rates).
- All seven models differ significantly from each other on corroboration demands and contextual support. Procedural hedges remain the only category where models mostly converge.
- phi4 is most similar to qwen3-nothink (2/5 significant) and deepseek-r1 (3/5 significant), suggesting the US-origin instruct model shares rhetorical sparsity with the Chinese-origin reasoning model.
- The qwen3 vs qwen3-nothink pair is architecturally unique: same Qwen3 base, thinking enabled vs disabled. Removing chain-of-thought produces significant drops in all four substantive categories (h = 0.20–0.71), with the largest effect on contextual support (53% → 20%, h = 0.706). This suggests that the internal reasoning phase actively amplifies rhetorical patterns rather than merely organising them.

## Actor uniformity comparison

| Model | Pairwise sig. (p<0.05) | Total tests | Characterisation |
|---|---|---|---|
| mistral:7b-instruct | 0/50 | 50 | Actor-uniform |
| qwen3:8b | 1/50 | 50 | Actor-uniform |
| deepseek-r1:8b | 1/50 | 50 | Actor-uniform |
| llama3.1:8b | 3/50 | 50 | Mostly uniform |
| qwen3-nothink:8b | 8/50 | 50 | Moderately differentiated |
| phi4:latest | 10/50 | 50 | Moderately differentiated |
| gemma3n:e4b | 13/50 | 50 | Actor-differentiated |

mistral is the most actor-uniform model in Phase II (0/50 significant tests), though this is driven by near-zero detection rates across all categories rather than genuine uniformity at high rates. Gemma3n and phi4 show the most actor differentiation. Gemma3n's 13 significant tests concentrate in corroboration demands (7 pairs) and contextual support (4 pairs). phi4's 10 significant tests concentrate in corroboration demands and contextual support, driven by US_Confirmed showing lower rates than other actors. Qwen3-nothink's 8 significant tests are driven by contextual support (7 pairs) — the same Qwen3 architecture with thinking enabled produces only 1/50, suggesting that chain-of-thought acts as a uniformity mechanism. Both Chinese-origin reasoning models (qwen3 and deepseek-r1) are actor-uniform with only 1/50 significant tests each.

## Certainty calibration comparison

All seven models show correct directional calibration (hedging increases from Confirmed to Suspected), but through different mechanisms:

| Model | Primary calibration mechanism | Significant tests |
|-------|-------------------------------|-------------------|
| qwen3:8b | Contextual-support drop (all 5 actors) | 7/25 |
| llama3.1:8b | Corroboration-demand drop + evidence-qual increase | 12/25 |
| gemma3n:e4b | Corroboration-demand drop (all 5 actors) + contextual-support drop (3 actors) | 10/25 |
| deepseek-r1:8b | Evidence-qual drop (all 5) + corroboration drop (all 5) + contextual-support drop (3) | 13/25 |
| qwen3-nothink:8b | Evidence-qual drop (4 actors) + corroboration drop (Russia) + contextual-support drop (DPRK) | 6/25 |
| phi4:latest | Evidence-qual drop (all 5) + misattribution drop (China, Russia) + corroboration drop (US) | 8/25 |
| mistral:7b-instruct | Corroboration-demand drop (US only) | 1/25 |

deepseek-r1 shows the broadest certainty calibration of all seven models, with significant Suspected-to-Confirmed drops across three categories for most or all actors. mistral shows the weakest calibration at the rhetorical-pattern level (1/25), though this reflects the taxonomy's poor fit with mistral's output vocabulary rather than absent calibration — its quantitative hedging metrics show strong certainty calibration (d = 0.78–1.91). phi4 calibrates primarily through evidence qualification (all 5 actors significant), matching deepseek-r1's pattern on this category despite being a standard instruct model without reasoning. qwen3-nothink calibrates primarily through evidence qualification (4 actors significant), a mechanism absent from the thinking variant (qwen3:8b calibrates exclusively through contextual support). Removing chain-of-thought shifts the calibration mechanism from contextual-support to evidence-qualification, a qualitative change despite lower overall sensitivity (6/25 vs 7/25).

## Temperature sensitivity comparison

| Model | Significant categories | Pattern |
|-------|----------------------|---------|
| qwen3:8b | 0/5 | Temperature-invariant |
| llama3.1:8b | 2/5 (evidence qual., misattribution) | Rhetorical degradation at T=0.7 |
| gemma3n:e4b | 0/5 | Temperature-invariant |
| deepseek-r1:8b | 1/5 (procedural hedges, marginal) | Effectively temperature-invariant |
| qwen3-nothink:8b | 1/5 (misattribution caveats) | Effectively temperature-invariant |
| phi4:latest | 1/5 (corroboration demands) | Effectively temperature-invariant |
| mistral:7b-instruct | 0/5 | Temperature-invariant |

Only llama3.1 shows meaningful temperature effects on rhetorical patterns. deepseek-r1, qwen3-nothink, and phi4 each have single marginal results that lack practical significance. mistral and qwen3:8b are fully temperature-invariant on rhetorical patterns (0/5 significant each).

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

**qwen3-nothink:8b** -- defensive-priorities vocabulary
- "geopolitical implications" (84%), "defensive priorities" (80%), "defensive priorities confidence" (71%), "confidence moderate" (75%), "confidence high" (74%), "attribution confidence" (79%), "linked actors" (69%)

**phi4:latest** -- high-frequency structured vocabulary
- "geopolitical implications" (96%), "attribution confidence" (96%), "escalation risks" (94%), "confidence moderate" (85%), "confidence high" (86%), "linked actors" (73%), "geopolitical implications confidence" (70%), "escalation risks confidence" (69%)

**mistral:7b-instruct** -- concise non-standard vocabulary
- Detection rates too low (0–2.1%) to extract meaningful n-gram patterns from the taxonomy. mistral's confidence assessments use concise, non-standard vocabulary that does not match the rhetorical pattern regexes. Manual inspection reveals a compact assessment style without the structured section headings (e.g. "geopolitical implications," "defensive priorities") that characterise other models.

The vocabulary differences reflect each model's rhetorical profile: llama3.1 uses geopolitical framing language even though it rarely triggers the taxonomy's contextual-support patterns; gemma3n emphasises evidence demands; qwen3 uses intelligence-community terminology. deepseek-r1 shares vocabulary elements with both llama3.1 ("attribution confidence," "geopolitical implications") and qwen3 ("e g," "state sponsored"), but its distinctive marker is "definitive proof" (51%) -- its primary hedging mechanism identified in the [[deepseek-r1/Cross_Phase_Comparison]]. qwen3-nothink's distinctive marker is the "defensive priorities" cluster (80%), absent from all other models including the thinking variant -- removing chain-of-thought produces a vocabulary shift towards defensive posture framing. phi4 has the highest n-gram frequencies of any model: "geopolitical implications" at 96% and "attribution confidence" at 96%, indicating extremely templated output structure; its "escalation risks confidence" cluster (69%) resembles qwen3-nothink's "defensive priorities confidence" pattern, suggesting both instruct models default to structured section-heading vocabulary. mistral's near-zero detection rates mean it falls entirely outside the taxonomy's vocabulary space — a limitation of the regex-based approach rather than evidence of missing analysis.

## Key findings

1. **Each model has a distinct rhetorical fingerprint.** The same prompt set produces dramatically different confidence-assessment rhetoric depending on the model. Corroboration demands range from 0.2% (mistral) to 66% (gemma3n). Contextual support ranges from 0.3% (mistral) to 53% (qwen3). Evidence qualification ranges from 0.1% (phi4, mistral) to 16% (qwen3).

2. **Actor uniformity varies by model.** Mistral (0/50) and qwen3/deepseek-r1 (1/50 each) are actor-uniform, llama3.1 is mostly uniform (3/50), qwen3-nothink (8/50) and phi4 (10/50) are moderately differentiated, and gemma3n is actor-differentiated (13/50). Removing chain-of-thought from Qwen3 increases actor differentiation from 1/50 to 8/50, suggesting that the reasoning phase functions as a uniformity mechanism.

3. **No model shows China-protective framing.** All seven models' China-vs-rest tests either show no difference or show China receiving *less* hedging. The consistency across seven models from five providers (Alibaba, DeepSeek, Meta, Google, Microsoft, Mistral AI) -- including two Chinese-origin architectures in three configurations and the first EU-origin model -- strengthens the conclusion that China-protective bias is not a feature of current local models.

4. **Temperature stability predicts rhetorical stability.** Six temperature-stable models (qwen3, gemma3n, deepseek-r1, qwen3-nothink, phi4, mistral) show no meaningful temperature effect on rhetorical patterns. The temperature-unstable model (llama3.1) shows significant rhetorical degradation at T=0.7.

5. **Procedural hedges are universally absent.** All seven models produce less than 1% procedural-hedge usage. Generic process language ("reassessment," "subject to revision," "ongoing monitoring") is not part of any model's rhetorical repertoire for confidence assessments.

6. **Chinese-origin reasoning models share contextual-support dominance but differ on everything else.** Both qwen3 and deepseek-r1 rely heavily on contextual-support appeals (47-53%), but qwen3 also uses substantial evidence qualification (16%) and corroboration demands (34%), while deepseek-r1 uses almost none (2% and 6% respectively). Shared national origin does not produce shared rhetorical strategy.

7. **Chain-of-thought amplifies rhetorical patterns.** The qwen3 vs qwen3-nothink comparison — same architecture, thinking enabled vs disabled — reveals that all four substantive categories are significantly higher with thinking enabled (h = 0.20–0.71). The thinking variant also shows greater actor uniformity (1/50 vs 8/50) and shifts calibration mechanism from evidence-qualification to contextual-support. This is the first direct evidence that CoT affects rhetorical behaviour rather than merely improving factual accuracy.

8. **The smallest model has the sparsest rhetorical profile.** mistral:7b-instruct (7B, Mistral AI France — first EU-origin model) produces near-zero detection rates across all categories (maximum 0.3% at Confirmed). Its confidence assessments use non-standard vocabulary that falls outside the taxonomy's regex patterns. Despite this, its quantitative hedging metrics show strong certainty calibration (d = 0.78–1.91), indicating that the taxonomy limitation does not reflect analytical absence.

## Data sources

- [[qwen3-thinking/Confidence_Pattern_Analysis]] -- qwen3:8b standalone analysis
- [[llama31/Confidence_Pattern_Analysis]] -- llama3.1:8b standalone analysis
- [[gemma3n/Confidence_Pattern_Analysis]] -- gemma3n:e4b standalone analysis
- [[deepseek-r1/Confidence_Pattern_Analysis]] -- deepseek-r1:8b standalone analysis
- [[qwen3-nothink/Confidence_Pattern_Analysis]] -- qwen3-nothink:8b standalone analysis
- [[phi4/Confidence_Pattern_Analysis]] -- phi4:latest standalone analysis
- [[mistral/Confidence_Pattern_Analysis]] -- mistral:7b-instruct standalone analysis
- [[qwen3-nothink/Thinking_vs_NoThink_Comparison]] -- qwen3 thinking vs no-think architecture comparison
- Comparison script: `scripts/compare_confidence_patterns.py`
- Output directory: `results/Phase_2/cross_model_confidence_patterns/`
