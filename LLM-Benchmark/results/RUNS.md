# Benchmark Runs

| Phase | Model | Run ID | JSONL file | Records | Status |
|-------|-------|--------|------------|---------|--------|
| 1 | qwen3:8b, deepseek-r1:8b, llama3.1:8b | `run_20260223T183701Z_c56fa1d40ab51b84` | `Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl` | 1,200 | Complete |
| 2 | llama3.1:8b-instruct-q4_K_M | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/llama31/run_20260224T103518Z_51e859312629dea4.jsonl` | 2,112 | Complete |
| 2 | gemma3n:e4b | (shared run infrastructure) | `Phase_2/gemma3n/gemma-results.jsonl` | 2,112 | Complete |

## Notes

- Phase 1 tested 3 models in a single run (all results in one JSONL).
- Phase 2 tested models separately; gemma3n uses a descriptive filename rather than a timestamp-based one.
- JSONL files are tracked via Git LFS.

## Regeneration

Derived files (CSVs, HTML dashboards, analysis reports) are not committed.
To regenerate from JSONL:

```bash
# Phase 1 analysis
python3 scripts/analyze_results.py Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl --outdir Phase_1/analysis

# Phase 2 llama3.1 analysis
python3 scripts/analyze_results.py Phase_2/llama31/run_20260224T103518Z_51e859312629dea4.jsonl --outdir Phase_2/llama31/analysis

# Phase 2 gemma3n analysis
python3 scripts/analyze_results.py Phase_2/gemma3n/gemma-results.jsonl --outdir Phase_2/gemma3n/analysis
```
