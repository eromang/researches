# Researches

Independent cybersecurity research projects by Eric Romang. Each project is self-contained with its own methodology, data, and findings.

Models and datasets are published on [Hugging Face](https://huggingface.co/eromang).

---

## Status at a glance

*Last reviewed: 2026-08-07.*

| Project | State | Last activity | Deliverable |
|---------|-------|---------------|-------------|
| [Exploit-Hazard-Validation](Exploit-Hazard-Validation/) | Tracks complete, one item of work left | 2026-08-06 | Internal validation record — **not sent** to CIRCL (user decision) |
| [CyberScale](CyberScale/) | Active — Phase 2 assessed, four costed options open | 2026-08-06 | MCP server + 4 published models |
| [CNVD-Dataset-Validation](CNVD-Dataset-Validation/) | Complete, dormant | 2026-03-24 | Consolidated report; GitHub issue **drafted, unfiled** |
| [LLM-Benchmark](LLM-Benchmark/) | Phase 1 + 2 complete, dormant | 2026-03-28 | 2 published Hugging Face corpora |

Each project carries a `BACKLOG.md` with live task state, open questions, decisions taken, and dropped items with their reason. The two dormant projects' backlogs were written retroactively on 2026-08-07 and say so — items that emerged mid-run and never reached a committed file are not recoverable.

---

## Projects

### [Exploit Hazard Model — External Validation](Exploit-Hazard-Validation/)

**Independent external validation of the local exploit hazard model ([arXiv:2607.24618](https://arxiv.org/abs/2607.24618), Shaffer & Voicu) and of its first production implementation, [vulnerability-lookup#530](https://github.com/vulnerability-lookup/vulnerability-lookup/pull/530).**

The model turns EPSS into a defender's own daily exploit hazard rate. The authors' internal sensitivity analysis is thorough, so this project does not re-run it — it tests **external validity**: whether the calibrated `k = 0.605` is a property of exploitation timing or of CISA's federal curation, whether the hazard ranking beats the EPSS score it derives from, whether predicted event counts match observed ones, and how wrong the independence assumption is on real software.

- **Tracks:** B1 calibration transferability · B1c censoring and cure · B2 discriminative gain over EPSS · B3 rate calibration · B4 aggregation and conformance
- **Key findings:** `k` is unstable — it moves with catalog (0.52 curated / 0.72 observational), with snapshot date (0.684 → 0.576 over 19 months), and with the tail (dropping the longest 10% of TTEs moves it more than the entire replication gap). Ranking quality is **monotone decreasing in `k`**, so refitting `k` to your own catalogue degrades prioritisation, with nothing in the API signalling the trade. 99.5% of CVEs are never exploited rather than still waiting, which makes the mixture-cure model the right one and the naive censored fit an overcorrection.
- **Method note:** a pre-release verification pass audited 63 claims with 20 independent recomputations and **found two real errors**, both fixed before release. See [VERIFICATION.md](Exploit-Hazard-Validation/VERIFICATION.md).
- **Not testable with public data, and recorded as a finding rather than omitted:** the Bayesian control-effectiveness layer (§3.1) and absolute hazard for a real organisation — both need local telemetry and a real asset inventory.

### [CyberScale](CyberScale/)

**Multi-phase cyber severity assessment MCP server using fine-tuned ModernBERT classifiers.**

Context-aware vulnerability severity scoring that goes beyond CVSS base scores. Combines three fine-tuned ModernBERT classifiers (vulnerability scorer, contextual severity, incident T/O classifiers) with NIS2 sector rules, a ChromaDB vulnerability knowledge store, and the EU Cyber Blueprint dual-scale incident classification matrix, all exposed via the Model Context Protocol (MCP).

- **Phases:** Vulnerability scoring (0-10), contextual NIS2 severity, incident dual-scale classification (T1-T4 x O1-O4)
- **Key results:** 88.0% predecessor benchmark (+7.3pp vs baseline); T macro F1 95.4%, O macro F1 96.4%, matrix 96.2%
- **Open:** a Phase 2 assessment (2026-08-06) sets out four costed options. One measured result there is worth reading before extending the design: **the contextual apparatus is beaten by reporting the raw CVSS band** — 36.95% for raw CVSS against 34.2–34.6% for the deployed contextual model, on 842 expert-labelled scenarios over 140 CVEs authored by a separate project before CyberScale existed. That is the only ground truth it was never trained to reproduce.
- **Assets:** MCP server (8 tools), training pipeline, evaluation benchmarks, reference data
- **Hugging Face:** [cyberscale-scorer-v1](https://huggingface.co/eromang/cyberscale-scorer-v1) | [cyberscale-contextual-v1](https://huggingface.co/eromang/cyberscale-contextual-v1) | [cyberscale-technical-v1](https://huggingface.co/eromang/cyberscale-technical-v1) | [cyberscale-operational-v1](https://huggingface.co/eromang/cyberscale-operational-v1)

### [CNVD Dataset Validation](CNVD-Dataset-Validation/)

**Independent technical validation of CIRCL's CNVD dataset and MacBERT severity classification model.**

When CIRCL published a 127,562-entry Chinese vulnerability dataset and a fine-tuned severity classifier on Hugging Face, I ran a multi-track review to test the claims. The validation covers dataset overlap with NVD/CVE (81% map to existing CVEs), model accuracy on unleaked data (76.6% vs reported 78.3%), systematic bias detection (keyword dependency, negation blindness), and dataset provenance analysis (CNVD publication rates declining from 94% to 4% post-RMSV regulations).

- **Tracks:** NVD overlap (n=10,457), model quality (n=12,757), bias detection (adversarial + typical/atypical), provenance (sequence gap + API probing)
- **Key findings:** 15.6% train/test leakage via duplicated descriptions; Low severity recall at 38.4%; 19% genuinely China-domestic vulnerabilities
- **Method note:** the V3 verdict ("functionally equivalent to a lookup table") was **overstated and corrected in place** by the R1 reinforcement, which showed the model beats a keyword heuristic by 12.2pp. The original claim and its retraction both remain visible.
- **Assets:** validation methodology, per-track findings, reinforcement tests, raw data CSVs, reproducible scripts

### [EU Cyber Threat Landscape LLM Benchmark](LLM-Benchmark/)

**Research benchmark for evaluating geopolitical bias in locally deployed LLMs applied to cyber threat assessments.**

Tests whether local language models exhibit actor-asymmetric framing when generating EU-relevant cyber threat landscape assessments. Seven models from six providers across three continents (US, China, EU) are evaluated on escalation framing, hedging modulation, certainty calibration, and rhetorical amplification. All experiments run fully offline via Ollama.

- **Phase I:** 1,200 prompts across 20 EU critical infrastructure scenarios, 5 attribution conditions (Neutral, China/Russia x Suspected/Confirmed), 3 models
- **Phase II:** 14,785 prompts across 48 scenarios, 11 conditions (adding US, Iran, DPRK attribution), 7 models including reasoning (qwen3, deepseek-r1) and standard (llama3.1, gemma3n, phi4, mistral, qwen3-nothink)
- **Key findings:** certainty calibration is universal across all models; **Phase I's China bias disappears at scale** — Phase 2 overturned a Phase 1 result, so Phase 1 must not be cited alone; no systematic geopolitical bias detected; CVE fixation is model-specific (deepseek-r1 on PwnKit, llama3.1/phi4 on Log4Shell); chain-of-thought amplifies calibration, CVE rate, and actor uniformity
- **Assets:** full JSONL raw data (Git LFS), prompt CSVs, analysis scripts, per-model statistical reports, cross-model comparisons
- **Hugging Face:** [Prompts](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-prompts) | [Responses](https://huggingface.co/datasets/eromang/eu-cyber-llm-benchmark-responses)

---

## House style

These projects report to be read by the maintainer of the thing under test. That sets the conventions:

- Numbers carry their sample size and confidence interval; a result from n=36 is reported as inconclusive rather than as a result.
- **"Found nothing" and "could not look" are never written the same way.** Untestable questions are recorded as findings, not omitted.
- Corrections are made *in place and visibly* — an overstated verdict is annotated, not quietly deleted.
- Items that emerged mid-work are labelled as such, because they are usually the ones nobody planned.
- Dropped work keeps its reason. A dropped arm is often itself a finding.

## Tooling

All research uses Python 3.10+, runs on Apple Silicon, and is designed for full local reproducibility. No cloud APIs are required for core experiments. Claude Code (Anthropic) was used for code generation, analysis, and report drafting across all projects.

## License

[MIT](CyberScale/LICENSE)
