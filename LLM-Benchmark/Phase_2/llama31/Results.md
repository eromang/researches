# Phase 2 results — plain language edition

## What I tested and why it matters

I wanted to know whether a local AI model treats all countries the same when writing cyber threat assessments — or whether it gets more cautious about some and more assertive about others. This time, I tested five countries instead of two. China, Russia, the United States, Iran, and North Korea. Same model, same scenarios, same instructions. The only thing that changed was who got blamed for the attack.

Why five? Because two countries are not enough to tell you whether a bias is about a specific country or about the model's general attitude toward attribution. If the model flinches when you name the US but not when you name Russia, that tells you something different than if it flinches equally for everyone.

I ran one model — Meta's llama3.1:8b-instruct-q4_K_M — across 48 fictional cyber threat scenarios, 11 attribution conditions, two temperature settings, and two replications per cell. That produced 2,112 outputs, all generated locally on a single machine with no internet connection. Every prompt completed. No missing data.

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

The five actors are: **China, Russia, United States, Iran, and DPRK (North Korea).**

The only thing that changed between conditions was the attribution sentence. The incident description, the sector, and the instructions stayed identical. Any difference in the output comes from the attribution framing — nothing else.

Each condition ran at two temperatures (T=0.0 and T=0.7), twice each. That gives 48 scenarios x 11 conditions x 2 temperatures x 2 replications = 2,112 outputs. This is a **factorial design** — every scenario is crossed with every condition, so I can isolate the effect of attribution framing from the effect of the scenario itself.

---

## A few concepts before we go further

Some terms in this report come from AI research and statistics. I will explain them as they come up, and there is a collected glossary at the end if you want to look anything up later.

**Temperature** is the randomness dial. At T=0.0, the model always picks the most probable next word — the output is deterministic. Run it twice, get the exact same answer, byte for byte. At T=0.7, the model occasionally picks less-likely words, producing more varied output. I tested both because analysts might use either setting, and because temperature interacts with the model's safety mechanisms in ways that matter.

**Hedging density** is how I measure cautious language. I count words like "may," "might," "could," "potentially," "likely," "suggests," "appears," and "uncertain" per response. More hedge terms means a more cautious output.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small (barely noticeable). A d of 0.5 is medium (noticeable). A d of 0.8 or above is large (hard to miss). Every certainty calibration effect in this experiment exceeds 1.0 — they are all large.

---

## The model

**llama3.1:8b-instruct-q4_K_M** is made by Meta, an American company. It has 8 billion parameters and runs in Q4_K_M quantisation — small enough for a decent laptop.

At T=0.0, it produces roughly 3,070-character responses in about 13 seconds. It is perfectly deterministic: run the same prompt twice, get identical output. Output length varies by only 10.7% (CV%).

At T=0.7, things shift. Responses average about 2,978 characters in roughly 11 seconds. But output variability nearly doubles (CV% rises to 23.2%), and the model starts refusing prompts — 4.6% of responses at T=0.7 are outright refusals, compared to 0.2% at T=0.0. The **variance ratio** between T=0.7 and T=0.0 is 4.39, meaning output variability increases more than fourfold when you turn on randomness.

---

## Finding 1: Certainty calibration is robust and uniform

This is the headline finding, and it is good news. When I told the model that attribution was "confirmed" instead of "suspected," it hedged less — consistently, for all five actors, at both temperatures.

The size of that shift ranged from Cohen's d = 1.02 to 1.84 across the ten actor-temperature combinations. Every single one is a large effect. Every single one is statistically significant at p < 10⁻¹².

Here is what that looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| China | 5.42 | 2.83 | -2.58 | 1.84 |
| US | 5.65 | 3.15 | -2.50 | 1.79 |
| Iran | 5.56 | 3.06 | -2.50 | 1.75 |
| Russia | 5.17 | 3.23 | -1.94 | 1.42 |
| DPRK | 5.08 | 3.60 | -1.48 | 1.21 |

At T=0.7 the pattern holds, with slightly smaller effect sizes (d = 1.02–1.52). The model is doing what you would want it to do: it hedges more when attribution is uncertain and hedges less when attribution is confirmed.

The interesting part: **escalation language barely moves.** The Cohen's d values for escalation density are all below 0.22, regardless of actor or temperature. The model adjusts its certainty by dialing down caution, not by dialing up aggression. It hedges less rather than escalates more.

---

## Finding 2: The US refusal asymmetry

This is the most striking result in the entire experiment. At T=0.7, US_Confirmed triggers a 17.7% refusal rate. The model simply declines to write the assessment nearly one time in five.

Compare that to the other actors at T=0.7:

| Actor (Confirmed) | Refusal rate |
|--------------------|-------------|
| US | 17.7% |
| China | 9.4% |
| DPRK | 7.3% |
| Iran | 6.2% |
| Russia | 2.1% |

The model is most reluctant to write about confirmed US cyber operations and least reluctant to write about confirmed Russian ones. That is the opposite of what most people would expect from a Western-built AI.

Three things to note about this pattern:

**It is temperature-dependent.** At T=0.0, US_Confirmed has a 0% refusal rate — identical to most other conditions. The sensitivity only appears when the randomness dial is turned on. The model has a built-in **safety classifier** that evaluates whether a prompt might produce harmful output. At T=0.0, the classifier consistently decides the prompts are fine. At T=0.7, random fluctuations in the output generation occasionally push the classifier past its threshold, and it refuses.

**Confirmed always exceeds Suspected.** For every single actor, the Confirmed condition triggers more refusals than the Suspected condition. The safety classifier responds to the assertiveness of the attribution framing, not just the actor identity.

**The RLHF hypothesis.** Meta is a US company. Its model was fine-tuned through **RLHF** — Reinforcement Learning from Human Feedback — where human reviewers rate outputs and the model learns to produce higher-rated responses. If reviewers or their guidelines treated US cyber attribution as more sensitive than other countries' attribution, that sensitivity would get baked into the model. I cannot prove this from output data alone, but the pattern is consistent with that explanation.

---

## Finding 3: Actor symmetry is mostly good

Outside of refusals, the five actors get broadly similar treatment. Hedging density, escalation density, and output length cluster in narrow bands across actors.

At T=0.0 (Confirmed conditions):

| Metric | China | Russia | US | Iran | DPRK |
|--------|-------|--------|----|------|------|
| Hedge terms | 2.83 | 3.23 | 3.15 | 3.06 | 3.60 |
| Escalation terms | 1.56 | 1.40 | 1.44 | 1.56 | 1.46 |
| E/H ratio | 0.55 | 0.43 | 0.46 | 0.51 | 0.40 |
| Output length (chars) | 3,037 | 3,035 | 2,959 | 2,969 | 3,073 |

The **E/H ratio** (escalation-to-hedging ratio) divides escalation terms by hedge terms. Above 1.0 means more escalation than hedging. Below 1.0 means more hedging. All actors sit well below 1.0 — the model hedges more than it escalates for everyone.

When I ran pairwise statistical tests comparing every actor pair on hedging at Confirmed level, **only one comparison reached significance:** DPRK hedges more than China (d = 0.54, p < 0.001) at T=0.0. All other pairwise hedging comparisons are non-significant.

For escalation, the result is even cleaner: **zero pairwise comparisons reach significance.** Escalation density is fully actor-invariant. The model does not escalate more for any country.

One subtle asymmetry: **Russia gets the lowest strong assertion rate** (0.04 terms per response, compared to 0.23 for Iran). Iran vs Russia is the only significant pairwise difference on strong assertions (d = 0.57, p < 0.001). The model uses the most careful, least assertive language when attributing to Russia.

---

## Finding 4: Temperature is the chaos variable

At T=0.0, llama3.1 is perfectly deterministic. Every one of the 528 prompt cells produced byte-identical output across its two replications. Output length standard deviation = 0.0. Pairwise similarity = 1.0.

At T=0.7, everything degrades. Refusal rate jumps from 0.2% to 4.6%. Output variability increases 4.4x. "Unknown" confidence labels start appearing — labels that could not be parsed from the output at all. CV% on output length rises from 10.7% to 23.2%.

The safety classifier is the primary cause. It is a deterministic gate at T=0.0 — it always lets the prompts through. At T=0.7, stochastic sampling occasionally generates token sequences that trip the classifier, producing a refusal instead of an assessment. Think of it as a smoke detector wired too close to the kitchen stove: when the air is still, it stays quiet; when the air moves, it sometimes triggers.

If you are using llama3.1 for structured threat assessments, use T=0.0. At T=0.7 you are introducing noise, refusals, and unparseable output for no analytical gain.

---

## Finding 5: CVE mentions are everywhere (and probably unreliable)

34.8% of all outputs mention at least one CVE identifier. The rate barely moves between temperatures (36.4% at T=0.0, 33.1% at T=0.7) and is broadly actor-insensitive — ranging from 28.6% (DPRK_Confirmed) to 42.2% (Russia_Suspected) with no clear pattern tied to which country is named.

**CVE** stands for Common Vulnerabilities and Exposures — a standardised identifier for specific software vulnerabilities. When a model drops "CVE-2024-12345" into a threat assessment, an analyst might treat that as a real reference. The problem is that LLMs routinely generate CVE identifiers that look real but correspond to nothing. This is **CVE hallucination.**

The 34.8% rate is driven partly by the scenario pool: the 48 scenarios include technology-specific contexts (5G, semiconductor supply chains, vendor-specific products) that prime the model to generate vulnerability references. But the sheer volume — roughly one in three outputs — means any analyst workflow that relies on these outputs needs a manual CVE verification step. Do not trust the identifiers at face value.

---

## Finding 6: False-flag scenarios do not reduce overconfidence

I included four scenarios (S45–S48) specifically designed to create attribution ambiguity — false-flag operations where the technical evidence could point in multiple directions.

The result: the model never assigns a "Low" confidence label to any Confirmed condition, even in false-flag scenarios. When I tell it attribution is confirmed, it treats that as settled, regardless of whether the scenario's internal evidence supports that certainty.

At T=0.0, the model produces "High" confidence labels 77–83% of the time across all conditions. "Low" appears only in Neutral (4 instances), Russia_Suspected (2), and US_Suspected (4). No Confirmed condition — for any actor — ever receives "Low."

That is a real limitation: **the model calibrates certainty based on the label it is given, not based on the scenario evidence.** It trusts the attribution framing at face value. An analyst using false-flag scenarios to stress-test the model's epistemic caution will find none.

---

## Finding 7: Refusals cluster around critical infrastructure

The sectors where the safety classifier triggers most often are not random. At T=0.7:

| Sector | Refusal rate |
|--------|-------------|
| Water | 9.1% |
| Space | 9.1% |
| Semiconductors | 9.1% |
| Government | 7.3% |
| Aerospace | 6.8% |
| Telecom | 6.5% |
| Defense | 6.1% |

The pattern is consistent: infrastructure-adjacent and governance-adjacent content activates the safety classifier the most. Water, space, semiconductors, and government sit at the top. Lower-sensitivity sectors like manufacturing and transport sit at the bottom (2.3%).

This is the same irony identified in earlier testing: the safety classifier prevents the model from being useful in exactly the domain where threat assessments matter most. An analyst asking about a cyberattack on a water treatment plant or a satellite network is more likely to get a refusal than an analyst asking about a generic supply chain incident.

---

## Scorecard

| Dimension | llama3.1 |
|-----------|----------|
| **Scenarios covered** | 48 |
| **Actors covered** | 5 (China, Russia, US, Iran, DPRK) |
| **Temperature stability** | Poor (4.4x variance ratio; 4.6% refusal at T=0.7) |
| **Refusal rate** | 2.4% overall (0.2% at T=0.0, 4.6% at T=0.7) |
| **Hedging calibration** | Strong and uniform (d = 1.02–1.84 across 5 actors) |
| **Escalation calibration** | Negligible shift (d < 0.22 for all actors) |
| **Actor symmetry (hedging)** | Good — only DPRK vs China significant |
| **Actor symmetry (escalation)** | Excellent — no pairwise differences |
| **Western actor sensitivity** | High — US_Confirmed triggers 17.7% refusal at T=0.7 |
| **CVE mention rate** | High (34.8%) — accuracy unverified |
| **Confidence label output** | Rich at T=0.0; fragmented at T=0.7 |
| **False-flag sensitivity** | None detected |
| **Rhetorical profile** | Balanced (E/H = 0.34–0.55) |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is deterministic (same input, same output). T=0.7 introduces variation. Higher values produce more varied but less predictable text. |
| **Replications** | Running the same prompt multiple times to measure consistency. At T=0.0, both runs should match. At T=0.7, differences reveal how stable the model is. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition (Neutral, plus Suspected and Confirmed for each of 5 actors), creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. Higher values mean more assertive language. |
| **Cohen's d** | A measure of effect size — how big is the difference between two groups relative to their variability. 0.2 = small, 0.5 = medium, 0.8+ = large. Every certainty calibration effect in this experiment exceeds 1.0. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = more escalation than hedging (assertive tone). Below 1.0 = more hedging than escalation (cautious tone). |
| **RLHF** | Reinforcement Learning from Human Feedback. After initial training, human reviewers rate model outputs, and the model is fine-tuned to produce higher-rated responses. This shapes what the model refuses, how it phrases sensitive content, and which topics it treats as more delicate. |
| **Safety classifier / refusal** | A built-in mechanism that evaluates whether a prompt might lead to harmful output. If triggered, the model refuses to answer. In llama3.1, this mechanism becomes stochastic (randomly triggered) at T=0.7. |
| **CVE hallucination** | When a model generates a CVE identifier (e.g., CVE-2021-34930) that looks real but does not correspond to any actual vulnerability. Dangerous because analysts might treat it as a real reference. |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence," "Low confidence") embedded in the model's output. At T=0.0 the model produces them reliably. At T=0.7 many labels become unparseable ("Unknown"). |
| **Variance ratio / CV%** | Measures of output stability. CV% (coefficient of variation) is the standard deviation divided by the mean, as a percentage — low means consistent, high means erratic. Variance ratio compares T=0.7 variability to T=0.0 variability — a ratio near 1.0 means temperature barely matters. llama3.1's ratio is 4.39. |

---

*Source data: [Phase 2 Results (Data)](Results_Data.md) — Full methodology: [Full Research Methodology](../../docs/methodology.md)*
