"""Test model robustness across description quality degradation levels.

Target: < 15% band accuracy drop from full to minimal descriptions.

Usage:
    cd CyberScale
    poetry run python evaluation/degradation_tests.py \
        --model data/models/scorer \
        --data training/data/training_cves.csv \
        --output evaluation/degradation_report.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# ---------------------------------------------------------------------------
# Allow importing from src/ when running from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.scorer import SeverityScorer  # noqa: E402

# Default config values (matches scorer.json)
DEFAULT_TEST_SPLIT = 0.15
DEFAULT_SEED = 42
DEFAULT_MC_PASSES = 5
DEFAULT_MAX_LENGTH = 192
DEGRADATION_SAMPLE = 200
MAX_DROP_THRESHOLD = 0.15  # 15%


# ---------------------------------------------------------------------------
# Helpers (must match training split logic exactly)
# ---------------------------------------------------------------------------
def assign_strat_bin(score: float) -> int:
    """Assign a stratification bin index for splitting."""
    if score <= 3.9:
        return 0
    if score <= 6.9:
        return 1
    if score <= 8.9:
        return 2
    return 3


def load_test_split(
    data_path: Path,
    test_split: float = DEFAULT_TEST_SPLIT,
    seed: int = DEFAULT_SEED,
) -> pd.DataFrame:
    """Load CSV and return test split as a DataFrame.

    Reproduces the exact same split as training.
    """
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["description", "cvss_score"]).reset_index(drop=True)

    scores = df["cvss_score"].astype(float).tolist()
    strat_bins = [assign_strat_bin(s) for s in scores]
    indices = list(range(len(df)))

    _, test_idx = train_test_split(
        indices, test_size=test_split, random_state=seed, stratify=strat_bins
    )

    return df.iloc[test_idx].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Degradation transforms
# ---------------------------------------------------------------------------
def degrade_full(desc: str) -> str:
    """No transformation -- original description."""
    return desc


def degrade_truncated_100(desc: str) -> str:
    """First 100 characters."""
    return desc[:100]


def degrade_truncated_50(desc: str) -> str:
    """First 50 characters."""
    return desc[:50]


def degrade_paraphrased(desc: str) -> str:
    """Lowercase, replace CVE IDs and version ranges."""
    text = desc.lower()
    # Replace CVE IDs (e.g., CVE-2024-12345) with generic term
    text = re.sub(r"cve-\d{4}-\d{4,}", "a vulnerability", text)
    # Replace version ranges (e.g., "before 1.2.3", "< 4.5", "1.0 to 2.0",
    # "versions 1.x through 3.x")
    text = re.sub(
        r"(versions?\s+)?\d+\.\d+[\.\d]*\s*(to|through|before|after|and earlier|and later)\s*\d*[\.\d]*",
        "certain versions",
        text,
    )
    text = re.sub(r"(before|after|prior to|up to)\s+\d+[\.\d]*", "certain versions", text)
    text = re.sub(r"[<>]=?\s*\d+[\.\d]*", "certain versions", text)
    return text


def degrade_minimal(desc: str) -> str:
    """Extract product name and create minimal description."""
    # Try common patterns: "in {product}", "{product} allows", "{product} is"
    # Pattern 1: "vulnerability in {Product Name}"
    match = re.search(r"(?:vulnerability|flaw|issue|bug)\s+in\s+([A-Z][\w\s\-\.]+?)(?:\s+(?:before|allows|could|is|has|was|through|prior))", desc)
    if match:
        product = match.group(1).strip()
        return f"vulnerability in {product}"

    # Pattern 2: "{Product Name} before/allows/is/has"
    match = re.search(r"^([A-Z][\w\s\-\.]+?)(?:\s+(?:before|allows|could|is|has|was|through|prior|v\d))", desc)
    if match:
        product = match.group(1).strip()
        return f"vulnerability in {product}"

    # Pattern 3: "in {product} component" from longer descriptions
    match = re.search(r"\bin\s+(?:the\s+)?([A-Z][\w\-\.]+(?:\s+[A-Z][\w\-\.]+){0,3})", desc)
    if match:
        product = match.group(1).strip()
        return f"vulnerability in {product}"

    # Fallback: first two words
    words = desc.split()[:2]
    return f"vulnerability in {' '.join(words)}"


DEGRADATION_LEVELS = {
    "full": degrade_full,
    "truncated_100": degrade_truncated_100,
    "truncated_50": degrade_truncated_50,
    "paraphrased": degrade_paraphrased,
    "minimal": degrade_minimal,
}


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def run_degradation_tests(
    model_path: Path,
    data_path: Path,
    output_path: Path,
) -> dict:
    """Run degradation tests and write markdown report."""
    # Load config if available, otherwise use defaults
    config_path = PROJECT_ROOT / "training" / "configs" / "scorer.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        seed = config["model"].get("seed", DEFAULT_SEED)
        test_split = config["evaluation"].get("test_split", DEFAULT_TEST_SPLIT)
        mc_passes = config["model"].get("mc_dropout_passes", DEFAULT_MC_PASSES)
        max_length = config["model"].get("max_length", DEFAULT_MAX_LENGTH)
    else:
        seed = DEFAULT_SEED
        test_split = DEFAULT_TEST_SPLIT
        mc_passes = DEFAULT_MC_PASSES
        max_length = DEFAULT_MAX_LENGTH

    # Load model
    print(f"Loading model from {model_path} ...")
    scorer = SeverityScorer(
        model_path=model_path,
        mc_passes=mc_passes,
        max_length=max_length,
    )

    # Load test split and sample
    print(f"Loading test split from {data_path} ...")
    test_df = load_test_split(data_path, test_split=test_split, seed=seed)

    if len(test_df) > DEGRADATION_SAMPLE:
        # Stratified sample for speed
        np.random.seed(seed)
        sample_idx = np.random.choice(len(test_df), DEGRADATION_SAMPLE, replace=False)
        test_df = test_df.iloc[sample_idx].reset_index(drop=True)

    print(f"Test samples (after sampling): {len(test_df)}")

    descriptions = test_df["description"].tolist()
    cwes = test_df["cwe"].tolist() if "cwe" in test_df.columns else [None] * len(test_df)
    true_scores = test_df["cvss_score"].astype(float).tolist()
    true_bands = [SeverityScorer.score_to_band(s) for s in true_scores]

    # Run each degradation level
    results: dict[str, dict] = {}

    for level_name, transform_fn in DEGRADATION_LEVELS.items():
        print(f"\nRunning level: {level_name} ...")
        pred_bands: list[str] = []
        abs_errors: list[float] = []

        for i, (desc, cwe, true_s) in enumerate(zip(descriptions, cwes, true_scores)):
            degraded_desc = transform_fn(desc)
            cwe_str = (
                str(cwe)
                if cwe and str(cwe).lower() not in ("nan", "none", "")
                else None
            )
            result = scorer.predict(degraded_desc, cwe=cwe_str)
            pred_bands.append(result.band)
            abs_errors.append(abs(result.score - true_s))

            if (i + 1) % 50 == 0:
                print(f"  Predicted {i + 1}/{len(descriptions)}")

        band_acc = float(
            sum(p == t for p, t in zip(pred_bands, true_bands)) / len(pred_bands)
        )
        mae = float(np.mean(abs_errors))

        results[level_name] = {
            "band_accuracy": round(band_acc, 4),
            "mae": round(mae, 4),
        }

        print(f"  Band accuracy: {band_acc:.4f}  MAE: {mae:.4f}")

    # Compute drops from full
    full_acc = results["full"]["band_accuracy"]
    for level_name, level_data in results.items():
        if full_acc > 0:
            drop = (full_acc - level_data["band_accuracy"]) / full_acc
        else:
            drop = 0.0
        level_data["drop_from_full"] = round(drop, 4)

    # Pass/Fail
    minimal_drop = results["minimal"]["drop_from_full"]
    passed = minimal_drop < MAX_DROP_THRESHOLD

    summary = {
        "samples": len(test_df),
        "levels": results,
        "minimal_drop": round(minimal_drop, 4),
        "threshold": MAX_DROP_THRESHOLD,
        "passed": passed,
    }

    print(f"\n--- Degradation Summary ---")
    print(f"  Full accuracy:    {full_acc:.4f}")
    print(f"  Minimal accuracy: {results['minimal']['band_accuracy']:.4f}")
    print(f"  Drop:             {minimal_drop:.4f}  {'PASS' if passed else 'FAIL'} (threshold < {MAX_DROP_THRESHOLD})")

    # Write report
    report = generate_markdown_report(summary)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    print(f"\nReport saved to {output_path}")

    return summary


# ---------------------------------------------------------------------------
# Markdown report generation
# ---------------------------------------------------------------------------
def generate_markdown_report(summary: dict) -> str:
    """Generate a markdown degradation report."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    overall = "PASS" if summary["passed"] else "FAIL"

    lines = [
        "# Phase 1 Degradation Test Report",
        "",
        f"**Generated:** {ts}",
        f"**Test samples:** {summary['samples']}",
        f"**Overall:** {overall}",
        "",
        "## Degradation Results",
        "",
        "| Level | Band Accuracy | MAE | Drop from Full |",
        "|-------|--------------|-----|----------------|",
    ]

    for level_name in ("full", "truncated_100", "truncated_50", "paraphrased", "minimal"):
        data = summary["levels"].get(level_name, {})
        ba = data.get("band_accuracy", 0)
        mae = data.get("mae", 0)
        drop = data.get("drop_from_full", 0)
        drop_str = f"{drop:.1%}" if level_name != "full" else "--"
        lines.append(f"| {level_name} | {ba:.4f} | {mae:.4f} | {drop_str} |")

    lines.extend([
        "",
        "## Pass/Fail",
        "",
        f"- Drop from full to minimal: **{summary['minimal_drop']:.1%}**",
        f"- Threshold: < {summary['threshold']:.0%}",
        f"- **Result: {overall}**",
        "",
        "## Degradation Level Descriptions",
        "",
        "| Level | Description |",
        "|-------|-------------|",
        "| full | Original description (no transformation) |",
        "| truncated_100 | First 100 characters of description |",
        "| truncated_50 | First 50 characters of description |",
        "| paraphrased | Lowercase, CVE IDs replaced, version ranges normalised |",
        "| minimal | Extracted product name only: \"vulnerability in {product}\" |",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Test model robustness across description quality levels"
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Path to trained model directory",
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to training CSV (same file used for training)",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path for markdown report output",
    )

    args = parser.parse_args()

    run_degradation_tests(
        model_path=Path(args.model),
        data_path=Path(args.data),
        output_path=Path(args.output),
    )


if __name__ == "__main__":
    main()
