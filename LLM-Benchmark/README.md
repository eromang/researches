# EU Cyber Threat Landscape LLM Benchmark

A research-grade benchmark for evaluating whether locally deployed Large Language Models (LLMs) exhibit geopolitical bias in cyber threat landscape assessments. The benchmark tests actor-asymmetric escalation framing, hedging modulation, certainty calibration, and rhetorical amplification across EU-relevant geopolitical contexts.

All experiments run fully offline using [Ollama](https://ollama.com) — no cloud APIs, no internet connection required. Raw JSONL results are the source of truth and are fully reproducible.

## Experimental Design

### Phase I — Controlled EU Context

- **20 scenarios** across EU critical infrastructure sectors
- **5 conditions** per scenario: Neutral, China_Suspected, China_Confirmed, Russia_Suspected, Russia_Confirmed
- **3 models** tested: qwen3:8b, deepseek-r1:8b, llama3.1:8b-instruct-q4_K_M
- **2 temperatures**: 0.0 (deterministic) and 0.7 (sampling)
- **2 replications** per cell
- **Total: 1,200 prompts**

Phase I prompt set: the first 100 rows (20 scenarios x 5 conditions) of the 200-prompt CSV.

### Phase II — Context Expansion

- **48 scenarios** spanning 7 thematic blocks (EU internal, Chinese tech, multipolar, false-flag, non-state, democratic process, vendor-specific)
- **11 conditions** per scenario: Neutral + Suspected/Confirmed for China, Russia, US, Iran, DPRK
- **4 models** tested: llama3.1:8b-instruct-q4_K_M, gemma3n:e4b, qwen3:8b (reasoning), deepseek-r1:8b (reasoning, incomplete)
- **2 temperatures**, **2 replications**
- **Total: 2,112 prompts per model** (8,448 target; 8,449 completed)

### Controlled Variables

- Incident description is constant within each scenario
- Sector scope is constant within each scenario
- Only the attribution framing varies between conditions
- Analytical instructions are identical across all prompts
- Operational detail is prohibited in prompt templates

### Model Panel

| Model | Origin | Type | Parameters | Thinking | Status |
|-------|--------|------|------------|----------|--------|
| qwen3:8b | Alibaba (China) | Reasoning | 8B | Yes | Phase I + II complete |
| deepseek-r1:8b | DeepSeek (China) | Reasoning | 8B | Yes | Phase I + II complete |
| llama3.1:8b-instruct-q4_K_M | Meta (US) | Standard | 8B (Q4_K_M) | No | Phase I + II complete |
| gemma3n:e4b | Google (US) | Standard | ~4B effective | No | Phase II complete |

### Group Structure

- **Standard models**: llama3.1, gemma3n — direct response generation
- **Reasoning models**: qwen3, deepseek-r1 — chain-of-thought with `<think>` tokens (stripped from analysis via `--strip-thinking`)

## Repository Structure

```
LLM-Benchmark/
├── README.md                   ← This file
├── LICENSE                     ← MIT
├── requirements.txt            ← Minimal (stdlib only)
├── .gitattributes              ← Git LFS tracking for *.jsonl
├── .gitignore
│
├── docs/
│   └── methodology.md          ← Full research methodology
│
├── prompts/
│   ├── README.md               ← Prompt file guide (phase mapping)
│   ├── EU_Cyber_Phase_II_40_Scenarios_200_Prompts_Harmonised.csv
│   ├── EU_Cyber_Phase_II_40_Scenarios_280_Prompts_7_Conditions_Harmonised.csv
│   └── EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv
│
├── scripts/
│   ├── run_benchmark_v2_4.py   ← Runner v2.4 (Phase I)
│   ├── run_benchmark_v2_5.py   ← Runner v2.5 (Phase II, current)
│   ├── analyze_results.py      ← Analysis script
│   ├── convert_jsonl_to_flat.py← JSONL → flat CSV/JSON converter
│   └── live_dashboard.py       ← Real-time HTML dashboard
│
├── Phase_1/
│   ├── Results.md              ← Plain language results
│   └── Results_Data.md         ← Quantitative results with tables
│
├── Phase_2/
│   ├── llama31/
│   │   ├── Results.md          ← Plain language results (llama3.1)
│   │   └── Results_Data.md     ← Quantitative results (llama3.1)
│   ├── gemma3n/
│   │   ├── Results.md          ← Plain language results (gemma3n)
│   │   └── Results_Data.md     ← Quantitative results (gemma3n)
│   ├── qwen3-thinking/
│   │   ├── Results.md          ← Plain language results (qwen3 thinking)
│   │   ├── Results_Data.md     ← Quantitative results (qwen3 thinking)
│   │   ├── Cross_Phase_Comparison.md  ← Phase I vs II comparison
│   │   └── Greedy_Decoding_Failure_Note.md ← T=0.0 failure analysis
│   └── deepseek-r1/
│       ├── Results.md          ← Plain language results (deepseek-r1)
│       ├── Results_Data.md     ← Quantitative results (deepseek-r1)
│       ├── Confidence_Pattern_Analysis.md ← Confidence patterns
│       └── Cross_Phase_Comparison.md  ← Phase I vs II comparison
│
└── results/
    ├── RUNS.md                 ← Run registry
    ├── Phase_1/
    │   └── *.jsonl             ← Raw data (Git LFS)
    └── Phase_2/
        ├── llama31/
        │   └── *.jsonl
        └── gemma3n/
            └── gemma-results.jsonl
```

## Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed and running
- At least one model pulled (e.g., `ollama pull qwen3:8b`)

### Run a Benchmark

```bash
# Start Ollama
ollama serve

# Phase I: 20 scenarios, 5 conditions, single model (reasoning model with thinking stripped)
python3 scripts/run_benchmark_v2_5.py \
  --prompts prompts/EU_Cyber_Phase_II_40_Scenarios_200_Prompts_Harmonised.csv \
  --models qwen3:8b \
  --temps 0 0.7 \
  --reps 2 \
  --num-ctx 4096 \
  --strip-thinking \
  --outdir results \
  --resume

# Phase II: 48 scenarios, 11 conditions
python3 scripts/run_benchmark_v2_5.py \
  --prompts prompts/EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv \
  --models llama3.1:8b-instruct-q4_K_M \
  --temps 0 0.7 \
  --reps 2 \
  --num-ctx 4096 \
  --outdir results \
  --resume
```

## Runner (v2.5)

Key features:

- Resume-safe: interrupted runs continue from last completed record
- JSONL source of truth with batched fsync (every 10 records)
- Optional `--strip-thinking` to remove `<think>` tokens (for reasoning models)
- Optional `--no-think` to append `/no_think` to prompts (for qwen3-style models)
- Optional `--use-chat` for `/api/chat` endpoint (default: `/api/generate`)
- Adaptive cooldown via `--cooldown-auto`
- Per-prompt Markdown export via `--export-md`
- Live HTML dashboard via `scripts/live_dashboard.py`

### CLI Reference

| Flag | Description | Default |
|------|-------------|---------|
| `--prompts` | Path to prompt CSV | Required |
| `--models` | Space-separated model names | Required |
| `--temps` | Space-separated temperatures | `0` |
| `--reps` | Replications per cell | `1` |
| `--num-ctx` | Context window size | `4096` |
| `--outdir` | Output directory | `results` |
| `--resume` | Resume from existing JSONL | Off |
| `--export-md` | Export per-prompt Markdown files | Off |
| `--strip-thinking` | Remove `<think>` blocks from output | Off |
| `--no-think` | Append `/no_think` to prompts | Off |
| `--use-chat` | Use `/api/chat` endpoint | Off |
| `--cooldown-auto` | Scale cooldown by model size | Off |
| `--cooldown-base` | Base cooldown in seconds | `0` |
| `--chunk-size` | Records per chunk before pause | `0` (off) |
| `--chunk-pause` | Pause between chunks (seconds) | `0` |
| `--num-gpu` | GPU layers to offload | Ollama default |

## Results

### Phase I (1,200 records)

- **Certainty calibration works**: all models hedge less under Confirmed attribution (Cohen's d = -0.95 to -2.32)
- **Actor asymmetry is negligible on escalation**: China_Confirmed and Russia_Confirmed differ by < 1% on escalation density; E/H ratio diverges (13.9%) due to hedging differences
- **llama3.1 breaks at T=0.7**: 14% refusal rate, 16x variance increase — temperature-dependent stochastic safety activation
- **Chinese-origin models show China-sensitivity**: qwen3 uses diplomatic framing, deepseek-r1 shifts the evidence burden for China attribution
- **CVE hallucination is model-specific**: deepseek-r1 fixates on PwnKit (CVE-2021-4034); qwen3 never mentions CVEs

Detailed results: [Phase 1 Results](Phase_1/Results.md) | [Phase 1 Data](Phase_1/Results_Data.md)

### Phase II — llama3.1 (2,112 records)

- **Certainty calibration is robust and actor-uniform**: Cohen's d = 1.02-1.84 across all 5 actors
- **US_Confirmed triggers highest refusal rate**: 17.7% at T=0.7 — Meta's model is most cautious about US attribution
- **Escalation density is actor-invariant**: no significant pairwise differences
- **False-flag scenarios do not reduce overconfidence**: the model trusts attribution framing at face value

Detailed results: [Phase 2 Results](Phase_2/llama31/Results.md) | [Phase 2 Data](Phase_2/llama31/Results_Data.md)

### Phase II — gemma3n (2,112 records)

- **No US refusal asymmetry**: 0% US_Confirmed refusal — confirms the llama3.1 pattern is model-specific, not LLM-inherent
- **Excellent temperature stability**: variance ratio 0.98 (vs llama3.1's 4.39)
- **Near-zero refusals**: 0.19% overall (4 out of 2,112)
- **Very low CVE mentions**: 1.9% (vs llama3.1's 34.8%)

Detailed results: [Gemma3n Results](Phase_2/gemma3n/Results.md) | [Gemma3n Data](Phase_2/gemma3n/Results_Data.md)

### Phase II — qwen3:8b thinking (2,115 records)

- **Chinese-origin reasoning model on expanded scenarios**: same qwen3:8b from Phase I, now tested on 48 scenarios × 11 conditions
- **Mid-run `--strip-thinking` activation**: first 479 records without flag, remainder with — creates a natural within-run comparison
- **3 timeout failures**: all at T=0.0 where internal reasoning never terminated

Detailed results: [Qwen3 Thinking Results](Phase_2/qwen3-thinking/Results.md) | [Qwen3 Thinking Data](Phase_2/qwen3-thinking/Results_Data.md)

### Phase II — deepseek-r1:8b (2,113 records)

- **Chinese-origin reasoning model**: second Chinese-origin model, enabling cross-origin comparison with qwen3:8b
- **Strong certainty calibration**: hedging drops for all 5 actors (d = 1.24–1.99) — large effects, weaker than qwen3's 2.26–3.35
- **Hedging-dominant profile**: E/H ratios near 1.0, similar to llama3.1 — opposite to qwen3's escalation-dominant posture
- **Slowest and longest model**: ~44.5s latency, ~7,932-char output — 2x longer than any other model
- **No China-protective framing**: Phase 1 China-sensitivity does not replicate

Detailed results: [deepseek-r1 Results](Phase_2/deepseek-r1/Results.md) | [deepseek-r1 Data](Phase_2/deepseek-r1/Results_Data.md)

## Analysis

### Metrics

The analysis script computes:

- **Escalation density**: count of escalation terms (sanctions, retaliation, deterrence, conflict, war, military) per response
- **Hedging density**: count of hedging terms (may, might, could, potentially, likely, suggests, appears, uncertain, risk) per response
- **E/H ratio**: escalation / hedging — proxy for overall rhetorical tone
- **Cohen's d**: effect size for Suspected to Confirmed shifts
- **Pairwise actor comparisons**: Welch's t-test across all actor pairs
- **Confidence label extraction**: High/Moderate/Low from structured output
- **CVE detection**: real vs hallucinated CVE identifiers
- **Refusal classification**: refusal_like vs avoidance_like patterns

### Run Analysis

```bash
python3 scripts/analyze_results.py results/Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl
```

This produces an analysis directory with:
- `analysis_report.md` — full statistical report
- `analysis_summary_by_model_condition.csv` — per-model per-condition summary
- `analysis_tests_overview.csv` — all statistical tests
- `analysis_within_scenario_deltas.csv` — within-scenario effect sizes

## Regenerating Derived Files

Only JSONL source files are committed. All derived artifacts can be regenerated:

```bash
# Post-run artifacts (summary, pairs, stability, dashboard, annotation sheet)
python3 scripts/run_benchmark_v2_5.py --prompts <csv> --models <model> --outdir results --resume

# Flat CSV/JSON export
python3 scripts/convert_jsonl_to_flat.py results/Phase_1/<run>.jsonl

# Statistical analysis
python3 scripts/analyze_results.py results/Phase_1/<run>.jsonl --outdir results/Phase_1/analysis
```

## Reproducibility

- **Deterministic baseline**: T=0.0 runs produce byte-identical output across replications
- **Resume-safe**: interrupted runs continue from last completed record via JSONL key matching
- **JSONL source of truth**: all derived outputs (CSV, HTML, Markdown) are regenerated from JSONL
- **Fixed prompt templates**: identical analytical instructions across all conditions
- **No cloud dependency**: fully local execution via Ollama

## Citation

```bibtex
@misc{romang2026eucyberbenchmark,
  author       = {Eric Romang},
  title        = {EU Cyber Threat Landscape LLM Benchmark: Geopolitical Bias in Local Language Models},
  year         = {2026},
  url          = {https://github.com/romang/researches/tree/main/LLM-Benchmark},
  note         = {Research benchmark for evaluating actor-asymmetric framing in local LLMs}
}
```

## License

[MIT](LICENSE)
