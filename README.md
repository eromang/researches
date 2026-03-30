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

### [CyberScale](CyberScale/)

**Multi-phase cyber severity assessment MCP server using fine-tuned ModernBERT classifiers.**

Context-aware vulnerability severity scoring that goes beyond CVSS base scores. Combines three fine-tuned ModernBERT classifiers (vulnerability scorer, contextual severity, incident T/O classifiers) with NIS2 sector rules, a ChromaDB vulnerability knowledge store, and the EU Cyber Blueprint dual-scale incident classification matrix, all exposed via the Model Context Protocol (MCP).

- **Phases:** Vulnerability scoring (0-10), contextual NIS2 severity, incident dual-scale classification (T1-T4 x O1-O4)
- **Key results:** 88.0% predecessor benchmark (+7.3pp vs baseline); T macro F1 95.4%, O macro F1 96.4%, matrix 96.2%
- **Assets:** MCP server (8 tools), training pipeline, evaluation benchmarks, reference data
- **Hugging Face:** [cyberscale-scorer-v1](https://huggingface.co/eromang/cyberscale-scorer-v1) | [cyberscale-contextual-v1](https://huggingface.co/eromang/cyberscale-contextual-v1) | [cyberscale-technical-v1](https://huggingface.co/eromang/cyberscale-technical-v1) | [cyberscale-operational-v1](https://huggingface.co/eromang/cyberscale-operational-v1)

---

## Tooling

All research uses Python 3.10+, runs on Apple Silicon, and is designed for full local reproducibility. No cloud APIs are required for core experiments. Claude Code (Anthropic) was used for code generation, analysis, and report drafting across all projects.

## License

[MIT](CyberScale/LICENSE)
