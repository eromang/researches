#!/usr/bin/env python3
"""R11 — accuracy with and without leaked test entries.

Reproduces the 2026-03-24 R11 measurement:

    leaked   (n=1,993, 15.6% of test)   87.6% accuracy
    unleaked (n=10,764, 84.4% of test)  76.6% accuracy
    headline 78.3% -> corrected 76.6%   (+1.7pp inflation)

"Leaked" means: the test entry's description also appears in the training
split, under a different CNVD ID. Definition identical to r8_leakage_scan.py
so the two runs partition the same rows.

> IMPORTANT SCOPE LIMIT
> This measures the *published checkpoint* against the *current dataset split*.
> The model card pins no dataset revision, so it is unknown whether the
> checkpoint was trained on this revision. If it was trained on an earlier
> corpus, the leaked/unleaked partition computed here is the split's property,
> not necessarily a record of what the model saw. Both figures are still
> measurements; only the causal reading depends on the unknown.
"""

import argparse
import json
import unicodedata

import torch
from datasets import load_dataset
from huggingface_hub import dataset_info
from transformers import AutoModelForSequenceClassification, AutoTokenizer

DATASET = "CIRCL/Vulnerability-CNVD"
MODEL = "CIRCL/vulnerability-severity-classification-chinese-macbert-base"
SEVERITY = {"低": "Low", "中": "Medium", "高": "High"}
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def normalise(text):
    if text is None:
        return None
    text = unicodedata.normalize("NFKC", str(text)).translate(ZERO_WIDTH)
    return " ".join(text.split()).lower() or None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--max-length", type=int, default=256)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    info = dataset_info(DATASET)
    revision = info.sha
    print(f"dataset : {DATASET}\nrevision: {revision}\nmodel   : {MODEL}")

    ds = load_dataset(DATASET, revision=revision)
    train, test = list(ds["train"]), list(ds["test"])

    train_desc = {normalise(r["description"]) for r in train}
    train_desc.discard(None)

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL).to(device).eval()
    id2label = model.config.id2label

    texts, golds, leaked_flags, unmappable = [], [], [], 0
    for r in test:
        gold = SEVERITY.get(r.get("severity"))
        key = normalise(r.get("description"))
        if gold is None or key is None:
            unmappable += 1
            continue
        texts.append(r["description"])
        golds.append(gold)
        leaked_flags.append(key in train_desc)

    n = len(texts)
    print(f"test rows: {len(test):,} | scored: {n:,} | unmappable (excluded): {unmappable:,}")
    if unmappable:
        print("  ^ excluded from every figure below; NOT counted as correct or incorrect.")

    preds = []
    with torch.inference_mode():
        for i in range(0, n, args.batch_size):
            batch = tok(texts[i:i + args.batch_size], truncation=True,
                        max_length=args.max_length, padding=True, return_tensors="pt").to(device)
            logits = model(**batch).logits
            preds.extend(id2label[int(j)] for j in logits.argmax(-1).cpu())
            if (i // args.batch_size) % 40 == 0:
                print(f"  {min(i + args.batch_size, n):,}/{n:,}", flush=True)

    def acc(idx):
        if not idx:
            return None, 0            # None means "could not measure", never 0.0
        ok = sum(preds[i] == golds[i] for i in idx)
        return ok / len(idx), len(idx)

    all_i = list(range(n))
    leaked_i = [i for i in all_i if leaked_flags[i]]
    unleaked_i = [i for i in all_i if not leaked_flags[i]]

    a_all, n_all = acc(all_i)
    a_lk, n_lk = acc(leaked_i)
    a_un, n_un = acc(unleaked_i)

    print(f"""
overall   : {a_all:.4f}  (n={n_all:,})
leaked    : {a_lk:.4f}  (n={n_lk:,}, {100*n_lk/n_all:.1f}% of scored)
unleaked  : {a_un:.4f}  (n={n_un:,}, {100*n_un/n_all:.1f}% of scored)
inflation : {100*(a_all - a_un):+.2f}pp on the headline
gap       : {100*(a_lk - a_un):+.2f}pp leaked vs unleaked""")

    per_class = {}
    print("\nper-class recall (unleaked):")
    for cls in ("Low", "Medium", "High"):
        idx = [i for i in unleaked_i if golds[i] == cls]
        r, cnt = acc(idx)
        per_class[cls] = {"recall": r, "support": cnt}
        print(f"  {cls:7} {r:.4f}  (n={cnt:,})" if r is not None
              else f"  {cls:7} not measurable (n=0)")

    result = {
        "dataset": DATASET, "revision": revision, "model": MODEL,
        "scored": n_all, "unmappable_excluded": unmappable,
        "accuracy_overall": a_all, "accuracy_leaked": a_lk, "accuracy_unleaked": a_un,
        "n_leaked": n_lk, "n_unleaked": n_un,
        "inflation_pp": 100 * (a_all - a_un),
        "per_class_unleaked": per_class,
        "baseline_2026_03_24": {
            "accuracy_overall": 0.7829, "accuracy_leaked": 0.876,
            "accuracy_unleaked": 0.766, "n_leaked": 1993, "n_unleaked": 10764,
            "inflation_pp": 1.7,
            "per_class_unleaked_recall": {"High": 0.736, "Low": 0.384},
        },
    }
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
