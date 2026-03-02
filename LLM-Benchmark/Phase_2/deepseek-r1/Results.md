---
title: Phase 2 Results — Plain Language Edition (deepseek-r1:8b)
date_created: 2026-02-28
date_updated: 2026-02-28
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[deepseek-r1/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 results — plain language edition (deepseek-r1:8b)

## What I tested and why it matters

I wanted to know whether a reasoning model from a Chinese company — one that is not Alibaba — treats all countries the same when writing cyber threat assessments. The model is DeepSeek's deepseek-r1:8b, running in thinking mode with the internal chain of thought stripped from visible output. DeepSeek is a Chinese company, like Alibaba, but it is a different organisation with a different development lineage and different alignment choices.

This is the same experiment I ran with Meta's llama3.1, Google's gemma3n, and Alibaba's qwen3:8b. Same 48 scenarios, same 11 conditions, same five countries: China, Russia, the United States, Iran, and North Korea. Same structure, different brain. deepseek-r1:8b also ran in Phase 1, where I had 400 records and only two actors (China and Russia). Phase 2 expands to 2,113 records and five actors, which gives me a much stronger basis for comparison — and a direct cross-phase check on whether Phase 1 patterns were real or noise.

I ran 2,113 prompts. 2,107 completed successfully. Six produced errors or were excluded. Everything else worked.

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

Each condition ran at two temperatures (T=0.0 and T=0.7), twice each. That gives 48 x 11 x 2 x 2 = 2,112 outputs, minus 6 failures = 2,107 valid records. This is a **factorial design** — every scenario is crossed with every condition, so I can isolate the effect of attribution framing from the effect of the scenario itself.

---

## A few concepts before we go further

**Temperature** is the randomness dial. At T=0.0, the model picks the most probable next word — in theory, the output should be deterministic. At T=0.7, the model occasionally picks less-likely words, producing more varied output.

**Thinking mode** means deepseek-r1:8b generates an internal chain-of-thought reasoning before writing its visible answer. This thinking is stripped from the output using `--strip-thinking` (you never see it), but it shapes everything the model writes. Like qwen3:8b, this means T=0.0 is not truly deterministic — the thinking process introduces path-dependent variation even under greedy decoding.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears") per response. More hedge terms means a more cautious output.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "military," "deterrence") per response. Higher values mean more assertive, conflict-oriented language.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). deepseek-r1:8b's certainty calibration effects range from 1.24 to 1.99 — all large, but weaker than qwen3:8b's 2.26–3.35.

---

## The model

**deepseek-r1:8b** is made by DeepSeek, a Chinese AI company. It has 8 billion parameters and runs in thinking mode — an architecture where the model generates internal reasoning before producing its visible response. The thinking is stripped (`--strip-thinking`), so you only see the final answer, but the reasoning shapes it.

This is the same configuration used in Phase 1, where deepseek-r1:8b ran against China and Russia scenarios only. Phase 2 adds three more actors (US, Iran, DPRK) and substantially more data.

At T=0.0, it produces roughly 7,932-character responses in about 44.5 seconds — the slowest and longest model I have tested. That is more than twice the output length of qwen3:8b (3,817 chars, 35 seconds) and three times the length of llama3.1 (3,070 chars, 13 seconds). The extra time and length come from a reasoning mode that appears to generate more elaborate visible responses than qwen3:8b's thinking architecture, even though both strip the internal `<think>` tokens.

Like qwen3:8b, deepseek-r1:8b is not deterministic at T=0.0. The thinking process introduces variation even when the decoding is greedy.

---

## Finding 1: Certainty calibration is strong

When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — clearly, for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 1.24 to 1.99 across the ten actor-temperature combinations. Every single one is statistically significant. These are large effects — but noticeably weaker than qwen3:8b's 2.26–3.35. The core signal is there; the model responds correctly to the Suspected/Confirmed distinction. It just responds less dramatically than qwen3:8b does.

Here is what the hedging shift looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| DPRK | 8.42 | 5.21 | -3.21 | ~1.99 |
| US | 8.88 | 5.69 | -3.19 | ~1.96 |
| Russia | 7.88 | 5.15 | -2.73 | ~1.74 |
| China | 8.19 | 5.67 | -2.52 | ~1.58 |
| Iran | 8.21 | 5.77 | -2.44 | ~1.24 |

The most important detail in this table is the absolute level of confirmed hedging. deepseek-r1:8b's Confirmed hedge counts (5.15–5.77) are far higher than qwen3:8b's (2.20–2.50). The model does reduce hedging when attribution is confirmed — but it remains substantially more cautious under Confirmed conditions than qwen3:8b. It never fully commits the way qwen3:8b does.

---

## Finding 2: Near-zero refusals

deepseek-r1:8b refused or failed to produce usable output for approximately 6 prompts out of 2,113 — a refusal rate of 0.28%. Nearly all of the failures cluster in one place: Russia_Suspected at T=0.0, where 3 of 97 prompts (3.09%) produced refusals or unusable output. No other condition approaches that level.

This is almost the opposite of llama3.1's pattern, where 17.7% of US_Confirmed prompts at T=0.7 were refused. deepseek-r1:8b shows no Western-actor sensitivity at all. The one cluster of failures is for Russia_Suspected at T=0.0 — a different actor, a different condition, and at a level that is probably noise given the small count (3 cases).

Like qwen3:8b, the Chinese-origin reasoning architecture here imposes no elevated safety barrier for US attribution. The model treats every prompt as something to answer rather than something to evaluate for safety.

---

## Finding 3: Hedging-dominant rhetorical profile

This is the sharpest difference between deepseek-r1:8b and qwen3:8b, and it matters for how you interpret the outputs.

qwen3:8b, when given confirmed attribution, produces 2.2 to 2.7 times more escalation language than hedging language — an escalation-dominant profile. It gets less cautious and more aggressive simultaneously.

deepseek-r1:8b does not. Its E/H ratios (escalation divided by hedging) at Confirmed T=0.0 are:

| Actor | E/H ratio |
|-------|-----------|
| DPRK | 1.03 |
| Russia | 1.02 |
| China | 0.91 |
| Iran | 0.93 |
| US | 0.80 |

All of these are near or below 1.0. The model produces roughly equal amounts of hedging and escalation language, or slightly more hedging than escalation. This is closer to llama3.1's profile (E/H = 0.50–0.72) than to qwen3:8b's.

In plain terms: deepseek-r1:8b reduces hedging when attribution is confirmed, but it does not ramp up conflict language the way qwen3:8b does. Its response to certainty is modulation of caution, not amplification of threat register. The two Chinese-origin reasoning models are quite different in this dimension.

---

## Finding 4: Good actor symmetry on hedging

Despite the higher absolute hedging levels, deepseek-r1:8b applies them relatively evenly across actors.

At T=0.0 Confirmed, hedging density spans a narrow range:

| Actor | Hedge terms |
|-------|------------|
| Russia | 5.15 |
| DPRK | 5.21 |
| China | 5.67 |
| US | 5.69 |
| Iran | 5.77 |

When I ran pairwise statistical tests comparing every actor pair on hedging at the Confirmed level, few comparisons reach significance. The model does not systematically hedge more for one country than another when attribution is confirmed.

One notable asymmetry is on strong assertions: US_Confirmed consistently produces fewer strong assertion terms than Russia_Confirmed (d ≈ -0.45) at T=0.0. The model makes fewer definitive claims when attributing to the US — a mild pattern that echoes findings in qwen3:8b, though the direction is the same and the magnitude is smaller.

On escalation, the key comparison is US_Confirmed vs Russia_Confirmed: US produces consistently lower escalation density (d ≈ -0.45). The model writes slightly less conflict-oriented language for US attribution than for Russian attribution.

---

## Finding 5: The slowest and longest model tested

deepseek-r1:8b is the most computationally expensive model in this benchmark on both dimensions I measured.

- Mean latency: approximately 44.5 seconds per response (vs qwen3:8b's 35 seconds, llama3.1's 13 seconds)
- Mean output length: approximately 7,932 characters (vs qwen3:8b's 3,817, llama3.1's 3,070)

That output length is striking. deepseek-r1:8b produces more than twice as many characters as qwen3:8b, even though both are 8-billion-parameter reasoning models with `--strip-thinking`. The visible responses are simply longer — more elaborated, more structured, with more content per answer.

What do you get for that cost? Strong but not exceptional certainty calibration (d = 1.24–1.99), near-zero refusals, good actor symmetry, and a hedging-dominant profile that is arguably more appropriate for analytical intelligence work than qwen3:8b's escalation-heavy outputs. Whether the length-to-quality trade-off is worthwhile depends on the use case.

---

## Finding 6: Temperature has minimal effect

For llama3.1, temperature was the chaos variable. At T=0.7, refusals spiked, variability quadrupled, and confidence labels fragmented.

For deepseek-r1:8b, temperature barely matters. Refusals remain near zero at both temperatures. Hedging and escalation distributions are nearly identical across T=0.0 and T=0.7. The model's outputs at T=0.7 are statistically indistinguishable from its outputs at T=0.0 on most measures.

As with qwen3:8b, this means T=0.0 does not give you the deterministic guarantee you might expect from a non-reasoning model. The thinking process introduces variation regardless of temperature setting. But it also means the model is highly predictable in practice — you get similar behavior whether you set T=0.0 or T=0.7.

---

## Finding 7: Confidence labels are reasonably calibrated

deepseek-r1:8b produces confidence labels that align with attribution framing, though with a less clean split than qwen3:8b.

At T=0.0:

- **Confirmed conditions** produce predominantly High labels (76–90 out of 96 responses per condition)
- **Suspected conditions** produce predominantly High but with more Moderate labels (74–84 High out of 96)
- **Neutral** produces a mix

The separation is real but imperfect. deepseek-r1:8b assigns "High" confidence to Suspected conditions at higher rates than qwen3:8b does. The model is confident even when attribution is uncertain — which tracks with its generally more verbose and elaborated response style.

Russia_Suspected at T=0.0 shows 3 Unknown labels, corresponding to the 3.09% refusal cluster noted in Finding 2.

At T=0.7, Unknown labels appear in small numbers (1–3) across several conditions. This is in contrast to llama3.1 at T=0.7, which produced hundreds of Unknown labels. deepseek-r1:8b's output remains structurally reliable across temperatures.

---

## Finding 8: Actor-uniform confidence rhetoric

I tested five categories of rhetorical patterns — evidence-qualification hedges, misattribution caveats, corroboration demands, contextual-support appeals, and procedural hedges — using 28 regex detectors applied to all 2,107 valid records.

The result is clear: 1 out of 50 pairwise actor tests is significant (Russia vs DPRK on contextual support). That single result is borderline and does not survive multiple-comparison correction.

The China-vs-rest comparison shows 0 significant results out of 5 tests. There is no evidence that deepseek-r1:8b applies special rhetorical treatment to China — no elevated corroboration demands that would imply skepticism of attribution, and no reduced escalation that would imply reluctance to name China as a threat.

What does shift systematically is certainty level: evidence-qualification hedges, corroboration demands, and contextual-support appeals all drop from Suspected to Confirmed for all five actors (13 of 25 certainty-shift tests significant). The model uses these rhetorical tools to signal certainty, and it applies them uniformly regardless of which country is named.

The dominant hedging mechanism in deepseek-r1:8b's vocabulary is the phrase cluster around "definitive proof" and "definitive attribution" — slightly different from qwen3:8b's "further corroboration" pattern, and worth noting in cross-phase comparison.

Full analysis: [[deepseek-r1/Confidence_Pattern_Analysis]]

---

## Scorecard

| Dimension | Value |
|-----------|-------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Reasoning (thinking mode) |
| **Temperature stability** | Good (near-zero refusals at both T) |
| **Refusal rate** | 0.28% |
| **Hedging calibration** | Strong (d = 1.24–1.99) |
| **Escalation calibration** | Small vs Neutral |
| **Actor symmetry (hedging)** | Good |
| **Actor symmetry (escalation)** | Good (US lower than Russia) |
| **Western actor sensitivity** | None detected |
| **CVE mention rate** | ~36% |
| **Confidence label output** | Reasonably calibrated |
| **Rhetorical profile** | Hedging-dominant (E/H ≈ 0.80–1.03) |
| **Confidence pattern symmetry** | Excellent (1/50 pairwise tests significant) |
| **Latency** | Slowest tested (~44.5s mean) |
| **Output length** | Longest tested (~7,932 chars mean) |

---

## Cross-phase check: does Phase 1 hold up?

Phase 1 ran deepseek-r1:8b against 400 records and two actors only (China and Russia). It found that "further corroboration" appeared at roughly 2.0x the rate for China/Russia combined on Suspected conditions, suggesting an elevated evidence-burden pattern.

Phase 2 tells a more complicated story. With 2,107 records and five actors, the ratio inverts to approximately 0.6x — Russia now shows higher rates of corroboration-demand language than China in the Suspected condition. The Phase 1 pattern does not replicate cleanly.

The dominant hedging mechanism in Phase 2 is the "definitive proof/attribution" cluster rather than "further corroboration." deepseek-r1:8b has a strong vocabulary preference for "definitive" framings when expressing epistemic caution, and this pattern is actor-uniform.

Whether Phase 1's "further corroboration" signal was a genuine China-specific pattern or a small-sample artifact is difficult to resolve with certainty. The Phase 2 evidence leans toward artifact: a 400-record run with two actors and one or two distinctive phrases is not a stable enough foundation to conclude systematic China-protective framing, especially when Phase 2's much larger dataset shows no such pattern.

Note also that Phase 1's CVE-2021-4034 (PwnKit) fixation — where deepseek-r1:8b disproportionately cited that specific vulnerability — needs a dedicated check in Phase 2 data. The overall CVE mention rate in Phase 2 is approximately 36%, lower than qwen3:8b's 56.5%, suggesting the model's CVE referencing behavior may have shifted across phases or scenarios.

Full analysis: [[deepseek-r1/Cross_Phase_Comparison]]

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Reasoning model / thinking mode** | An LLM architecture where the model generates an internal chain of thought before producing its visible answer. The reasoning is stripped from the output but shapes the response. deepseek-r1:8b uses this architecture with `--strip-thinking`. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is greedy decoding (always picks the most probable word). T=0.7 introduces sampling variation. For reasoning models, T=0.0 is not truly deterministic because the thinking phase introduces its own variation. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, a non-reasoning model should produce identical output. deepseek-r1:8b does not, because of its thinking process. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. deepseek-r1:8b's Confirmed hedging (5.15–5.77) is substantially higher than qwen3:8b's (2.20–2.50). |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. deepseek-r1:8b's certainty calibration effects range from 1.24 to 1.99. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging. Below 1.0 = more hedging. deepseek-r1:8b sits near or below 1.0 (hedging-dominant), while qwen3:8b sits above 1.0 (escalation-dominant). |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. llama3.1's classifier triggers at T=0.7, especially for US attribution. deepseek-r1:8b's classifier almost never triggers in this experiment (0.28% rate, clustered in Russia_Suspected). |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2024-12345) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. deepseek-r1:8b produces them reliably but with less clean bifurcation between Suspected and Confirmed conditions than qwen3:8b. |
| **RLHF** | Reinforcement Learning from Human Feedback. After initial training, human reviewers rate model outputs, and the model is fine-tuned to produce higher-rated responses. Different companies use different review guidelines, which is why Meta's llama3.1, Alibaba's qwen3:8b, and DeepSeek's deepseek-r1:8b have different safety profiles despite similar sizes and architectures. |
| **Variance ratio / CV%** | Measures of output stability. CV% (coefficient of variation) is the standard deviation divided by the mean, as a percentage. Variance ratio compares T=0.7 variability to T=0.0 variability. For deepseek-r1:8b, temperature has minimal effect on either measure. |
| **`--strip-thinking`** | A flag that removes the model's internal `<think>...</think>` tokens from visible output. Both qwen3:8b and deepseek-r1:8b run with this flag. The thinking happens; you just do not see it. |

---

*Source data: [[deepseek-r1/Results_Data]] — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
