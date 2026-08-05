#!/usr/bin/env python3
"""Benchmark Phase 0 prioritisation against the exploit-hazard validation data.

The ranking in `cyberscale.prioritisation` implements the age term of the local
exploit hazard model. That term was validated independently in the sibling
project `Exploit-Hazard-Validation`, over four frozen snapshots and three
ground-truth sources. This re-runs CyberScale's own implementation against that
same data and checks it reproduces the result.

Two things are asserted, and they are different in kind:

  REPRODUCTION  CyberScale's sort key must reproduce the validation's AUC-ROC
                figures for k=0.550 to within floating-point tolerance. A
                mismatch means the implementations diverged, not that the model
                changed.

  BEHAVIOUR     The ranking must beat raw EPSS on AUC-ROC in all 11 cells, and
                must NOT show a reliable gain at top-100 or top-1000. The second
                half matters as much as the first: a tool claiming a gain there
                would be overselling what the evidence supports.

Exits non-zero on any failure. If the validation data is absent it exits 2 with
an explanation rather than passing quietly — an unrunnable benchmark is not a
green one.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VALIDATION = REPO.parent / "Exploit-Hazard-Validation" / "data"

sys.path.insert(0, str(REPO / "src"))
from cyberscale.prioritisation import hazard_sort_key  # noqa: E402

HORIZON = 90
MIN_CVE_YEAR = 2022
K = 0.550  # the value the validation tested; DEFAULT_K rounds to the same


def _require_data() -> None:
    missing = [f for f in ("b2_results.json", "cve_published.csv", "tte_multicatalog.csv")
               if not (VALIDATION / f).exists()]
    if missing or not list(VALIDATION.glob("epss-*.csv")):
        print("Cannot run: exploit-hazard validation data not found.")
        print(f"  looked in: {VALIDATION}")
        print(f"  missing:   {missing or 'epss-*.csv snapshots'}")
        print("\nRebuild it with, from the Exploit-Hazard-Validation project:")
        print("  python scripts/b1_build_tte.py")
        print("  python scripts/b2_build_cve_dates.py --keep-zip")
        print("  python scripts/b2_evaluate.py")
        sys.exit(2)


def main() -> int:
    _require_data()
    import numpy as np
    import pandas as pd
    from sklearn.metrics import roc_auc_score

    expected = {(c["source"], c["T"]): c for c in json.loads((VALIDATION / "b2_results.json").read_text())}
    pub = pd.read_csv(VALIDATION / "cve_published.csv", usecols=["cve", "published_date"])
    tte = pd.read_csv(VALIDATION / "tte_multicatalog.csv",
                      usecols=["cve", "catalog", "source", "exploited_date"])
    circl = tte[tte.catalog == "circl"][["cve", "source", "exploited_date"]].dropna()

    print(f"{'cell':<28}{'EPSS':>9}{'ranked':>9}{'delta':>9}{'expected':>10}  repro")
    rows, repro_fail, worse = [], [], []

    for (src, T), cell in sorted(expected.items()):
        snap = VALIDATION / f"epss-{T}.csv"
        if not snap.exists():
            continue
        ev = circl if src == "any" else circl[circl.source == src]
        end = (date.fromisoformat(T) + timedelta(days=HORIZON)).isoformat()

        df = pd.read_csv(snap).merge(pub, on="cve", how="inner")
        df = df[(df.published_date >= f"{MIN_CVE_YEAR}-01-01") & (df.published_date <= T)]
        first = ev.groupby("cve").exploited_date.min()
        df["fe"] = df.cve.map(first)
        df = df[~(df.fe.notna() & (df.fe <= T))]
        y = ((df.fe > T) & (df.fe <= end)).astype(int).to_numpy()
        if y.sum() < 5:
            continue

        p = df.epss.to_numpy()
        age = (pd.to_datetime(T) - pd.to_datetime(df.published_date)).dt.days.to_numpy()
        # CyberScale's own sort key, applied row by row
        scored = np.array([hazard_sort_key(float(a), int(b), K) for a, b in zip(p, age)])

        auc_epss = roc_auc_score(y, p)
        auc_rank = roc_auc_score(y, scored)
        want = cell["metrics"][f"hazard_wb_daily_k{K:.3f}"]["auc_roc"]
        ok = abs(auc_rank - want) < 1e-9
        if not ok:
            repro_fail.append((src, T, auc_rank, want))
        if auc_rank <= auc_epss:
            worse.append((src, T, auc_epss, auc_rank))
        rows.append((src, T, auc_epss, auc_rank, cell))
        print(f"{src + '@' + T:<28}{auc_epss:>9.4f}{auc_rank:>9.4f}"
              f"{auc_rank - auc_epss:>+9.4f}{want:>10.4f}  {'ok' if ok else 'MISMATCH'}")

    print()
    print(f"REPRODUCTION  {len(rows) - len(repro_fail)}/{len(rows)} cells match the validation exactly")
    for f in repro_fail:
        print(f"   MISMATCH {f[0]}@{f[1]}: got {f[2]:.6f}, validation recorded {f[3]:.6f}")

    print(f"BEHAVIOUR     AUC-ROC better than EPSS in {len(rows) - len(worse)}/{len(rows)} cells")
    for w in worse:
        print(f"   NOT BETTER {w[0]}@{w[1]}: EPSS {w[2]:.4f} vs ranked {w[3]:.4f}")

    # The other half of the contract: no reliable gain where capacity binds.
    better = {n: 0 for n in (100, 1000, 5000)}
    for src, T, _, _, cell in rows:
        for n in better:
            e = cell["metrics"]["epss"][f"coverage@{n}"]
            r = cell["metrics"][f"hazard_wb_daily_k{K:.3f}"][f"coverage@{n}"]
            better[n] += r > e
    print()
    print("Coverage@N — the ranking is expected to help deep and not shallow:")
    for n, b in better.items():
        verdict = "gain" if b >= len(rows) - 1 else ("wash" if b <= len(rows) * 0.6 else "mixed")
        print(f"   top {n:>5}: better in {b}/{len(rows)} cells  ({verdict})")
    shallow_overclaim = better[100] >= len(rows) - 1 or better[1000] >= len(rows) - 1
    if shallow_overclaim:
        print("   WARNING: a consistent shallow gain contradicts the validation; "
              "check the population construction")

    failed = bool(repro_fail or worse or shallow_overclaim)
    print("\n" + ("FAILED" if failed else "PASS"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
