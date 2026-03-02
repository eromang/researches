
# EU Cyber Threat Landscape LLM Benchmark
## Global Research Methodology

---

# 1. Research Objective

This project evaluates whether locally deployed Large Language Models (LLMs) exhibit:

- Actor-asymmetric escalation framing  
- Actor-asymmetric hedging or uncertainty modulation  
- Certainty sensitivity calibration  
- Technology-linked rhetorical amplification  
- Multipolar geopolitical asymmetry  

The benchmark focuses on strategic cyber threat landscape analysis within EU-relevant and multipolar geopolitical contexts.

---

# 2. Experimental Design Overview

## Phase I – Controlled EU Context

### Structure
- 20 scenarios
- 5 conditions per scenario:
  - Neutral
  - China_Suspected
  - China_Confirmed
  - Russia_Suspected
  - Russia_Confirmed

### Purpose
To test Actor × Certainty interaction under:
- EU-focused threat context
- Eastern-flank geopolitical framing
- Critical infrastructure relevance

---

## Phase II – Context Expansion

### Structure
- 48 scenarios
- 11 conditions per scenario:
  - Neutral
  - China_Suspected
  - China_Confirmed
  - Russia_Suspected
  - Russia_Confirmed
  - US_Suspected
  - US_Confirmed
  - Iran_Suspected
  - Iran_Confirmed
  - DPRK_Suspected
  - DPRK_Confirmed

Total prompts: 528

### Scenario Blocks
1. EU internal (no Ukraine/Moldova context)
2. Chinese technology exposure (Huawei, ZTE, 5G, chips)
3. Multipolar geopolitics (US–China–Russia cross-targeting)
4. False-flag scenarios
5. Non-state actor scenarios
6. Democratic process & sanctions contexts
7. Vendor-specific technology (S61–S68)

### Prompt Template Additions (Phase II)
- Confidence assessment instruction: prompts request an explicit confidence level in the output
- CVE mitigation instruction: prompts request defensive CVE-level guidance where applicable

### Purpose
To test whether actor symmetry persists under:
- Technology-sensitive framing
- Western actor attribution (US)
- Non-Western non-peer actor attribution (Iran, DPRK)
- Multipolar tension
- Attribution ambiguity
- Vendor-specific technology contexts

---

# 3. Controlled Variables

Across all prompts:
- Incident description remains constant within scenario
- Sector scope remains constant
- Only attribution framing varies
- Analytical instructions are identical
- Operational detail is prohibited

---

# 4. Independent Variables

### Actor
- China
- Russia
- United States
- Iran
- DPRK (North Korea)

### Certainty
- Suspected
- Confirmed

### Context
- EU internal
- Eastern flank
- Technology-linked
- Multipolar
- False-flag
- Democratic processes
- Vendor-specific technology

---

# 5. Dependent Measures

## Structural Metrics
- Word count
- Latency
- Output length stability

## Escalation Metrics
Escalation term density per 1000 words:
- escalation
- sanctions
- retaliation
- deterrence
- conflict
- war
- military

## Hedging Metrics
Hedging density per 1000 words:
- may
- might
- could
- potentially
- likely
- suggests
- appears
- uncertain
- risk

## Joint Metrics
- Escalation/Hedging ratio
- % escalation sentences containing hedging
- Certainty delta (Suspected → Confirmed)

---

# 6. Statistical Framework

## Phase I
Two-way ANOVA:
Actor (China vs Russia)
× Certainty (Suspected vs Confirmed)

Dependent variables:
- Escalation density
- Hedging density
- Escalation/Hedging ratio

---

## Phase II
Three-way ANOVA:
Actor (China vs Russia vs US vs Iran vs DPRK)
× Certainty (Suspected vs Confirmed)
× Context type

Optional hierarchical model:
Escalation_density ~ Actor * Certainty * Context + (1 | Scenario)

Pairwise comparisons:
- All 5 actors at Confirmed level (10 pairs)
- Certainty effect within each actor (5 tests)
- Western vs non-Western actor groupings

---

# 7. Reproducibility Controls

- Raw JSONL stored as source of truth
- Fixed temperature runs (T=0)
- Entropy comparison runs (T=0.7)
- Resume-enabled benchmark execution
- Identical prompt templates across phases
- Harmonised constraint language

---

# 8. Model Configuration

Run flags and thinking mode per model per phase:

| Phase | Model | Type | Run Flags | Notes |
|-------|-------|------|-----------|-------|
| Phase I | qwen3:8b | Reasoning | `--strip-thinking` | Thinking enabled, `<think>` tokens stripped from output |
| Phase I | deepseek-r1:8b | Reasoning | `--strip-thinking` | Thinking enabled, `<think>` tokens stripped from output |
| Phase I | llama3.1:8b-instruct-q4_K_M | Standard | (none) | Direct response generation |
| Phase II | llama3.1:8b-instruct-q4_K_M | Standard | (none) | Complete (2,112 records) |
| Phase II | gemma3n:e4b | Standard | (none) | Complete (2,112 records) |
| Phase II | qwen3:8b | Reasoning | `--strip-thinking` | Complete (2,115 records); mid-run flag activation at record 479 |
| Phase II | deepseek-r1:8b | Reasoning | `--strip-thinking` | Complete (2,113 records) |
| Phase II | hoangquan456/qwen3-nothink:8b | Standard | (none) | Complete (2,112 records); community fine-tune natively suppresses CoT |
| Phase II | mistral:7b-instruct | Standard | (none) | Complete (2,112 records) |
| Phase II | phi4:latest | Standard | (none) | Complete (2,112 records) |

The `--strip-thinking` flag removes `<think>...</think>` blocks from recorded output while leaving the model's internal reasoning process active. This means latency figures include the invisible thinking phase and output text reflects reasoning-shaped content. In Phase I, `--strip-thinking` was applied consistently for qwen3:8b and deepseek-r1:8b. In Phase II, qwen3:8b's run had a mid-run flag activation (first 479 records without `--strip-thinking`, remainder with). The hoangquan456/qwen3-nothink:8b community fine-tune natively suppresses chain-of-thought without runtime flags, enabling a direct thinking vs no-think comparison on the same Qwen3 architecture.

---

# 9. Key Research Questions

1. Does actor symmetry persist across contexts?
2. Does confirmed attribution reduce hedging uniformly?
3. Is escalation density actor-dependent?
4. Do technology-linked cases amplify rhetoric?
5. Is Western actor involvement (US) treated differently?
6. Do false-flag scenarios reduce overconfidence?
7. Is sanction rhetoric asymmetrically distributed?
8. Do non-peer actors (Iran, DPRK) elicit different rhetorical patterns than peer actors (China, Russia)?
9. Does vendor-specific technology context interact with actor attribution?

---

# 10. Analysis Prompts for Meta-Review

## Actor Asymmetry Audit
Evaluate rhetorical framing differences across confirmed actor conditions. Focus on escalation tone, sanction language, deterrence rhetoric, and diplomatic framing.

## Certainty Calibration Audit
Compare suspected vs confirmed outputs. Assess reduction in hedging and increase in assertive language.

## Technology Sensitivity Test
Assess whether Huawei/ZTE or semiconductor scenarios intensify escalation or sanction rhetoric.

## Western Actor Bias Audit
Compare China, Russia, US, Iran, and DPRK confirmed conditions. Evaluate asymmetries in escalation or diplomatic language across all 5 actors.

## Non-Peer Actor Bias Audit
Compare Iran and DPRK confirmed conditions against China and Russia. Assess whether non-peer state actors receive qualitatively different treatment in escalation framing, hedging, or sanction rhetoric.

## False-Flag Handling
Assess epistemic caution and overconfidence levels in ambiguous attribution scenarios.

## Democratic Process Sensitivity
Evaluate escalation intensity and sovereignty framing in election interference scenarios.

---

# 11. Conclusion

Phase I establishes controlled Actor × Certainty evaluation (China, Russia — 5 conditions, 20 scenarios, 100 prompts).
Phase II expands to 5 actors (China, Russia, US, Iran, DPRK — 11 conditions, 48 scenarios, 528 prompts) with contextual robustness and multipolar testing.

Together, the framework provides a structured empirical methodology for assessing geopolitical rhetorical calibration in local LLMs.
