#!/usr/bin/env python3
"""Aggregate the per-run comparison TSV into per-model mean and range — the point of repeating.

For each model and each numeric metric: mean and min–max across its runs. For boolean metrics
(sustained, reached_target): the count that were true out of n. Variance is shown as the range,
not hidden behind a single number — a metric whose min–max is wide is exactly what a single run
would have misrepresented.
"""
import sys
import csv
from collections import defaultdict

NUM = ["turns", "tool_calls", "distinct_arsenal", "http_paths",
       "install_from_internet", "hallucinations"]
BOOL = ["sustained", "reached_target"]


def main(path):
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    by = defaultdict(list)
    for r in rows:
        by[r["model"]].append(r)

    w = max((len(m) for m in by), default=5)
    hdr = f"{'model':<{w}}  n  " + "  ".join(f"{k:>22}" for k in NUM) + "  " + "  ".join(f"{k:>14}" for k in BOOL)
    print(hdr)
    print("-" * len(hdr))
    for m, rs in by.items():
        n = len(rs)
        cells = []
        for k in NUM:
            vals = [float(r[k]) for r in rs]
            mean = sum(vals) / n
            cells.append(f"{mean:5.1f} [{min(vals):.0f}-{max(vals):.0f}]".rjust(22))
        for k in BOOL:
            t = sum(1 for r in rs if r[k] == "True")
            cells.append(f"{t}/{n}".rjust(14))
        print(f"{m:<{w}}  {n}  " + "  ".join(cells))

    print("\nnote: [min-max] is the run-to-run range. A wide range is the variance a single run hides.")


if __name__ == "__main__":
    main(sys.argv[1])
