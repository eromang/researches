# CyberScale Phase 3 — Incident Classification Benchmark

**Date:** 2026-03-30 11:41
**T-model:** `data/models/technical`
**O-model:** `data/models/operational`
**Test scenarios:** 1000
**Seed:** 999
**Elapsed:** 157.5s

## T-model Results

- **Accuracy:** 95.40%
- **Macro F1:** 0.9536

### Per-level F1

| Level | F1 |
|-------|-----|
| T1 | 0.8987 |
| T2 | 0.9158 |
| T3 | 1.0000 |
| T4 | 1.0000 |

### Confusion Matrix

| Actual \ Predicted | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| **T1** | 102 | 23 | 0 | 0 |
| **T2** | 0 | 125 | 0 | 0 |
| **T3** | 0 | 0 | 125 | 0 |
| **T4** | 0 | 0 | 0 | 125 |

## O-model Results

- **Accuracy:** 96.40%
- **Macro F1:** 0.9638

### Per-level F1

| Level | F1 |
|-------|-----|
| O1 | 0.9407 |
| O2 | 0.9380 |
| O3 | 0.9766 |
| O4 | 1.0000 |

### Confusion Matrix

| Actual \ Predicted | O1 | O2 | O3 | O4 |
|---|---|---|---|---|
| **O1** | 111 | 12 | 2 | 0 |
| **O2** | 0 | 121 | 4 | 0 |
| **O3** | 0 | 0 | 125 | 0 |
| **O4** | 0 | 0 | 0 | 125 |

## End-to-end Matrix Results

- **Accuracy:** 96.20%

### Classification Distribution

| Classification | Count | Pct |
|---------------|-------|-----|
| below_threshold | 28 | 5.6% |
| significant | 148 | 29.6% |
| large_scale | 227 | 45.4% |
| cyber_crisis | 97 | 19.4% |

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
| T-model macro F1 | > 75% | 95.4% | PASS |
| O-model macro F1 | > 75% | 96.4% | PASS |
| Matrix end-to-end | > 70% | 96.2% | PASS |
| Illustrative cases | 6/6 | 6/6 | PASS |
| **Overall** | **All pass** | | **PASS** |
