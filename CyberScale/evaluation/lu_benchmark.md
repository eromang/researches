# CyberScale v7 — Luxembourg National Threshold Benchmark

**Date:** 2026-04-02 15:45
**Dataset:** `data/reference/curated_lu_incidents.json`
**Scenarios:** 20
**Elapsed:** 0.0s

## Summary

| Metric | Result | Target |
|--------|--------|--------|
| Overall accuracy | 20/20 (100%) | 100% |
| Routing correctness | 20/20 | 100% |
| Significance correctness | 20/20 | 100% |

## Routing Tier Distribution

| Tier | Count | Correct |
|------|-------|---------|
| ir_thresholds | 4 | 4/4 |
| national_lu_thresholds | 13 | 13/13 |
| nis2_ml | 3 | 3/3 |

## Per-scenario Results

| ID | Scenario | Expected Model | Actual Model | Pass |
|----|----------|---------------|-------------|------|
| LU-01 | POST Luxembourg electricity — LV-POD outage | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-02 | LuxTrust trust services — IR entity | ir_thresholds | ir_thresholds | PASS |
| LU-03 | CFL rail — train cancellation threshold | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-04 | CHL hospital — reversible health impact | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-05 | .LU registry — DNS zone compromise | ir_thresholds | ir_thresholds | PASS |
| LU-06 | LU-IX IXP — member impact | ir_thresholds | ir_thresholds | PASS |
| LU-07 | Luxair — flight cancellation threshold | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-08 | Creos Luxembourg — gas SCADA | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-09 | LU road transport — below threshold | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-10 | LU road transport — at threshold | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-11 | POST cloud — IR entity in LU | ir_thresholds | ir_thresholds | PASS |
| LU-12 | LU bank — DORA applies | nis2_ml | nis2_ml | PASS |
| LU-13 | LU wastewater — not covered | nis2_ml | nis2_ml | PASS |
| LU-14 | LU electricity HV/EHV — automatic trigger | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-15 | LU drinking water — 10% users 6h | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-16 | LU hospital — death | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-17 | LU lab — 60% analyses 5h | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-18 | LU gas — valve control loss | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-19 | LU digital service provider — 6M user-hours | national_lu_thresholds | national_lu_thresholds | PASS |
| LU-20 | DE electricity (non-LU) — NIS2 ML fallback | nis2_ml | nis2_ml | PASS |

## All scenarios passed.
