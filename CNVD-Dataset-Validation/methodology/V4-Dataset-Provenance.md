# V4 — Dataset Provenance

**Objective:** Determine whether the Hugging Face dataset is the full CNVD or a filtered/curated subset, and explain the 2022 structural discontinuity identified in V1.

---

## Context from V1

V1 identified two anomalies requiring explanation:

1. **2022 volume cliff:** Entries drop from 17,398 (2021) to 9,660 (2022) — a 44% decline. Simultaneously, CVE mapping rate jumps from 66.5% to 97.8%.
2. **Post-2023 severity shift:** High severity rises from ~35% to ~50%, Low drops from ~12% to ~4%.

Both coincide with China's RMSV regulations (effective September 2021). V4 investigates whether these reflect changes in the CNVD database itself, or filtering applied when creating the Hugging Face dataset.

---

## Prerequisites

Same venv as V1–V3. Additional tool: web browser or `curl` for CNVD website inspection.

```bash
source cnvd-validation/bin/activate
```

---

## Step 1 — Compare dataset size against CNVD website totals

The CNVD website (`cnvd.org.cn`) displays a running count of published vulnerabilities.

```python
import requests
import re
from bs4 import BeautifulSoup

# Attempt to scrape CNVD homepage for total vulnerability count
url = "https://www.cnvd.org.cn/"
headers = {"User-Agent": "Mozilla/5.0 (Research/CNVD-Validation)"}

try:
    resp = requests.get(url, headers=headers, timeout=30)
    if resp.status_code == 200:
        # Look for total count (typically displayed on the homepage)
        # Pattern varies — may need manual inspection
        numbers = re.findall(r'\d{4,}', resp.text)
        print(f"Numbers found on CNVD homepage: {numbers[:20]}")
        print(f"\nPage title: {resp.text[:500]}")
    else:
        print(f"HTTP {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
    print("Fallback: check CNVD website manually in browser")
```

> [!WARNING] CNVD website access
> The CNVD website may be slow or inaccessible from Europe. If automated scraping fails:
> 1. Use a browser with a VPN (Asian exit node)
> 2. Check `https://www.cnvd.org.cn/flaw/list`  for pagination totals
> 3. Search for "CNVD total vulnerabilities" in Chinese search engines (Baidu)
> 4. Check archived versions via Wayback Machine: `https://web.archive.org/web/*/cnvd.org.cn`

**Expected comparison:**

| Source | Count | Interpretation |
|--------|-------|---------------|
| Hugging Face dataset | 127,562 | Known |
| CNVD website (current) | ??? | If much larger → dataset is a subset |
| CNVD website (2021 snapshot) | ??? | Pre-RMSV comparison |

> [!WARNING] Step 1 — Executed 2026-03-24 — CNVD website inaccessible
> - `https://www.cnvd.org.cn/` → HTTP 521 (Cloudflare origin down)
> - `https://www.cnvd.org.cn/flaw/list` → HTTP 521
> - Wayback Machine: no 200 snapshots available for 2022–2026
> - VL API endpoints (`/stats`, `/info`, `/sources`) → all 404
> - **Fallback:** Step 2 (sequence gap analysis) provides a more precise answer than the website total would have.

---

## Step 2 — Analyse CNVD ID sequence gaps

CNVD IDs follow the pattern `CNVD-YYYY-NNNNN`. If the dataset is complete, the sequence numbers within each year should be roughly contiguous.

```python
import pandas as pd
from datasets import load_dataset

ds = load_dataset("CIRCL/Vulnerability-CNVD")
df = pd.concat([pd.DataFrame(ds["train"]), pd.DataFrame(ds["test"])], ignore_index=True)

# Extract year and sequence number
df["year"] = df["id"].str.extract(r"CNVD-(\d{4})-", expand=False).astype(int)
df["seq"] = df["id"].str.extract(r"CNVD-\d{4}-(\d+)", expand=False).astype(int)

print("=== SEQUENCE ANALYSIS BY YEAR ===\n")
print(f"{'Year':>6s}  {'Count':>6s}  {'Min seq':>8s}  {'Max seq':>8s}  {'Range':>8s}  {'Coverage':>9s}  {'Gaps':>6s}")
print("-" * 65)

for year in sorted(df["year"].unique()):
    yr = df[df["year"] == year]
    count = len(yr)
    min_seq = yr["seq"].min()
    max_seq = yr["seq"].max()
    seq_range = max_seq - min_seq + 1
    coverage = count / seq_range * 100 if seq_range > 0 else 0
    gaps = seq_range - count
    flag = " ⚠️" if coverage < 50 else ""
    print(f"  {year}  {count:6d}  {min_seq:8d}  {max_seq:8d}  {seq_range:8d}  {coverage:8.1f}%  {gaps:6d}{flag}")
```

**What to look for:**
- **Coverage <50%** → heavy filtering for that year. If the max sequence number is 20,000 but only 5,000 entries exist, 75% of entries were excluded.
- **Post-2022 coverage drop** → confirms the 2022 cliff is due to filtering, not reduced CNVD submissions
- **Pre-2022 coverage near 100%** → the pre-RMSV dataset is complete
- **Non-contiguous sequences** → specific entries were removed (selective filtering)

> [!NOTE] Step 2 — Executed 2026-03-24 — CNVD reserves ~100K IDs/year
>
> | Year | In dataset | Max seq | ID range | Coverage |
> |------|-----------|---------|----------|----------|
> | 2015 | 8,045 | 8,561 | 8,561 | **94.0%** |
> | 2016 | 10,496 | 13,303 | 13,302 | 78.9% |
> | 2017 | 15,318 | 38,524 | 38,516 | 39.8% |
> | 2018 | 13,915 | 26,996 | 26,919 | 51.7% |
> | 2019 | 14,733 | 47,663 | 47,661 | 30.9% |
> | 2020 | 18,201 | 75,709 | 75,709 | **24.0%** |
> | 2021 | 17,398 | 103,668 | 103,668 | **16.8%** |
> | 2022 | 9,660 | 91,582 | 90,997 | **10.6%** |
> | 2023 | 4,129 | 101,689 | 101,689 | **4.1%** |
> | 2024 | 5,375 | 49,866 | 49,710 | 10.8% |
> | 2025 | 8,714 | 31,568 | 31,468 | 27.7% |
> | 2026 | 1,504 | 13,836 | 13,836 | 10.9% |
>
> **Key finding:** CNVD reserves 50,000–100,000 IDs per year (2019–2023). Coverage declined steadily from 94% (2015) to 4% (2023). The ID reservation rate did NOT decrease after RMSV — what decreased is the rate of publishing full vulnerability details.

---

## Step 3 — Check Vulnerability-Lookup's CNVD coverage

The Vulnerability-Lookup API may have more CNVD entries than the Hugging Face dataset (the dataset was curated for ML training, not as a complete mirror).

```python
import requests
import time

# Sample CNVD IDs NOT in the Hugging Face dataset
# Generate IDs from known gaps in Step 2
dataset_ids = set(df["id"].tolist())

# Pick a year with suspected gaps (e.g., 2022)
test_year = 2022
yr_df = df[df["year"] == test_year]
max_seq = yr_df["seq"].max()
existing_seqs = set(yr_df["seq"].tolist())

# Find 50 missing sequence numbers
missing_seqs = []
for seq in range(1, max_seq + 1):
    if seq not in existing_seqs:
        missing_seqs.append(seq)
    if len(missing_seqs) >= 50:
        break

print(f"Testing {len(missing_seqs)} CNVD IDs missing from Hugging Face dataset (year {test_year})")

found_in_vl = 0
not_found = 0
found_entries = []

for seq in missing_seqs[:50]:
    cnvd_id = f"CNVD-{test_year}-{seq:05d}"
    url = f"https://vulnerability.circl.lu/api/vulnerability/{cnvd_id}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            sev = data.get("serverity", "?")
            has_cve = "cves" in data and data["cves"]
            found_in_vl += 1
            found_entries.append({"id": cnvd_id, "severity": sev, "has_cve": bool(has_cve)})
        elif resp.status_code == 404:
            not_found += 1
    except:
        pass
    time.sleep(0.5)

print(f"\nResults for {test_year} missing IDs:")
print(f"  Found in Vulnerability-Lookup: {found_in_vl}")
print(f"  Not found (404):               {not_found}")
print(f"  Coverage in VL:                 {found_in_vl/(found_in_vl+not_found)*100:.1f}%")

if found_entries:
    fdf = pd.DataFrame(found_entries)
    print(f"\n  Severity distribution of found entries:")
    print(f"  {fdf['severity'].value_counts().to_string()}")
    print(f"  Has CVE: {fdf['has_cve'].sum()}/{len(fdf)}")
```

**What this tells us:**
- If missing IDs exist in Vulnerability-Lookup but not in the HF dataset → the HF dataset is a **filtered subset** of what CIRCL has ingested
- If missing IDs don't exist in VL either → the CNVD itself doesn't have those sequence numbers (CNVD may skip IDs)
- If missing entries are predominantly Low severity or Chinese-domestic → the filtering was severity-based or CVE-mapping-based

> [!NOTE] Step 3 — Executed 2026-03-24 — Missing IDs are empty stubs
>
> 100 missing IDs probed (25/year for 2020–2023) — **all 100 exist in Vulnerability-Lookup but contain no data:**
>
> | Property | In HF dataset (n=100) | Missing from HF (n=100) |
> |----------|:--------------------:|:----------------------:|
> | Has description | Yes (141 chars avg) | **No (0 chars)** |
> | Has severity | Yes (高/中/低) | **No ("?")** |
> | Has CVE mapping | 84% | **0%** |
>
> **Conclusion:** The excluded entries are empty stubs — CNVD IDs reserved but never populated with vulnerability details. The HF dataset is NOT filtered by CIRCL. It contains all entries with actual content. The filtering happens upstream at CNVD itself.
>
> Additionally, 100 in-dataset entries were probed for comparison, confirming the content/no-content distinction is the sole differentiator.

---

## Step 4 — Check the Hugging Face dataset's Git history

The dataset is hosted on Hugging Face with Git-backed versioning. Check the commit history for evidence of filtering, updates, or removals.

```bash
# Clone the dataset repo metadata (not the data files)
git clone --depth 5 https://huggingface.co/datasets/CIRCL/Vulnerability-CNVD /tmp/cnvd-hf-repo 2>/dev/null
cd /tmp/cnvd-hf-repo
git log --oneline -20
```

Or via the Hugging Face API:

```python
from huggingface_hub import HfApi

api = HfApi()
commits = api.list_repo_commits("CIRCL/Vulnerability-CNVD", repo_type="dataset")
for c in commits[:20]:
    print(f"{c.commit_id[:8]}  {c.created_at}  {c.title}")
```

**What to look for:**
- Multiple commits → the dataset has been updated/modified
- Commit messages mentioning "filter", "clean", "remove", "subset" → explicit curation
- Dataset size changes across commits → entries added or removed over time
- README changes explaining the curation criteria

> [!NOTE] Step 4 — Executed 2026-03-24 — Dataset actively maintained
> - **14 commits** total, from initial commit (2025-06-27) to most recent upload (2026-03-23)
> - Roughly monthly update cadence
> - All commit messages are generic ("Upload dataset") — no filtering criteria documented
> - Most recent update coincides with the LinkedIn announcement
> - The dataset is a living, periodically refreshed snapshot — not a one-time dump

---

## Step 5 — Check CIRCL's ML-Gateway source code

The model is used via `vulnerability-lookup/ML-Gateway` (GitHub). The source code may reveal how the dataset was constructed.

```bash
# Clone ML-Gateway
git clone --depth 1 https://github.com/vulnerability-lookup/ML-Gateway /tmp/ml-gateway
# Look for dataset construction, filtering, or preprocessing scripts
find /tmp/ml-gateway -name "*.py" | head -20
grep -r "CNVD\|cnvd\|filter\|severity\|train_test_split" /tmp/ml-gateway --include="*.py" -l
```

**What to look for:**
- Data preprocessing scripts that filter by severity, CVE presence, or date range
- Train/test split logic — was it random or stratified?
- Any explicit exclusion criteria (e.g., "remove entries without description", "exclude severity=低")

> [!NOTE] Step 5 — Executed 2026-03-24 — Inference API only, no filtering code
> - Cloned `vulnerability-lookup/ML-Gateway` from GitHub
> - Repository contains only a FastAPI inference service: model loading, classification endpoint, schemas
> - **No dataset construction, preprocessing, or filtering scripts found**
> - Python files: `classification_router.py`, `severity_model.py`, `schemas.py`, `cli.py`, `main.py`, `classification_service.py`
> - The model name `CIRCL/vulnerability-severity-classification-chinese-macbert-base` is hardcoded as one of three supported models (alongside RoBERTa-base and DistilBERT)
> - **Conclusion:** Dataset construction happens in CIRCL's Vulnerability-Lookup ingestion pipeline, not in ML-Gateway. The HF dataset is a periodic export of ingested CNVD entries with content.

---

## Step 6 — Compare CNVD website statistics with dataset by year

If Step 1 fails to get the total from the website directly, use the Wayback Machine to find historical snapshots.

```python
import requests

# Wayback Machine CDX API — find snapshots of CNVD
cdx_url = "http://web.archive.org/cdx/search/cdx"
params = {
    "url": "cnvd.org.cn",
    "output": "json",
    "limit": 20,
    "fl": "timestamp,statuscode",
    "filter": "statuscode:200",
}

try:
    resp = requests.get(cdx_url, params=params, timeout=30)
    if resp.status_code == 200:
        data = resp.json()
        print("Available CNVD snapshots (Wayback Machine):")
        for row in data[1:]:
            print(f"  {row[0][:4]}-{row[0][4:6]}-{row[0][6:8]}  HTTP {row[1]}")
except Exception as e:
    print(f"Wayback Machine query failed: {e}")
```

> [!WARNING] Step 6 — Executed 2026-03-24 — No usable Wayback snapshots
> - Wayback Machine CDX API returned snapshots only for 2010–2012 (HTTP 200)
> - No 200 snapshots available for 2022–2026
> - The 2021 query timed out
> - **Step 6 is inconclusive** — but Steps 2 and 3 already provide a more precise answer (per-year coverage percentages and confirmation that missing IDs are empty stubs) than a website total comparison would have.

---

## Step 7 — Generate report

Compile findings into [V4 Findings Report](../findings/V4-Dataset-Provenance-Findings.md):

1. Dataset size vs CNVD total — is it complete or a subset?
2. Sequence gap analysis — per-year coverage percentages
3. Missing ID probing via Vulnerability-Lookup — what was excluded?
4. HF commit history — evidence of curation
5. ML-Gateway source — filtering logic if found
6. Verdict: what explains the 2022 cliff?

---

## Interpretation Framework

| Finding | Interpretation |
|---------|---------------|
| Coverage ~100% pre-2022, <50% post-2022 | CIRCL filtered post-RMSV entries (or CNVD stopped publishing them) |
| Missing IDs exist in VL but not HF dataset | HF dataset is a curated ML training subset, not a full mirror |
| Missing IDs are predominantly Low severity | Severity-based filtering for ML training (balanced classes) |
| Missing IDs have no CVE mapping | CVE-mapping-based filtering post-RMSV |
| ML-Gateway has explicit filtering code | Confirms deliberate curation |
| Commit history shows size changes | Dataset has evolved — not a single dump |
| CNVD website total >> 127,562 | Dataset is a small fraction of the full CNVD |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Step 1 — CNVD website total | 15 min | May require VPN; fallback to Wayback |
| Step 2 — Sequence gap analysis | 10 min | Analysis on existing dataset |
| Step 3 — Missing ID probing | 30 min | 50 API queries with rate limiting |
| Step 4 — HF commit history | 10 min | API query |
| Step 5 — ML-Gateway source | 15 min | Git clone + grep |
| Step 6 — Wayback comparison | 15 min | CDX API query |
| Step 7 — Report | 15 min | Compile findings |
| **Total** | **~2 hours** | Step 1 may need manual fallback |

---

## Next Steps After V4

- If the dataset is confirmed as a curated subset → the "127,562 vulnerabilities" framing is misleading; update the brief
- If post-2022 filtering is CVE-based → the 2022 cliff is an artifact of dataset construction, not RMSV
- If the full CNVD is significantly larger → the actual coverage expansion may be larger than what the HF dataset represents
- [V5 Integration Audit](V5-Integration-Audit.md) becomes more important — does Vulnerability-Lookup use the full CNVD ingestion or only the HF subset?
