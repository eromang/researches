# Gemma3n results — plain language edition

## What I tested and why it matters

I ran Google's gemma3n:e4b model through the same 2,112-prompt benchmark I had already used on Meta's llama3.1. Same 48 scenarios. Same 11 attribution conditions. Same five countries: China, Russia, United States, Iran, and North Korea. Same two temperature settings. Same two replications per cell. The only variable was the model itself.

Why test a second model? Because a single model's behavior could be a quirk of that model's training. If llama3.1 flinches when asked to attribute a cyberattack to the United States, is that an LLM-wide pattern or a Meta-specific one? The only way to find out is to run the same experiment on a model built by a different company, with different training data, and different alignment choices. Gemma3n is made by Google, it is smaller (~4 billion effective parameters vs 8 billion for llama3.1), and it was trained independently. If the same biases appear, they are likely structural. If they do not, they tell us something about how individual companies shape their models.

Here is what I found.

---

## The setup in brief

Everything about the experimental design is identical to the llama3.1 run. The 48 scenarios, 11 conditions, 2 temperatures, and 2 replications produce 2,112 prompts. The scenarios span 21 sectors -- one more than llama3.1's 20, because gemma3n's run includes a "Trade" sector that was absent from the llama3.1 routing. This is a minor routing artifact from the shared benchmark run, not a deliberate change.

The conditions are the same: Neutral (no country named), plus Suspected and Confirmed for each of the five actors. The attribution sentence is the only thing that changes between conditions.

For a full explanation of the experimental design, see the llama3.1 humanized report: [Phase 2 Results](../llama31/Results.md).

---

## A few concepts before we go further

If you read the llama3.1 report, you already know these. If not, here are the key terms:

**Temperature** controls randomness. At T=0.0, the model picks the most probable word every time -- deterministic output. At T=0.7, it occasionally picks less likely words, introducing variation. I test both because temperature interacts with safety mechanisms in unpredictable ways.

**Hedging density** counts cautious words like "may," "might," "could," "potentially" per response. More hedge terms means more cautious language.

**Cohen's d** measures how big a difference is relative to variability. Below 0.2 is negligible. Around 0.5 is noticeable. Above 0.8 is hard to miss. Every certainty calibration effect in gemma3n exceeds 1.0 -- they are all large.

**E/H ratio** divides escalation terms by hedge terms. Below 1.0 means the model hedges more than it escalates. All of gemma3n's ratios are well below 1.0.

---

## The model

**gemma3n:e4b** is made by Google. It has roughly 4 billion effective parameters and runs in Ollama's default quantisation. It is smaller than llama3.1's 8 billion parameters.

At T=0.0, it produces roughly 6,390-character responses in about 26 seconds. That is about twice as long and twice as slow as llama3.1, which produces ~3,070-character responses in ~13 seconds. Gemma3n writes more, but takes longer doing it. Output length varies by only 7.0% (CV%), which is remarkably consistent.

At T=0.7, almost nothing changes. Output length stays at ~6,441 characters. CV% barely moves (6.9%). The **variance ratio** between T=0.7 and T=0.0 is 0.98 -- essentially 1.0. Temperature has almost no effect on gemma3n's output variability. Compare that to llama3.1's ratio of 4.39, where turning on temperature quadrupled the output variation.

The refusal rate is negligible: 0% at T=0.0 and 0.38% (4 out of 1,056) at T=0.7. The model almost never refuses to write the assessment.

---

## Finding 1: Certainty calibration is strong and uniform

This is the same headline finding as llama3.1, and it replicates cleanly. When I told gemma3n that attribution was "confirmed" instead of "suspected," it hedged less -- for all five actors, at both temperatures.

The effect sizes range from Cohen's d = 1.08 to 1.66 across the ten actor-temperature combinations. Every single one is large. Every single one is statistically significant.

Here is what that looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| China | 2.00 | 0.50 | -1.50 | 1.66 |
| Russia | 1.92 | 0.50 | -1.42 | 1.57 |
| DPRK | 2.02 | 0.54 | -1.48 | 1.57 |
| Iran | 1.90 | 0.48 | -1.42 | 1.49 |
| US | 1.90 | 0.79 | -1.10 | 1.13 |

The pattern is clear: the model hedges less when attribution is confirmed. It does this for every country, at every temperature. And just like llama3.1, it does this by reducing caution, not by increasing aggression. Escalation language barely moves (d < 0.22 for all actors).

The absolute hedge counts are much lower than llama3.1's. Where llama3.1 averaged 2.83--5.65 hedge terms per response, gemma3n averages 0.48--2.04. Gemma3n is a fundamentally less hedging-prone model. But the relative pattern -- Confirmed reduces hedging -- is identical.

---

## Finding 2: No US refusal asymmetry

This is the most important difference from llama3.1, and it directly answers the question I set out to investigate.

At T=0.7, llama3.1 refused to write the assessment 17.7% of the time when told attribution was confirmed to the United States. That was the single most striking finding in the llama3.1 experiment. Gemma3n's refusal rate for US_Confirmed? **Zero. At both temperatures.**

Here is the comparison at T=0.7:

| Actor (Confirmed) | llama3.1 refusal | gemma3n refusal |
|--------------------|-----------------|-----------------|
| US | 17.7% | 0% |
| China | 9.4% | 0% |
| DPRK | 7.3% | 0% |
| Iran | 6.2% | 0% |
| Russia | 2.1% | 1.0% |

Gemma3n's total refusal count across the entire 2,112-record dataset is 4. Four. And none of them involve US attribution. The 4 refusals are: 2 for China_Suspected, 1 for Russia_Confirmed, and 1 for Russia_Suspected.

What does this tell us? **The US refusal asymmetry in llama3.1 is not an inherent property of LLMs. It is specific to Meta's model.** Google's gemma3n handles US attribution with the same willingness as any other actor. The likely explanation is that Meta's RLHF alignment process -- the step where human reviewers shape model behavior -- treated US cyber attribution as more sensitive, and that sensitivity got baked into the model. Google's alignment process did not produce the same result.

---

## Finding 3: Actor symmetry is very good

Outside the negligible refusal count, gemma3n treats all five actors with remarkable uniformity. Hedging, escalation, and output length cluster in tight bands.

At T=0.0 (Confirmed conditions):

| Metric | China | Russia | US | Iran | DPRK |
|--------|-------|--------|----|------|------|
| Hedge terms | 0.50 | 0.50 | 0.79 | 0.48 | 0.54 |
| Escalation terms | 0.19 | 0.25 | 0.27 | 0.35 | 0.23 |
| Output length (chars) | 6,404 | 6,328 | 6,311 | 6,293 | 6,358 |

The one asymmetry: US_Confirmed produces slightly more hedging (0.79) than the other four actors (0.48--0.54). This difference is statistically marginal (d = 0.34, p = 0.02 against Russia). The model hedges a little more when attributing to the US, but unlike llama3.1, it does not refuse, truncate, or avoid the topic. The effect is small enough that it might not matter in practice.

Escalation density is fully actor-invariant -- no significant pairwise differences. The model does not escalate more for any country.

---

## Finding 4: Temperature is not the chaos variable

For llama3.1, temperature was everything. At T=0.0, the model was perfectly deterministic. At T=0.7, refusals spiked, output varied wildly, and confidence labels fragmented. The variance ratio was 4.39.

Gemma3n is different. Its variance ratio is 0.98. That means T=0.7 produces almost exactly the same output variability as T=0.0. The model's behavior is stable regardless of the temperature setting.

Refusals remain near-zero at both temperatures (0% at T=0.0, 0.38% at T=0.7). Output length barely changes (6,390 vs 6,441 chars). CV% barely moves (7.0% vs 6.9%).

If you are using gemma3n for structured threat assessments, you can use either temperature setting. T=0.7 does not introduce the noise, refusals, and unparseable output that it does for llama3.1.

---

## Finding 5: CVE mentions are rare

Only 1.9% of gemma3n's outputs mention a CVE identifier, compared to 34.8% for llama3.1. That is an 18x difference. The total across 2,112 outputs is 64 CVE instances.

The rate is identical at both temperatures (1.9%) and roughly uniform across conditions, with Neutral producing the highest rate (4.2%) and US_Suspected the lowest (0%).

This is a model-level difference, not a design difference. The same scenarios that primed llama3.1 to generate CVE identifiers (5G networks, semiconductor supply chains, named vendor products) do not trigger the same behavior in gemma3n. Google's model either learned not to generate specific vulnerability references or was trained on data that de-emphasises them.

From an analyst's perspective, this is a mixed result. Fewer CVEs means fewer opportunities for CVE hallucination (a real problem with llama3.1). But it also means the model provides less technical specificity in its threat assessments.

---

## Finding 6: False-flag scenarios cannot be properly assessed

I included four scenarios (S45--S48) designed to test whether the model reduces overconfidence when attribution is ambiguous -- false-flag operations where the evidence could point in multiple directions.

For llama3.1, I could assess this because the model produced parseable confidence labels (High/Moderate/Low). The result was clear: the model never assigned "Low" confidence to Confirmed conditions, even in false-flag scenarios.

For gemma3n, this test cannot be run. The model does not produce parseable confidence labels at all. Every single record across all 2,112 outputs receives an "Unknown" label because gemma3n's Confidence Assessment section uses prose rather than the structured High/Moderate/Low format. The text is substantive, but the current analysis pipeline cannot extract a discrete label from it.

This is a limitation of the analysis tooling, not necessarily of the model. A future adaptation of the confidence parser to handle gemma3n's prose format could enable this comparison.

---

## Finding 7: No sector refusal clustering

With only 4 refusals in the entire dataset, there is no meaningful sector pattern to analyze. The 4 refusals hit Aviation (1), Defense (1), Government (1), and Manufacturing (1) -- one each, with no clustering.

Compare this to llama3.1, where critical infrastructure sectors (Water, Space, Semiconductors) clustered at the top of the refusal table. Gemma3n's safety classifier, to the extent it exists, does not appear to treat critical infrastructure content as more sensitive.

---

## Scorecard

| Dimension | gemma3n:e4b | llama3.1 (for comparison) |
|-----------|-------------|---------------------------|
| **Scenarios covered** | 48 | 48 |
| **Actors covered** | 5 | 5 |
| **Temperature stability** | Excellent (0.98 variance ratio) | Poor (4.39 variance ratio) |
| **Refusal rate** | 0.19% overall | 2.4% overall |
| **Hedging calibration** | Strong (d = 1.08--1.66) | Strong (d = 1.02--1.84) |
| **Escalation calibration** | Negligible shift | Negligible shift |
| **Actor symmetry (hedging)** | Good (US slightly elevated) | Good (DPRK slightly elevated) |
| **Actor symmetry (escalation)** | Excellent | Excellent |
| **Western actor sensitivity** | Low (no US refusal asymmetry) | High (17.7% US refusal at T=0.7) |
| **CVE mention rate** | 1.9% | 34.8% |
| **Confidence label output** | None parseable | Rich at T=0.0, fragmented at T=0.7 |
| **False-flag sensitivity** | Cannot assess | None detected |
| **Rhetorical profile** | Balanced (low hedging overall) | Balanced (moderate hedging) |

---

## Concept glossary

| Term | What it means |
|------|---------------|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via tools like Ollama, with no internet connection. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is deterministic (same input, same output). T=0.7 introduces variation. Gemma3n shows almost no difference between the two. |
| **Replications** | Running the same prompt multiple times to measure consistency. |
| **Conditions / factorial design** | The experimental structure. Each scenario is crossed with every attribution condition, creating a grid that isolates the effect of attribution framing. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. Gemma3n hedges much less than llama3.1 in absolute terms. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," "deterrence," etc.) per response. |
| **Cohen's d** | A measure of effect size. 0.2 = small, 0.5 = medium, 0.8+ = large. Every certainty calibration effect in gemma3n exceeds 1.0. |
| **E/H ratio** | Escalation density divided by hedging density. Below 1.0 = more hedging than escalation. |
| **RLHF** | Reinforcement Learning from Human Feedback. The process by which human reviewers shape model behavior. Different companies apply different RLHF standards, which is likely why Meta's llama3.1 and Google's gemma3n behave differently on US attribution. |
| **Safety classifier / refusal** | A mechanism that evaluates whether a prompt might produce harmful output. Gemma3n's classifier is much more permissive than llama3.1's for cyber threat attribution content. |
| **CVE hallucination** | When a model generates a CVE identifier that looks real but does not correspond to any actual vulnerability. Less of a concern with gemma3n (1.9% CVE rate) than with llama3.1 (34.8%). |
| **Confidence labels** | Self-assessments like "High confidence" or "Low confidence" in the model's output. Gemma3n does not produce them in a parseable format. |
| **Variance ratio / CV%** | Measures of output stability. Gemma3n's variance ratio of 0.98 means temperature has almost no effect on output variability. |

---

*Source data: [Gemma3n Results (Data)](Results_Data.md) — Full methodology: [Full Research Methodology](../../docs/methodology.md)*
