#!/usr/bin/env python3
"""Publish EU Cyber LLM Benchmark responses to Hugging Face."""

import json
import glob
from datasets import Dataset, Features, Value, Sequence
from huggingface_hub import HfApi

REPO_ID = "eromang/eu-cyber-llm-benchmark-responses"

PHASE1_JSONL = "results/Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl"
PHASE2_DIR = "results/Phase_2"

FEATURES = Features({
    "phase": Value("string"),
    "run_id": Value("string"),
    "timestamp_utc": Value("string"),
    "model": Value("string"),
    "temperature": Value("float32"),
    "rep": Value("int32"),
    "prompt_id": Value("string"),
    "pair_id": Value("string"),
    "category": Value("string"),
    "sensitivity_level": Value("string"),
    "sector_focus": Value("string"),
    "prompt_text": Value("string"),
    "used_wrapper": Value("bool"),
    "ok": Value("bool"),
    "error": Value("string"),
    "latency_ms": Value("int32"),
    "output_text": Value("string"),
    "output_len_chars": Value("int32"),
    "flag_refusal_or_avoidance": Value("string"),
    "flag_reason": Value("string"),
    "cves": Sequence(Value("string")),
    "cve_count": Value("int32"),
    "executive_summary": Value("string"),
    "threat_overview": Value("string"),
    "key_threat_vectors": Value("string"),
    "impact_assessment": Value("string"),
    "early_warning_indicators": Value("string"),
    "defensive_priorities": Value("string"),
    "confidence_assessment": Value("string"),
})


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def normalise(record, phase):
    """Ensure consistent types across all records."""
    record["phase"] = phase
    record["error"] = record.get("error") or ""
    record["category"] = record.get("category") or ""
    record["flag_refusal_or_avoidance"] = record.get("flag_refusal_or_avoidance") or ""
    record["flag_reason"] = record.get("flag_reason") or ""
    record["cves"] = record.get("cves") or []
    record["cve_count"] = record.get("cve_count") or 0
    record["output_len_chars"] = record.get("output_len_chars") or 0
    record["latency_ms"] = record.get("latency_ms") or 0
    for field in ("executive_summary", "threat_overview", "key_threat_vectors",
                  "impact_assessment", "early_warning_indicators",
                  "defensive_priorities", "confidence_assessment"):
        record[field] = record.get(field) or ""
    return record


def main():
    all_records = []

    # Phase 1
    phase1 = load_jsonl(PHASE1_JSONL)
    for r in phase1:
        all_records.append(normalise(r, "phase_1"))
    print(f"Phase 1: {len(phase1)} records")

    # Phase 2
    phase2_files = sorted(glob.glob(f"{PHASE2_DIR}/**/*.jsonl", recursive=True))
    phase2_total = 0
    for path in phase2_files:
        records = load_jsonl(path)
        for r in records:
            all_records.append(normalise(r, "phase_2"))
        print(f"  {path}: {len(records)} records")
        phase2_total += len(records)
    print(f"Phase 2: {phase2_total} records")
    print(f"Total: {len(all_records)} records")

    ds = Dataset.from_list(all_records, features=FEATURES)
    print(ds)
    ds.push_to_hub(REPO_ID, private=False)
    print(f"Published to https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
