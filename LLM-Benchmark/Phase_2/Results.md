---
title: "Phase 2 — Actor Symmetry Across 7 Local LLMs: EU Cyber Threat Benchmark Results"
date_created: 2026-03-02
date_updated: 2026-03-02
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
related:
  - "[[Cross_Model_Confidence_Patterns]]"
  - "[[CVE_Fixation_Analysis]]"
  - "[[SA_Crisis_Model_Recommendation]]"
  - "[[04_Personal/LLM-Benchmark/docs/methodology]]"
---

# Phase 2 — Actor symmetry across 7 local LLMs: EU cyber threat benchmark results

## What I tested and why it matters

Phase 1 tested three models, two actors, and 20 scenarios. It found that certainty calibration works, that llama3.1 breaks at temperature 0.7, and that two Chinese-origin models showed China-specific diplomatic framing. That last finding raised a question worth answering: was it real bias, or a quirk of the small sample?

Phase 2 was built to answer that question at scale. I expanded the experiment from 3 models to 7, from 2 actors (China, Russia) to 5 (adding the US, Iran, and DPRK), and from 20 scenarios to 48. The result: 14,785 benchmark records across seven models from six providers spanning three continents. Every model ran fully offline on the same local machine using Ollama. No cloud APIs, no internet, no external dependencies. The whole thing is reproducible.

The model panel now includes the first EU-origin model (Mistral AI, France), three US-origin models (Meta, Google, Microsoft), and two Chinese-origin providers (Alibaba, DeepSeek) in three configurations. One of those configurations is a matched architecture pair: the same Qwen3 8B base with chain-of-thought reasoning enabled versus disabled. That pair lets me isolate the effect of the thinking process itself, separate from model training or provider origin.

Here is what I found.

---

## The setup in brief

Each of the 48 scenarios ran under 11 conditions:

- **Neutral** — no country named
- **Suspected** and **Confirmed** for each of 5 actors: China, Russia, US, Iran, DPRK

Only the attribution sentence changed between conditions. The incident description, sector, and analytical instructions stayed identical. Any difference in the output comes from the attribution framing alone.

Each model ran every scenario at two temperature settings (T=0.0 and T=0.7), twice each. That gives 48 scenarios x 11 conditions x 2 temperatures x 2 replications = 2,112 prompts per model. Seven models x 2,112 = 14,784 target records. The actual count is 14,785 because deepseek-r1 produced one extra record during resume handling.

---

## A few concepts before we go further

Some terms from Phase 1 carry forward, and Phase 2 introduces a few new ones. I will explain them as they come up, but here is a quick orientation.

**Temperature** is the randomness dial. At T=0.0 the model always picks the most probable next word (deterministic). At T=0.7 it sometimes picks less-likely words (more varied output). I tested both because analysts might use either setting.

**Hedging density** counts cautious words ("may," "might," "could," "potentially," "likely," "suggests," "appears," "uncertain") per response. More hedging means more cautious language.

**Escalation density** counts conflict-related words ("sanctions," "retaliation," "deterrence," "conflict," "war," "military") per response, after filtering out negation patterns like "de-escalation."

**E/H ratio** is escalation density divided by hedging density. Above 1.0 means the model escalates more than it hedges (assertive tone). Below 1.0 means it hedges more than it escalates (cautious tone). It is a quick proxy for overall rhetorical stance.

**Cohen's d** measures how big a difference is relative to the data's own variability. A d of 0.2 is small, 0.5 is medium, 0.8 or above is large. When I say hedging calibration has d = 1.34, that is a very large effect.

**Reasoning models** (qwen3:8b, deepseek-r1:8b) generate an internal chain of thought in `<think>` tokens before producing visible output. The thinking shapes the response but is stripped from the recorded output. **Standard instruct models** (llama3.1, gemma3n, qwen3-nothink, phi4, mistral) respond directly without an internal reasoning phase.

**Actor symmetry** means the model treats all five actors the same on a given metric. I test this with pairwise statistical comparisons across all 10 actor pairs (C(5,2) = 10) for each of 5 rhetorical pattern categories, yielding 50 tests per model.

**CVE fixation** means a model cites the same vulnerability identifier (like CVE-2021-4034) across unrelated sectors and scenarios. When a model inserts PwnKit into a water-utility scenario, an election scenario, and a semiconductor scenario, it is not performing vulnerability analysis. It is regurgitating a memorised pattern.

---

## The seven models

**llama3.1:8b-instruct-q4_K_M** — Meta (US). The fast one. About 13 seconds per response, roughly 3,070 characters. Reliable at T=0.0 but unstable at T=0.7 where its safety classifier starts misfiring. The only model with a significant refusal problem: 17.7% refusal rate on US_Confirmed at T=0.7.

**gemma3n:e4b** — Google (US). About 26 seconds, roughly 6,390 characters. The most stable model on temperature: variance ratio of 0.98 means T=0.7 output is almost identical to T=0.0. Near-zero refusals (0.19%), near-zero CVE mentions (1.9%). Uses prose-form confidence assessments rather than discrete labels.

**qwen3:8b (thinking mode)** — Alibaba (China). A reasoning model with internal chain-of-thought. About 35 seconds, roughly 3,817 characters. The strongest certainty calibration of any model (d = 2.26-3.35). Escalation-dominant rhetorical profile (E/H = 2.03-2.70). Zero refusals. The highest CVE citation rate (56.5%) with high diversity but mostly unverified identifiers. Three timeout failures where internal reasoning never converged.

**deepseek-r1:8b** — DeepSeek (China). Also a reasoning model. The slowest and longest: about 44.5 seconds and 7,932 characters per response. Hedging-dominant rhetorical profile (E/H = 0.80-1.03), the opposite of qwen3 despite sharing Chinese origin. Near-zero refusals (0.28%). Persistent PwnKit fixation from Phase 1 (73% of CVE-containing records cite the same vulnerability).

**qwen3-nothink:8b** — Alibaba/Community. A community fine-tune of the same Qwen3 8B base that natively suppresses chain-of-thought. About 21.8 seconds, roughly 4,756 characters. The architecture pair with qwen3-thinking: same weights, thinking off. Balanced rhetorical profile (E/H near 1.0). Zero refusals. The cleanest run in Phase 2.

**phi4:latest** — Microsoft (US). The largest model at 14 billion parameters, nearly twice the 8B models. About 30 seconds, roughly 3,894 characters. Hedging-dominant profile (E/H = 0.88-1.06). Effectively zero refusals. Very low CVE rate (2.8%) but when it does cite CVEs, 60.3% are Log4Shell.

**mistral:7b-instruct** — Mistral AI (France). The first EU-origin model in the benchmark. The smallest at 7B parameters and the fastest at about 15 seconds per response, with the shortest output at roughly 3,442 characters. Escalation-dominant profile (E/H = 1.12-1.95). Zero refusals. The most actor-uniform model: zero significant pairwise tests out of 50. Its confidence assessments use non-standard vocabulary that falls outside the taxonomy's regex patterns.

These models split naturally into groups. **Reasoning models**: qwen3-thinking and deepseek-r1, which generate internal chains of thought. **Architecture pair**: qwen3-thinking versus qwen3-nothink, the only case where I can compare the same base model with and without reasoning. **Standard instruct models**: llama3.1, gemma3n, phi4, and mistral, which respond directly.

---

## Finding 1: Every model calibrates certainty correctly

When I tell a model that attribution is "confirmed" instead of "suspected," it hedges less. This was true for all three Phase 1 models, and it is true for all seven Phase 2 models. No exceptions.

The size of the effect varies. At the strong end, qwen3-thinking produces Cohen's d values of 2.26-3.35 across the five actors, the largest effects in the entire benchmark. At the modest end, mistral produces d = 0.78-1.91, still solidly in the "large effect" range. Every model, every actor, every temperature: confirmed attribution reduces hedging.

| Model | Hedging calibration (d range) |
|-------|-------------------------------|
| qwen3-thinking | 2.26-3.35 |
| qwen3-nothink | 1.35-2.69 |
| llama3.1 | 1.34-2.36 |
| gemma3n | 1.41-2.24 |
| deepseek-r1 | 1.24-1.99 |
| phi4 | 1.07-2.53 |
| mistral | 0.78-1.91 |

This is the most replicated finding across the entire experiment. The mechanism varies: some models calibrate primarily through hedging reduction, others through a combination of hedging reduction and escalation increase (dual-channel calibration). But the direction is universal. Certainty framing works on every model I tested.

---

## Finding 2: Phase 1's China bias disappears at scale

Phase 1 found that qwen3 used diplomatic framing 6x more often for China than Russia ("further corroboration required" at 30% vs 5%). deepseek-r1 shifted the evidence burden, giving "High confidence" labels less often for China_Confirmed (50%) than Russia_Confirmed (55.6%).

Phase 2 tested whether this pattern survived with more data, more actors, and more scenarios. It did not.

I ran the same diplomatic-framing indicators from Phase 1 across qwen3's 2,109 Phase 2 records. The "further corroboration" ratio flipped: 16.7% for China_Confirmed versus 20.4% for Russia_Confirmed (0.8x, compared to Phase 1's 3.6x). The "false positives" warning, previously China-exclusive, now appeared for Russia at a slightly higher rate than China. The "avoid escalation" phrase, previously China-exclusive, was highest for Iran (11.5%), not China (7.8%).

Then I tested all seven models with pairwise actor-symmetry tests on confidence rhetoric. The results: 0 out of 5 China-versus-rest tests significant for any model. Not just the Chinese-origin models: all seven models from six providers (Alibaba, DeepSeek, Meta, Google, Microsoft, Mistral AI) agree. No model treats China differently from the other four actors.

The Phase 1 finding was a small-sample artifact. With 80 records per condition and only 2 actors, a few extra diplomatic phrases created large percentage swings. Phase 2's 192 records per condition and 5-actor design provides stable estimates. The China-specific diplomatic framing was a general hedging strategy that qwen3 applies to all attribution scenarios, not a China-specific deflection.

---

## Finding 3: Refusal patterns are model-specific, not origin-specific

llama3.1's refusal problem from Phase 1 persists and gets worse in Phase 2. At T=0.7, US_Confirmed triggers a 17.7% refusal rate, the highest of any condition for any model. Meta's safety classifier is most cautious about US attribution, not about adversary nations.

But this is a Meta-specific artifact, not a property of LLMs in general:

| Model | Origin | Refusal rate |
|-------|--------|-------------|
| llama3.1 | Meta (US) | 2.4% overall, 17.7% US_Confirmed at T=0.7 |
| deepseek-r1 | DeepSeek (China) | 0.28% |
| gemma3n | Google (US) | 0.19% |
| phi4 | Microsoft (US) | ~0.05% |
| qwen3-thinking | Alibaba (China) | 0% |
| qwen3-nothink | Alibaba (China) | 0% |
| mistral | Mistral AI (France) | 0% |

Three US-origin models, three completely different refusal profiles. Gemma3n and phi4 almost never refuse. llama3.1 refuses 17.7% of the time on one specific condition. The refusal behaviour reflects Meta's specific safety training choices, not something inherent to US-origin models or LLMs broadly.

---

## Finding 4: Models split into two rhetorical families

The E/H ratio reveals a clean split in how models frame their assessments at the Confirmed attribution level:

**Escalation-dominant** (E/H > 1.0): these models use more conflict-related language than cautious language when attribution is confirmed.

- qwen3-thinking: E/H = 2.03-2.70
- mistral: E/H = 1.12-1.95

**Hedging-dominant or balanced** (E/H near or below 1.0): these models maintain cautious framing even under confirmed attribution.

- deepseek-r1: E/H = 0.80-1.03
- phi4: E/H = 0.88-1.06
- qwen3-nothink: E/H = 0.94-1.13
- llama3.1: E/H = 0.50-0.72
- gemma3n: balanced (prose-form assessments)

This split does not follow model origin. Chinese-origin qwen3-thinking is the most escalation-dominant model in the benchmark. Chinese-origin deepseek-r1 is hedging-dominant. EU-origin mistral is escalation-dominant. The rhetorical family reflects model architecture and training methodology, not geography.

---

## Finding 5: Chain-of-thought amplifies everything

The qwen3-thinking versus qwen3-nothink pair is the only case in the benchmark where I can compare the same architecture with and without chain-of-thought reasoning. The differences are dramatic.

| Dimension | qwen3-thinking | qwen3-nothink | Effect |
|-----------|---------------|---------------|--------|
| Contextual support at Confirmed | 53% | 20% | h = 0.71 drop |
| Evidence qualification | 16% | 10% | significant drop |
| Corroboration demands | 34% | 18% | significant drop |
| CVE citation rate | 56.5% | 25.3% | halved |
| Actor pairwise tests significant | 1/50 | 8/50 | uniformity lost |
| Mean latency | ~34.5s | ~21.8s | 37% slower |
| Mean output length | ~3,817 chars | ~4,756 chars | 20% shorter |
| E/H ratio at Confirmed | 2.03-2.70 | 0.94-1.13 | escalation-dominant vs balanced |

Chain-of-thought is a rhetorical amplifier. It makes hedging calibration stronger (d = 2.26-3.35 versus 1.35-2.69), but it also makes the model more escalation-dominant, more CVE-prone, and more rhetorically uniform across actors. The thinking process imposes a consistent rhetorical stance that smooths out actor-specific differences.

It also makes the model 37% slower for 20% shorter visible output. The internal reasoning replaces rather than supplements visible elaboration. Whether the stronger calibration justifies the latency cost depends on the use case.

---

## Finding 6: CVE citations are training artifacts, not analysis

Three of seven models are fixated on a single CVE (>40% of CVE-containing records cite it):

| Model | Top CVE | Concentration | Overall CVE rate |
|-------|---------|--------------|-----------------|
| deepseek-r1 | CVE-2021-4034 (PwnKit) | 73.0% | 36.4% |
| phi4 | CVE-2021-44228 (Log4Shell) | 60.3% | 2.8% |
| llama3.1 | CVE-2021-44228 (Log4Shell) | 48.6% | 34.8% |

deepseek-r1's PwnKit fixation is essentially unchanged from Phase 1 (75% then, 73% now). With 32 times more data and a much wider scenario set, the model still cites the same Linux privilege-escalation vulnerability in three-quarters of its CVE-containing responses. This is a deeply embedded training artifact.

qwen3-thinking cites CVEs in 56.5% of responses with high diversity (no single CVE above 24%), but 4 of its top 5 CVEs are unverified, likely fabricated identifiers. qwen3-nothink shares the same fabricated CVE cluster (confirming these are base-model training artifacts, not reasoning-mode artifacts) but at half the rate (25.3%).

The sector-appropriateness check seals it: 57 CVEs appear across 5 or more unrelated sectors. The worst offenders span all 21 sectors in the benchmark. No vulnerability is relevant to aerospace, elections, water utilities, and parliamentary systems simultaneously. CVE citations in these responses are training memorisation, not analytical reasoning.

---

## Finding 7: Temperature mostly does not matter

Six of seven models are temperature-stable on rhetorical patterns. Their output at T=0.0 and T=0.7 shows no meaningful difference in confidence rhetoric, hedging calibration, or escalation framing.

The exception is llama3.1. At T=0.7, its refusal rate jumps from 0.2% to 4.6% overall (and 17.7% for US_Confirmed specifically), its rhetorical patterns degrade on 2 of 5 confidence categories, and its output variance increases by a factor of 4.4.

| Model | Temperature sensitivity |
|-------|----------------------|
| qwen3-thinking | Invariant (0/5 significant) |
| gemma3n | Invariant (0/5 significant) |
| mistral | Invariant (0/5 significant) |
| deepseek-r1 | Effectively invariant (1/5 marginal) |
| qwen3-nothink | Effectively invariant (1/5 marginal) |
| phi4 | Effectively invariant (1/5 marginal) |
| llama3.1 | Unstable (2/5 significant, refusal spike) |

For operational deployment, T=0.0 is the safer choice. But most models tolerate T=0.7 without meaningful degradation.

---

## Finding 8: The smallest model produces the most uniform output

mistral:7b-instruct (7B parameters, Mistral AI France) is the smallest model in Phase 2 and produces the most actor-uniform confidence rhetoric: 0 out of 50 pairwise tests significant. No actor pair shows any difference on any rhetorical pattern category. It is also the fastest (15 seconds per response), produces the shortest output (3,442 characters), and has the lowest confirmed-level hedging (0.62-1.02 terms per response).

This uniformity partly reflects a vocabulary-fit limitation: mistral's confidence assessments use non-standard vocabulary that falls outside the taxonomy's regex patterns, producing near-zero detection rates across all categories. But its quantitative hedging metrics show strong certainty calibration (d = 0.78-1.91), confirming that the model does differentiate between suspected and confirmed attribution. It just does so using language the taxonomy does not capture.

The lesson: being small and simple does not mean biased. It may mean less rhetorical surface area for bias to appear in.

---

## Finding 9: No Western-actor sensitivity

A reasonable concern going into Phase 2 was that models might treat Western actors (particularly the US) differently from adversary nations. The results show this is not a systematic pattern.

US_Confirmed is not treated with more caution or more aggression than Iran_Confirmed or DPRK_Confirmed by any model, with one exception: llama3.1's refusal pattern, which specifically targets US_Confirmed at T=0.7. But that is Meta's safety classifier, not a rhetorical bias in the analytical content.

Iran and DPRK are not treated as "lesser" actors. No model produces significantly different hedging for non-peer actors versus peer actors. All seven models apply hedging reductions uniformly across the five-actor panel when attribution moves from suspected to confirmed.

---

## The answer to the original question

The question I set out to answer was: do local LLMs treat all countries the same when writing cyber threat assessments?

Phase 2's answer: mostly yes. Seven models from six providers, tested across five actors and 48 scenarios, produce actor-uniform analytical content. No model shows systematic geopolitical bias in hedging calibration, escalation density, or confidence rhetoric.

The exceptions are real but model-specific:

- **llama3.1's US refusal pattern** (17.7% at T=0.7) reflects Meta's safety training, not a geopolitical stance
- **deepseek-r1's PwnKit fixation** (73% of CVE records) is a training-data memorisation artifact
- **phi4's Log4Shell fixation** (60.3% of its rare CVE records) is the same kind of training artifact

These are individual model quirks traceable to specific training choices, not systematic bias patterns shared across providers or model origins. Phase 1's most concerning finding, that Chinese-origin models showed China-specific diplomatic framing, does not survive at scale. It was a small-sample artifact amplified by a two-actor design.

---

## Scorecard

| | llama3.1 | gemma3n | qwen3-thinking | deepseek-r1 | qwen3-nothink | phi4 | mistral |
|---|---|---|---|---|---|---|---|
| **Origin** | Meta (US) | Google (US) | Alibaba (CN) | DeepSeek (CN) | Alibaba (CN) | Microsoft (US) | Mistral AI (FR) |
| **Parameters** | 8B | ~4B | 8B | 8B | 8B | 14B | 7B |
| **Type** | Instruct | Instruct | Reasoning | Reasoning | Instruct | Instruct | Instruct |
| **Latency** | ~13s | ~26s | ~35s | ~44.5s | ~21.8s | ~30s | ~15s |
| **Output length** | ~3,070 | ~6,390 | ~3,817 | ~7,932 | ~4,756 | ~3,894 | ~3,442 |
| **Refusal rate** | 2.4% | 0.19% | 0% | 0.28% | 0% | ~0% | 0% |
| **Hedging calibration (d)** | 1.34-2.36 | 1.41-2.24 | 2.26-3.35 | 1.24-1.99 | 1.35-2.69 | 1.07-2.53 | 0.78-1.91 |
| **E/H profile** | Hedging-dominant | Balanced | Escalation-dominant | Hedging-dominant | Balanced | Hedging-dominant | Escalation-dominant |
| **CVE rate** | 34.8% | 1.9% | 56.5% | 36.4% | 25.3% | 2.8% | 10.9% |
| **CVE fixated?** | Yes (Log4Shell) | No | No | Yes (PwnKit) | No | Yes (Log4Shell) | No |
| **Actor uniformity** | 3/50 | 13/50 | 1/50 | 1/50 | 8/50 | 10/50 | 0/50 |
| **Temp. stability** | Poor | Excellent | Excellent | Good | Good | Good | Excellent |

---

## What comes next

Phase 2 answers the core question about actor symmetry with reasonable confidence. Several directions remain open:

**Larger models.** All Phase 2 models are 7-14B parameters. Commercial-grade models (70B+, cloud APIs) might show different patterns, particularly on CVE accuracy and refusal behaviour.

**Multilingual prompts.** Every prompt in this benchmark is in English. Testing French, German, or Mandarin prompts could reveal language-dependent bias patterns invisible in English.

**Taxonomy limitations.** mistral's near-zero detection rates on rhetorical pattern categories expose a vocabulary-coverage gap in the regex-based taxonomy. A future iteration could use embedding-based similarity rather than keyword matching to capture non-standard confidence vocabulary.

**Operational recommendations.** For analysts choosing a model for situational awareness in cyber crisis management, the [[SA_Crisis_Model_Recommendation]] note synthesises the Phase 2 findings into a practical recommendation. The short version: qwen3-nothink offers the best balance of speed, reliability, calibration strength, and zero refusals.

---

## Concept glossary

| Term | What it means |
|---|---|
| **LLM** | Large Language Model. A neural network trained on text that generates text. "Local" means running it on your own hardware via Ollama, with no internet connection. |
| **Temperature** | A parameter controlling output randomness. T=0.0 is deterministic. T=0.7 introduces variation. |
| **Hedging density** | Count of cautious words ("may," "might," "could," "potentially," etc.) per response. Higher values mean more cautious language. |
| **Escalation density** | Count of conflict-related words ("sanctions," "retaliation," "military," etc.) per response, after negation-aware filtering. |
| **E/H ratio** | Escalation density divided by hedging density. Above 1.0 = assertive tone. Below 1.0 = cautious tone. |
| **Cohen's d** | Effect size measure. 0.2 = small, 0.5 = medium, 0.8+ = large. A d of 2.0+ is very large. |
| **Reasoning model** | An LLM that generates internal chain-of-thought (in `<think>` tokens) before visible output. qwen3:8b and deepseek-r1:8b are reasoning models. |
| **Actor symmetry** | Whether a model treats all five actors the same on a given metric. Tested via pairwise statistical comparisons (50 tests per model). |
| **CVE fixation** | When a model repeatedly cites the same vulnerability identifier across unrelated sectors. Flagged when one CVE exceeds 40% of CVE-containing records. |
| **CVE hallucination** | When a model generates a CVE identifier that looks real but does not correspond to any known vulnerability. |
| **Shannon entropy (normalised H)** | A diversity measure for CVE citations. 0 = all citations are the same CVE. 1 = perfectly uniform distribution. |
| **Confidence labels** | Explicit self-assessments ("High confidence," "Moderate confidence") extracted from model output. Calibration quality varies by model. |
| **RLHF** | Reinforcement Learning from Human Feedback. How models learn to refuse harmful requests and follow instructions. Can encode reviewer biases. |
| **Pairwise significance test** | A statistical test comparing two groups (e.g., China_Confirmed vs Russia_Confirmed hedging). Significance at p < 0.05 means the difference is unlikely to be random chance. |
| **Variance ratio** | Compares output variability at T=0.7 to T=0.0. Near 1.0 = temperature has little effect. Much above 1.0 = temperature destabilises output. |

---

*Source data: [[Cross_Model_Confidence_Patterns]] | [[CVE_Fixation_Analysis]] | Individual model results under Phase_2/{model}/ — Full methodology: [[04_Personal/LLM-Benchmark/docs/methodology]]*
