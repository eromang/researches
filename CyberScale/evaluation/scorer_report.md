# Phase 1 Scorer Evaluation Report

**Generated:** 2026-03-27 17:15 UTC
**Test samples:** 4597
**MC dropout passes:** 20
**Overall:** FAIL

## Summary Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| MAE | 1.1238 | < 1.0 | FAIL |
| RMSE | 1.5451 | -- | -- |
| Pearson r | 0.6959 | -- | -- |
| Band accuracy | 0.6106 | > 0.75 | FAIL |

## Confidence Calibration

| Confidence | Count | MAE |
|------------|-------|-----|
| high | 4597 | 1.1238 |
| medium | 0 | -- |
| low | 0 | -- |

## Per-Band Breakdown

| Band | Count | MAE | Band Accuracy |
|------|-------|-----|---------------|
| Critical | 553 | 1.3400 | 0.3454 |
| High | 1357 | 0.9609 | 0.6153 |
| Medium | 2004 | 1.0416 | 0.7141 |
| Low | 683 | 1.5138 | 0.5124 |

## Pass/Fail Summary

- MAE < 1.0: **FAIL** (1.1238)
- Band accuracy > 75%: **FAIL** (0.6106)
- **Overall: FAIL**
