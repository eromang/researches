# CNVD Dataset Validation

Independent technical validation of the [CIRCL/Vulnerability-CNVD](https://huggingface.co/datasets/CIRCL/Vulnerability-CNVD) dataset and [severity classification model](https://huggingface.co/CIRCL/vulnerability-severity-classification-chinese-macbert-base) published on Hugging Face.

> See [VALIDATION.md](VALIDATION.md) for the full project overview, validation plan, and execution log.
> See [findings/](findings/) for per-track findings reports.
> See [methodology/](methodology/) for reproducible step-by-step procedures.

---

# Technical review of the CNVD dataset and severity classification model

**To:** CIRCL (Computer Incident Response Center Luxembourg)
**From:** Eric Romang
**Date:** 2026-03-24
**Subject:** Technical review of `CIRCL/Vulnerability-CNVD` dataset and `CIRCL/vulnerability-severity-classification-chinese-macbert-base` model
**Status:** Final

---

## Why this report exists

On 2026-03-23, CIRCL published an updated CNVD dataset on Hugging Face (127,562 entries) along with a fine-tuned MacBERT severity classification model. The announcement described the dataset as covering "127,562 vulnerabilities" and stated the model "is already used in Vulnerability-Lookup."

I ran a technical review to test these claims. Four review tracks were executed (dataset overlap, model quality, systematic bias, provenance), followed by 14 reinforcement tests to strengthen the evidence. All data, code, and intermediate results are available.

This report presents the findings factually. It is not a critique of CIRCL's work, which I consider valuable. It is an attempt to characterise what the dataset and model actually are, so that consumers can make informed decisions.

---

## 1. The dataset

### What it contains

The dataset has 127,562 entries with four fields: `id` (CNVD identifier), `title` (Chinese), `description` (Chinese), and `severity` (高/中/低). There are no CVE cross-references, no CVSS scores, no date fields, and no CWE classifications. The severity labels are categorical: High (36.1%), Medium (55.1%), Low (8.8%). Entries span 2010-2026, with 62% concentrated in 2017-2021.

### How much of it is new

I queried the Vulnerability-Lookup API for 10,457 stratified entries (proportional by year) to check whether each CNVD entry maps to an existing CVE.

81.0% of entries have a CVE equivalent. The remaining 19.0% (roughly 24,200 entries) are genuinely Chinese-domestic vulnerabilities without CVE identifiers. This figure carries a 99% confidence interval of +/-1.0% (18.0%-20.0%).

The CNVD-only entries are concentrated in 2020-2021, when the CVE mapping rate was 68-69%. After 2022, the rate jumped to 91-97%.

The severity breakdown is statistically significant (chi-squared = 69.94, p = 6.5e-16): High-severity entries have the lowest CVE mapping rate (77.3%), Medium 82.3%, and Low the highest (88.0%). Chinese-domestic vulnerabilities that never receive CVEs tend to be classified as high severity.

### What the CNVD-only entries actually are

I ran vendor keyword analysis on the CNVD-only subset separately from the CVE-mapped entries. The CNVD-only tail is dominated by Chinese domestic PHP CMS and ERP systems (25% match PHP-related keywords). Chinese-only vendors (Hikvision, Kingsoft, UFIDA/Yonyou, Panwei, H3C) appear in the CNVD-only set but not in the CVE-mapped set. Western vendors (Adobe, Microsoft, IBM, Cisco) are absent from the CNVD-only entries entirely.

Sample CNVD-only entries include products like 院校图书管控系统 (campus library management), 鑫众博考试服务平台 (exam service platform), 三一网络技术建站系统 (website builder), and 南京软核科技配变终端 (power distribution terminal). These are real Chinese domestic software products that do not participate in CVE assignment.

The operational value of these entries depends on whether the consumer uses Chinese domestic software. For most Western organisations, the 19.2% CNVD-only tail has limited practical relevance.

### The dataset is not the full CNVD

CNVD IDs follow the pattern `CNVD-YYYY-NNNNN`. By examining the maximum sequence number per year, I found that CNVD reserves 50,000-100,000 IDs per year (2019-2023), but only a fraction have published content.

| Year | In dataset | Max sequence | Coverage |
|------|-----------|-------------|----------|
| 2015 | 8,045 | 8,561 | 94% |
| 2020 | 18,201 | 75,709 | 24% |
| 2021 | 17,398 | 103,668 | 17% |
| 2023 | 4,129 | 101,689 | 4% |

I probed 100 missing CNVD IDs via the Vulnerability-Lookup API. All 100 returned HTTP 200 but contained no data: no description, no severity, no CVE mapping. They are empty stubs. CNVD reserves IDs that are never populated with vulnerability details.

The Hugging Face dataset is not filtered by CIRCL. It contains all CNVD entries that have actual content. The filtering happens upstream at CNVD itself. The dataset is a complete mirror of published CNVD entries, not a curated subset.

The coverage drop from 94% (2015) to 4% (2023) coincides with China's RMSV regulations (effective September 2021), which mandated state-first vulnerability disclosure. CNVD continued reserving IDs at the same rate but published fewer complete entries. This suggests vulnerability details are being redirected to government channels rather than public databases.

### The dataset is actively maintained

The Hugging Face repository has 14 commits between June 2025 and March 2026, with roughly monthly updates. The most recent upload was 2026-03-23, the day of the LinkedIn announcement.

---

## 2. The model

### Accuracy

CIRCL reports 77.83% accuracy. I reproduced 78.29% on the same test split (12,757 entries), within expected variance.

However, the test set has a data leakage problem. 1,587 unique descriptions appear in both the training and test splits under different CNVD IDs. This affects 1,993 test entries (15.6% of the test set). CNVD reuses boilerplate vulnerability descriptions across product IDs; the train/test split was done on IDs, not on description text.

The leaked entries have 87.6% accuracy. The unleaked entries have 76.6% accuracy. The difference is 11 percentage points. The true model accuracy on unseen text is 76.6%, not 78.3%.

76.6% is still 12.2 percentage points above a keyword heuristic baseline (64.4%) and 21 percentage points above the majority-class baseline (55.6%). The model adds real value. But the reported 78.3% is inflated by leakage.

I recommend CIRCL deduplicate descriptions before splitting and retrain, or at minimum report the unleaked accuracy alongside the headline number.

### Per-class performance

| Class | Precision | Recall | F1 | Support | Notes |
|-------|-----------|--------|----|---------|-------|
| High | 0.777 | 0.736 | 0.756 | 3,721 | Acceptable (unleaked) |
| Medium | 0.772 | 0.847 | 0.807 | 6,046 | Best class |
| Low | 0.636 | 0.384 | 0.479 | 997 | 60% of Low entries misclassified |

Low recall is 38.4% on unleaked data. 92% of misclassified Low entries are predicted as Medium. The model has a strong Medium bias and cannot reliably identify low-severity vulnerabilities.

### The model is keyword-dependent

I ran two tests to characterise how the model classifies severity.

First, I built a deterministic keyword heuristic based on Chinese vulnerability type keywords (e.g., if "远程代码执行" in text, predict High; if "跨站脚本" in text, predict Medium). This 15-line heuristic achieves 64.4% accuracy. The model at 76.6% outperforms it by 12.2 percentage points. The model is not a simple lookup table.

Second, I measured accuracy on entries where the actual severity deviates from the vulnerability type's typical severity. For example, most XSS vulnerabilities are Medium, but some are High. I call these "atypical" entries. Across 10,787 entries in 12 vulnerability types:

- Typical entries (severity matches the type's default): 89.4% accuracy
- Atypical entries (severity deviates from the type's default): 55.4% accuracy

The difference is 34 percentage points (chi-squared = 1607, p near zero). When a vulnerability deviates from its type's typical severity, the model gets it right only slightly better than random.

Specific examples:

- CSRF that is actually High severity: 11.4% accuracy (model predicts Medium 86% of the time)
- XSS that is actually High severity: model predicts Medium 57% of the time
- RCE that is actually Medium severity: model predicts High 46% of the time

The model also has two properties that are concerning from an NLP perspective:

**Negation blindness.** "存在远程代码执行漏洞" (has RCE vulnerability) and "不存在远程代码执行漏洞" (does NOT have RCE vulnerability) produce nearly identical predictions: High with 0.807 and 0.791 confidence respectively. The model responds to the presence of the keyword regardless of negation.

**Minimal text sufficiency.** A 4-character input like "代码执行漏洞" (code execution vulnerability) produces High with 0.897 confidence. The model does not need the full description to classify; 2-4 words of type keyword are sufficient for a high-confidence prediction.

These properties suggest the model learns a mapping from vulnerability type keywords to default severity levels. It captures more than flat keyword matching (it outperforms the heuristic by 12.2pp) but fundamentally defaults to type-based severity when uncertain.

### Overfitting

The training log from the model card shows validation loss increasing after epoch 3 (1.0848 to 1.2224 at epoch 5) while training loss continues to drop. The published model is epoch 5; epoch 3 achieved 78.29% accuracy. The overfit penalty is small (0.46pp) but the published checkpoint is not optimal.

### Calibration

The model's expected calibration error (ECE) is 0.053, which is acceptable. The model is consistently overconfident in the 0.7-0.9 confidence range (7-9pp gap between confidence and actual accuracy). At the extremes, calibration is reasonable: a 0.95+ confidence threshold yields 95.1% accuracy on 30% of predictions.

---

## 3. Summary of findings

| Claim | Finding |
|-------|---------|
| "127,562 vulnerabilities" | Accurate. The dataset contains 127,562 entries with content, out of roughly 500,000+ reserved CNVD IDs. |
| Implied: new vulnerability intelligence | Partially. 81.0% map to existing CVEs (n=10,457, 99% CI +/-1.0%). 19.0% (~24,200) are genuinely CNVD-only, mostly Chinese domestic software. |
| "We also trained a model" | Accurate. The model exists and achieves 76.6% accuracy on unleaked data (reported: 78.3%). |
| Implied: AI-driven severity assessment | Partially. The model outperforms a keyword heuristic by 12.2pp but is keyword-dependent, negation-blind, and unreliable on atypical entries (55.4% accuracy). Low severity recall is 38.4%. |
| Implied: China sharing data openly | Accurate for CNVD (CNCERT). CNVD publication rates have declined from 94% (2015) to 4% (2023), coinciding with RMSV regulations. The dataset is a mirror of what CNVD chooses to publish. |

---

## 4. Recommendations

These are operational observations, not prescriptions.

**On the dataset:**
- Document the CVE overlap rate in the dataset README so consumers know 81% of entries have CVE equivalents
- Consider adding CVE cross-reference as a dataset field (the data exists in VL's API)
- Note the RMSV-driven publication decline in the dataset documentation

**On the model:**
- Deduplicate descriptions before train/test splitting to eliminate the 15.6% leakage
- Report per-class metrics alongside overall accuracy, particularly Low recall
- Consider class-weighted loss or oversampling to address the 38.4% Low recall
- Consider publishing the epoch 3 checkpoint (best validation loss) alongside epoch 5
- Document the keyword dependency and negation blindness as known limitations

---

## 5. Methodology

This validation was conducted over 2026-03-23 and 2026-03-24. All code ran on Apple Silicon (MPS) using Python 3.13.3 with pandas, datasets, transformers, torch, scikit-learn, and scipy.

| Track | Method | Sample size |
|-------|--------|-------------|
| V1 - Dataset overlap | Stratified reverse lookup via VL API | 10,457 (99% CI +/-1.0%) |
| V2 - Model quality | Inference on held-out test split | 12,757 |
| V3 - Bias detection | Keyword extraction + adversarial tests + R1/R2 reinforcement | 12,757 + 20 adversarial + 10,787 typical/atypical |
| V4 - Provenance | Sequence gap analysis + missing ID probing | 127,562 (sequence) + 100 (probes) |
| R1-R14 | Reinforcement tests | Various |

Raw data files: [v1_reverse_lookup_10500.csv](data/v1_reverse_lookup_10500.csv), [v1_reverse_lookup_1225.csv](data/v1_reverse_lookup_1225.csv), [v2_test_predictions.csv](data/v2_test_predictions.csv), [v3_enriched_predictions.csv](data/v3_enriched_predictions.csv), [v4_provenance_probes.csv](data/v4_provenance_probes.csv), [r14_ood_predictions.csv](data/r14_ood_predictions.csv).

Full methodology notes, step-by-step code, and per-track findings reports are available in the project folder.

---

## 6. Note on this review

This work took approximately 16 hours across two days. I used Claude Code (Anthropic) for code generation, analysis, and report drafting. All API queries, model inference, and statistical tests were executed locally and verified against the actual data. The text in this report was written to be readable, not to obscure its origins.

I have no affiliation with CIRCL, CNVD, or any related organisation. This review was conducted out of professional interest.

---

*Eric Romang, 2026-03-24*
