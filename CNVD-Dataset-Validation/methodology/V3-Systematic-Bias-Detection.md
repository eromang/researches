# V3 — Systematic Bias Detection

**Objective:** Determine whether the model has systematic blind spots — vulnerability types, vendor families, or description patterns where classification accuracy degrades significantly below the 78.3% baseline.

---

## Context from V1 and V2

V2 established that the model is effectively a two-class classifier (High vs Medium) with broken Low recall (39.8%). V3 asks a different question: **within the classes the model handles, are there systematic blind spots by vulnerability category or vendor?**

Key V2 findings that shape V3:
- The model has a **Medium bias** — when uncertain, it predicts Medium
- **Low recall collapses post-2024** (18–25%) — the model is getting worse over time for Low
- **Confidence between 0.7–0.9 is overconfident** by 7–9pp
- The dataset is **94% Western software** (V1) — the model may perform differently on Chinese-domestic entries

---

## Prerequisites

Same venv as V1/V2 — no additional packages needed.

```bash
source cnvd-validation/bin/activate
```

**Input:** `v2_test_predictions.csv` (12,757 entries with predictions and confidence from V2).

---

## Step 1 — Vulnerability type classification from description text

The dataset has no CWE field, so extract vulnerability types via Chinese keyword matching on the `description` field.

```python
import pandas as pd

df = pd.read_csv("v2_test_predictions.csv")

cn_to_en = {"高": "High", "中": "Medium", "低": "Low"}
df["true_en"] = df["severity"].map(cn_to_en)
df["pred_en"] = df["predicted"].map(cn_to_en)

# Chinese vulnerability type keywords → approximate CWE mapping
vuln_types = {
    "SQL Injection":        ["SQL注入", "sql注入"],
    "XSS":                  ["跨站脚本", "XSS", "xss"],
    "Buffer Overflow":      ["缓冲区溢出", "栈溢出", "堆溢出"],
    "RCE":                  ["远程代码执行", "代码执行", "命令执行", "命令注入"],
    "Privilege Escalation": ["权限提升", "提权"],
    "Info Disclosure":      ["信息泄露", "信息泄漏", "敏感信息"],
    "DoS":                  ["拒绝服务", "DoS", "dos"],
    "Auth Bypass":          ["认证绕过", "身份验证绕过", "安全绕过", "授权绕过"],
    "Path Traversal":       ["目录遍历", "路径遍历"],
    "CSRF":                 ["跨站请求伪造", "CSRF"],
    "File Upload":          ["文件上传", "任意文件"],
    "Deserialization":      ["反序列化"],
    "SSRF":                 ["服务端请求伪造", "SSRF"],
    "XXE":                  ["XML外部实体", "XXE"],
    "Default Credentials":  ["默认口令", "弱口令", "默认密码"],
    "Hardcoded Credentials":["硬编码"],
    "Unspecified":          ["未明漏洞", "存在安全漏洞"],
}

df["text"] = df["title"].fillna("") + " " + df["description"].fillna("")

for vtype, keywords in vuln_types.items():
    pattern = "|".join(keywords)
    df[f"is_{vtype}"] = df["text"].str.contains(pattern, case=False, na=False)

# Assign primary type (first match; "Other" if none)
def get_primary_type(row):
    for vtype in vuln_types:
        if row[f"is_{vtype}"]:
            return vtype
    return "Other"

df["vuln_type"] = df.apply(get_primary_type, axis=1)
print(df["vuln_type"].value_counts())
```

> [!NOTE] Step 1 — Executed 2026-03-24
> - 17 vulnerability type categories extracted via Chinese keyword matching
> - **85.5% of entries classified** (10,908/12,757); 14.5% "Other" (no keyword match)
> - Top types: DoS (1,601), Info Disclosure (1,464), XSS (1,441), RCE (1,271), SQL Injection (1,182), Unspecified (1,124), Buffer Overflow (1,028)
> - Enriched predictions saved to `v3_enriched_predictions.csv`

---

## Step 2 — Accuracy by vulnerability type

```python
from sklearn.metrics import accuracy_score

print(f"{'Vuln Type':25s}  {'n':>5s}  {'Acc':>6s}  {'H Rec':>6s}  {'M Rec':>6s}  {'L Rec':>6s}  {'Δ Base':>7s}")
print("-" * 85)

baseline_acc = (df["severity"] == df["predicted"]).mean()

for vtype in sorted(df["vuln_type"].unique()):
    sub = df[df["vuln_type"] == vtype]
    if len(sub) < 20:
        continue
    acc = (sub["severity"] == sub["predicted"]).mean()
    delta = acc - baseline_acc

    h = sub[sub["true_en"] == "High"]
    m = sub[sub["true_en"] == "Medium"]
    l = sub[sub["true_en"] == "Low"]
    h_rec = (h["pred_en"] == "High").mean() if len(h) >= 5 else float("nan")
    m_rec = (m["pred_en"] == "Medium").mean() if len(m) >= 5 else float("nan")
    l_rec = (l["pred_en"] == "Low").mean() if len(l) >= 5 else float("nan")

    flag = " ⚠️" if delta < -0.05 else ""
    print(f"{vtype:25s}  {len(sub):5d}  {acc:5.3f}  {h_rec:5.3f}  {m_rec:5.3f}  "
          f"{'N/A' if pd.isna(l_rec) else f'{l_rec:5.3f}':>5s}  {delta:+6.3f}{flag}")
```

**What to look for:**
- Vulnerability types with accuracy >5pp below baseline — these are systematic blind spots
- Types where High recall drops sharply — the model may systematically underclassify certain threats
- "Unspecified" category — the model may rely on vulnerability type keywords rather than severity signals

> [!NOTE] Step 2 — Executed 2026-03-24 — Type→severity mapping exposed
>
> **Blind spots (>5pp below baseline):**
> - **Privilege Escalation:** -8.9pp (69.4%) — significant
> - **Hardcoded Credentials:** -15.4pp (62.9%) — worst performer (n=35)
>
> **Critical pattern discovered:** The model maps vulnerability type keywords to default severity levels. When actual severity matches the type's typical severity, recall is >80%. When it deviates:
> - **XSS actual=High:** 17.1% recall (83% missed — model always predicts Medium for XSS)
> - **Info Disclosure actual=High:** 32.0% recall (68% missed)
> - **SQL Injection actual=Low:** 0% recall (all missed)
> - **CSRF actual=High:** 14.3% recall (86% missed)
> - **DoS actual=High:** 54.1% recall (half missed)
>
> The model is a **type-keyword→default-severity mapper**, not a severity assessor.

---

## Step 3 — Accuracy by vendor family

Cross-reference V1's vendor keyword lists with the test set predictions.

```python
vendor_groups = {
    "Huawei":     ["huawei", "华为"],
    "Microsoft":  ["microsoft", "微软"],
    "Adobe":      ["adobe"],
    "Google":     ["google", "谷歌"],
    "Apache":     ["apache"],
    "Linux":      ["linux"],
    "PHP":        ["php"],
    "WordPress":  ["wordpress"],
    "Cisco":      ["cisco", "思科"],
    "Oracle":     ["oracle", "甲骨文"],
    "Seeyon":     ["seeyon", "致远"],
    "UFIDA":      ["ufida", "用友", "yonyou"],
    "D-Link":     ["d-link", "dlink"],
    "TP-Link":    ["tp-link", "tplink"],
    "Foxit":      ["foxit", "福昕"],
}

print(f"{'Vendor':15s}  {'n':>5s}  {'Acc':>6s}  {'Δ Base':>7s}  {'Sev distribution':>20s}")
print("-" * 65)

for vendor, keywords in vendor_groups.items():
    pattern = "|".join(keywords)
    mask = df["text"].str.contains(pattern, case=False, na=False)
    sub = df[mask]
    if len(sub) < 20:
        continue
    acc = (sub["severity"] == sub["predicted"]).mean()
    delta = acc - baseline_acc
    sev_dist = sub["true_en"].value_counts(normalize=True)
    dist_str = f"H:{sev_dist.get('High',0):.0%} M:{sev_dist.get('Medium',0):.0%} L:{sev_dist.get('Low',0):.0%}"
    flag = " ⚠️" if delta < -0.05 else ""
    print(f"{vendor:15s}  {len(sub):5d}  {acc:5.3f}  {delta:+6.3f}  {dist_str}{flag}")
```

**What to look for:**
- Chinese domestic vendors (Seeyon, UFIDA) with lower accuracy — these are the CNVD-only entries from V1, potentially harder for the model
- Western vendors with atypical severity distributions — if a vendor is predominantly High but accuracy is low, the model may struggle with that vendor's description style

> [!NOTE] Step 3 — Executed 2026-03-24
> - **Huawei** is the worst vendor: 65.7% accuracy (-12.6pp) — 15.2% Low proportion contributes
> - **Cisco** (-7.1pp) and **IBM** (-6.4pp) also underperform — both have >6% Low entries
> - **Chinese domestic vendors (Seeyon 91.9%, UFIDA 91.3%) perform well** — but only because they're predominantly High severity, which the model handles
> - **Pattern:** Vendor accuracy correlates inversely with Low severity proportion. The model fails on vendors with atypical severity distributions.

---

## Step 4 — Description length effect

Does the model perform differently on short vs long descriptions?

```python
df["desc_len"] = df["description"].str.len()

bins = [0, 50, 100, 150, 200, 300, 500, 1300]
df["len_bin"] = pd.cut(df["desc_len"], bins=bins)

print(f"{'Length bin':>20s}  {'n':>5s}  {'Acc':>6s}  {'Mean conf':>10s}  {'Δ Base':>7s}")
print("-" * 55)

for bin_label in sorted(df["len_bin"].dropna().unique()):
    sub = df[df["len_bin"] == bin_label]
    if len(sub) < 20:
        continue
    acc = (sub["severity"] == sub["predicted"]).mean()
    delta = acc - baseline_acc
    conf = sub["confidence"].mean()
    print(f"{str(bin_label):>20s}  {len(sub):5d}  {acc:5.3f}  {conf:9.4f}  {delta:+6.3f}")
```

**What to look for:**
- Very short descriptions (<50 chars) with lower accuracy — the model may lack enough signal
- Very long descriptions with different accuracy — could indicate overfit to description length as a proxy

> [!NOTE] Step 4 — Executed 2026-03-24
> - Very short descriptions (<50 chars): **69.7% accuracy (-8.6pp) but 0.878 confidence** — most overconfident on least informative text
> - Sweet spot: 50–80 chars (+5.9pp, 84.1%)
> - Accuracy degrades slightly with length beyond 130 chars (-1 to -3pp)
> - **Pattern:** the model doesn't benefit from longer descriptions — consistent with keyword-based classification

---

## Step 5 — Adversarial robustness — keyword dependency test

Test whether the model relies on vulnerability type keywords rather than severity signals.

```python
from transformers import pipeline

classifier = pipeline(
    "text-classification",
    model="CIRCL/vulnerability-severity-classification-chinese-macbert-base",
    device="mps",
)

# Test pairs: same severity description with different vulnerability types
adversarial_tests = [
    # High severity descriptions with type keywords swapped
    ("存在远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "Expected: High (RCE)"),
    ("存在跨站脚本漏洞，攻击者可利用该漏洞执行任意代码。", "Swapped: XSS + RCE impact"),
    ("存在信息泄露漏洞，攻击者可利用该漏洞获取敏感信息。", "Expected: Medium (info disclosure)"),
    ("存在远程代码执行漏洞，攻击者可利用该漏洞获取敏感信息。", "Swapped: RCE + info impact"),

    # Minimal descriptions — how little text does the model need?
    ("代码执行漏洞", "Minimal: code execution"),
    ("信息泄露", "Minimal: info disclosure"),
    ("缓冲区溢出", "Minimal: buffer overflow"),
    ("跨站脚本", "Minimal: XSS"),
    ("SQL注入", "Minimal: SQL injection"),
    ("拒绝服务", "Minimal: DoS"),

    # Negation test — does the model understand negation?
    ("存在远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "Positive: RCE"),
    ("不存在远程代码执行漏洞。", "Negated: no RCE"),

    # Severity-irrelevant padding
    ("该软件是一款办公管理系统。存在远程代码执行漏洞。", "With product context"),
    ("存在远程代码执行漏洞。", "Without product context"),
]

print(f"{'Description':60s}  {'Label':>8s}  {'Conf':>6s}  {'Note'}")
print("-" * 100)
for desc, note in adversarial_tests:
    result = classifier(desc, truncation=True, max_length=512)[0]
    print(f"{desc[:58]:60s}  {result['label']:>8s}  {result['score']:5.3f}  {note}")
```

**What to look for:**
- **Keyword dependency:** If swapping "远程代码执行" (RCE) to "信息泄露" (info disclosure) changes the prediction from High to Medium even when the impact description stays the same → the model classifies by vulnerability type, not severity
- **Minimal text sensitivity:** How few characters does the model need to make a confident prediction? If 4-character type names produce high-confidence predictions → the model is a keyword classifier in disguise
- **Negation blindness:** If "不存在远程代码执行漏洞" (does NOT have RCE) still predicts High → the model ignores negation
- **Context insensitivity:** If product context padding doesn't change the prediction → the model ignores product information (which may be fine)

> [!WARNING] Step 5 — Executed 2026-03-24 — Model is a keyword classifier
>
> **Keyword dependency — CONFIRMED:**
> - "XSS keyword + RCE impact" → **Medium** (0.771) — type keyword overrides impact description
> - "RCE keyword + InfoDisc impact" → **High** (0.597) — type keyword still dominates
>
> **Minimal text — 2–4 words sufficient:**
> - "代码执行漏洞" (4 chars) → High (0.897 confidence)
> - "信息泄露" (4 chars) → Medium (0.858 confidence)
>
> **Negation blindness — CONFIRMED:**
> - "存在远程代码执行漏洞" (has RCE) → High (0.807)
> - "不存在远程代码执行漏洞" (does NOT have RCE) → **High (0.791)** — identical prediction
> - "已修复远程代码执行漏洞" (RCE fixed) → **High (0.693)** — still predicts High
>
> **Severity qualifiers — partially working:** "严重的" (severe) increases confidence (0.968) but doesn't change label. "轻微的" (minor) doesn't change label either.
>
> **Verdict:** The model is functionally equivalent to a keyword lookup table. It classifies by vulnerability type keyword presence, not by actual severity assessment.

---

## Step 6 — CVE-mapped vs CNVD-only accuracy (cross-reference with V1)

Use the V1 reverse lookup data to check if the model performs differently on CNVD-only entries.

```python
# Load V1 reverse lookup results
v1_df = pd.read_csv("v1_reverse_lookup_1225.csv")
v1_lookup = set(v1_df[v1_df["has_cve"] == False]["cnvd_id"].tolist())
v1_cve = set(v1_df[v1_df["has_cve"] == True]["cnvd_id"].tolist())

# Cross-reference with V2 test predictions
df["in_v1_sample"] = df["id"].isin(v1_lookup | v1_cve)
df["is_cnvd_only"] = df["id"].isin(v1_lookup)
df["is_cve_mapped"] = df["id"].isin(v1_cve)

for label, mask_col in [("CNVD-only (V1 sample)", "is_cnvd_only"), ("CVE-mapped (V1 sample)", "is_cve_mapped")]:
    sub = df[df[mask_col]]
    if len(sub) >= 10:
        acc = (sub["severity"] == sub["predicted"]).mean()
        print(f"{label}: n={len(sub)}, accuracy={acc:.3f}")
    else:
        print(f"{label}: n={len(sub)} (too few for analysis)")
```

> [!NOTE] Limited overlap
> The V1 sample (1,232 entries) was drawn from the full dataset (train + test), while V2 predictions are on the test split only (12,757). The overlap will be small (~100–130 entries). If insufficient, run the model on a dedicated sample of known CNVD-only entries from the V1 CSV.

> [!NOTE] Step 6 — Executed 2026-03-24 — Insufficient overlap but indicative
> - Only **110 entries** overlap between V1 sample and test set (21 CNVD-only, 89 CVE-mapped)
> - CNVD-only: 81.0% accuracy, 0.909 mean confidence
> - CVE-mapped: 74.2% accuracy, 0.842 mean confidence
> - **Not statistically robust** due to small n, but CNVD-only entries perform better — likely because they skew toward High severity (which the model handles well)
> - A dedicated experiment on known CNVD-only entries would be needed for a conclusive answer

---

## Step 7 — Generate report

Compile all V3 findings into [V3 Findings Report](../findings/V3-Bias-Detection-Findings.md):

1. Vulnerability type accuracy breakdown
2. Vendor family accuracy breakdown
3. Description length effect
4. Adversarial robustness results
5. CNVD-only vs CVE-mapped accuracy
6. Verdict: are there actionable blind spots?

---

## Interpretation Thresholds

| Metric | No concern | Minor concern | Major concern |
|--------|-----------|---------------|---------------|
| Accuracy delta by vuln type | <5pp below baseline | 5–10pp below | >10pp below |
| Accuracy delta by vendor | <5pp below baseline | 5–10pp below | >10pp below |
| Keyword dependency | Predictions change with impact, not type | Mixed | Predictions follow type keyword, not impact |
| Negation blindness | Model recognises negation | — | Model ignores negation |
| CNVD-only vs CVE-mapped delta | <3pp | 3–8pp | >8pp |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Step 1 — Vuln type extraction | 10 min | Keyword matching on existing predictions |
| Step 2 — Type accuracy breakdown | 5 min | Groupby + metrics |
| Step 3 — Vendor accuracy | 5 min | Groupby + metrics |
| Step 4 — Description length | 5 min | Binning + metrics |
| Step 5 — Adversarial tests | 10 min | ~15 individual predictions |
| Step 6 — CNVD-only cross-reference | 10 min | Join with V1 data |
| Step 7 — Report | 15 min | Compile findings |
| **Total** | **~1 hour** | All steps use existing prediction data |

---

## Next Steps After V3

- If vulnerability type accuracy varies >10pp → the model is unreliable for specific threat categories; document which ones
- If adversarial tests show keyword dependency → the model is a keyword classifier, not a severity assessor; the "AI model" framing in the LinkedIn post is misleading
- If CNVD-only entries have lower accuracy → the model is less useful for the genuinely new data (the 19% tail from V1)
- Regardless → update the CNVD Dataset Hugging Face Brief with V3 findings
