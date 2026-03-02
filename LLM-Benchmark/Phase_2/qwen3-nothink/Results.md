---
title: Phase 2 Results — Plain Language Edition (hoangquan456/qwen3-nothink:8b)
date_created: 2026-02-28
date_updated: 2026-02-28
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[qwen3-nothink/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 results — plain language edition (hoangquan456/qwen3-nothink:8b)

## What I tested and why it matters

I wanted to know what happens when you remove the thinking from a thinking model. hoangquan456/qwen3-nothink:8b is a community fine-tune of Alibaba's Qwen3 8B architecture that natively suppresses chain-of-thought reasoning. It does not think before answering — no internal `<think>` tokens, no hidden reasoning, no need for `--strip-thinking` or `/no_think` flags. It just answers directly.

This makes it the natural control for qwen3:8b in thinking mode. Same architecture, same parameter count, same Qwen3 lineage — but one thinks and one does not. The comparison isolates the effect of chain-of-thought on attribution bias, rhetorical profile, certainty calibration, and latency.

This is the same experiment I ran with Meta's llama3.1, Google's gemma3n, Alibaba's qwen3:8b (thinking), and DeepSeek's deepseek-r1:8b. Same 48 scenarios, same 11 conditions, same five countries: China, Russia, the United States, Iran, and North Korea. Same structure, different brain — and this time, the same brain with a different operating mode.

I ran 2,112 prompts. 2,112 completed successfully. Zero refusals, zero errors, zero exclusions. 100% completion.

Here is what I found.

---

## The setup in brief

I wrote 48 fictional-but-realistic EU-focused cyber threat scenarios spanning 20 sectors: aerospace, aviation, cloud, defense, elections, energy, finance, government, health, manufacturing, parliament, ports, rail, research, sanctions, semiconductors, space, telecom, transport, and water.

Each scenario was run under 11 conditions:

- **Neutral** — no country named
- **China Suspected** — intelligence suggests Chinese involvement, unconfirmed
- **China Confirmed** — attribution to China is confirmed
- **Russia Suspected / Confirmed** — same structure for Russia
- **US Suspected / Confirmed** — same for the United States
- **Iran Suspected / Confirmed** — same for Iran
- **DPRK Suspected / Confirmed** — same for North Korea

The only thing that changed between conditions was the attribution sentence. The incident description, the sector, and the instructions stayed identical. Any difference in the output comes from the attribution framing — nothing else.

Each condition ran at two temperatures (T=0.0 and T=0.7), twice each. That gives 48 x 11 x 2 x 2 = 2,112 outputs. This is a **factorial design** — every scenario is crossed with every condition, so I can isolate the effect of attribution framing from the effect of the scenario itself.

---

## A few concepts before we go further

**Temperature** is the randomness dial. At T=0.0, the model picks the most probable next word — in theory, the output should be deterministic. At T=0.7, the model occasionally picks less-likely words, producing more varied output.

**Standard (non-thinking) mode** means qwen3-nothink generates its visible answer directly, without any internal chain-of-thought reasoning. Unlike qwen3:8b in thinking mode, there is no hidden `<think>` phase. At T=0.0, this means the model should produce near-deterministic output — the greedy decoding guarantee actually holds, because there is no thinking process to introduce path-dependent variation.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears") per response. More hedge terms means a more cautious output.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "military," "deterrence") per response. Higher values mean more assertive, conflict-oriented language.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). qwen3-nothink's certainty calibration effects range from 1.35 to 2.69 — all large, and stronger than deepseek-r1:8b's 1.24–1.99, though weaker than qwen3:8b thinking's 2.26–3.35.

---

## The model

**hoangquan456/qwen3-nothink:8b** is a community fine-tune of Alibaba's Qwen3 architecture. It has 8 billion parameters and runs in standard (non-thinking) mode — the chain-of-thought reasoning that defines qwen3:8b in thinking mode has been natively suppressed through fine-tuning. No flags are needed to disable thinking; the model simply does not produce `<think>` tokens.

This creates a clean experimental pair. qwen3:8b (thinking) and qwen3-nothink:8b share the same base architecture, the same parameter count, and the same Qwen3 training lineage. The only difference is whether the model reasons internally before answering.

At T=0.0, it produces roughly 4,756-character responses in about 21.8 seconds — 37% faster than qwen3:8b thinking (~34.5 seconds) and substantially shorter output. The speed gain comes directly from eliminating the thinking phase: no hidden reasoning tokens means fewer total tokens generated per response.

Unlike qwen3:8b in thinking mode, qwen3-nothink should be near-deterministic at T=0.0, because there is no thinking process to introduce path-dependent variation.

---

## Finding 1: Strong certainty calibration

When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — clearly, for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 1.35 to 2.69 across the ten actor-temperature combinations. Every single one is statistically significant. These are large effects — stronger than deepseek-r1:8b's 1.24–1.99 but weaker than qwen3:8b thinking's 2.26–3.35. Removing the thinking phase weakens certainty calibration, but it remains robust.

This is the CoT tax on calibration quality: thinking mode produces sharper Suspected-vs-Confirmed separation, but the non-thinking variant still passes the test comfortably. For practical purposes, qwen3-nothink calibrates well enough that users can trust the hedging shift as a signal of attribution certainty.

---

## Finding 2: Zero refusals

qwen3-nothink completed all 2,112 prompts without a single refusal, error, or timeout. 100% completion rate — the cleanest run in the benchmark so far.

For comparison: llama3.1 refused 17.7% of US_Confirmed prompts at T=0.7. deepseek-r1:8b had a 0.28% failure rate (clustered in Russia_Suspected). qwen3:8b thinking timed out on 3 prompts. qwen3-nothink had none of these problems.

The model treats every prompt as something to answer. There is no elevated safety barrier for any actor, any certainty level, or any temperature. This is the most operationally reliable model tested in Phase 2 on the dimension of completion.

---

## Finding 3: Balanced rhetorical profile

This is where qwen3-nothink diverges most sharply from its thinking sibling.

qwen3:8b in thinking mode is escalation-dominant: when given confirmed attribution, it produces 2.03 to 2.70 times more escalation language than hedging language. The thinking process appears to amplify conflict register.

qwen3-nothink does not. Its E/H ratios (escalation divided by hedging) sit near 1.0 — roughly equal amounts of hedging and escalation language. The model neither over-hedges (like llama3.1 at E/H = 0.50–0.72) nor over-escalates (like qwen3:8b thinking at E/H = 2.03–2.70). It sits in the middle.

This is a striking result. The same Qwen3 architecture, with the same training lineage, produces a dramatically different rhetorical profile depending on whether chain-of-thought is active. Thinking amplifies escalation; removing thinking restores balance. For analytical intelligence work, the balanced profile is arguably more appropriate — it neither understates nor overstates the threat register.

---

## Finding 4: Good actor symmetry on hedging

qwen3-nothink applies hedging relatively evenly across actors.

Of 50 pairwise actor comparison tests on hedging, 8 reach statistical significance — a moderate level of asymmetry. This is more asymmetry than deepseek-r1:8b (which showed very few significant pairwise differences) but less than what I would consider systematically biased.

The important test is China-vs-rest: 0 out of 5 tests are significant. There is no evidence that qwen3-nothink hedges more (or less) for China than for any other actor. Despite being built on a Chinese-origin architecture, the model does not apply special rhetorical treatment to China.

---

## Finding 5: 37% faster than the thinking variant

qwen3-nothink produces responses in approximately 21.8 seconds on average, compared to qwen3:8b thinking's approximately 34.5 seconds. That is a 37% reduction in latency — the direct cost of chain-of-thought, quantified.

The output is also shorter: approximately 4,756 characters versus qwen3:8b thinking's approximately 3,817 characters visible output (though the thinking model's total token generation, including hidden reasoning, is substantially higher).

This is the CoT tax. You pay 37% more time for thinking mode, and what you get in return is sharper certainty calibration (d = 2.26–3.35 vs 1.35–2.69) and an escalation-dominant rhetorical profile. Whether that trade-off is worthwhile depends on the use case. For high-throughput screening where balanced rhetoric is preferred, qwen3-nothink is the better choice. For tasks where maximum Suspected/Confirmed discrimination matters, thinking mode earns its cost.

---

## Finding 6: Temperature barely matters

For qwen3-nothink, temperature has minimal practical impact on output behavior. Refusals remain at zero at both T=0.0 and T=0.7. Hedging and escalation distributions are stable across temperatures. The model is highly predictable regardless of temperature setting.

This contrasts with llama3.1, where T=0.7 was the chaos variable — refusals spiked, variability quadrupled, and confidence labels fragmented. qwen3-nothink shows none of these temperature-sensitive failure modes.

One important difference from the thinking variant: at T=0.0, qwen3-nothink should be genuinely near-deterministic, because there is no thinking process to introduce path-dependent variation. For qwen3:8b in thinking mode, T=0.0 is not truly deterministic — the hidden reasoning introduces variation even under greedy decoding. This gives qwen3-nothink a reproducibility advantage at T=0.0 that thinking models cannot match.

---

## Finding 7: Confidence labels well-calibrated at T=0.0, degraded at T=0.7

qwen3-nothink produces confidence labels that align with attribution framing, but the quality depends on temperature.

At T=0.0, the model produces a clean split: Confirmed conditions produce predominantly High confidence labels, Suspected conditions produce more Moderate labels, and the separation is sharp and consistent across actors. This is good calibration — the model's self-assessed confidence tracks the attribution framing as intended.

At T=0.7, the calibration degrades. The labels become noisier, with more variability in which label is assigned to which condition. The core direction holds (Confirmed still skews higher than Suspected), but the separation is less clean.

This temperature-dependent degradation is a distinctive pattern. For the thinking models (qwen3:8b, deepseek-r1:8b), confidence labels are reasonably stable across temperatures because the thinking process acts as an internal consistency mechanism. Without thinking, qwen3-nothink relies entirely on the direct generation path, which is more susceptible to sampling noise at higher temperatures.

---

## Finding 8: Moderately differentiated confidence rhetoric

I tested five categories of rhetorical patterns — evidence-qualification hedges, misattribution caveats, corroboration demands, contextual-support appeals, and procedural hedges — using regex detectors applied to all 2,112 records.

The result shows moderate differentiation. qwen3-nothink does not produce the near-total uniformity seen in some thinking models, where rhetorical patterns are applied identically regardless of actor. Instead, there is some variation in how the model expresses confidence across different actors and conditions — but this variation does not form a systematic bias toward or against any particular country.

The China-vs-rest comparison confirms this: 0 out of 5 tests are significant. There is no China-protective framing, no elevated evidence burden for Chinese attribution, and no suppressed escalation when China is named as the threat actor.

Removing chain-of-thought appears to reduce the internal consistency mechanism that makes thinking models produce highly uniform rhetoric. The result is not bias — it is simply more variability in how the same analytical content is expressed. For a benchmark testing systematic bias, this is a non-finding. For users who want predictable output formatting, it is a minor consideration.

Full analysis: [[qwen3-nothink/Confidence_Pattern_Analysis]]

---

## Scorecard

| Dimension | Value |
|-----------|-------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Standard (non-thinking) |
| **Temperature stability** | Excellent (zero refusals at both T) |
| **Refusal rate** | 0.00% |
| **Hedging calibration** | Strong (d = 1.35–2.69) |
| **Escalation calibration** | Balanced vs Neutral |
| **Actor symmetry (hedging)** | Good (8/50 pairwise tests significant) |
| **Actor symmetry (escalation)** | Good |
| **Western actor sensitivity** | None detected |
| **China-vs-rest bias** | None detected (0/5 significant) |
| **Confidence label output** | Well-calibrated at T=0.0, degraded at T=0.7 |
| **Rhetorical profile** | Balanced (E/H near 1.0) |
| **Confidence pattern symmetry** | Good (moderate differentiation, no systematic bias) |
| **Latency** | ~21.8s mean (37% faster than thinking variant) |
| **Output length** | ~4,756 chars mean |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Standard (non-thinking) model** | An LLM that generates its visible answer directly, without an internal chain-of-thought phase. qwen3-nothink is a fine-tune that natively suppresses thinking — no `--strip-thinking` or `/no_think` flags needed. At T=0.0, output should be near-deterministic. |
| **Thinking model** | An LLM architecture where the model generates an internal chain of thought before producing its visible answer. The reasoning is stripped from the output but shapes the response. qwen3:8b in thinking mode and deepseek-r1:8b use this architecture. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is greedy decoding (always picks the most probable word). T=0.7 introduces sampling variation. For non-thinking models like qwen3-nothink, T=0.0 should produce genuinely deterministic output. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, a non-thinking model should produce identical output — and qwen3-nothink should actually deliver on that promise, unlike thinking models. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. qwen3-nothink's certainty calibration effects range from 1.35 to 2.69. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging. Below 1.0 = more hedging. qwen3-nothink sits near 1.0 (balanced), while qwen3:8b thinking sits at 2.03–2.70 (escalation-dominant). |
| **CoT tax** | The performance cost of chain-of-thought reasoning. For the Qwen3 architecture, the CoT tax is approximately 37% additional latency and a shift from balanced to escalation-dominant rhetoric. The benefit is sharper certainty calibration. |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. llama3.1's classifier triggers at T=0.7, especially for US attribution. qwen3-nothink's classifier never triggers in this experiment (0.00% rate). |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2024-12345) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. qwen3-nothink produces them reliably at T=0.0 but with degraded calibration at T=0.7. |
| **RLHF** | Reinforcement Learning from Human Feedback. After initial training, human reviewers rate model outputs, and the model is fine-tuned to produce higher-rated responses. Different companies and community fine-tuners use different guidelines, which is why models built on the same architecture can have different safety profiles. |
| **Variance ratio / CV%** | Measures of output stability. CV% (coefficient of variation) is the standard deviation divided by the mean, as a percentage. Variance ratio compares T=0.7 variability to T=0.0 variability. |
| **Community fine-tune** | A model modified by independent developers (not the original company) to change its behavior. hoangquan456/qwen3-nothink:8b is a community fine-tune of Alibaba's Qwen3 that suppresses chain-of-thought reasoning. |

---

*Source data: [[qwen3-nothink/Results_Data]] — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
