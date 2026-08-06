#!/usr/bin/env python3
"""Rule vs model on human-curated scenarios — the non-circular test for D11.

Everything measured so far compares both arms against the *synthetic* corpus,
whose labels the rule reimplements. That comparison is circular by construction
and cannot decide whether the model should be retired.

This uses the CVE-Severity-Context predecessor dataset: 842 scenarios over 140
CVEs, each carrying an expert-assigned `contextual_severity` alongside its CVSS
base severity and a deployment description. It was authored by a different
project, before CyberScale existed, so neither arm has seen it.

Both arms are given **the same four inputs** — description, sector,
cross_border, CVSS score — because that is the production interface
`ContextualClassifier.predict()` exposes. Handing the rule anything more would
be a comparison the model could not win.

What the dataset says before either arm is run
----------------------------------------------
Of the 842 scenarios, the expert severity differs from the CVSS base severity in
535, and the direction is the finding:

    downward   378  (44.9 %)
    none       307  (36.5 %)
    upward     157  (18.6 %)

**CyberScale's rule chain can only escalate.** Sector triggers, cross-border,
CER status and impact all move severity up; nothing moves it down. So the single
most common expert judgement — context making a vulnerability *less* severe than
its CVSS score, a small cooperative below the significant-incident threshold —
is not expressible by the rule, and was absent from every row the model trained
on. The breakdown by direction is therefore the point of this script, not a
secondary cut.

MC dropout is disabled (`mc_passes=1`): backlog D6 established that leaving it on
makes benchmark figures irreproducible run to run.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "evaluation"))
sys.path.insert(0, str(REPO / "training" / "scripts"))

from benchmark_predecessor import load_scenarios  # noqa: E402
from derive_contextual_rule import derive  # noqa: E402

LEVELS = ["Low", "Medium", "High", "Critical"]


def rule_predict(rec: dict, rules: dict) -> str:
    """The rule, given exactly the four inputs the model's interface takes."""
    parsed = {
        "description": rec["description"],
        "sector": rec["sector"],
        "cross_border": bool(rec["cross_border"]),
        "score": float(rec["cvss_score"]),
        "entity_type": "",
        "cer": False,          # not present in the predecessor schema
        "incident": False,     # these are exposure scenarios, not incidents
        "service_impact": "none", "data_impact": "none", "safety_impact": "none",
        "affected_persons_count": 0, "suspected_malicious": False,
        "impact_duration_hours": 0,
    }
    # cross-border escalation: the deterministic reading, matching the variant
    # that scored best on the synthetic set
    return derive(parsed, rules, cross_border_fired=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenarios", required=True)
    ap.add_argument("--model", default="data/models/contextual")
    ap.add_argument("--rules", default="data/reference/sector_severity_rules.json")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    sdir = Path(args.scenarios)
    if not sdir.is_dir():
        print(f"ERROR: scenarios not found at {sdir}", file=sys.stderr)
        print("Nothing was measured. This is not a score of zero.", file=sys.stderr)
        return 2
    rules_path = REPO / args.rules
    if not rules_path.exists():
        print(f"ERROR: rules not found at {rules_path}", file=sys.stderr)
        return 2
    rules = json.loads(rules_path.read_text())

    records = load_scenarios(sdir)
    if not records:
        print("ERROR: no scenario parsed — refusing to report 0 %", file=sys.stderr)
        return 2

    # A missing CVSS score cannot be defaulted: the base severity is derived
    # from it, so inventing one would fabricate the very thing under test.
    # Excluded and counted, never silently coerced.
    no_score = [r for r in records if r.get("cvss_score") is None]
    records = [r for r in records if r.get("cvss_score") is not None]
    if no_score:
        print(f"{len(no_score)} scenario(s) excluded: no CVSS score, so no base "
              "severity to derive. Not defaulted.")
    if not records:
        print("ERROR: every scenario lacked a score — nothing measurable",
              file=sys.stderr)
        return 2
    print(f"{len(records)} scenarios usable\n")

    from cyberscale.models.contextual import ContextualClassifier
    model_dir = REPO / args.model
    if not model_dir.exists():
        print(f"ERROR: model not found at {model_dir}", file=sys.stderr)
        return 2
    clf = ContextualClassifier(model_path=model_dir, mc_passes=1)

    for i, rec in enumerate(records):
        rec["rule"] = rule_predict(rec, rules)
        # The interface no longer takes cross_border: it is expressed by
        # ms_affected being non-empty. (benchmark_predecessor.py still calls the
        # old signature and is therefore broken against current code — noted,
        # not fixed here.) Member states are fixed rather than random so the
        # run is reproducible; the model was trained on all 27 uniformly, so the
        # choice carries no signal.
        rec["model"] = clf.predict(
            description=rec["description"], sector=rec["sector"],
            ms_established="FR",
            ms_affected=["DE", "BE"] if rec["cross_border"] else None,
            score=rec["cvss_score"]).severity
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(records)}")

    truth = [r["ground_truth"] for r in records]
    n = len(records)
    rk = sum(1 for r in records if r["rule"] == r["ground_truth"])
    mk = sum(1 for r in records if r["model"] == r["ground_truth"])
    print(f"\nOverall on {n} human-curated scenarios:")
    print(f"  rule   {rk:>4}/{n} = {100 * rk / n:.2f}%")
    print(f"  model  {mk:>4}/{n} = {100 * mk / n:.2f}%")

    # the breakdown that matters
    by = collections.defaultdict(lambda: [0, 0, 0])
    for r in records:
        d = r.get("divergence_direction") or "none"
        by[d][0] += r["rule"] == r["ground_truth"]
        by[d][1] += r["model"] == r["ground_truth"]
        by[d][2] += 1
    print("\nBy how the expert moved severity away from the CVSS base:")
    print(f"  {'direction':<12}{'n':>6}{'rule':>10}{'model':>10}")
    for d in ("downward", "none", "upward"):
        if d not in by:
            continue
        rr, mm, nn = by[d]
        print(f"  {d:<12}{nn:>6}{100 * rr / nn:>9.2f}%{100 * mm / nn:>9.2f}%")

    payload = {"n": n, "rule_correct": rk, "model_correct": mk,
               "by_direction": {d: {"n": v[2], "rule": v[0], "model": v[1]}
                                for d, v in by.items()}}
    if args.out:
        Path(args.out).write_text(json.dumps(payload, indent=2))
        print(f"\nWrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
