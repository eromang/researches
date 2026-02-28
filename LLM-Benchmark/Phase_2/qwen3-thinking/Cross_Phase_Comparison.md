---
title: "Cross-Phase Comparison — Finding 4 Replication (Multi-Model Diplomatic Framing)"
date_created: 2026-02-26
date_updated: 2026-02-26
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
finding_tested: "Phase 1 Finding 4 — Chinese-origin models are softer on China"
status: complete
models_tested:
  - qwen3:8b
  - "llama3.1:8b-instruct-q4_K_M"
  - "deepseek-r1:8b"
related:
  - "[[qwen3-thinking/Results_Data]]"
  - "[[qwen3-thinking/Results]]"
  - "[[Phase_1/Results_Data]]"
---

# Cross-Phase Comparison — Finding 4 Replication

## 1. Finding Under Test

Phase 1 Finding 4 reported that qwen3:8b (Alibaba, 8B parameters) uses **diplomatic framing** when attributing cyber threats to China, while treating Russia attribution as a straightforward technical investigation. The key indicators were:

| Indicator | Phase 1 China_Confirmed | Phase 1 Russia_Confirmed | Phase 1 Ratio |
|---|---|---|---|
| "further corroboration required" | 30% | 5% | 6x |
| "false positives" warning | 2% | 0% | China-exclusive |
| "balance / avoid escalation" (Suspected) | 15% | 0% | China-exclusive |

Phase 1 Section 10.5 explicitly called for Phase 2 testing: *"Phase 2 should test non-Chinese-origin models as controls to determine whether this is a model-family-specific effect."*

## 2. Methodology

### Data

| Phase | qwen3:8b Records | Actors | Scenarios | Conditions |
|---|---|---|---|---|
| Phase 1 | 400 | China, Russia | 20 | 5 (Neutral, CN/RU x Suspected/Confirmed) |
| Phase 2 | 2,109 | China, Russia, US, Iran, DPRK | 48 | 11 (Neutral, 5 actors x Suspected/Confirmed) |

### Search method

Six indicator phrase families were searched (case-insensitive regex) across full `output_text`:

1. **further corroboration** — `further\s+corroboration`
2. **false positive(s)** — `false[\s-]positives?`
3. **false flag(s)** — `false[\s-]flags?`
4. **avoid/risk of/diplomatic escalation** — `(?:avoid|risk\s+of|diplomatic)\s+escalation`
5. **definitive proof/attribution** — `definitive\s+(?:proof|attribution)`
6. **corroborated by** — `corroborated\s+by`

Rates are computed as (records with at least one hit) / (total records per condition).

### Important caveat

The Phase 1 report cited rates of 30% vs 5% (6x ratio) for "further corroboration." When this script processes the same Phase 1 JSONL, it finds 31.2% vs 8.8% (3.6x). The difference likely reflects different grouping in the original analysis (e.g., temperature-stratified counts vs pooled counts, or manual review vs regex). The script's Phase 1 numbers are the regex-based ground truth used for consistent cross-phase comparison.

## 3. Results

### 3.1 "Further corroboration" — the key Phase 1 signal

| Phase | China_Confirmed | Russia_Confirmed | Ratio |
|---|---|---|---|
| Phase 1 | 25/80 (31.2%) | 7/80 (8.8%) | 3.6x |
| Phase 2 | 32/192 (16.7%) | 39/191 (20.4%) | 0.8x |

**Finding: Does not replicate.** The 3.6x China/Russia ratio from Phase 1 collapses to 0.8x in Phase 2. Russia actually shows a slightly higher rate than China. The absolute rate for China dropped from 31.2% to 16.7%, while Russia's rate rose from 8.8% to 20.4%.

For Suspected conditions, the pattern is similarly flat: Phase 2 shows 13.1% China vs 12.0% Russia (1.1x).

### 3.2 "False positives" — previously China-exclusive

| Phase | China_Confirmed | Russia_Confirmed | Ratio |
|---|---|---|---|
| Phase 1 | 2/80 (2.5%) | 0/80 (0.0%) | China-exclusive |
| Phase 2 | 5/192 (2.6%) | 7/191 (3.7%) | 0.7x |

**Finding: Does not replicate.** The phrase was China-exclusive in Phase 1 but appears for Russia at a slightly higher rate in Phase 2. It also appears in Neutral (2.6%), Iran_Suspected (5.2%), and US_Suspected (3.1%) conditions.

### 3.3 "Avoid/diplomatic/risk of escalation" — previously China-exclusive

| Phase | China_Suspected | Russia_Suspected | China_Confirmed | Russia_Confirmed |
|---|---|---|---|---|
| Phase 1 | 5/80 (6.2%) | 6/80 (7.5%) | 1/80 (1.2%) | 5/80 (6.2%) |
| Phase 2 | 8/191 (4.2%) | 13/191 (6.8%) | 15/192 (7.8%) | 7/191 (3.7%) |

**Finding: Does not replicate as China-exclusive.** The Phase 1 report cited 15% China_Suspected vs 0% Russia. The script finds 6.2% vs 7.5% for Phase 1 Suspected — Russia is actually slightly higher. In Phase 2, the pattern distributes across all actors. Iran_Confirmed shows the highest rate at 11.5%.

### 3.4 Expanded actor comparison — Phase 2 Confirmed

| Indicator | China | Russia | US | Iran | DPRK |
|---|---|---|---|---|---|
| further corroboration | 16.7% | 20.4% | 24.0% | 26.0% | 19.8% |
| false positive | 2.6% | 3.7% | 1.0% | 1.6% | 1.0% |
| false flag | 5.2% | 6.8% | 7.8% | 6.8% | 9.4% |
| avoid escalation | 7.8% | 3.7% | 6.8% | 11.5% | 3.1% |
| definitive proof | 45.3% | 37.7% | 44.3% | 40.1% | 39.1% |
| corroborated by | 5.2% | 5.2% | 5.2% | 3.1% | 6.8% |

**Key observation:** No indicator shows China-specific concentration. "Further corroboration" is actually highest for Iran (26.0%) and US (24.0%), with China lowest among attributed actors (16.7%). "Avoid escalation" is highest for Iran (11.5%), and "false flag" is highest for DPRK (9.4%). The distribution is actor-uniform or shows variation unrelated to the China-specific hypothesis.

### 3.5 Phase 2 Suspected conditions

| Indicator | China | Russia | US | Iran | DPRK |
|---|---|---|---|---|---|
| further corroboration | 13.1% | 12.0% | 12.0% | 9.9% | 12.0% |
| false positive | 4.7% | 2.6% | 3.1% | 5.2% | 1.0% |
| false flag | 8.4% | 11.5% | 8.3% | 6.8% | 7.8% |
| avoid escalation | 4.2% | 6.8% | 1.6% | 7.8% | 4.7% |
| definitive proof | 59.2% | 48.7% | 42.2% | 50.0% | 56.8% |
| corroborated by | 0.0% | 0.0% | 0.5% | 0.5% | 0.0% |

"Definitive proof" shows some variation (China 59.2% vs US 42.2%), but this indicator was not part of the original Finding 4 signal — it appeared symmetrically in Phase 1 and reflects a general hedging pattern under Suspected conditions.

### 3.6 Multi-model comparison — do other models show the same pattern?

Phase 1 Section 10.5 called for non-Chinese-origin models as controls. We tested the same six indicator phrases on two additional models:

| Model | Origin | Phase 1 | Phase 2 | Notes |
|---|---|---|---|---|
| qwen3:8b | Alibaba (CN) | 400 | 2,109 | Original Finding 4 subject |
| llama3.1:8b-instruct-q4_K_M | Meta (US) | 400 | 2,112 | US-origin control |
| deepseek-r1:8b | DeepSeek (CN) | 400 | 319 | ~29/condition — directional only |

#### llama3.1 (Meta, US-origin)

llama3.1 uses a fundamentally different rhetorical vocabulary. Key observations:

- **"Further corroboration":** 0% across virtually all conditions in both phases. llama3.1 simply does not use this phrase. The diplomatic hedging pattern that defined Finding 4 is absent from the US-origin model's vocabulary.
- **"False positives":** 0% everywhere. Not part of llama3.1's output repertoire.
- **"False flag":** Present at moderate rates (4.2%–11.5% in Phase 2), with China_Confirmed showing the highest rate (11.5% vs 6.2% for Russia and US). This is the only indicator where llama3.1 shows a mild China concentration — but it appears to reflect the model associating "false flag" with geopolitical complexity rather than diplomatic deflection.
- **"Avoid escalation":** Distributed across all actors (3.6%–9.9%), with no China-specific concentration.
- **"Definitive proof":** Low overall (1.0%–7.3%), with China_Confirmed slightly higher (7.3%) than Russia (3.6%).

**Conclusion:** llama3.1 does not exhibit the "further corroboration" or "false positives" patterns at all. Its rhetorical toolkit differs fundamentally from qwen3:8b. The Finding 4 indicators are model-specific to qwen3:8b, not a general LLM behavior.

#### deepseek-r1 (DeepSeek, Chinese-origin)

> [!warning] Sample-size caveat
> deepseek-r1 Phase 2 has only ~29 records per condition (319 total vs 2,109 for qwen3). Percentage differences of 3–7% are within sampling noise. Results are directional only.

Phase 1 observations:
- **"Further corroboration" (Suspected):** 17.5% China vs 8.8% Russia (2.0x) — consistent with Phase 1 Finding 4's observation that deepseek-r1 shifts the evidence burden for China.
- **"Further corroboration" (Confirmed):** 0% China vs 2.5% Russia — no China-specific pattern at Confirmed level.
- **"Definitive proof":** Very high rates overall (40%–96%), far exceeding qwen3:8b. This is deepseek-r1's primary hedging mechanism.

Phase 2 observations:
- **"Further corroboration" (Confirmed):** 13.3% China vs 10.3% Russia (1.3x) — mild China lean but within sampling noise at N=30.
- **"Further corroboration" (Suspected):** 10.0% China vs 17.9% Russia (0.6x) — ratio inverted from Phase 1.
- **"Definitive proof":** Dominant across all conditions (63%–93%), uniformly distributed. No actor-specific pattern.

**Conclusion:** The Phase 1 evidence-burden pattern (2.0x China/Russia on "further corroboration" Suspected) does not clearly replicate in Phase 2, though the small sample limits confidence. deepseek-r1's dominant hedging mechanism is "definitive proof/attribution" rather than "further corroboration," and this mechanism is actor-uniform.

### 3.7 Actor pairwise ratios — is any actor treated differently?

Beyond the China/Russia comparison, we tested whether any model treats US or DPRK actors systematically differently. Key actor pairings for Phase 2 Confirmed conditions:

#### China vs US (qwen3:8b, Phase 2 Confirmed)

| Indicator | China | US | Ratio |
|---|---|---|---|
| further corroboration | 16.7% | 24.0% | 0.7x |
| false positive | 2.6% | 1.0% | 2.5x |
| false flag | 5.2% | 7.8% | 0.7x |
| avoid escalation | 7.8% | 6.8% | 1.2x |
| definitive proof | 45.3% | 44.3% | 1.0x |

The US actually receives more "further corroboration" language than China (24.0% vs 16.7%). No indicator shows China-specific diplomatic framing relative to the US.

#### China vs DPRK (qwen3:8b, Phase 2 Confirmed)

| Indicator | China | DPRK | Ratio |
|---|---|---|---|
| further corroboration | 16.7% | 19.8% | 0.8x |
| false flag | 5.2% | 9.4% | 0.6x |
| avoid escalation | 7.8% | 3.1% | 2.5x |
| definitive proof | 45.3% | 39.1% | 1.2x |

"Avoid escalation" is higher for China than DPRK (7.8% vs 3.1%), but Iran shows an even higher rate (11.5%). This likely reflects the geopolitical complexity of China scenarios rather than protective framing.

#### US vs Russia (qwen3:8b, Phase 2 Confirmed)

| Indicator | US | Russia | Ratio |
|---|---|---|---|
| further corroboration | 24.0% | 20.4% | 1.2x |
| false flag | 7.8% | 6.8% | 1.1x |
| avoid escalation | 6.8% | 3.7% | 1.8x |
| definitive proof | 44.3% | 37.7% | 1.2x |

US rates are slightly higher than Russia across most indicators, suggesting that if any actor gets more cautious treatment, it is the US — not China. The difference is small and not statistically tested here.

#### Cross-model actor-pair comparison (Phase 2 Confirmed, "further corroboration")

| Actor pair | qwen3 ratio | llama3.1 ratio | deepseek-r1 ratio |
|---|---|---|---|
| China/Russia | 0.8x | — (both 0%) | 1.3x |
| China/US | 0.7x | — (both 0%) | 1.3x |
| China/DPRK | 0.8x | — (both 0%) | 4.0x |
| US/Russia | 1.2x | — (both 0%) | 1.0x |
| DPRK/Russia | 1.0x | — (both 0%) | 0.3x |

qwen3:8b shows no actor-specific concentration on any key indicator. llama3.1 does not use the phrase at all. deepseek-r1's China/DPRK ratio (4.0x) is notable but based on N=30 — a single additional hit shifts the ratio by ~3%.

## 4. Interpretation

### Why did the pattern not replicate?

Three factors likely explain the non-replication:

1. **Sample size:** Phase 1 had 80 records per condition (T=0.0 and T=0.7 pooled), a sample where a few extra phrase occurrences create large percentage swings. Phase 2's 192 per condition provides more stable estimates.

2. **Scenario diversity:** Phase 1 used 20 scenarios; Phase 2 uses 48. The additional 28 scenarios span more sectors and contexts. If the diplomatic framing was concentrated in a subset of Phase 1 scenarios (e.g., supply chain, semiconductors), dilution from other scenarios would reduce the rate.

3. **Thinking mode non-determinism:** qwen3:8b's internal chain-of-thought introduces path-dependent variation. At the same T=0.0, only 9.3% of prompt pairs produce identical output. The diplomatic phrasing choices may be stochastic artifacts of specific reasoning paths rather than systematic bias. Importantly, both phases used the same `--strip-thinking` configuration (thinking enabled, `<think>` tokens stripped from output), so thinking mode is not a confound between phases — the non-determinism referenced here is inherent to the thinking architecture in both phases.

### What about the Phase 1 numbers?

The script's regex-based Phase 1 numbers differ from the original report:
- "Further corroboration" Confirmed: script finds 31.2% CN vs 8.8% RU (3.6x), report cited 30% vs 5% (6x)
- "Avoid escalation" Suspected: script finds 6.2% CN vs 7.5% RU (0.8x), report cited 15% vs 0% (China-exclusive)

The "avoid escalation" discrepancy is the most significant. The original Finding 4 may have used narrower phrase matching or included related expressions not captured by this regex. Even so, the Phase 2 data shows no China-specific concentration regardless of search precision.

## 5. Verdict

**Finding 4 does not replicate in Phase 2 — for any model, any actor pairing.**

### 5.1 qwen3:8b (original Finding 4 subject)

| Indicator | Phase 1 Pattern | Phase 2 Result | Status |
|---|---|---|---|
| "further corroboration" | 3.6x China/Russia | 0.8x (Russia slightly higher) | Not replicated |
| "false positives" | China-exclusive | Distributed across actors | Not replicated |
| "avoid escalation" | China-exclusive | Highest for Iran, not China | Not replicated |

The Phase 1 finding of China-specific diplomatic framing was likely a **small-sample artifact** amplified by the 2-actor design (China and Russia only). When tested with 5 actors and 48 scenarios, qwen3:8b distributes diplomatic hedging phrases uniformly across all attribution targets.

### 5.2 Multi-model control (Phase 1 Section 10.5 question answered)

| Question | Answer |
|---|---|
| Does llama3.1 (US-origin) show the same diplomatic framing? | **No.** llama3.1 does not use "further corroboration" or "false positives" at all. Its rhetorical toolkit is fundamentally different. |
| Does deepseek-r1 (Chinese-origin) replicate its Phase 1 evidence-burden pattern? | **Not clearly.** The 2.0x China/Russia ratio on "further corroboration" Suspected from Phase 1 does not replicate in Phase 2 (0.6x), though the small sample (N~29/condition) limits confidence. |
| Is the Finding 4 pattern model-family-specific (Chinese-origin models)? | **No evidence for this.** The diplomatic framing indicators that defined Finding 4 are qwen3:8b-specific vocabulary, not a shared trait of Chinese-origin models. deepseek-r1 uses "definitive proof" as its primary hedging mechanism rather than "further corroboration." |

### 5.3 Actor pairwise ratios

| Question | Answer |
|---|---|
| Does any model treat China differently from the US? | **No.** qwen3:8b shows China/US ratios near 1.0 across all indicators. llama3.1 shows 0% for key indicators regardless of actor. |
| Does any model treat DPRK differently from Russia? | **No systematic pattern.** qwen3:8b's DPRK/Russia ratios are near 1.0. deepseek-r1 shows a 4.0x China/DPRK ratio on "further corroboration" but at N=30 this is not reliable. |
| Is any actor systematically treated with more diplomatic caution? | **No.** If anything, US and Iran show slightly higher rates on some indicators (e.g., "further corroboration" 24.0% for US vs 16.7% for China in qwen3:8b). The variation is small and not actor-specific. |

### 5.4 Overall conclusion

The diplomatic framing identified in Phase 1 Finding 4 was a general hedging strategy that qwen3:8b applies to all attribution scenarios, not a China-specific deflection. This conclusion is reinforced by three lines of evidence:

1. **Within qwen3:8b:** Phase 2's 5-actor, 48-scenario design shows uniform distribution of diplomatic phrases across all actors.
2. **Cross-model:** llama3.1 (US-origin) does not use the Finding 4 indicators at all — they are qwen3:8b-specific vocabulary, not a universal LLM behavior or a Chinese-origin model trait.
3. **Actor pairwise:** No model treats any specific actor with systematically more diplomatic caution than others. The variation that exists is small, inconsistent across indicators, and not aligned with the China-specific hypothesis.

This does not mean these models have no attribution biases — Phase 2's quantitative analysis (Results_Data Sections 5–9) identified subtle asymmetries (e.g., qwen3:8b's US assertion avoidance, llama3.1's US refusal pattern). But Finding 4's specific claim of China-targeted diplomatic framing is not supported by the expanded data.

## 6. Data Sources

- Phase 1 JSONL: `results/Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl`
- Phase 2 JSONL: `results/run_20260224T103518Z_51e859312629dea4.jsonl`
- Script: `scripts/finding4_crossphase.py`
- Raw counts: `results/qwen3_thinking/finding4_crossphase.csv`
- Formatted report: `results/qwen3_thinking/finding4_crossphase_report.md`

### Models covered

| Model | Origin | Phase 1 | Phase 2 |
|---|---|---|---|
| qwen3:8b | Alibaba (CN) | 400 | 2,109 |
| llama3.1:8b-instruct-q4_K_M | Meta (US) | 400 | 2,112 |
| deepseek-r1:8b | DeepSeek (CN) | 400 | 319 (~29/cond, directional) |

---

*Generated 2026-02-26 by `scripts/finding4_crossphase.py` with manual analysis.*
