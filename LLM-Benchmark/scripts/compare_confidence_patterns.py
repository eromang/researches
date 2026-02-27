#!/usr/bin/env python3
"""
compare_confidence_patterns.py

Cross-model comparison of confidence assessment rhetorical patterns.
Reads pattern_rates_by_actor_level.csv from each model's output directory
and produces comparison tables and a summary report.

Usage:
  python3 scripts/compare_confidence_patterns.py \
    --models qwen3=results/Phase_2/qwen3-thinking/confidence_patterns \
             llama31=results/Phase_2/llama31/confidence_patterns \
             gemma3n=results/Phase_2/gemma3n/confidence_patterns \
    --outdir results/Phase_2/cross_model_confidence_patterns
"""

from __future__ import annotations

import argparse
import csv
import math
import os
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Statistical helpers
# ---------------------------------------------------------------------------

def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def prop_z_test(p1: float, n1: int, p2: float, n2: int) -> Tuple[Optional[float], Optional[float]]:
    """Two-proportion z-test."""
    if n1 == 0 or n2 == 0:
        return None, None
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_pool == 0 or p_pool == 1:
        return None, None
    se = math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    if se == 0:
        return None, None
    z = (p1 - p2) / se
    p = 2.0 * (1.0 - normal_cdf(abs(z)))
    return z, p


def cohen_h(p1: float, p2: float) -> float:
    """Cohen's h for two proportions."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


CATEGORIES = [
    "evidence_qualification",
    "misattribution_caveats",
    "corroboration_demands",
    "contextual_support",
    "procedural_hedges",
]

CATEGORY_SHORT = {
    "evidence_qualification": "Evid. qual.",
    "misattribution_caveats": "Misattr.",
    "corroboration_demands": "Corroboration",
    "contextual_support": "Contextual",
    "procedural_hedges": "Procedural",
}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_actor_rates(dirpath: str) -> List[dict]:
    """Load pattern_rates_by_actor_level.csv."""
    path = os.path.join(dirpath, "pattern_rates_by_actor_level.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_pairwise(dirpath: str) -> List[dict]:
    """Load pattern_pairwise_tests.csv."""
    path = os.path.join(dirpath, "pattern_pairwise_tests.csv")
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def load_ngrams(dirpath: str) -> List[dict]:
    """Load pattern_ngram_discovery.csv."""
    path = os.path.join(dirpath, "pattern_ngram_discovery.csv")
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# Cross-model rate table
# ---------------------------------------------------------------------------

def build_cross_model_rates(models: Dict[str, str]) -> List[dict]:
    """Build a combined rate table: model x category x actor x level."""
    rows = []
    for model_name, dirpath in models.items():
        actor_rates = load_actor_rates(dirpath)
        for ar in actor_rates:
            for cat in CATEGORIES:
                rows.append({
                    "model": model_name,
                    "actor": ar["actor"],
                    "level": ar["level"],
                    "n": int(ar["n"]),
                    "category": cat,
                    "rate": float(ar[f"{cat}_rate"]),
                    "count": int(ar[f"{cat}_count"]),
                })
    return rows


# ---------------------------------------------------------------------------
# Model pairwise comparison
# ---------------------------------------------------------------------------

def build_model_pairwise(models: Dict[str, str]) -> List[dict]:
    """Pairwise model comparison per category (Confirmed level, all actors pooled)."""
    # Aggregate per model: pool all Confirmed actors
    model_data: Dict[str, Dict[str, Tuple[int, int]]] = {}  # model -> cat -> (hits, n)
    for model_name, dirpath in models.items():
        actor_rates = load_actor_rates(dirpath)
        cat_hits: Dict[str, int] = defaultdict(int)
        cat_n: Dict[str, int] = defaultdict(int)
        for ar in actor_rates:
            if ar["level"] == "Confirmed":
                n = int(ar["n"])
                for cat in CATEGORIES:
                    cat_hits[cat] += int(ar[f"{cat}_count"])
                    cat_n[cat] += n
        model_data[model_name] = {cat: (cat_hits[cat], cat_n[cat]) for cat in CATEGORIES}

    model_names = sorted(models.keys())
    rows = []
    for i, m1 in enumerate(model_names):
        for m2 in model_names[i + 1:]:
            for cat in CATEGORIES:
                h1, n1 = model_data[m1][cat]
                h2, n2 = model_data[m2][cat]
                p1 = h1 / n1 if n1 else 0
                p2 = h2 / n2 if n2 else 0
                z, p_val = prop_z_test(p1, n1, p2, n2)
                h = cohen_h(p1, p2)
                rows.append({
                    "model_1": m1,
                    "model_2": m2,
                    "category": cat,
                    "rate_1": round(p1, 4),
                    "rate_2": round(p2, 4),
                    "n_1": n1,
                    "n_2": n2,
                    "z_stat": round(z, 4) if z is not None else None,
                    "p_value": round(p_val, 6) if p_val is not None else None,
                    "cohen_h": round(h, 4),
                    "significant_005": "yes" if p_val is not None and p_val < 0.05 else "no",
                })
    return rows


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    models: Dict[str, str],
    cross_rates: List[dict],
    model_pairwise: List[dict],
) -> str:
    model_names = sorted(models.keys())
    lines = [
        "# Cross-Model Confidence Pattern Comparison",
        "",
        f"**Models compared:** {', '.join(model_names)}",
        f"**Categories:** {len(CATEGORIES)}",
        "",
        "---",
        "",
        "## 1. Overall detection rates at Confirmed level (all actors pooled)",
        "",
    ]

    # Build summary table: model x category
    header = "| Category | " + " | ".join(model_names) + " |"
    sep = "|---|" + "|".join(["---"] * len(model_names)) + "|"
    lines.append(header)
    lines.append(sep)

    # Aggregate rates per model per category
    model_cat_rates: Dict[str, Dict[str, float]] = defaultdict(dict)
    model_cat_n: Dict[str, Dict[str, int]] = defaultdict(dict)
    for r in cross_rates:
        if r["level"] == "Confirmed":
            key = (r["model"], r["category"])
            if r["category"] not in model_cat_rates[r["model"]]:
                model_cat_rates[r["model"]][r["category"]] = 0
                model_cat_n[r["model"]][r["category"]] = 0
            model_cat_rates[r["model"]][r["category"]] += r["count"]
            model_cat_n[r["model"]][r["category"]] += r["n"]

    for cat in CATEGORIES:
        vals = []
        for m in model_names:
            h = model_cat_rates.get(m, {}).get(cat, 0)
            n = model_cat_n.get(m, {}).get(cat, 1)
            vals.append(f"{h/n:.1%}")
        lines.append(f"| {CATEGORY_SHORT[cat]} | " + " | ".join(vals) + " |")

    lines.extend(["", "---", "", "## 2. Model pairwise tests (Confirmed, all actors pooled)", ""])
    lines.append("| Model pair | Category | Rate 1 | Rate 2 | h | p | Sig? |")
    lines.append("|---|---|---|---|---|---|---|")

    sig_count = 0
    for r in model_pairwise:
        h_str = f"{r['cohen_h']:.3f}" if r["cohen_h"] is not None else "—"
        p_str = f"{r['p_value']:.4f}" if r["p_value"] is not None else "—"
        sig = r["significant_005"]
        if sig == "yes":
            sig_count += 1
        lines.append(
            f"| {r['model_1']} vs {r['model_2']} | {CATEGORY_SHORT[r['category']]} "
            f"| {r['rate_1']:.1%} | {r['rate_2']:.1%} | {h_str} | {p_str} | {sig} |"
        )
    total_tests = len(model_pairwise)
    lines.extend([
        "",
        f"**Summary:** {sig_count}/{total_tests} tests significant at p<0.05.",
        "",
    ])

    # Actor uniformity comparison
    lines.extend(["---", "", "## 3. Actor uniformity comparison", ""])
    lines.append("| Model | Pairwise sig. (p<0.05) | Total tests | Uniformity |")
    lines.append("|---|---|---|---|")
    for m in model_names:
        pw = load_pairwise(models[m])
        sig = sum(1 for r in pw if r.get("significant_005") == "yes")
        total = len(pw)
        if sig <= 2:
            label = "Actor-uniform"
        elif sig <= 5:
            label = "Mostly uniform"
        elif sig <= 10:
            label = "Moderately differentiated"
        else:
            label = "Actor-differentiated"
        lines.append(f"| {m} | {sig} | {total} | {label} |")

    # N-gram vocabulary highlights
    lines.extend(["", "---", "", "## 4. Model-specific vocabulary (top 10 n-grams)", ""])
    for m in model_names:
        ngrams = load_ngrams(models[m])
        lines.append(f"### {m}")
        lines.append("")
        if ngrams:
            lines.append("| N-gram | Doc rate |")
            lines.append("|---|---|")
            for ng in ngrams[:10]:
                lines.append(f"| {ng['ngram']} | {float(ng['doc_rate']):.1%} |")
        else:
            lines.append("*No n-gram data available.*")
        lines.append("")

    # Conclusions
    lines.extend(["---", "", "## 5. Key observations", ""])

    lines.extend(["", "---", ""])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV output
# ---------------------------------------------------------------------------

def write_csv(path: str, rows: List[dict]):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Cross-model confidence pattern comparison")
    parser.add_argument("--models", nargs="+", required=True,
                        help="Model=dir pairs, e.g. qwen3=results/Phase_2/qwen3-thinking/confidence_patterns")
    parser.add_argument("--outdir", required=True, help="Output directory")
    args = parser.parse_args()

    # Parse model=dir pairs
    models: Dict[str, str] = {}
    for pair in args.models:
        name, path = pair.split("=", 1)
        models[name] = path

    print(f"Comparing {len(models)} models: {', '.join(sorted(models.keys()))}")

    print("Building cross-model rate table...")
    cross_rates = build_cross_model_rates(models)

    print("Computing model pairwise tests...")
    model_pairwise = build_model_pairwise(models)

    print("Generating report...")
    report = generate_report(models, cross_rates, model_pairwise)

    # Write outputs
    os.makedirs(args.outdir, exist_ok=True)
    write_csv(os.path.join(args.outdir, "cross_model_pattern_rates.csv"), cross_rates)
    write_csv(os.path.join(args.outdir, "cross_model_pairwise.csv"), model_pairwise)

    report_path = os.path.join(args.outdir, "cross_model_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nOutputs written to {args.outdir}/")
    for fn in ["cross_model_pattern_rates.csv", "cross_model_pairwise.csv", "cross_model_report.md"]:
        path = os.path.join(args.outdir, fn)
        if os.path.exists(path):
            print(f"  ✓ {fn}")
        else:
            print(f"  ✗ {fn} MISSING")

    # Quick summary
    sig = sum(1 for r in model_pairwise if r["significant_005"] == "yes")
    print(f"\nModel pairwise: {sig}/{len(model_pairwise)} significant at p<0.05")


if __name__ == "__main__":
    main()
