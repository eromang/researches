# GitHub issue draft

**Target repository:** `vulnerability-lookup/vulnerability-lookup` (or `CIRCL/Vulnerability-CNVD` discussions on Hugging Face)

---

## Issue title

Technical review: CNVD dataset CVE overlap, model leakage, and severity classification behaviour

---

## Issue body

Hi,

I ran a technical review of the `CIRCL/Vulnerability-CNVD` dataset and the `CIRCL/vulnerability-severity-classification-chinese-macbert-base` model after seeing the March 2026 announcement. Sharing findings below in case they're useful. All data and code are available on request.

### Dataset: 81% of entries map to existing CVEs

I queried the Vulnerability-Lookup API for 10,457 stratified entries to check CNVD-to-CVE mappings.

- **81.0% have a CVE equivalent** (99% CI: 80.0%-82.0%)
- **19.0% are CNVD-only** (~24,200 entries, 99% CI: 18.0%-20.0%)
- CNVD-only entries are concentrated in 2020-2021 (68-69% CVE mapping rate). After 2022 the rate jumps to 91-97%.
- CNVD-only entries are dominated by Chinese domestic PHP CMS and ERP systems. Western vendors (Adobe, Microsoft, IBM, Cisco) are absent from the CNVD-only subset.

The dataset contains all CNVD entries with published content. CNVD reserves 50,000-100,000 IDs per year but publishes full details for only a fraction (94% in 2015, dropping to 4% in 2023). Missing IDs are empty stubs with no description or severity. The coverage decline coincides with China's RMSV regulations (September 2021).

**Suggestion:** Document the CVE overlap rate in the dataset README. Consider adding CVE cross-references as a dataset field since the mapping already exists in the VL API.

### Model: data leakage in train/test split

I reproduced the reported 77.83% accuracy (got 78.29%). However, the train/test split has a leakage issue.

1,587 unique description texts appear in both splits under different CNVD IDs. This affects 1,993 test entries (15.6% of the test set). CNVD reuses boilerplate descriptions across product-specific vulnerability IDs; the split was done on IDs, not on description text.

- Leaked entries accuracy: 87.6%
- Unleaked entries accuracy: **76.6%**
- Inflation from leakage: ~1.7pp on the headline number

76.6% still outperforms a keyword heuristic baseline by 12.2pp, so the model adds real value. The leakage inflates the number but doesn't invalidate the model.

**Suggestion:** Deduplicate on description text before splitting, or report both the headline and unleaked accuracy.

### Model: Low severity recall is 38.4%

Per-class metrics on unleaked data:

```
Class     Precision   Recall   F1      n
High      0.777       0.736    0.756   3721
Medium    0.772       0.847    0.807   6046
Low       0.636       0.384    0.479   997
```

60% of Low entries are misclassified, 92% of those as Medium. The model has a strong Medium bias on the Low class.

**Suggestion:** Consider class-weighted loss or oversampling for the Low class. Reporting per-class metrics alongside overall accuracy would help consumers assess fitness for their use case.

### Model: keyword dependency

I measured accuracy on entries where actual severity deviates from the vulnerability type's typical severity (e.g., High-severity XSS, which is typically Medium). Across 10,787 entries in 12 vulnerability types:

- Typical entries: **89.4% accuracy**
- Atypical entries: **55.4% accuracy**
- Chi-squared = 1607, p near zero

The model biases toward the vulnerability type's default severity. When a vulnerability has an unusual severity for its type, accuracy drops to near-random.

A deterministic keyword heuristic achieves 64.4% accuracy, so the model does learn patterns beyond flat keyword matching (+12.2pp). But adversarial tests show it is negation-blind ("does NOT have RCE" still predicts High with 0.791 confidence) and can produce high-confidence predictions from 2-4 word inputs alone.

**Suggestion:** Document keyword dependency and negation blindness as known limitations.

### Minor: published checkpoint is not optimal

The model card shows validation loss increasing after epoch 3 (1.0848 to 1.2224 at epoch 5). The published model is epoch 5; epoch 3 had slightly better accuracy (78.29% vs 77.83%). The overfit penalty is small (0.46pp).

### Methodology

- Dataset overlap: 10,457 stratified samples via VL API, 99% CI +/-1.0%
- Model evaluation: inference on 12,757 test entries, leakage analysis, keyword heuristic baseline, adversarial tests
- Provenance: CNVD ID sequence gap analysis (127,562 entries) + 100 missing ID probes via VL API
- All code ran on Python 3.13.3, Apple Silicon (MPS), using datasets, transformers, torch, scikit-learn, scipy

Happy to share the raw data, code, or more detailed findings if useful. This was done out of interest in the project, not as criticism. The dataset and the work behind it are valuable.

Eric Romang
