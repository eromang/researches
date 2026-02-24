
# EU Cyber Threat Landscape LLM Benchmark (Local – Ollama)

---

# Overview

This project provides a research-grade benchmarking framework to evaluate local Large Language Models (LLMs) for strategic EU-focused cyber threat landscape analysis, including geopolitical attribution sensitivity testing.

The benchmark is designed to:

- Run fully offline using Ollama
- Produce publication-ready artifacts (JSONL, CSV, Markdown, HTML dashboard)
- Support resume-enabled long benchmark runs
- Enable reproducible rhetorical and quantitative analysis

---

# Experimental Design

## Phase I – Controlled EU Context

### Structure
- 20 scenarios
- 5 conditions per scenario:
  - Neutral
  - China_Suspected
  - China_Confirmed
  - Russia_Suspected
  - Russia_Confirmed

Total prompts: 100

### Purpose
To test Actor × Certainty interaction under controlled EU and Eastern-flank geopolitical framing.

### Phase I Findings (qwen3:8b)

- No actor-specific escalation bias detected
- No actor-specific hedging bias detected
- Strong certainty calibration (Suspected → more hedging)
- Stable behavior across temperatures (T=0 and T=0.7)
- Institutional strategic tone maintained

Phase I establishes a baseline of actor symmetry under controlled EU context.

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
2. Chinese technology exposure (Huawei, ZTE, 5G, semiconductor supply chain)
3. Multipolar geopolitics (US–China–Russia cross-targeting)
4. False-flag scenarios
5. Non-state actor cases
6. Democratic process & sanctions contexts
7. Vendor-specific technology (S61–S68)

### Purpose
To test robustness of actor symmetry under:
- Technology-sensitive framing
- Western actor attribution (US)
- Non-Western non-peer actor attribution (Iran, DPRK)
- Multipolar geopolitical diversity
- Attribution ambiguity
- Vendor-specific technology contexts

---

# Controlled Variables

Across all prompts:

- Incident description remains constant within scenario
- Sector scope remains constant
- Only attribution framing varies
- Analytical instructions are identical
- Operational detail is prohibited

This ensures clean factorial manipulation.

---

# Runner

File:

run_benchmark_ollama_api.py (v2.4 resume-enabled)

Key features:

- Resume support (safe interruption)
- Durable JSONL checkpointing
- Automatic run_id management
- Markdown export per output
- CSV flat summaries
- HTML dashboard generation

---

# Example Execution

Phase I:

python3 run_benchmark_ollama_api.py \
  --prompts prompts/EU_Cyber_5_Condition_20_Scenarios_100_Prompts_Harmonised.csv \
  --models qwen3:8b deepseek-r1:8b llama3.1:8b-instruct-q4_K_M \
  --temps 0 0.7 \
  --reps 2 \
  --num-ctx 4096 \
  --outdir results \
  --export-md \
  --cooldown-auto \
  --chunk-size 10 \
  --chunk-pause 6

Phase II:

python3 run_benchmark_ollama_api.py \
  --prompts prompts/EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv \
  --models qwen3:8b deepseek-r1:8b llama3.1:8b-instruct-q4_K_M \
  --temps 0 0.7 \
  --reps 2 \
  --num-ctx 4096 \
  --outdir results \
  --export-md \
  --cooldown-auto \
  --chunk-size 10 \
  --chunk-pause 6

Each run creates a new run_id and does not overwrite previous runs unless --overwrite is used.

python3 run_benchmark_ollama_api.py \
  --prompts prompts/EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv \
  --models llama3.1:8b-instruct-q4_K_M \
  --temps 0 0.7 \
  --reps 2 \
  --num-ctx 4096 \
  --outdir results \
  --export-md \
  --cooldown-auto \
  --chunk-size 10 \
  --chunk-pause 6
  --resume

---

# Outputs

For each run:

- results/<run_id>.jsonl (source of truth)
- _flat.csv
- _summary.csv
- _stability.csv
- _pairs.csv
- _annotation_sheet.csv
- _report.md
- _dashboard.html
- Markdown exports per prompt (optional)

---

# Analysis Framework

Quantitative metrics:

- Escalation density per 1000 words
- Hedging density per 1000 words
- Escalation/Hedging ratio
- Certainty delta
- Effect sizes (Cohen’s d)
- ANOVA / hierarchical models

Qualitative audits:

- Actor asymmetry
- Certainty calibration
- Technology sensitivity
- Western actor bias
- False-flag handling
- Democratic process sensitivity

---

# Reproducibility

- Raw JSONL preserved
- Deterministic T=0 baseline
- Entropy robustness at T=0.7
- Harmonised prompt templates
- Resume-safe execution

---

# Scientific Positioning

Phase I:
Controlled Actor × Certainty evaluation (China, Russia — 5 conditions, 20 scenarios, 100 prompts).

Phase II:
Multipolar robustness testing with 5 actors (China, Russia, US, Iran, DPRK — 11 conditions, 48 scenarios, 528 prompts), technology and geopolitical diversity.

Together, the framework enables structured empirical assessment of geopolitical rhetorical calibration in local LLMs.
