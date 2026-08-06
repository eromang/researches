#!/usr/bin/env python3
"""Can ~60 lines of rules replace the contextual ML model?

Lesson 18 in `docs/lessons-learned.md` states the project's own test: *before
training a model, ask whether the label assignment function is itself
deterministic from the inputs. If yes, skip the model.* It was applied to the
T-model (removed, replaced by 30 lines, identical results) and to the O-model
(removed in v5). It has never been applied to this one — Phase 2's contextual
severity — on the stated grounds that it "operates on free text where ML
genuinely adds value over rules".

D10 measured the opposite of what that justification predicts. The model scores
94.28 % where the rules leave the CVSS base severity alone, and 60.28 % where
they move it — weakest exactly where context is supposed to matter.

So this reimplements the label chain of `training/scripts/generate_contextual.py`
and scores it on the same frozen test split, reading **only `input_text`**, the
same string the model sees. Nothing is taken from the CSV's structured columns,
which would be a comparison the model could not win by construction.

The one thing the rule cannot recover
-------------------------------------
The generator's cross-border step is a coin flip:

    if cross_border and rng.random() < cross_border_escalation_prob:
        ctx_sev = escalate(ctx_sev, cross_border_esc)

The outcome of that flip is **not written into `input_text`**. A row saying
`cross_border: true` may or may not carry the +1, and nothing observable says
which. So the label is *not* a deterministic function of the model's input, and
there is an irreducible ceiling below 100 % for any predictor — rule or model.
Measuring that ceiling is half the point of this script: without it, the model's
60 % on escalated rows cannot be read as a learning failure rather than a
property of the data.

Three variants are therefore scored:

  ``cb_never``   assume the flip never fired
  ``cb_always``  assume it always fired
  ``oracle``     count correct if *either* assumption matches — not a usable
                 predictor, but an upper bound on what any predictor could reach

And one control: rows with ``cross_border: false`` carry no randomness at all,
so the rule must be **exactly right** on them. If it is not, the reimplementation
is wrong and every other number here is void. That check runs first and refuses
to report anything else if it fails.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "training" / "scripts"))

from generate_contextual import (  # noqa: E402  the generator's own helpers
    SEVERITY_INDEX,
    SEVERITY_LEVELS,
    cvss_to_base_severity,
    detect_triggers,
    escalate,
    impact_escalation,
    parse_escalation,
)

FIELD = re.compile(r"(\w+):\s*([^\s]+)")


def parse_input_text(text: str) -> dict:
    """Recover the generator's inputs from the string the model is given."""
    desc, _, tail = text.partition(" [SEP] ")
    f = dict(FIELD.findall(tail))
    out = {
        "description": desc,
        "sector": f.get("sector", ""),
        "cross_border": f.get("cross_border") == "true",
        "score": float(f.get("score", 0.0)),
        "entity_type": f.get("entity_type", ""),
        "cer": f.get("cer_critical_entity") == "true",
        "incident": f.get("entity_affected") == "true",
        "service_impact": f.get("service_impact", "none"),
        "data_impact": f.get("data_impact", "none"),
        "safety_impact": f.get("safety_impact", "none"),
        "affected_persons_count": int(f.get("affected_persons", 0)),
        "suspected_malicious": f.get("suspected_malicious") == "true",
        "impact_duration_hours": int(f.get("duration_hours", 0)),
    }
    return out


def derive(parsed: dict, rules: dict, *, cross_border_fired: bool) -> str:
    """The generator's chain, minus the randomness it does not record."""
    cfg = rules["rules"]["escalation_triggers"]
    bands = rules["rules"]["base_severity_from_cvss"]
    cb_esc = parse_escalation(rules["rules"]["cross_border_rule"]["escalation"])

    sector = parsed["sector"]
    sector_cfg = cfg.get(sector)
    sev = cvss_to_base_severity(parsed["score"], bands)

    if sector_cfg and sector != "non_nis2":
        if detect_triggers(parsed["description"]) & set(sector_cfg["triggers"]):
            sev = escalate(sev, parse_escalation(sector_cfg["escalation"]))

    if parsed["cross_border"] and cross_border_fired:
        sev = escalate(sev, cb_esc)

    if parsed["cer"] and sector != "non_nis2":
        sev = escalate(sev, 1)

    if parsed["incident"]:
        sev = impact_escalation(sev, {
            "service_impact": parsed["service_impact"],
            "data_impact": parsed["data_impact"],
            "financial_impact": "none",   # never contributes, see impact_escalation
            "safety_impact": parsed["safety_impact"],
            "affected_persons_count": parsed["affected_persons_count"],
            "suspected_malicious": parsed["suspected_malicious"],
            "impact_duration_hours": parsed["impact_duration_hours"],
        })
    return sev


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="evaluation/frozen/contextual_eval_v4split.csv")
    ap.add_argument("--rules", default="data/reference/sector_severity_rules.json")
    ap.add_argument("--model-predictions", default=None,
                    help="CSV from eval_contextual_vocabulary.py --dump-predictions, "
                         "to compare rule and model row by row")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    data_path = REPO / args.data
    rules_path = REPO / args.rules
    for p, what in ((data_path, "dataset"), (rules_path, "rules")):
        if not p.exists():
            print(f"ERROR: {what} not found at {p}", file=sys.stderr)
            print("Nothing was measured. This is not a score of zero.", file=sys.stderr)
            return 2

    rules = json.loads(rules_path.read_text())
    csv.field_size_limit(10**9)
    rows = list(csv.DictReader(data_path.open(newline="")))
    if not rows:
        print(f"ERROR: {data_path} is empty", file=sys.stderr)
        return 2

    parsed = [parse_input_text(r["input_text"]) for r in rows]
    truth = [int(r["label"]) for r in rows]

    # --- control: rows without cross_border carry no randomness at all -------
    dom = [i for i, p in enumerate(parsed) if not p["cross_border"]]
    dom_ok = sum(1 for i in dom
                 if SEVERITY_INDEX[derive(parsed[i], rules, cross_border_fired=False)]
                 == truth[i])
    print(f"Control — rows with cross_border: false ({len(dom)} of {len(rows)}), "
          f"where the chain is fully determined:")
    print(f"  rule reproduces the label on {dom_ok}/{len(dom)} = "
          f"{100 * dom_ok / len(dom):.2f}%")
    if dom_ok != len(dom):
        print("\nERROR: the reimplementation does not reproduce the generator on "
              "rows that contain no randomness. Every other figure below would "
              "be measuring a bug, so none is reported.", file=sys.stderr)
        miss = [i for i in dom
                if SEVERITY_INDEX[derive(parsed[i], rules, cross_border_fired=False)]
                != truth[i]][:3]
        for i in miss:
            got = derive(parsed[i], rules, cross_border_fired=False)
            print(f"  row {i}: expected {SEVERITY_LEVELS[truth[i]]}, rule says {got}",
                  file=sys.stderr)
            print(f"    {rows[i]['input_text'][:200]}", file=sys.stderr)
        return 1

    # --- the three variants --------------------------------------------------
    res = {}
    for name, fired in (("cb_never", False), ("cb_always", True)):
        ok = sum(1 for i, p in enumerate(parsed)
                 if SEVERITY_INDEX[derive(p, rules, cross_border_fired=fired)] == truth[i])
        res[name] = ok
    oracle = sum(1 for i, p in enumerate(parsed)
                 if truth[i] in {SEVERITY_INDEX[derive(p, rules, cross_border_fired=f)]
                                 for f in (False, True)})
    n = len(rows)
    print(f"\nRule on the frozen set ({n:,} rows):")
    for name in ("cb_never", "cb_always"):
        print(f"  {name:<10} {res[name]:>5,}/{n:,} = {100 * res[name] / n:.2f}%")
    print(f"  {'oracle':<10} {oracle:>5,}/{n:,} = {100 * oracle / n:.2f}%   "
          "<- upper bound for ANY predictor, rule or model")

    cb = sum(1 for p in parsed if p["cross_border"])
    print(f"\nThe unrecoverable part: {cb:,} rows ({100 * cb / n:.1f}%) say "
          "cross_border: true, and whether the +1 fired is not in the input.")
    print(f"  ceiling = {100 * oracle / n:.2f}%, so {100 - 100 * oracle / n:.2f}% "
          "of the set is unanswerable from what the model is shown.")

    payload = {"n": n, "control_rows": len(dom), "control_exact": dom_ok,
               "cb_never": res["cb_never"], "cb_always": res["cb_always"],
               "oracle": oracle, "cross_border_rows": cb}

    if args.model_predictions:
        mp = Path(args.model_predictions)
        if not mp.exists():
            print(f"\nERROR: {mp} not found — model comparison skipped, not zero.",
                  file=sys.stderr)
            return 2
        preds = list(csv.DictReader(mp.open(newline="")))
        if len(preds) != n:
            print(f"\nERROR: prediction file has {len(preds)} rows, dataset has {n}. "
                  "Refusing to align two different sets.", file=sys.stderr)
            return 2
        model_ok = sum(1 for i, r in enumerate(preds) if int(r["pred"]) == truth[i])
        best = max(res["cb_never"], res["cb_always"])
        print(f"\nHead to head on the same {n:,} rows:")
        print(f"  model            {model_ok:>5,} = {100 * model_ok / n:.2f}%")
        print(f"  rule (best fixed){best:>5,} = {100 * best / n:.2f}%")
        print(f"  rule (oracle)    {oracle:>5,} = {100 * oracle / n:.2f}%")
        payload["model"] = model_ok
        # where each is right, split by whether the rules moved the label
        esc = [i for i, r in enumerate(rows)
               if r["base_severity"] != r["contextual_severity"]]
        noesc = [i for i in range(n) if i not in set(esc)]
        for label, idx in (("escalated", esc), ("not escalated", noesc)):
            m = sum(1 for i in idx if int(preds[i]["pred"]) == truth[i])
            rl = sum(1 for i in idx
                     if SEVERITY_INDEX[derive(parsed[i], rules, cross_border_fired=False)]
                     == truth[i])
            o = sum(1 for i in idx
                    if truth[i] in {SEVERITY_INDEX[derive(parsed[i], rules, cross_border_fired=f)]
                                    for f in (False, True)})
            print(f"  {label:<14} n={len(idx):>5}  model {100 * m / len(idx):5.2f}%  "
                  f"rule {100 * rl / len(idx):5.2f}%  ceiling {100 * o / len(idx):5.2f}%")

    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2))
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
