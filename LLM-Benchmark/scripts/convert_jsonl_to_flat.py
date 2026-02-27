#!/usr/bin/env python3
"""
convert_jsonl_to_flat.py

Convert a benchmark JSONL file to a flat CSV, re-extracting sections from
output_text when the dedicated section fields are empty.

Reuses extract_sections() and normalize_text() from run_benchmark_ollama_api.py.

Usage:
  python3 convert_jsonl_to_flat.py results/gemma-results.jsonl results/gemma_results_flat.csv
"""

from __future__ import annotations

import csv
import json
import re
import sys
from typing import Any, Dict, List, Tuple

# ---------------------
# Section extraction (mirrored from run_benchmark_ollama_api.py)
# ---------------------

_SECTION_KEYS = [
    ("executive_summary", "Executive Summary"),
    ("threat_overview", "Threat Overview"),
    ("key_threat_vectors", "Key Threat Vectors"),
    ("impact_assessment", "Impact Assessment"),
    ("early_warning_indicators", "Early Warning Indicators"),
    ("defensive_priorities", "Defensive Priorities"),
    ("confidence_assessment", "Confidence Assessment"),
]


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def extract_sections(text: str) -> Dict[str, str]:
    raw = (text or "").strip()
    if not raw:
        return {k: "" for k, _ in _SECTION_KEYS}

    positions: List[Tuple[int, str]] = []
    for key, title in _SECTION_KEYS:
        pats = [
            re.compile(rf"(?im)^\s*\d+\s*[\)\.\-:]\s*{re.escape(title)}\s*$"),
            re.compile(rf"(?im)^\s*\d+\s*[\)\.\-:]\s*\*\*{re.escape(title)}\*\*\s*$"),
            re.compile(rf"(?im)^\s*#+\s*{re.escape(title)}\s*$"),
            re.compile(rf"(?im)^\s*\*\*\d+[\)\.\-:]*\s*{re.escape(title)}\*\*"),
            re.compile(rf"(?im)^\s*\*\*\d+\)\s*{re.escape(title)}:?\*\*\s*$"),
            re.compile(rf"(?im)^\s*\*\*{re.escape(title)}\*\*\s*:?\s*$"),
            re.compile(rf"(?im)^\s*{re.escape(title)}\s*:\s*$"),
        ]
        for pat in pats:
            m = pat.search(raw)
            if m:
                positions.append((m.start(), key))
                break

    if not positions:
        return {k: "" for k, _ in _SECTION_KEYS}

    positions = sorted(positions, key=lambda x: x[0])

    out = {k: "" for k, _ in _SECTION_KEYS}
    for idx, (pos, key) in enumerate(positions):
        start = pos
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(raw)
        chunk = raw[start:end].strip()
        lines = chunk.splitlines()
        chunk_body = "\n".join(lines[1:]).strip() if lines else ""
        out[key] = chunk_body

    return out


# ---------------------
# Flat row builder
# ---------------------

def build_flat_row(r: Dict[str, Any]) -> Dict[str, Any]:
    snippet = normalize_text(r.get("output_text", ""))[:500]

    flat: Dict[str, Any] = {
        "run_id": r.get("run_id"),
        "timestamp_utc": r.get("timestamp_utc"),
        "model": r.get("model"),
        "temperature": r.get("temperature"),
        "rep": r.get("rep"),
        "prompt_id": r.get("prompt_id"),
        "pair_id": r.get("pair_id", ""),
        "category": r.get("category", ""),
        "condition": r.get("sensitivity_level", r.get("condition", "")),
        "sensitivity_level": r.get("sensitivity_level", ""),
        "sector_focus": r.get("sector_focus", ""),
        "used_wrapper": r.get("used_wrapper", True),
        "ok": r.get("ok"),
        "error": (r.get("error") or "")[:200],
        "latency_ms": r.get("latency_ms"),
        "output_len_chars": r.get("output_len_chars"),
        "flag_refusal_or_avoidance": r.get("flag_refusal_or_avoidance"),
        "flag_reason": r.get("flag_reason"),
        "cve_count": r.get("cve_count"),
        "cves": ";".join(r.get("cves") or []),
        "output_snippet": snippet,
        "output_md_path": "",
    }

    # Re-extract sections from output_text if JSONL has empty sections
    sections = {k: r.get(k, "") for k, _ in _SECTION_KEYS}
    if not any(v for v in sections.values()):
        sections = extract_sections(r.get("output_text", ""))
    flat.update({
        "executive_summary": sections.get("executive_summary", ""),
        "threat_overview": sections.get("threat_overview", ""),
        "key_threat_vectors": sections.get("key_threat_vectors", ""),
        "impact_assessment": sections.get("impact_assessment", ""),
        "early_warning_indicators": sections.get("early_warning_indicators", ""),
        "defensive_priorities": sections.get("defensive_priorities", ""),
        "confidence_assessment": sections.get("confidence_assessment", ""),
    })
    flat["prompt_text"] = r.get("prompt_text", "")
    return flat


def main() -> None:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input.jsonl> <output.csv> [--model <name>]", file=sys.stderr)
        sys.exit(1)

    in_path = sys.argv[1]
    out_path = sys.argv[2]
    model_filter = None
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        model_filter = sys.argv[idx + 1]

    records: List[Dict[str, Any]] = []
    decoder = json.JSONDecoder()
    with open(in_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Handle lines with concatenated JSON objects (missing newline)
            pos = 0
            while pos < len(line):
                remaining = line[pos:].lstrip()
                if not remaining:
                    break
                obj, end = decoder.raw_decode(remaining)
                records.append(obj)
                pos += (len(line[pos:]) - len(remaining)) + end

    if model_filter:
        before = len(records)
        records = [r for r in records if r.get("model") == model_filter]
        print(f"Loaded {before} records, filtered to {len(records)} for model={model_filter}")
    else:
        print(f"Loaded {len(records)} records from {in_path}")

    flat_rows = [build_flat_row(r) for r in records]

    if flat_rows:
        csv_fields = list(flat_rows[0].keys())
        with open(out_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=csv_fields)
            w.writeheader()
            for row in flat_rows:
                w.writerow(row)

    print(f"Wrote {len(flat_rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
