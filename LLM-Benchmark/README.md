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
- **7 models** tested: llama3.1:8b-instruct-q4_K_M, gemma3n:e4b, qwen3:8b (reasoning), deepseek-r1:8b (reasoning), hoangquan456/qwen3-nothink:8b, phi4:latest, mistral:7b-instruct
- **2 temperatures**, **2 replications**
- **Total: 2,112 prompts per model** (14,784 target; 14,785 completed)

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
| hoangquan456/qwen3-nothink:8b | Alibaba/Community | Standard | 8B | No | Phase II complete |
| phi4:latest | Microsoft (US) | Standard | 14B | No | Phase II complete |
| mistral:7b-instruct | Mistral AI (France/EU) | Standard | 7B | No | Phase II complete |

### Group Structure

- **Standard models**: llama3.1, gemma3n, qwen3-nothink, phi4, mistral — direct response generation
- **Reasoning models**: qwen3, deepseek-r1 — chain-of-thought with `<think>` tokens (stripped from analysis via `--strip-thinking`)
- **Architecture pair**: qwen3:8b (thinking) and hoangquan456/qwen3-nothink:8b share the same Qwen3 base; the community fine-tune natively suppresses CoT without runtime flags

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
│   ├── EU_Cyber_Phase_II_40_Scenarios_200_Prompts_Harmonised.csv   ← Phase I (100 prompts)
│   └── EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv  ← Phase II (528 prompts)
│
├── scripts/
│   ├── run_benchmark_v2_4.py          ← Runner v2.4 (Phase I)
│   ├── run_benchmark_v2_5.py          ← Runner v2.5 (Phase II, current)
│   ├── analyze_results.py             ← Per-run statistical analysis
│   ├── analyze_cve_patterns.py        ← Cross-model CVE fixation analysis
│   ├── analyze_confidence_patterns.py ← Per-model confidence pattern extraction
│   ├── compare_confidence_patterns.py ← Cross-model confidence pattern comparison
│   ├── finding4_crossphase.py         ← Phase I vs II cross-phase analysis
│   ├── convert_jsonl_to_flat.py       ← JSONL → flat CSV/JSON converter
│   └── live_dashboard.py              ← Real-time HTML dashboard
│
├── Phase_1/
│   ├── Results.md              ← Plain language results
│   └── Results_Data.md         ← Quantitative results with tables
│
├── Phase_2/
│   ├── Results.md              ← Global plain language results (all 7 models)
│   ├── CVE_Fixation_Analysis.md           ← Cross-model CVE fixation patterns
│   ├── Cross_Model_Confidence_Patterns.md ← Cross-model confidence comparison
│   ├── SA_Crisis_Model_Recommendation.md  ← Model selection for SA/crisis use
│   ├── llama31/
│   │   ├── Results.md, Results_Data.md
│   │   └── Confidence_Pattern_Analysis.md
│   ├── gemma3n/
│   │   ├── Results.md, Results_Data.md
│   │   └── Confidence_Pattern_Analysis.md
│   ├── qwen3-thinking/
│   │   ├── Results.md, Results_Data.md
│   │   ├── Confidence_Pattern_Analysis.md
│   │   ├── Cross_Phase_Comparison.md
│   │   └── Greedy_Decoding_Failure_Note.md
│   ├── deepseek-r1/
│   │   ├── Results.md, Results_Data.md
│   │   ├── Confidence_Pattern_Analysis.md
│   │   └── Cross_Phase_Comparison.md
│   ├── qwen3-nothink/
│   │   ├── Results.md, Results_Data.md
│   │   ├── Confidence_Pattern_Analysis.md
│   │   └── Thinking_vs_NoThink_Comparison.md
│   ├── phi4/
│   │   ├── Results.md, Results_Data.md
│   │   └── Confidence_Pattern_Analysis.md
│   └── mistral/
│       ├── Results.md, Results_Data.md
│       └── Confidence_Pattern_Analysis.md
│
└── results/
    ├── RUNS.md                 ← Run registry
    ├── Phase_1/
    │   └── *.jsonl             ← Raw data (Git LFS)
    └── Phase_2/
        ├── llama31/            ← llama31.jsonl
        ├── gemma3n/            ← gemma3n.jsonl
        ├── qwen3-thinking/     ← qwen3-thinking.jsonl
        ├── deepseek-r1/        ← deepseek-r1.jsonl
        ├── qwen3-nothink/      ← qwen3-nothink.jsonl
        ├── phi4/               ← phi4.jsonl
        ├── mistral/            ← mistral.jsonl
        ├── cross_model_confidence_patterns/  ← Cross-model confidence CSVs + report
        └── cve_patterns/       ← Cross-model CVE fixation CSVs + report
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

### Phase II — Global (14,785 records)

- **7 models from 6 providers** across 3 continents (US, China, EU), 5 actors, 48 scenarios
- **Certainty calibration is universal**: all 7 models reduce hedging from Suspected to Confirmed (d ranges from 0.78 to 3.35)
- **Phase 1's China bias disappears at scale**: 0/5 China-vs-rest tests significant for any model
- **No systematic geopolitical bias**: actor-uniform confidence rhetoric across all models
- **CVE fixation is model-specific**: deepseek-r1 (PwnKit 73%), llama3.1 (Log4Shell 49%), phi4 (Log4Shell 60%)
- **Chain-of-thought amplifies everything**: qwen3 thinking vs nothink pair shows CoT increases calibration, CVE rate, escalation dominance, and actor uniformity

Global results: [Phase 2 — Actor Symmetry Across 7 Local LLMs](Phase_2/Results.md)

### Phase II — llama3.1 (2,112 records)

- **Certainty calibration is robust and actor-uniform**: Cohen's d = 1.34-2.36 across all 5 actors
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

### Phase II — qwen3-nothink (2,112 records)

- **Community fine-tune of Qwen3 8B**: natively suppresses chain-of-thought, enabling a direct thinking vs no-think comparison on the same architecture
- **Strong certainty calibration**: hedging drops for all 5 actors (d = 1.35–2.69) — stronger than deepseek-r1's 1.24–1.99
- **Zero refusals**: 2,112/2,112 records completed — cleanest run in Phase 2
- **Balanced rhetorical profile**: E/H ratios near 1.0; no single confidence pattern category dominates
- **37% faster than thinking variant**: ~21.8s vs ~34.5s, quantifying the CoT latency tax
- **No China-protective framing**: 0/5 China-vs-rest tests significant
- **CVE rate halved by removing CoT**: 25.3% vs thinking variant's 56.5%

Detailed results: [qwen3-nothink Results](Phase_2/qwen3-nothink/Results.md) | [qwen3-nothink Data](Phase_2/qwen3-nothink/Results_Data.md)

### Phase II — phi4:latest (2,112 records)

- **US-origin instruct model at 14B**: largest model in Phase II by parameter count, nearly twice the 8B models
- **Strong certainty calibration**: hedging drops for all 5 actors (d = 1.07–2.53) — comparable to deepseek-r1's 1.24–1.99
- **Zero refusals at T=0.0**: 1/2,112 total (one Iran_Suspected at T=0.7) — lowest refusal rate in Phase II
- **Hedging-dominant rhetorical profile**: E/H ratios near 1.0, consistent with deepseek-r1 and llama3.1
- **Very low CVE mention rate**: 2.8% — second-lowest after gemma3n's 1.9%
- **CVE fixation on Log4Shell**: CVE-2021-44228 at 60.3% of CVE-containing records
- **Temperature-sensitive confidence labels**: near-uniform "High" at T=0.0 but diversified at T=0.7
- **No China-protective framing**: 0/5 China-vs-rest tests significant

Detailed results: [phi4 Results](Phase_2/phi4/Results.md) | [phi4 Data](Phase_2/phi4/Results_Data.md)

### Phase II — mistral:7b-instruct (2,112 records)

- **First EU-origin model**: Mistral AI (France), 7B parameters — the smallest model in Phase II
- **Strong certainty calibration**: hedging drops for all 5 actors (d = 0.78–1.91) with the lowest confirmed hedging levels of any model (0.62–1.02)
- **Zero refusals**: 0/2,112 at both temperatures
- **Escalation-dominant rhetorical profile**: E/H ratios above 1.0 (1.12–1.95) — dual-channel calibration (hedging reduction + escalation increase)
- **Best actor symmetry**: hedging range 0.40 (tightest of any model), 0/50 pairwise confidence pattern tests significant
- **No China-protective framing**: 0/5 China-vs-rest tests significant
- **Moderate CVE rate, no fixation**: 10.9%, top CVE at 28.7%, second-highest CVE diversity (H = 0.803)

Detailed results: [mistral Results](Phase_2/mistral/Results.md) | [mistral Data](Phase_2/mistral/Results_Data.md)

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

## Hugging Face Datasets

The prompts and full response corpus are published on Hugging Face for direct use with the `datasets` library:

- [eromang/eu-cyber-llm-benchmark-prompts](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-prompts) — 728 evaluation prompts (Phase I + Phase II)
- [eromang/eu-cyber-llm-benchmark-responses](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-responses) — 15,988 model responses across 7 models

```python
from datasets import load_dataset

prompts = load_dataset("eromang/eu-cyber-llm-benchmark-prompts", split="phase_2")
responses = load_dataset("eromang/eu-cyber-llm-benchmark-responses")
```

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
