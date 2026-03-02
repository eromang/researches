---
title: Thinking vs No-Think Comparison — Qwen3 8B Architecture
date_created: 2026-02-28
date_updated: 2026-02-28
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[qwen3-thinking/Results_Data]]"
  - "[[qwen3-nothink/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

## 1. Motivation

This is the only model pair in Phase II that enables a direct comparison of the same architecture with and without chain-of-thought reasoning. `qwen3:8b` uses `--strip-thinking` (thinking enabled, CoT stripped from output). `qwen3-nothink:8b` is a community fine-tune that natively suppresses CoT without flags. Both are 8B parameter Qwen3 models running on the same benchmark (48 scenarios, 11 conditions, 2 temps, 2 reps).

## 2. Summary Table

| Dimension | qwen3:8b (thinking) | qwen3-nothink:8b |
|---|---|---|
| Records (ok) | 2,109 | 2,112 |
| Architecture | Reasoning (strip_thinking) | Standard (CoT suppressed) |
| Mean latency (combined) | ~34,300 ms | ~21,750 ms |
| Mean output (combined) | ~3,793 chars | ~4,756 chars |
| Refusal rate | 0% | 0% |
| Hedging calibration (d range) | 2.26--3.35 | 1.35--2.69 |
| E/H ratio at Confirmed (T=0.0) | 2.03--2.70 | 0.94--1.13 |
| Actor pairwise sig (confidence patterns) | 1/50 | 8/50 |
| China-vs-rest sig | 0/5 | 0/5 |
| Certainty calibration sig (rhetorical) | 7/25 | 6/25 |
| Confidence label Unknown (total) | ~5 | ~130+ at T=0.7 |
| T=0.0 determinism | Non-deterministic | Deterministic (expected) |

## 3. Hedging Calibration

Thinking variant shows d = 2.26--3.35 across actors. No-think shows d = 1.35--2.69. The thinking process amplifies hedging calibration -- the model that reasons internally before answering produces sharper hedging differentiation between Suspected and Confirmed conditions.

At T=0.0 Confirmed, thinking variant hedge means are 2.20--2.47 vs no-think's 4.04--4.77. Thinking reduces the absolute hedging level by roughly 50%, creating the larger effect sizes.

## 4. Rhetorical Profile Shift

The most dramatic difference. Thinking: E/H = 2.03--2.70 (escalation-dominant). No-think: E/H = 0.94--1.13 (balanced). Chain-of-thought reasoning transforms the model's rhetorical stance from balanced to escalation-dominant.

Thinking variant escalation at Confirmed T=0.0: 5.31--5.96. No-think: 4.35--4.58. Thinking increases escalation modestly (+15-25%) while halving hedging. The net effect is the dramatic E/H ratio shift.

## 5. Latency and Output Length

Thinking: ~34.3s, ~3,793 chars. No-think: ~21.8s, ~4,756 chars.

The thinking tax: 37% additional latency for 20% SHORTER output. The thinking process consumes computation but compresses visible output -- the internal reasoning replaces rather than supplements visible elaboration.

## 6. Actor Uniformity in Confidence Rhetoric

Thinking: 1/50 pairwise tests significant (actor-uniform). No-think: 8/50 significant (moderately differentiated). Chain-of-thought reasoning appears to impose uniformity on confidence rhetoric -- the internal deliberation smooths out actor-specific differences.

Both models show 0/5 China-vs-rest significance. Actor uniformity differs quantitatively but not on the China-specific dimension.

## 7. Confidence Label Quality

Thinking at T=0.0: near-perfect label parsing (~5 Unknown total). No-think at T=0.0: also clean. At T=0.7: thinking maintains good labels while no-think shows ~130 Unknown labels. The thinking process may stabilize structured output format compliance under temperature variation.

## 8. Strong Assertions

Thinking Confirmed: 0.88--1.38 strong assertions. No-think Confirmed: 0.42--0.65. Thinking roughly doubles the model's propensity for definitive claims. This tracks with the escalation-dominant profile -- the thinking process both reduces hedging and increases assertiveness.

## 9. Implications

1. **Thinking amplifies calibration.** The CoT process strengthens hedging differentiation (d increase of ~40%) but at the cost of 37% more latency.
2. **Thinking shifts rhetorical stance.** The same architecture produces balanced output without thinking and escalation-dominant output with thinking. This is a fundamental architectural effect, not a model-specific quirk.
3. **Thinking imposes actor uniformity.** The CoT process appears to smooth out actor-specific differences in confidence rhetoric (1/50 vs 8/50 significant).
4. **Thinking compresses visible output.** Internal reasoning replaces visible elaboration -- thinking produces shorter, more decisive output.
5. **The thinking tax is substantial.** 37% more latency for arguable quality improvements. Whether the stronger calibration justifies the cost depends on the downstream use case.
6. **Both modes are safe.** Zero refusals in both variants. The Alibaba safety profile is architecture-independent.
7. **Thinking stabilizes structured output.** Under temperature variation, thinking maintains cleaner confidence label formatting.
