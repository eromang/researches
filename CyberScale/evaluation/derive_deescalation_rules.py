#!/usr/bin/env python3
"""De-escalation rules derived from the 378 expert down-gradings.

CyberScale's rule chain only escalates. The expert lowers severity below the
CVSS base score in 378 of 842 scenarios — more often than they raise it (157) —
so the single most common contextual judgement is inexpressible today, and was
absent from every row the models trained on.

These rules are **derived from the worked examples, not invented**. Each is
anchored in what the expert wrote in `threshold_matched`, whose recurring
formulas are "N/A — no NIS2 obligation", "Below significant incident threshold —
limited deployment on specialist workstations", "no cross-border service
disruption threshold met".

Derivation discipline
---------------------
Thresholds are fixed on a 60 % derivation split and reported on the untouched
40 %. Rules tuned and reported on the same rows would measure memorisation.
The split is stratified on the expert label and seeded.

The finding that constrains everything
--------------------------------------
The strongest predictors of de-escalation live in `deployment_context` — *home*
(96.6 % of scenarios containing it are down-graded), *personal* (91.1 %),
*single* (89.2 %), *workstations* (71.2 %). **`ContextualClassifier.predict()`
does not accept a deployment context.** It takes the CVE description, sector,
member states, score, entity type, the CER flag and incident impact fields. The
information the expert actually judges on never reaches Phase 2 at all.

So two rule sets are measured, and the gap between them is the point:

``production``  uses only what the interface accepts today
``with_context`` additionally reads the deployment context

If the second is much better, the deficit is an **interface** problem, not a
model or rule problem, and no amount of retraining will close it.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import random
import re
import sys

LEVELS = ["Low", "Medium", "High", "Critical"]
INDEX = {n: i for i, n in enumerate(LEVELS)}

# Wording taken from the expert's own threshold_matched formulas. Each marks a
# deployment that is not the entity's essential service: personal or home use,
# a single user, an office or desktop tool, a departmental or specialist
# workstation install.
NON_ESSENTIAL_TERMS = [
    "home", "personal", "single user", "single-user", "single ",
    "workstation", "desktop", "laptop", "office", "employee",
    "department", "individual", "consumer",
]


def load(scenarios_dir: str) -> list[dict]:
    rows = []
    for f in sorted(glob.glob(os.path.join(scenarios_dir, "*", "*.md"))):
        text = open(f, encoding="utf-8", errors="replace").read()
        m = re.match(r"---\n(.*?)\n---", text, re.S)
        if not m:
            continue
        d = dict(re.findall(r'^(\w+):\s*"?(.*?)"?\s*$', m.group(1), re.M))
        if d.get("contextual_severity") in INDEX and d.get("cvss_base_severity") in INDEX:
            rows.append(d)
    return rows


def de_escalation_steps(row: dict, *, use_context: bool) -> int:
    """How many levels the expert's reasoning would lower this scenario.

    R1 — out of NIS2 scope. No Annex I or II entity means no notification
         obligation, so the regulatory severity cannot stand at the technical
         one. This is the directive's scope, not a judgement call. Available in
         production as sector == non_nis2.

    R2 — the affected system is not the essential service. A desktop, an office
         tool, a single-user or personal install cannot meet the significant
         incident threshold whatever the CVSS score. Needs the deployment
         context, which production does NOT supply.

    Capped at 2: the expert lowered by 3 in only 20 of 378 cases.
    """
    steps = 0
    if (row.get("nis2_annex") or "none").lower() in ("none", "n/a", ""):
        steps += 1
    if use_context:
        ctx = (row.get("deployment_context") or "").lower()
        if any(t in ctx for t in NON_ESSENTIAL_TERMS):
            steps += 1
    return min(steps, 2)


def predict(row: dict, *, use_context: bool) -> str:
    base = INDEX[row["cvss_base_severity"]]
    return LEVELS[max(base - de_escalation_steps(row, use_context=use_context), 0)]


def score(rows: list[dict], *, use_context: bool) -> dict:
    ok = sum(1 for r in rows if predict(r, use_context=use_context)
             == r["contextual_severity"])
    base_ok = sum(1 for r in rows if r["cvss_base_severity"] == r["contextual_severity"])
    return {"n": len(rows), "correct": ok, "acc": ok / len(rows),
            "cvss_passthrough": base_ok / len(rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios",
                    default="evaluation/benchmarks/cve-severity-context/scenarios")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if not os.path.isdir(args.scenarios):
        print(f"ERROR: {args.scenarios} not found — nothing measured.", file=sys.stderr)
        return 2
    rows = load(args.scenarios)
    if not rows:
        print("ERROR: no scenario carried both severities — refusing to report 0 %",
              file=sys.stderr)
        return 2

    # stratified 60/40 on the expert label, seeded
    by = collections.defaultdict(list)
    for r in rows:
        by[r["contextual_severity"]].append(r)
    rng = random.Random(args.seed)
    derive, held = [], []
    for lvl, group in sorted(by.items()):
        g = group[:]
        rng.shuffle(g)
        cut = int(len(g) * 0.6)
        derive += g[:cut]
        held += g[cut:]
    print(f"{len(rows)} scenarios — derivation {len(derive)}, held out {len(held)}\n")

    print(f"{'rule set':<16}{'split':<12}{'accuracy':>10}{'vs CVSS passthrough':>22}")
    results = {}
    for name, ctx in (("production", False), ("with_context", True)):
        for split_name, split in (("derivation", derive), ("held-out", held)):
            s = score(split, use_context=ctx)
            results[f"{name}/{split_name}"] = s
            print(f"{name:<16}{split_name:<12}{100 * s['acc']:>9.2f}%"
                  f"{100 * s['cvss_passthrough']:>21.2f}%")

    prod = results["production/held-out"]["acc"]
    with_ctx = results["with_context/held-out"]["acc"]
    print(f"\nHeld-out gain from the deployment context alone: "
          f"{100 * (with_ctx - prod):+.2f} points")
    print("That field is not an input to ContextualClassifier.predict().")

    # what the down-graded subset alone looks like — the rules exist for these
    down = [r for r in held if r.get("divergence_direction") == "downward"]
    if down:
        for name, ctx in (("production", False), ("with_context", True)):
            s = score(down, use_context=ctx)
            print(f"  on the {len(down)} down-graded held-out scenarios, "
                  f"{name}: {100 * s['acc']:.2f}%")

    if args.out:
        with open(args.out, "w") as fh:
            json.dump(results, fh, indent=2)
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
