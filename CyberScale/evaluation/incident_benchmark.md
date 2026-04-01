# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** 2026-04-01 09:59
**T-model:** `data/models/technical`
**O-model:** `data/models/operational`
**Test scenarios:** 1000
**Seed:** 999
**Elapsed:** 46.1s

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

- **Accuracy:** 79.00%
- **Macro F1:** 0.7795

### Per-level F1

| Level | F1 |
|-------|-----|
| O1 | 0.9158 |
| O2 | 0.8026 |
| O3 | 0.6291 |
| O4 | 0.7707 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 125 | 0 | 0 | 0 |
| **O2** | 1 | 124 | 0 | 0 |
| **O3** | 22 | 35 | 67 | 1 |
| **O4** | 0 | 25 | 21 | 79 |

## End-to-end Matrix Results

- **Accuracy:** 83.80%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 40 | 8.0% |
| significant | 183 | 36.6% |
| large_scale | 218 | 43.6% |
| cyber_crisis | 59 | 11.8% |

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
| O-model macro F1 | > 75% | 78.0% | PASS |
| Matrix end-to-end | > 70% | 83.8% | PASS |
| Illustrative cases | 6/6 | 6/6 | PASS |
| **Overall** | **All pass** | | **PASS** |
