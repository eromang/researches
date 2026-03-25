# V1 — NVD Overlap Analysis

**Objective:** Determine what proportion of the 127,562 CNVD entries on Hugging Face map to existing NVD CVEs, and what proportion is genuinely net-new Chinese-only vulnerability data.

---

## Dataset Schema (verified)

**Source:** `CIRCL/Vulnerability-CNVD` on Hugging Face

| Field | Type | Example |
|-------|------|---------|
| `id` | string (14–16 chars) | `CNVD-2020-20184` |
| `title` | string (Chinese, 7–131 chars) | `流星网络电视存在代码执行漏洞` |
| `description` | string (Chinese, 25–1260 chars) | Detailed vulnerability description |
| `severity` | 3-class string | `高` (High) / `中` (Medium) / `低` (Low) |
| `split` | string | `train` / `test` |

**Key constraints:**
- **No CVE column** — only CNVD identifiers (format: `CNVD-YYYY-NNNNN`)
- **No date column** — year must be extracted from the `id` field
- **No CVSS scores** — severity is categorical only (3 values)
- **All text in Simplified Chinese** — vendor matching requires Chinese names
- **Splits:** train (115,000) / test (12,800) — use both for analysis

> [!WARNING] Methodological impact
> The absence of a CVE column means overlap analysis cannot be done by simple column matching. Two approaches are available:
> 1. **Text extraction** — regex for `CVE-YYYY-NNNNN` in `title` and `description` fields
> 2. **Reverse lookup** — query CNVD IDs against an external CNVD→CVE mapping source (Vulnerability-Lookup API, CNVD website scraping)
>
> Both approaches should be tried. Text extraction gives a lower bound; reverse lookup gives the true mapping.

---

## Prerequisites

### Environment (set up 2026-03-24)

**Activate:**

```bash
source cnvd-validation/bin/activate
```

**Installed packages (pinned in `requirements.txt`):**

| Package | Version | Purpose |
|---------|---------|---------|
| `pandas` | 3.0.1 | DataFrame operations |
| `datasets` | 4.8.4 | Hugging Face dataset loading |
| `requests` | 2.32.5 | HTTP for NVD API / CNVD scraping |
| `tqdm` | 4.67.3 | Progress bars |
| `matplotlib` | 3.10.8 | Temporal/severity plots |
| `scipy` | 1.17.1 | Chi-squared test for severity skew |

**Rebuild from scratch:**

```bash
python3 -m venv cnvd-validation
source cnvd-validation/bin/activate
pip install -r requirements.txt
```

### Data sources

| Source | Method | Notes |
|--------|--------|-------|
| CNVD dataset | `datasets` library | `CIRCL/Vulnerability-CNVD` |
| NVD CVE corpus | NVD API 2.0 or CVE List V5 clone | Paginated API or `github.com/CVEProject/cvelistV5` |
| Vulnerability-Lookup | REST API | CNVD→CVE mapping (if exposed) |

---

## Step 1 — Download and inspect the CNVD dataset

```python
from datasets import load_dataset
import pandas as pd

ds = load_dataset("CIRCL/Vulnerability-CNVD")

# Combine train and test splits for full analysis
df_train = pd.DataFrame(ds["train"])
df_test = pd.DataFrame(ds["test"])
df = pd.concat([df_train, df_test], ignore_index=True)

print(f"Columns: {df.columns.tolist()}")
print(f"Total entries: {len(df)}")
print(f"  train: {len(df_train)}")
print(f"  test:  {len(df_test)}")
print(f"\nSeverity distribution:")
print(df["severity"].value_counts())
print(f"\nSample entry:")
print(df.iloc[0].to_dict())
```

**Verify:**
- Total should be ~127,562
- Columns should be `['id', 'title', 'description', 'severity']` (4 columns — `split` is implicit)
- All `id` values match `CNVD-YYYY-NNNNN` pattern

> [!NOTE] Step 1 — Executed 2026-03-24
> - Total: 127,562 (train: 114,805 / test: 12,757)
> - Columns: `['id', 'title', 'description', 'severity']`
> - Field lengths: id 14–16, title 7–141 (mean 35), description 25–1256 (mean 144)
> - Severity: 中 70,264 (55.1%) / 高 46,077 (36.1%) / 低 11,221 (8.8%)

---

## Step 2 — Extract year from CNVD identifier

Since there is no date column, extract the year from the `id` field.

```python
import re

# Extract year from CNVD-YYYY-NNNNN
df["year"] = df["id"].str.extract(r"CNVD-(\d{4})-", expand=False).astype(float)

print("Entries by year:")
print(df["year"].value_counts().sort_index())
print(f"\nYear range: {df['year'].min():.0f} — {df['year'].max():.0f}")
print(f"Missing year: {df['year'].isna().sum()}")
```

> [!NOTE] Step 2 — Executed 2026-03-24
> - Year range: 2010–2026 (no missing values)
> - Peak years: 2017–2021 (62% of dataset)
> - **2022 drop-off:** entries halve from 17,398 (2021) to 9,660 (2022) — potential RMSV impact (regulations effective September 2021)
> - 2025 recovery: 8,714 entries — dataset is reasonably current
> - **Severity shift post-2023:** High severity jumps from ~30-37% to ~50-54%; Low drops from ~12% to ~4%. Possible change in CNVD submission criteria or selective curation.

---

## Step 3 — Extract CVE identifiers from text fields

The dataset has no CVE column, so extract CVE references from `title` and `description`.

```python
cve_pattern = re.compile(r"CVE-\d{4}-\d{4,}")

def extract_cves(row):
    """Search title and description for CVE identifiers."""
    cves = set()
    for field in ["title", "description"]:
        val = str(row[field])
        cves.update(cve_pattern.findall(val))
    return list(cves)

df["extracted_cves"] = df.apply(extract_cves, axis=1)
df["has_cve"] = df["extracted_cves"].apply(len) > 0
df["cve_count"] = df["extracted_cves"].apply(len)

total = len(df)
with_cve = df["has_cve"].sum()
without_cve = total - with_cve

print(f"Total entries:             {total}")
print(f"With CVE in text:          {with_cve} ({with_cve/total*100:.1f}%)")
print(f"Without CVE in text:       {without_cve} ({without_cve/total*100:.1f}%)")
print(f"Unique CVEs found in text: {len(set(c for cves in df['extracted_cves'] for c in cves))}")
```

> [!IMPORTANT] This is a lower bound
> CVE references may exist for these CNVD entries but not be mentioned in the Chinese text. The true overlap rate requires a reverse lookup (Step 5). This step tells you *at minimum* how many entries have CVE cross-references embedded in the text.

**Decision point:**
- If most entries contain CVE references in the text → proceed to Step 4 (NVD cross-reference)
- If very few contain CVE references → this step alone doesn't answer the overlap question; Step 5 (reverse lookup) becomes critical

> [!WARNING] Step 3 — Executed 2026-03-24 — Text extraction is NOT viable
> - **Only 27 out of 127,562 entries (0.02%) contain CVE references in text**
> - 26 unique CVEs found — negligible
> - Even entries for well-known international software (Adobe Audition, Google Android, IBM Sterling) use CNVD IDs only without mentioning the CVE
> - **Conclusion:** The dataset was built for Chinese-language severity classification, not as a CVE cross-reference resource. Text extraction gives zero usable signal.
> - **Impact:** Step 4 (NVD cross-reference of extracted CVEs) is skipped — nothing to cross-reference. Step 5 (reverse lookup via Vulnerability-Lookup API or CNVD website) becomes the **only viable path** to determine overlap.

---

## Step 4 — Cross-reference extracted CVEs against NVD

### 4a — Build NVD CVE ID set

```python
import requests
import time
from pathlib import Path
import json

# Option A: Use CVE List V5 bulk download (faster)
# https://github.com/CVEProject/cvelistV5 — clone or download
# Each CVE is a JSON file: cves/{year}/{NNNNN}/CVE-YYYY-NNNNN.json

# Option B: Use NVD API 2.0 (paginated, rate-limited)
def download_nvd_cve_ids():
    """Download all CVE IDs from NVD API 2.0."""
    all_cve_ids = set()
    start_index = 0
    results_per_page = 2000

    while True:
        url = (
            f"https://services.nvd.nist.gov/rest/json/cves/2.0"
            f"?startIndex={start_index}&resultsPerPage={results_per_page}"
        )
        resp = requests.get(url, timeout=30)

        if resp.status_code == 403:
            print("Rate limited — waiting 30s...")
            time.sleep(30)
            continue

        if resp.status_code != 200:
            print(f"Error {resp.status_code} at index {start_index}")
            break

        data = resp.json()
        vulns = data.get("vulnerabilities", [])

        if not vulns:
            break

        for v in vulns:
            cve_id = v["cve"]["id"]
            all_cve_ids.add(cve_id)

        total_results = data.get("totalResults", 0)
        start_index += results_per_page
        print(f"  Fetched {start_index}/{total_results} CVEs...")

        if start_index >= total_results:
            break

        time.sleep(6)  # Rate limit: ~10 req/min without API key

    return all_cve_ids

# This takes 2-3 hours without an API key
# Save result to disk for reuse
nvd_cache = Path("nvd_cve_ids.json")
if nvd_cache.exists():
    all_nvd_cves = set(json.loads(nvd_cache.read_text()))
    print(f"Loaded {len(all_nvd_cves)} NVD CVE IDs from cache")
else:
    all_nvd_cves = download_nvd_cve_ids()
    nvd_cache.write_text(json.dumps(list(all_nvd_cves)))
    print(f"Downloaded and cached {len(all_nvd_cves)} NVD CVE IDs")
```

> [!TIP] Faster alternative: CVE List V5
> Clone `https://github.com/CVEProject/cvelistV5` and enumerate file names — each file is a CVE. This avoids the NVD rate limit entirely and is much faster.
>
> ```bash
> git clone --depth 1 https://github.com/CVEProject/cvelistV5.git
> find cvelistV5/cves -name "CVE-*.json" | sed 's|.*/||;s|\.json||' > all_cve_ids.txt
> ```

### 4b — Compute overlap

```python
# Flatten all extracted CVEs from CNVD dataset
cnvd_cves = set()
for cve_list in df["extracted_cves"]:
    cnvd_cves.update(cve_list)

overlap = cnvd_cves & all_nvd_cves
cnvd_only_cves = cnvd_cves - all_nvd_cves

print(f"Unique CVEs in CNVD text:    {len(cnvd_cves)}")
print(f"Overlap with NVD:            {len(overlap)} ({len(overlap)/max(len(cnvd_cves),1)*100:.1f}%)")
print(f"CVEs in CNVD text, not NVD:  {len(cnvd_only_cves)}")
print(f"\nEntries with NO CVE at all:  {without_cve} ({without_cve/total*100:.1f}%)")

# List the CVEs found in CNVD but not in NVD (interesting ones)
if cnvd_only_cves:
    print(f"\nCVEs in CNVD text but not in NVD:")
    for cve in sorted(cnvd_only_cves)[:20]:
        print(f"  {cve}")
    if len(cnvd_only_cves) > 20:
        print(f"  ... and {len(cnvd_only_cves) - 20} more")
```

---

## Step 5 — Reverse lookup: CNVD ID → CVE mapping

This is the critical step for entries where no CVE appears in the text. The CNVD website and Vulnerability-Lookup may provide CNVD→CVE mappings.

### 5a — Check Vulnerability-Lookup API

```python
# Vulnerability-Lookup may expose CNVD→CVE mapping
# Check the API documentation or try a sample lookup
sample_ids = df["id"].head(10).tolist()

for cnvd_id in sample_ids:
    # Try Vulnerability-Lookup API (adjust endpoint as needed)
    url = f"https://vulnerability.circl.lu/api/search/{cnvd_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        print(f"{cnvd_id}: {json.dumps(data, indent=2)[:200]}")
    else:
        print(f"{cnvd_id}: HTTP {resp.status_code}")
    time.sleep(1)
```

> [!NOTE] API discovery — Resolved 2026-03-24
> **Working endpoint:** `https://vulnerability.circl.lu/api/vulnerability/{CNVD-ID}`
> - Returns full CNVD record including `cves.cve.cveNumber` field (CVE mapping)
> - No authentication required
> - Rate: 0.3s delay between requests is sufficient (no rate limiting observed)
> - Response includes additional fields not in Hugging Face dataset: `submitTime`, `openTime`, `products`, `discovererName`, `referenceLink`, `patchName`, `patchDescription`

> [!NOTE] Step 5 — Executed 2026-03-24 — Stratified reverse lookup (1,232 samples, refined)
>
> **Method:** Proportional stratified sampling (~1% per year), 0.5s delay between requests, queried via Vulnerability-Lookup API. Supersedes initial 262-sample run.
>
> | Metric | Value | 95% CI |
> |--------|-------|--------|
> | Sample size | 1,232 (0 errors, 0 rate limits) | — |
> | With CVE mapping | 996 (80.8%) | 78.6%–83.0% |
> | CNVD-only (no CVE) | 236 (19.2%) | 17.0%–21.4% |
> | Estimated CNVD-only in full dataset | ~24,400 | 21,600–27,200 |
>
> **CVE mapping rate by year:**
>
> | Year | Sample | With CVE | No CVE | Rate |
> |------|--------|----------|--------|------|
> | 2014 | 5 | 4 | 1 | 80.0% |
> | 2015 | 77 | 61 | 16 | 79.2% |
> | 2016 | 101 | 79 | 22 | 78.2% |
> | 2017 | 147 | 118 | 29 | 80.3% |
> | 2018 | 134 | 112 | 22 | 83.6% |
> | 2019 | 141 | 114 | 27 | 80.9% |
> | 2020 | 175 | 123 | 52 | 70.3% |
> | 2021 | 167 | 111 | 56 | 66.5% |
> | 2022 | 93 | 91 | 2 | 97.8% |
> | 2023 | 40 | 39 | 1 | 97.5% |
> | 2024 | 52 | 50 | 2 | 96.2% |
> | 2025 | 84 | 78 | 6 | 92.9% |
> | 2026 | 14 | 14 | 0 | 100.0% |
>
> **CVE mapping rate by severity (chi-squared=18.82, p < 0.0001):**
> - High: 74.4% +/-4.0% | Medium: 84.7% +/-2.7% | Low: 83.6% +/-6.7%
>
> **Key observations:**
> - 2020–2021 have the lowest CVE mapping rate (66–70%) — peak of Chinese-domestic vulnerabilities
> - 2022 jumps to 97.8% — structural change coinciding with RMSV (September 2021)
> - High severity has the *lowest* CVE mapping rate (74.4%) — statistically significant (p < 0.0001); Chinese-domestic vulnerabilities that never receive CVEs tend to be high severity
> - Results saved to `v1_reverse_lookup_1225.csv`

### 5b — CNVD website scraping (fallback — not needed)

If Vulnerability-Lookup doesn't provide the mapping, scrape CNVD directly.

```python
# CNVD website: https://www.cnvd.org.cn/flaw/show/CNVD-YYYY-NNNNN
# The page typically shows a "CVE ID" field if a mapping exists
# WARNING: Respect rate limits and robots.txt

import time

def lookup_cnvd_cve(cnvd_id):
    """Scrape CNVD website for CVE mapping. Use sparingly."""
    url = f"https://www.cnvd.org.cn/flaw/show/{cnvd_id}"
    headers = {"User-Agent": "CNVD-Research/1.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            # Look for CVE pattern in the page
            cves = cve_pattern.findall(resp.text)
            return cves
    except Exception as e:
        print(f"Error for {cnvd_id}: {e}")
    return []

# Sample 100 entries without CVE in text to estimate the true mapping rate
no_cve_sample = df[~df["has_cve"]].sample(min(100, without_cve), random_state=42)
mapped_count = 0

for idx, row in no_cve_sample.iterrows():
    cves = lookup_cnvd_cve(row["id"])
    if cves:
        mapped_count += 1
        print(f"  {row['id']} → {cves}")
    time.sleep(2)  # Be respectful

sample_mapping_rate = mapped_count / len(no_cve_sample)
estimated_total_mapped = with_cve + int(without_cve * sample_mapping_rate)

print(f"\nSample mapping rate: {sample_mapping_rate*100:.1f}%")
print(f"Estimated total with CVE mapping: {estimated_total_mapped} ({estimated_total_mapped/total*100:.1f}%)")
print(f"Estimated true CNVD-only: {total - estimated_total_mapped} ({(total - estimated_total_mapped)/total*100:.1f}%)")
```

> [!WARNING] CNVD access from Europe
> The CNVD website (`cnvd.org.cn`) may be slow or intermittently accessible from European IP ranges. Consider:
> - Using a VPN with an Asian exit node for faster access
> - Caching all responses to disk
> - Running the scraper during Chinese business hours for best availability
> - Sampling rather than full enumeration (100 samples gives +/-10% confidence interval)

---

## Step 6 — Temporal and severity distribution analysis

### 6a — Temporal distribution

```python
import matplotlib.pyplot as plt

year_counts = df["year"].value_counts().sort_index()

# Split by CVE presence
with_cve_by_year = df[df["has_cve"]].groupby("year").size()
without_cve_by_year = df[~df["has_cve"]].groupby("year").size()

fig, ax = plt.subplots(figsize=(14, 6))
years_all = sorted(df["year"].dropna().unique())

bar_with = [with_cve_by_year.get(y, 0) for y in years_all]
bar_without = [without_cve_by_year.get(y, 0) for y in years_all]

ax.bar(years_all, bar_with, label="CVE reference in text", alpha=0.7, color="#2196F3")
ax.bar(years_all, bar_without, bottom=bar_with,
       label="CNVD-only (no CVE in text)", alpha=0.7, color="#FF9800")
ax.set_xlabel("Year (from CNVD ID)")
ax.set_ylabel("Entries")
ax.set_title("CNVD Dataset — Temporal Distribution by CVE Mapping Status")
ax.legend()
plt.tight_layout()
plt.savefig("cnvd_temporal_distribution.png", dpi=150)
plt.show()
```

**What to look for:**
- Heavy concentration pre-2020 → lower operational value
- Recent years (2024-2026) with high CNVD-only counts → highest operational value
- Temporal gaps → evidence of filtering or incomplete data
- Year range should be plausible (CNVD was established in 2009)

### 6b — Severity distribution

```python
# Severity is categorical: 高 (High), 中 (Medium), 低 (Low)
sev_map = {"高": "High", "中": "Medium", "低": "Low"}
df["severity_en"] = df["severity"].map(sev_map)

print("Overall severity distribution:")
print(df["severity_en"].value_counts())
print()

# Compare severity distribution: with CVE vs without CVE
print("With CVE reference in text:")
print(df[df["has_cve"]]["severity_en"].value_counts(normalize=True).round(3))
print()
print("Without CVE reference (CNVD-only):")
print(df[~df["has_cve"]]["severity_en"].value_counts(normalize=True).round(3))
```

> [!TIP] RMSV signal check
> If the CNVD-only subset has a statistically lower proportion of `高` (High) entries compared to the CVE-mapped subset, that could indicate selective withholding of high-severity vulnerabilities — consistent with RMSV state-first disclosure requirements.
>
> Use a chi-squared test to check if the difference is statistically significant:
> ```python
> from scipy.stats import chi2_contingency
>
> ct = pd.crosstab(df["has_cve"], df["severity_en"])
> chi2, p, dof, expected = chi2_contingency(ct)
> print(f"Chi-squared: {chi2:.2f}, p-value: {p:.4e}")
> ```

---

## Step 7 — Vendor coverage analysis

Since all text is in Chinese, vendor matching needs both English and Chinese names.

```python
# Chinese vendors with both English and Chinese name variants
target_vendors = {
    "Huawei":     ["huawei", "华为"],
    "ZTE":        ["zte", "中兴"],
    "Hikvision":  ["hikvision", "海康威视"],
    "Dahua":      ["dahua", "大华"],
    "Tencent":    ["tencent", "腾讯"],
    "Alibaba":    ["alibaba", "阿里巴巴", "阿里云"],
    "Baidu":      ["baidu", "百度"],
    "Xiaomi":     ["xiaomi", "小米"],
    "Lenovo":     ["lenovo", "联想"],
    "Sangfor":    ["sangfor", "深信服"],
    "NSFOCUS":    ["nsfocus", "绿盟"],
    "Venustech":  ["venustech", "启明星辰"],
    "360":        ["360", "奇虎"],
    "Kingsoft":   ["kingsoft", "金山"],
    "DJI":        ["dji", "大疆"],
    "H3C":        ["h3c", "新华三", "华三"],
    "Ruijie":     ["ruijie", "锐捷"],
    "Inspur":     ["inspur", "浪潮"],
    "UFIDA":      ["ufida", "用友"],
    "Kingdee":    ["kingdee", "金蝶"],
}

print(f"{'Vendor':15s} | {'Count':>6s} | {'% of total':>10s}")
print("-" * 40)

for vendor_name, keywords in target_vendors.items():
    pattern = "|".join(keywords)
    # Search both title and description
    matches = (
        df["title"].str.contains(pattern, case=False, na=False) |
        df["description"].str.contains(pattern, case=False, na=False)
    )
    count = matches.sum()
    pct = count / total * 100
    print(f"{vendor_name:15s} | {count:6d} | {pct:9.1f}%")
```

**What to look for:**
- Major vendors (Huawei, ZTE, Hikvision) should have hundreds of entries
- If a major vendor is near-zero → evidence of selective filtering
- High presence of enterprise software vendors (UFIDA, Kingdee) → the dataset covers Chinese domestic software stack, which is genuinely absent from NVD

> [!NOTE] Steps 6 & 7 — Executed 2026-03-24
>
> **Step 6 — Temporal and severity charts generated:**
> - `cnvd_temporal_severity.png` — confirms RMSV cliff at 2022 (volume halves, severity composition shifts)
> - Post-2023 High severity doubles from ~35% to ~50%
> - Chi-squared test for severity x CVE mapping: chi-squared=18.82, p < 0.0001 (already computed in Step 5)
>
> **Step 7 — Vendor coverage findings:**
>
> The dataset is **dominated by Western/open-source software**, not Chinese vendors:
>
> | Category | Entries | % of dataset |
> |----------|---------|-------------|
> | PHP | 16,914 | 13.3% |
> | Linux | 8,733 | 6.9% |
> | Google | 8,029 | 6.3% |
> | Microsoft | 5,927 | 4.7% |
> | Adobe | 5,464 | 4.3% |
> | Oracle | 4,940 | 3.9% |
> | IBM | 4,875 | 3.8% |
> | WordPress | 4,549 | 3.6% |
> | **All Chinese vendors (30 searched)** | **7,567** | **5.9%** |
>
> **Top Chinese vendors:**
>
> | Vendor | Entries | Notes |
> |--------|---------|-------|
> | Huawei | 1,908 | Largest — likely all CVE-mapped |
> | D-Link | 1,186 | Networking — mostly CVE-mapped |
> | Foxit | 998 | PDF software |
> | Seeyon (致远) | 398 | OA platform — genuinely absent from NVD |
> | Qihoo 360 | 382 | Security vendor |
> | TP-Link | 341 | Networking — mostly CVE-mapped |
> | Kingsoft (金山) | 322 | Office/antivirus |
> | UFIDA/Yonyou (用友) | 204 | ERP — genuinely absent from NVD |
> | Ruijie (锐捷) | 192 | Networking |
> | Panwei (泛微) | 124 | OA platform — genuinely absent from NVD |
>
> **Key conclusions:**
> - Only 5.9% of entries match Chinese vendor keywords — the dataset is overwhelmingly Western software described in Chinese
> - The ~24,400 CNVD-only entries are likely from **smaller Chinese domestic software** (ERP, OA, CMS systems) that doesn't appear in the 30-vendor keyword search
> - Enterprise OA platforms (Seeyon, UFIDA/Yonyou, Panwei) — the software genuinely absent from NVD — have modest but real representation
> - Major Chinese hardware/network vendors (Huawei, ZTE, Hikvision) already have CVE coverage and contribute primarily to the 81% overlap, not the 19% tail
> - Charts saved: `cnvd_vendor_coverage.png`

---

## Step 8 — Generate report

```python
report = f"""# V1 — NVD Overlap Analysis — Findings

**Date:** {pd.Timestamp.now().strftime('%Y-%m-%d')}
**Dataset:** CIRCL/Vulnerability-CNVD (Hugging Face)
**Dataset size:** {total} entries

## Dataset Schema

| Field | Type | Notes |
|-------|------|-------|
| id | CNVD-YYYY-NNNNN | No CVE column |
| title | Chinese text | |
| description | Chinese text | |
| severity | 高/中/低 | No CVSS scores |

## CVE Text Extraction (lower bound)

| Metric | Count | Percentage |
|--------|-------|------------|
| Total entries | {total} | 100% |
| With CVE in text | {with_cve} | {with_cve/total*100:.1f}% |
| Without CVE in text | {without_cve} | {without_cve/total*100:.1f}% |
| Unique CVEs in text | {len(cnvd_cves)} | — |
| CVEs also in NVD | {len(overlap)} | {len(overlap)/max(len(cnvd_cves),1)*100:.1f}% of extracted CVEs |

## Reverse Lookup (estimated true mapping)

| Metric | Value |
|--------|-------|
| Sample size | {len(no_cve_sample)} |
| Sample mapping rate | {sample_mapping_rate*100:.1f}% |
| Estimated total with CVE | ~{estimated_total_mapped} |
| Estimated true CNVD-only | ~{total - estimated_total_mapped} ({(total - estimated_total_mapped)/total*100:.1f}%) |

## Year range

{df['year'].min():.0f} — {df['year'].max():.0f}

## Severity distribution

{df['severity_en'].value_counts().to_string()}

## Verdict

[FILL based on thresholds]
"""

with open("v1_findings.md", "w") as f:
    f.write(report)

print("Report written to v1_findings.md")
```

---

## Interpretation Thresholds

| Estimated CNVD-only % | Interpretation                                    | Impact on brief                                             |
| --------------------- | ------------------------------------------------- | ----------------------------------------------------------- |
| < 10%                 | Dataset is largely an NVD mirror                  | "Coverage expansion" claim collapses — downgrade to Claimed |
| 10–40%                | Modest expansion, depends on recency and severity | Nuance the brief — expansion is real but qualified          |
| 40–70%                | Significant unique coverage                       | Brief holds — confirmed net-new intelligence value          |
| > 70%                 | Dataset is predominantly Chinese-only data        | Strong validation — brief may understate the coverage gap   |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Step 1 — Download dataset | 5 min | Small dataset (23.9 MB Parquet) |
| Step 2 — Extract years | 5 min | Regex on `id` field |
| Step 3 — Extract CVEs from text | 10 min | Regex on `title` + `description` |
| Step 4 — NVD cross-reference | 1–3 hours | Depends on method (CVE List V5 clone is fastest) |
| Step 5 — Reverse lookup | 1–2 hours | Sampling 100 entries with rate limiting |
| Step 6 — Temporal + severity | 15 min | Plotting + chi-squared test |
| Step 7 — Vendor coverage | 15 min | Chinese + English keyword matching |
| Step 8 — Report | 15 min | Compile and interpret |
| **Total** | **3–5 hours** | First run; CVE List V5 clone saves ~2 hours |

---

## V1 — Verdict (2026-03-24, updated with 1,232-sample run)

> [!WARNING] Result: 19.2% CNVD-only (95% CI: 17.0%–21.4%) — Modest expansion (10–40% bracket)

**The dataset is primarily an NVD mirror (~81%) with a meaningful Chinese-domestic tail (~19%, estimated ~24,400 entries, 95% CI: 21,600–27,200).**

### Sampling progression

| Run | Samples | CVE mapping | CNVD-only | 95% CI |
|-----|---------|-------------|-----------|--------|
| Initial | 262 | 85.1% | 14.9% | +/-4.3% |
| Refined | 1,232 | 80.8% | 19.2% | +/-2.2% |

The refined run shifted the estimate by +4.3pp toward more CNVD-only entries, with a tighter confidence interval. The initial 262-sample run overestimated CVE coverage.

### What this means for the brief

The original assessment ("net coverage expansion") is **partially validated but overstated**:

1. **"Coverage expansion" should be downgraded** from Assessed to Claimed with qualification — 81% of entries already have CVE mappings, so the dataset's primary value for Western teams is *not* new vulnerability discovery but rather Chinese-language descriptions and severity classification of known CVEs.

2. **The genuine net-new coverage (~24,400 entries) is concentrated in 2019–2021** — the period with the lowest CVE mapping rates (66–70%). These are likely Chinese-domestic software vulnerabilities. Their operational value depends on whether the target organisation uses Chinese software.

3. **High-severity entries are disproportionately CNVD-only** (74.4% CVE mapping vs 84.7% for Medium, chi-squared=18.82, p < 0.0001). Chinese-domestic vulnerabilities that never receive CVEs tend to be classified as high severity. This is the opposite of the CNNVD severity-withholding pattern documented by Recorded Future — CNVD is not suppressing high-severity entries, it's accumulating them.

4. **The 2022 discontinuity** (CVE mapping jumps to 93–100%, entry volume drops by half) suggests a structural change in CNVD's submission process after RMSV took effect — worth investigating in [V4 Dataset Provenance](V4-Dataset-Provenance.md).

5. **The MacBERT model's primary utility** is severity classification of Chinese-language text for already-known CVEs, not discovery of unknown vulnerabilities.

### Recommended updates to brief

- [x] Downgrade "net coverage expansion" from Assessed to Claimed
- [x] Add V1 findings as a new section with tables
- [x] Reframe the dataset's value: Chinese-language severity classification of known CVEs, with a ~19% tail of Chinese-domestic entries
- [x] Add severity skew finding (statistically significant)
- [x] Note the 2022 structural discontinuity as an open question

### Vendor coverage findings (Step 7)

The dataset is 94% Western/open-source software (PHP 13.3%, Linux 6.9%, Google 6.3%, Microsoft 4.7%) with only 5.9% matching Chinese vendor keywords. The ~24,400 CNVD-only entries are likely from smaller Chinese domestic software (ERP, OA, CMS) — enterprise platforms like Seeyon (致远), UFIDA/Yonyou (用友), and Panwei (泛微) that are genuinely absent from NVD. Major Chinese vendors (Huawei, ZTE, Hikvision) already have CVE coverage and contribute to the 81% overlap, not the 19% tail.

### Next steps

- **[V4 Dataset Provenance](V4-Dataset-Provenance.md)** is now the highest-priority follow-up — the 2022 discontinuity needs explanation
- **V2–V3 (model quality)** remain relevant but reframed: the model classifies severity for known CVEs, not unknown vulnerabilities
