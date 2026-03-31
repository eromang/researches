# Phase 1 Scorer Evaluation Report

**Generated:** 2026-03-31 00:49 UTC
**Test samples:** 4597
**MC dropout passes:** 5
**Overall:** FAIL

## Summary Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Accuracy | 0.6032 | > 0.75 | FAIL |
| Macro F1 | 0.5557 | > 0.70 | FAIL |

## Per-Class Breakdown

| Class | Precision | Recall | F1 | Count |
|-------|-----------|--------|----|-------|
| Low | 0.6996 | 0.4773 | 0.5674 | 683 |
| Medium | 0.6082 | 0.7839 | 0.6850 | 2004 |
| High | 0.5723 | 0.4959 | 0.5314 | 1357 |
| Critical | 0.5457 | 0.3671 | 0.4389 | 553 |

## Confidence Calibration

| Confidence | Count | Accuracy |
|------------|-------|----------|
| high | 4056 | 0.6267 |
| medium | 516 | 0.4302 |
| low | 25 | 0.3600 |

## Confusion Matrix

```
                   Low    Medium      High  Critical   <- predicted
         Low       326       309        42         6
      Medium       112      1571       269        52
        High        19       554       673       111
    Critical         9       149       192       203
^ actual
```

## Pass/Fail Summary

- Accuracy > 75%: **FAIL** (0.6032)
- Macro F1 > 70%: **FAIL** (0.5557)
- **Overall: FAIL**
