# Benchmark Runs

| Phase | Model | Run ID | JSONL file | Records | Status |
|-------|-------|--------|------------|---------|--------|
| 1 | qwen3:8b, deepseek-r1:8b, llama3.1:8b | `run_20260223T183701Z_c56fa1d40ab51b84` | `Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl` | 1,200 | Complete |
| 2 | llama3.1:8b-instruct-q4_K_M | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/llama31/llama31.jsonl` | 2,112 | Complete |
| 2 | gemma3n:e4b | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/gemma3n/gemma3n.jsonl` | 2,112 | Complete |
| 2 | qwen3:8b | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/qwen3-thinking/qwen3-thinking.jsonl` | 2,115 | Complete |
| 2 | deepseek-r1:8b | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/deepseek-r1/deepseek-r1.jsonl` | 2,113 | Complete |
| 2 | hoangquan456/qwen3-nothink:8b | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/qwen3-nothink/qwen3-nothink.jsonl` | 2,112 | Complete |
| 2 | phi4:latest | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/phi4/phi4.jsonl` | 2,112 | Complete |
| 2 | mistral:7b-instruct | `run_20260224T103518Z_51e859312629dea4` | `Phase_2/mistral/mistral.jsonl` | 2,112 | Complete |

## Notes

- Phase 1 tested 3 models in a single run (all results in one JSONL).
- Phase 2 used a shared monolithic JSONL for all 7 models; per-model JSONL files are split extracts.
- JSONL files are tracked via Git LFS.

## Run Flags

| Phase | Model                       | Flags                                                                        |
| ----- | --------------------------- | ---------------------------------------------------------------------------- |
| 1     | qwen3:8b                    | `--strip-thinking` (thinking enabled, `<think>` tokens stripped from output) |
| 1     | deepseek-r1:8b              | `--strip-thinking` (thinking enabled, `<think>` tokens stripped from output) |
| 1     | llama3.1:8b-instruct-q4_K_M | Standard (no thinking flags)                                                 |
| 2     | llama3.1:8b-instruct-q4_K_M | Standard (no thinking flags)                                                 |
| 2     | gemma3n:e4b                 | Standard (no thinking flags)                                                 |
| 2     | qwen3:8b                    | `--strip-thinking` (mid-run activation at record 479; 3 timeout failures)    |
| 2     | deepseek-r1:8b              | `--strip-thinking` (thinking enabled, `<think>` tokens stripped from output) |
| 2     | hoangquan456/qwen3-nothink:8b | Standard (no thinking flags — community fine-tune natively suppresses CoT) |
| 2     | phi4:latest                   | Standard (no thinking flags)                                                 |
| 2     | mistral:7b-instruct           | Standard (no thinking flags)                                                 |

## Regeneration

Derived files (CSVs, HTML dashboards, analysis reports) are not committed.
To regenerate from JSONL:

```bash
# Phase 1 analysis
python3 scripts/analyze_results.py Phase_1/run_20260223T183701Z_c56fa1d40ab51b84.jsonl --outdir Phase_1/analysis

# Phase 2 — per-model analysis (all models have per-model JSONL files)
for model_dir in llama31 gemma3n qwen3-thinking deepseek-r1 qwen3-nothink phi4 mistral; do
  python3 scripts/analyze_results.py "Phase_2/$model_dir/$model_dir.jsonl" --outdir "Phase_2/$model_dir/analysis"
done

# Phase 2 — confidence pattern analysis (per-model)
python3 scripts/analyze_confidence_patterns.py Phase_2/deepseek-r1/deepseek-r1.jsonl --outdir Phase_2/deepseek-r1/confidence_patterns
python3 scripts/analyze_confidence_patterns.py Phase_2/qwen3-nothink/qwen3-nothink.jsonl --outdir Phase_2/qwen3-nothink/confidence_patterns
python3 scripts/analyze_confidence_patterns.py Phase_2/phi4/phi4.jsonl --outdir Phase_2/phi4/confidence_patterns
python3 scripts/analyze_confidence_patterns.py Phase_2/mistral/mistral.jsonl --outdir Phase_2/mistral/confidence_patterns

# Cross-model confidence patterns
python3 scripts/compare_confidence_patterns.py --outdir Phase_2/cross_model_confidence_patterns

# CVE pattern analysis
python3 scripts/analyze_cve_patterns.py --outdir Phase_2/cve_patterns
```
