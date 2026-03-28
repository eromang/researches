# Researches

Independent cybersecurity research projects by Eric Romang. Each project is self-contained with its own methodology, data, and findings.

Models and datasets are published on [Hugging Face](https://huggingface.co/eromang).

---

## Projects

### [CNVD Dataset Validation](CNVD-Dataset-Validation/)

**Independent technical validation of CIRCL's CNVD dataset and MacBERT severity classification model.**

When CIRCL published a 127,562-entry Chinese vulnerability dataset and a fine-tuned severity classifier on Hugging Face, I ran a multi-track review to test the claims. The validation covers dataset overlap with NVD/CVE (81% map to existing CVEs), model accuracy on unleaked data (76.6% vs reported 78.3%), systematic bias detection (keyword dependency, negation blindness), and dataset provenance analysis (CNVD publication rates declining from 94% to 4% post-RMSV regulations).

- **Tracks:** NVD overlap (n=10,457), model quality (n=12,757), bias detection (adversarial + typical/atypical), provenance (sequence gap + API probing)
- **Key findings:** 15.6% train/test leakage via duplicated descriptions; Low severity recall at 38.4%; 19% genuinely China-domestic vulnerabilities
- **Assets:** validation methodology, per-track findings, reinforcement tests, raw data CSVs, reproducible scripts

### [EU Cyber Threat Landscape LLM Benchmark](LLM-Benchmark/)

**Research benchmark for evaluating geopolitical bias in locally deployed LLMs applied to cyber threat assessments.**

Tests whether local language models exhibit actor-asymmetric framing when generating EU-relevant cyber threat landscape assessments. Seven models from six providers across three continents (US, China, EU) are evaluated on escalation framing, hedging modulation, certainty calibration, and rhetorical amplification. All experiments run fully offline via Ollama.

- **Phase I:** 1,200 prompts across 20 EU critical infrastructure scenarios, 5 attribution conditions (Neutral, China/Russia x Suspected/Confirmed), 3 models
- **Phase II:** 14,785 prompts across 48 scenarios, 11 conditions (adding US, Iran, DPRK attribution), 7 models including reasoning (qwen3, deepseek-r1) and standard (llama3.1, gemma3n, phi4, mistral, qwen3-nothink)
- **Key findings:** certainty calibration is universal across all models; Phase I China bias disappears at scale; no systematic geopolitical bias detected; CVE fixation is model-specific (deepseek-r1 on PwnKit, llama3.1/phi4 on Log4Shell); chain-of-thought amplifies calibration, CVE rate, and actor uniformity
- **Assets:** full JSONL raw data (Git LFS), prompt CSVs, analysis scripts, per-model statistical reports, cross-model comparisons
- **Hugging Face:** [Prompts](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-prompts) | [Responses](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-responses)

---

## Tooling

All research uses Python 3.10+, runs on Apple Silicon, and is designed for full local reproducibility. No cloud APIs are required for any experiment. Claude Code (Anthropic) was used for code generation, analysis, and report drafting across both projects.

## License

[MIT](LLM-Benchmark/LICENSE)
