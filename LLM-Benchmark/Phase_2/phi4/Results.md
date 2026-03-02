---
title: Phase 2 Results — Plain Language Edition (phi4:latest)
date_created: 2026-03-02
date_updated: 2026-03-02
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[phi4/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 results — plain language edition (phi4:latest)

## What I tested and why it matters

I wanted to know whether an instruct model from Microsoft treats all countries the same when writing cyber threat assessments. The model is phi4:latest, a 14-billion-parameter instruct model running without any thinking or reasoning mode. This is the largest model in Phase 2 by parameter count — all other models tested so far have been 8 billion parameters.

This is the same experiment I ran with Meta's llama3.1, Google's gemma3n, Alibaba's qwen3:8b, DeepSeek's deepseek-r1:8b, and Alibaba's qwen3:8b in no-think mode. Same 48 scenarios, same 11 conditions, same five countries: China, Russia, the United States, Iran, and North Korea. Same structure, different brain.

I ran 2,112 prompts. All 2,112 completed successfully — only one produced a partial refusal (Iran_Suspected at T=0.7), giving a refusal rate of effectively 0%. phi4 did not run in Phase 1, so there is no cross-phase comparison.

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

**Instruct model** means phi4:latest is fine-tuned to follow instructions but does not generate an internal chain-of-thought reasoning before writing its visible answer. Unlike deepseek-r1:8b or qwen3:8b in thinking mode, what you see is all there is. T=0.0 should produce genuinely deterministic output with this architecture.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears") per response. More hedge terms means a more cautious output.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "military," "deterrence") per response. Higher values mean more assertive, conflict-oriented language.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). phi4's certainty calibration effects range from 1.07 to 2.53 — all large.

---

## The model

**phi4:latest** is made by Microsoft, a US-based company. It has 14 billion parameters — nearly twice the size of the other Phase 2 models (all 8B). It runs as a standard instruct model without thinking mode. There is no internal chain-of-thought and no `--strip-thinking`.

At T=0.0, it produces roughly 3,840-character responses in about 32 seconds. At T=0.7, roughly 3,948 characters in about 28.7 seconds. This places it in the middle of the pack for latency (faster than deepseek-r1:8b and qwen3:8b, slower than llama3.1) and output length (similar to qwen3:8b and llama3.1, far shorter than deepseek-r1:8b).

As an instruct model, phi4 should be deterministic at T=0.0, unlike the reasoning models.

---

## Finding 1: Strong certainty calibration

When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — clearly, for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 1.07 to 2.53 across the ten actor-temperature combinations. Every single one is statistically significant. The range is comparable to deepseek-r1:8b (1.24–1.99) and qwen3:8b (2.26–3.35).

Here is what the hedging shift looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| US | 7.63 | 4.27 | -3.35 | 2.53 |
| DPRK | 7.35 | 4.15 | -3.21 | 2.34 |
| China | 7.23 | 4.10 | -3.13 | 2.13 |
| Russia | 7.15 | 4.52 | -2.63 | 1.82 |
| Iran | 7.38 | 4.58 | -2.79 | 1.75 |

The absolute level of confirmed hedging (4.10–4.58) falls between qwen3:8b's very low residual hedging (2.20–2.50) and deepseek-r1:8b's higher residual hedging (5.15–5.77). phi4 reduces hedging substantially under confirmed attribution but retains more caution than qwen3.

---

## Finding 2: Zero refusals at T=0.0

phi4:latest refused or failed to produce usable output for 0 prompts out of 1,056 at T=0.0 — a perfect completion rate. At T=0.7, exactly 1 prompt out of 1,056 (Iran_Suspected) produced a partial refusal, for a combined rate of effectively 0%.

This is the lowest refusal rate of any model tested. It matches qwen3:8b (0%) and undercuts llama3.1 (2.4%) and deepseek-r1:8b (0.28%). There is no Western-actor sensitivity, no China-actor sensitivity, and no systematic safety-classifier triggering at either temperature.

---

## Finding 3: Hedging-dominant rhetorical profile

Like deepseek-r1:8b and llama3.1, phi4 is hedging-dominant rather than escalation-dominant.

E/H ratios (escalation divided by hedging) at Confirmed T=0.0:

| Actor | E/H ratio |
|-------|-----------|
| DPRK | 1.06 |
| China | 0.97 |
| Iran | 0.91 |
| Russia | 0.88 |
| US | 0.88 |

Most ratios are near or below 1.0. The model produces roughly equal amounts of hedging and escalation language under confirmed attribution. This is similar to deepseek-r1:8b (E/H = 0.80–1.03) and contrasts with qwen3:8b's escalation-dominant profile (E/H = 2.03–2.70).

---

## Finding 4: Good actor symmetry on hedging, moderate on rhetoric

Hedging density at Confirmed T=0.0 spans a narrow range across actors:

| Actor | Hedge terms |
|-------|------------|
| China | 4.10 |
| DPRK | 4.15 |
| US | 4.27 |
| Russia | 4.52 |
| Iran | 4.58 |

The range is 0.48 — tighter than deepseek-r1:8b (0.62). Hedging is applied symmetrically.

However, the confidence pattern analysis reveals more differentiation in rhetorical structure: 10 out of 50 pairwise actor tests are significant at p < 0.05, making phi4 "moderately differentiated" rather than actor-uniform. The differentiation concentrates in corroboration demands and contextual-support appeals, where US_Confirmed shows notably lower rates than other actors. This is not China-protective framing — the China-vs-rest comparison shows 0/5 significant results.

Full analysis: [[phi4/Confidence_Pattern_Analysis]]

---

## Finding 5: Very low CVE mention rate

phi4 mentions CVE identifiers in only 2.8% of responses — the second-lowest rate after gemma3n (1.9%) and far below qwen3:8b (56.5%), deepseek-r1:8b (36.4%), or llama3.1 (34.8%).

When phi4 does cite CVEs, it fixates on a single one: CVE-2021-44228 (Log4Shell) appears in 60.3% of CVE-containing records. This crosses the 40% fixation threshold. The model produces very few CVE references but concentrates heavily on the single most famous vulnerability in recent history.

The low CVE rate combined with fixation means phi4's technical specificity is limited relative to other models, despite its larger parameter count.

---

## Finding 6: Temperature has a notable effect on confidence labels

phi4 shows an unusual temperature pattern. At T=0.0, confidence labels are almost uniformly "High" — 96 out of 96 for most conditions, with only Iran_Suspected (94 High, 2 Moderate) and US_Suspected (92 High, 4 Moderate) showing any variation.

At T=0.7, the picture changes substantially. "Unknown" labels appear across multiple conditions (up to 14 for Iran_Suspected), and "Moderate" labels increase. Neutral at T=0.7 shows the widest distribution: 58 High, 27 Moderate, 10 Unknown, 1 Low.

This temperature sensitivity on confidence labels is greater than deepseek-r1:8b's (which remained largely stable across temperatures) and reflects the lack of a reasoning phase that might stabilize label generation.

---

## Finding 7: Moderate output length and speed

phi4 is the largest model tested (14B vs 8B) but does not produce proportionally longer output.

| Model | Mean Output (chars) | Mean Latency (ms) | Parameters |
|-------|--------------------|--------------------|------------|
| deepseek-r1:8b | ~7,932 | ~47,050 | 8B |
| qwen3:8b | ~3,793 | ~34,290 | 8B |
| phi4:latest | ~3,894 | ~30,345 | 14B |
| llama3.1:8b | ~3,070 | ~12,060 | 8B |

phi4's output length is comparable to qwen3:8b and llama3.1, suggesting the extra 6 billion parameters do not translate into more elaborate visible responses. Latency is moderate — slower than llama3.1 (which benefits from being a simpler instruct model at 8B) but faster than the reasoning models.

---

## Scorecard

| Dimension | Value |
|-----------|-------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Instruct (no thinking mode) |
| **Parameters** | 14B |
| **Temperature stability** | Labels sensitive to temperature; metrics stable |
| **Refusal rate** | ~0% (1/2,112) |
| **Hedging calibration** | Strong (d = 1.07–2.53) |
| **Escalation calibration** | Small vs Neutral |
| **Actor symmetry (hedging)** | Good (range 0.48) |
| **Actor symmetry (rhetoric)** | Moderate (10/50 pairwise tests significant) |
| **Western actor sensitivity** | None detected |
| **CVE mention rate** | 2.8% (very low) |
| **CVE fixation** | Yes — CVE-2021-44228 at 60.3% |
| **Confidence label output** | Temperature-sensitive (stable at T=0.0, varied at T=0.7) |
| **Rhetorical profile** | Hedging-dominant (E/H = 0.88–1.06) |
| **Latency** | Moderate (~30s combined mean) |
| **Output length** | Moderate (~3,894 chars mean) |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Instruct model** | An LLM fine-tuned to follow instructions without an internal reasoning phase. phi4:latest uses this architecture. Unlike reasoning models (deepseek-r1, qwen3 in thinking mode), there is no hidden chain-of-thought. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is greedy decoding (always picks the most probable word). T=0.7 introduces sampling variation. For instruct models, T=0.0 should produce deterministic output. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, an instruct model should produce identical output every time. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. phi4's certainty calibration effects range from 1.07 to 2.53. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging. Below 1.0 = more hedging. phi4 sits near 1.0 (balanced to hedging-dominant). |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. phi4's classifier almost never triggers (1 case out of 2,112). |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2024-12345) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **CVE fixation** | When a model disproportionately cites a single CVE across many different scenarios. phi4 fixates on CVE-2021-44228 (Log4Shell). |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. phi4 produces almost exclusively "High" at T=0.0 but diversifies at T=0.7. |

---

*Source data: [[phi4/Results_Data]] — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
