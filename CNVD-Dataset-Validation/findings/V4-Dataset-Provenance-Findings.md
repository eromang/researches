# V4 — Dataset Provenance — Findings Report

**Date:** 2026-03-24
**Dataset:** `CIRCL/Vulnerability-CNVD` (Hugging Face)
**Method:** CNVD ID sequence analysis, missing ID probing via Vulnerability-Lookup API, HF commit history, ML-Gateway source review

---

## 1. Executive Finding

**The Hugging Face dataset (127,562 entries) represents approximately 10–25% of the full CNVD database, which reserves ~100,000 vulnerability IDs per year.** The dataset is not filtered by CIRCL — it contains all CNVD entries with actual content (title, description, severity). The vast majority of CNVD IDs are empty stubs: reserved identifiers with no published vulnerability details. The "2022 cliff" is not an RMSV curation artifact — it reflects CNVD publishing fewer complete entries post-2021 while continuing to reserve IDs at the same rate.

---

## 2. Sequence Gap Analysis

CNVD IDs follow the pattern `CNVD-YYYY-NNNNN`. By comparing the dataset entry count against the ID range (max - min + 1), we can measure what fraction of reserved IDs have published content.

| Year | In dataset | Max ID seq | ID range | Coverage | Missing IDs |
|------|-----------|------------|----------|----------|-------------|
| 2015 | 8,045 | 8,561 | 8,561 | **94.0%** | 516 |
| 2016 | 10,496 | 13,303 | 13,302 | **78.9%** | 2,806 |
| 2017 | 15,318 | 38,524 | 38,516 | 39.8% | 23,198 |
| 2018 | 13,915 | 26,996 | 26,919 | 51.7% | 13,004 |
| 2019 | 14,733 | 47,663 | 47,661 | 30.9% | 32,928 |
| 2020 | 18,201 | 75,709 | 75,709 | **24.0%** | 57,508 |
| 2021 | 17,398 | 103,668 | 103,668 | **16.8%** | 86,270 |
| 2022 | 9,660 | 91,582 | 90,997 | **10.6%** | 81,337 |
| 2023 | 4,129 | 101,689 | 101,689 | **4.1%** | 97,560 |
| 2024 | 5,375 | 49,866 | 49,710 | 10.8% | 44,335 |
| 2025 | 8,714 | 31,568 | 31,468 | 27.7% | 22,754 |
| 2026 | 1,504 | 13,836 | 13,836 | 10.9% | 12,332 |

### Key observations

1. **CNVD reserves 50,000–100,000 IDs per year** (2019–2023) — far more than the entries with published content
2. **Coverage has declined steadily** from 94% (2015) to 4–11% (2022–2023)
3. **The ID reservation rate did not decrease after RMSV** — CNVD-2022 goes up to sequence 91,582, CNVD-2023 up to 101,689. CNVD continued reserving ~100,000 IDs/year.
4. **What decreased is the publication rate** — fewer reserved IDs are populated with actual vulnerability details post-RMSV

---

## 3. Missing ID Probing

100 missing IDs were probed via the Vulnerability-Lookup API (25 per year, 2020–2023). **All 100 exist in Vulnerability-Lookup but contain no data:**

| Property | In HF dataset (n=100) | Missing from HF (n=100) |
|----------|:--------------------:|:----------------------:|
| Has description | Yes (141 chars avg) | **No (0 chars)** |
| Has severity | Yes | **No (field = "?")** |
| Has CVE mapping | 84% | **0%** |

The excluded entries are **empty stubs** — CNVD IDs that were reserved but never populated with vulnerability details. Vulnerability-Lookup has ingested these stubs (they return HTTP 200), but there is no content to include in a training dataset.

### What this means

The HF dataset is not filtered by CIRCL. The filtering happens upstream at CNVD: the database reserves IDs but only publishes full details for a fraction. The HF dataset contains **all entries with actual content**.

---

## 4. HF Commit History

| Date | Commit |
|------|--------|
| 2025-06-27 | Initial commit + 3 uploads (dataset creation) |
| 2025-07-16 | Upload dataset |
| 2025-09-23 | Upload dataset |
| 2025-10-06 | Upload dataset |
| 2025-11-03 | Upload dataset |
| 2025-11-19 | Upload dataset |
| 2026-01-03 | Upload dataset |
| 2026-01-09 | Upload dataset |
| 2026-01-13 | Upload dataset |
| **2026-03-23** | **Upload dataset (most recent — day of LinkedIn post)** |

**14 commits total.** The dataset is actively maintained with roughly monthly updates. All commit messages are generic ("Upload dataset") — no filtering criteria documented. The most recent update (2026-03-23) coincides with the LinkedIn announcement.

---

## 5. ML-Gateway Source Review

The ML-Gateway repository (`vulnerability-lookup/ML-Gateway`) contains only inference code — a FastAPI service that loads the model and classifies text. **No dataset construction, preprocessing, or filtering scripts were found.**

The dataset construction pipeline exists elsewhere in CIRCL's infrastructure (likely in the Vulnerability-Lookup ingestion pipeline itself). The HF dataset appears to be a periodic dump of entries with non-empty content fields.

---

## 6. Verdict

### What explains the 2022 cliff?

| Hypothesis | Evidence | Assessment |
|-----------|----------|------------|
| CIRCL filtered post-RMSV entries | Missing IDs are empty stubs, not filtered content | **Rejected** |
| CNVD stopped publishing after RMSV | CNVD continued reserving 90,000+ IDs/year | **Rejected** |
| **CNVD reduced the rate of publishing full details** | Coverage dropped from 17% (2021) to 4% (2023) while ID reservation continued | **Supported** |
| Dataset curation by CIRCL | No filtering code found; all entries with content are included | **Rejected** |

**Conclusion:** The 2022 cliff is real — CNVD's publication rate of complete vulnerability entries dropped significantly after RMSV took effect. This is consistent with state-first disclosure requirements redirecting vulnerability details away from public databases and toward government channels. CNVD continues to reserve IDs (likely for internal tracking) but publishes fewer complete entries.

### Revised understanding of the dataset

| Aspect | Original understanding | Revised understanding |
|--------|----------------------|----------------------|
| Dataset size | "127,562 vulnerabilities" | 127,562 entries with content out of ~500,000+ reserved CNVD IDs |
| Completeness | Assumed near-complete CNVD mirror | ~10–25% of CNVD IDs have published content (varies by year) |
| 2022 cliff cause | RMSV filtering or CIRCL curation | CNVD publishing fewer complete entries post-RMSV |
| CNVD annual volume | ~10,000–18,000 (from dataset) | ~50,000–100,000 reserved IDs per year |
| Dataset maintenance | Single dump | Actively updated monthly (14 commits since June 2025) |

### Impact on original brief

- The "127,562 vulnerabilities" framing is accurate for entries with content, but understates the total CNVD namespace
- The RMSV impact is confirmed but operates differently than initially hypothesised: it reduced CNVD's *publication rate*, not CIRCL's inclusion rate
- The 19.2% CNVD-only finding from V1 should be understood in context: these are the entries that CNVD chose to publish with full details but without CVE mapping — a deliberate publication decision, not an oversight

---

## 7. Methodology Notes

- **CNVD website:** Returned HTTP 521 (Cloudflare block) — direct access failed from European IP
- **Wayback Machine:** No accessible snapshots for 2022–2026
- **Sequence analysis:** Based on CNVD ID pattern `CNVD-YYYY-NNNNN`, extracting max sequence per year
- **Missing ID probes:** 100 entries (25/year for 2020–2023) via Vulnerability-Lookup API, 0.5s rate limiting
- **HF commit history:** Via `huggingface_hub` API
- **ML-Gateway:** Git clone of `vulnerability-lookup/ML-Gateway`, grep for preprocessing/filtering code
- **Raw data:** `v4_provenance_probes.csv`
- **Full methodology:** [V4 Dataset Provenance](../methodology/V4-Dataset-Provenance.md)
