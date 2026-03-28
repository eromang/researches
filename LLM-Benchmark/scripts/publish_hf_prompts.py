#!/usr/bin/env python3
"""Publish EU Cyber LLM Benchmark prompts to Hugging Face."""

import csv
from datasets import Dataset, DatasetDict, Features, Value
from huggingface_hub import HfApi

REPO_ID = "eromang/eu-cyber-llm-benchmark-prompts"

PHASE1_CSV = "prompts/EU_Cyber_Phase_II_40_Scenarios_200_Prompts_Harmonised.csv"
PHASE2_CSV = "prompts/EU_Cyber_Phase_II_48_Scenarios_528_Prompts_11_Conditions_Harmonised.csv"

FEATURES = Features({
    "prompt_id": Value("string"),
    "scenario_id": Value("string"),
    "condition": Value("string"),
    "sector_focus": Value("string"),
    "prompt_text": Value("string"),
})


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def main():
    phase1 = load_csv(PHASE1_CSV)
    phase2 = load_csv(PHASE2_CSV)

    print(f"Phase 1: {len(phase1)} prompts")
    print(f"Phase 2: {len(phase2)} prompts")

    ds = DatasetDict({
        "phase_1": Dataset.from_list(phase1, features=FEATURES),
        "phase_2": Dataset.from_list(phase2, features=FEATURES),
    })

    print(ds)
    ds.push_to_hub(REPO_ID, private=False)
    print(f"Published to https://huggingface.co/datasets/{REPO_ID}")


if __name__ == "__main__":
    main()
