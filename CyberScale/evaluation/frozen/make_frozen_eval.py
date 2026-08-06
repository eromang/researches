#!/usr/bin/env python3
"""Freeze the v4 test split so two models can be compared on identical rows.

Why this exists
---------------
`eval_contextual_vocabulary.py` re-derives the test split from whatever CSV it
is given (`train_test_split`, stratified, seed 42, test_split 0.15). That is
correct while there is one corpus, and wrong the moment there are two: a
regenerated corpus yields a *different* split, so the new model would be scored
on rows the old model never saw — and, worse, rows the new model may have
trained on. The measured gain would then be partly leakage.

So the evaluation set is frozen **before** any regeneration, and both models are
scored on it with `--no-split`. The v5 corpus additionally has these rows
removed before training: 4,122 of the 4,800 reappeared in v5, which is the
contamination this guards against, measured rather than assumed.

The removal costs v5 ~4k training rows it would otherwise have had. That is the
conservative direction — it can only understate a genuine improvement, never
manufacture one.

Reproducing
-----------
The output is not tracked (2.9 MB, and `training/data/` is gitignored anyway).
It is deterministic from inputs that are themselves reproducible — the same
argument that justified deleting the v3 corpus in backlog D2:

    poetry run python training/scripts/generate_contextual.py \\
      --cves training/data/training_cves.csv \\
      --rules data/reference/sector_severity_rules.json \\
      --config training/configs/contextual_cls.json \\
      --output training/data/contextual_training.csv     # sha256 090bd96c…
    poetry run python evaluation/frozen/make_frozen_eval.py

Expected output sha256:
    b7b0eddea8a46b760da4d01a09237e83a1cdfcc4b5d0e52ffb44e3a8d1d1119d

A mismatch means the corpus or the split parameters moved; the before/after
comparison is void until it is explained. The script verifies it and exits
non-zero on disagreement rather than printing a warning nobody reads.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
EXPECTED_SHA256 = "b7b0eddea8a46b760da4d01a09237e83a1cdfcc4b5d0e52ffb44e3a8d1d1119d"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default="training/data/contextual_training.csv")
    ap.add_argument("--config", default="training/configs/contextual_cls.json")
    ap.add_argument("--out", default="evaluation/frozen/contextual_eval_v4split.csv")
    ap.add_argument("--expect", default=EXPECTED_SHA256,
                    help="expected sha256 of the output; '' disables the check")
    args = ap.parse_args()

    src = REPO / args.data
    if not src.exists():
        print(f"ERROR: corpus not found at {src}", file=sys.stderr)
        print("Regenerate it first — see this file's docstring. "
              "This is not an empty split.", file=sys.stderr)
        return 2

    cfg = json.loads((REPO / args.config).read_text())
    seed = cfg["model"].get("seed", 42)
    test_size = cfg["evaluation"].get("test_split", 0.15)

    from sklearn.model_selection import train_test_split

    csv.field_size_limit(10**9)
    with src.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        print(f"ERROR: {src} contains no records", file=sys.stderr)
        return 2

    labels = [int(r["label"]) for r in rows]
    _, test_idx = train_test_split(
        list(range(len(rows))), test_size=test_size, random_state=seed,
        stratify=labels)
    test = [rows[i] for i in test_idx]

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(test)

    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"frozen {len(test):,} rows -> {args.out}")
    print(f"sha256 {digest}")

    if args.expect and digest != args.expect:
        print(f"ERROR: expected {args.expect}", file=sys.stderr)
        print("The frozen evaluation set is not the one the published "
              "before/after figures were measured on. Do not compare against "
              "them until this is explained.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
