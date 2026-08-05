# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** 2026-08-05 17:05
**T-model:** `data/models/technical`
**O-model:** `data/models/operational`
**Test scenarios:** 1000
**Seed:** 999
**Elapsed:** 75.7s

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

- **Accuracy:** 77.40%
- **Macro F1:** 0.7609

### Per-level F1

| Level | F1 |
|-------|-----|
| O1 | 0.9158 |
| O2 | 0.8013 |
| O3 | 0.5767 |
| O4 | 0.7500 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 125 | 0 | 0 | 0 |
| **O2** | 0 | 125 | 0 | 0 |
| **O3** | 23 | 40 | 62 | 0 |
| **O4** | 0 | 22 | 28 | 75 |

## End-to-end Matrix Results

- **Accuracy:** 82.60%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 39 | 7.8% |
| significant | 191 | 38.2% |
| large_scale | 213 | 42.6% |
| cyber_crisis | 57 | 11.4% |

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
| O-model macro F1 | > 75% | 76.1% | PASS |
| Matrix end-to-end | > 70% | 82.6% | PASS |
| Illustrative cases | 6/6 | 6/6 | PASS |
| **Overall** | **All pass** | | **PASS** |
