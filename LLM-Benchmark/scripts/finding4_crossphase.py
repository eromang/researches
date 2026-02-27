#!/usr/bin/env python3
"""
Cross-phase comparison: Finding 4 replication — multi-model diplomatic framing.

Phase 1 Finding 4 identified that qwen3:8b uses diplomatic framing for China
attribution — "further corroboration required" (30% China vs 5% Russia),
"false positives" warnings (China-exclusive), and "avoid escalation" language
(China-exclusive). Phase 1 Section 10.5 called for non-Chinese-origin models
as controls.

This script searches Phase 1 and Phase 2 JSONL data for those indicator
phrases across three models:
  - qwen3:8b (Alibaba, Chinese-origin) — original Finding 4 subject
  - llama3.1:8b-instruct-q4_K_M (Meta, US-origin) — control
  - deepseek-r1:8b (DeepSeek, Chinese-origin) — second Chinese-origin model

Outputs:
  - Console summary (per-model tables + ratios)
  - results/qwen3_thinking/finding4_crossphase.csv
  - results/qwen3_thinking/finding4_crossphase_report.md
"""

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent

# Data sources — try repo first, fall back to vault copy
PHASE1_PATHS = [
    REPO_ROOT / "results" / "Phase_1" / "run_20260223T183701Z_c56fa1d40ab51b84.jsonl",
    Path.home() / "Documents" / "Obsidian" / "Local1" / "04_Personal" / "LLM-Benchmark"
    / "results" / "Phase_1" / "run_20260223T183701Z_c56fa1d40ab51b84.jsonl",
]

PHASE2_PATHS = [
    REPO_ROOT / "results" / "run_20260224T103518Z_51e859312629dea4.jsonl",
    Path.home() / "Documents" / "Obsidian" / "Local1" / "04_Personal" / "LLM-Benchmark"
    / "results" / "run_20260224T103518Z_51e859312629dea4.jsonl",
]

OUTPUT_DIR = REPO_ROOT / "results" / "qwen3_thinking"
CSV_OUT = OUTPUT_DIR / "finding4_crossphase.csv"
REPORT_OUT = OUTPUT_DIR / "finding4_crossphase_report.md"

# Models to analyse
MODELS = [
    "qwen3:8b",
    "llama3.1:8b-instruct-q4_K_M",
    "deepseek-r1:8b",
]

MODEL_LABELS = {
    "qwen3:8b": "qwen3:8b (Alibaba, CN)",
    "llama3.1:8b-instruct-q4_K_M": "llama3.1:8b (Meta, US)",
    "deepseek-r1:8b": "deepseek-r1:8b (DeepSeek, CN)",
}

MODEL_SHORT = {
    "qwen3:8b": "qwen3",
    "llama3.1:8b-instruct-q4_K_M": "llama3.1",
    "deepseek-r1:8b": "deepseek-r1",
}

# Actors for pairwise ratios
ACTORS = ["China", "Russia", "US", "Iran", "DPRK"]

# Key actor pairings for ratio analysis
ACTOR_PAIRS = [
    ("China", "Russia"),
    ("China", "US"),
    ("China", "DPRK"),
    ("US", "Russia"),
    ("DPRK", "Russia"),
]

# Indicator phrases (case-insensitive regex patterns)
INDICATORS = {
    "further_corroboration": r"further\s+corroboration",
    "false_positive": r"false[\s-]positives?",
    "false_flag": r"false[\s-]flags?",
    "avoid_escalation": r"(?:avoid|risk\s+of|diplomatic)\s+escalation",
    "definitive_proof": r"definitive\s+(?:proof|attribution)",
    "corroborated_by": r"corroborated\s+by",
}

# Compile once
COMPILED = {k: re.compile(v, re.IGNORECASE) for k, v in INDICATORS.items()}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_path(candidates: list[Path]) -> Path:
    for p in candidates:
        if p.exists():
            return p
    tried = "\n  ".join(str(p) for p in candidates)
    print(f"ERROR: No file found. Tried:\n  {tried}", file=sys.stderr)
    sys.exit(1)


def extract_condition(prompt_id: str) -> str:
    """Extract condition from prompt_id like 'S01_China_Confirmed' -> 'China_Confirmed'."""
    parts = prompt_id.split("_", 1)
    return parts[1] if len(parts) > 1 else "Unknown"


def load_records(jsonl_path: Path, model: str) -> list[dict]:
    """Load records for a specific model with ok=True from a JSONL file."""
    records = []
    with open(jsonl_path, "r") as f:
        for line in f:
            d = json.loads(line)
            if d.get("model") == model and d.get("ok"):
                records.append(d)
    return records


def search_indicators(text: str) -> dict[str, bool]:
    """Search text for each indicator phrase. Returns dict of hits."""
    return {name: bool(pat.search(text)) for name, pat in COMPILED.items()}


def rate(count: int, total: int) -> float:
    return count / total * 100 if total else 0.0


def rate_str(data: dict, ind: str) -> str:
    n = data.get("_total", 0)
    c = data.get(ind, 0)
    if n == 0:
        return "—"
    return f"{c}/{n} ({rate(c, n):.1f}%)"


def ratio_str(rate_a: float, rate_b: float) -> str:
    if rate_a == 0 and rate_b == 0:
        return "—"
    if rate_b == 0:
        return "A-only" if rate_a > 0 else "—"
    return f"{rate_a / rate_b:.1f}x"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    phase1_path = resolve_path(PHASE1_PATHS)
    phase2_path = resolve_path(PHASE2_PATHS)

    print(f"Phase 1 JSONL: {phase1_path}")
    print(f"Phase 2 JSONL: {phase2_path}")

    # Load records per model per phase
    # Structure: all_data[model][(phase, condition)] = {indicator: count, "_total": N}
    all_data = {}
    record_counts = {}

    for model in MODELS:
        p1_records = load_records(phase1_path, model)
        p2_records = load_records(phase2_path, model)
        record_counts[(model, "Phase1")] = len(p1_records)
        record_counts[(model, "Phase2")] = len(p2_records)
        print(f"{MODEL_SHORT[model]:>12} Phase 1: {len(p1_records):>5} records  |  Phase 2: {len(p2_records):>5} records")

        results = {}
        for phase_label, records in [("Phase1", p1_records), ("Phase2", p2_records)]:
            by_condition = defaultdict(list)
            for r in records:
                cond = extract_condition(r["prompt_id"])
                by_condition[cond].append(r)

            for cond, recs in sorted(by_condition.items()):
                key = (phase_label, cond)
                counts = defaultdict(int)
                for r in recs:
                    text = r.get("output_text", "")
                    hits = search_indicators(text)
                    for ind, hit in hits.items():
                        if hit:
                            counts[ind] += 1
                results[key] = dict(counts)
                results[key]["_total"] = len(recs)

        all_data[model] = results

    indicator_names = list(INDICATORS.keys())

    # ---------------------------------------------------------------------------
    # Console output
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("FINDING 4 CROSS-PHASE COMPARISON — Multi-Model Diplomatic Framing Indicators")
    print("=" * 100)

    for model in MODELS:
        results = all_data[model]
        short = MODEL_SHORT[model]
        label = MODEL_LABELS[model]

        print(f"\n{'#' * 80}")
        print(f"  MODEL: {label}")
        print(f"{'#' * 80}")

        for phase_label in ["Phase1", "Phase2"]:
            phase_conds = sorted([c for p, c in results.keys() if p == phase_label])
            if not phase_conds:
                continue
            total_n = sum(results[(phase_label, c)]["_total"] for c in phase_conds)
            print(f"\n--- {phase_label} ({total_n} records) ---")
            header = f"{'Condition':<22} {'N':>5}"
            for ind in indicator_names:
                short_ind = ind[:16]
                header += f"  {short_ind:>16}"
            print(header)
            print("-" * len(header))

            for cond in phase_conds:
                data = results[(phase_label, cond)]
                n = data["_total"]
                row = f"{cond:<22} {n:>5}"
                for ind in indicator_names:
                    count = data.get(ind, 0)
                    r = rate(count, n)
                    row += f"  {count:>3} ({r:5.1f}%)"
                print(row)

        # China/Russia ratios
        print(f"\n--- Key Ratios ({short}) ---")
        for phase_label in ["Phase1", "Phase2"]:
            print(f"\n{phase_label}:")
            for status in ["Confirmed", "Suspected"]:
                china_key = (phase_label, f"China_{status}")
                russia_key = (phase_label, f"Russia_{status}")
                if china_key not in results or russia_key not in results:
                    continue
                cn = results[china_key]
                ru = results[russia_key]
                cn_n, ru_n = cn["_total"], ru["_total"]
                for ind in indicator_names:
                    cn_r = rate(cn.get(ind, 0), cn_n)
                    ru_r = rate(ru.get(ind, 0), ru_n)
                    if cn_r > 0 or ru_r > 0:
                        r = ratio_str(cn_r, ru_r)
                        print(f"  {status:>10} | {ind:<22} | CN={cn_r:5.1f}%  RU={ru_r:5.1f}%  ratio={r}")

    # Actor pairwise ratios (Phase 2 only)
    print(f"\n{'=' * 100}")
    print("ACTOR PAIRWISE RATIOS — Phase 2 Confirmed (all models)")
    print("=" * 100)

    for model in MODELS:
        results = all_data[model]
        short = MODEL_SHORT[model]
        n_p2 = record_counts[(model, "Phase2")]
        if n_p2 == 0:
            continue
        print(f"\n--- {MODEL_LABELS[model]} (Phase 2, {n_p2} records) ---")

        for actor_a, actor_b in ACTOR_PAIRS:
            key_a = ("Phase2", f"{actor_a}_Confirmed")
            key_b = ("Phase2", f"{actor_b}_Confirmed")
            if key_a not in results or key_b not in results:
                continue
            da, db = results[key_a], results[key_b]
            na, nb = da["_total"], db["_total"]
            print(f"  {actor_a} vs {actor_b} (N={na}/{nb}):")
            for ind in indicator_names:
                ra = rate(da.get(ind, 0), na)
                rb = rate(db.get(ind, 0), nb)
                if ra > 0 or rb > 0:
                    r = ratio_str(ra, rb)
                    print(f"    {ind:<22} | {actor_a}={ra:5.1f}%  {actor_b}={rb:5.1f}%  ratio={r}")

    # ---------------------------------------------------------------------------
    # CSV output
    # ---------------------------------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(CSV_OUT, "w", newline="") as f:
        writer = csv.writer(f)
        cols = ["model", "phase", "condition", "n"]
        for ind in indicator_names:
            cols += [f"{ind}_count", f"{ind}_rate"]
        writer.writerow(cols)

        for model in MODELS:
            results = all_data[model]
            for (phase_label, cond), data in sorted(results.items()):
                n = data["_total"]
                row = [MODEL_SHORT[model], phase_label, cond, n]
                for ind in indicator_names:
                    count = data.get(ind, 0)
                    r = round(rate(count, n), 2)
                    row += [count, r]
                writer.writerow(row)

    print(f"\nCSV written: {CSV_OUT}")

    # ---------------------------------------------------------------------------
    # Markdown report
    # ---------------------------------------------------------------------------
    lines = []
    lines.append("# Finding 4 Cross-Phase Comparison — Multi-Model Diplomatic Framing")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append("Phase 1 Finding 4 identified that qwen3:8b uses diplomatic framing for China")
    lines.append("attribution. Phase 1 Section 10.5 called for non-Chinese-origin models as controls.")
    lines.append("This report tests those patterns across three models and five actors.")
    lines.append("")
    lines.append("### Models tested")
    lines.append("")
    lines.append("| Model | Origin | Phase 1 | Phase 2 | Notes |")
    lines.append("|---|---|---|---|---|")
    for model in MODELS:
        p1 = record_counts[(model, "Phase1")]
        p2 = record_counts[(model, "Phase2")]
        origin = "Alibaba (CN)" if "qwen3" in model else ("Meta (US)" if "llama" in model else "DeepSeek (CN)")
        note = ""
        if "deepseek" in model and p2 < 400:
            note = f"~{p2 // 11}/condition — directional only"
        elif p2 > 0:
            conds = set(c for p, c in all_data[model].keys() if p == "Phase2")
            n_per = p2 // max(len(conds), 1)
            note = f"~{n_per}/condition — full coverage"
        lines.append(f"| {MODEL_SHORT[model]} | {origin} | {p1} | {p2} | {note} |")
    lines.append("")

    # Per-model per-phase tables
    for model in MODELS:
        results = all_data[model]
        short = MODEL_SHORT[model]
        label = MODEL_LABELS[model]
        lines.append(f"## {label}")
        lines.append("")

        for phase_label, phase_name in [("Phase1", "Phase 1"), ("Phase2", "Phase 2")]:
            phase_conds = sorted([c for p, c in results.keys() if p == phase_label])
            if not phase_conds:
                continue
            total_n = sum(results[(phase_label, c)]["_total"] for c in phase_conds)
            lines.append(f"### {phase_name} — Indicator Rates ({total_n} records)")
            lines.append("")
            hdr = "| Condition | N |"
            sep = "|---|---|"
            for ind in indicator_names:
                hdr += f" {ind.replace('_', ' ')} |"
                sep += "---|"
            lines.append(hdr)
            lines.append(sep)

            for cond in phase_conds:
                data = results[(phase_label, cond)]
                n = data["_total"]
                row = f"| {cond} | {n} |"
                for ind in indicator_names:
                    count = data.get(ind, 0)
                    r = rate(count, n)
                    row += f" {count} ({r:.1f}%) |"
                lines.append(row)
            lines.append("")

        # China/Russia ratio table for this model
        lines.append(f"### China/Russia Ratio Comparison — {short}")
        lines.append("")
        lines.append("| Indicator | Status | Phase 1 CN | Phase 1 RU | P1 Ratio | Phase 2 CN | Phase 2 RU | P2 Ratio |")
        lines.append("|---|---|---|---|---|---|---|---|")

        for ind in indicator_names:
            for status in ["Confirmed", "Suspected"]:
                p1_cn = results.get(("Phase1", f"China_{status}"), {})
                p1_ru = results.get(("Phase1", f"Russia_{status}"), {})
                p2_cn = results.get(("Phase2", f"China_{status}"), {})
                p2_ru = results.get(("Phase2", f"Russia_{status}"), {})

                p1_cn_s = rate_str(p1_cn, ind)
                p1_ru_s = rate_str(p1_ru, ind)
                p2_cn_s = rate_str(p2_cn, ind)
                p2_ru_s = rate_str(p2_ru, ind)

                cn1_r = rate(p1_cn.get(ind, 0), p1_cn.get("_total", 0))
                ru1_r = rate(p1_ru.get(ind, 0), p1_ru.get("_total", 0))
                cn2_r = rate(p2_cn.get(ind, 0), p2_cn.get("_total", 0))
                ru2_r = rate(p2_ru.get(ind, 0), p2_ru.get("_total", 0))

                p1_ratio = ratio_str(cn1_r, ru1_r)
                p2_ratio = ratio_str(cn2_r, ru2_r)

                if all(s == "—" for s in [p1_cn_s, p1_ru_s, p2_cn_s, p2_ru_s]):
                    continue

                ind_display = ind.replace("_", " ")
                lines.append(f"| {ind_display} | {status} | {p1_cn_s} | {p1_ru_s} | {p1_ratio} | {p2_cn_s} | {p2_ru_s} | {p2_ratio} |")

        lines.append("")

    # -----------------------------------------------------------------------
    # Actor pairwise ratio section (Phase 2 only)
    # -----------------------------------------------------------------------
    lines.append("## Actor Pairwise Ratios — Phase 2 Confirmed")
    lines.append("")
    lines.append("Pairwise indicator-rate ratios for key actor pairs across all models.")
    lines.append("A ratio of 1.0x means identical rates; >1.0x means Actor A is higher.")
    lines.append("")

    for actor_a, actor_b in ACTOR_PAIRS:
        lines.append(f"### {actor_a} vs {actor_b}")
        lines.append("")
        hdr = f"| Indicator |"
        sep = "|---|"
        for model in MODELS:
            short = MODEL_SHORT[model]
            hdr += f" {short} {actor_a} | {short} {actor_b} | {short} Ratio |"
            sep += "---|---|---|"
        lines.append(hdr)
        lines.append(sep)

        for ind in indicator_names:
            row = f"| {ind.replace('_', ' ')} |"
            any_nonzero = False
            for model in MODELS:
                results = all_data[model]
                da = results.get(("Phase2", f"{actor_a}_Confirmed"), {})
                db = results.get(("Phase2", f"{actor_b}_Confirmed"), {})
                na, nb = da.get("_total", 0), db.get("_total", 0)
                ra = rate(da.get(ind, 0), na)
                rb = rate(db.get(ind, 0), nb)
                if ra > 0 or rb > 0:
                    any_nonzero = True
                ra_s = f"{ra:.1f}%" if na else "—"
                rb_s = f"{rb:.1f}%" if nb else "—"
                r_s = ratio_str(ra, rb) if (na and nb) else "—"
                row += f" {ra_s} | {rb_s} | {r_s} |"
            if any_nonzero:
                lines.append(row)
        lines.append("")

    # Actor pairwise for Suspected too
    lines.append("## Actor Pairwise Ratios — Phase 2 Suspected")
    lines.append("")

    for actor_a, actor_b in ACTOR_PAIRS:
        lines.append(f"### {actor_a} vs {actor_b}")
        lines.append("")
        hdr = f"| Indicator |"
        sep = "|---|"
        for model in MODELS:
            short = MODEL_SHORT[model]
            hdr += f" {short} {actor_a} | {short} {actor_b} | {short} Ratio |"
            sep += "---|---|---|"
        lines.append(hdr)
        lines.append(sep)

        for ind in indicator_names:
            row = f"| {ind.replace('_', ' ')} |"
            any_nonzero = False
            for model in MODELS:
                results = all_data[model]
                da = results.get(("Phase2", f"{actor_a}_Suspected"), {})
                db = results.get(("Phase2", f"{actor_b}_Suspected"), {})
                na, nb = da.get("_total", 0), db.get("_total", 0)
                ra = rate(da.get(ind, 0), na)
                rb = rate(db.get(ind, 0), nb)
                if ra > 0 or rb > 0:
                    any_nonzero = True
                ra_s = f"{ra:.1f}%" if na else "—"
                rb_s = f"{rb:.1f}%" if nb else "—"
                r_s = ratio_str(ra, rb) if (na and nb) else "—"
                row += f" {ra_s} | {rb_s} | {r_s} |"
            if any_nonzero:
                lines.append(row)
        lines.append("")

    # Cross-model summary table
    lines.append("## Cross-Model Summary — Phase 2 China/Russia Ratio (Confirmed)")
    lines.append("")
    lines.append("Does any model show China-specific diplomatic framing?")
    lines.append("")
    hdr = "| Indicator |"
    sep = "|---|"
    for model in MODELS:
        short = MODEL_SHORT[model]
        hdr += f" {short} CN | {short} RU | {short} Ratio |"
        sep += "---|---|---|"
    lines.append(hdr)
    lines.append(sep)

    for ind in indicator_names:
        row = f"| {ind.replace('_', ' ')} |"
        any_nonzero = False
        for model in MODELS:
            results = all_data[model]
            cn = results.get(("Phase2", "China_Confirmed"), {})
            ru = results.get(("Phase2", "Russia_Confirmed"), {})
            cn_n, ru_n = cn.get("_total", 0), ru.get("_total", 0)
            cn_r = rate(cn.get(ind, 0), cn_n)
            ru_r = rate(ru.get(ind, 0), ru_n)
            if cn_r > 0 or ru_r > 0:
                any_nonzero = True
            cn_s = f"{cn_r:.1f}%" if cn_n else "—"
            ru_s = f"{ru_r:.1f}%" if ru_n else "—"
            r_s = ratio_str(cn_r, ru_r) if (cn_n and ru_n) else "—"
            row += f" {cn_s} | {ru_s} | {r_s} |"
        if any_nonzero:
            lines.append(row)
    lines.append("")

    # Caveats
    lines.append("## Caveats")
    lines.append("")
    lines.append("- **deepseek-r1 Phase 2 sample size:** Only ~29 records/condition (319 total).")
    lines.append("  Results are directional only — not definitive. Percentage swings are expected")
    lines.append("  with samples this small.")
    lines.append("- **Regex matching:** Rates are regex-based and may differ from manual Phase 1 analysis.")
    lines.append("  The script's Phase 1 numbers are the ground truth for consistent cross-phase comparison.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Generated by `scripts/finding4_crossphase.py`*")
    lines.append("")

    with open(REPORT_OUT, "w") as f:
        f.write("\n".join(lines))

    print(f"Report written: {REPORT_OUT}")


if __name__ == "__main__":
    main()
