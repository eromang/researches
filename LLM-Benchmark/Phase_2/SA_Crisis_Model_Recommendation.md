---
title: "Model Recommendation — Situational Awareness in Cyber Crisis Management"
date: 2026-02-28
phase: 2
document_type: analysis-index
tags:
  - benchmark/phase2
  - benchmark/cross-model
  - benchmark/recommendation
  - research/llm-crisis-management
related:
  - "[[Cross_Model_Confidence_Patterns]]"
  - "[[CVE_Fixation_Analysis]]"
  - "[[qwen3-nothink/Results]]"
  - "[[deepseek-r1/Results]]"
  - "[[qwen3-nothink/Thinking_vs_NoThink_Comparison]]"
---

# Model recommendation: situational awareness in cyber crisis management

Based on Phase 2 LLM Benchmark results (~10,552 records across 5 locally deployed 8B models), this note evaluates which model is best suited for **situational awareness (SA) during cyber crisis management** — a use case requiring unbiased, calibrated, reliable threat landscape assessments under operational pressure.

## SA crisis management requirements

For this use case, the critical dimensions are:

| Requirement | Why it matters |
|-------------|----------------|
| **Actor symmetry** | SA must treat all nation-state actors equally — bias distorts the threat picture |
| **Zero/near-zero refusal** | Cannot have a model refuse to analyze a scenario involving a specific actor during a crisis |
| **Strong certainty calibration** | Must distinguish suspected from confirmed attribution — drives response escalation decisions |
| **Balanced rhetorical profile** | Over-escalation risks panic; over-hedging risks inaction |
| **No CVE fixation/hallucination** | Fabricated CVEs contaminate technical intelligence |
| **Temperature stability** | Outputs must be reliable regardless of inference parameters |
| **Completion rate** | Zero tolerance for timeouts during crisis |
| **Latency** | Faster is better under operational pressure |

## Model scoring against SA requirements

| Dimension | llama3.1 | gemma3n | qwen3-think | deepseek-r1 | qwen3-nothink |
|-----------|----------|---------|-------------|-------------|---------------|
| Actor symmetry | Good (1/10) | **Poor** (13/50, US bias) | **Excellent** (1/50) | **Excellent** (1/50) | Good (8/50) |
| Refusal rate | **FAIL** (17.7% US) | Good (0.19%) | **Perfect** (0%) | Good (0.28%) | **Perfect** (0%) |
| Calibration strength | Strong (d = 1.3--2.4) | Strong (d = 1.4--2.2) | **Strongest** (d = 2.3--3.3) | Strong (d = 1.2--2.0) | Strong (d = 1.4--2.7) |
| Rhetorical balance | Hedging-heavy | Hedging-heavy | **Escalation-heavy** | Near-balanced | **Balanced** |
| CVE fixation | **FIXATED** (Log4Shell 49%) | Clean (1.9%) | Clean (diverse) | **FIXATED** (PwnKit 73%) | Clean (diverse) |
| Temp. stability | **Poor** (4.39 ratio) | Excellent (0.98) | Excellent (0.73) | Good (1.02) | Excellent (1.04) |
| Completion rate | Good | Good | 3 timeouts | 6 failures | **Perfect** (100%) |
| Latency | **Fastest** (~12s) | ~25s | ~35s | **Slowest** (~47s) | ~22s |

## Recommendation: qwen3-nothink:8b

### Why qwen3-nothink is the best fit for SA crisis management

**1. Zero refusals + zero failures.** 100% completion rate across 2,112 prompts. During a crisis, the model will never refuse to analyze a scenario or timeout. No other model achieves both.

**2. Balanced rhetorical profile (E/H = 0.85--1.13).** Neither over-escalating (which could trigger disproportionate responses) nor over-hedging (which could cause paralysis). This is uniquely suited to SA, where the output must inform but not panic decision-makers. Qwen3-thinking's escalation-dominant profile (E/H = 2.03--2.70) is a liability for crisis SA.

**3. Strong calibration without escalation bias.** Clearly distinguishes suspected from confirmed (d = 1.35--2.69) through hedging reduction, without also amplifying escalation language. This means escalation decisions remain with human analysts, not embedded in LLM rhetoric.

**4. Good actor symmetry (8/50).** No China-protective framing (0/5 China-vs-rest significant), no Western-actor refusal. The 8/50 differentiation is moderate but without systematic directional bias toward any specific actor.

**5. No CVE fixation.** Diverse CVE citations without fixation on a single vulnerability. While it does cite unverified CVEs (a universal problem), it doesn't contaminate outputs with a single memorised CVE across all sectors.

**6. Fast and stable.** ~22s latency (2nd fastest), excellent temperature stability (1.04 ratio), deterministic at T=0.0.

### Runner-up: deepseek-r1:8b

Strong calibration and excellent actor symmetry (1/50), but disqualified as primary recommendation due to:

- **PwnKit CVE fixation at 73%** — would contaminate technical SA with irrelevant vulnerability data
- **Slowest model (~47s)** — latency penalty unacceptable during crisis tempo
- **Longest output (~7,932 chars)** — over-verbose for rapid SA consumption

### Models to avoid for this use case

**llama3.1:8b** — 17.7% US refusal rate is a hard disqualifier. Cannot have SA gaps for US-attributed scenarios.

**qwen3:8b (thinking)** — Escalation-dominant rhetoric (E/H = 2.03--2.70) would systematically inflate threat perception in SA products, potentially triggering disproportionate crisis responses.

**gemma3n:e4b** — Most actor-differentiated model (13/50 significant pairwise tests) with systematic US hedging asymmetry. SA requires uniform treatment.

## Deployment note: false-flag blindness

All tested models share a universal weakness: **false-flag scenarios do not induce epistemic caution.** Models trust attribution framing at face value. This means SA products from any of these models must be paired with human analyst review for attribution quality, especially during crises where false-flag operations are a realistic concern.

This finding applies to qwen3-nothink as much as any other model. The recommendation does not eliminate the need for human oversight — it minimises the model's contribution to distortion.

## Implications for LLM-Crisis-Management project

This recommendation directly informs model selection for the [[LLM-Crisis-Management - Master Index|LLM-Crisis-Management]] project, which evaluates governance reliability of local LLMs in multi-phase crisis coordination simulations grounded in PGGCCN, NIS2, and EU-CyCLONe frameworks.

Based on this analysis:

- **qwen3-nothink:8b** should be prioritised as the first model to run through the crisis management benchmark
- **deepseek-r1:8b** is the natural second model for comparison (strong calibration, different rhetorical profile, but known CVE fixation liability)
- **llama3.1:8b** should be included for completeness but its US refusal pattern may produce data gaps in Russia_Suspected/Confirmed conditions
- The crisis management benchmark's **Institutional Fidelity Score** and **Escalation Proportionality Index** will provide validation data for this recommendation — if qwen3-nothink's balanced E/H ratio holds under role-constrained prompts, the recommendation is strengthened

## Data sources

- [[Cross_Model_Confidence_Patterns]] — actor uniformity, calibration mechanisms, rhetorical profiles
- [[CVE_Fixation_Analysis]] — CVE fixation detection, diversity indices, hallucination check
- [[qwen3-nothink/Results]] — qwen3-nothink:8b full results
- [[qwen3-nothink/Confidence_Pattern_Analysis]] — qwen3-nothink:8b confidence patterns
- [[qwen3-nothink/Thinking_vs_NoThink_Comparison]] — thinking vs no-think architecture comparison
- [[deepseek-r1/Results]] — deepseek-r1:8b full results (runner-up)
- [[llama31/Results]] — llama3.1:8b results (US refusal data)
- [[gemma3n/Results]] — gemma3n:e4b results (actor differentiation data)
- [[qwen3-thinking/Results]] — qwen3:8b thinking results (escalation profile data)
- Phase 2 source data: `results/run_20260224T103518Z_51e859312629dea4.jsonl`
