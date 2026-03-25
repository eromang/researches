# V5 — Integration Audit — Findings Report

**Date:** 2026-03-24
**Repositories audited:** `vulnerability-lookup/vulnerability-lookup` (320 Python files), `vulnerability-lookup/ML-Gateway` (6 Python files)
**Method:** Source code review, API response inspection, web UI analysis, severity mismatch check

---

## 1. Executive Finding

**The MacBERT model is NOT integrated into the CNVD data pipeline.** CNVD data is ingested directly from source JSON files and stored with original severity values unchanged. The model exists as an optional, on-demand client-side enrichment in the web UI — it is called via JavaScript on page load, displays a prediction alongside (not replacing) the original severity, and silently disappears if ML-Gateway is unreachable. The API exposes no model predictions. Zero severity mismatches were found across 50 sampled entries.

---

## 2. Architecture

```
CNVD Source (Git repo of JSON files)
    │
    ▼
CNVD Feeder (cnvd.py)          ← Ingests raw JSON, stores as-is
    │                               No model call
    ▼
Valkey/Redis Store              ← Raw CNVD data with original severity
    │
    ├──▶ REST API (/api/vulnerability/{id})  ← Returns raw CNVD JSON
    │                                            No model fields
    │
    └──▶ Web UI (/vuln/{id})
              │
              └──▶ JavaScript (client-side, on page load)
                      │
                      └──▶ POST /api/vlai/severity-classification
                              │
                              └──▶ ML-Gateway (separate service)
                                      │
                                      └──▶ MacBERT model prediction
                                              │
                                              ▼
                                      Displayed as additional badge:
                                      "High 高 (confidence: 0.9802)"
                                      (silently removed if ML-Gateway down)
```

---

## 3. CNVD Data Ingestion (Step 1–2)

**File:** `vulnerabilitylookup/feeders/cnvd.py`

The CNVD feeder:
- Pulls from a Git repository of CNVD JSON files (hourly: `sleep_in_sec=3600`)
- Iterates over new commits, reads JSON vulnerability entries
- Stores raw vulnerability JSON directly in Valkey (`p.set(vuln_id, vuln_bytes)`)
- Creates CVE cross-reference links (`p.sadd(f"{vuln_id}:link", cveid)`)
- Tracks publication counters by year and month
- **No model call anywhere in the ingestion pipeline**
- **No severity transformation** — the `serverity` field from CNVD source is stored verbatim

---

## 4. ML-Gateway Integration (Step 3)

**File:** `website/web/api/v1/vlai.py`

The VLAI endpoint is a **proxy to ML-Gateway**:
- Exposed as `POST /api/vlai/severity-classification`
- Accepts `description` (text) and `model` (model name) as JSON
- Forwards to ML-Gateway's `/classify/severity` endpoint
- Returns `{"severity": "...", "confidence": ...}`
- Validates severity labels per model (Chinese labels for MacBERT, English+Critical for RoBERTa)
- **No confidence threshold** — all predictions returned regardless of confidence
- **No storage** — predictions are not persisted; each call is stateless

The endpoint is **on-demand only**. It is not called during data ingestion, not called by the API, and not called by any batch process.

> [!NOTE] R3 reinforcement (2026-03-24) — Endpoint confirmed LIVE
> Direct `POST` to `https://vulnerability.circl.lu/api/vlai/severity-classification` returned HTTP 200 for all three models:
> - Chinese MacBERT: `{"severity": "高", "confidence": 0.8075}`
> - English RoBERTa: `{"severity": "High", "confidence": 0.9098}`
> - Default (RoBERTa): `{"severity": "Critical", "confidence": 0.6228}`
>
> ML-Gateway is running in production. The web UI classification widget is functional — not a dead feature.

---

## 5. API Response (Step 4)

5 CNVD entries inspected. All return raw CNVD JSON with no model-related fields:

| Field | Present | Notes |
|-------|---------|-------|
| `number` | Yes | CNVD ID |
| `title` | Yes | Chinese title |
| `serverity` | Yes | Original CNVD severity (高/中/低) |
| `description` | Yes | Chinese description |
| `cves` | Some | CVE cross-references (when available) |
| `products` | Yes | Affected products |
| `submitTime` | Yes | Submission date |
| `openTime` | Yes | Publication date |
| `predicted_severity` | **No** | Not present |
| `confidence` | **No** | Not present |
| `model` | **No** | Not present |
| `ai_*` | **No** | No AI/ML fields |

---

## 6. Web UI Presentation (Step 5)

The web UI **does** display model predictions, but as a **client-side enrichment**:

1. Page loads with CNVD data (original severity)
2. JavaScript function `updateSeverityScore()` fires on `DOMContentLoaded`
3. JavaScript reads the vulnerability description from the page DOM
4. JavaScript detects the model name from a `model-name` attribute on the description element
5. `fetch("/api/vlai/severity-classification", ...)` sends description + model to VLAI endpoint
6. On success: displays a colored badge with `"High 高 (confidence: 0.9802)"`
7. On failure: **silently removes the classification element** (`.catch(() => aiSeverityElement.parentNode.remove())`)

**Key observations:**
- The model prediction is displayed **alongside** the original severity, not replacing it
- The model name is visible in the UI (via the `model-name` attribute)
- Confidence score is displayed
- Chinese severity labels are translated: `"低" → "Low 低"`, `"中" → "Medium 中"`, `"高" → "High 高"`
- If ML-Gateway is down, the prediction disappears without error — users see only the original CNVD severity
- No disclaimer or "AI-generated" label — but the model name serves as implicit attribution

---

## 7. Severity Mismatch Check (Step 6)

50 entries checked (20 High, 20 Medium, 10 Low):

| Metric | Value |
|--------|-------|
| Checked | 50 |
| Matches (API = HF dataset) | **50** |
| Mismatches | **0** |
| Errors | 0 |

**The model does NOT override CNVD severity in the API.** All severity values come directly from CNVD source data.

---

## 8. Verdict

### The model's actual role in Vulnerability-Lookup

| Aspect | Claim (LinkedIn post) | Reality (V5 audit) |
|--------|----------------------|-------------------|
| "This model is already used in Vulnerability-Lookup" | Implies production integration | Model is a client-side JavaScript enrichment; ML-Gateway confirmed live (R3), but silently disappears if down |
| Implied: model classifies CNVD vulnerabilities | Implies model output is authoritative | CNVD's own severity is the stored/API value; model output is transient |
| Implied: model augments vulnerability intelligence | Implies operational value | Model adds a redundant severity badge to entries that already have CNVD severity |

### What the model actually does in VL

1. **Displays a redundant prediction** — for entries that already have CNVD severity, the model predicts the same thing from the description text. This adds no information.
2. **Potentially useful for entries without severity** — but V4 showed that entries without severity also have no description (empty stubs), so there's nothing for the model to classify.
3. **Optional and degradation-tolerant** — if ML-Gateway is down, VL works identically. The model is a nice-to-have, not infrastructure.

### Impact on original brief

The "model used in Vulnerability-Lookup" claim is **technically true but functionally misleading**:
- The model runs client-side on page view, not in the data pipeline
- Its output is not stored, not searchable, not in the API
- For CNVD entries, it produces a redundant prediction alongside the existing severity
- The V3 finding (keyword classifier, negation-blind) means this redundant prediction is also unreliable for atypical entries

---

## 9. Methodology Notes

- **VL main repo:** `vulnerability-lookup/vulnerability-lookup`, 320 Python files
- **Key files:** `feeders/cnvd.py` (ingestion), `web/api/v1/vlai.py` (ML proxy), `bin/cnvd.py` (importer script)
- **API probing:** 5 entries checked for model fields (none found)
- **Web UI:** JavaScript analysis of `updateSeverityScore()` function
- **Mismatch check:** 50 entries (20 High, 20 Medium, 10 Low)
- **Full methodology:** [V5 Integration Audit](../methodology/V5-Integration-Audit.md)
