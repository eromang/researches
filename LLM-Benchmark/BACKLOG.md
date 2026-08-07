# Backlog — EU Cyber Threat Landscape LLM Benchmark

Living list. Updated at every working checkpoint, not at the end.

**Status vocabulary:** `OPEN` · `IN PROGRESS` · `BLOCKED` · `DONE` · `DROPPED` (with reason)
**Priority:** `P1` acts on something time-sensitive · `P2` substantive · `P3` depth/nice-to-have

Last updated: **2026-08-07** — written retroactively. Phase 1 and Phase 2 ran to completion
before this convention existed; this file reconstructs the trail from [README.md](README.md),
[Phase_2/Results.md](Phase_2/Results.md) and [results/RUNS.md](results/RUNS.md).

> [!warning] Retroactive, and therefore weaker than a live backlog
> Items that emerged mid-run and were resolved without reaching a committed file are **not
> recoverable** and are not represented here. What follows is the shape of the finished work,
> not a record of how it was found.

**Project status: PHASE 1 + PHASE 2 COMPLETE, then DORMANT since 2026-03-28.** No work in
4½ months. Both corpora are published on Hugging Face. The notes match that state — this is
a delivered project, not a stale one.

---

## Delivery

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| D1 | Phase 1 — controlled EU context | P1 | **DONE** | 20 scenarios × 5 conditions × 3 models × 2 temperatures × 2 reps = **1,200 prompts** |
| D2 | Phase 2 — context expansion | P1 | **DONE** | 48 scenarios × 11 conditions × 7 models. Target 14,784, **14,785 completed** — the surplus of 1 is unexplained in the record (see Q5) |
| D3 | Publish prompt corpus to Hugging Face | P2 | **DONE** | `eromang/eu-cyber-llm-benchmark-prompts` |
| D4 | Publish response corpus to Hugging Face | P2 | **DONE** | `eromang/eu-cyber-llm-benchmark-responses` — full outputs, extracted sections, CVE mentions, refusal flags, latency |
| D5 | Cross-link GitHub ↔ Hugging Face | P3 | **DONE** 2026-03-28 | Last commit on the project |
| D6 | Per-model confidence-pattern analysis | P2 | **DONE** | `analyze_confidence_patterns.py` over all 7 models |
| D7 | Cross-model comparison | P2 | **DONE** | `Phase_2/Cross_Model_Confidence_Patterns.md` |
| D8 | CVE citation analysis | P2 | **DONE** | `Phase_2/CVE_Fixation_Analysis.md` — fixation found in llama3.1 (Log4Shell), deepseek-r1 (PwnKit), phi4 (Log4Shell) |
| D9 | Operational recommendation for SA/crisis use | P2 | **DONE** | `Phase_2/SA_Crisis_Model_Recommendation.md` — qwen3-nothink |

---

## Findings, as published

Nine findings in `Phase_2/Results.md`. The two that carry the most weight for how this
project should be read:

| # | Finding | Note |
|---|---------|------|
| F2 | **Phase 1's China bias disappears at scale** | Phase 2 *overturned* a Phase 1 result. The single most important property of this project: the small design produced an artifact, and the larger one caught it. Any citation of Phase 1 alone is citing a superseded result |
| F5 | Chain-of-thought amplifies everything | Reasoning models amplify both escalation and hedging — not a bias direction, a gain increase |
| F6 | CVE citations are training artifacts, not analysis | CVE rate varies 1.9% (gemma3n) to 56.5% (qwen3-thinking) with fixation on specific CVEs. Cited CVEs must not be read as retrieval |

---

## Open

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| N1 | Larger models (70B+, cloud APIs) | P2 | OPEN | *Declared in `Results.md` §What comes next.* All 7 models are 7–14B. CVE accuracy and refusal behaviour are the two axes most likely to move. **Conflicts with the project's own offline-only design** — see Q1 |
| N2 | Multilingual prompts | P2 | OPEN | *Declared.* Every prompt is English. French, German, Mandarin could expose language-dependent bias invisible here. For an **EU** benchmark this is arguably the largest external-validity gap |
| N3 | Embedding-based taxonomy instead of regex | P2 | OPEN | *Declared.* mistral's near-zero detection on rhetorical categories is a **vocabulary-coverage gap in the instrument**, not necessarily a property of the model — so mistral's row in the scorecard is partly a measurement artifact and should be read as such |
| N4 | Re-run against current model versions | P3 | OPEN | *Emerged from dormancy.* The panel was pinned in March 2026. `phi4:latest` is a **moving tag** — it no longer denotes what it denoted then, so that column is not reproducible as written. The pinned-digest question applies to every Ollama tag used |

---

## Open questions

| # | Question | Status | Note |
|---|----------|--------|------|
| Q1 | Can N1 be done without breaking the offline guarantee? | OPEN | "All experiments run fully offline — no cloud APIs" is a stated property of the benchmark, and prompts describe EU critical-infrastructure incidents. Testing cloud APIs would send that corpus to third parties. **A design decision, not a scheduling one** |
| Q2 | Does F2 mean Phase 1 was wrong, or that scale changes the effect? | OPEN | Phase 2 has more scenarios, more conditions *and* more models — three changes at once, so the mechanism behind the disappearance is not isolated. The finding as stated ("disappears at scale") is the safe reading; *why* is unestablished |
| Q3 | Are the Ollama quantisations comparable across the panel? | OPEN | llama3.1 is `q4_K_M`; the others are unqualified tags. Comparing a Q4 llama against unquantised peers may confound origin with quantisation on any quality-sensitive metric |
| Q4 | Is `hoangquan456/qwen3-nothink:8b` a clean architecture pair with `qwen3:8b`? | OPEN | Treated as a controlled thinking/no-thinking pair. It is a **community fine-tune**, so it differs by more than CoT suppression. The pair carries F5, which makes this load-bearing |
| Q5 | Why 14,785 completions for a 14,784-prompt target? | OPEN | One extra record. Trivial in effect, but an unexplained off-by-one in a corpus published as a dataset is worth resolving or documenting |

---

## Decisions taken

| Date | Decision | Rationale |
|------|----------|-----------|
| — | Fully offline via Ollama, no cloud APIs | Reproducibility, and the prompt corpus describes EU critical-infrastructure incidents. Constrains N1 — see Q1 |
| — | Raw JSONL is the source of truth | Every derived table is regenerable from it; `results/RUNS.md` records the exact commands |
| — | Strip `<think>` tokens from reasoning models before analysis | `--strip-thinking`. Otherwise CoT length dominates every text metric |
| — | Hold incident text, sector and instructions constant; vary only attribution framing | This is what makes the actor-symmetry claim a controlled comparison rather than an observation |
| — | Prohibit operational detail in prompt templates | The benchmark studies framing, not exploitability |
| — | Publish both corpora under MIT with cross-links | Third parties can reproduce without re-running 14,785 generations |

---

## Dropped

| Item | Reason |
|------|--------|
| Phase 1's 3-model panel as the basis for conclusions | Superseded by Phase 2 (F2). Retained as a published record, **not** as a current result |
| Cloud-API models in the Phase 1/2 panels | Excluded by the offline design (Q1), not by oversight |
