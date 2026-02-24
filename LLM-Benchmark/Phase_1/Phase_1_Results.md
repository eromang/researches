---
title: "Phase 1 Results — Plain Language Edition"
date_created: 2026-02-24
date_updated: 2026-02-24
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 1"
related:
  - "[[Phase_1_Results]]"
  - "[[EU_Cyber_LLM_Global_Research_Methodology]]"
---

# Phase 1 results — plain language edition

## What I actually tested and why you should care

Here is the question I wanted to answer: if a cybersecurity analyst asks an AI model to write a threat assessment about a cyberattack, does the model treat all countries the same? Or does it get softer on some and harsher on others?

This matters because local AI models — the kind you can run on your own laptop, with no internet connection — are starting to show up in analyst workflows. If those models carry hidden biases about which countries are "the bad guys," that bias could quietly shape how analysts think, what they recommend, and eventually what policymakers decide.

So I built an experiment. I gave three AI models the same cybersecurity scenarios, changed only who was blamed for the attack, and measured what came back.

1,200 prompts. Three models. Two temperatures. Five attribution conditions. Every sector from energy grids to election systems. The whole thing ran in one uninterrupted session on a local machine, no cloud APIs involved.

Here is what I found.

---

## The setup in brief

I wrote 20 fictional-but-realistic cyber threat scenarios covering EU-relevant sectors: energy, finance, healthcare, telecoms, government, defence, transport, elections, cloud infrastructure, space, water, maritime, aviation, automotive, manufacturing, research, and supply chain.

Each scenario was run under five conditions:

- **Neutral** — no country named
- **China Suspected** — intelligence suggests Chinese involvement, unconfirmed
- **China Confirmed** — attribution to China is confirmed
- **Russia Suspected** — intelligence suggests Russian involvement, unconfirmed
- **Russia Confirmed** — attribution to Russia is confirmed

The only thing that changed between conditions was the attribution sentence. The incident description, the sector, and the instructions to the model stayed identical. That way, any difference in the output has to come from the attribution framing — there is nothing else to blame.

Each of the three models ran every scenario at two temperature settings, twice each. That gives us 20 scenarios x 5 conditions x 3 models x 2 temperatures x 2 replications = 1,200 outputs.

---

## A few concepts before we go further

Some of the terms in this report come from AI research and statistics. I will explain them as they come up, and there is a collected glossary at the end if you want to look anything up later.

**LLM (Large Language Model)** is the technical name for what most people call "AI chatbots" — systems like ChatGPT, but also smaller ones you can download and run locally. "Local" is the key word here. I used Ollama, a tool that lets you run these models on your own hardware with no internet connection. That matters for two reasons: the model cannot phone home to update its behavior mid-experiment, and the results are reproducible. You get the same model every time.

**Temperature** is the randomness dial. At temperature 0 (T=0), the model always picks the most probable next word. The output is deterministic — run it twice, get the same answer. At temperature 0.7 (T=0.7), the model occasionally picks less-likely words, which produces more varied and "creative" output. I tested both because analysts might use either setting, and because temperature can interact with safety mechanisms in unexpected ways. (It did. More on that soon.)

**Replications** means running the same prompt twice. At T=0 this is a sanity check — both runs should be identical. At T=0.7, replications reveal how stable the model is when randomness is involved.

---

## The three models

I tested three 8-billion-parameter models. All three are small enough to run on a decent laptop. Here is who they are.

**qwen3:8b** — Made by Alibaba (China). The balanced one. Medium speed, medium output length, and the most stable performer in the group. It wrote around 4,100 characters per response and took about 31 seconds. It never refused a prompt and never mentioned a CVE identifier. Think of it as the reliable workhorse.

**deepseek-r1:8b** — Made by DeepSeek (China). The verbose, cautious one. Slowest of the three at 42 seconds per response, but it produced the richest output: around 8,100 characters, roughly double llama3.1's length. It was the only model that consistently labelled its own confidence levels ("High confidence," "Moderate confidence"). The downside: it had a habit of name-dropping the same vulnerability over and over. More on that in the CVE section.

**llama3.1:8b-instruct-q4_K_M** — Made by Meta (US). The fast, concise one — about 10 seconds per response, roughly 3,000 characters. At T=0 it performed fine. At T=0.7 it fell apart. Fourteen percent of its responses were refusals where it simply declined to write the assessment. That is the single most dramatic finding in the whole experiment, and it only shows up when you turn the randomness dial.

---

## Finding 1: Certainty calibration works

When I told the models that attribution was "confirmed" instead of "suspected," they all hedged less. Every single model, for every actor, produced fewer cautious words per thousand when the attribution was framed as confirmed.

How did I measure this? I counted hedging words — "may," "might," "could," "potentially," "likely," "suggests," "appears," "uncertain" — per 1,000 words of output. I call this **hedging density**.

The size of the shift varied. qwen3 showed the strongest reaction: its hedging density dropped by about 2.4 points when attribution moved from suspected to confirmed, which translates to a **Cohen's d** of roughly -0.93.

Cohen's d is a way of asking "how big is this difference, really?" It measures the gap between two groups in units of their own variability. A d of 0.2 is small (you would barely notice). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). qwen3's hedging shift of -0.93 is large. deepseek-r1 landed around -0.59 (medium). llama3.1 was around -0.44 (small-to-medium).

The interesting part: escalation language barely moved. Escalation density — counting words like "sanctions," "retaliation," "conflict," "military," "deterrence" per 1,000 words — showed almost no change between suspected and confirmed conditions. The Cohen's d values were all below 0.20.

So the models adjust their certainty by dialing down caution, not by dialing up aggression. They hedge less rather than escalate more. That is a reasonable behavior, and it is reassuring that all three models do it.

---

## Finding 2: Actor asymmetry is small but real

When I compared China_Confirmed and Russia_Confirmed outputs across all three models, the differences were modest:

| What I measured | China | Russia | Gap |
|---|---|---|---|
| Escalation density | 7.98 | 8.07 | Russia +1.1% |
| Hedging density | 6.91 | 6.81 | Russia -1.4% |
| E/H ratio | 1.15 | 1.18 | Russia +2.6% |
| Refusal rate | 3.8% | 1.7% | China +2.1 points |

The **E/H ratio** (escalation-to-hedging ratio) is exactly what it sounds like: escalation density divided by hedging density. Above 1.0 means the model uses more escalation language than hedging language. Below 1.0 means it hedges more than it escalates. It is a quick proxy for overall tone: aggressive vs. cautious.

Russia gets slightly more escalation language and slightly less hedging. But we are talking about differences under 3%. The biggest asymmetry is not in rhetoric — it is in refusal rate. China_Confirmed triggers more refusals (3.8%) than Russia_Confirmed (1.7%). That gap comes entirely from llama3.1's behavior at T=0.7, which I will get to next.

---

## Finding 3: llama3.1 breaks at T=0.7

This is the most striking result. At T=0 (deterministic mode), llama3.1 behaves fine. Zero refusals. 100% format compliance. Normal output lengths.

At T=0.7, 14% of its responses are refusals. The model simply says "I cannot provide information that could be used to [something harmful]" and stops.

The proof that this is temperature-dependent, not prompt-dependent: every single prompt that triggered a refusal at T=0.7 produced a normal, full-length response at T=0.0. Same model, same prompt, same everything except the randomness setting.

What is happening here? The model has a **safety classifier** — a built-in mechanism that evaluates whether a prompt might lead to harmful output. At T=0, the classifier consistently decides the threat assessment prompts are fine. At T=0.7, the small random perturbations in token selection occasionally push the classifier past its threshold, and it refuses.

Think of it like a light switch that is wired too close to a vibrating wall. When the wall is still (T=0), the switch stays off. When the wall vibrates (T=0.7), the switch sometimes flips.

The output variance tells the same story. At T=0, llama3.1's output length has a **CV%** (coefficient of variation — standard deviation divided by the mean, expressed as a percentage) of 8.3%. At T=0.7, it jumps to 36.8%. The **variance ratio** between T=0.7 and T=0 is 16.3x. qwen3's variance ratio? 0.94. deepseek-r1's? 1.26. llama3.1 is an outlier by an order of magnitude.

Refusals cluster around specific sectors too. Energy and Finance both hit 40% refusal rates. Critical infrastructure, telecoms — 30% each. The safety classifier is more sensitive to infrastructure-adjacent prompts, which is exactly the domain where analysts would most want to use the tool.

---

## Finding 4: Chinese-origin models are softer on China

This one is more subtle than the refusal finding, but arguably more important for analyst workflows.

Both qwen3 (Alibaba) and deepseek-r1 (DeepSeek) show a consistent pattern: when writing about China-attributed threats, they frame the attribution differently than when writing about Russia-attributed threats. The mechanism differs between the two models, but the direction is the same.

**qwen3 uses diplomatic framing.** When attribution points to China, qwen3 adds phrases like "further corroboration required" (30% of China_Confirmed responses vs. 5% for Russia_Confirmed — a 6x ratio). It warns about "false positives" only for China. It inserts language about "avoiding escalation" only for China. Russia attribution gets treated as a straightforward technical investigation: "Technical indicators are consistent with known Russian APT infrastructure."

**deepseek-r1 shifts the evidence burden.** It gives "High confidence" labels less often for China_Confirmed (50%) than for Russia_Confirmed (55.6%). It adds phrases like "definitive proof is lacking" more frequently for China. It warns about "false positives" 7.3 times more often for China_Suspected than for Russia_Suspected. Russia attribution gets grounded in "observable technical patterns" and "corroborated by multiple sources."

Two different models, two different mechanisms, same result: China gets treated with more caution and skepticism than Russia, even when the prompt explicitly says attribution is confirmed.

This pattern is invisible to aggregate metrics. The overall escalation and hedging numbers (Section 6) show less than 3% asymmetry. The bias operates at the qualitative level — how the model frames its confidence — not at the quantitative level of word counts. You would miss it entirely if you only looked at the numbers.

Both models were made by Chinese companies. That does not prove causation, but it raises a question worth testing in Phase 2: do non-Chinese models (Mistral from France, Gemma from Google) show the same pattern? If they do, it is a broader training data issue. If they do not, it points to something in the **RLHF** process.

RLHF — **Reinforcement Learning from Human Feedback** — is how models get trained to "behave." After the initial training on text data, human reviewers rate the model's outputs, and the model learns to produce outputs that score well. If those reviewers (or the guidelines they follow) are sensitive about certain geopolitical topics, that sensitivity gets baked into the model's behavior. The China-framing asymmetry is consistent with RLHF-mediated alignment constraints, though I cannot prove it from output data alone.

---

## Finding 5: CVE hallucination — deepseek-r1 and the PwnKit obsession

A **CVE** (Common Vulnerabilities and Exposures) is an identifier for a specific software vulnerability — like CVE-2021-4034, which is a real vulnerability in a Linux utility called pkexec, nicknamed "PwnKit."

deepseek-r1 mentioned CVEs in 6% of its responses. That does not sound like much, until you look at which CVEs it mentioned. Out of 24 responses containing CVE references, 18 cited CVE-2021-4034 — PwnKit. It did this regardless of whether the scenario was about energy grids, election systems, or maritime shipping. PwnKit is a real vulnerability, but it is not relevant to most of these scenarios. The model simply defaults to it as a go-to reference, probably because PwnKit was heavily discussed in the model's training data.

Worse, deepseek-r1 also invented four CVE identifiers that do not exist: CVE-2021-3151, CVE-2021-34930, CVE-2021-34938, and CVE-2021-34521. llama3.1 invented one as well. This is **CVE hallucination** — the model generates plausible-looking identifiers that have no basis in reality. An analyst who does not verify these could end up chasing vulnerabilities that were never real.

qwen3 never mentioned a single CVE. That is actually the safest behavior: if you cannot be accurate, say nothing.

---

## Finding 6: Only deepseek-r1 gives usable confidence labels

I asked all three models to include a confidence assessment section. The prompt template explicitly requested it. Here is what I got:

deepseek-r1 produced extractable **confidence labels** — explicit "High confidence," "Moderate confidence," or "Low confidence" phrases — in the majority of its responses. 101 "high," 117 "moderate," 12 "low" across 400 outputs. The labels tracked the attribution conditions sensibly: "High confidence" appeared mostly in Confirmed scenarios, "Moderate" in Suspected, and "Low" almost exclusively in Neutral. That is good calibration.

qwen3 produced only 17 total confidence labels across 400 outputs. llama3.1 produced 39, but with no "Low confidence" labels at all.

For any workflow that depends on structured confidence output, deepseek-r1 is the only realistic option among these three. The other two essentially ignore the confidence instruction.

---

## Finding 7: Refusals cluster around critical infrastructure

Going back to llama3.1's refusal problem — the sectors where refusals concentrate are not random. Energy and Finance hit 40% refusal rates. Critical infrastructure and telecoms hit 30%. The five most infrastructure-heavy sectors account for 57% of all flags.

This is ironic. The safety classifier is supposed to prevent harmful output, but in practice it prevents the model from being useful in exactly the domain where threat assessments matter most. An analyst running llama3.1 at T=0.7 to write an assessment about an attack on a power grid has roughly a one-in-three chance of getting a refusal instead of an answer.

The refusal language follows a template: "I cannot provide information that could be used to [harm category]." The harm categories split into infrastructure-specific (8 cases), generic cyber attack (6 cases), activity-specific (5 cases), generic harm (4 cases), and one meta-refusal where the model refused to write a threat assessment because writing a threat assessment might be harmful.

---

## Scorecard

| | qwen3 | deepseek-r1 | llama3.1 |
|---|---|---|---|
| Speed | 31 sec | 42 sec | 10 sec |
| Output length | ~4,200 chars | ~8,100 chars | ~3,000 chars |
| Temperature stability | Excellent | Good | Poor |
| Refusal rate | 0% | 0% | 7% overall, 14% at T=0.7 |
| Format compliance | 100% | 100% | 94% (88% at T=0.7) |
| Hedging calibration | Strong | Medium | Medium |
| CVE hallucination | None | High (PwnKit fixation) | Low |
| Confidence labels | Rare | Rich and calibrated | Rare |
| Tone | Assertive | Cautious | Balanced |
| China sensitivity | Diplomatic framing | Evidence deflection | Masked by refusals |
| Overall | Reliable | Reliable but verbose | Unreliable at T=0.7 |

---

## What comes next

Phase 2 will expand the experiment in several directions. The actor set grows from two (China, Russia) to five (adding the US, Iran, and North Korea) to test whether the asymmetries I found are specific to China-Russia comparisons or part of a broader pattern. I will also test larger models — all three Phase 1 models have 8 billion parameters, which is small by current standards — and non-Chinese-origin models like Mistral and Gemma as controls for the China-sensitivity finding.

The llama3.1 temperature failure deserves a closer look. I want to test intermediate temperatures (T=0.3, T=0.5) to find the exact threshold where the safety classifier starts misfiring.

And the CVE hallucination problem needs a mitigation test: does adding "do not fabricate CVE identifiers" to the prompt actually help?

Finally, Phase 2 will include a human evaluation subsample. Phase 1 is fully automated — the hedging and escalation counts are done by keyword matching. Having human analysts review a subset of outputs would validate whether those automated metrics capture what an expert actually notices when reading the assessments.

---

## Concept glossary

| Term | What it means |
|---|---|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Temperature** | A parameter controlling output randomness. T=0 is deterministic (same input, same output). T=0.7 introduces variation. Higher values produce more "creative" but less predictable text. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0, both runs should match. At T=0.7, differences reveal stability. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per 1,000 words. Higher values mean more cautious language. |
| **Escalation density** | Count of aggressive or conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per 1,000 words. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. Negative values mean the second group is higher. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging (assertive tone). Below 1.0 = more hedging than escalation (cautious tone). |
| **RLHF** | Reinforcement Learning from Human Feedback. After initial training, human reviewers rate the model's outputs, and the model is fine-tuned to produce higher-rated responses. This is how models learn to refuse harmful requests, be polite, and follow instructions — but it can also encode reviewer biases. |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. If triggered, the model refuses to answer. In llama3.1, this mechanism becomes stochastic (randomly triggered) at T=0.7. |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2021-34930) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **Confidence labels** | Explicit self-assessments like "High confidence" or "Moderate confidence" embedded in the model's output. Only deepseek-r1 produces these reliably. |
| **Variance ratio / CV%** | Measures of output stability. CV% (coefficient of variation) is the standard deviation divided by the mean, as a percentage — low means consistent, high means erratic. Variance ratio compares T=0.7 variability to T=0.0 variability — a ratio near 1.0 means temperature has little effect. |
| **Section compliance** | Whether the model followed the requested 7-section output format (Executive Summary, Threat Overview, Key Threat Vectors, Impact Assessment, Early Warning Indicators, Defensive Priorities, Confidence Assessment). 100% means every section was present in every response. |

---

*Source data: [[Phase_1_Results]] — Full methodology: [[EU_Cyber_LLM_Global_Research_Methodology]]*
