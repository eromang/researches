---
title: "Gemma3n Results — Plain Language Edition"
date_created: 2026-02-25
date_updated: 2026-02-27
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
related:
  - "[[gemma3n/Results_Data]]"
  - "[[methodology]]"
---

# Gemma3n results — plain language edition

## What I tested and why it matters

I ran Google's gemma3n:e4b model through the same 2,112-prompt benchmark I had already used on Meta's llama3.1. Same 48 scenarios. Same 11 attribution conditions. Same five countries: China, Russia, United States, Iran, and North Korea. Same two temperature settings. Same two replications per cell. The only variable was the model itself.

Why test a second model? Because a single model's behavior could be a quirk of that model's training. If llama3.1 flinches when asked to attribute a cyberattack to the United States, is that an LLM-wide pattern or a Meta-specific one? The only way to find out is to run the same experiment on a model built by a different company, with different training data, and different alignment choices. Gemma3n is made by Google, it is smaller (~4 billion effective parameters vs 8 billion for llama3.1), and it was trained independently. If the same biases appear, they are likely structural. If they do not, they tell us something about how individual companies shape their models.

Here is what I found.

---

## The setup in brief

Everything about the experimental design is identical to the llama3.1 run. The 48 scenarios, 11 conditions, 2 temperatures, and 2 replications produce 2,112 prompts. The scenarios span 21 sectors -- one more than llama3.1's 20, because gemma3n's run includes a "Trade" sector that was absent from the llama3.1 routing. This is a minor routing artifact from the shared benchmark run, not a deliberate change.

The conditions are the same: Neutral (no country named), plus Suspected and Confirmed for each of the five actors. The attribution sentence is the only thing that changes between conditions.

For a full explanation of the experimental design, see the llama3.1 humanized report: [[llama31/Results]].

---

## A few concepts before we go further

If you read the llama3.1 report, you already know these. If not, here are the key terms:

**Temperature** controls randomness. At T=0.0, the model picks the most probable word every time -- deterministic output. At T=0.7, it occasionally picks less likely words, introducing variation. I test both because temperature interacts with safety mechanisms in unpredictable ways.

**Hedging density** counts cautious words like "may," "might," "could," "potentially" per response. More hedge terms means more cautious language.

**Cohen's d** measures how big a difference is relative to variability. Below 0.2 is negligible. Around 0.5 is noticeable. Above 0.8 is hard to miss. Every certainty calibration effect in gemma3n exceeds 1.4 -- they are all large.

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

The effect sizes range from Cohen's d = 1.414 to 2.239 across the ten actor-temperature combinations. Every single one is large. Every single one is statistically significant.

Here is what that looks like at T=0.0:

| Actor | Suspected | Confirmed | Drop | Cohen's d |
|-------|-----------|-----------|------|-----------|
| China | 2.96 | 0.63 | -2.33 | 2.239 |
| DPRK | 3.08 | 0.77 | -2.31 | 2.230 |
| Russia | 2.94 | 0.79 | -2.15 | 1.936 |
| Iran | 2.92 | 0.77 | -2.15 | 1.877 |
| US | 2.92 | 1.21 | -1.71 | 1.474 |

The pattern is clear: the model hedges less when attribution is confirmed. It does this for every country, at every temperature. And just like llama3.1, it does this by reducing caution, not by increasing aggression. Escalation language barely moves (d < 0.34 for all actors).

The absolute hedge counts are lower than llama3.1's. Where llama3.1 averaged 2.91--7.13 hedge terms per response, gemma3n averages 0.63--3.08. Gemma3n is a fundamentally less hedging-prone model. But the relative pattern -- Confirmed reduces hedging -- is identical.

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

## Finding 3: Actor symmetry is very good, with a clear US hedging asymmetry

Outside the negligible refusal count, gemma3n treats all five actors with remarkable uniformity in most dimensions. Hedging, escalation, and output length cluster in tight bands -- but US_Confirmed stands apart on hedging.

At T=0.0 (Confirmed conditions):

| Metric | China | Russia | US | Iran | DPRK |
|--------|-------|--------|----|------|------|
| Hedge terms | 0.63 | 0.79 | 1.21 | 0.77 | 0.77 |
| Escalation terms | 0.54 | 0.38 | 0.31 | 0.58 | 0.48 |
| Output length (chars) | 6,404 | 6,328 | 6,311 | 6,293 | 6,358 |

The asymmetry: US_Confirmed produces clearly more hedging (1.21) than the other four actors (0.63--0.79). This difference is statistically significant: US vs China d = 0.595 (p = 0.00004) and US vs Russia d = 0.411 (p = 0.004) at T=0.0. The model hedges substantially more when attributing to the US, but unlike llama3.1, it does not refuse, truncate, or avoid the topic. The effect persists at T=0.7, though at reduced magnitude (US vs China d = 0.333, p = 0.021).

Escalation density is broadly actor-invariant. The one significant pairwise escalation comparison is Iran vs Russia at T=0.0 (d = 0.290, p = 0.044) -- Iran_Confirmed produces marginally more escalation language than Russia_Confirmed.

---

## Finding 4: Temperature is not the chaos variable

For llama3.1, temperature was everything. At T=0.0, the model was perfectly deterministic. At T=0.7, refusals spiked, output varied wildly, and confidence labels fragmented. The variance ratio was 4.39.

Gemma3n is different. Its variance ratio is 0.98. That means T=0.7 produces almost exactly the same output variability as T=0.0. The model's behavior is stable regardless of the temperature setting.

Refusals remain near-zero at both temperatures (0% at T=0.0, 0.38% at T=0.7). Output length barely changes (6,390 vs 6,441 chars). CV% barely moves (7.0% vs 6.9%).

If you are using gemma3n for structured threat assessments, you can use either temperature setting. T=0.7 does not introduce the noise, refusals, and unparseable output that it does for llama3.1.

---

## Finding 5: CVE mentions are rare

Only 1.9% of gemma3n's outputs mention a CVE identifier, compared to 34.8% for llama3.1. That is an 18x difference. The total across 2,112 outputs is 40 CVE instances.

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

## Finding 8: Gemma3n uses different hedging language for different countries -- more than any other model

Beyond measuring how much the model hedges (Finding 1), I also looked at what kind of cautious language it uses. I grouped hedging phrases into five categories: evidence qualification ("definitive attribution requires..."), misattribution warnings ("potential for misattribution"), corroboration demands ("further analysis needed"), contextual support ("geopolitical context supports..."), and procedural hedges ("subject to revision"). The same taxonomy used for qwen3 and llama3.1.

Gemma3n turned out to be the most uneven of the three models. Out of 50 statistical comparisons across actor pairs and categories, 13 reached significance. Qwen3 had 1. Llama3.1 had 3. Gemma3n has 13. This model does not treat all countries the same when choosing how to hedge.

The unevenness shows up in two places. First, how often the model asks for more evidence. When writing about confirmed Chinese attribution, gemma3n includes phrases like "further analysis needed" or "independent verification required" in 53% of responses. For Iran, that number is 76%. The full ranking: China (53%), DPRK (63%), Russia (65%), US (75%), Iran (76%). That ordering does not map onto any obvious geopolitical alignment -- it is not East-vs-West or authoritarian-vs-democratic.

Second, how often the model invokes geopolitical context to support its assessment. When writing about the US, only 26% of responses include language like "geopolitical context supports this" or "consistent with known capabilities." For Russia, 44% do. The model is less willing to lean on background knowledge when attributing to the US, which echoes the US hedging asymmetry from Finding 3.

One thing that might concern readers: does gemma3n protect China by demanding more evidence before blaming it? The data says the opposite. China gets the *fewest* demands for further corroboration -- 53% compared to 70% for everyone else combined. If the model were trying to cast doubt on Chinese attribution, it would demand more evidence, not less.

Gemma3n's overall rhetorical style is distinctive. It asks for more evidence far more often than the other two models -- corroboration phrases appear in 53 to 92% of responses, compared to 28-47% for qwen3 and 10-34% for llama3.1. This is a model that, by default, tells you the evidence is not enough. Temperature has no effect on any of this, consistent with gemma3n's stability.

Full analysis: [[gemma3n/Confidence_Pattern_Analysis]]. Cross-model comparison: [[Cross_Model_Confidence_Patterns]].

---

## Scorecard

| Dimension | gemma3n:e4b | llama3.1 (for comparison) |
|-----------|-------------|---------------------------|
| **Scenarios covered** | 48 | 48 |
| **Actors covered** | 5 | 5 |
| **Temperature stability** | Excellent (0.98 variance ratio) | Poor (4.39 variance ratio) |
| **Refusal rate** | 0.19% overall | 2.4% overall |
| **Hedging calibration** | Strong (d = 1.414--2.239) | Strong (d = 1.338--2.360) |
| **Escalation calibration** | Negligible shift | Negligible shift |
| **Actor symmetry (hedging)** | Good (US clearly elevated) | Good (DPRK slightly elevated) |
| **Actor symmetry (escalation)** | Excellent | Excellent |
| **Western actor sensitivity** | Low (no US refusal asymmetry) | High (17.7% US refusal at T=0.7) |
| **CVE mention rate** | 1.9% | 34.8% |
| **Confidence label output** | None parseable | Rich at T=0.0, fragmented at T=0.7 |
| **False-flag sensitivity** | Cannot assess | None detected |
| **Rhetorical profile** | Balanced (low hedging overall) |
| **Confidence pattern uniformity** | Actor-differentiated (13/50 sig.) | Mostly uniform (3/50 sig.) |

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
| **Cohen's d** | A measure of effect size. 0.2 = small, 0.5 = medium, 0.8+ = large. Every certainty calibration effect in gemma3n exceeds 1.4. |
| **E/H ratio** | Escalation density divided by hedging density. Below 1.0 = more hedging than escalation. |
| **RLHF** | Reinforcement Learning from Human Feedback. The process by which human reviewers shape model behavior. Different companies apply different RLHF standards, which is likely why Meta's llama3.1 and Google's gemma3n behave differently on US attribution. |
| **Safety classifier / refusal** | A mechanism that evaluates whether a prompt might produce harmful output. Gemma3n's classifier is much more permissive than llama3.1's for cyber threat attribution content. |
| **CVE hallucination** | When a model generates a CVE identifier that looks real but does not correspond to any actual vulnerability. Less of a concern with gemma3n (1.9% CVE rate) than with llama3.1 (34.8%). |
| **Confidence labels** | Self-assessments like "High confidence" or "Low confidence" in the model's output. Gemma3n does not produce them in a parseable format. |
| **Variance ratio / CV%** | Measures of output stability. Gemma3n's variance ratio of 0.98 means temperature has almost no effect on output variability. |

---

*Source data: [[gemma3n/Results_Data]] — Full methodology: [[methodology]]*