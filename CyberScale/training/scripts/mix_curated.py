#!/usr/bin/env python3
"""Mix curated real-world incidents into synthetic training data.

Converts curated incidents from JSON to model-specific CSV format,
adds a weight column (curated=1.0, synthetic=0.8), and outputs
augmented training CSVs.

Usage:
    poetry run python training/scripts/mix_curated.py \
        --curated data/reference/curated_incidents.json \
        --synthetic-t training/data/technical_training.csv \
        --synthetic-o training/data/operational_training.csv \
        --output-t training/data/technical_training_v2.csv \
        --output-o training/data/operational_training_v2.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from functools import partial
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "training" / "scripts"))

from generate_incidents import _paraphrase

print = partial(print, flush=True)


def convert_to_t_csv(
    incident: dict,
    paraphrase_variants: int = 3,
    seed: int = 42,
) -> list[dict]:
    tf = incident["t_fields"]
    desc = incident["description"]
    label = incident["expected_t"]

    base_text = (
        f"{desc} [SEP] "
        f"service_impact: {tf['service_impact']} "
        f"entities: {tf['affected_entities']} "
        f"sectors: {tf['sectors_affected']} "
        f"cascading: {tf['cascading']} "
        f"data_impact: {tf['data_impact']}"
    )

    rows = [{"text": base_text, "label": label, "weight": 1.0}]

    rng = random.Random(seed + hash(incident["id"]))
    for v in range(1, paraphrase_variants + 1):
        para_desc = _paraphrase(desc, v, rng)
        para_text = (
            f"{para_desc} [SEP] "
            f"service_impact: {tf['service_impact']} "
            f"entities: {tf['affected_entities']} "
            f"sectors: {tf['sectors_affected']} "
            f"cascading: {tf['cascading']} "
            f"data_impact: {tf['data_impact']}"
        )
        rows.append({"text": para_text, "label": label, "weight": 1.0})

    return rows


def convert_to_o_csv(
    incident: dict,
    paraphrase_variants: int = 3,
    seed: int = 42,
) -> list[dict]:
    of = incident["o_fields"]
    desc = incident["description"]
    label = incident["expected_o"]

    base_text = (
        f"{desc} [SEP] "
        f"sectors: {of['sectors_affected']} "
        f"relevance: {of['entity_relevance']} "
        f"ms_affected: {of['ms_affected']} "
        f"cross_border: {of['cross_border_pattern']} "
        f"capacity_exceeded: {str(of['capacity_exceeded']).lower()}"
    )

    rows = [{"text": base_text, "label": label, "weight": 1.0}]

    rng = random.Random(seed + hash(incident["id"]))
    for v in range(1, paraphrase_variants + 1):
        para_desc = _paraphrase(desc, v, rng)
        para_text = (
            f"{para_desc} [SEP] "
            f"sectors: {of['sectors_affected']} "
            f"relevance: {of['entity_relevance']} "
            f"ms_affected: {of['ms_affected']} "
            f"cross_border: {of['cross_border_pattern']} "
            f"capacity_exceeded: {str(of['capacity_exceeded']).lower()}"
        )
        rows.append({"text": para_text, "label": label, "weight": 1.0})

    return rows


def mix_into_training(
    synthetic_csv: Path,
    curated_incidents: list[dict],
    output_csv: Path,
    model_type: str,
    paraphrase_variants: int = 3,
    synthetic_weight: float = 0.8,
) -> int:
    converter = convert_to_t_csv if model_type == "t" else convert_to_o_csv

    rows: list[dict] = []

    with open(synthetic_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["weight"] = synthetic_weight
            rows.append(row)

    for inc in curated_incidents:
        rows.extend(converter(inc, paraphrase_variants=paraphrase_variants))

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label", "weight"])
        writer.writeheader()
        writer.writerows(rows)

    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Mix curated incidents into training data")
    parser.add_argument("--curated", type=Path, default=Path("data/reference/curated_incidents.json"))
    parser.add_argument("--synthetic-t", type=Path, default=Path("training/data/technical_training.csv"))
    parser.add_argument("--synthetic-o", type=Path, default=Path("training/data/operational_training.csv"))
    parser.add_argument("--output-t", type=Path, default=Path("training/data/technical_training_v2.csv"))
    parser.add_argument("--output-o", type=Path, default=Path("training/data/operational_training_v2.csv"))
    parser.add_argument("--paraphrase-variants", type=int, default=3)
    parser.add_argument("--synthetic-weight", type=float, default=0.8)
    args = parser.parse_args()

    data = json.loads(args.curated.read_text(encoding="utf-8"))
    incidents = data["incidents"]
    print(f"Loaded {len(incidents)} curated incidents")

    t_count = mix_into_training(
        synthetic_csv=args.synthetic_t,
        curated_incidents=incidents,
        output_csv=args.output_t,
        model_type="t",
        paraphrase_variants=args.paraphrase_variants,
        synthetic_weight=args.synthetic_weight,
    )
    print(f"T-model: {t_count} rows written to {args.output_t}")

    o_count = mix_into_training(
        synthetic_csv=args.synthetic_o,
        curated_incidents=incidents,
        output_csv=args.output_o,
        model_type="o",
        paraphrase_variants=args.paraphrase_variants,
        synthetic_weight=args.synthetic_weight,
    )
    print(f"O-model: {o_count} rows written to {args.output_o}")


if __name__ == "__main__":
    main()
