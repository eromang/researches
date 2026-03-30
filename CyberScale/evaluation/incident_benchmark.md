# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** 2026-03-30 22:18
**T-model:** `data/models/technical`
**O-model:** `data/models/operational`
**Test scenarios:** 1000
**Seed:** 999
**Elapsed:** 83.2s

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

- **Accuracy:** 99.60%
- **Macro F1:** 0.9960

### Per-level F1

| Level | F1 |
|-------|-----|
| O1 | 0.9919 |
| O2 | 0.9921 |
| O3 | 1.0000 |
| O4 | 1.0000 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 123 | 2 | 0 | 0 |
| **O2** | 0 | 125 | 0 | 0 |
| **O3** | 0 | 0 | 125 | 0 |
| **O4** | 0 | 0 | 0 | 125 |

## End-to-end Matrix Results

- **Accuracy:** 100.00%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 30 | 6.0% |
| significant | 155 | 31.0% |
| large_scale | 223 | 44.6% |
| cyber_crisis | 92 | 18.4% |

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
| O-model macro F1 | > 75% | 99.6% | PASS |
| Matrix end-to-end | > 70% | 100.0% | PASS |
| Illustrative cases | 6/6 | 6/6 | PASS |
| **Overall** | **All pass** | | **PASS** |
