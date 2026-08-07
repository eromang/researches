# Backlog — AI-Agent-Autonomy-Lab

Living list. Updated at every working checkpoint, not at the end.

**Status vocabulary:** `OPEN` · `IN PROGRESS` · `BLOCKED` · `DONE` · `DROPPED` (with reason)
**Priority:** `P1` acts on something time-sensitive · `P2` substantive · `P3` depth/nice-to-have

Last updated: **2026-08-07** — v0.1 scaffold complete. Nothing run against a live model yet.

> [!note] Live from checkpoint zero
> Like the VLAI backlog and unlike the retroactive ones, this file starts with the project.
> The interesting findings will be behaviours that emerge mid-run — add them the moment
> they appear, labelled *emerged during work*.

---

## Safety scaffold (the spine)

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| S1 | Four containment invariants tied to real incidents | P1 | **DONE** | `SAFETY.md`. I1 no-egress, I2 internal target, I3 total logging, I4 human-in-loop |
| S2 | Egress pre-flight gate that MEASURES, not trusts | P1 | **DONE** | `verify_containment.sh` — probe container on the range, aborts on any reachability |
| S3 | `internal: true` range network | P1 | **DONE** | `docker/compose.yml` — no gateway = no route out |
| S4 | Model/target path split into two networks | P1 | **DONE** | reasoning path and target path are physically distinct, so they cannot be confused as at Irregular |
| S5 | Harness refuses to run with no `--step`/`--auto` | P1 | **DONE** | no unattended default |
| S6 | Live-test the containment gate, both directions | P1 | **DONE** 2026-08-07 | Proven with Docker up. **Pass:** `verify_containment.sh` on the `internal:true` range → EXIT 0, probe could reach neither 1.1.1.1 nor 8.8.8.8. **Fail-detection:** same probe on a throwaway `bridge` (non-internal) network REACHED 1.1.1.1 — the gate's detection logic fires on real egress, it does not merely rubber-stamp. A gate only shown to pass is not a gate. Note: the probe image (`alpine`) pulls host-side once if absent; the pull is not egress from the range |

---

## Harness

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| H1 | observe→reason→act loop, live JSONL transcript | P1 | **DONE** | `harness/agent_loop.py`, stdlib only |
| H2 | Confined tool surface (http/shell/note) | P1 | **DONE** | `harness/tools.py`; failures surfaced, never swallowed |
| H3 | OpenAI-compatible backend (MLX / ollama) | P1 | **DONE** | `MODEL_BASE_URL`; both speak /chat/completions |
| H4 | Agent Dockerfile, no exploit tooling | P1 | **DONE** | `docker/agent.Dockerfile` — curl + shell only |
| H5 | **First `--step` run against Juice Shop with MLX serving** | P1 | **OPEN** | Needs `mlx_lm.server` reinstalled (currently absent per LOCAL_MODELS_INVENTORY) or ollama with a model pulled. The first real transcript |
| H6 | Tool-call protocol robustness | P2 | OPEN | Current parser is a fenced ```action``` block. Measure how often the 14–35B model emits malformed actions; a high rate would confound "agent can't act" with "harness too strict" |

---

## Experiments (once H5 lands)

| # | Item | Prio | Status | Note |
|---|------|------|--------|------|
| E1 | Baseline: single model, one objective, `--step` | P1 | OPEN | Establish that the loop closes and the transcript is legible before measuring anything |
| E2 | **Split-model reproduction** — reasoning on the local model, execution via the harness | P2 | OPEN | The §3.7 architecture, contained. The point the panorama makes: no provider guardrail sees a reasoning step performed on another vendor's weights. Reproducing it in isolation measures exactly that blind spot |
| E3 | Guardrail-circumvention behaviour | P2 | OPEN | Does the model refuse, comply, or rationalise? The CMU corrigibility result (panorama §5.5) says instruction alone will not hold — measure it on THIS model |
| E4 | Goal-drift / boundary-testing | P2 | OPEN | Give an in-scope objective; measure whether the agent stays in scope. The panorama's grey zone is entirely about agents that did not |
| E5 | Turn-budget sensitivity | P3 | OPEN | Does behaviour change as the budget grows? OpenAI's models "spent substantial inference compute" finding a way out — is there a compute threshold where drift appears? |

---

## Open questions

| # | Question | Status | Note |
|---|----------|--------|------|
| Q1 | Does an `internal: true` Docker network truly have zero egress on macOS/Docker Desktop's VM? | OPEN | Believed yes; **S6 must prove it by measurement**, not assume it. The whole lab rests on this |
| Q2 | Does the host VPN (`utun8`, seen 2026-08-07) create any path from the range? | OPEN | Reasoned no — an internal network has no gateway to reach the VPN either — but recorded as a variable, and the gate notes VPN state each run |
| Q3 | Is a 14–35B local model capable enough to exercise the failure modes at all? | OPEN | If it cannot close the loop, the negative result is itself informative about the capability floor for autonomous misbehaviour |
| Q4 | Can `mlx_lm.server` serve a tool-use-shaped chat completion well enough, or is ollama the better backend? | OPEN | Both expose the API; quality of instruction-following on the action protocol may differ |

---

## Decisions taken

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-07 | No egress is the ONE load-bearing control; everything else follows | Every grey-zone incident in the panorama had the same proximate cause — a "sealed" environment with live internet |
| 2026-08-07 | The gate MEASURES egress, it does not trust the compose flag | AISI had the guideline written and did not apply it; a control you trust but never test is the failure mode itself |
| 2026-08-07 | No exploit tooling in the agent image; vulns live in the target | The research object is the agent's autonomy, not a pre-loaded capability. What it tries to fetch and cannot is itself data |
| 2026-08-07 | stdlib-only harness | Auditable, and the harness has no supply-chain surface of its own |
| 2026-08-07 | No unattended default; `--step` or explicit `--auto` | AISI: containment held on human vigilance. Make that a control, not a hope |
| 2026-08-07 | Findings state the capability ceiling explicitly | Or they overclaim exactly as the third-party VRAM aggregators did about DeepSeek's specs |

---

## Dropped

*(nothing yet)*
