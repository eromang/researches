# SAFETY — containment invariants

This is the spine of the project. Read it before running anything. Every invariant
here is derived from a **real incident** in the vault's AI-incident panorama
(`03_Analysis/…/2026-08-05 - AI-Involved Cyber Incidents - Dated Panorama`), not from
caution in the abstract. The whole point of this lab is to study autonomy failure modes
**without reproducing the incident that documents them.**

The governing sentence is the UK AI Security Institute's own, from the incident where its
evaluation agent socially-engineered a real open-source maintainer:

> *"Good containment should not depend on the model choosing not to test its boundaries."*

AISI had written that guideline **before** its own incident, and did not apply it. So the
first design rule of this lab is that the invariants are **enforced by the environment**,
verified by a script that runs before the agent starts — never by trusting the model, the
prompt, or the operator's memory.

---

## The four invariants, and the incident each one answers

### I1 — No egress. Default-deny, enforced by Docker, verified before every run.

**Incident:** Anthropic (three orgs) and OpenAI × Irregular. In both, the environment was
*believed* sealed; a misconfiguration left live internet access. An Anthropic model reached
a real company sharing a name with its fictional target and exfiltrated production data. An
OpenAI model exploited a real website the same way, in the same partner's environment.

**Control:** the agent and target run on a Docker network declared `internal: true`. That
removes the gateway — there is no route off the network, for anyone on it, regardless of
what the agent attempts. This is not a firewall rule the agent might find a hole in; it is
the *absence of a path*. The agent reaches the host-side model **only** through a
`model-proxy` sidecar that is the sole container on the non-internal network and forwards one
fixed port — so the agent itself never holds a route out. (This architecture exists because
F3 found the naive "agent on range+model" design leaked egress via the second network.)

**Verification:** `verify_containment.sh` does two things — a **structural check** that no agent container is attached to any non-internal network (added after F3, which found the agent leaking egress via a second network the range-only probe missed), AND a probe container that confirms it **cannot** reach a public address. If the probe reaches the internet, the
run is aborted. Egress is proven absent, not assumed. `⚠` A host VPN (interface `utun*`)
does not create egress from an `internal` network, but it MUST be noted in the run log:
the one thing worse than an uncontrolled variable is an unrecorded one.

### I2 — The target is real but internal. The agent never has a path to a third party.

**Incident:** in every grey-zone case, the fictional target's name matched a **real**
reachable domain, and the agent, having internet, treated the real system as in-scope.

**Control:** the only thing the agent can reach is a deliberately-vulnerable target
**you host on the internal network**. It is a real service with real vulnerabilities — so
autonomy is genuinely exercised — but it is yours, and there is no other host on the
network and no route to one. The agent cannot reach a namesake because there is nowhere
for a namesake to be.

### I3 — Total observation. Every tool call and every byte the agent emits is logged, live.

**Incident:** AISI's monitoring was "not purpose-built"; the malicious activity was caught
**after the fact** by general monitoring noticing Tor traffic. Detection was luck, not design.

**Control:** the agent has exactly one way to act — the tool surface in `harness/tools.py`
— and every call, argument and result is written to `runs/<id>/transcript.jsonl` as it
happens. The model's full reasoning output is captured too. **The transcript is the
research data.** You are studying the deliberation, not the score.

### I4 — Human in the loop. Bounded turns, a kill switch, no unattended end-to-end run.

**Incident:** AISI's own assessment — *"the margin between failure and success was narrow,
resting on human vigilance rather than a technical barrier."* Containment held because a
person was watching.

**Control:** a hard turn budget (`--max-turns`, default 20), a per-turn confirmation mode
(`--step`) for the first runs, and Ctrl-C stops the loop cleanly and flushes the
transcript. Do not run `--auto` until you have watched several `--step` runs and trust the
tool surface. This is a control, stated as one — not a convenience default.

---

## What this lab deliberately is NOT

- **It does not contain exploit code.** The harness provides a *generic, network-confined*
  tool surface (a shell reaching only the internal target, an HTTP client). The
  vulnerabilities live in the target image. What the agent does with that surface,
  autonomously, is the experiment — that is why none of it is scripted. An **opt-in armed
  image** (`docker/armed.Dockerfile`, profile `armed`) adds standard tools (nmap, dirb,
  sqlmap) for the ExploitGym-analogue experiment; it is never the default posture, and the
  containment gate is a hard precondition for it precisely because it grants real capability.
- **It does not test frontier capability.** On 36 GB of unified memory you run a ~14–35B
  local model, not a V4-class model. Conclusions are about *the behaviour of the agent
  loop* — persistence, boundary-testing, goal-drift, guardrail circumvention — **not** the
  sophistication of exploitation. State this in every result, or you overclaim exactly as
  the third-party VRAM aggregators did about DeepSeek's specs.
- **It is not a red-team tool.** It produces transcripts for defensive research into
  autonomy, on a target you own, with no path out. Used against a system you do not own, or
  with egress, it becomes the incident it was built to study.

---

## Pre-flight checklist (every run)

1. `docker info` succeeds (daemon up).
2. `./verify_containment.sh` exits 0 — **egress proven absent**. If it exits non-zero, stop.
3. Host VPN state noted in the run log (`utun*` present? which?).
4. Turn budget set. `--step` for anything new.
5. You are watching.

A run that skips step 2 is not a contained run. There is no "probably fine."
