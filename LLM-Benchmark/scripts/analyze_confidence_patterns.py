#!/usr/bin/env python3
"""
analyze_confidence_patterns.py

Detect and quantify rhetorical pattern categories in confidence assessment
sections of LLM benchmark outputs. Defines a 5-category taxonomy of hedging
patterns, applies regex detection, and tests for actor symmetry / certainty
calibration / temperature effects.

Usage:
  python3 scripts/analyze_confidence_patterns.py \
    --flat results/Phase_2/qwen3-thinking/qwen3_flat.csv \
    --outdir results/Phase_2/qwen3-thinking/confidence_patterns
"""

from __future__ import annotations

import argparse
import csv
import math
import os
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Statistical helpers (duplicated from analyze_results.py for standalone use)
# ---------------------------------------------------------------------------

def cohen_d(x: List[float], y: List[float]) -> Optional[float]:
    if len(x) < 2 or len(y) < 2:
        return None
    mx, my = sum(x) / len(x), sum(y) / len(y)
    vx = sum((v - mx) ** 2 for v in x) / (len(x) - 1)
    vy = sum((v - my) ** 2 for v in y) / (len(y) - 1)
    denom = len(x) + len(y) - 2
    pooled = math.sqrt(((len(x) - 1) * vx + (len(y) - 1) * vy) / denom) if denom else 0.0
    if pooled == 0:
        return None
    return (mx - my) / pooled


def normal_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def t_test_welch(x: List[float], y: List[float]) -> Tuple[Optional[float], Optional[float]]:
    if len(x) < 2 or len(y) < 2:
        return None, None
    mx, my = sum(x) / len(x), sum(y) / len(y)
    vx = sum((v - mx) ** 2 for v in x) / (len(x) - 1)
    vy = sum((v - my) ** 2 for v in y) / (len(y) - 1)
    denom = math.sqrt(vx / len(x) + vy / len(y))
    if denom == 0:
        return None, None
    t = (mx - my) / denom
    p = 2.0 * (1.0 - normal_cdf(abs(t)))
    return t, p


# ---------------------------------------------------------------------------
# Pattern taxonomy
# ---------------------------------------------------------------------------

PATTERN_TAXONOMY: Dict[str, Dict[str, str]] = {
    "evidence_qualification": {
        "definitive attribution requires": r"definitive\s+attribution\s+requires",
        "attribution remains probabilistic": r"attribution\s+remains\s+probabilistic",
        "absence of direct attribution": r"absence\s+of\s+direct\s+attribution",
        "reliance on indirect indicators": r"reliance\s+on\s+indirect",
        "circumstantial evidence": r"circumstantial\s+evidence",
        "definitive proof remains": r"definitive\s+proof\s+remains",
    },
    "misattribution_caveats": {
        "potential for misattribution": r"potential\s+for\s+misattribution",
        "alternative explanations": r"alternative\s+explanations?",
        "cannot be ruled out": r"cannot\s+be\s+ruled\s+out",
        "false flag": r"false[\s-]flags?",
        "false positive": r"false[\s-]positives?",
        "planted evidence": r"planted\s+evidence",
    },
    "corroboration_demands": {
        "further corroboration": r"further\s+corroboration",
        "further analysis": r"further\s+analysis",
        "further investigation": r"further\s+investigation",
        "independent verification": r"independent\s+verification",
        "additional intelligence": r"additional\s+intelligence",
        "corroborated by": r"corroborated\s+by",
    },
    "contextual_support": {
        "geopolitical context": r"geopolitical\s+context",
        "historical patterns": r"historical\s+patterns?",
        "consistent with known": r"consistent\s+with\s+known",
        "aligns with capabilities": r"aligns?\s+with\s+.*?capabilities",
        "does not replace concrete": r"do(?:es)?\s+not\s+replace\s+concrete",
    },
    "procedural_hedges": {
        "further analysis to rule out": r"further\s+analysis\s+to\s+rule\s+out",
        "ongoing monitoring": r"ongoing\s+monitoring",
        "reassessment": r"reassessment",
        "pending additional": r"pending\s+additional",
        "subject to revision": r"subject\s+to\s+revision",
    },
}

CATEGORY_DESCRIPTIONS = {
    "evidence_qualification": "Evidence-qualification hedges — statements that evidence is insufficient for definitive attribution",
    "misattribution_caveats": "Misattribution / alternative-explanation caveats — warnings about false attribution or alternative actors",
    "corroboration_demands": "Corroboration demands — calls for further analysis or independent verification",
    "contextual_support": "Contextual-support appeals — geopolitical context supports but doesn't prove attribution",
    "procedural_hedges": "Procedural hedges — generic analytical caution about process",
}

# Compiled regexes
COMPILED_PATTERNS: Dict[str, Dict[str, re.Pattern]] = {}
for cat, patterns in PATTERN_TAXONOMY.items():
    COMPILED_PATTERNS[cat] = {name: re.compile(regex, re.IGNORECASE) for name, regex in patterns.items()}

ACTORS = ["China", "Russia", "US", "Iran", "DPRK"]
LEVELS = ["Suspected", "Confirmed"]
TEMPERATURES = [0.0, 0.7]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(flat_path: str) -> List[dict]:
    """Load CSV and return list of record dicts with ok==True."""
    rows = []
    with open(flat_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("ok") == "True":
                rows.append(row)
    return rows


def parse_condition(condition: str) -> Tuple[Optional[str], Optional[str]]:
    """Parse condition like 'China_Confirmed' into (actor, level). Returns (None, None) for Neutral."""
    if condition == "Neutral":
        return None, None
    parts = condition.split("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return None, None


# ---------------------------------------------------------------------------
# Pattern detection
# ---------------------------------------------------------------------------

def detect_patterns(text: str) -> Dict[str, Dict[str, bool]]:
    """For each category, return which patterns matched."""
    results = {}
    t = text or ""
    for cat, patterns in COMPILED_PATTERNS.items():
        results[cat] = {name: bool(pat.search(t)) for name, pat in patterns.items()}
    return results


def category_binary(detection: Dict[str, Dict[str, bool]]) -> Dict[str, int]:
    """1 if any pattern in category matched, 0 otherwise."""
    return {cat: int(any(hits.values())) for cat, hits in detection.items()}


def category_count(detection: Dict[str, Dict[str, bool]]) -> Dict[str, int]:
    """Count of matched patterns within category."""
    return {cat: sum(hits.values()) for cat, hits in detection.items()}


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

def compute_rates_by_condition(records: List[dict]) -> List[dict]:
    """Compute category hit rates per condition × temperature."""
    groups: Dict[Tuple[str, float], List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        cond = rec["condition"]
        temp = float(rec["temperature"])
        det = detect_patterns(rec.get("confidence_assessment", ""))
        binary = category_binary(det)
        groups[(cond, temp)].append(binary)

    rows = []
    for (cond, temp), binaries in sorted(groups.items()):
        n = len(binaries)
        row = {"condition": cond, "temperature": temp, "n": n}
        for cat in PATTERN_TAXONOMY:
            hits = sum(b[cat] for b in binaries)
            row[f"{cat}_rate"] = round(hits / n, 4) if n else 0
            row[f"{cat}_count"] = hits
        rows.append(row)
    return rows


def compute_rates_by_actor_level(records: List[dict]) -> List[dict]:
    """Compute category rates grouped by actor × level (all temperatures combined)."""
    groups: Dict[Tuple[str, str], List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        actor, level = parse_condition(rec["condition"])
        if actor is None:
            continue
        det = detect_patterns(rec.get("confidence_assessment", ""))
        binary = category_binary(det)
        groups[(actor, level)].append(binary)

    rows = []
    for (actor, level), binaries in sorted(groups.items()):
        n = len(binaries)
        row = {"actor": actor, "level": level, "n": n}
        for cat in PATTERN_TAXONOMY:
            hits = sum(b[cat] for b in binaries)
            row[f"{cat}_rate"] = round(hits / n, 4) if n else 0
            row[f"{cat}_count"] = hits
        rows.append(row)
    return rows


def compute_pairwise_tests(records: List[dict]) -> List[dict]:
    """Pairwise Welch's t-test + Cohen's d for every actor pair at Confirmed level, per category."""
    # Build per-actor binary lists at Confirmed
    actor_data: Dict[str, List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        actor, level = parse_condition(rec["condition"])
        if actor and level == "Confirmed":
            det = detect_patterns(rec.get("confidence_assessment", ""))
            binary = category_binary(det)
            actor_data[actor].append(binary)

    rows = []
    for i, a1 in enumerate(ACTORS):
        for a2 in ACTORS[i + 1:]:
            for cat in PATTERN_TAXONOMY:
                x = [b[cat] for b in actor_data.get(a1, [])]
                y = [b[cat] for b in actor_data.get(a2, [])]
                t_stat, p_val = t_test_welch(x, y)
                d = cohen_d(x, y)
                rows.append({
                    "actor_1": a1,
                    "actor_2": a2,
                    "category": cat,
                    "n_1": len(x),
                    "n_2": len(y),
                    "mean_1": round(sum(x) / len(x), 4) if x else None,
                    "mean_2": round(sum(y) / len(y), 4) if y else None,
                    "t_stat": round(t_stat, 4) if t_stat is not None else None,
                    "p_value": round(p_val, 6) if p_val is not None else None,
                    "cohen_d": round(d, 4) if d is not None else None,
                    "significant_005": "yes" if p_val is not None and p_val < 0.05 else "no",
                })
    return rows


def compute_certainty_tests(records: List[dict]) -> List[dict]:
    """Suspected vs Confirmed shift per actor, per category."""
    groups: Dict[Tuple[str, str], List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        actor, level = parse_condition(rec["condition"])
        if actor:
            det = detect_patterns(rec.get("confidence_assessment", ""))
            binary = category_binary(det)
            groups[(actor, level)].append(binary)

    rows = []
    for actor in ACTORS:
        for cat in PATTERN_TAXONOMY:
            susp = [b[cat] for b in groups.get((actor, "Suspected"), [])]
            conf = [b[cat] for b in groups.get((actor, "Confirmed"), [])]
            t_stat, p_val = t_test_welch(susp, conf)
            d = cohen_d(susp, conf)
            rows.append({
                "actor": actor,
                "category": cat,
                "n_suspected": len(susp),
                "n_confirmed": len(conf),
                "rate_suspected": round(sum(susp) / len(susp), 4) if susp else None,
                "rate_confirmed": round(sum(conf) / len(conf), 4) if conf else None,
                "t_stat": round(t_stat, 4) if t_stat is not None else None,
                "p_value": round(p_val, 6) if p_val is not None else None,
                "cohen_d": round(d, 4) if d is not None else None,
                "significant_005": "yes" if p_val is not None and p_val < 0.05 else "no",
            })
    return rows


def compute_china_vs_rest(records: List[dict]) -> List[dict]:
    """China vs mean of other actors at Confirmed level, per category."""
    actor_data: Dict[str, List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        actor, level = parse_condition(rec["condition"])
        if actor and level == "Confirmed":
            det = detect_patterns(rec.get("confidence_assessment", ""))
            binary = category_binary(det)
            actor_data[actor].append(binary)

    rows = []
    china = actor_data.get("China", [])
    rest = []
    for a in ACTORS:
        if a != "China":
            rest.extend(actor_data.get(a, []))

    for cat in PATTERN_TAXONOMY:
        x = [b[cat] for b in china]
        y = [b[cat] for b in rest]
        t_stat, p_val = t_test_welch(x, y)
        d = cohen_d(x, y)
        rows.append({
            "category": cat,
            "china_n": len(x),
            "rest_n": len(y),
            "china_rate": round(sum(x) / len(x), 4) if x else None,
            "rest_rate": round(sum(y) / len(y), 4) if y else None,
            "t_stat": round(t_stat, 4) if t_stat is not None else None,
            "p_value": round(p_val, 6) if p_val is not None else None,
            "cohen_d": round(d, 4) if d is not None else None,
            "significant_005": "yes" if p_val is not None and p_val < 0.05 else "no",
        })
    return rows


def compute_temperature_tests(records: List[dict]) -> List[dict]:
    """T=0.0 vs T=0.7 at Confirmed level (all actors pooled), per category."""
    temp_data: Dict[float, List[Dict[str, int]]] = defaultdict(list)
    for rec in records:
        actor, level = parse_condition(rec["condition"])
        if actor and level == "Confirmed":
            temp = float(rec["temperature"])
            det = detect_patterns(rec.get("confidence_assessment", ""))
            binary = category_binary(det)
            temp_data[temp].append(binary)

    rows = []
    for cat in PATTERN_TAXONOMY:
        x = [b[cat] for b in temp_data.get(0.0, [])]
        y = [b[cat] for b in temp_data.get(0.7, [])]
        t_stat, p_val = t_test_welch(x, y)
        d = cohen_d(x, y)
        rows.append({
            "category": cat,
            "n_t0": len(x),
            "n_t07": len(y),
            "rate_t0": round(sum(x) / len(x), 4) if x else None,
            "rate_t07": round(sum(y) / len(y), 4) if y else None,
            "t_stat": round(t_stat, 4) if t_stat is not None else None,
            "p_value": round(p_val, 6) if p_val is not None else None,
            "cohen_d": round(d, 4) if d is not None else None,
            "significant_005": "yes" if p_val is not None and p_val < 0.05 else "no",
        })
    return rows


def collect_examples(records: List[dict], max_per_cat: int = 3) -> List[dict]:
    """Collect example text snippets per category."""
    examples: Dict[str, List[dict]] = {cat: [] for cat in PATTERN_TAXONOMY}
    for rec in records:
        text = rec.get("confidence_assessment", "")
        if not text:
            continue
        det = detect_patterns(text)
        for cat, hits in det.items():
            if len(examples[cat]) >= max_per_cat:
                continue
            if any(hits.values()):
                matched = [name for name, hit in hits.items() if hit]
                examples[cat].append({
                    "category": cat,
                    "condition": rec["condition"],
                    "temperature": rec["temperature"],
                    "matched_patterns": "; ".join(matched),
                    "text_snippet": text[:500],
                })
    rows = []
    for cat in PATTERN_TAXONOMY:
        rows.extend(examples[cat])
    return rows


# ---------------------------------------------------------------------------
# N-gram discovery (model-specific vocabulary)
# ---------------------------------------------------------------------------

# Build a set of all taxonomy pattern words for filtering
_TAXONOMY_WORDS: set = set()
for _cat, _pats in PATTERN_TAXONOMY.items():
    for _name in _pats:
        _TAXONOMY_WORDS.update(_name.lower().split())

_STOPWORDS = {
    "the", "a", "an", "of", "to", "in", "for", "and", "or", "is", "are",
    "was", "were", "be", "been", "being", "that", "this", "these", "those",
    "it", "its", "with", "as", "at", "by", "on", "from", "but", "not",
    "no", "if", "may", "can", "will", "should", "would", "could", "has",
    "have", "had", "do", "does", "did", "than", "more", "most", "such",
    "also", "any", "all", "each", "both", "other", "some", "their", "there",
    "they", "them", "we", "our", "which", "who", "whom", "what", "where",
    "when", "how", "about", "between", "through", "during", "before",
    "after", "above", "below", "up", "down", "out", "off", "over", "under",
    "again", "then", "once", "here", "why", "so", "very", "just", "only",
    "own", "same", "into", "while", "because", "against", "however",
}


def extract_ngrams(text: str, n: int) -> List[str]:
    """Extract word n-grams from text, filtering stopwords at edges."""
    words = re.findall(r"[a-z]+", text.lower())
    ngrams = []
    for i in range(len(words) - n + 1):
        gram = words[i:i + n]
        # Skip if first or last word is a stopword
        if gram[0] in _STOPWORDS or gram[-1] in _STOPWORDS:
            continue
        ngrams.append(" ".join(gram))
    return ngrams


def discover_ngrams(records: List[dict], top_k: int = 30) -> List[dict]:
    """Find frequent 2-4 word n-grams NOT covered by taxonomy patterns."""
    # Flatten all taxonomy regex patterns into a combined match set
    all_compiled = []
    for cat, pats in COMPILED_PATTERNS.items():
        for name, pat in pats.items():
            all_compiled.append(pat)

    counter: Counter = Counter()
    doc_count: Counter = Counter()  # how many records contain each n-gram
    total_docs = 0

    for rec in records:
        text = rec.get("confidence_assessment", "")
        if not text:
            continue
        total_docs += 1
        seen_in_doc: set = set()
        for n in (2, 3, 4):
            for gram in extract_ngrams(text, n):
                counter[gram] += 1
                if gram not in seen_in_doc:
                    doc_count[gram] += 1
                    seen_in_doc.add(gram)

    # Filter: remove n-grams that match any taxonomy pattern
    filtered = []
    for gram, count in counter.most_common(top_k * 5):
        # Check if this gram is just a substring of a taxonomy pattern
        is_taxonomy = False
        for pat in all_compiled:
            if pat.search(gram):
                is_taxonomy = True
                break
        if is_taxonomy:
            continue
        # Require minimum document frequency
        if doc_count[gram] < 5:
            continue
        filtered.append({
            "ngram": gram,
            "raw_count": count,
            "doc_count": doc_count[gram],
            "doc_rate": round(doc_count[gram] / total_docs, 4) if total_docs else 0,
        })
        if len(filtered) >= top_k:
            break

    return filtered


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def generate_report(
    rates_by_actor: List[dict],
    pairwise: List[dict],
    certainty: List[dict],
    china_vs_rest: List[dict],
    temperature: List[dict],
    total_records: int,
    model_label: str = "unknown",
) -> str:
    """Generate markdown summary report."""
    lines = [
        "# Confidence Assessment Rhetorical Pattern Analysis",
        "",
        f"**Records analysed:** {total_records} ({model_label}, ok==True)",
        f"**Categories:** {len(PATTERN_TAXONOMY)}",
        f"**Total patterns:** {sum(len(p) for p in PATTERN_TAXONOMY.values())}",
        "",
        "---",
        "",
        "## 1. Taxonomy",
        "",
        "| Category | Description | Patterns |",
        "|----------|-------------|----------|",
    ]
    for cat, desc in CATEGORY_DESCRIPTIONS.items():
        n = len(PATTERN_TAXONOMY[cat])
        lines.append(f"| {cat} | {desc} | {n} |")

    lines.extend(["", "---", "", "## 2. Detection rates by actor × level", ""])
    lines.append("| Actor | Level | N | " + " | ".join(PATTERN_TAXONOMY.keys()) + " |")
    lines.append("|" + "---|" * (3 + len(PATTERN_TAXONOMY)))
    for row in rates_by_actor:
        vals = " | ".join(f"{row[f'{cat}_rate']:.1%}" for cat in PATTERN_TAXONOMY)
        lines.append(f"| {row['actor']} | {row['level']} | {row['n']} | {vals} |")

    lines.extend(["", "---", "", "## 3. Actor pairwise tests (Confirmed level)", ""])
    lines.append("| Actor pair | Category | d | p | Sig? |")
    lines.append("|---|---|---|---|---|")
    sig_count = 0
    for row in pairwise:
        d_str = f"{row['cohen_d']:.3f}" if row["cohen_d"] is not None else "—"
        p_str = f"{row['p_value']:.4f}" if row["p_value"] is not None else "—"
        sig = row["significant_005"]
        if sig == "yes":
            sig_count += 1
        lines.append(f"| {row['actor_1']} vs {row['actor_2']} | {row['category']} | {d_str} | {p_str} | {sig} |")
    total_tests = len(pairwise)
    lines.extend([
        "",
        f"**Summary:** {sig_count}/{total_tests} tests significant at p<0.05.",
        "",
    ])

    lines.extend(["---", "", "## 4. Certainty calibration (Suspected vs Confirmed)", ""])
    lines.append("| Actor | Category | Suspected rate | Confirmed rate | d | p | Sig? |")
    lines.append("|---|---|---|---|---|---|---|")
    for row in certainty:
        sr = f"{row['rate_suspected']:.1%}" if row["rate_suspected"] is not None else "—"
        cr = f"{row['rate_confirmed']:.1%}" if row["rate_confirmed"] is not None else "—"
        d_str = f"{row['cohen_d']:.3f}" if row["cohen_d"] is not None else "—"
        p_str = f"{row['p_value']:.4f}" if row["p_value"] is not None else "—"
        lines.append(f"| {row['actor']} | {row['category']} | {sr} | {cr} | {d_str} | {p_str} | {row['significant_005']} |")

    lines.extend(["", "---", "", "## 5. China vs rest (Confirmed level)", ""])
    lines.append("| Category | China rate | Rest rate | d | p | Sig? |")
    lines.append("|---|---|---|---|---|---|")
    for row in china_vs_rest:
        cr = f"{row['china_rate']:.1%}" if row["china_rate"] is not None else "—"
        rr = f"{row['rest_rate']:.1%}" if row["rest_rate"] is not None else "—"
        d_str = f"{row['cohen_d']:.3f}" if row["cohen_d"] is not None else "—"
        p_str = f"{row['p_value']:.4f}" if row["p_value"] is not None else "—"
        lines.append(f"| {row['category']} | {cr} | {rr} | {d_str} | {p_str} | {row['significant_005']} |")

    lines.extend(["", "---", "", "## 6. Temperature effect (Confirmed, all actors)", ""])
    lines.append("| Category | T=0.0 rate | T=0.7 rate | d | p | Sig? |")
    lines.append("|---|---|---|---|---|---|")
    for row in temperature:
        t0 = f"{row['rate_t0']:.1%}" if row["rate_t0"] is not None else "—"
        t07 = f"{row['rate_t07']:.1%}" if row["rate_t07"] is not None else "—"
        d_str = f"{row['cohen_d']:.3f}" if row["cohen_d"] is not None else "—"
        p_str = f"{row['p_value']:.4f}" if row["p_value"] is not None else "—"
        lines.append(f"| {row['category']} | {t0} | {t07} | {d_str} | {p_str} | {row['significant_005']} |")

    lines.extend(["", "---", ""])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CSV output helpers
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
    parser = argparse.ArgumentParser(description="Analyse confidence assessment rhetorical patterns")
    parser.add_argument("--flat", required=True, help="Path to flat CSV")
    parser.add_argument("--outdir", required=True, help="Output directory")
    parser.add_argument("--model-label", default=None, help="Model label for report headers (default: inferred from CSV path)")
    args = parser.parse_args()

    # Infer model label from path if not provided
    model_label = args.model_label
    if not model_label:
        base = os.path.basename(args.flat).replace("_flat.csv", "")
        model_label = base

    print(f"Loading data from {args.flat}...")
    records = load_data(args.flat)
    print(f"  {len(records)} ok records loaded.")

    print("Computing rates by condition × temperature...")
    rates_cond = compute_rates_by_condition(records)

    print("Computing rates by actor × level...")
    rates_actor = compute_rates_by_actor_level(records)

    print("Computing pairwise actor tests (Confirmed)...")
    pairwise = compute_pairwise_tests(records)

    print("Computing certainty calibration tests...")
    certainty = compute_certainty_tests(records)

    print("Computing China-vs-rest tests...")
    china_rest = compute_china_vs_rest(records)

    print("Computing temperature tests...")
    temperature = compute_temperature_tests(records)

    print("Collecting examples...")
    examples = collect_examples(records)

    print("Discovering model-specific n-grams...")
    ngrams = discover_ngrams(records, top_k=30)

    print("Generating report...")
    report = generate_report(rates_actor, pairwise, certainty, china_rest, temperature, len(records), model_label=model_label)

    # Write outputs
    os.makedirs(args.outdir, exist_ok=True)
    write_csv(os.path.join(args.outdir, "pattern_rates_by_condition.csv"), rates_cond)
    write_csv(os.path.join(args.outdir, "pattern_rates_by_actor_level.csv"), rates_actor)
    write_csv(os.path.join(args.outdir, "pattern_pairwise_tests.csv"), pairwise)
    write_csv(os.path.join(args.outdir, "pattern_certainty_tests.csv"), certainty)
    write_csv(os.path.join(args.outdir, "pattern_examples.csv"), examples)
    write_csv(os.path.join(args.outdir, "pattern_ngram_discovery.csv"), ngrams)

    report_path = os.path.join(args.outdir, "confidence_pattern_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\nOutputs written to {args.outdir}/")
    for fn in [
        "pattern_rates_by_condition.csv",
        "pattern_rates_by_actor_level.csv",
        "pattern_pairwise_tests.csv",
        "pattern_certainty_tests.csv",
        "pattern_examples.csv",
        "pattern_ngram_discovery.csv",
        "confidence_pattern_report.md",
    ]:
        path = os.path.join(args.outdir, fn)
        if os.path.exists(path):
            print(f"  ✓ {fn}")
        else:
            print(f"  ✗ {fn} MISSING")

    # Print quick summary
    print("\n--- Quick summary ---")
    sig_pairwise = sum(1 for r in pairwise if r["significant_005"] == "yes")
    print(f"Pairwise actor tests: {sig_pairwise}/{len(pairwise)} significant at p<0.05")
    sig_cert = sum(1 for r in certainty if r["significant_005"] == "yes")
    print(f"Certainty calibration: {sig_cert}/{len(certainty)} significant")
    sig_china = sum(1 for r in china_rest if r["significant_005"] == "yes")
    print(f"China-vs-rest: {sig_china}/{len(china_rest)} significant")
    sig_temp = sum(1 for r in temperature if r["significant_005"] == "yes")
    print(f"Temperature effect: {sig_temp}/{len(temperature)} significant")
    print(f"N-gram discovery: {len(ngrams)} non-taxonomy n-grams found")


if __name__ == "__main__":
    main()
