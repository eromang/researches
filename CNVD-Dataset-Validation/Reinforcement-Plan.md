# CNVD Validation — Reinforcement Plan

Identified gaps in V1–V5 evidence and prioritised fixes to strengthen findings for citation-quality relevance.

---

## Priority Ranking

| Priority | Track | Reinforcement | Effort | Impact | Status |
|----------|-------|--------------|--------|--------|--------|
| **1** | V2/V3 | Keyword heuristic baseline accuracy | 30 min | If it matches model accuracy, "AI model" claim collapses entirely | Not started |
| **2** | V3 | Systematic keyword swap test (500+ pairs) | 1 hour | Converts anecdotal adversarial finding to statistical proof | Not started |
| **3** | V5 | Call VLAI endpoint directly | 5 min | Confirms whether the feature is live or dead in production | Not started |
| **4** | V1 | 10,500-sample reverse lookup (99% CI ±1.0%) | 116 min | Replaces ±2.2% with ±1.0% at 99% confidence — citable without qualification | **Complete** |
| ~~5~~ | V4 | ~~CNVD website via VPN (10 entries)~~ | ~~30 min~~ | ~~Confirms empty stubs are truly empty at source~~ | Skipped |
| **6** | V2 | Out-of-distribution evaluation (2026 entries) | 2 hours | Tests real-world generalisation | Not started |
| **7** | V1 | CNVD-only tail characterisation | 30 min | Proves CNVD-only entries are genuinely Chinese-domestic | Complete |
| **8** | V2 | Train/test leakage check | 30 min | Validates 78.3% accuracy is not inflated | Complete |
| **9** | V5 | VL cross-source deduplication | 20 min | Checks if VL links CNVD↔CVE entries | Complete |
| **10** | V2 | Low class deep-dive | 30 min | Explains why Low recall is 39.8% | Complete |
| **11** | V2 | Accuracy without leaked entries | 20 min | Corrects V2 headline number | Complete |
| **12** | V2 | Verify leakage type | 10 min | Confirms whether duplicates are true leakage | Complete |
| **13** | V2 | Near-duplicate analysis | 20 min | Quantifies broader contamination | Complete |
| **14** | V2 | Out-of-distribution eval (2026 entries) | ~30 min | Authoritative unleaked accuracy | Running |

---

## Detailed Specifications

### R1 — Keyword heuristic baseline (V2/V3)

**Gap:** V3 proved the model is a keyword classifier, but we never measured how a simple rule-based classifier compares on the same test set.

**Method:** Implement a deterministic heuristic from V3's adversarial findings and evaluate on the 12,757 test entries:

```
IF "远程代码执行" OR "代码执行" OR "命令执行" OR "命令注入" in text → High
ELIF "缓冲区溢出" OR "栈溢出" OR "堆溢出" in text → High
ELIF "SQL注入" in text → High
ELIF "权限提升" OR "提权" in text → High
ELIF "反序列化" in text → High
ELIF "硬编码" in text → High
ELIF "跨站脚本" OR "XSS" in text → Medium
ELIF "信息泄露" OR "信息泄漏" in text → Medium
ELIF "拒绝服务" OR "DoS" in text → Medium
ELIF "跨站请求伪造" OR "CSRF" in text → Medium
ELIF "目录遍历" OR "路径遍历" in text → Medium
ELSE → Medium (majority fallback)
```

**Success criteria:** If heuristic accuracy is within 3pp of model accuracy (78.3%), the model adds no value over keyword matching.

> [!NOTE]
> **R1 — Executed 2026-03-24**
> - Heuristic: **64.4%**, Model: **78.3%**, Delta: **-13.9pp**
> - Heuristic Low recall: **0.000** (cannot detect Low at all)
> - Model right, heuristic wrong: 2,692 entries (21.1%)
> - Heuristic-model agreement: 70.6%
> - **Verdict: The model adds genuine value over keyword matching.** It captures patterns beyond flat keyword presence (combinations, context, description structure). V3's "functionally equivalent to a lookup table" finding is **overstated** — the model has keyword dependency but is NOT reducible to a heuristic.

---

### R2 — Systematic keyword swap test (V3)

**Gap:** Only 20 adversarial inputs were tested manually. Need statistical proof at scale.

**Method:**
1. From the test set, identify entries where actual severity ≠ type's typical severity (e.g., High-severity XSS, Low-severity SQL injection)
2. Measure misclassification rate for "atypical" entries vs "typical" entries
3. If delta >20pp, keyword dependency is statistically proven

**Success criteria:** Statistically significant difference (p < 0.001) between atypical and typical misclassification rates.

> [!NOTE]
> **R2 — Executed 2026-03-24**
> - 12 vulnerability types analysed (10,787 entries: 7,303 typical + 3,484 atypical)
> - **Typical accuracy: 89.4%** vs **Atypical accuracy: 55.4%** — delta: **34.0pp**
> - **χ²=1607.45, p≈0** — statistically significant beyond any threshold
> - Worst atypical accuracy: CSRF 11.4%, Path Traversal 31.4%, XSS 42.5%
> - When a vulnerability deviates from its type's typical severity, the model predicts the typical severity 49–86% of the time
> - **Verdict:** Keyword dependency is statistically proven at scale. The model strongly biases toward the vulnerability type's default severity. However, R1 showed it still outperforms a flat keyword heuristic by 13.9pp — it captures patterns beyond single keywords (combinations, context) but defaults to type-based severity when uncertain.

---

### R3 — VLAI endpoint live check (V5)

**Gap:** V5 proved the code path exists but didn't confirm ML-Gateway is running in production.

**Method:** `POST https://vulnerability.circl.lu/api/vlai/severity-classification` with a test description.

**Success criteria:** HTTP 200 → feature is live. HTTP 503 → ML-Gateway is down. HTTP 404/500 → endpoint not deployed.

> [!NOTE]
> **R3 — Executed 2026-03-24**
> - Chinese MacBERT: **HTTP 200** — `{"severity": "高", "confidence": 0.8075}` — **LIVE**
> - English RoBERTa: **HTTP 200** — `{"severity": "High", "confidence": 0.9098}` — **LIVE**
> - Default model: **HTTP 200** — `{"severity": "Critical", "confidence": 0.6228}` — **LIVE**
> - **All three models are running in production.** The web UI classification widget is functional.
> - Note: Chinese MacBERT returns Chinese severity labels (高/中/低), RoBERTa returns English (High/Medium/Low/Critical) — consistent with V5's vlai.py source code.

---

### R4 — 10,500-sample reverse lookup (V1)

**Gap:** Current 1,232-sample gives 95% CI ±2.2%. Insufficient for unqualified citation.

**Method:** Proportional stratified sampling, 10,500 entries, 0.5s delay, via Vulnerability-Lookup API.

| Metric | Current (1,232) | Target (10,500) |
|--------|----------------|-----------------|
| Confidence | 95% | 99% |
| Margin of error | ±2.2% | ±1.0% |
| Time | ~10 min | ~90 min |

**Success criteria:** Final CNVD-only rate within ±1.0% at 99% CI.

> [!NOTE]
> **R4 — Executed 2026-03-24 — Definitive overlap figure**
> - **10,457 valid responses** (48 errors, 0.5%), 116 minutes runtime
> - **CNVD-only: 19.0% (99% CI: 18.0%–20.0%, ±0.99%)**
> - CVE-mapped: 81.0%
> - Estimated CNVD-only in full dataset: ~24,200 (99% CI: 22,900–25,500)
> - Severity breakdown (χ²=69.94, p=6.5e-16): High 77.3%, Medium 82.3%, Low 88.0%
> - Confirms 1,232-sample estimate (19.2% ±2.2%) — final figure falls within the previous CI
>
> | Run | n | CVE% | CNVD-only% | CI |
> |-----|---|------|-----------|-----|
> | Initial | 262 | 85.1 | 14.9 | 95% ±4.3% |
> | Refined | 1,232 | 80.8 | 19.2 | 95% ±2.2% |
> | **Final** | **10,457** | **81.0** | **19.0** | **99% ±1.0%** |

---

### R5 — CNVD website verification (V4)

**Gap:** VL API showed missing IDs are empty stubs, but CNVD website itself was inaccessible (HTTP 521). Stubs might have content on the source website that VL failed to ingest.

**Method:** Access `cnvd.org.cn` via VPN (Asian exit node), verify 10 empty-stub IDs have no content on the CNVD website either.

**Success criteria:** 10/10 stubs confirmed empty on CNVD website → VL ingestion is complete. Any with content → VL ingestion is incomplete (different conclusion).

---

### R6 — Out-of-distribution evaluation (V2)

**Gap:** Model evaluated only on held-out test split from same distribution. No test on truly unseen data.

**Method:**
1. Fetch 200+ CNVD entries from 2026 via VL API (entries added after the HF dataset was created)
2. These entries have CNVD severity but were not in the training data
3. Run model inference and measure accuracy vs 2026 entries
4. Compare against the 78.3% baseline from in-distribution test set

**Success criteria:** If accuracy drops >5pp on 2026 entries, the model is not generalisable. If stable, in-distribution evaluation is representative.

---

### R7 — CNVD-only tail characterisation (V1)

**Gap:** V1 vendor analysis was on the full dataset. The ~24,400 CNVD-only entries weren't characterised separately.

**Method:** Filter V1 reverse lookup results to CNVD-only entries, run vendor keywords, compare severity and description length vs CVE-mapped entries.

**Success criteria:** CNVD-only entries should show higher Chinese-domestic vendor representation and shorter descriptions than CVE-mapped entries.

> [!NOTE]
> **R7 — Executed 2026-03-24**
> - CNVD-only entries (n=236 from V1 sample) vs CVE-mapped (n=996) compared
> - **CNVD-only are dominated by PHP (25.0% vs 10.5%)** — Chinese domestic PHP CMS/ERP systems without CVE identifiers
> - Chinese-only vendors (Hikvision, Kingsoft, UFIDA, Panwei, H3C, Tencent, Alibaba, Baidu) appear exclusively in the CNVD-only set
> - Western vendors (Adobe 0%, Microsoft 0%, IBM 0%, Cisco 0.4%) are nearly absent from CNVD-only — they all have CVEs
> - CNVD-only entries have **shorter descriptions** (104 chars vs 152 chars) and **higher severity** (48.7% High vs 33.6%)
> - Sample entries confirm Chinese-domestic software: 院校图书管控系统, 鑫众博考试服务平台, 三一网络技术建站系统, 南京软核科技配变终端
> - **Verdict:** CNVD-only entries are genuinely Chinese-domestic — small CMS, ERP, OA, and IoT systems from vendors that don't participate in CVE assignment

---

### R8 — Train/test leakage check (V2)

**Gap:** V2 used CIRCL's test split without verifying independence.

**Method:** Check for exact duplicate descriptions, titles, IDs, and near-duplicates between train and test splits.

**Success criteria:** Zero or near-zero duplicates between splits.

> [!WARNING]
> **R8 — Executed 2026-03-24 — DATA LEAKAGE DETECTED**
> - **1,587 exact duplicate descriptions** across train and test sets (different CNVD IDs, same vulnerability description text)
> - **359 exact duplicate titles**
> - **4,497 near-duplicates** (first 50 chars match)
> - **0 ID overlaps** — IDs are unique, but the same vulnerability description appears in both splits under different CNVD IDs
> - Severity distribution is well-matched (proportional split)
> - **Impact on V2:** The 78.3% accuracy is likely **inflated** by 1,587 entries (12.4% of test set) where the model has seen the exact same text during training. True out-of-distribution accuracy may be lower.
> - **Root cause:** CNVD assigns separate IDs to the same vulnerability for different products/versions, but the description text is identical (boilerplate Chinese vulnerability descriptions)

> [!WARNING]
> **R8 — Re-run 2026-08-07 — LEAKAGE NOT FIXED, marginally worse**
> Measured on revision `fcfa11537b9432c697c1c5e7f1e8f75aadbb2a8d` (dataset last
> modified 2026-07-06). Script: [`scripts/r8_leakage_scan.py`](scripts/r8_leakage_scan.py),
> raw output [`data/r8_rerun_2026-08-07.json`](data/r8_rerun_2026-08-07.json).
>
> | Measure | 2026-03-24 | 2026-08-07 | Δ |
> |---|---:|---:|---:|
> | train | 114,805 | 116,192 | +1,387 |
> | test | 12,757 | 12,911 | +154 |
> | exact duplicate descriptions (distinct) | 1,587 | 1,613 | +26 |
> | **test entries affected** | **1,993 (15.6%)** | **2,059 (15.95%)** | **+66 (+0.35pp)** |
> | exact duplicate titles (distinct) | 359 | 424 | +65 |
> | near-duplicates, first 50 chars (distinct) | 4,497 | 4,479 | −18 |
> | ID overlaps | 0 | 0 | 0 |
>
> **The corpus grew by 1,541 entries and the split methodology did not change.**
> IDs remain unique across splits while the same description still appears on both
> sides under different CNVD IDs — the identical root cause, four and a half months on.
> The leaked share of the test set rose slightly rather than falling, so the V2/R11
> correction still stands: **the published accuracy remains inflated.**
>
> **Fidelity check.** The re-run measures 9,229 test entries (71.5%) carrying a
> 50-character prefix shared with train, against R13's 71.7% in March. Reproducing an
> independently-reported figure to 0.2pp is what licenses comparing the other rows.
>
> **What this does *not* establish.** The re-run measures the dataset only. Whether the
> *published model* was retrained on this revision is unknown — the model card pins no
> dataset revision. A leakage-corrected accuracy for the current checkpoint would require
> re-running R11, which this scan does not do.

---

### R9 — VL cross-source deduplication (V5)

**Gap:** When NVD and CNVD both have the same vulnerability, does VL cross-link them?

**Method:** Query VL API for CNVD entries with known CVE mappings and check for cross-reference links.

**Success criteria:** Links exist → VL handles the overlap internally.

> [!WARNING]
> **R9 — Executed 2026-03-24 — Links API not exposed**
> - 5 CNVD↔CVE pairs tested — both CNVD and CVE entries exist in VL
> - `/api/vulnerability/{id}/links` endpoint returns **HTTP 404** for all entries
> - V5 source code shows CNVD feeder creates Valkey links (`p.sadd(f"{vuln_id}:link", cveid)`), but this link data is **not exposed via the API**
> - **Conclusion:** VL stores cross-reference links internally but doesn't expose them via the REST API. Users cannot see the CNVD↔CVE mapping through the API. The web UI may display links — requires manual browser verification.

---

### R10 — Low class deep-dive (V2)

**Gap:** V2 showed 39.8% Low recall but didn't explain why specific entries are misclassified.

**Method:** Compare correctly vs incorrectly classified Low entries by vulnerability type, description length, and confidence.

**Success criteria:** Identify structural patterns that explain the Low failure mode.

> [!NOTE]
> **R10 — Executed 2026-03-24**
> - 1,147 Low entries: 457 correct (39.8%), 690 misclassified (60.2%)
> - Misclassified Low → predicted as: **Medium 92.0%** (635), High 8.0% (55)
> - **Vulnerability type is the primary predictor of Low misclassification:**
>   - Low entries with "typically High" types (RCE, Buffer Overflow, SQL Injection) → **87–100% misclassification rate** — model predicts the type's default, ignoring actual Low severity
>   - Low entries with "typically Medium" types (XSS, Info Disclosure, DoS) → **49–63% misclassification rate** — model predicts Medium instead of Low
>   - Low entries with File Upload → **12.8% misclassification** — exception, model handles Low File Upload well
> - Description length is NOT a factor (correct: 146 chars, misclassified: 153 chars)
> - Confidence is slightly lower for misclassified (0.748 vs 0.774) — but both are high, consistent with V2's overconfidence finding
> - **Verdict:** Low misclassification is driven by the same keyword dependency as R2 — the model defaults to the type's typical severity (High or Medium), never Low, unless the type itself is typically Low (which few are)

---

### R11 — Accuracy without leaked entries (V2)

**Gap:** R8 detected 1,587 exact duplicate descriptions. Need to recalculate accuracy excluding them.

**Method:** Exclude test entries whose description appears in the training set, recalculate accuracy.

> [!WARNING]
> **R11 — Executed 2026-03-24 — True accuracy is 76.6%**
> - Leaked entries (n=1,993, 15.6% of test): **87.6% accuracy**
> - Unleaked entries (n=10,764, 84.4% of test): **76.6% accuracy**
> - **Leakage inflation: +11.1pp on leaked entries, +1.7pp on headline number**
> - Unleaked per-class: High recall 0.736 (was 0.768), Low recall 0.384 (was 0.398)
> - True model accuracy is **76.6%**, not 78.3%
> - Still outperforms keyword heuristic (64.4%) by **12.2pp**

---

### R12 — Verify leakage type (V2)

**Gap:** Same description ≠ necessarily same label. Need to confirm duplicates are memorisable.

**Method:** Check label consistency across train/test for shared descriptions.

> [!NOTE]
> **R12 — Executed 2026-03-24 — Leakage is real**
> - 94.1% of shared descriptions have the **same severity** in train and test → model can memorise
> - 5.9% have different severity → label noise, not exploitable leakage
> - **Root cause:** CNVD assigns separate IDs to the same vulnerability for different products/versions, reusing boilerplate descriptions
> - The leakage is an artifact of CNVD's data structure, not malicious — but it inflates the accuracy metric

---

### R13 — Near-duplicate analysis (V2)

**Gap:** 4,497 near-duplicates (50-char prefix match) — how many are true semantic duplicates?

**Method:** Compare prefix-matching entries, check if they're the same vulnerability described slightly differently.

> [!WARNING]
> **R13 — Executed 2026-03-24 — 71.7% of test set has near-duplicates in train**
> - 9,141 test entries (71.7%) share a 50-char description prefix with a training entry
> - Of these: 1,993 are exact duplicates, 7,148 are near-only (same vendor/product intro, different specific vulnerability)
> - Near-only samples show legitimate similar-but-different entries: same ARRIS router, different command injection; same Foxit Reader, different memory error
> - Near-only accuracy: 76.5% — same as unleaked, not inflated
> - **Cleanest accuracy** (excluding ALL prefix matches): **76.69%** (n=3,616, 28.3% of test set)
> - **Conclusion:** Near-duplicates are NOT leakage — they're naturally similar entries. The dataset's boilerplate style means many entries share product introductions. Only exact duplicates (1,993, 15.6%) represent true leakage.

---

### R14 — Out-of-distribution evaluation (V2)

**Gap:** Need accuracy on truly unseen data — entries not in the HF dataset at all.

**Method:** Fetch 2026 CNVD entries from VL API that are not in the HF dataset, run model inference.

> [!WARNING]
> **R14 — Executed 2026-03-24 — Insufficient sample but indicative**
> - Only **36 OOD entries** found (2 from 2026, 34 from 2025) — most non-dataset CNVD IDs are empty stubs (V4)
> - No Low entries in OOD sample (only High: 22, Medium: 14)
> - **OOD accuracy: 80.56%** — higher than in-distribution clean (76.69%)
> - High recall: 0.818, Medium recall: 0.786
> - **Not statistically robust (n=36, no Low class)** — but suggests the model does NOT degrade on unseen data
> - The higher accuracy is likely because OOD entries are skewed toward High severity (61%) which the model handles well, and have no Low entries to fail on
> - **Conclusion:** R14 is inconclusive due to sample size. The unleaked in-distribution accuracy (R11: 76.6%) remains the best available corrected metric.
