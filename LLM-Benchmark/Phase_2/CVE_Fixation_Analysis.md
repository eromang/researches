---
title: "CVE Fixation Analysis — Phase 2"
date: 2026-03-02
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/cve-analysis
  - benchmark/cross-model
---

# CVE fixation analysis

When an LLM repeatedly cites the same CVE across unrelated sectors and scenarios, it reveals a training artifact rather than analytical reasoning. A model that inserts CVE-2021-4034 (PwnKit) into a water-utility scenario, a parliamentary-election scenario, and a semiconductor supply-chain scenario is not performing vulnerability analysis — it is regurgitating a memorised pattern. This note examines CVE citation behaviour across all seven Phase 2 models and compares deepseek-r1's Phase 1 PwnKit fixation against its Phase 2 results.

## Phase 1 baseline

Phase 1 tested three models (qwen3, deepseek-r1, llama3.1) across 1,200 records. Only deepseek-r1 cited CVEs with any frequency, and its behaviour was striking:

- 24 records contained CVE mentions
- 18 of those 24 cited CVE-2021-4034 (PwnKit)
- **Concentration: 75%**

The other two Phase 1 models rarely or never cited CVEs. This made deepseek-r1's PwnKit fixation a clear Phase 2 verification target.

## CVE mention rates

Phase 2 expanded to 14,776 records across seven models. CVE citation rates vary dramatically:

| Model | Records | With CVEs | Rate | Mean CVE/record | Mean when present |
|-------|---------|-----------|------|-----------------|-------------------|
| qwen3:8b | 2,109 | 1,192 | 56.5% | 0.898 | 1.589 |
| deepseek-r1:8b | 2,107 | 767 | 36.4% | 0.638 | 1.754 |
| llama3.1:8b | 2,112 | 734 | 34.8% | 0.386 | 1.112 |
| qwen3-nothink:8b | 2,112 | 534 | 25.3% | 0.486 | 1.921 |
| mistral:7b-instruct | 2,112 | 230 | 10.9% | 0.167 | 1.535 |
| phi4:latest | 2,112 | 58 | 2.8% | 0.028 | 1.017 |
| gemma3n:e4b | 2,112 | 40 | 1.9% | 0.030 | 1.600 |

Qwen3 is the most CVE-active model by a wide margin, citing CVEs in more than half its responses. Gemma3n and phi4 essentially never cite CVEs — 40 and 58 records respectively out of 2,112. mistral:7b-instruct sits in the middle at 10.9% (230/2,112) — substantially below the high-CVE models (qwen3 at 56.5%, deepseek-r1 at 36.4%) but well above the near-zero models (phi4 at 2.8%, gemma3n at 1.9%). When mistral does cite CVEs, its density (1.535 per CVE-containing record) is moderate. phi4's CVE rate (2.8%) is slightly higher than gemma3n (1.9%) but both are negligible relative to the active models. When phi4 does cite CVEs, it produces the lowest density per record (1.017) — nearly always exactly one CVE. Qwen3-nothink (25.3%) cites CVEs at roughly half the rate of its thinking variant (56.5%), suggesting that chain-of-thought amplifies CVE citation behaviour. When qwen3-nothink does cite CVEs, it produces the highest density per record (1.921) of any model.

## Top CVEs per model

### deepseek-r1

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-4034 | 560 | 73.0% | real |
| 2 | CVE-2021-44228 | 148 | 19.3% | real |
| 3 | CVE-2021-3493 | 68 | 8.9% | real |
| 4 | CVE-2021-3156 | 33 | 4.3% | real |
| 5 | CVE-2021-4033 | 21 | 2.7% | unverified |

PwnKit dominates. The runner-up (Log4Shell) appears in under 20% of CVE-containing records.

### qwen3

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2023-1234 | 286 | 24.0% | unverified |
| 2 | CVE-2023-22891 | 258 | 21.6% | unverified |
| 3 | CVE-2021-44228 | 185 | 15.5% | real |
| 4 | CVE-2023-22892 | 122 | 10.2% | unverified |
| 5 | CVE-2023-22893 | 107 | 9.0% | unverified |

Qwen3 cites CVEs frequently but with no single dominant entry. Its top CVE (CVE-2023-1234) at 24% is well below the 40% fixation threshold. However, 4 of its top 5 are unverified — likely fabricated identifiers.

### llama3.1

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-44228 | 357 | 48.6% | real |
| 2 | CVE-2020-1472 | 79 | 10.8% | unverified |
| 3 | CVE-2019-0604 | 48 | 6.5% | unverified |
| 4 | CVE-2021-40444 | 40 | 5.4% | real |
| 5 | CVE-2021-31440 | 16 | 2.2% | unverified |

Log4Shell (CVE-2021-44228) appears in nearly half of llama3.1's CVE-containing records — exceeding the 40% fixation threshold. This is a new finding not observed in Phase 1.

### gemma3n

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2017-0144 | 10 | 25.0% | unverified |
| 2 | CVE-2023-23397 | 8 | 20.0% | unverified |
| 3 | CVE-2023-0666 | 5 | 12.5% | unverified |
| 4 | CVE-2023-0669 | 3 | 7.5% | unverified |
| 5 | CVE-2023-0123 | 3 | 7.5% | unverified |

With only 40 CVE-containing records total, gemma3n's percentages are not statistically meaningful. Its top CVE (likely an EternalBlue reference) appears in just 10 records.

### qwen3-nothink

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2023-22892 | 121 | 22.7% | unverified |
| 2 | CVE-2023-22891 | 120 | 22.5% | unverified |
| 3 | CVE-2023-22893 | 64 | 12.0% | unverified |
| 4 | CVE-2021-44228 | 60 | 11.2% | real |
| 5 | CVE-2021-40444 | 57 | 10.7% | real |

Qwen3-nothink shares its top CVE identifiers with qwen3-thinking (CVE-2023-22891, CVE-2023-22892, CVE-2023-22893) — the same fabricated CVE cluster appears in both variants, confirming these are training artifacts from the shared Qwen3 base rather than reasoning-mode artifacts. The top CVE at 22.7% is well below the 40% fixation threshold. No PwnKit fixation (0 mentions).

### phi4

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2021-44228 | 35 | 60.3% | real |
| 2 | CVE-2020-10135 | 4 | 6.9% | unverified |
| 3 | CVE-2020-1472 | 3 | 5.2% | unverified |
| 4 | CVE-2020-1234 | 2 | 3.4% | unverified |
| 5 | CVE-2020-15999 | 2 | 3.4% | unverified |

phi4 cites CVEs very rarely (58 records out of 2,112) but when it does, it fixates heavily on Log4Shell (CVE-2021-44228) at 60.3% — the highest single-CVE concentration of any model. This is the same fixation target as llama3.1 (48.6%), suggesting a shared training-data emphasis on Log4Shell across US-origin models. With only 18 unique CVEs and near-zero overall rate, phi4's CVE behaviour is essentially a rare-event pattern dominated by one memorised vulnerability.

### mistral

| Rank | CVE | Records | % of CVE records | Status |
|------|-----|---------|------------------|--------|
| 1 | CVE-2019-19781 | 66 | 28.7% | unverified |
| 2 | CVE-2021-30551 | 32 | 13.9% | unverified |
| 3 | CVE-2017-11882 | 21 | 9.1% | unverified |
| 4 | CVE-2017-0144 | 15 | 6.5% | unverified |
| 5 | CVE-2022-30668 | 15 | 6.5% | unverified |

mistral's top CVE (CVE-2019-19781, a Citrix ADC vulnerability) appears in 28.7% of CVE-containing records — well below the 40% fixation threshold. No PwnKit fixation (1 mention, 0.4%). The model cites 94 unique CVEs across 230 CVE-containing records, giving it the second-highest Shannon diversity (normalised H = 0.803) after gemma3n (0.910). Unlike other models, mistral's top CVEs are predominantly 2017–2019 vintage rather than 2021+, suggesting a different training-data emphasis.

## Fixation detection

The diversity index uses Shannon entropy to quantify how concentrated a model's CVE citations are. Normalised H ranges from 0 (all citations are the same CVE) to 1 (perfectly uniform distribution). Fixation is flagged when a single CVE exceeds 40% of CVE-containing records.

| Model | CVE records | Unique CVEs | Shannon H | Normalised H | Top CVE | Top % | Fixated? |
|-------|-------------|-------------|-----------|--------------|---------|-------|----------|
| deepseek-r1 | 767 | 274 | 4.789 | 0.591 | CVE-2021-4034 | 73.0% | **YES** |
| llama3.1 | 734 | 137 | 4.144 | 0.584 | CVE-2021-44228 | 48.6% | **YES** |
| phi4 | 58 | 18 | 2.556 | 0.613 | CVE-2021-44228 | 60.3% | **YES** |
| qwen3 | 1,192 | 336 | 5.624 | 0.670 | CVE-2023-1234 | 24.0% | no |
| qwen3-nothink | 534 | 228 | 5.781 | 0.738 | CVE-2023-22892 | 22.7% | no |
| mistral | 230 | 94 | 5.263 | 0.803 | CVE-2019-19781 | 28.7% | no |
| gemma3n | 40 | 29 | 4.420 | 0.910 | CVE-2017-0144 | 25.0% | no |

Three of seven models are fixated. Deepseek-r1 and llama3.1 have nearly identical normalised entropy (~0.59), but their fixation targets are different CVEs. phi4 is also fixated on Log4Shell (60.3%) with low normalised entropy (0.613), but its tiny sample (58 CVE records) means this is a rare-event fixation — the model almost never cites CVEs, and when it does, it defaults to Log4Shell. mistral sits in a middle zone: moderate CVE rate (10.9%), no fixation (top CVE at 28.7%), and the second-highest normalised entropy (0.803) after gemma3n — a genuinely diverse CVE profile rather than a rare-event artifact. Qwen3-nothink has the highest normalised entropy (0.738) of any CVE-active model — more diverse than qwen3-thinking (0.670), suggesting that chain-of-thought increases fixation tendency while reducing diversity. Gemma3n's high normalised H (0.910) reflects its tiny sample size rather than genuine diversity.

## PwnKit: Phase 1 to Phase 2 comparison

Deepseek-r1 is the only model tested in both phases with meaningful CVE citation, allowing direct comparison:

| Metric | Phase 1 | Phase 2 | Change |
|--------|---------|---------|--------|
| CVE-containing records | 24 | 767 | 32x more data |
| PwnKit mentions | 18 | 560 | — |
| PwnKit concentration | 75.0% | 73.0% | -2.0 pp |

The fixation persists essentially unchanged. With 32 times more data and a much wider scenario set (48 scenarios vs 20, 11 conditions vs 5), deepseek-r1 still cites PwnKit in nearly three-quarters of its CVE-containing responses. The 2 percentage-point decrease is not meaningful — this is a stable, deeply embedded training artifact.

## New finding: llama3.1 Log4Shell fixation

Phase 1 did not flag llama3.1 for CVE fixation because its overall CVE mention rate was low. Phase 2's expanded dataset reveals that when llama3.1 does cite CVEs (734 records), it fixates on Log4Shell (CVE-2021-44228) at 48.6% — crossing the 40% threshold.

This is a qualitatively different fixation from deepseek-r1's PwnKit pattern:

- **deepseek-r1** fixates on a Linux privilege-escalation vulnerability (PwnKit), inserting it into scenarios where privilege escalation is irrelevant
- **llama3.1** fixates on a Java logging library vulnerability (Log4Shell), inserting it into scenarios where Java infrastructure is irrelevant

Both represent the same underlying problem: the model has a memorised CVE that it produces whenever the prompt mentions "vulnerability" or "exploit," regardless of sector or technical context.

## Sector appropriateness

57 CVEs appear across 5 or more unrelated sectors in the benchmark output (up from 52 with 6 models). The top offenders each span 21 sectors — effectively every sector in the benchmark:

| CVE | Sector count | Models contributing |
|-----|-------------|---------------------|
| CVE-2021-44228 (Log4Shell) | 21 | deepseek-r1, qwen3, llama3.1, phi4 |
| CVE-2021-4034 (PwnKit) | 21 | deepseek-r1 |
| CVE-2023-1234 | 21 | qwen3 |
| CVE-2020-1472 | 19 | deepseek-r1, llama3.1 |
| CVE-2021-40444 | 19 | qwen3, llama3.1, mistral |

A CVE appearing in 21 out of 21 sectors is definitionally sector-inappropriate — no single vulnerability is relevant to aerospace, elections, water utilities, and parliamentary systems simultaneously. This confirms that CVE citations in benchmark responses are training artifacts, not analytical outputs.

## CVE hallucination check

Each model's CVE inventory was checked against known CVE databases:

| Model | Real | Hallucinated | Unverified | Total unique |
|-------|------|-------------|------------|--------------|
| deepseek-r1 | 5 | 3 | 266 | 274 |
| qwen3 | 3 | 0 | 333 | 336 |
| llama3.1 | 5 | 0 | 132 | 137 |
| qwen3-nothink | 2 | 0 | 226 | 228 |
| mistral | 3 | 0 | 91 | 94 |
| phi4 | 2 | 0 | 16 | 18 |
| gemma3n | 1 | 0 | 28 | 29 |

"Unverified" means the CVE identifier has a valid format but could not be confirmed in public databases at analysis time. The vast majority of cited CVEs across all models are unverified — models generate plausible-looking CVE identifiers that may or may not correspond to real vulnerabilities. Only deepseek-r1 produces confirmed hallucinated CVEs (3 identifiers that are demonstrably invalid). mistral has 3 confirmed-real CVEs (CVE-2020-0688, CVE-2021-4034, CVE-2021-40444), 0 hallucinated, and 91 unverified — placing it in the middle of the pack for real-CVE recall, matching qwen3's count. phi4 has the smallest CVE inventory (18 unique) with 2 confirmed real (CVE-2021-44228 and CVE-2021-40444), 0 hallucinated, and only 16 unverified — reflecting its near-zero CVE citation rate rather than higher accuracy. Qwen3-nothink produces fewer confirmed-real CVEs (2) than its thinking variant (3), despite 228 unique identifiers — chain-of-thought may marginally improve CVE recall accuracy.

## Condition and temperature effects

CVE citation rates vary modestly by actor condition and temperature. Full breakdowns are available in the script output; key patterns:

**Actor effects:** No model shows dramatic actor-dependent CVE rates. Deepseek-r1 ranges from 29.2% (US Confirmed) to 42.2% (Neutral). Qwen3 ranges from 47.1% (Russia Confirmed) to 62.8% (China Suspected). Qwen3-nothink ranges from 19.8% (China/US Confirmed) to 34.9% (Russia Suspected). mistral ranges from 6.2% (US Confirmed) to 16.2% (Neutral) — a wider range than phi4 but still without a consistent geopolitical pattern. phi4 ranges from 1.6% (Iran Suspected) to 3.6% (China/US Confirmed) — effectively flat across all conditions at its near-zero baseline. The variation does not follow a consistent geopolitical pattern across any model.

**Temperature effects:** Deepseek-r1 shows a modest decrease at T=0.7 (38.7% to 34.1%). Qwen3 is temperature-invariant (56.4% vs 56.6%). Llama3.1 shows a small decrease (36.4% to 33.1%). Gemma3n is invariant (1.9% at both temperatures). mistral shows a modest increase at T=0.7 (9.8% to 11.9%), consistent with the general pattern of slight temperature-induced variation. phi4 shows a modest increase at T=0.7 (2.1% to 3.4%), though with such small absolute numbers (22 vs 36 records) this is not statistically meaningful. Qwen3-nothink shows a modest increase at T=0.7 (22.4% to 28.2%) — the only model where higher temperature meaningfully increases CVE citation.

## Key findings

1. **PwnKit fixation persists in deepseek-r1.** 560 of 767 CVE-containing records (73.0%) cite CVE-2021-4034 — essentially unchanged from Phase 1's 75%. This is a stable training artifact that 32x more data and wider scenario coverage did not dilute.

2. **llama3.1 has a Log4Shell fixation.** 357 of 734 CVE-containing records (48.6%) cite CVE-2021-44228. This new finding was not visible in Phase 1 due to lower overall CVE mention rates.

3. **qwen3 is the most CVE-active but most diverse.** It cites CVEs in 56.5% of responses but no single CVE exceeds 24% of its CVE records. Its diversity (normalised H = 0.670) comes at a cost: 4 of its top 5 CVEs are unverified identifiers.

4. **qwen3-nothink is the most CVE-diverse active model.** Normalised entropy of 0.738 exceeds qwen3-thinking's 0.670, with no single CVE above 23%. Removing chain-of-thought halves CVE mention rate (56.5% → 25.3%) while improving diversity — CoT amplifies CVE citation and concentrates it.

5. **phi4 has a rare-event Log4Shell fixation.** phi4 cites CVEs in only 2.8% of responses (58/2,112), but when it does, 60.3% cite CVE-2021-44228 — the highest single-CVE concentration of any model. This shares the same fixation target as llama3.1, suggesting Log4Shell emphasis in US-origin model training data.

6. **gemma3n and phi4 effectively do not cite CVEs.** At 1.9% (gemma3n) and 2.8% (phi4), CVE citation is negligible for both models — a fundamentally different approach to the benchmark prompts compared to the CVE-active models.

7. **mistral occupies a moderate middle ground.** At 10.9% (230/2,112), mistral cites CVEs more than phi4 and gemma3n but far less than the high-CVE models. Its top CVE (CVE-2019-19781) at 28.7% sits well below the 40% fixation threshold, and its normalised entropy (0.803) is the second-highest — a genuinely diverse CVE profile. Its top CVEs skew older (2017–2019 vintage), unlike other models' 2021+ emphasis.

8. **57 CVEs appear across 5+ unrelated sectors.** The worst offenders span all 21 sectors, confirming that CVE citation is sector-inappropriate and reflects training memorisation rather than analytical reasoning.

9. **Most cited CVEs are unverified.** Across all seven models, the vast majority of unique CVE identifiers could not be confirmed against public databases. Only 21 unique CVEs across all models are confirmed real; 3 are confirmed hallucinated (all from deepseek-r1).

10. **CVE fixation is model-specific, not model-origin-specific.** The two Chinese-origin models (deepseek-r1 and qwen3) show opposite CVE behaviours — one fixated, one diverse. The two US-origin models (llama3.1 and phi4) both fixate on Log4Shell but at very different citation rates (34.8% vs 2.8%). The EU-origin model (mistral) shows no fixation and the second-highest diversity. The community fine-tune (qwen3-nothink) preserves the same fabricated CVE identifiers as qwen3-thinking, confirming these are base-model training artifacts. Training data composition, not model provenance or reasoning mode, drives CVE citation patterns.

## Data sources

- Script output: `results/Phase_2/cve_patterns/cve_fixation_report.md`
- Analysis script: `scripts/analyze_cve_patterns.py`
- Phase 1 baseline: [[Phase_1/Results]] (Finding 5: CVE hallucination)
- Phase 2 source data: `results/run_20260224T103518Z_51e859312629dea4.jsonl`
- Related analysis: [[Cross_Model_Confidence_Patterns]]
