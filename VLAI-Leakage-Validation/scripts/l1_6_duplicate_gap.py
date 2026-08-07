#!/usr/bin/env python3
"""L1-6 — does VLAI score duplicated descriptions better than unique ones?

The decisive test of whether the model's 90/10 split is grouped or random,
without needing CIRCL's seed (which is not published).

  random split  -> a row whose description repeats in the corpus is very
                   likely to have a twin on the training side, so the model
                   has seen its exact text. Predicts a LARGE accuracy gap.
  grouped split -> all rows sharing a description sit on the same side, so
                   duplication confers no advantage. Predicts NO gap.

Population: the 626,324 rows carrying at least one CVSS score, i.e. the rows
that can be labelled at all — established in findings/L0.

> The gap, not the absolute accuracy, is the result. Absolute accuracy here is
> inflated by construction (most of this population is the model's own training
> data) and must not be compared with the card's 0.8186. A label-derivation
> error would shift both arms together, so the gap is robust to it in a way the
> absolute number is not.
"""

import argparse
import json
import unicodedata
from collections import Counter

import torch
from datasets import load_dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DATASET = "CIRCL/vulnerability-scores"
DATASET_REV = "5c017b72fba32aa8c700b512914935c2a385fd2c"
MODEL = "CIRCL/vulnerability-severity-classification-roberta-base"
MODEL_REV = "accca22ddbc2064d7975b7894ca65bfdbfe7ca0d"

# Newest first. Recorded explicitly because it is an assumption: the card does
# not state which CVSS version is preferred when several are present.
CVSS_ORDER = ["cvss_v4_0", "cvss_v3_1", "cvss_v3_0", "cvss_v2_0"]
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def norm(t):
    if t is None:
        return None
    return " ".join(unicodedata.normalize("NFKC", str(t)).translate(ZERO_WIDTH).split()).lower() or None


def bucket(score):
    """CVSS v3.x qualitative bands. Applied to every version, including v2.

    v2 officially has no Critical band; applying v3 bands to a v2 score is a
    choice, recorded in the findings rather than hidden here.
    """
    if score is None:
        return None
    s = float(score)
    if s < 0.1:
        return None          # 'None' severity is not one of the four classes
    if s < 4.0:
        return "Low"
    if s < 7.0:
        return "Medium"
    if s < 9.0:
        return "High"
    return "Critical"


def label_of(row):
    for col in CVSS_ORDER:
        v = row.get(col)
        if v is not None:
            b = bucket(v)
            if b:
                return b, col
    return None, None


def wilson(k, n):
    """95% Wilson interval — a proportion needs its interval, not a point."""
    if n == 0:
        return None
    p, z = k / n, 1.959964
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - h) / d, (c + h) / d)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=128)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--limit", type=int, default=None, help="debug only")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    print(f"dataset {DATASET}@{DATASET_REV[:8]}\nmodel   {MODEL}@{MODEL_REV[:8]}", flush=True)
    ds = load_dataset(DATASET, revision=DATASET_REV)
    rows = [r for s in ds for r in ds[s]]

    counts = Counter(k for k in (norm(r.get("description")) for r in rows) if k)

    texts, golds, dup, srcver, skipped = [], [], [], [], 0
    for r in rows:
        key = norm(r.get("description"))
        gold, col = label_of(r)
        if key is None or gold is None:
            skipped += 1
            continue
        texts.append(r["description"])
        golds.append(gold)
        dup.append(counts[key] > 1)
        srcver.append(col)
    if args.limit:
        texts, golds, dup, srcver = (x[:args.limit] for x in (texts, golds, dup, srcver))

    n = len(texts)
    print(f"corpus {len(rows):,} | scored {n:,} | skipped (no CVSS or no text) {skipped:,}")
    print(f"label source: {dict(Counter(srcver))}")
    print(f"gold distribution: {dict(Counter(golds))}")
    print(f"duplicated-description rows: {sum(dup):,} ({100*sum(dup)/n:.1f}%)", flush=True)

    tok = AutoTokenizer.from_pretrained(MODEL, revision=MODEL_REV)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, revision=MODEL_REV)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = model.to(device).eval()
    id2label = model.config.id2label

    preds = []
    with torch.inference_mode():
        for i in range(0, n, args.batch_size):
            b = tok(texts[i:i + args.batch_size], truncation=True, max_length=args.max_length,
                    padding=True, return_tensors="pt").to(device)
            preds.extend(id2label[int(j)] for j in model(**b).logits.argmax(-1).cpu())
            if (i // args.batch_size) % 200 == 0:
                print(f"  {min(i+args.batch_size, n):,}/{n:,}", flush=True)

    def arm(mask):
        idx = [i for i in range(n) if mask(i)]
        if not idx:
            return {"n": 0, "accuracy": None, "ci95": None}   # None, never 0.0
        k = sum(preds[i] == golds[i] for i in idx)
        lo, hi = wilson(k, len(idx))
        return {"n": len(idx), "correct": k, "accuracy": k / len(idx), "ci95": [lo, hi]}

    overall = arm(lambda i: True)
    a_dup = arm(lambda i: dup[i])
    a_uni = arm(lambda i: not dup[i])
    gap = a_dup["accuracy"] - a_uni["accuracy"]

    print(f"""
=== L1-6 RESULT ===
overall            : {overall['accuracy']:.4f}  (n={overall['n']:,})
duplicated desc.   : {a_dup['accuracy']:.4f}  [{a_dup['ci95'][0]:.4f}, {a_dup['ci95'][1]:.4f}]  (n={a_dup['n']:,})
unique desc.       : {a_uni['accuracy']:.4f}  [{a_uni['ci95'][0]:.4f}, {a_uni['ci95'][1]:.4f}]  (n={a_uni['n']:,})
GAP (dup - unique) : {100*gap:+.2f} pp

interpretation: a large positive gap indicates a RANDOM split (duplicates
leak across it); a gap near zero indicates a GROUPED split.""")

    per_class = {}
    for cls in ("Low", "Medium", "High", "Critical"):
        d = arm(lambda i, c=cls: dup[i] and golds[i] == c)
        u = arm(lambda i, c=cls: (not dup[i]) and golds[i] == c)
        per_class[cls] = {"dup": d, "unique": u}
        if d["accuracy"] is not None and u["accuracy"] is not None:
            print(f"  {cls:9} dup {d['accuracy']:.4f} (n={d['n']:,})  "
                  f"uniq {u['accuracy']:.4f} (n={u['n']:,})  gap {100*(d['accuracy']-u['accuracy']):+.2f}pp")

    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump({"dataset": DATASET, "dataset_revision": DATASET_REV,
                       "model": MODEL, "model_revision": MODEL_REV,
                       "scored": n, "skipped": skipped,
                       "cvss_preference_order": CVSS_ORDER,
                       "overall": overall, "duplicated": a_dup, "unique": a_uni,
                       "gap_pp": 100 * gap, "per_class": per_class}, fh, indent=2)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
