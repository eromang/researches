# CNVD Dataset Validation — Technical Challenge Project

## Context

In March 2026, the CIRCL-affiliated Vulnerability-Lookup project released a dataset of 127,562 entries from China's National Vulnerability Database (CNVD) on Hugging Face, along with a fine-tuned `hfl/chinese-macbert-base` model for automated vulnerability classification.

An initial threat intelligence brief (2026-03-23 - CNVD Dataset Hugging Face - Brief) assessed the dataset as a net coverage expansion for Western vulnerability intelligence. This project exists to technically validate or challenge that assessment.

### Source materials

| Resource | Location |
|----------|----------|
| Hugging Face dataset | `CIRCL/Vulnerability-CNVD` (Hugging Face) |
| Fine-tuned model | `CIRCL/vulnerability-severity-classification-chinese-macbert-base` (Hugging Face) |
| Base model | `hfl/chinese-macbert-base` (Hugging Face) |
| Collection | VLAI for Severity (Hugging Face) |
| Vulnerability-Lookup example | CNVD integration in Vulnerability-Lookup |
| Feedback channel | Vulnerability-Lookup GitHub Discussions |

### Dataset schema (verified 2026-03-23)

| Field | Type | Example |
|-------|------|---------|
| `id` | string (14–16 chars) | `CNVD-2020-20184` |
| `title` | string (Chinese, 7–141 chars) | `流星网络电视存在代码执行漏洞` |
| `description` | string (Chinese, 25–1256 chars) | Detailed vulnerability description (mean: 144 chars) |
| `severity` | 3-class (Chinese) | `高` (High) / `中` (Medium) / `低` (Low) |

- **127,562 entries** (train: 114,805 / test: 12,757) — `split` is implicit, not a data column
- **Format:** Apache Parquet (23.9 MB)
- **No CVE column** — CNVD identifiers only
- **No CVSS scores** — severity is categorical (高/中/低)
- **All text in Simplified Chinese**
- **Severity distribution:** 中 55.1% / 高 36.1% / 低 8.8%
- **Year range:** 2016–2025 (from CNVD ID pattern)

---

## Validation Plan

### V1 — NVD overlap analysis

> [!NOTE]
> **V1 COMPLETE — 2026-03-24**
> **Result:** 80.8% CVE-mapped / 19.2% CNVD-only (~24,400 entries, 95% CI ±2.2%)
> - See [V1 Findings Report](findings/V1-NVD-Overlap-Findings.md) for full findings
> - See [V1 NVD Overlap Analysis](methodology/V1-NVD-Overlap-Analysis.md) for methodology and code

**Question:** How many of the 127,562 entries are net-new vs NVD mirrors?

**Answer:** 80.8% map to existing CVEs. 19.2% (~24,400) are genuinely CNVD-only, concentrated in 2019–2021 and dominated by Chinese domestic enterprise software (OA, ERP, CMS). High-severity entries are disproportionately CNVD-only (p < 0.0001). The 2022 RMSV cliff remains an open question.

**Status:** Complete

---

### V2 — Model quality evaluation

> [!NOTE]
> **V2 COMPLETE — 2026-03-24**
> **Result:** 78.29% accuracy confirmed. Effective as High-vs-Medium classifier. Low recall broken (39.8%). ECE 0.053.
> - See [V2 Findings Report](findings/V2-Model-Quality-Findings.md) for full findings
> - See [V2 Model Quality Evaluation](methodology/V2-Model-Quality-Evaluation.md) for methodology and code

**Question:** Is the CIRCL severity classifier (77.83% self-reported accuracy) actually useful for operational triage?

**Answer:** Partially. The model works as a binary High-vs-Medium classifier (+22.7pp over majority baseline) but fails on Low severity (39.8% recall — 60% misclassified as Medium). Confidence scores are directionally useful; a 0.9 threshold yields 91.6% accuracy on 46% of predictions. Low recall degrades further on post-2024 data (18–25%). Mild overfitting (epoch 5 published, epoch 3 was optimal).

**Status:** Complete

---

### V3 — Model integrity — systematic bias detection

> [!WARNING]
> **V3 COMPLETE — 2026-03-24 (corrected by R1/R2)**
> **Result:** The model is keyword-dependent but not a simple lookup table. It outperforms a keyword heuristic by 13.9pp (R1) while showing 34pp typical-atypical accuracy gap (R2). Negation-blind, impact-insensitive.
> - See [V3 Findings Report](findings/V3-Bias-Detection-Findings.md) for full findings (updated with R1/R2 corrections)
> - See [V3 Systematic Bias Detection](methodology/V3-Systematic-Bias-Detection.md) for methodology

**Question:** Does the model have systematic blind spots by vulnerability type, vendor, or description pattern?

**Answer:** Yes. The model strongly biases toward type-default severity (R2: 89.4% accuracy on typical entries vs 55.4% on atypical, χ²=1607, p≈0). It ignores negation and impact descriptions. Huawei is the worst vendor (-12.6pp). However, R1 showed a keyword heuristic achieves only 64.4% vs the model's 78.3% — the model captures patterns beyond flat keyword matching. Original verdict ("functionally equivalent to a lookup table") was overstated.

**Status:** Complete

---

### V4 — Dataset provenance — filtering detection

> [!NOTE]
> **V4 COMPLETE — 2026-03-24**
> **Result:** Dataset contains all CNVD entries with content (~10–25% of reserved IDs). CNVD reserves ~100,000 IDs/year but publishes full details for only a fraction. 2022 cliff is real — CNVD reduced publication rate post-RMSV, not CIRCL filtering.
> - See [V4 Findings Report](findings/V4-Dataset-Provenance-Findings.md) for full findings
> - See [V4 Dataset Provenance](methodology/V4-Dataset-Provenance.md) for methodology

**Question:** Is the HF dataset the full CNVD or a curated subset, and what explains the 2022 cliff?

**Answer:** The HF dataset contains all CNVD entries with actual content (title + description + severity). Missing IDs are empty stubs — reserved but never populated. CNVD reserves ~100,000 IDs/year but published only 4–17% with full details post-2020. The 2022 cliff reflects CNVD reducing its publication rate after RMSV, not CIRCL filtering. The dataset is actively maintained (14 commits, monthly updates).

**Status:** Complete

---

### V5 — Vulnerability-Lookup integration audit

> [!NOTE]
> **V5 COMPLETE — 2026-03-24**
> **Result:** Model is NOT in the CNVD data pipeline. It's a client-side JavaScript enrichment in the web UI — on-demand, transient, silently removed if ML-Gateway is down. API serves raw CNVD severity. Zero mismatches across 50 entries.
> - See [V5 Findings Report](findings/V5-Integration-Audit-Findings.md) for full findings
> - See [V5 Integration Audit](methodology/V5-Integration-Audit.md) for methodology and code

**Question:** Does Vulnerability-Lookup actually use the MacBERT model in production, and if so, how are predictions exposed to end users?

**Answer:** The model is NOT integrated into the CNVD ingestion pipeline. CNVD severity is stored and served as raw source data. The model exists as an optional client-side enrichment — JavaScript calls ML-Gateway on page load and displays a prediction badge alongside (not replacing) the original severity. If ML-Gateway is down, the badge silently disappears. The API exposes no model fields. Zero severity mismatches found. The model is functionally a nice-to-have UI widget, not production infrastructure.

**Status:** Complete

---

### V6 — Reproducibility — independent model rebuild

> [!NOTE]
> Detailed instructions
> See [V6 Reproducibility](methodology/V6-Reproducibility.md) for full step-by-step procedure (5 steps, estimated 1–2 hours).

**Question:** Can the fine-tuning be independently reproduced, and does the keyword-classifier behaviour persist?

**Method (reframed after V2–V5):**
- Reproduce the fine-tuning with documented parameters (5 epochs, lr=3e-05, batch=32, seed=42)
- Compare training dynamics (per-epoch val loss and accuracy) against CIRCL's model card
- Compare predictions on test set — agreement rate between reproduced and published model
- Run V3 adversarial tests on reproduced model — confirm keyword dependency is inherent to data+architecture
- Optional: retrain with class-weighted loss to fix Low recall

**Priority:** Lowest. V1–V5 provide a comprehensive picture. V6 is a scientific reproducibility check — most valuable if you plan to retrain a better model.

**Status:** Skipped (R1/R2 already prove keyword dependency is inherent to the data; 8.5h compute for confirmatory result not justified)

---

## Priority Order

| Priority | Validation | Rationale |
|----------|------------|-----------|
| 1 | V1 — NVD overlap | Highest value, lowest effort. Determines if the core coverage claim holds. |
| 2 | V4 — Provenance | Can be done with web scraping only. Reveals filtering if present. |
| 3 | V2 — Model quality | Requires ML setup but directly tests the tool's utility. |
| 4 | V3 — Bias detection | Builds on V2 infrastructure. |
| 5 | V5 — Integration audit | Code review only. Useful but not blocking. |
| 6 | V6 — Reproducibility | Most resource-intensive. Only necessary if V2/V3 raise flags. |

### Evidence reinforcement

> See [Reinforcement Plan](Reinforcement-Plan.md) for 6 prioritised fixes to strengthen V1–V5 findings to citation quality.

---

## Regulatory Context

> [!WARNING]
> **RMSV — China's 2021 Vulnerability Disclosure Regulations**
> China's Regulations on the Management of Security Vulnerabilities (RMSV, effective September 2021) require Chinese researchers to report vulnerabilities to MIIT before public disclosure. This applies to CNVD (CNCERT/MIIT), not only CNNVD (MSS). The "open track" (CNVD) may therefore also reflect state-managed disclosure timing, just via a different ministry. Any validation work should account for this structural constraint.

---

## Log

| Date | Entry |
|------|-------|
| 2026-03-23 | Project created. Initial threat intel brief completed. Six validation tracks defined. |
| 2026-03-23 | Dataset schema verified. Correct URL: `CIRCL/Vulnerability-CNVD`. No CVE column — overlap analysis requires CNVD→CVE reverse lookup. Severity is 3-class categorical, not CVSS. Model is for severity classification only. |
| 2026-03-24 | V1 complete. Steps 1–7 executed. 1,232-sample reverse lookup: 80.8% CVE-mapped, 19.2% CNVD-only (~24,400 entries). Severity skew significant (p < 0.0001). Vendor analysis: 94% Western software, 5.9% Chinese vendors. Findings report generated. Brief updated. |
| 2026-03-24 | V2 complete. Model accuracy confirmed (78.29%). Per-class: High/Medium acceptable, Low broken (39.8% recall). ECE 0.053. Low recall collapses post-2024 (18–25%). Mild overfitting (epoch 5 vs optimal epoch 3). Findings report generated. |
| 2026-03-24 | V3 complete. Model is a keyword-to-severity lookup table. Adversarial tests: keyword dependency confirmed, negation blindness confirmed, 2-4 words sufficient for high-confidence prediction. Huawei worst vendor (-12.6pp). Findings report generated. |
| 2026-03-24 | V4 complete. Dataset is NOT filtered by CIRCL — contains all CNVD entries with content. Missing IDs are empty stubs. CNVD reserves ~100K IDs/year but publishes only 4–25% with details. 2022 cliff is CNVD publication rate drop post-RMSV. Dataset actively maintained (14 HF commits, monthly updates). |
| 2026-03-24 | V5 complete. Model NOT in CNVD data pipeline. Client-side JS enrichment in web UI — on-demand, transient, no storage, silently removed if ML-Gateway down. API serves raw CNVD severity. Zero mismatches (50 entries). Model is a UI widget, not production infrastructure. |
| 2026-03-24 | R1 complete. Keyword heuristic: 64.4% vs model 78.3% — model outperforms by 13.9pp. V3 "lookup table" verdict **overstated**; model captures more than flat keywords. V3 findings report corrected. |
| 2026-03-24 | R2 complete. Typical vs atypical: 89.4% vs 55.4% (χ²=1607, p≈0, n=10,787). Keyword dependency proven at scale — but R1 shows model still adds value over heuristic. |
| 2026-03-24 | R3 complete. VLAI endpoint LIVE — all 3 models responding (MacBERT, RoBERTa, default). V5 updated. |
| 2026-03-24 | R4 running. 10,500-sample reverse lookup for 99% CI ±1.0%. ETA ~90 min. |
| 2026-03-24 | R7 complete. CNVD-only tail confirmed Chinese-domestic: PHP CMS 25%, Chinese-only vendors (Hikvision, Kingsoft, UFIDA, Panwei), shorter descriptions, higher severity. Western vendors absent. |
| 2026-03-24 | R8 complete. **DATA LEAKAGE DETECTED:** 1,587 exact duplicate descriptions (12.4% of test set) across train/test. V2's 78.3% accuracy is likely inflated. Boilerplate CNVD descriptions reused across CNVD IDs. |
| 2026-03-24 | R9 complete. VL stores CNVD↔CVE links internally but doesn't expose them via API (404 on /links endpoint). Cross-reference exists in code but not in user-facing interface. |
| 2026-03-24 | R10 complete. Low misclassification driven by keyword dependency: Low entries with "typically High" types → 87–100% miss rate. Model never predicts Low unless the vulnerability type itself is typically Low. |
| 2026-03-24 | R11 complete. True accuracy is **76.6%** (not 78.3%). Leakage inflates by 1.7pp. 15.6% of test set has exact duplicate descriptions in train. |
| 2026-03-24 | R12 complete. Leakage confirmed: 94.1% of shared descriptions have same severity in both splits. Caused by CNVD boilerplate reuse across product IDs. |
| 2026-03-24 | R13 complete. 71.7% of test set shares 50-char prefix with train — but these are legitimate similar entries, not leakage. Cleanest accuracy (no prefix matches): 76.69%. |
| 2026-03-24 | R14 complete. OOD accuracy: 80.56% but only n=36 (insufficient). Most non-dataset CNVD IDs are empty stubs. Inconclusive — R11's 76.6% remains the best corrected metric. |
| 2026-03-24 | **R4 complete.** 10,457 samples: **CNVD-only 19.0% (99% CI: 18.0%-20.0%, ±1.0%)**. CVE mapping 81.0%. Confirms 1,232-sample estimate. Severity skew confirmed (χ²=69.94, p=6.5e-16): High 77.3%, Medium 82.3%, Low 88.0%. Consolidated report finalised. |
| 2026-03-24 | V6 skipped. Retraining would reproduce the same keyword-dependent behaviour (proven by R1/R2). Not worth 8.5h compute for a confirmatory result. |
| 2026-03-24 | **PROJECT COMPLETE.** V1–V5 executed, R1–R14 reinforcements done, consolidated report and GitHub issue drafted. V6 skipped (justified). |
| 2026-08-07 | Project reopened. Backlog written retroactively; the drafted GitHub issue found never to have been filed. |
| 2026-08-07 | **R11 re-run — result DISCARDED, and it reversed the R8 conclusion.** The re-run scored 84.97% "unleaked" against March's 76.6%. The jump was an artifact: it evaluated the model on the dataset's **published** split, much of which lies inside the model's own grouped training split. Chasing the anomaly to the model card revealed the real state — CIRCL now trains on an **80/20 split deduplicated on description text** (25,878 test rows) and reports **76.85%**, against this project's independently computed **76.6%**. **The defect was fixed and the correction was adopted; the agreement is 0.25pp.** The invalid script and output are kept, not deleted. Consequence: the drafted GitHub issue is **dropped** — filing it would have reported a resolved defect. |
| 2026-08-07 | ⚠️ **The entry below is correct in its numbers and wrong in its conclusion.** Kept as written, with the correction above it, rather than edited into agreement. |
| 2026-08-07 | **R8 re-run on the current dataset — leakage NOT fixed.** Revision `fcfa1153` (modified 2026-07-06): 2,059 test entries carry a train description, **15.95%** against 15.6% in March. Corpus +1,541 entries, split still ID-based (0 ID overlaps, 1,613 shared descriptions, 424 shared titles). Method reproduced faithfully — the 50-char prefix control returns 71.5% against R13's 71.7%. The V2/R11 correction stands: the published accuracy remains inflated. **Scope limit:** this measures the dataset, not the current checkpoint — whether the published model was retrained on this revision is unknown (Q5b, T4). |
