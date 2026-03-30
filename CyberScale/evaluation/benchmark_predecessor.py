#!/usr/bin/env python3
"""Benchmark Phase 2 contextual model against CVE-Severity-Context predecessor dataset.

Parses all 1,890 markdown scenario files from the predecessor project,
maps old sector names to CyberScale's 19 NIS2 sectors, runs predictions,
and compares accuracy against Variant F baseline (80.7%).

Usage:
    poetry run python evaluation/benchmark_predecessor.py \
        --scenarios ../CVE-Severity-Context/Dataset/Scenarios \
        --model data/models/contextual \
        --output evaluation/predecessor_benchmark.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# Sector mapping: old project names → CyberScale VALID_SECTORS
# ---------------------------------------------------------------------------

SECTOR_MAP = {
    # Exact matches (lowercase)
    "energy": "energy",
    "transport": "transport",
    "banking": "banking",
    "health": "health",
    "healthcare": "health",
    "manufacturing": "manufacturing",
    "water": "drinking_water",
    "water supply": "drinking_water",
    "water utility": "drinking_water",
    # Title case
    "Energy": "energy",
    "Transport": "transport",
    "Banking": "banking",
    "Health": "health",
    "Healthcare": "health",
    "Manufacturing": "manufacturing",
    "Water": "drinking_water",
    "Technology": "non_nis2",
    "Technology distribution": "non_nis2",
    "Consumer": "non_nis2",
    "Personal": "non_nis2",
    "Personal use": "non_nis2",
    "personal use": "non_nis2",
    "General": "non_nis2",
    "General commercial": "non_nis2",
    "General consumer": "non_nis2",
    "General enterprise": "non_nis2",
    # Digital infrastructure variants
    "Digital infrastructure": "digital_infrastructure",
    "Digital Infrastructure": "digital_infrastructure",
    "digital infrastructure": "digital_infrastructure",
    "digital-infrastructure": "digital_infrastructure",
    "digital infrastructure provider": "digital_infrastructure",
    "Cloud infrastructure management": "digital_infrastructure",
    # Digital providers
    "Digital providers": "digital_providers",
    "Digital Providers": "digital_providers",
    "Digital services / Consumer platform": "digital_providers",
    "Digital services / Consumer software": "digital_providers",
    # ICT service management
    "ICT service management": "ict_service_management",
    "ICT Service Management": "ict_service_management",
    # Public administration
    "Public administration": "public_administration",
    "Public Administration": "public_administration",
    "public administration": "public_administration",
    "public-admin": "public_administration",
    "Defense and public administration": "public_administration",
    # Banking/financial
    "banking and financial": "banking",
    "Banking and financial market infrastructure": "financial_market",
    "Financial services / Enterprise integration": "financial_market",
    "Financial services / Fintech": "financial_market",
    # Enterprise / small / misc → non_nis2
    "Enterprise": "non_nis2",
    "enterprise": "non_nis2",
    "Enterprise IT": "non_nis2",
    "enterprise IT": "non_nis2",
    "E-commerce": "non_nis2",
    "Small Business": "non_nis2",
    "Small business": "non_nis2",
    "small business": "non_nis2",
    "small-deployment": "non_nis2",
    "small office": "non_nis2",
    "Professional Services": "non_nis2",
    "Professional services": "non_nis2",
    "Commercial enterprise": "non_nis2",
    "Telecommunications": "digital_infrastructure",
    "Building automation / HVAC": "manufacturing",
    "N/A": "non_nis2",
    # Scenario-type based sectors (from scenario_type field)
    "energy utility": "energy",
    "rail operator": "transport",
}

VALID_SEVERITIES = {"Critical", "High", "Medium", "Low"}


def parse_yaml_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from markdown text."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return None

    yaml_text = match.group(1)
    data = {}
    current_key = None
    list_mode = False

    for line in yaml_text.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith("- ") and list_mode:
            if current_key:
                if current_key not in data:
                    data[current_key] = []
                data[current_key].append(stripped[2:].strip().strip('"'))
            continue

        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1 :].strip()

            if not value:
                current_key = key
                list_mode = True
                continue

            list_mode = False
            current_key = key
            value = value.strip('"').strip("'")

            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.lower() in ("null", "none", "~"):
                value = None
            elif re.match(r"^-?\d+\.?\d*$", value):
                try:
                    value = float(value) if "." in value else int(value)
                except ValueError:
                    pass

            data[key] = value

    return data


def map_sector(raw_sector: str, scenario_type: str | None = None) -> str | None:
    """Map old sector name to CyberScale sector. Returns None if unmappable."""
    if raw_sector in SECTOR_MAP:
        return SECTOR_MAP[raw_sector]

    # Try lowercase
    if raw_sector.lower() in SECTOR_MAP:
        return SECTOR_MAP[raw_sector.lower()]

    # Infer from scenario_type
    scenario_sector_map = {
        "cross-border": "ict_service_management",
        "digital-infrastructure": "digital_infrastructure",
        "energy": "energy",
        "health": "health",
        "enterprise": "non_nis2",
        "small-deployment": "non_nis2",
        "public-admin": "public_administration",
        "banking": "banking",
        "transport": "transport",
        "manufacturing": "manufacturing",
        "water": "drinking_water",
        "essential-service": None,  # Ambiguous — need sector field
    }
    if scenario_type and scenario_type in scenario_sector_map:
        return scenario_sector_map[scenario_type]

    return None


def load_scenarios(scenarios_dir: Path) -> list[dict]:
    """Load all scenario markdown files and extract fields."""
    records = []
    skipped = 0

    for md_file in sorted(scenarios_dir.glob("CVE-*/CVE-*.md")):
        text = md_file.read_text(encoding="utf-8")
        data = parse_yaml_frontmatter(text)
        if data is None:
            skipped += 1
            continue

        # Must have contextual_severity
        ctx_sev = data.get("contextual_severity")
        if ctx_sev not in VALID_SEVERITIES:
            skipped += 1
            continue

        # Must have description
        desc = data.get("cve_description")
        if not desc or len(str(desc)) < 20:
            skipped += 1
            continue

        # Map sector
        raw_sector = str(data.get("sector", ""))
        scenario_type = data.get("scenario_type")
        sector = map_sector(raw_sector, scenario_type)
        if sector is None:
            skipped += 1
            continue

        cross_border = data.get("cross_border", False)
        if isinstance(cross_border, str):
            cross_border = cross_border.lower() == "true"

        cvss_score = data.get("cvss_v3_base_score")
        if cvss_score is not None:
            try:
                cvss_score = float(cvss_score)
            except (ValueError, TypeError):
                cvss_score = None

        records.append(
            {
                "scenario_id": data.get("scenario_id", md_file.stem),
                "cve_id": data.get("cve_id", ""),
                "description": str(desc),
                "sector": sector,
                "raw_sector": raw_sector,
                "cross_border": cross_border,
                "cvss_score": cvss_score,
                "ground_truth": ctx_sev,
                "scenario_type": scenario_type,
            }
        )

    print(f"Loaded {len(records)} scenarios ({skipped} skipped)")
    return records


def run_benchmark(records: list[dict], model_path: Path, mc_passes: int = 5) -> list[dict]:
    """Run model predictions on all scenarios."""
    # Import here to avoid loading torch at module level
    from cyberscale.models.contextual import ContextualClassifier

    print(f"Loading model from {model_path}...")
    clf = ContextualClassifier(model_path=model_path, mc_passes=mc_passes)
    print(f"Model loaded on {clf.device}")

    results = []
    for i, rec in enumerate(records):
        result = clf.predict(
            description=rec["description"],
            sector=rec["sector"],
            cross_border=rec["cross_border"],
            score=rec["cvss_score"],
        )
        rec["predicted"] = result.severity
        rec["confidence"] = result.confidence
        rec["correct"] = result.severity == rec["ground_truth"]
        results.append(rec)

        if (i + 1) % 100 == 0:
            acc_so_far = sum(r["correct"] for r in results) / len(results)
            print(f"  {i + 1}/{len(records)} — running accuracy: {acc_so_far:.1%}")

    return results


def compute_metrics(results: list[dict]) -> dict:
    """Compute accuracy metrics from benchmark results."""
    total = len(results)
    correct = sum(r["correct"] for r in results)
    accuracy = correct / total if total > 0 else 0

    # Per-severity
    per_severity = {}
    for sev in ["Critical", "High", "Medium", "Low"]:
        subset = [r for r in results if r["ground_truth"] == sev]
        if subset:
            per_severity[sev] = {
                "total": len(subset),
                "correct": sum(r["correct"] for r in subset),
                "accuracy": sum(r["correct"] for r in subset) / len(subset),
            }

    # Per-sector
    per_sector = {}
    for sector in sorted(set(r["sector"] for r in results)):
        subset = [r for r in results if r["sector"] == sector]
        if subset:
            per_sector[sector] = {
                "total": len(subset),
                "correct": sum(r["correct"] for r in subset),
                "accuracy": sum(r["correct"] for r in subset) / len(subset),
            }

    # Per-scenario-type
    per_scenario = {}
    for st in sorted(set(r["scenario_type"] for r in results if r["scenario_type"])):
        subset = [r for r in results if r["scenario_type"] == st]
        if subset:
            per_scenario[st] = {
                "total": len(subset),
                "correct": sum(r["correct"] for r in subset),
                "accuracy": sum(r["correct"] for r in subset) / len(subset),
            }

    # Confusion matrix
    confusion = defaultdict(lambda: defaultdict(int))
    for r in results:
        confusion[r["ground_truth"]][r["predicted"]] += 1

    # Confidence distribution
    conf_dist = Counter(r["confidence"] for r in results)

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_severity": per_severity,
        "per_sector": per_sector,
        "per_scenario_type": per_scenario,
        "confusion": {k: dict(v) for k, v in confusion.items()},
        "confidence_distribution": dict(conf_dist),
    }


def generate_report(metrics: dict, variant_f_accuracy: float = 0.807) -> str:
    """Generate markdown benchmark report."""
    m = metrics
    delta = m["accuracy"] - variant_f_accuracy
    delta_str = f"+{delta:.1%}" if delta >= 0 else f"{delta:.1%}"
    target_met = abs(m["accuracy"] - variant_f_accuracy) <= 0.05 or m["accuracy"] >= variant_f_accuracy

    lines = [
        "# Phase 2 Predecessor Benchmark Report",
        "",
        f"**Date:** 2026-03-28",
        f"**Dataset:** CVE-Severity-Context (1,890 human-curated scenarios)",
        f"**Model:** CyberScale contextual-v1 (ModernBERT-base, 4-class)",
        f"**MC Dropout passes:** 5 (reduced for benchmark speed)",
        "",
        "---",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Scenarios evaluated | {m['total']} |",
        f"| Overall accuracy | **{m['accuracy']:.1%}** |",
        f"| Variant F baseline | {variant_f_accuracy:.1%} |",
        f"| Delta | {delta_str} |",
        f"| Target (within 5pp) | {'MET' if target_met else 'NOT MET'} |",
        "",
        "---",
        "",
        "## Per-severity accuracy",
        "",
        "| Severity | Total | Correct | Accuracy |",
        "|----------|-------|---------|----------|",
    ]

    for sev in ["Critical", "High", "Medium", "Low"]:
        if sev in m["per_severity"]:
            s = m["per_severity"][sev]
            lines.append(f"| {sev} | {s['total']} | {s['correct']} | {s['accuracy']:.1%} |")

    lines += [
        "",
        "---",
        "",
        "## Per-sector accuracy",
        "",
        "| Sector | Total | Correct | Accuracy |",
        "|--------|-------|---------|----------|",
    ]

    for sector, s in sorted(m["per_sector"].items(), key=lambda x: -x[1]["accuracy"]):
        lines.append(f"| {sector} | {s['total']} | {s['correct']} | {s['accuracy']:.1%} |")

    lines += [
        "",
        "---",
        "",
        "## Per-scenario-type accuracy",
        "",
        "| Scenario type | Total | Correct | Accuracy |",
        "|---------------|-------|---------|----------|",
    ]

    for st, s in sorted(m["per_scenario_type"].items(), key=lambda x: -x[1]["accuracy"]):
        lines.append(f"| {st} | {s['total']} | {s['correct']} | {s['accuracy']:.1%} |")

    lines += [
        "",
        "---",
        "",
        "## Confusion matrix",
        "",
        "| Ground truth \\ Predicted | Critical | High | Medium | Low |",
        "|--------------------------|----------|------|--------|-----|",
    ]

    for gt in ["Critical", "High", "Medium", "Low"]:
        row = m["confusion"].get(gt, {})
        cells = [str(row.get(p, 0)) for p in ["Critical", "High", "Medium", "Low"]]
        lines.append(f"| {gt} | {' | '.join(cells)} |")

    lines += [
        "",
        "---",
        "",
        "## Confidence distribution",
        "",
        "| Confidence | Count | Percentage |",
        "|------------|-------|------------|",
    ]

    total = m["total"]
    for conf in ["high", "medium", "low"]:
        count = m["confidence_distribution"].get(conf, 0)
        lines.append(f"| {conf} | {count} | {count / total:.1%} |")

    lines += [
        "",
        "---",
        "",
        "## Analysis",
        "",
        "This benchmark evaluates the CyberScale Phase 2 contextual severity model",
        "against the predecessor CVE-Severity-Context dataset. The predecessor used",
        "human-curated scenarios with detailed deployment context and NIS2 regulatory",
        "framework assessments.",
        "",
        "Key differences from training data:",
        "- Predecessor scenarios have rich narrative deployment contexts",
        "- Sector naming is inconsistent (mapped to CyberScale's 19 NIS2 sectors)",
        "- Cross-border scenarios always map to ICT service management (MSP context)",
        "- Some scenario types (essential-service) have ambiguous sector mapping",
        "",
    ]

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Benchmark Phase 2 against predecessor dataset")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path("../CVE-Severity-Context/Dataset/Scenarios"),
        help="Path to CVE-Severity-Context Scenarios directory",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("data/models/contextual"),
        help="Path to trained contextual model",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evaluation/predecessor_benchmark.md"),
        help="Output report path",
    )
    parser.add_argument(
        "--mc-passes",
        type=int,
        default=5,
        help="MC dropout passes (fewer = faster, default 5)",
    )
    args = parser.parse_args()

    # Load scenarios
    records = load_scenarios(args.scenarios)
    if not records:
        print("ERROR: No valid scenarios loaded")
        sys.exit(1)

    # Run benchmark
    results = run_benchmark(records, args.model, mc_passes=args.mc_passes)

    # Compute metrics
    metrics = compute_metrics(results)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"BENCHMARK RESULTS")
    print(f"{'=' * 60}")
    print(f"Scenarios:  {metrics['total']}")
    print(f"Accuracy:   {metrics['accuracy']:.1%}")
    print(f"Variant F:  80.7%")
    delta = metrics["accuracy"] - 0.807
    print(f"Delta:      {'+' if delta >= 0 else ''}{delta:.1%}")
    print(f"Target:     {'MET' if abs(delta) <= 0.05 or delta >= 0 else 'NOT MET'}")
    print(f"{'=' * 60}")

    # Generate and save report
    report = generate_report(metrics)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"\nReport saved to {args.output}")

    # Save raw metrics
    metrics_path = args.output.with_suffix(".json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2, default=str)
    print(f"Metrics saved to {metrics_path}")


if __name__ == "__main__":
    main()
