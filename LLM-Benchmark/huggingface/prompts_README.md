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
pretty_name: EU Cyber Threat Landscape LLM Benchmark — Prompts
size_categories:
  - n<1K
---

# EU Cyber Threat Landscape LLM Benchmark — Prompts

A research-grade evaluation benchmark for measuring geopolitical bias in LLM-generated cyber threat landscape assessments.

## What this is

A set of structured prompts designed to test whether language models exhibit actor-asymmetric framing when generating strategic cyber threat assessments in EU contexts. Each prompt describes a cyber incident in a specific critical infrastructure sector, paired with an attribution condition that varies the suspected or confirmed threat actor.

The incident description and sector scope are held constant within each scenario. Only the attribution framing changes. This isolates the effect of geopolitical framing on model output.

## Splits

| Split | Scenarios | Conditions | Prompts | Actors |
|-------|-----------|------------|---------|--------|
| `phase_1` | 20 | 5 | 200 | Neutral, China, Russia (Suspected/Confirmed) |
| `phase_2` | 48 | 11 | 528 | Neutral, China, Russia, US, Iran, DPRK (Suspected/Confirmed) |

Phase 2 expands Phase 1 with 28 additional scenarios across 7 thematic blocks (EU internal, Chinese tech, multipolar, false-flag, non-state, democratic process, vendor-specific) and 6 additional conditions (US, Iran, DPRK attribution).

## Schema

| Field | Type | Description |
|-------|------|-------------|
| `prompt_id` | string | Unique identifier (e.g., `S21_China_Confirmed`) |
| `scenario_id` | string | Scenario group (e.g., `S21`) |
| `condition` | string | Attribution condition (e.g., `China_Confirmed`, `Neutral`) |
| `sector_focus` | string | Critical infrastructure sector (e.g., `Energy`, `Health`) |
| `prompt_text` | string | Full prompt text |

## How to use

```python
from datasets import load_dataset

ds = load_dataset("eromang/eu-cyber-llm-benchmark-prompts")

# Phase 2 prompts
for row in ds["phase_2"]:
    print(row["prompt_id"], row["condition"], row["sector_focus"])
```

### Run against a local model (Ollama)

```python
import requests
from datasets import load_dataset

ds = load_dataset("eromang/eu-cyber-llm-benchmark-prompts", split="phase_2")

for row in ds:
    resp = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3.1:8b-instruct-q4_K_M",
        "prompt": row["prompt_text"],
        "stream": False,
        "options": {"temperature": 0.0, "num_ctx": 4096},
    })
    print(row["prompt_id"], len(resp.json()["response"]))
```

## Controlled variables

- Incident description is constant within each scenario
- Sector scope is constant within each scenario
- Only the attribution framing varies between conditions
- Analytical instructions are identical across all prompts
- Operational detail is prohibited in prompt templates

## Sectors covered

Energy, Health, Transport, Finance, Digital Infrastructure, Water, Space, Defence, Telecommunications, Government, Maritime, Supply Chain, and others across EU critical infrastructure.

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

- [Response dataset](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-responses) — 15,988 model responses across 7 models
- [GitHub repository](https://github.com/eromang/researches/tree/main/LLM-Benchmark) — Full analysis scripts, per-model reports, methodology

## License

MIT
