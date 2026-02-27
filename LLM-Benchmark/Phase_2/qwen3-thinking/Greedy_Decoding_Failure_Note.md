---
title: "qwen3:8b Greedy Decoding Timeout Failures"
date_created: 2026-02-26
date_updated: 2026-02-26
project: "EU Cyber Threat Landscape LLM Benchmark"
phase: "Phase 2"
related:
  - "[[methodology]]"
  - "[[gemma3n/Results]]"
---

# qwen3:8b greedy decoding timeout failures

## Observation

During Phase 2 benchmark execution, 3 out of 1,551 qwen3:8b records failed with a 600-second timeout and 0 characters of output. All three failures share the same profile:

- **Model:** qwen3:8b (only model affected)
- **Temperature:** T=0.0 (greedy decoding)
- **Replication:** rep=2 only (rep=1 succeeded for all three prompts)
- **Error:** `TimeoutError('timed out')` at ~600,000ms
- **Output:** 0 characters (no visible output or thinking content)

| prompt_id | sector | rep | T | ok | chars | latency_ms |
|---|---|---|---|---|---|---|
| S38_Russia_Confirmed | Semiconductors | 2 | 0.0 | false | 0 | 600,010 |
| S46_China_Suspected | Finance | 2 | 0.0 | false | 0 | 599,999 |
| S47_Russia_Suspected | Telecom | 2 | 0.0 | false | 0 | 599,998 |

No other model (llama3.1:8b-instruct-q4_K_M, gemma3n:e4b) produced any timeout failures across any prompt at any temperature.

## Evidence: sibling variants

### S38 siblings (qwen3:8b, T=0.0)

| prompt_id | rep=1 | rep=2 |
|---|---|---|
| S38_China_Confirmed | 3,370 chars / 30s | 3,842 chars / 49s |
| S38_China_Suspected | 3,129 chars / 29s | 3,966 chars / 29s |
| S38_DPRK_Confirmed | 3,429 chars / 421s | 3,453 chars / 37s |
| S38_DPRK_Suspected | 3,852 chars / 30s | 3,578 chars / 32s |
| S38_Iran_Confirmed | 3,725 chars / 31s | 3,553 chars / 37s |
| S38_Iran_Suspected | 3,620 chars / 29s | 4,023 chars / 35s |
| S38_Neutral | 2,948 chars / 25s | 3,410 chars / 30s |
| S38_Russia_Confirmed | 3,744 chars / 30s | **TIMEOUT (600s)** |
| S38_Russia_Suspected | 3,990 chars / 30s | 3,787 chars / 32s |
| S38_US_Confirmed | 3,199 chars / 26s | 3,572 chars / 31s |
| S38_US_Suspected | 4,137 chars / 31s | 3,922 chars / 30s |

### S46 siblings (qwen3:8b, T=0.0)

| prompt_id | rep=1 | rep=2 |
|---|---|---|
| S46_China_Confirmed | 4,578 chars / 51s | 3,625 chars / 30s |
| S46_China_Suspected | 3,615 chars / 29s | **TIMEOUT (600s)** |
| S46_DPRK_Confirmed | 4,279 chars / 32s | 3,993 chars / 30s |
| S46_DPRK_Suspected | 4,434 chars / 35s | 3,985 chars / 27s |
| S46_Iran_Confirmed | 3,838 chars / 32s | 3,466 chars / 30s |
| S46_Iran_Suspected | 4,059 chars / 32s | 4,012 chars / 32s |
| S46_Neutral | 3,803 chars / 35s | 3,469 chars / 34s |
| S46_Russia_Confirmed | 3,999 chars / 32s | 4,091 chars / 49s |
| S46_Russia_Suspected | 3,871 chars / 29s | 3,840 chars / 30s |
| S46_US_Confirmed | 4,344 chars / 43s | 3,535 chars / 31s |
| S46_US_Suspected | 4,329 chars / 37s | 4,408 chars / 36s |

### S47 siblings (qwen3:8b, T=0.0)

| prompt_id | rep=1 | rep=2 |
|---|---|---|
| S47_China_Confirmed | 4,005 chars / 36s | 4,170 chars / 35s |
| S47_China_Suspected | 4,267 chars / 36s | 4,384 chars / 35s |
| S47_DPRK_Confirmed | 4,141 chars / 36s | 3,940 chars / 41s |
| S47_DPRK_Suspected | 3,930 chars / 36s | 4,310 chars / 35s |
| S47_Iran_Confirmed | 4,180 chars / 32s | 4,279 chars / 31s |
| S47_Iran_Suspected | 4,260 chars / 36s | 3,588 chars / 31s |
| S47_Neutral | 3,875 chars / 28s | 3,555 chars / 30s |
| S47_Russia_Confirmed | 4,142 chars / 33s | 3,963 chars / 34s |
| S47_Russia_Suspected | 4,059 chars / 33s | **TIMEOUT (600s)** |
| S47_US_Confirmed | 3,824 chars / 31s | 4,645 chars / 36s |
| S47_US_Suspected | 4,572 chars / 31s | 3,862 chars / 31s |

## Analysis

### Not strictly deterministic

The failures occur only on rep=2 while rep=1 succeeded for the same prompts at T=0.0. At greedy decoding (T=0.0), identical input should produce identical output. The fact that rep=1 and rep=2 diverge suggests that qwen3's internal thinking process (chain-of-thought reasoning before the visible response) introduces non-determinism even at T=0.0. This is consistent with qwen3's architecture: the model uses a thinking mode (`strip_thinking: true`, `no_think: false`) where an internal reasoning chain is generated before the visible output.

### Thinking-loop hypothesis

The 600-second timeout with 0 output characters (including 0 thinking characters) points to the model entering a degenerate thinking loop where tokens are generated but never reach the output boundary. Supporting evidence:

- S38_DPRK_Confirmed rep=1 had a latency of 420,680ms (~7 minutes) yet still produced 3,429 chars of visible output. This near-timeout latency suggests the thinking phase consumed most of the time budget.
- Several other records show elevated latencies (49s, 51s vs the ~30s baseline), indicating variable-length thinking phases.
- The failures produce no thinking text and no output text, suggesting the model never exited the thinking phase.

### Attribution pattern

Two of three failures involve Russia-attributed scenarios, and one involves China. However, the same attribution conditions succeed in the majority of sibling prompts. The failure appears to depend on the specific combination of scenario content, attribution condition, and the stochastic state of the thinking process at rep=2.

### Cross-model comparison

Neither llama3.1:8b-instruct-q4_K_M (2,112 records) nor gemma3n:e4b (2,112 records) produced any timeout failures across any prompt, temperature, or replication. This is a qwen3:8b-specific behavior, likely attributable to its thinking-mode architecture.

## Methodological note

- **Failure rate:** 3/1,551 = 0.19% of qwen3:8b records; 3/5,774 = 0.05% of the total dataset
- **Dataset integrity:** The failures do not affect the validity of the remaining 1,548 qwen3:8b records or the broader dataset
- **Recommendation:** These records should be excluded from statistical analyses (already flagged as `ok: false`). No re-run is necessary; the rep=1 data provides valid observations for these prompts.

## Source data

- JSONL: `results/run_20260224T103518Z_51e859312629dea4.jsonl`
- Prompts: `prompts/EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv`
