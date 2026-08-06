#!/usr/bin/env python3
"""Evaluate a contextual model against the v4 test split, by entity type.

Written to test a claim that turned out to be false, and kept because it is what
disproved it. Backlog D8 asserted the deployed model was v2-era — trained on 8
entity types while `models/contextual.py` validates against 59, with zero
overlap. That rested on `git diff c51b3b6~1 HEAD -- data/models/contextual/`
returning empty. **`data/models/` is gitignored**, so the diff compared nothing;
an empty diff over untracked paths is the absence of evidence, not evidence of
identity.

What this script measured instead: the deployed model scores 81.71% on the v4
test split, reproducing `metrics.json` to four decimals on five metrics, and
80.67% on the subset whose `entity_type` does not exist in v2 at all. A model
blind to those tokens cannot do that. With the file dates (v4 03:48 → weights
05:31 → metrics 06:59, all 1 Apr) the conclusion is settled: **the deployed
model is v4-trained and has seen all 59 entity types.**

The real finding is narrower and survives: accuracy on the three entity types
the IR scope fix re-routed to this model (`ixp_operator`, `public_ecn_provider`,
`public_ecs_provider`) is 66.0% against 81.7% overall — Wilson 95% intervals
[52.2, 77.6] vs [80.6, 82.8], non-overlapping, so the gap is established even at
n=50. Use `--by-entity-type` to reproduce.

Reports "could not evaluate" distinctly from "scored badly": a missing model or
dataset exits non-zero rather than printing a zero.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

LABELS = ["Low", "Medium", "High", "Critical"]


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — usable at the small per-entity-type counts here,
    where the normal approximation is not."""
    if n == 0:
        raise ValueError("no observations; caller must report 'cannot conclude'")
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return centre - half, centre + half


def load_split(csv_path: Path, seed: int, test_size: float):
    """Reproduce the trainer's stratified test split exactly."""
    from sklearn.model_selection import train_test_split

    csv.field_size_limit(10**9)
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"ERROR: {csv_path} contains no records", file=sys.stderr)
        sys.exit(2)

    labels = [int(r["label"]) for r in rows]
    idx = list(range(len(rows)))
    _, test_idx = train_test_split(
        idx, test_size=test_size, random_state=seed, stratify=labels
    )
    return [rows[i] for i in test_idx]


def load_all(csv_path: Path):
    """Every row of *csv_path*, in file order.

    Used with --no-split when the file IS the evaluation set. Exits 2 on an
    empty file rather than reporting a score over zero rows.
    """
    csv.field_size_limit(10**9)
    with csv_path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print(f"ERROR: {csv_path} contains no records", file=sys.stderr)
        sys.exit(2)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="data/models/contextual")
    ap.add_argument("--data", default="training/data/contextual_training.csv")
    ap.add_argument("--config", default="training/configs/contextual_cls.json")
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--limit", type=int, default=None,
                    help="evaluate only the first N test rows (smoke runs)")
    ap.add_argument("--out", default=None, help="write metrics JSON here")
    ap.add_argument("--by-entity-type", action="store_true",
                    help="break accuracy down per entity_type, with Wilson 95% intervals")
    ap.add_argument("--no-split", action="store_true",
                    help="evaluate every row of --data instead of re-deriving a "
                         "test split from it. Required when --data is already a "
                         "frozen evaluation set: re-splitting it would compare "
                         "two models on different rows.")
    ap.add_argument("--dump-predictions", default=None, metavar="PATH",
                    help="write per-row predictions as CSV, so a slice (escalated "
                         "vs not, by sector) can be analysed without re-running "
                         "inference")
    ap.add_argument("--focus", nargs="*", default=None,
                    help="report these entity types as a group (default: the three IR re-routed)")
    args = ap.parse_args()

    model_dir = REPO / args.model
    data_path = REPO / args.data
    for p, what in ((model_dir, "model directory"), (data_path, "dataset")):
        if not p.exists():
            print(f"ERROR: {what} not found at {p}", file=sys.stderr)
            print("Cannot evaluate. This is not a score of zero.", file=sys.stderr)
            return 2

    cfg = json.loads((REPO / args.config).read_text())
    seed = cfg["model"].get("seed", 42)
    test_size = cfg["evaluation"].get("test_split", 0.15)

    if args.no_split:
        test = load_all(data_path)
        provenance = "frozen set, no re-split"
    else:
        test = load_split(data_path, seed, test_size)
        provenance = f"test split, seed {seed}"
    if args.limit:
        test = test[: args.limit]
    print(f"Model   : {args.model}")
    print(f"Dataset : {args.data}  ({len(test):,} rows, {provenance})")

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tok = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir), num_labels=4)
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    model.to(device).eval()

    max_len = cfg["model"].get("max_length", 256)
    preds: list[int] = []
    with torch.no_grad():
        for i in range(0, len(test), args.batch_size):
            chunk = test[i : i + args.batch_size]
            enc = tok([r["input_text"] for r in chunk], return_tensors="pt",
                      truncation=True, max_length=max_len, padding="max_length")
            enc = {k: v.to(device) for k, v in enc.items()}
            preds.extend(model(**enc).logits.argmax(-1).tolist())
            if (i // args.batch_size) % 20 == 0:
                print(f"  {min(i + args.batch_size, len(test)):>6,}/{len(test):,}", end="\r")

    truth = [int(r["label"]) for r in test]

    if args.dump_predictions:
        with open(args.dump_predictions, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["cve_id", "entity_type", "sector", "base_severity",
                        "contextual_severity", "cross_border", "entity_affected",
                        "cer_critical_entity", "label", "pred"])
            for r, p_ in zip(test, preds):
                w.writerow([r.get("cve_id", ""), r.get("entity_type", ""),
                            r.get("sector", ""), r.get("base_severity", ""),
                            r.get("contextual_severity", ""),
                            r.get("cross_border", ""), r.get("entity_affected", ""),
                            r.get("cer_critical_entity", ""), r["label"], p_])
        print(f"  predictions → {args.dump_predictions}")
    correct = sum(p == t for p, t in zip(preds, truth))
    acc = correct / len(truth)

    from sklearn.metrics import f1_score
    macro_f1 = f1_score(truth, preds, average="macro")
    per_class = f1_score(truth, preds, average=None, labels=[0, 1, 2, 3])

    print(f"\n  accuracy  {acc * 100:.2f}%   ({correct:,}/{len(truth):,})")
    print(f"  macro F1  {macro_f1:.4f}")
    for name, f1 in zip(LABELS, per_class):
        print(f"    {name:<9} F1 {f1:.4f}")

    # A model that has never seen the label vocabulary often collapses onto a
    # few classes. Report the spread — it distinguishes "wrong" from "inert".
    from collections import Counter
    dist = Counter(preds)
    print("  predicted class distribution: "
          + ", ".join(f"{LABELS[c]} {dist.get(c, 0)}" for c in range(4)))

    if args.by_entity_type:
        focus = args.focus or ["ixp_operator", "public_ecn_provider", "public_ecs_provider"]
        by: dict[str, list[int]] = {}
        for r, p_, t in zip(test, preds, truth):
            by.setdefault(r["entity_type"], [0, 0])
            by[r["entity_type"]][0] += int(p_ == t)
            by[r["entity_type"]][1] += 1

        print("\n  Per entity type (Wilson 95% interval; n is small per type):")
        for et in sorted(by, key=lambda e: by[e][0] / by[e][1]):
            k, n = by[et]
            lo, hi = _wilson(k, n)
            mark = "  <-- IR re-routed" if et in focus else ""
            print(f"    {et:<40} {k:>4}/{n:<4} {k / n * 100:6.2f}%  "
                  f"[{lo * 100:5.1f};{hi * 100:5.1f}]{mark}")

        fk = sum(by[e][0] for e in focus if e in by)
        fn = sum(by[e][1] for e in focus if e in by)
        if fn == 0:
            print("\n  No test rows for the focus group — cannot conclude, not 0%.")
        else:
            flo, fhi = _wilson(fk, fn)
            alo, ahi = _wilson(correct, len(truth))
            print(f"\n  focus group  {fk}/{fn} = {fk / fn * 100:.2f}%  "
                  f"[{flo * 100:.1f};{fhi * 100:.1f}]")
            print(f"  whole test   {correct}/{len(truth)} = {acc * 100:.2f}%  "
                  f"[{alo * 100:.1f};{ahi * 100:.1f}]")
            overlap = flo < ahi and alo < fhi
            print("  intervals overlap — gap NOT established" if overlap
                  else "  intervals disjoint — gap established at 95%")

    metrics = {
        "model": args.model,
        "dataset": args.data,
        "test_rows": len(truth),
        "accuracy": round(acc, 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_class_f1": {LABELS[i]: round(float(per_class[i]), 4) for i in range(4)},
        "predicted_distribution": {LABELS[c]: dist.get(c, 0) for c in range(4)},
    }
    if args.out:
        Path(args.out).write_text(json.dumps(metrics, indent=2))
        print(f"  metrics → {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
