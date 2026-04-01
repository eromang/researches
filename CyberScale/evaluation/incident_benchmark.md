# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** 2026-04-01 03:20
**T-model:** `data/models/technical`
**O-model:** `data/models/operational`
**Test scenarios:** 1000
**Seed:** 999
**Elapsed:** 48.7s

## T-model Results

- **Accuracy:** 100.00%
- **Macro F1:** 1.0000

### Per-level F1

| Level | F1 |
|-------|-----|
| T1 | 1.0000 |
| T2 | 1.0000 |
| T3 | 1.0000 |
| T4 | 1.0000 |

### Confusion Matrix

| Actual \ Predicted | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| **T1** | 125 | 0 | 0 | 0 |
| **T2** | 0 | 125 | 0 | 0 |
| **T3** | 0 | 0 | 125 | 0 |
| **T4** | 0 | 0 | 0 | 125 |

## O-model Results

- **Accuracy:** 89.20%
- **Macro F1:** 0.8926

### Per-level F1

| Level | F1 |
|-------|-----|
| O1 | 0.8493 |
| O2 | 0.8410 |
| O3 | 0.9302 |
| O4 | 0.9500 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 93 | 31 | 1 | 0 |
| **O2** | 0 | 119 | 5 | 1 |
| **O3** | 1 | 4 | 120 | 0 |
| **O4** | 0 | 4 | 7 | 114 |

## End-to-end Matrix Results

- **Accuracy:** 94.40%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 27 | 5.4% |
| significant | 152 | 30.4% |
| large_scale | 234 | 46.8% |
| cyber_crisis | 87 | 17.4% |

## Illustrative Use Cases

| # | Scenario | Expected T/O | Predicted T/O | Matrix | Pass |
|---|----------|-------------|--------------|--------|------|
| 1 | Below threshold (T1/O1) | T1/O1 | T1/O1 | Below threshold | PASS |
| 2 | Significant (T2/O2) | T2/O2 | T2/O2 | Significant | PASS |
| 3 | Large-scale (T3/O3) | T3/O3 | T3/O3 | Large-scale | PASS |
| 4 | Cyber crisis (T4/O4) | T4/O4 | T4/O4 | Cyber crisis | PASS |
| 5 | Asymmetric high-T/low-O (T4/O1) | T4/O1 | T4/O1 | Large-scale | PASS |
| 6 | Asymmetric low-T/high-O (T1/O4) | T1/O4 | T1/O4 | Large-scale | PASS |

## Summary

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| T-model macro F1 | > 75% | 100.0% | PASS |
| O-model macro F1 | > 75% | 89.3% | PASS |
| Matrix end-to-end | > 70% | 94.4% | PASS |
| Illustrative cases | 6/6 | 6/6 | PASS |
| **Overall** | **All pass** | | **PASS** |
