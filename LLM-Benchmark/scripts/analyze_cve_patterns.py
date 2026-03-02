#!/usr/bin/env python3
"""Analyse CVE citation patterns across LLM benchmark models.

Detects fixation behaviour (e.g. PwnKit fixation in deepseek-r1),
computes diversity metrics, and cross-tabulates CVEs against
experimental conditions.

Usage:
    python3 scripts/analyze_cve_patterns.py \
        --models deepseek-r1=results/Phase_2/deepseek-r1/deepseek-r1_flat.csv \
                 qwen3=results/Phase_2/qwen3-thinking/qwen3_flat.csv \
        --outdir results/Phase_2/cve_patterns
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FIXATION_THRESHOLD = 0.40  # flag if single CVE > 40% of CVE-containing records

# Phase 1 validated CVEs (from Results_Data.md §11)
KNOWN_REAL_CVES = {
    "CVE-2021-4034",   # PwnKit
    "CVE-2021-44228",  # Log4Shell
    "CVE-2020-0688",   # Exchange RCE
    "CVE-2021-40444",  # MSHTML RCE
    "CVE-2021-3493",   # OverlayFS
    "CVE-2021-3156",   # Baron Samedit
    "CVE-2021-1675",   # PrintNightmare
    "CVE-2022-22947",  # Spring Cloud GW
    "CVE-2019-2725",   # WebLogic RCE
    "CVE-2020-1337",   # Print Spooler
}

# Phase 1 confirmed hallucinated CVEs
KNOWN_HALLUCINATED_CVES = {
    "CVE-2021-3151",
    "CVE-2021-34930",
    "CVE-2021-34938",
    "CVE-2021-34521",
}

# Phase 1 PwnKit stats for comparison
PHASE1_PWNKIT = {
    "cve_records": 24,
    "pwnkit_count": 18,
    "concentration": 0.75,
}

# CVE regex for extraction / validation
CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,}")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data(flat_path: str) -> List[dict]:
    """Load flat CSV, return only ok==True records."""
    rows = []
    with open(flat_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("ok") == "True":
                rows.append(row)
    return rows


def parse_cves(cve_str: str) -> List[str]:
    """Parse semicolon-separated CVE string into list of unique CVEs."""
    if not cve_str or cve_str.strip() == "":
        return []
    cves = [c.strip() for c in cve_str.split(";") if c.strip()]
    return cves


def parse_condition(condition: str) -> Tuple[str, str]:
    """Split condition into (actor, level). Neutral → ('Neutral', 'Neutral')."""
    if condition == "Neutral":
        return ("Neutral", "Neutral")
    parts = condition.rsplit("_", 1)
    if len(parts) == 2:
        return (parts[0], parts[1])
    return (condition, "Unknown")


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------


def compute_mention_rates(
    all_models: Dict[str, List[dict]],
) -> List[dict]:
    """Per-model CVE mention rates."""
    rows = []
    for model, records in all_models.items():
        total = len(records)
        with_cves = sum(1 for r in records if int(r.get("cve_count", 0)) > 0)
        cve_counts = [int(r.get("cve_count", 0)) for r in records]
        mean_count = sum(cve_counts) / total if total else 0
        mean_when_present = (
            sum(c for c in cve_counts if c > 0) / with_cves if with_cves else 0
        )
        rows.append(
            {
                "model": model,
                "total_records": total,
                "records_with_cves": with_cves,
                "cve_mention_rate": round(with_cves / total, 4) if total else 0,
                "mean_cve_per_record": round(mean_count, 3),
                "mean_cve_when_present": round(mean_when_present, 3),
            }
        )
    return rows


def compute_cve_frequency(
    all_models: Dict[str, List[dict]],
) -> List[dict]:
    """Per-model CVE frequency ranked list."""
    rows = []
    for model, records in all_models.items():
        cve_counter: Counter = Counter()
        cve_records = 0
        for r in records:
            cves = parse_cves(r.get("cves", ""))
            if cves:
                cve_records += 1
                for cve in set(cves):  # count each CVE once per record
                    cve_counter[cve] += 1
        for rank, (cve, count) in enumerate(cve_counter.most_common(), 1):
            pct = round(count / cve_records * 100, 1) if cve_records else 0
            known = cve in KNOWN_REAL_CVES
            hallucinated = cve in KNOWN_HALLUCINATED_CVES
            status = (
                "real"
                if known
                else "hallucinated"
                if hallucinated
                else "unverified"
            )
            rows.append(
                {
                    "model": model,
                    "rank": rank,
                    "cve": cve,
                    "record_count": count,
                    "pct_of_cve_records": pct,
                    "status": status,
                }
            )
    return rows


def compute_shannon_entropy(counter: Counter) -> float:
    """Shannon entropy (log2) of a frequency distribution."""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in counter.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def compute_diversity(
    all_models: Dict[str, List[dict]],
) -> Dict[str, dict]:
    """Per-model CVE diversity metrics."""
    result = {}
    for model, records in all_models.items():
        cve_counter: Counter = Counter()
        cve_records = 0
        for r in records:
            cves = parse_cves(r.get("cves", ""))
            if cves:
                cve_records += 1
                for cve in set(cves):
                    cve_counter[cve] += 1
        unique = len(cve_counter)
        entropy = compute_shannon_entropy(cve_counter)
        max_entropy = math.log2(unique) if unique > 1 else 0
        # Fixation detection
        top_cve = cve_counter.most_common(1)[0] if cve_counter else (None, 0)
        top_pct = top_cve[1] / cve_records if cve_records else 0
        fixated = top_pct > FIXATION_THRESHOLD
        result[model] = {
            "cve_records": cve_records,
            "unique_cves": unique,
            "shannon_entropy": round(entropy, 3),
            "max_entropy": round(max_entropy, 3),
            "normalised_entropy": (
                round(entropy / max_entropy, 3) if max_entropy > 0 else 0
            ),
            "top_cve": top_cve[0],
            "top_cve_count": top_cve[1],
            "top_cve_pct": round(top_pct * 100, 1),
            "fixated": fixated,
        }
    return result


def compute_sector_crosstab(
    all_models: Dict[str, List[dict]],
) -> Tuple[List[dict], Dict[str, set]]:
    """CVE × sector cross-tabulation. Returns rows and per-CVE sector sets."""
    # Collect all CVE-sector pairs across all models
    cve_sector: Dict[str, Dict[str, Counter]] = {}  # model → {cve → sector counter}
    all_sectors: set = set()
    cve_all_sectors: Dict[str, set] = defaultdict(set)  # cve → set of sectors (global)

    for model, records in all_models.items():
        cve_sector[model] = defaultdict(Counter)
        for r in records:
            cves = parse_cves(r.get("cves", ""))
            sector = r.get("sector_focus", "Unknown")
            all_sectors.add(sector)
            for cve in set(cves):
                cve_sector[model][cve][sector] += 1
                cve_all_sectors[cve].add(sector)

    rows = []
    for model in all_models:
        for cve, sector_counts in sorted(cve_sector[model].items()):
            for sector in sorted(all_sectors):
                count = sector_counts.get(sector, 0)
                if count > 0:
                    rows.append(
                        {
                            "model": model,
                            "cve": cve,
                            "sector": sector,
                            "count": count,
                        }
                    )
    return rows, cve_all_sectors


def compute_condition_rates(
    all_models: Dict[str, List[dict]],
) -> List[dict]:
    """CVE mention rate by model × actor × certainty level."""
    rows = []
    for model, records in all_models.items():
        # Group by condition
        groups: Dict[str, List[dict]] = defaultdict(list)
        for r in records:
            groups[r.get("condition", "Unknown")].append(r)

        for condition in sorted(groups):
            actor, level = parse_condition(condition)
            group = groups[condition]
            total = len(group)
            with_cves = sum(1 for r in group if int(r.get("cve_count", 0)) > 0)
            rate = round(with_cves / total, 4) if total else 0
            rows.append(
                {
                    "model": model,
                    "condition": condition,
                    "actor": actor,
                    "level": level,
                    "total_records": total,
                    "records_with_cves": with_cves,
                    "cve_rate": rate,
                }
            )
    return rows


def compute_temperature_effects(
    all_models: Dict[str, List[dict]],
) -> List[dict]:
    """CVE mention rate by model × temperature."""
    rows = []
    for model, records in all_models.items():
        groups: Dict[str, List[dict]] = defaultdict(list)
        for r in records:
            groups[r.get("temperature", "?")].append(r)
        for temp in sorted(groups):
            group = groups[temp]
            total = len(group)
            with_cves = sum(1 for r in group if int(r.get("cve_count", 0)) > 0)
            cve_counts = [int(r.get("cve_count", 0)) for r in group if int(r.get("cve_count", 0)) > 0]
            mean_when_present = sum(cve_counts) / len(cve_counts) if cve_counts else 0
            rows.append(
                {
                    "model": model,
                    "temperature": temp,
                    "total_records": total,
                    "records_with_cves": with_cves,
                    "cve_rate": round(with_cves / total, 4) if total else 0,
                    "mean_cves_when_present": round(mean_when_present, 3),
                }
            )
    return rows


def classify_cves(
    all_models: Dict[str, List[dict]],
) -> Dict[str, Dict[str, List[str]]]:
    """Classify all cited CVEs into real / hallucinated / unverified per model."""
    result = {}
    for model, records in all_models.items():
        all_cves: set = set()
        for r in records:
            all_cves.update(parse_cves(r.get("cves", "")))
        real = sorted(all_cves & KNOWN_REAL_CVES)
        hallucinated = sorted(all_cves & KNOWN_HALLUCINATED_CVES)
        unverified = sorted(all_cves - KNOWN_REAL_CVES - KNOWN_HALLUCINATED_CVES)
        result[model] = {
            "real": real,
            "hallucinated": hallucinated,
            "unverified": unverified,
        }
    return result


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def write_csv(path: str, rows: List[dict], fieldnames: Optional[List[str]] = None):
    """Write list of dicts to CSV."""
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def generate_report(
    all_models: Dict[str, List[dict]],
    mention_rates: List[dict],
    frequency: List[dict],
    diversity: Dict[str, dict],
    sector_crosstab: List[dict],
    cve_all_sectors: Dict[str, set],
    condition_rates: List[dict],
    temp_effects: List[dict],
    cve_classes: Dict[str, Dict[str, List[str]]],
) -> str:
    """Generate the Markdown fixation report."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []
    a = lines.append

    a("---")
    a("title: CVE Fixation Analysis — Phase 2")
    a(f"generated: {now}")
    a("document_type: analysis-index")
    a("tags:")
    a("  - llm-benchmark/phase-2")
    a("  - llm-benchmark/cve-analysis")
    a("---")
    a("")
    a("# CVE Fixation Analysis — Phase 2")
    a("")
    a(f"> Generated: {now}")
    a("")

    # --- Section 1: Mention Rates ---
    a("## 1. CVE Mention Rates")
    a("")
    a("| Model | Records | With CVEs | Rate | Mean CVE/record | Mean when present |")
    a("|-------|---------|-----------|------|-----------------|-------------------|")
    for mr in mention_rates:
        a(
            f"| {mr['model']} | {mr['total_records']} | {mr['records_with_cves']} "
            f"| {mr['cve_mention_rate']:.1%} | {mr['mean_cve_per_record']:.3f} "
            f"| {mr['mean_cve_when_present']:.3f} |"
        )
    a("")

    # --- Section 2: Top CVEs ---
    a("## 2. CVE Frequency Distribution (Top 10 per model)")
    a("")
    for model in all_models:
        model_freq = [f for f in frequency if f["model"] == model][:10]
        if not model_freq:
            continue
        a(f"### {model}")
        a("")
        a("| Rank | CVE | Records | % of CVE records | Status |")
        a("|------|-----|---------|------------------|--------|")
        for f in model_freq:
            a(
                f"| {f['rank']} | {f['cve']} | {f['record_count']} "
                f"| {f['pct_of_cve_records']}% | {f['status']} |"
            )
        a("")

    # --- Section 3: PwnKit Fixation ---
    a("## 3. PwnKit Fixation Check")
    a("")
    a("### Phase 1 Baseline")
    a("")
    a(f"- CVE-containing records: {PHASE1_PWNKIT['cve_records']}")
    a(f"- PwnKit (CVE-2021-4034) mentions: {PHASE1_PWNKIT['pwnkit_count']}")
    a(f"- Concentration: {PHASE1_PWNKIT['concentration']:.0%}")
    a("")
    a("### Phase 2 Results")
    a("")
    pwnkit_cve = "CVE-2021-4034"
    for model in all_models:
        d = diversity[model]
        # Count PwnKit specifically
        pwnkit_count = 0
        cve_records = 0
        for r in all_models[model]:
            cves = parse_cves(r.get("cves", ""))
            if cves:
                cve_records += 1
                if pwnkit_cve in cves:
                    pwnkit_count += 1
        pwnkit_pct = (pwnkit_count / cve_records * 100) if cve_records else 0
        a(f"**{model}:**")
        a(f"- CVE-containing records: {cve_records}")
        a(f"- PwnKit mentions: {pwnkit_count} ({pwnkit_pct:.1f}%)")
        if model.startswith("deepseek"):
            delta = pwnkit_pct - PHASE1_PWNKIT["concentration"] * 100
            direction = "increase" if delta > 0 else "decrease"
            a(
                f"- Phase 1 → 2 change: {delta:+.1f}pp ({direction})"
            )
        a("")

    # --- Section 4: Diversity Index ---
    a("## 4. CVE Diversity Index")
    a("")
    a("| Model | CVE records | Unique CVEs | Shannon H | Max H | Normalised H | Top CVE | Top % | Fixated? |")
    a("|-------|-------------|-------------|-----------|-------|-------------|---------|-------|----------|")
    for model in all_models:
        d = diversity[model]
        flag = "YES" if d["fixated"] else "no"
        a(
            f"| {model} | {d['cve_records']} | {d['unique_cves']} "
            f"| {d['shannon_entropy']:.3f} | {d['max_entropy']:.3f} "
            f"| {d['normalised_entropy']:.3f} | {d['top_cve']} "
            f"| {d['top_cve_pct']}% | {flag} |"
        )
    a("")
    a(f"> Fixation threshold: >{FIXATION_THRESHOLD:.0%} of CVE-containing records cite a single CVE.")
    a("")

    # --- Section 5: Sector Appropriateness ---
    a("## 5. Sector Appropriateness")
    a("")
    cross_sector_cves = {
        cve: sectors
        for cve, sectors in cve_all_sectors.items()
        if len(sectors) >= 5
    }
    if cross_sector_cves:
        a(
            f"**{len(cross_sector_cves)} CVE(s) appear across 5+ sectors** "
            "(potential contextual inappropriateness):"
        )
        a("")
        a("| CVE | Sector count | Sectors |")
        a("|-----|-------------|---------|")
        for cve in sorted(cross_sector_cves, key=lambda c: -len(cross_sector_cves[c])):
            sectors = sorted(cross_sector_cves[cve])
            a(f"| {cve} | {len(sectors)} | {', '.join(sectors)} |")
        a("")
    else:
        a("No CVEs found across 5+ unrelated sectors.")
        a("")

    # --- Section 6: CVE Hallucination Check ---
    a("## 6. CVE Hallucination Check")
    a("")
    for model in all_models:
        cls = cve_classes[model]
        a(f"### {model}")
        a("")
        a(f"- **Real** ({len(cls['real'])}): {', '.join(cls['real']) if cls['real'] else 'none'}")
        a(f"- **Hallucinated** ({len(cls['hallucinated'])}): {', '.join(cls['hallucinated']) if cls['hallucinated'] else 'none'}")
        a(f"- **Unverified** ({len(cls['unverified'])}): {', '.join(cls['unverified']) if cls['unverified'] else 'none'}")
        a("")

    # --- Section 7: Condition Effects ---
    a("## 7. Condition Effects on CVE Citation")
    a("")
    a("| Model | Actor | Level | Records | With CVEs | Rate |")
    a("|-------|-------|-------|---------|-----------|------|")
    for cr in condition_rates:
        a(
            f"| {cr['model']} | {cr['actor']} | {cr['level']} "
            f"| {cr['total_records']} | {cr['records_with_cves']} "
            f"| {cr['cve_rate']:.1%} |"
        )
    a("")

    # --- Section 8: Temperature Effects ---
    a("## 8. Temperature Effects on CVE Citation")
    a("")
    a("| Model | Temperature | Records | With CVEs | Rate | Mean CVEs (present) |")
    a("|-------|-------------|---------|-----------|------|---------------------|")
    for te in temp_effects:
        a(
            f"| {te['model']} | {te['temperature']} | {te['total_records']} "
            f"| {te['records_with_cves']} | {te['cve_rate']:.1%} "
            f"| {te['mean_cves_when_present']:.3f} |"
        )
    a("")

    # --- Summary ---
    a("## Summary")
    a("")
    fixated_models = [m for m, d in diversity.items() if d["fixated"]]
    if fixated_models:
        a(f"**Fixation detected** in: {', '.join(fixated_models)}")
    else:
        a("**No fixation detected** (no model exceeds the 40% single-CVE threshold).")
    a("")

    # deepseek-r1 specific summary
    if "deepseek-r1" in diversity:
        d = diversity["deepseek-r1"]
        a("### deepseek-r1 Phase 1 → Phase 2 Evolution")
        a("")
        a(f"- Phase 1: 24 CVE records, PwnKit at 75%, Shannon H ≈ low (dominated by single CVE)")
        a(f"- Phase 2: {d['cve_records']} CVE records, top CVE ({d['top_cve']}) at {d['top_cve_pct']}%, Shannon H = {d['shannon_entropy']:.3f}")
        if d["fixated"]:
            a(f"- **Fixation persists** — {d['top_cve']} exceeds {FIXATION_THRESHOLD:.0%} threshold")
        else:
            a(f"- **Fixation resolved** — no single CVE exceeds {FIXATION_THRESHOLD:.0%} threshold")
        a("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Analyse CVE citation patterns across LLM benchmark models"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        required=True,
        help="model=path pairs to flat CSVs, e.g. deepseek-r1=path/to/flat.csv",
    )
    parser.add_argument(
        "--outdir",
        default="results/Phase_2/cve_patterns",
        help="Output directory (default: results/Phase_2/cve_patterns)",
    )
    args = parser.parse_args()

    # Parse model=path pairs
    models: Dict[str, str] = {}
    for pair in args.models:
        if "=" not in pair:
            print(f"ERROR: expected model=path format, got: {pair}", file=sys.stderr)
            sys.exit(1)
        name, path = pair.split("=", 1)
        models[name] = path

    # Load data
    all_models: Dict[str, List[dict]] = {}
    for name, path in models.items():
        if not os.path.exists(path):
            print(f"ERROR: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        data = load_data(path)
        print(f"  {name}: {len(data)} valid records from {path}")
        all_models[name] = data

    os.makedirs(args.outdir, exist_ok=True)

    # Run analyses
    print("\nRunning CVE pattern analysis...")

    mention_rates = compute_mention_rates(all_models)
    write_csv(os.path.join(args.outdir, "cve_mention_rates.csv"), mention_rates)
    print("  - cve_mention_rates.csv")

    frequency = compute_cve_frequency(all_models)
    write_csv(os.path.join(args.outdir, "cve_frequency.csv"), frequency)
    print("  - cve_frequency.csv")

    diversity = compute_diversity(all_models)

    sector_crosstab, cve_all_sectors = compute_sector_crosstab(all_models)
    write_csv(os.path.join(args.outdir, "cve_sector_crosstab.csv"), sector_crosstab)
    print("  - cve_sector_crosstab.csv")

    condition_rates = compute_condition_rates(all_models)
    write_csv(os.path.join(args.outdir, "cve_condition_rates.csv"), condition_rates)
    print("  - cve_condition_rates.csv")

    temp_effects = compute_temperature_effects(all_models)

    cve_classes = classify_cves(all_models)

    report = generate_report(
        all_models,
        mention_rates,
        frequency,
        diversity,
        sector_crosstab,
        cve_all_sectors,
        condition_rates,
        temp_effects,
        cve_classes,
    )
    report_path = os.path.join(args.outdir, "cve_fixation_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  - cve_fixation_report.md")

    print(f"\nDone. Output in {args.outdir}/")


if __name__ == "__main__":
    main()
