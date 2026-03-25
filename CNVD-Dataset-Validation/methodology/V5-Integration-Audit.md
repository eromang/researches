# V5 — Vulnerability-Lookup Integration Audit

**Objective:** Determine how CNVD data and the severity model are actually used in Vulnerability-Lookup — is the model output exposed to end users, is there a confidence gate, and does the platform surface the keyword-classifier limitations identified in V3?

---

## Context from V1–V4

| Track | Finding | Relevance to V5 |
|-------|---------|-----------------|
| V1 | 81% of entries map to existing CVEs | VL already has CVE severity from NVD — does it prefer CNVD model output or NVD CVSS? |
| V2 | Low recall 39.8%, ECE 0.053 | If model output is exposed without confidence gate, 60% of Low entries are misclassified |
| V3 | Keyword classifier, negation-blind | If VL uses model predictions for search/filter, users get misleading severity for atypical entries |
| V4 | Dataset = all CNVD entries with content, monthly updates | VL ingests CNVD stubs too (404-less for empty IDs) — how does VL handle entries with no severity? |

**Key question:** Does Vulnerability-Lookup expose the MacBERT model's severity predictions to end users as if they were authoritative CNVD severity ratings?

---

## Prerequisites

Same venv as V1–V4. No additional packages needed — this is primarily a code review and API audit.

```bash
source cnvd-validation/bin/activate
```

**Repositories to inspect:**
- `vulnerability-lookup/ML-Gateway` — already cloned in V4 (inference API)
- `vulnerability-lookup/vulnerability-lookup` — main platform

> [!NOTE] Prerequisites — Verified 2026-03-24
> - VL main repo cloned (320 Python files)
> - Key files identified:
>   - `vulnerabilitylookup/feeders/cnvd.py` — CNVD data ingestion feeder
>   - `website/web/api/v1/vlai.py` — ML-Gateway API proxy endpoint
>   - `bin/cnvd.py` — CNVD importer script (runs hourly: `sleep_in_sec=3600`)
> - CNVD feeder **stores raw CNVD JSON as-is** (line 108: `p.set(vuln_id, vuln_bytes)`) — no severity transformation
> - ML-Gateway is exposed as a **separate on-demand API endpoint** (`/vlai/severity-classification`), NOT called during CNVD ingestion
> - The CNVD feeder creates CVE cross-reference links (lines 97–104) but does NOT call the model
>
> **Preliminary conclusion (before completing all steps):** The model is NOT integrated into the CNVD ingestion pipeline. It's an on-demand API endpoint that users can call separately. CNVD severity comes directly from CNVD source data.

---

## Step 1 — Clone and map the Vulnerability-Lookup codebase

```bash
git clone --depth 1 https://github.com/vulnerability-lookup/vulnerability-lookup /tmp/vl-main
```

**Map the architecture:**
- Entry points (web routes, API endpoints)
- CNVD data ingestion pipeline
- Where ML-Gateway is called (if at all)
- How severity is stored and displayed
- Configuration for data sources

```bash
# Find Python files
find /tmp/vl-main -name "*.py" | head -30

# Search for CNVD-related code
grep -r "CNVD\|cnvd\|macbert\|ml-gateway\|ML.Gateway\|severity\|classify" \
  /tmp/vl-main --include="*.py" -l

# Search for model integration points
grep -r "classify\|prediction\|confidence\|threshold\|score" \
  /tmp/vl-main --include="*.py" -l

# Search for configuration
find /tmp/vl-main -name "*.cfg" -o -name "*.ini" -o -name "*.yml" -o -name "*.yaml" -o -name "*.toml" | head -20
```

> [!NOTE] Step 1 — Executed 2026-03-24
> - 320 Python files in repo
> - CNVD-related files: `feeders/cnvd.py`, `bin/cnvd.py`, `bin/index_fulltext.py`, `bin/index_vulnerabilities.py`
> - ML-related file: `website/web/api/v1/vlai.py` (single file — proxy endpoint)
> - Feeder architecture: Git-backed JSON ingestion → Valkey/Redis store
> - CNVD feeder runs hourly (`sleep_in_sec=3600`)

---

## Step 2 — Trace the CNVD data ingestion pipeline

**Question:** How does CNVD data enter Vulnerability-Lookup?

```bash
# Search for CNVD source configuration
grep -rn "CNVD\|cnvd\|china\|cncert" /tmp/vl-main --include="*.py" --include="*.cfg" --include="*.yml"

# Search for data source / feed management
grep -rn "source\|feed\|ingest\|import\|fetch\|crawl\|scrape" /tmp/vl-main --include="*.py" -l
```

**What to look for:**
- Scheduled fetching from CNVD website/API
- Data normalization (how CNVD fields map to VL's internal schema)
- Whether CNVD severity (高/中/低) is stored directly or replaced by model output
- How empty stubs (no description/severity) are handled — stored as placeholders or skipped?

> [!NOTE] Step 2 — Executed 2026-03-24
> - CNVD data ingested from Git repo of JSON files (`feeders/cnvd.py`)
> - Raw JSON stored directly: `p.set(vuln_id, orjson.dumps(vuln))` — **no transformation**
> - CVE cross-references created as Valkey links: `p.sadd(f"{vuln_id}:link", cveid)`
> - Severity comes from source field `serverity` (note: typo is in CNVD's original data)
> - **No model call in the ingestion pipeline**

---

## Step 3 — Trace the ML-Gateway integration

**Question:** Where and when does Vulnerability-Lookup call the severity classifier?

```bash
# Search for ML-Gateway calls, HTTP requests to classification endpoint
grep -rn "ml.gateway\|classify\|severity.*classif\|/classify\|prediction" \
  /tmp/vl-main --include="*.py"

# Search for model-related configuration
grep -rn "model\|macbert\|chinese.*bert\|transformer" \
  /tmp/vl-main --include="*.py" --include="*.cfg" --include="*.yml"
```

**What to look for:**
- Is ML-Gateway called at ingestion time (batch classification) or at query time (on-demand)?
- Is there a confidence threshold? (e.g., only use model output if confidence > 0.8)
- Is model severity stored alongside or instead of CNVD's original severity?
- Is the model output labeled as "predicted" or presented as the entry's severity?

> [!NOTE] Step 3 — Executed 2026-03-24
> - ML-Gateway exposed via `POST /api/vlai/severity-classification` (`vlai.py`)
> - **On-demand only** — not called during ingestion, not batch-processed
> - **No confidence threshold** — all predictions returned regardless of confidence
> - **No storage** — predictions are stateless, not persisted to Valkey
> - Validates severity labels per model (Chinese for MacBERT, English+Critical for RoBERTa)
> - Called exclusively from client-side JavaScript in the web UI

---

## Step 4 — Examine the web UI and API response for a CNVD entry

Compare what the API returns against what the CNVD source data says.

```python
import requests
import json

# Pick entries with known severity from the HF dataset
test_entries = [
    ("CNVD-2020-20184", "高"),    # High — code execution
    ("CNVD-2024-39267", "高"),    # High — Adobe Audition
    ("CNVD-2017-07695", "高"),    # High — SQL injection
    ("CNVD-2023-96681", "中"),    # Medium — Google Android
]

for cnvd_id, expected_sev in test_entries:
    url = f"https://vulnerability.circl.lu/api/vulnerability/{cnvd_id}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        api_sev = data.get("serverity", "?")  # Note: typo "serverity" in API

        # Check if model prediction is exposed
        model_fields = {k: v for k, v in data.items()
                       if "predict" in k.lower() or "classif" in k.lower()
                       or "model" in k.lower() or "confidence" in k.lower()
                       or "ml" in k.lower()}

        print(f"{cnvd_id}:")
        print(f"  HF dataset severity: {expected_sev}")
        print(f"  API severity:        {api_sev}")
        print(f"  Model fields:        {model_fields if model_fields else 'None found'}")
        print(f"  All keys:            {list(data.keys())}")
        print()
```

**What to look for:**
- Does the API expose model predictions as separate fields (e.g., `predicted_severity`, `model_confidence`)?
- Or is the `serverity` field the CNVD original value with no model augmentation?
- Are there entries where API severity differs from HF dataset severity → would indicate model override

> [!NOTE] Step 4 — Executed 2026-03-24
> - 5 entries inspected — all severity values match HF dataset exactly
> - **Zero model-related fields** in any API response (no `predicted`, `confidence`, `model`, `ml`, `ai`, `score`)
> - API keys: `number`, `title`, `serverity`, `products`, `isEvent`, `submitTime`, `openTime`, `discovererName`, `formalWay`, `description`, `patchName`, `patchDescription` (+ `cves`, `bids`, `referenceLink` when present)
> - **The API serves raw CNVD data with no model augmentation**

---

## Step 5 — Check the web UI presentation

**Question:** How is CNVD severity displayed to end users?

```python
# Fetch the web page for a CNVD entry
import requests

cnvd_id = "CNVD-2020-20184"
url = f"https://vulnerability.circl.lu/vuln/{cnvd_id}"
resp = requests.get(url, timeout=15)

if resp.status_code == 200:
    # Look for severity display, model indicators, confidence scores
    import re

    # Search for severity-related text
    sev_patterns = [
        r'severity.*?["\'].*?["\']',
        r'serverity.*?["\'].*?["\']',
        r'高|中|低|High|Medium|Low|Critical',
        r'confidence.*?\d+\.\d+',
        r'predicted|classified|model',
    ]

    for pattern in sev_patterns:
        matches = re.findall(pattern, resp.text, re.IGNORECASE)
        if matches:
            print(f"Pattern '{pattern}': {matches[:5]}")

    # Check for ML/model disclaimers
    if "model" in resp.text.lower() or "predict" in resp.text.lower() or "classif" in resp.text.lower():
        print("\nModel-related text found in page")
    else:
        print("\nNo model-related text found in page — severity appears as native data")
```

**What to look for:**
- Is the severity displayed with a "predicted by AI" label or disclaimer?
- Or does it appear as if it's the official CNVD severity with no distinction?
- Is confidence score visible to users?
- Is there any indication that the severity came from a keyword classifier vs CNVD's own assessment?

> [!NOTE] Step 5 — Executed 2026-03-24 — Client-side enrichment found
> - The web UI **does** reference VLAI — JavaScript function `updateSeverityScore()` fires on `DOMContentLoaded`
> - Reads description text from DOM, gets model name from `model-name` attribute
> - Calls `POST /api/vlai/severity-classification` via `fetch()`
> - On success: displays colored badge `"High 高 (confidence: 0.9802)"` with Bootstrap styling
> - On failure: **silently removes the element** (`.catch(() => aiSeverityElement.parentNode.remove())`)
> - Chinese labels translated: `高 → "High 高"`, `中 → "Medium 中"`, `低 → "Low 低"`
> - No explicit "AI-predicted" disclaimer — but model name serves as implicit attribution
> - **The prediction is displayed alongside the original CNVD severity, not replacing it**

---

## Step 6 — Check for entries where model severity != CNVD severity

If the model is used to augment or override CNVD severity, there should be entries where the API severity differs from the HF dataset.

```python
from datasets import load_dataset
import pandas as pd
import requests
import time

ds = load_dataset("CIRCL/Vulnerability-CNVD")
df = pd.concat([pd.DataFrame(ds["train"]), pd.DataFrame(ds["test"])], ignore_index=True)

# Sample 50 entries across severity levels
sample = pd.concat([
    df[df["severity"] == "高"].sample(20, random_state=42),
    df[df["severity"] == "中"].sample(20, random_state=42),
    df[df["severity"] == "低"].sample(10, random_state=42),
])

mismatches = []
for _, row in sample.iterrows():
    url = f"https://vulnerability.circl.lu/api/vulnerability/{row['id']}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            api_sev = data.get("serverity", "?")
            if api_sev != row["severity"] and api_sev != "?":
                mismatches.append({
                    "id": row["id"],
                    "hf_severity": row["severity"],
                    "api_severity": api_sev,
                })
    except:
        pass
    time.sleep(0.5)

print(f"Checked {len(sample)} entries")
print(f"Mismatches: {len(mismatches)}")
for m in mismatches:
    print(f"  {m['id']}: HF={m['hf_severity']}, API={m['api_severity']}")
```

**What this tells us:**
- **Zero mismatches** → the model is NOT used to override CNVD severity in the API. Severity comes from CNVD directly.
- **Some mismatches** → the model augments or overrides CNVD severity for some entries. Check which direction (model upgrades or downgrades severity).
- **Systematic mismatches** → the model has replaced CNVD severity entirely.

> [!NOTE] Step 6 — Executed 2026-03-24 — Zero mismatches
> - 50 entries checked (20 High, 20 Medium, 10 Low)
> - **50/50 matches** — API severity = HF dataset severity for every entry
> - 0 mismatches, 0 errors
> - **The model does NOT override CNVD severity.** All severity values come directly from CNVD source data.

---

## Step 7 — Generate report

Compile findings into [V5 Findings Report](../findings/V5-Integration-Audit-Findings.md):

1. Architecture overview — how VL is structured
2. CNVD ingestion pipeline — how data flows in
3. ML-Gateway integration — where/when the model is called
4. API response analysis — does model output appear in responses?
5. Web UI presentation — how severity is displayed to users
6. Severity mismatch check — model override detection
7. Verdict: what role does the model actually play?

---

## Interpretation Framework

| Finding | Interpretation | Impact |
|---------|---------------|--------|
| Model not called in VL codebase | ML-Gateway is standalone; model is not integrated into the platform | Model is a research artifact, not production infrastructure |
| Model called at ingestion | Severity is pre-classified; all entries get model severity | All V2/V3 limitations propagate to VL users |
| Model called at query time | On-demand classification; user sees model output | Performance impact; V3 limitations visible per-query |
| Confidence threshold exists | VL filters low-confidence predictions | Partially mitigates V2 calibration issues |
| No confidence threshold | All model predictions treated equally | V2's overconfidence on short text is a real risk |
| API severity = CNVD severity | Model is not used for CNVD entries at all | Model is for other sources or future use only |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Step 1 — Clone and map codebase | 15 min | git clone + grep |
| Step 2 — CNVD ingestion trace | 15 min | Code reading |
| Step 3 — ML-Gateway integration trace | 15 min | Code reading |
| Step 4 — API response inspection | 10 min | 4 API queries |
| Step 5 — Web UI check | 10 min | 1 web page fetch + parse |
| Step 6 — Severity mismatch check | 30 min | 50 API queries with rate limiting |
| Step 7 — Report | 15 min | Compile findings |
| **Total** | **~2 hours** | Primarily code review |

---

## Next Steps After V5

- If model is not integrated → the "AI model" claim in the LinkedIn post overstates its operational role; the model is a research artifact
- If model overrides CNVD severity → V2/V3 findings (keyword classifier, negation-blind) are production issues
- If confidence threshold exists → document it; check if it mitigates the worst V2/V3 failures
- If severity comes directly from CNVD → the model's practical value is limited to the HF dataset itself (ML research), not Vulnerability-Lookup operations
- Regardless → update the CNVD Dataset Hugging Face Brief with V5 findings
