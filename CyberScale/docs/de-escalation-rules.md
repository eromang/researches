# De-escalation rules for contextual severity

**Status:** derived and measured 2026-08-06, **not deployed**. See the closing
section for why they are not yet good enough to replace anything.

## Why they are needed

CyberScale's contextual chain only escalates: sector triggers, cross-border,
CER status and impact all raise severity, nothing lowers it. Against the
external validation set, the expert lowers severity below the CVSS base score in
**378 of 842 scenarios (44.9 %)** and raises it in only 157. The most common
contextual judgement in the data is therefore inexpressible by the rules, and
absent from every row the models trained on.

## The rules

Derived from the expert's own `threshold_matched` formulas, not authored from
first principles. Thresholds fixed on a 60 % derivation split and reported on
the untouched 40 %.

### R1 — Entity outside NIS2 scope → lower one level

An entity that falls under neither Annex I nor Annex II carries no notification
obligation, so a regulatory severity cannot stand at the technical one. This is
the directive's scope rather than a judgement call.

> Expert wording: *"N/A — no NIS2 obligation"*, *"N/A — no NIS2 obligation,
> personal use"*.

Available in production: yes, via `entity_type` (each canonical type carries its
annex) or `sector == non_nis2`.

### R2 — Affected system is not the essential service → lower one level

A desktop application, an office tool, a departmental or single-user install
cannot meet the significant-incident threshold whatever its CVSS score, because
the essential service is not what was hit.

> Expert wording: *"Below significant incident threshold — limited deployment on
> specialist workstations"*, *"— QA tool on limited workstations"*, *"— ancillary
> therapy tool"*, *"minimal business impact: single Manager deployment"*.

Signals, measured over the whole set — share of scenarios containing the term
that the expert down-graded: *home* 96.6 %, *personal* 91.1 %, *single* 89.2 %,
*person* 87.5 %, *department* 75.9 %, *workstations* 71.2 %, *office* 70.0 %.

**Available in production: NO.** These live in `deployment_context`, and
`ContextualClassifier.predict()` does not accept a deployment context. It takes
the CVE description, sector, member states, score, entity type, the CER flag and
incident impact fields.

### Cap

Two levels. The expert lowered by three in only 20 of 378 cases.

## Measured

Held-out split, 329 scenarios never used to fix a threshold:

| | accuracy |
|---|---|
| CVSS passthrough, no contextual rules at all | 34.04 % |
| **R1 only (deployable today)** | **41.95 %** |
| **R1 + R2 (needs an interface change)** | **48.63 %** |
| deployed model v4, whole set | 34.2–34.6 % |

On the 149 down-graded scenarios in the held-out split, where these rules exist
to help:

| | accuracy |
|---|---|
| R1 only | 24.83 % |
| R1 + R2 | **55.70 %** |

## What this says

**R1 alone already beats the deployed model** — 41.95 % against 34.2–34.6 % —
using nothing but the entity's regulatory scope, a fact the system already
knows.

**The deployment context is worth as much as everything else combined.** It adds
6.7 points overall and more than doubles accuracy on the cases it addresses, and
Phase 2 cannot receive it. That makes the largest remaining deficit an
**interface** problem: no retraining closes it, because the information never
arrives. A `deployment_context` free-text parameter on `predict()` is the
change that would.

**None of this is deployable as an answer.** 48.63 % on four classes, against a
25 % chance level, is an improvement and not a working system. What the exercise
establishes is where the ceiling comes from — not model capacity, but the
inputs Phase 2 is given and a rule chain that can only move one way.
