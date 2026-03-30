"""NVD vs EUVD scoring comparison for shared CVEs.

Outputs a findings document informing the CVSS arbitration logic:
- Score correlation between sources
- Systematic bias direction
- Recommended arbitration strategy

Usage:
    cd CyberScale
    poetry run python evaluation/reconciliation_analysis.py \
        --input training/data/training_cves.csv \
        --output evaluation/reconciliation_report.md
"""

from __future__ import annotations

import argparse
import csv
import logging
import random
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Ensure project src is importable when running from project root
# ---------------------------------------------------------------------------
_project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_project_root / "src"))

from cyberscale.api.euvd import EUVDClient  # noqa: E402
from cyberscale.api.nvd import NVDClient  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CVSS band mapping
# ---------------------------------------------------------------------------

def cvss_band(score: float) -> str:
    """Map a CVSS 3.x score to its severity band."""
    if score >= 9.0:
        return "Critical"
    if score >= 7.0:
        return "High"
    if score >= 4.0:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# Data collection
# ---------------------------------------------------------------------------

def load_nvd_cve_ids(csv_path: Path, sample_size: int) -> list[str]:
    """Read the training CSV and sample up to *sample_size* NVD-sourced CVE IDs."""
    nvd_ids: list[str] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("source", "").strip().lower() == "nvd":
                cve_id = row.get("cve_id", "").strip()
                if cve_id:
                    nvd_ids.append(cve_id)

    if len(nvd_ids) > sample_size:
        random.seed(42)
        nvd_ids = random.sample(nvd_ids, sample_size)

    log.info("Selected %d NVD CVE IDs for reconciliation (from %s)", len(nvd_ids), csv_path)
    return nvd_ids


def fetch_score_pairs(
    cve_ids: list[str],
) -> list[dict[str, float | str]]:
    """Fetch each CVE from both NVD and EUVD; return pairs where both have scores."""
    nvd = NVDClient()
    euvd = EUVDClient()
    pairs: list[dict[str, float | str]] = []

    for i, cve_id in enumerate(cve_ids, 1):
        log.info("[%d/%d] Fetching %s", i, len(cve_ids), cve_id)

        # --- NVD ---
        try:
            nvd_result = nvd.get_cve(cve_id)
        except Exception:
            log.warning("  NVD fetch failed for %s, skipping", cve_id)
            continue

        if nvd_result is None or nvd_result.get("cvss_score") is None:
            log.info("  NVD: no score for %s", cve_id)
            continue

        nvd_score = nvd_result["cvss_score"]

        # --- EUVD ---
        try:
            euvd_results = euvd.search(text=cve_id, size=1)
        except Exception:
            log.warning("  EUVD fetch failed for %s, skipping", cve_id)
            continue

        euvd_score: float | None = None
        for item in euvd_results:
            if cve_id in item.get("cve_ids", []):
                euvd_score = item.get("cvss_score")
                break

        if euvd_score is None:
            log.info("  EUVD: no matching score for %s", cve_id)
            continue

        pairs.append({
            "cve_id": cve_id,
            "nvd_score": nvd_score,
            "euvd_score": euvd_score,
        })
        log.info("  Pair: NVD=%.1f  EUVD=%.1f", nvd_score, euvd_score)

    log.info("Collected %d score pairs from %d candidates", len(pairs), len(cve_ids))
    return pairs


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def pearson_r(xs: list[float], ys: list[float]) -> float | None:
    """Compute Pearson correlation coefficient. Returns None if < 3 points."""
    n = len(xs)
    if n < 3:
        return None
    mean_x = statistics.mean(xs)
    mean_y = statistics.mean(ys)
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    std_x = (sum((x - mean_x) ** 2 for x in xs)) ** 0.5
    std_y = (sum((y - mean_y) ** 2 for y in ys)) ** 0.5
    if std_x == 0 or std_y == 0:
        return None
    return cov / (std_x * std_y)


def compute_stats(pairs: list[dict]) -> dict:
    """Compute all reconciliation statistics from score pairs."""
    nvd_scores = [p["nvd_score"] for p in pairs]
    euvd_scores = [p["euvd_score"] for p in pairs]
    deltas = [abs(p["nvd_score"] - p["euvd_score"]) for p in pairs]
    signed_deltas = [p["nvd_score"] - p["euvd_score"] for p in pairs]
    n = len(pairs)

    exact_match = sum(1 for d in deltas if d == 0.0)
    within_05 = sum(1 for d in deltas if d <= 0.5)
    within_10 = sum(1 for d in deltas if d <= 1.0)
    within_20 = sum(1 for d in deltas if d <= 2.0)

    band_agree = sum(
        1 for p in pairs
        if cvss_band(p["nvd_score"]) == cvss_band(p["euvd_score"])
    )

    # Band confusion matrix
    bands = ["Critical", "High", "Medium", "Low"]
    confusion: dict[str, dict[str, int]] = {
        b: {b2: 0 for b2 in bands} for b in bands
    }
    for p in pairs:
        nb = cvss_band(p["nvd_score"])
        eb = cvss_band(p["euvd_score"])
        confusion[nb][eb] += 1

    return {
        "n": n,
        "pearson_r": pearson_r(nvd_scores, euvd_scores),
        "mean_nvd": statistics.mean(nvd_scores) if n else 0,
        "mean_euvd": statistics.mean(euvd_scores) if n else 0,
        "mean_abs_delta": statistics.mean(deltas) if n else 0,
        "median_abs_delta": statistics.median(deltas) if n else 0,
        "mean_signed_delta": statistics.mean(signed_deltas) if n else 0,
        "exact_match_pct": (exact_match / n * 100) if n else 0,
        "within_05_pct": (within_05 / n * 100) if n else 0,
        "within_10_pct": (within_10 / n * 100) if n else 0,
        "within_20_pct": (within_20 / n * 100) if n else 0,
        "band_agree_pct": (band_agree / n * 100) if n else 0,
        "confusion": confusion,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

def recommend_strategy(mean_abs_delta: float) -> tuple[str, str]:
    """Return (strategy_name, explanation) based on mean absolute delta."""
    if mean_abs_delta < 0.5:
        return (
            "NVD primary",
            "Mean absolute delta is below 0.5 — sources agree closely. "
            "Use NVD score as the canonical CVSS value.",
        )
    if mean_abs_delta < 1.0:
        return (
            "NVD primary with freshness override",
            "Mean absolute delta is moderate (0.5-1.0). Use NVD as primary, "
            "but prefer EUVD when its record is more recently updated.",
        )
    return (
        "Weighted average (0.6 NVD + 0.4 EUVD)",
        "Mean absolute delta exceeds 1.0 — sources diverge materially. "
        "Use a weighted average: 0.6 * NVD + 0.4 * EUVD.",
    )


def generate_report(stats: dict, sample_size: int, csv_path: str) -> str:
    """Render the reconciliation report as markdown."""
    strategy, explanation = recommend_strategy(stats["mean_abs_delta"])

    r_display = f"{stats['pearson_r']:.4f}" if stats["pearson_r"] is not None else "N/A"

    lines = [
        "# NVD vs EUVD Reconciliation Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Source CSV:** `{csv_path}`",
        f"**Requested sample size:** {sample_size}",
        f"**Pairs with scores from both sources:** {stats['n']}",
        "",
        "---",
        "",
        "## 1. Score Correlation",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Pearson r | {r_display} |",
        f"| Mean NVD score | {stats['mean_nvd']:.2f} |",
        f"| Mean EUVD score | {stats['mean_euvd']:.2f} |",
        f"| Mean signed delta (NVD - EUVD) | {stats['mean_signed_delta']:+.3f} |",
        "",
        "## 2. Delta Distribution",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Mean absolute delta | {stats['mean_abs_delta']:.3f} |",
        f"| Median absolute delta | {stats['median_abs_delta']:.3f} |",
        f"| Exact match (delta = 0) | {stats['exact_match_pct']:.1f}% |",
        f"| Within 0.5 | {stats['within_05_pct']:.1f}% |",
        f"| Within 1.0 | {stats['within_10_pct']:.1f}% |",
        f"| Within 2.0 | {stats['within_20_pct']:.1f}% |",
        "",
        "## 3. Band Agreement",
        "",
        f"Overall band agreement: **{stats['band_agree_pct']:.1f}%**",
        "",
        "Bands: Critical (>=9.0), High (>=7.0), Medium (>=4.0), Low (<4.0)",
        "",
        "### Confusion Matrix (NVD band -> EUVD band)",
        "",
        "| NVD \\ EUVD | Critical | High | Medium | Low |",
        "|------------|----------|------|--------|-----|",
    ]

    for nvd_band in ["Critical", "High", "Medium", "Low"]:
        row = stats["confusion"][nvd_band]
        lines.append(
            f"| {nvd_band} | {row['Critical']} | {row['High']} "
            f"| {row['Medium']} | {row['Low']} |"
        )

    lines += [
        "",
        "## 4. Recommended Arbitration Strategy",
        "",
        f"**Strategy:** {strategy}",
        "",
        explanation,
        "",
        "---",
        "",
        "*This report was auto-generated by `evaluation/reconciliation_analysis.py`.*",
        "",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="NVD vs EUVD reconciliation analysis",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to training CVEs CSV (must have cve_id, source columns)",
    )
    parser.add_argument(
        "--output",
        default="evaluation/reconciliation_report.md",
        help="Path for output markdown report",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=200,
        help="Max CVEs to sample for comparison (default: 200)",
    )
    args = parser.parse_args()

    csv_path = Path(args.input)
    if not csv_path.exists():
        log.error("Input CSV not found: %s", csv_path)
        sys.exit(1)

    # 1. Load and sample CVE IDs
    cve_ids = load_nvd_cve_ids(csv_path, args.sample_size)
    if not cve_ids:
        log.error("No NVD-sourced CVE IDs found in %s", csv_path)
        sys.exit(1)

    # 2. Fetch score pairs from both APIs
    pairs = fetch_score_pairs(cve_ids)
    if not pairs:
        log.error("No score pairs collected — cannot generate report")
        sys.exit(1)

    # 3. Compute statistics
    stats = compute_stats(pairs)

    # 4. Generate and write report
    report = generate_report(stats, args.sample_size, args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    log.info("Report written to %s", output_path)


if __name__ == "__main__":
    main()
