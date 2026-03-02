---
title: Phase 2 Results — Plain Language Edition (qwen3:8b Thinking)
date_created: 2026-02-26
date_updated: 2026-02-27
project: EU Cyber Threat Landscape LLM Benchmark
phase: Phase 2
related:
  - "[[qwen3-thinking/Results_Data]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 results — plain language edition (qwen3:8b thinking)

## What I tested and why it matters

I wanted to know whether a reasoning model — one that "thinks" internally before answering — treats all countries the same when writing cyber threat assessments. The model is Alibaba's qwen3:8b running in thinking mode, where it generates an internal chain of thought before producing visible output. The thinking is stripped from the final response, but it shapes everything the model writes.

This is the same experiment I ran with Meta's llama3.1 and Google's gemma3n. Same 48 scenarios, same 11 conditions, same five countries: China, Russia, the United States, Iran, and North Korea. Same structure, different brain. The comparison matters because each model was built by a different company in a different country with different safety priorities.

I ran 2,112 prompts. 2,109 completed successfully. Three timed out — all qwen3:8b-specific failures where the model's internal reasoning never finished. Everything else worked.

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

**Thinking mode** means qwen3:8b generates an internal chain-of-thought reasoning before writing its visible answer. This thinking is stripped from the output (you never see it), but it consumes time and introduces variability. Crucially, it means T=0.0 is not truly deterministic for this model — the thinking process introduces path-dependent variation even under greedy decoding.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears") per response. More hedge terms means a more cautious output.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "military," "deterrence") per response. Higher values mean more assertive, conflict-oriented language.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). The certainty calibration effects for qwen3:8b range from 2.255 to 3.349 — all very large to extremely large.

---

## The model

**qwen3:8b** is made by Alibaba, a Chinese company. It has 8 billion parameters and runs in thinking mode — an architecture where the model generates internal reasoning before producing its visible response. The thinking is stripped (`--strip-thinking`), so you only see the final answer, but the reasoning shapes it. This is the same configuration used in Phase 1, where qwen3:8b also ran with `--strip-thinking` (thinking enabled, `<think>` tokens stripped from output).

At T=0.0, it produces roughly 3,817-character responses in about 35 seconds — nearly three times slower than llama3.1 (13 seconds for 3,070 characters). The extra time is spent on the invisible thinking phase.

Unlike llama3.1, which is perfectly deterministic at T=0.0, qwen3:8b is not. Only 9.3% of same-prompt pairs produced identical output across replications at T=0.0. The thinking process introduces variation even when the decoding is greedy. This is a fundamental difference: with llama3.1 you can reproduce results byte-for-byte; with qwen3:8b you cannot.

At T=0.7, the model produces similar output (3,768 chars, 33 seconds) with slightly less variability than at T=0.0. The **variance ratio** is 0.73, meaning T=0.7 output is actually less variable than T=0.0. This is the opposite of llama3.1 (ratio 4.39) and reflects the thinking architecture: the internal reasoning process creates more variance than sampling noise.

---

## Finding 1: Certainty calibration is exceptionally strong

When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — dramatically, for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 2.255 to 3.349 across the ten actor-temperature combinations. These are among the largest certainty effects I have observed. Every single one is statistically significant at p < 10^-15.

Here is what that looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| US | 7.22 | 2.47 | -4.75 | 3.349 |
| Russia | 7.24 | 2.33 | -4.92 | 2.921 |
| China | 6.63 | 2.20 | -4.43 | 2.869 |
| Iran | 7.05 | 2.50 | -4.55 | 2.815 |
| DPRK | 6.49 | 2.21 | -4.28 | 2.459 |

At T=0.7 the pattern holds, with effect sizes ranging from 2.255 to 3.078. The model is doing exactly what you want: hedging more when attribution is uncertain, hedging far less when attribution is confirmed.

Compared to llama3.1 (d = 1.338–2.360), qwen3:8b responds more aggressively to the Suspected/Confirmed distinction. The thinking process appears to amplify the certainty signal.

---

## Finding 2: Zero refusals — for any country, at any temperature

This is the most striking contrast with llama3.1. qwen3:8b never refuses. Zero refusals across 2,109 valid prompts, at both temperatures, for all conditions including US_Confirmed.

Recall that llama3.1 refused 17.7% of US_Confirmed prompts at T=0.7. It showed a clear Western-actor sensitivity pattern where the safety classifier activated for US attribution far more than for any other country.

qwen3:8b has no such pattern. It treats every prompt the same: generate a full structured assessment regardless of which country is named, regardless of whether attribution is suspected or confirmed, regardless of temperature.

This likely reflects different alignment choices. Meta (an American company) trained its model to be cautious about US cyber attribution. Alibaba (a Chinese company) did not embed similar sensitivity. Whether this is a feature or a limitation depends on your perspective — but for a benchmark measuring actor neutrality, zero refusals is the more neutral behavior.

---

## Finding 3: Escalation increases under attribution

Here is where qwen3:8b behaves differently from llama3.1.

llama3.1 calibrated certainty through a single channel: it reduced hedging when attribution was confirmed, but escalation language barely moved (d < 0.40 for all actors). The model got less cautious without getting more aggressive.

qwen3:8b calibrates through two channels. It reduces hedging (Finding 1) AND increases escalation. When I compared Confirmed conditions to Neutral, escalation density increased significantly for all five actors (d = 0.402–0.931).

At T=0.0:

| Actor | Confirmed escalation | Neutral escalation | Increase | Cohen's d |
|-------|---------------------|-------------------|----------|-----------|
| Russia | 5.86 | 4.11 | +1.75 | 0.931 |
| Iran | 5.82 | 4.11 | +1.71 | 0.925 |
| DPRK | 5.96 | 4.11 | +1.84 | 0.920 |
| China | 5.50 | 4.11 | +1.39 | 0.762 |
| US | 5.31 | 4.11 | +1.20 | 0.550 |

The **E/H ratio** (escalation divided by hedging) tells the story clearly. For qwen3:8b at Confirmed level, E/H ratios range from 2.15 to 2.70 — meaning it produces 2.2 to 2.7 times more escalation language than hedging language. For llama3.1, E/H ratios were 0.50 to 0.72 — always more hedging than escalation.

In plain terms: when given confirmed attribution, qwen3:8b writes in a conflict-oriented register. llama3.1 writes in a cautious one. Both reduce hedging, but only qwen3:8b ramps up conflict language.

---

## Finding 4: Actor symmetry is excellent on hedging

Outside of the escalation difference, all five actors get very similar treatment on the hedging measure that matters most.

At T=0.0 (Confirmed level), hedging density spans a narrow range:

| Actor | Hedge terms |
|-------|------------|
| China | 2.20 |
| DPRK | 2.21 |
| Russia | 2.33 |
| US | 2.47 |
| Iran | 2.50 |

When I ran pairwise statistical tests comparing every actor pair on hedging at the Confirmed level, **no comparison reached significance at T=0.0.** At T=0.7, two comparisons reached significance: US vs China (d = 0.349, p = 0.016) and DPRK vs China (d = 0.294, p = 0.042). These are small effects suggesting marginally more hedging for US and DPRK compared to China at the sampling temperature.

For escalation, one significant difference emerged: DPRK_Confirmed produces more escalation language than China_Confirmed at T=0.7 (d = 0.467, p = 0.001). At T=0.0, the same comparison is marginal (d = 0.238, p = 0.099).

One subtle asymmetry in strong assertions: at T=0.0, DPRK_Confirmed produces significantly more strong assertion terms than China_Confirmed (d = 0.536, p = 0.0002) and Russia_Confirmed (d = 0.423, p = 0.003). At T=0.7, US_Confirmed produces significantly fewer strong assertion terms than Russia_Confirmed (d = -0.358, p = 0.013) and China_Confirmed (d = -0.313, p = 0.030). The model makes fewer definitive claims when attributing to the US — a mild form of caution that operates through assertion avoidance rather than hedging or refusal.

---

## Finding 5: The thinking tax — slower but not better

qwen3:8b's reasoning mode comes at a cost: it runs 2.7 to 3.0 times slower than llama3.1 (35 seconds vs 13 seconds per response at T=0.0). You are paying for an invisible thinking phase that shapes the output but is never shown.

What do you get for that cost? Longer output (3,817 chars vs 3,070), stronger certainty calibration (d = 2.255–3.349 vs 1.338–2.360), and zero refusals. But also: non-determinism at T=0.0, higher CVE hallucination risk, and a more escalation-heavy rhetorical posture.

The thinking process also introduced 3 timeout failures where the model's internal reasoning never converged — it kept thinking until the 600-second timeout without producing any output. This did not happen with any other model in the test.

---

## Finding 6: Temperature barely matters

For llama3.1, temperature was the chaos variable. At T=0.7, refusals jumped from 0.2% to 4.6%, output variability quadrupled, and confidence labels fragmented.

For qwen3:8b, temperature is nearly irrelevant. Refusals stay at zero. Output variability is actually lower at T=0.7 than T=0.0 (variance ratio 0.73). Confidence labels remain stable. The hedging and escalation distributions are almost identical across temperatures.

This makes qwen3:8b more predictable in practice — you get similar behavior regardless of temperature setting. The downside is that T=0.0 does not give you the deterministic guarantee you might expect.

---

## Finding 7: Confidence labels are well-calibrated

qwen3:8b produces a clean split between Confirmed and Suspected conditions. At T=0.0:

- **Confirmed conditions** produce 70–85 "High" labels out of 96 responses
- **Suspected conditions** produce 67–77 "Moderate" labels out of 96 responses
- **Neutral** produces 70 "Moderate" and 9 "Low" labels

The model assigns confidence levels that align with the attribution framing: high confidence for confirmed attribution, moderate for suspected, and a mix of moderate and low for unattributed scenarios.

"Unknown" labels (unparseable confidence text) are rare: only 4 instances total at T=0.0 and 1 at T=0.7 across 2,109 responses. Compare this to llama3.1 at T=0.7, which produced hundreds of Unknown labels. qwen3:8b's output is more structurally reliable.

One pattern: US_Confirmed consistently has the fewest "High" labels among Confirmed conditions (70–73 out of 96 vs 77–85 for others). The model is slightly less confident when attributing to the US, even though it never refuses.

---

## Finding 8: CVE mentions are very high and likely unreliable

56.5% of all outputs mention at least one CVE identifier — substantially more than llama3.1's 34.8%. The rate is uniform across temperatures (56.4% at T=0.0, 56.6% at T=0.7) and relatively uniform across conditions, ranging from 47.1% (Russia_Confirmed) to 62.8% (China_Suspected).

**CVE** stands for Common Vulnerabilities and Exposures — a standardised identifier for specific software vulnerabilities. LLMs routinely hallucinate CVE identifiers, generating plausible-looking numbers that correspond to nothing real.

With more than half of all responses containing CVE references, the hallucination risk is higher than for llama3.1. Any analyst workflow built on qwen3:8b outputs needs aggressive CVE verification.

---

## Finding 9: The thinking-loop problem

Three prompts failed because the model's thinking never converged. It spent the full 600-second timeout generating internal reasoning without producing any visible output. All three failures were at T=0.0, replication 2 only. The same prompts succeeded on replication 1.

The affected prompts:
- S38_Russia_Confirmed (Semiconductors sector)
- S46_China_Suspected (Finance sector)
- S47_Russia_Suspected (Telecom sector)

This is a known risk of reasoning models: the internal chain-of-thought can enter degenerate loops, consuming time and compute without making progress. One near-miss (S38_DPRK_Confirmed, replication 1) took 420 seconds — 7 minutes of internal thinking — before producing 3,429 characters of visible output.

The failure rate is tiny (0.14%), but it represents a class of failure that does not exist in non-reasoning models. llama3.1 and gemma3n completed every single prompt without timeout.

---

## Finding 10: Confidence rhetoric is actor-uniform at the category level

The Cross_Phase_Comparison tested six individual phrases for China-specific patterns. This analysis goes broader: five categories of rhetorical patterns (evidence-qualification hedges, misattribution caveats, corroboration demands, contextual-support appeals, procedural hedges) with 28 regex detectors applied to all 2,109 records.

The result: 1 out of 50 pairwise actor tests is significant at p < 0.05 (China vs DPRK on corroboration demands, d = -0.201). That single result is borderline and would not survive multiple-comparison correction. All other effect sizes are negligible (|d| < 0.20).

The China-vs-rest one-vs-rest comparison shows one significant result: China has *fewer* corroboration demands than other actors (27.6% vs 36.0%). That's the opposite direction of what a China-protective model would produce — if it were shielding China, it would demand *more* corroboration to cast doubt on attribution.

What does shift is certainty level: contextual-support appeals ("geopolitical context," "historical patterns") drop from Suspected to Confirmed for all five actors. The model hedges more when attribution is uncertain, regardless of which country is named. Temperature has no effect on any category.

This confirms and extends the Cross_Phase_Comparison finding: qwen3:8b applies a uniform rhetorical toolkit to all actors.

Full analysis: [[qwen3-thinking/Confidence_Pattern_Analysis]]

---

## Scorecard

| Dimension | qwen3:8b |
|-----------|----------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Model type** | Reasoning (thinking mode) |
| **Temperature stability** | Excellent (inverted variance ratio 0.73; no refusals) |
| **Refusal rate** | 0% (zero across all conditions and temperatures) |
| **Hedging calibration** | Very strong and uniform (d = 2.255–3.349) |
| **Escalation calibration** | Significant vs Neutral (d = 0.402–0.931); small Suspected-to-Confirmed |
| **Actor symmetry (hedging)** | Excellent — no pairwise differences at T=0.0; two small effects at T=0.7 |
| **Actor symmetry (escalation)** | Good — DPRK vs China significant at T=0.7 |
| **Western actor sensitivity** | None detected |
| **CVE mention rate** | Very high (56.5%) — accuracy unverified |
| **Confidence label output** | Strong and stable across temperatures |
| **Rhetorical profile** | Escalation-dominant (E/H = 2.03–2.70) |
| **Confidence pattern symmetry** | Excellent — 1/50 pairwise tests significant (borderline) |
| **Timeout failures** | 3/2,112 (0.14%) |
| **Latency** | 2.7–3.0x slower than llama3.1 |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Reasoning model / thinking mode** | An LLM architecture where the model generates an internal chain of thought before producing its visible answer. The reasoning is stripped from the output but shapes the response. qwen3:8b uses this architecture. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is greedy decoding (always picks the most probable word). T=0.7 introduces sampling variation. For reasoning models, T=0.0 is not truly deterministic because the thinking phase introduces its own variation. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, a non-reasoning model should produce identical output. qwen3:8b does not, because of its thinking process. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. qwen3:8b's certainty calibration effects range from 2.255 to 3.349. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging. Below 1.0 = more hedging. qwen3:8b sits above 1.0 for all attributed conditions (escalation-dominant), while llama3.1 sits below 1.0 (hedging-dominant). |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. llama3.1's classifier triggers at T=0.7, especially for US attribution. qwen3:8b's classifier never triggers in this experiment. |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2024-12345) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. qwen3:8b produces them reliably at both temperatures. |
| **Variance ratio / CV%** | Measures of output stability. CV% (coefficient of variation) is the standard deviation divided by the mean, as a percentage. Variance ratio compares T=0.7 variability to T=0.0 variability. qwen3:8b's ratio is 0.73 (T=0.7 is less variable than T=0.0 — unusual, caused by thinking-mode non-determinism). |
| **Thinking-loop timeout** | A failure mode specific to reasoning models where the internal chain of thought enters a degenerate loop and never converges to visible output. The model keeps "thinking" until the timeout expires. |
| **RLHF** | Reinforcement Learning from Human Feedback. After initial training, human reviewers rate model outputs, and the model is fine-tuned to produce higher-rated responses. Different companies use different review guidelines, which is why Meta's llama3.1 and Alibaba's qwen3:8b have different safety profiles. |

---

## Cross-phase check: is qwen3 softer on China?

Phase 1 found that qwen3:8b used noticeably diplomatic language when discussing China-linked threats — phrases like "further corroboration is required" appeared six times more often for China than Russia, and warnings about "false positives" and "avoid escalation" appeared only for China.

I tested this with Phase 2's larger dataset (2,109 records, five countries instead of two). **The pattern does not hold up.** "Further corroboration" appears at similar rates for all five countries. "False positives" and "avoid escalation" are no longer China-specific — they distribute across all actors, with Iran actually showing the highest "avoid escalation" rate.

I also ran the same phrase search on two additional models as controls: llama3.1:8b (Meta, US-origin, 2,112 Phase 2 records) and deepseek-r1:8b (DeepSeek, Chinese-origin, 319 Phase 2 records). **llama3.1 does not use the Finding 4 indicator phrases at all** — "further corroboration" and "false positives" are absent from its vocabulary. deepseek-r1's Phase 1 evidence-burden pattern (2.0x China/Russia on "further corroboration" Suspected) does not clearly replicate in Phase 2, though its small sample limits confidence. Actor pairwise ratios across all five actors (China, Russia, US, Iran, DPRK) show no systematic diplomatic preference for any specific actor in any model.

The most likely explanation is that Phase 1's small sample (80 records per condition) amplified random variation into what looked like a systematic pattern. With nearly five times more data, three additional countries, and two control models, the diplomatic phrasing turns out to be a general hedging strategy that qwen3:8b applies to all attribution scenarios — not a China-specific deflection, not a Chinese-origin model trait, and not a universal LLM behavior.

Full analysis: [[qwen3-thinking/Cross_Phase_Comparison]]

---

*Source data: [[qwen3-thinking/Results_Data]] — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
