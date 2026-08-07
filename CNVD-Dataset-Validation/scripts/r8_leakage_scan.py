#!/usr/bin/env python3
"""R8 — train/test leakage scan on CIRCL/Vulnerability-CNVD.

Reproduces the 2026-03-24 R8 measurement so the two runs are comparable:

    exact duplicate descriptions across train and test   1,587
    exact duplicate titles                                 359
    near-duplicates (first 50 chars)                     4,497
    ID overlaps                                              0
    test entries affected by a duplicate description     1,993  (R11, 15.6%)

Two counts are reported for descriptions because the original run reported
both and they answer different questions:

  * *distinct duplicated descriptions* — how many texts are shared (1,587)
  * *test entries affected*            — how many test rows carry such a
                                         text (1,993); this is the one that
                                         governs the accuracy correction

Prints the resolved dataset revision. A leakage number quoted without the
revision it was measured on cannot be checked by anyone else.
"""

import argparse
import json
import sys
import unicodedata

from datasets import load_dataset
from huggingface_hub import dataset_info

DATASET = "CIRCL/Vulnerability-CNVD"

# Python's \s does not match U+200B (category Cf), so .strip() leaves it in
# place and two visually identical descriptions hash differently. Strip
# explicitly rather than relying on whitespace semantics.
ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍﻿"), None)


def normalise(text):
    """Lower, NFKC-fold, drop zero-width chars, collapse whitespace.

    Returns None for a missing or empty value so that "absent" never
    collapses into a single shared empty-string key and reads as leakage.
    """
    if text is None:
        return None
    text = unicodedata.normalize("NFKC", str(text)).translate(ZERO_WIDTH)
    text = " ".join(text.split()).lower()
    return text or None


def scan(field, train_rows, test_rows, prefix=None):
    """Count cross-split exact (or prefix-truncated) collisions on `field`.

    Returns (distinct_shared_keys, affected_test_rows, unusable_rows).
    `unusable_rows` counts values that could not be keyed — reported so an
    empty result is never confused with an unmeasurable one.
    """
    train_keys, unusable = set(), 0
    for r in train_rows:
        k = normalise(r.get(field))
        if k is None:
            unusable += 1
            continue
        train_keys.add(k[:prefix] if prefix else k)

    shared, affected = set(), 0
    for r in test_rows:
        k = normalise(r.get(field))
        if k is None:
            unusable += 1
            continue
        k = k[:prefix] if prefix else k
        if k in train_keys:
            shared.add(k)
            affected += 1
    return len(shared), affected, unusable


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--revision", default=None,
                    help="Pin a dataset revision. Default: resolve and report current HEAD.")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    info = dataset_info(DATASET, revision=args.revision)
    revision = info.sha
    print(f"dataset : {DATASET}")
    print(f"revision: {revision}")
    print(f"modified: {info.last_modified}")

    ds = load_dataset(DATASET, revision=revision)
    if "train" not in ds or "test" not in ds:
        sys.exit(f"FATAL: expected train+test splits, got {list(ds)} — "
                 "cannot reproduce R8 against a different split layout")

    train, test = list(ds["train"]), list(ds["test"])
    print(f"\ntrain: {len(train):,}  test: {len(test):,}  total: {len(train)+len(test):,}")

    desc_shared, desc_affected, desc_unusable = scan("description", train, test)
    title_shared, title_affected, title_unusable = scan("title", train, test)
    near_shared, near_affected, _ = scan("description", train, test, prefix=50)

    train_ids = {r.get("id") for r in train}
    id_overlap = sum(1 for r in test if r.get("id") in train_ids)

    pct = 100.0 * desc_affected / len(test) if test else float("nan")
    near_pct = 100.0 * near_affected / len(test) if test else float("nan")

    print(f"""
exact duplicate descriptions (distinct texts) : {desc_shared:,}
test entries affected by one                  : {desc_affected:,}  ({pct:.1f}% of test)
exact duplicate titles (distinct)             : {title_shared:,}
near-duplicates, first 50 chars (distinct)    : {near_shared:,}
test entries affected by a near-duplicate     : {near_affected:,}  ({near_pct:.1f}% of test)
ID overlaps between splits                    : {id_overlap:,}
unkeyable description/title values            : {desc_unusable + title_unusable:,}""")

    if desc_unusable + title_unusable:
        print("  ^ these rows could not be keyed and are excluded from the counts above;"
              "\n    they are NOT evidence of absence of leakage.")

    result = {
        "dataset": DATASET, "revision": revision,
        "last_modified": str(info.last_modified),
        "train": len(train), "test": len(test),
        "exact_duplicate_descriptions_distinct": desc_shared,
        "test_entries_affected": desc_affected,
        "test_entries_affected_pct": round(pct, 2),
        "exact_duplicate_titles_distinct": title_shared,
        "near_duplicates_50char_distinct": near_shared,
        "near_duplicate_test_entries": near_affected,
        "id_overlaps": id_overlap,
        "unkeyable_values": desc_unusable + title_unusable,
        "baseline_2026_03_24": {
            "exact_duplicate_descriptions_distinct": 1587,
            "test_entries_affected": 1993,
            "test_entries_affected_pct": 15.6,
            "exact_duplicate_titles_distinct": 359,
            "near_duplicates_50char_distinct": 4497,
            "id_overlaps": 0,
            "train": 114805, "test": 12757,
        },
    }
    if args.json_out:
        with open(args.json_out, "w") as fh:
            json.dump(result, fh, indent=2, ensure_ascii=False)
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
