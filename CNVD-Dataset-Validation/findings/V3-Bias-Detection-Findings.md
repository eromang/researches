# V3 — Systematic Bias Detection — Findings Report

**Model:** `CIRCL/vulnerability-severity-classification-chinese-macbert-base`
**Date:** 2026-03-24
**Test set:** 12,757 entries (enriched with vulnerability types via keyword extraction)

---

## 1. Executive Finding

**The model is heavily keyword-dependent but not reducible to a simple keyword heuristic.** Adversarial testing demonstrates that the model biases toward vulnerability type default severity (RCE → High, XSS → Medium), is blind to negation, and ignores impact descriptions. When a vulnerability deviates from its type's typical severity, accuracy drops from 89.4% to 55.4% (χ²=1607, p≈0, n=10,787 — R2 reinforcement). However, a deterministic keyword heuristic achieves only 64.4% accuracy vs the model's 78.3% — a 13.9pp gap (R1 reinforcement). The model captures keyword combinations and contextual patterns beyond flat keyword matching, but fundamentally defaults to type-based severity when uncertain.

> [!WARNING] R1/R2 correction (2026-03-24)
> The original V3 verdict ("functionally equivalent to a lookup table") was overstated. R1 demonstrated the model outperforms a keyword heuristic by 13.9pp. The corrected assessment: the model is keyword-dependent (proven at scale by R2) but captures more than a flat heuristic (proven by R1). It is a sophisticated keyword classifier, not a simple lookup table.

---

## 2. Vulnerability Type Accuracy

### 2.1 Accuracy by type (baseline: 78.3%)

| Vulnerability type | n | Accuracy | Δ baseline | High recall | Low recall | Assessment |
|-------------------|---|----------|------------|-------------|------------|------------|
| CSRF | 232 | 84.5% | +6.2pp | 14.3% | 0.0% | Strong on Medium (85% are Medium) |
| RCE | 1,271 | 81.9% | +3.6pp | 93.0% | 13.0% | Strong on High (75% are High) |
| Buffer Overflow | 1,028 | 81.3% | +3.0pp | 84.9% | 28.1% | Good |
| XSS | 1,441 | 81.0% | +2.7pp | **17.1%** | 45.3% | Broken on High — 83% of High XSS missed |
| Info Disclosure | 1,464 | 80.1% | +1.8pp | **32.0%** | 50.6% | Broken on High — 68% missed |
| File Upload | 399 | 78.7% | +0.4pp | 90.7% | 87.2% | Balanced |
| SQL Injection | 1,182 | 77.7% | -0.5pp | 81.7% | **0.0%** | Zero Low detection |
| DoS | 1,601 | 77.5% | -0.8pp | **54.1%** | 36.6% | Half of High DoS missed |
| Unspecified | 1,124 | 74.0% | -4.3pp | 59.0% | 22.9% | Below baseline |
| Auth Bypass | 266 | 73.3% | -5.0pp | 67.9% | 38.9% | Borderline blind spot |
| Path Traversal | 188 | 73.9% | -4.4pp | **34.2%** | 23.1% | 66% of High missed |
| **Privilege Escalation** | **591** | **69.4%** | **-8.9pp** | 78.7% | **21.1%** | **Blind spot** |
| **Hardcoded Credentials** | **35** | **62.9%** | **-15.4pp** | 66.7% | N/A | **Worst performer** |

### 2.2 Pattern: type keyword → default severity

The model has learned a mapping from vulnerability type keywords to "typical" severity:

| Type keyword | Model's default prediction | Actual typical severity | Match? |
|-------------|---------------------------|----------------------|--------|
| 远程代码执行 (RCE) | High | 74.6% High | Yes |
| 缓冲区溢出 (Buffer Overflow) | High | 52.9% High | Mostly |
| SQL注入 (SQL Injection) | High | 65.1% High | Mostly |
| 跨站脚本 (XSS) | Medium | 74.9% Medium | Yes |
| 信息泄露 (Info Disclosure) | Medium | 73.6% Medium | Yes |
| 拒绝服务 (DoS) | Medium | 68.2% Medium | Yes |
| 跨站请求伪造 (CSRF) | Medium | 84.9% Medium | Yes |

When the actual severity matches the type's typical severity, the model performs well (80–95% recall). When it doesn't (e.g., High-severity XSS, Low-severity SQL injection), the model fails because it relies on the type keyword, not the impact description.

---

## 3. Vendor Accuracy

| Vendor | n | Accuracy | Δ baseline | %Low | Assessment |
|--------|---|----------|------------|------|------------|
| Foxit | 104 | 95.2% | +16.9pp | 3.8% | Best — low ambiguity |
| Seeyon (致远) | 37 | 91.9% | +13.6pp | 2.7% | Strong — mostly High |
| Adobe | 514 | 91.6% | +13.3pp | 2.1% | Strong |
| UFIDA (用友) | 23 | 91.3% | +13.0pp | 0.0% | Strong (small n) |
| D-Link | 129 | 88.4% | +10.1pp | 1.6% | Strong |
| PHP | 1,726 | 80.4% | +2.1pp | 8.9% | Good |
| Microsoft | 574 | 79.1% | +0.8pp | 9.2% | Average |
| Google | 809 | 78.0% | -0.3pp | 8.4% | Average |
| Linux | 897 | 75.1% | -3.1pp | 11.9% | Below average |
| Oracle | 515 | 74.2% | -4.1pp | 16.7% | Below average |
| IBM | 501 | 71.9% | -6.4pp | 20.4% | Below — high Low% |
| **Cisco** | **319** | **71.2%** | **-7.1pp** | 6.0% | **Underperforming** |
| **Huawei (华为)** | **198** | **65.7%** | **-12.6pp** | **15.2%** | **Worst vendor** |

**Pattern:** Vendor accuracy correlates inversely with Low severity proportion. Vendors with >10% Low entries (Huawei 15.2%, IBM 20.4%, Oracle 16.7%) underperform because the model cannot classify Low.

**Chinese domestic vendors** (Seeyon, UFIDA) perform *better* than the baseline — but only because their vulnerabilities are predominantly High severity, which the model handles well.

---

## 4. Description Length Effect

| Length (chars) | n | Accuracy | Δ baseline | Confidence |
|---------------|---|----------|------------|------------|
| 0–50 | 33 | **69.7%** | **-8.6pp** | **0.878** |
| 50–80 | 1,022 | 84.1% | +5.9pp | 0.880 |
| 80–100 | 1,814 | 80.9% | +2.6pp | 0.847 |
| 100–130 | 2,972 | 78.4% | +0.1pp | 0.830 |
| 130–170 | 3,577 | 77.0% | -1.3pp | 0.829 |
| 170–250 | 2,812 | 76.6% | -1.7pp | 0.827 |
| 250–500 | 524 | 75.4% | -2.9pp | 0.838 |

**Key finding:** Very short descriptions (<50 chars) have the worst accuracy but the highest confidence — the model is **most overconfident on the least informative text**. The sweet spot is 50–100 characters.

---

## 5. Adversarial Robustness

### 5.1 Keyword dependency — CONFIRMED

| Test | Description | Prediction | Conf | Finding |
|------|-------------|-----------|------|---------|
| Control | RCE keyword + RCE impact | **High** | 0.791 | Baseline |
| Swap type | **XSS keyword** + RCE impact | **Medium** | 0.771 | Type keyword overrides impact |
| Swap type | InfoDisc keyword + RCE impact | High | 0.526 | Borderline — type pulls toward Medium |
| Swap type | SQLi keyword + RCE impact | High | 0.603 | Type pulls toward High (correct here) |

**Verdict:** Swapping "远程代码执行" to "跨站脚本" while keeping the impact phrase "执行任意代码" (execute arbitrary code) identical flips the prediction from High to Medium. The model classifies by type keyword, not by impact.

### 5.2 Impact insensitivity — CONFIRMED

| Test | Description | Prediction | Conf |
|------|-------------|-----------|------|
| RCE + RCE impact | "执行任意代码" | High | 0.791 |
| RCE + InfoDisc impact | "获取敏感信息" | High | 0.597 |
| RCE + DoS impact | "导致拒绝服务" | High | 0.844 |

**Verdict:** Changing the impact from "execute arbitrary code" to "obtain sensitive information" while keeping the RCE type keyword barely changes the prediction. The model ignores the impact clause.

### 5.3 Minimal text — 4 characters is enough

| Input | Prediction | Confidence |
|-------|-----------|------------|
| 代码执行漏洞 (code execution vuln) | High | **0.897** |
| 信息泄露 (info disclosure) | Medium | 0.858 |
| 缓冲区溢出 (buffer overflow) | High | 0.764 |
| 跨站脚本 (XSS) | Medium | 0.794 |
| SQL注入 (SQL injection) | Medium | 0.607 |
| 拒绝服务 (DoS) | Medium | 0.874 |
| 权限提升 (privilege escalation) | Medium | 0.696 |

**Verdict:** The model produces high-confidence predictions from 2–4 word type names alone. The remaining 100+ characters of description are largely ignored.

### 5.4 Negation blindness — CONFIRMED

| Input | Prediction | Confidence |
|-------|-----------|------------|
| "存在远程代码执行漏洞..." (has RCE) | High | 0.807 |
| "不存在远程代码执行漏洞" (does NOT have RCE) | **High** | **0.791** |
| "已修复远程代码执行漏洞" (RCE fixed/patched) | **High** | 0.693 |

**Verdict:** The model cannot distinguish between "has a vulnerability", "does not have a vulnerability", and "vulnerability has been fixed". It responds to the presence of the keyword "远程代码执行" regardless of context.

### 5.5 Severity qualifiers — partially working

| Input | Prediction | Confidence |
|-------|-----------|------------|
| "严重的远程代码执行漏洞，系统完全被控制" (severe RCE, full control) | High | **0.968** |
| "轻微的信息泄露漏洞，影响范围有限" (minor info disc, limited) | Medium | 0.782 |
| "存在远程代码执行漏洞" (neutral RCE) | High | 0.808 |

**Verdict:** Severity qualifiers (严重/轻微) and impact scope descriptions do modulate confidence slightly, but the label prediction is determined by the type keyword. The model does not change its classification based on qualifiers.

---

## 6. CNVD-only vs CVE-mapped

| Category | n (in test set) | Accuracy | Confidence |
|----------|----------------|----------|------------|
| CNVD-only | 21 | 81.0% | 0.909 |
| CVE-mapped | 89 | 74.2% | 0.842 |

> [!NOTE] Insufficient sample
> Only 110 entries from the V1 sample overlap with the test set. These results are indicative but not statistically robust. CNVD-only entries perform better likely because they are skewed toward High severity (which the model handles well).

---

## 7. Verdict

### The model is a keyword-dependent severity classifier

The adversarial tests and reinforcement analysis show the model:

1. **Biases heavily toward vulnerability type default severity** — RCE/buffer overflow → High, XSS/info disclosure/DoS → Medium
2. **Ignores the impact description** — changing "execute arbitrary code" to "obtain sensitive information" does not change the prediction
3. **Ignores negation** — "does not have" and "has been fixed" produce the same prediction as "has"
4. **Needs only 2–4 words** to make a high-confidence prediction — but captures more than just the top keyword
5. **Fails on atypical severity** — when a vulnerability type has unusual severity, accuracy drops from 89.4% to 55.4% (R2: χ²=1607, p≈0, n=10,787)
6. **BUT outperforms a keyword heuristic by 13.9pp** (R1: 78.3% vs 64.4%) — captures keyword combinations and contextual patterns beyond flat matching

### Assessment against thresholds

| Metric | Value | Rating |
|--------|-------|--------|
| Accuracy delta by vuln type (worst) | -15.4pp (Hardcoded Credentials) | **Major concern** |
| Accuracy delta by vendor (worst) | -12.6pp (Huawei) | **Major concern** |
| Keyword dependency | Type keyword strongly biases prediction (R2: 34pp typical-atypical gap) | **Major concern** |
| Negation blindness | Confirmed — ignores negation | **Major concern** |
| Model vs keyword heuristic | +13.9pp (R1) | Model adds genuine value |
| CNVD-only vs CVE-mapped delta | -6.8pp (insufficient n) | Inconclusive |

### Impact on original claims

The LinkedIn post describes this as "a fine-tuned version" used in Vulnerability-Lookup, implying sophisticated AI-driven severity assessment. V3 + R1/R2 demonstrate the model is a **keyword-dependent severity classifier** — better than a simple heuristic (+13.9pp, R1) but fundamentally biased toward type-default severity and unable to handle atypical entries (55.4% accuracy, R2).

A deterministic keyword heuristic achieves 64.4% accuracy — the model's 78.3% represents genuine learned patterns beyond flat keyword matching, but the model remains negation-blind, impact-insensitive, and unreliable for entries that deviate from type-typical severity.

---

## 8. Charts

- `v2_confusion_matrix.png` — from V2, still applies
- No additional charts generated for V3 (findings are tabular and adversarial)

---

## 9. Methodology Notes

- **Vulnerability types:** 17 categories extracted via Chinese keyword matching, covering 85.5% of test entries
- **Adversarial tests:** 20 manually crafted input pairs testing keyword dependency, impact insensitivity, minimal text, negation, and severity qualifiers
- **V1 cross-reference:** Limited to 110 overlapping entries between V1 sample and test set
- **Raw data:** `v3_enriched_predictions.csv` (12,757 records with vulnerability types)
- **Full methodology:** [V3 Systematic Bias Detection](../methodology/V3-Systematic-Bias-Detection.md)
