---
title: Phase 2 Results — Plain Language Edition (mistral:7b-instruct)
date_created: 2026-03-02
date_updated: 2026-03-02
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[mistral/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 results — plain language edition (mistral:7b-instruct)

## What I tested and why it matters

I wanted to know whether a small instruct model from Mistral AI treats all countries the same when writing cyber threat assessments. The model is mistral:7b-instruct, a 7-billion-parameter instruct model running without any thinking or reasoning mode. This is the first EU-origin model in Phase 2 — Mistral AI is headquartered in Paris, France. All other models tested so far come from US or Chinese companies.

This is the same experiment I ran with Meta's llama3.1, Google's gemma3n, Alibaba's qwen3:8b, DeepSeek's deepseek-r1:8b, Alibaba's qwen3:8b in no-think mode, and Microsoft's phi4. Same 48 scenarios, same 11 conditions, same five countries: China, Russia, the United States, Iran, and North Korea. Same structure, different brain.

I ran 2,112 prompts. All 2,112 completed successfully with zero refusals — a perfect 0% refusal rate. mistral did not run in Phase 1, so there is no cross-phase comparison.

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

Each condition ran at two temperatures (T=0.0 and T=0.7), twice each. That gives 48 x 11 x 2 x 2 = 2,112 outputs.

---

## A few concepts before we go further

**Temperature** is the randomness dial. At T=0.0, the model picks the most probable next word — the output should be deterministic. At T=0.7, the model occasionally picks less-likely words, producing more varied output.

**Instruct model** means mistral:7b-instruct is fine-tuned to follow instructions but does not generate an internal chain-of-thought reasoning before writing its visible answer. Unlike deepseek-r1:8b or qwen3:8b in thinking mode, what you see is all there is. T=0.0 should produce genuinely deterministic output with this architecture.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears") per response. More hedge terms means a more cautious output.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "military," "deterrence") per response. Higher values mean more assertive, conflict-oriented language.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). mistral's certainty calibration effects range from 0.78 to 1.91 — all large.

---

## The model

**mistral:7b-instruct** is made by Mistral AI, a French company headquartered in Paris. It has 7 billion parameters — the smallest model in Phase 2. It runs as a standard instruct model without thinking mode. There is no internal chain-of-thought and no `--strip-thinking`.

This is the first EU-origin model in the benchmark. All other Phase 2 models come from US companies (Meta, Google, Microsoft) or Chinese companies (Alibaba, DeepSeek). The EU origin makes mistral a useful reference point for understanding whether a European-trained model exhibits different geopolitical biases than US- or Chinese-origin models.

At T=0.0, it produces roughly 3,442-character responses in about 14.8 seconds. At T=0.7, roughly 3,597 characters in about 15.6 seconds. This makes it the fastest model in Phase 2 and the one with the shortest output.

---

## Finding 1: Strong certainty calibration

When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — clearly, for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 0.78 to 1.91 across the ten actor-temperature combinations. Every single one is statistically significant. The range overlaps with deepseek-r1:8b (1.24–1.99) and sits below phi4 (1.07–2.53) and qwen3:8b (2.26–3.35).

Here is what the hedging shift looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| Iran | 2.90 | 0.62 | -2.27 | 1.91 |
| China | 3.12 | 1.00 | -2.12 | 1.61 |
| US | 3.00 | 0.88 | -2.12 | 1.54 |
| Russia | 2.71 | 0.85 | -1.85 | 1.44 |
| DPRK | 2.83 | 1.02 | -1.81 | 1.31 |

The absolute level of confirmed hedging (0.62–1.02) is the lowest of any Phase 2 model. For comparison, phi4 retains 4.10–4.58 hedge terms at Confirmed, and even qwen3:8b retains 2.14–2.73. mistral almost entirely eliminates hedging under confirmed attribution.

---

## Finding 2: Zero refusals

mistral:7b-instruct refused or failed to produce usable output for 0 prompts out of 2,112 — a perfect completion rate at both temperatures. This matches phi4 and qwen3:8b (both ~0%) and undercuts llama3.1 (2.4%) and deepseek-r1:8b (0.28%).

There is no Western-actor sensitivity, no China-actor sensitivity, and no systematic safety-classifier triggering at either temperature.

---

## Finding 3: Escalation-dominant rhetorical profile

Unlike most other Phase 2 models, mistral is escalation-dominant rather than hedging-dominant. This is a distinctive rhetorical posture.

E/H ratios (escalation divided by hedging) at Confirmed T=0.0:

| Actor | E/H ratio |
|-------|-----------|
| Iran | 1.95 |
| US | 1.42 |
| Russia | 1.25 |
| DPRK | 1.15 |
| China | 1.12 |

All ratios exceed 1.0, meaning the model consistently produces more escalation language than hedging language under confirmed attribution. This is the opposite of deepseek-r1:8b (E/H = 0.80–1.03), phi4 (E/H = 0.88–1.06), and llama3.1, and closer to — but different from — qwen3:8b's escalation-dominant profile (E/H = 2.03–2.70).

---

## Finding 4: Good actor symmetry on hedging

Hedging density at Confirmed T=0.0 spans a narrow range across actors:

| Actor | Hedge terms |
|-------|------------|
| Iran | 0.62 |
| Russia | 0.85 |
| US | 0.88 |
| China | 1.00 |
| DPRK | 1.02 |

The range is 0.40 — the tightest of any Phase 2 model (phi4 = 0.48, deepseek-r1 = 0.62). Hedging is applied symmetrically across all five actors.

The confidence pattern analysis reveals near-zero rhetorical pattern detection across all categories: 0 out of 50 pairwise actor tests are significant at p < 0.05, making mistral the most actor-uniform model in the confidence pattern taxonomy. The China-vs-rest comparison shows 0/5 significant results.

Full analysis: [[mistral/Confidence_Pattern_Analysis]]

---

## Finding 5: Moderate CVE mention rate with no fixation

mistral mentions CVE identifiers in 10.9% of responses — placing it in the middle of the pack between the high-CVE models (qwen3 at 56.5%, deepseek-r1 at 36.4%) and the low-CVE models (phi4 at 2.8%, gemma3n at 1.9%).

The top CVE is CVE-2019-19781 (Citrix ADC vulnerability) at 28.7% of CVE-containing records. This is below the 40% fixation threshold, so mistral does not exhibit CVE fixation — unlike deepseek-r1, llama3.1, and phi4.

The model cites 94 unique CVEs across 230 CVE-containing records, giving it a Shannon diversity of 5.263 (normalised 0.803) — the second-highest diversity after gemma3n (0.910). mistral spreads its CVE references more broadly than any other model except gemma3n.

---

## Finding 6: Confidence labels are mostly absent

mistral shows an unusual confidence label pattern. At T=0.0, the model's confidence assessment text does not contain standard "High," "Moderate," or "Low" keywords in any condition — all 1,056 records return "Unknown" under the label extraction regex. The model writes confidence assessments but uses non-standard language that does not match the expected label vocabulary.

At T=0.7, some standard labels emerge: a handful of "High" labels appear for Confirmed conditions (5–10 per condition), and "Moderate" labels appear for Suspected conditions (5–9 per condition). But the vast majority remain "Unknown."

This is the most divergent label profile in Phase 2. All other models produce clear, extractable confidence labels at both temperatures.

---

## Finding 7: Fastest and shortest output

mistral:7b-instruct is the fastest and most compact model in Phase 2.

| Model | Mean Output (chars) | Mean Latency (ms) | Parameters |
|-------|--------------------|--------------------|------------|
| deepseek-r1:8b | ~7,932 | ~47,050 | 8B |
| qwen3:8b | ~3,793 | ~34,290 | 8B |
| phi4:latest | ~3,894 | ~30,345 | 14B |
| qwen3-nothink | ~3,503 | ~17,000 | 8B |
| gemma3n | ~3,500 | ~14,500 | 8B |
| llama3.1:8b | ~3,070 | ~12,060 | 8B |
| mistral:7b-instruct | ~3,520 | ~15,200 | 7B |

At 7B parameters, mistral produces output comparable in length to the 8B instruct models while running at roughly the same speed as llama3.1 and gemma3n. The smaller parameter count does not visibly reduce output quality or length.

---

## Finding 8: Significant escalation under confirmed attribution

Unlike most other models (which calibrate primarily through hedging reduction), mistral shows significant escalation increases under confirmed attribution at T=0.0. All five Confirmed-vs-Neutral escalation comparisons are significant:

| Actor | Confirmed Esc | Neutral Esc | Delta | Cohen's d |
|-------|--------------|-------------|-------|-----------|
| US | 1.25 | 0.58 | +0.67 | 0.86 |
| Iran | 1.21 | 0.58 | +0.63 | 0.71 |
| DPRK | 1.17 | 0.58 | +0.59 | 0.67 |
| China | 1.12 | 0.58 | +0.54 | 0.65 |
| Russia | 1.06 | 0.58 | +0.48 | 0.61 |

This dual-channel calibration (hedging reduction plus escalation amplification) distinguishes mistral from other models which primarily reduce hedging without increasing escalation.

---

## Scorecard

| Dimension | Value |
|-----------|-------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Instruct (no thinking mode) |
| **Parameters** | 7B (smallest in Phase II) |
| **Origin** | Mistral AI (France, EU) — first EU-origin model |
| **Temperature stability** | Good on metrics; labels mostly absent at T=0.0 |
| **Refusal rate** | 0% (0/2,112) |
| **Hedging calibration** | Strong (d = 0.78–1.91) |
| **Escalation calibration** | Strong vs Neutral (d = 0.61–0.86 at T=0.0) |
| **Actor symmetry (hedging)** | Strong (range 0.40) |
| **Actor symmetry (rhetoric)** | Very strong (0/50 pairwise tests significant) |
| **Western actor sensitivity** | None detected |
| **CVE mention rate** | 10.9% (moderate) |
| **CVE fixation** | No — top CVE at 28.7% |
| **Confidence label output** | Mostly absent at T=0.0; sparse at T=0.7 |
| **Rhetorical profile** | Escalation-dominant (E/H = 1.12–1.95) |
| **Latency** | Fast (~15s combined mean) |
| **Output length** | Moderate (~3,520 chars mean) |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Instruct model** | An LLM fine-tuned to follow instructions without an internal reasoning phase. mistral:7b-instruct uses this architecture. Unlike reasoning models (deepseek-r1, qwen3 in thinking mode), there is no hidden chain-of-thought. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is greedy decoding (always picks the most probable word). T=0.7 introduces sampling variation. For instruct models, T=0.0 should produce deterministic output. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, an instruct model should produce identical output every time. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. mistral's certainty calibration effects range from 0.78 to 1.91. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging. Below 1.0 = more hedging. mistral sits above 1.0 (escalation-dominant). |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. mistral's classifier never triggers (0 cases out of 2,112). |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2024-12345) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **CVE fixation** | When a model disproportionately cites a single CVE across many different scenarios. mistral does not fixate (top CVE at 28.7%). |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. mistral rarely produces extractable labels. |

---

*Source data: [[mistral/Results_Data]] — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
