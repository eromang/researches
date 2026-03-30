#!/usr/bin/env python3
"""Mix predecessor CVE-Severity-Context data with synthetic training data.

Converts predecessor CSV rows to the same input format, oversamples to give
predecessor data proportional influence, and outputs a mixed training CSV.

Usage:
    poetry run python training/scripts/mix_predecessor.py \
        --synthetic training/data/contextual_training_v2.csv \
        --predecessor ../CVE-Severity-Context/Dataset/Export/dataset.csv \
        --predecessor-weight 0.3 \
        --output training/data/contextual_training_v3.csv
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

# Same mapping as benchmark script
SECTOR_MAP = {
    "energy": "energy", "Energy": "energy",
    "transport": "transport", "Transport": "transport",
    "banking": "banking", "Banking": "banking",
    "banking and financial": "banking",
    "Banking and financial market infrastructure": "financial_market",
    "Financial services / Enterprise integration": "financial_market",
    "Financial services / Fintech": "financial_market",
    "health": "health", "Health": "health",
    "healthcare": "health", "Healthcare": "health",
    "manufacturing": "manufacturing", "Manufacturing": "manufacturing",
    "Building automation / HVAC": "manufacturing",
    "water": "drinking_water", "Water": "drinking_water",
    "water supply": "drinking_water",
    "Digital infrastructure": "digital_infrastructure",
    "Digital Infrastructure": "digital_infrastructure",
    "digital infrastructure": "digital_infrastructure",
    "digital-infrastructure": "digital_infrastructure",
    "Cloud infrastructure management": "digital_infrastructure",
    "Telecommunications": "digital_infrastructure",
    "Digital providers": "digital_providers",
    "Digital Providers": "digital_providers",
    "Digital services / Consumer platform": "digital_providers",
    "Digital services / Consumer software": "digital_providers",
    "ICT service management": "ict_service_management",
    "ICT Service Management": "ict_service_management",
    "Public administration": "public_administration",
    "Public Administration": "public_administration",
    "public administration": "public_administration",
    "public-admin": "public_administration",
    "Defense and public administration": "public_administration",
    "Enterprise": "non_nis2", "enterprise": "non_nis2",
    "Enterprise IT": "non_nis2", "enterprise IT": "non_nis2",
    "Small Business": "non_nis2", "Small business": "non_nis2",
    "small business": "non_nis2", "small-deployment": "non_nis2",
    "small office": "non_nis2",
    "General commercial": "non_nis2", "General enterprise": "non_nis2",
    "General consumer": "non_nis2", "General": "non_nis2",
    "Consumer": "non_nis2", "Personal": "non_nis2",
    "Personal use": "non_nis2", "personal use": "non_nis2",
    "Professional Services": "non_nis2", "Professional services": "non_nis2",
    "E-commerce": "non_nis2", "Technology": "non_nis2",
    "Technology distribution": "non_nis2",
    "N/A": "non_nis2",
}

SCENARIO_TYPE_SECTOR_MAP = {
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
    "essential-service": "energy",  # Default for ambiguous essential-service
}

SEVERITY_INDEX = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}


def parse_yaml_frontmatter(text: str) -> dict | None:
    """Extract YAML frontmatter from markdown text."""
    import re
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
                data.setdefault(current_key, []).append(stripped[2:].strip().strip('"'))
            continue
        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1:].strip()
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


def convert_predecessor(predecessor_path: Path) -> list[dict]:
    """Convert predecessor scenario files to training format.

    Accepts either a CSV file or a Scenarios directory (markdown files).
    """
    if predecessor_path.is_dir():
        return _convert_from_markdown(predecessor_path)
    return _convert_from_csv(predecessor_path)


def _convert_from_markdown(scenarios_dir: Path) -> list[dict]:
    """Parse all markdown scenario files from the Scenarios directory."""
    rows = []
    skipped = 0

    for md_file in sorted(scenarios_dir.glob("CVE-*/CVE-*.md")):
        text = md_file.read_text(encoding="utf-8")
        rec = parse_yaml_frontmatter(text)
        if rec is None:
            skipped += 1
            continue

        sev = rec.get("contextual_severity")
        if sev not in SEVERITY_INDEX:
            skipped += 1
            continue

        desc = rec.get("cve_description")
        if not desc or len(str(desc)) < 20:
            skipped += 1
            continue

        raw_sector = str(rec.get("sector", ""))
        scenario_type = rec.get("scenario_type")
        sector = SECTOR_MAP.get(raw_sector)
        if sector is None and scenario_type:
            sector = SCENARIO_TYPE_SECTOR_MAP.get(scenario_type)
        if sector is None:
            skipped += 1
            continue

        try:
            score = float(rec.get("cvss_v3_base_score", 0))
        except (ValueError, TypeError):
            skipped += 1
            continue
        if score <= 0:
            skipped += 1
            continue

        cross_border = rec.get("cross_border", False)
        if isinstance(cross_border, str):
            cross_border = cross_border.lower() == "true"

        input_text = (
            f"{desc} [SEP] sector: {sector} "
            f"cross_border: {str(cross_border).lower()} "
            f"score: {score}"
        )

        rows.append({
            "cve_id": rec.get("cve_id", md_file.stem),
            "input_text": input_text,
            "sector": sector,
            "cross_border": cross_border,
            "cvss_score": score,
            "base_severity": rec.get("cvss_base_severity", ""),
            "contextual_severity": sev,
            "label": SEVERITY_INDEX[sev],
        })

    print(f"Predecessor (markdown): {len(rows)} converted, {skipped} skipped")
    return rows


def _convert_from_csv(predecessor_path: Path) -> list[dict]:
    """Convert predecessor CSV rows to training format."""
    rows = []
    skipped = 0

    with open(predecessor_path) as f:
        for rec in csv.DictReader(f):
            sev = rec["contextual_severity"]
            if sev not in SEVERITY_INDEX:
                skipped += 1
                continue

            desc = rec["cve_description"]
            if not desc or len(desc) < 20:
                skipped += 1
                continue

            raw_sector = rec["sector"]
            sector = SECTOR_MAP.get(raw_sector)
            if sector is None:
                skipped += 1
                continue

            try:
                score = float(rec["cvss_v3_base_score"])
            except (ValueError, TypeError):
                skipped += 1
                continue

            cross_border = rec["cross_border"].strip().lower() == "true"

            input_text = (
                f"{desc} [SEP] sector: {sector} "
                f"cross_border: {str(cross_border).lower()} "
                f"score: {score}"
            )

            rows.append({
                "cve_id": rec["cve_id"],
                "input_text": input_text,
                "sector": sector,
                "cross_border": cross_border,
                "cvss_score": score,
                "base_severity": rec.get("cvss_base_severity", ""),
                "contextual_severity": sev,
                "label": SEVERITY_INDEX[sev],
            })

    print(f"Predecessor (CSV): {len(rows)} converted, {skipped} skipped")
    return rows


def mix_datasets(
    synthetic_path: Path,
    predecessor_rows: list[dict],
    predecessor_weight: float,
    seed: int,
) -> list[dict]:
    """Mix synthetic and predecessor data with oversampling."""
    rng = random.Random(seed)

    # Load synthetic
    with open(synthetic_path) as f:
        synthetic = list(csv.DictReader(f))
    print(f"Synthetic: {len(synthetic)} rows")

    # Calculate oversampling factor
    # predecessor_weight = predecessor_count / (predecessor_count + synthetic_count)
    # So: predecessor_count = predecessor_weight * synthetic_count / (1 - predecessor_weight)
    target_predecessor = int(predecessor_weight * len(synthetic) / (1 - predecessor_weight))
    oversample_factor = max(1, target_predecessor // len(predecessor_rows))
    remainder = target_predecessor - oversample_factor * len(predecessor_rows)

    print(f"Oversampling predecessor {oversample_factor}x + {remainder} extra = {target_predecessor} target")

    # Oversample
    oversampled = predecessor_rows * oversample_factor
    if remainder > 0:
        oversampled += rng.sample(predecessor_rows, min(remainder, len(predecessor_rows)))

    # Convert to same dict format as synthetic CSV
    predecessor_dicts = []
    for row in oversampled:
        predecessor_dicts.append({
            "cve_id": row["cve_id"],
            "input_text": row["input_text"],
            "sector": row["sector"],
            "cross_border": row["cross_border"],
            "cvss_score": row["cvss_score"],
            "base_severity": row["base_severity"],
            "contextual_severity": row["contextual_severity"],
            "label": row["label"],
        })

    # Combine and shuffle
    mixed = synthetic + predecessor_dicts
    rng.shuffle(mixed)

    print(f"Mixed: {len(mixed)} total ({len(synthetic)} synthetic + {len(predecessor_dicts)} predecessor)")

    # Report label distribution
    labels = Counter(int(r["label"]) for r in mixed)
    sev_names = {0: "Low", 1: "Medium", 2: "High", 3: "Critical"}
    print("Label distribution:")
    for label_id in sorted(labels):
        print(f"  {sev_names[label_id]}: {labels[label_id]}")

    return mixed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic", type=Path, required=True)
    parser.add_argument("--predecessor", type=Path, required=True)
    parser.add_argument("--predecessor-weight", type=float, default=0.3,
                        help="Fraction of final dataset from predecessor (default 0.3)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    predecessor_rows = convert_predecessor(args.predecessor)
    mixed = mix_datasets(args.synthetic, predecessor_rows, args.predecessor_weight, args.seed)

    # Write output
    fieldnames = ["cve_id", "input_text", "sector", "cross_border", "cvss_score",
                  "base_severity", "contextual_severity", "label"]
    with open(args.output, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(mixed)

    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
