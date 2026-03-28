---
license: mit
task_categories:
  - text-generation
language:
  - en
tags:
  - cybersecurity
  - geopolitical-bias
  - benchmark
  - threat-assessment
  - eu
  - evaluation
  - model-comparison
pretty_name: EU Cyber Threat Landscape LLM Benchmark — Responses
size_categories:
  - 10K<n<100K
---

# EU Cyber Threat Landscape LLM Benchmark — Responses

15,988 LLM-generated cyber threat landscape assessments from 7 models across 3 continents, designed to measure geopolitical bias in attribution framing.

## What this is

The complete response corpus from running the [EU Cyber LLM Benchmark prompts](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-prompts) against 7 locally deployed models via Ollama. Each record contains the full model output, pre-extracted analytical sections, CVE mentions, refusal flags, and latency measurements.

All experiments ran fully offline on Apple Silicon. No cloud APIs were used.

## Corpus summary

| Phase | Records | Models | Scenarios | Conditions |
|-------|---------|--------|-----------|------------|
| `phase_1` | 1,200 | 3 | 20 | 5 |
| `phase_2` | 14,788 | 7 | 48 | 11 |
| **Total** | **15,988** | **7** | **48** | **11** |

### Model panel

| Model | Origin | Type | Parameters | Phase |
|-------|--------|------|------------|-------|
| llama3.1:8b-instruct-q4_K_M | Meta (US) | Standard | 8B | 1 + 2 |
| qwen3:8b | Alibaba (China) | Reasoning | 8B | 1 + 2 |
| deepseek-r1:8b | DeepSeek (China) | Reasoning | 8B | 1 + 2 |
| gemma3n:e4b | Google (US) | Standard | ~4B | 2 |
| hoangquan456/qwen3-nothink:8b | Alibaba/Community | Standard | 8B | 2 |
| phi4:latest | Microsoft (US) | Standard | 14B | 2 |
| mistral:7b-instruct | Mistral AI (France/EU) | Standard | 7B | 2 |

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `phase` | string | `phase_1` or `phase_2` |
| `run_id` | string | Unique run identifier |
| `timestamp_utc` | string | ISO 8601 timestamp |
| `model` | string | Ollama model name |
| `temperature` | float | 0.0 or 0.7 |
| `rep` | int | Replication number (1 or 2) |
| `prompt_id` | string | Prompt identifier |
| `pair_id` | string | Pair group for within-scenario comparison |
| `category` | string | Thematic block (Phase 2 only) |
| `sensitivity_level` | string | Attribution condition |
| `sector_focus` | string | Critical infrastructure sector |
| `prompt_text` | string | Full prompt text |
| `used_wrapper` | bool | Whether system wrapper was used |
| `ok` | bool | Whether generation completed |
| `error` | string | Error message if failed |
| `latency_ms` | int | Generation time in milliseconds |
| `output_text` | string | Full model response |
| `output_len_chars` | int | Response length in characters |
| `flag_refusal_or_avoidance` | string | `refusal_like`, `avoidance_like`, or empty |
| `flag_reason` | string | Reason for refusal/avoidance flag |
| `cves` | list[string] | CVE identifiers mentioned |
| `cve_count` | int | Number of CVEs mentioned |
| `executive_summary` | string | Extracted executive summary section |
| `threat_overview` | string | Extracted threat overview section |
| `key_threat_vectors` | string | Extracted threat vectors section |
| `impact_assessment` | string | Extracted impact assessment section |
| `early_warning_indicators` | string | Extracted early warning section |
| `defensive_priorities` | string | Extracted defensive priorities section |
| `confidence_assessment` | string | Extracted confidence assessment section |

## How to use

```python
from datasets import load_dataset

ds = load_dataset("eromang/eu-cyber-llm-benchmark-responses")

# Filter by model
llama = ds["train"].filter(lambda x: x["model"] == "llama3.1:8b-instruct-q4_K_M")
print(f"llama3.1 records: {len(llama)}")

# Compare hedging across attribution conditions for a model
from collections import Counter
conditions = Counter(r["sensitivity_level"] for r in llama)
print(conditions)
```

### Reproduce the analysis

```python
# CVE fixation by model
from collections import Counter
ds = load_dataset("eromang/eu-cyber-llm-benchmark-responses", split="train")

for model in set(ds["model"]):
    subset = ds.filter(lambda x: x["model"] == model)
    cve_records = subset.filter(lambda x: x["cve_count"] > 0)
    all_cves = [c for r in cve_records for c in r["cves"]]
    top = Counter(all_cves).most_common(3)
    print(f"{model}: {len(cve_records)}/{len(subset)} with CVEs, top: {top}")
```

## Key findings

- **Certainty calibration is universal**: all 7 models reduce hedging from Suspected to Confirmed attribution
- **No systematic geopolitical bias**: Phase 1 China-sensitivity disappears at scale; 0/5 China-vs-rest tests significant for any model
- **CVE fixation is model-specific**: deepseek-r1 fixates on PwnKit (73%), llama3.1 on Log4Shell (49%), phi4 on Log4Shell (60%)
- **Chain-of-thought amplifies everything**: qwen3 thinking vs nothink pair shows CoT increases calibration, CVE rate, and actor uniformity
- **Refusal patterns are model-specific**: llama3.1 has 17.7% US_Confirmed refusal at T=0.7; gemma3n and mistral have near-zero refusals

## Citation

```bibtex
@misc{romang2026eucyberbenchmark,
  author       = {Eric Romang},
  title        = {EU Cyber Threat Landscape LLM Benchmark: Geopolitical Bias in Local Language Models},
  year         = {2026},
  url          = {https://github.com/eromang/researches/tree/main/LLM-Benchmark},
  note         = {Research benchmark for evaluating actor-asymmetric framing in local LLMs}
}
```

## Related

- [Prompt dataset](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-prompts) — Reusable evaluation prompts
- [GitHub repository](https://github.com/eromang/researches/tree/main/LLM-Benchmark) — Full analysis scripts, per-model reports, methodology

## License

MIT
