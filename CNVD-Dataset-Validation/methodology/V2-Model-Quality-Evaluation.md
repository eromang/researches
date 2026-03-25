# V2 — Model Quality Evaluation

**Objective:** Independently evaluate the CIRCL severity classification model's accuracy, per-class performance, and practical utility beyond the self-reported 77.83% accuracy.

---

## Model Profile (verified 2026-03-24)

| Field | Value |
|-------|-------|
| Model | `CIRCL/vulnerability-severity-classification-chinese-macbert-base` |
| Base | `hfl/chinese-macbert-base` (RoBERTa-based, 0.1B params) |
| Task | Text classification (3-class severity) |
| Labels | `高` (High) / `中` (Medium) / `低` (Low) |
| Training data | `CIRCL/Vulnerability-CNVD` (train split: 114,805) |
| Self-reported accuracy | 77.83% (on test split: 12,757) |
| Training | 5 epochs, lr=3e-05, batch=32, AdamW, linear scheduler |
| Validation loss | 1.2224 (increasing from epoch 3 — signs of overfitting) |
| License | Apache 2.0 |
| Implementation | `vulnerability-lookup/ML-Gateway` (GitHub) |

> [!WARNING] V1 context — why this matters
> V1 showed the dataset is 81% CVE-mapped. The model classifies severity of Chinese-language vulnerability descriptions — primarily for known CVEs. Its practical value depends on:
> 1. Whether 77.83% accuracy is useful for triage (vs random baseline of 55% if always predicting Medium)
> 2. Whether accuracy varies by vulnerability type, vendor, or year
> 3. Whether the model generalises beyond CNVD-formatted text

---

## Prerequisites

### Environment (set up 2026-03-24)

**Activate:**

```bash
source cnvd-validation/bin/activate
```

**V2 packages added (pinned in `requirements.txt`):**

| Package | Version | Purpose |
|---------|---------|---------|
| `transformers` | 5.3.0 | Model loading and inference |
| `torch` | 2.11.0 | PyTorch backend (MPS acceleration) |
| `scikit-learn` | 1.8.0 | Classification metrics, confusion matrix |
| `seaborn` | 0.13.2 | Confusion matrix heatmap |

**Hardware:** MPS (Apple Silicon) confirmed available. Model is 0.1B params — inference runs on MPS without issues.

**Model cached:** `CIRCL/vulnerability-severity-classification-chinese-macbert-base` downloaded and verified.

> [!NOTE] Prerequisites — Verified 2026-03-24
> - All imports work
> - MPS backend available
> - Model downloads and produces correct test prediction: `High` with score 0.9798 for buffer overflow description
> - Note: model outputs English labels (`High`/`Medium`/`Low`), not Chinese (高/中/低). Dataset uses Chinese labels. Mapping required.

---

## Step 1 — Reproduce the self-reported accuracy

Use the held-out test split (12,757 entries) — the same evaluation set CIRCL used.

```python
from datasets import load_dataset
from transformers import pipeline
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tqdm import tqdm

ds = load_dataset("CIRCL/Vulnerability-CNVD")
test_df = pd.DataFrame(ds["test"])

classifier = pipeline(
    "text-classification",
    model="CIRCL/vulnerability-severity-classification-chinese-macbert-base",
    device="mps",  # Use "cpu" if not on Apple Silicon
    batch_size=64,
)

# Run predictions on test set descriptions
descriptions = test_df["description"].tolist()
predictions = []

for i in tqdm(range(0, len(descriptions), 64)):
    batch = descriptions[i:i+64]
    results = classifier(batch, truncation=True, max_length=512)
    predictions.extend([r["label"] for r in results])

test_df["predicted"] = predictions
test_df["correct"] = test_df["severity"] == test_df["predicted"]

accuracy = accuracy_score(test_df["severity"], test_df["predicted"])
print(f"Reproduced accuracy: {accuracy:.4f}")
print(f"CIRCL reported:      0.7783")
print(f"Delta:               {accuracy - 0.7783:+.4f}")
```

**Expected:** Accuracy should be ~77.83% (+/-0.5% for framework version differences). A larger delta suggests a reproducibility issue.

> [!NOTE] Step 1 — Executed 2026-03-24
> - Reproduced accuracy: **78.29%** (CIRCL reported 77.83%, delta +0.46pp) — **confirmed within +/-0.5% threshold**
> - Inference: 12,757 predictions in 81.6s (156 predictions/sec on MPS)
> - Label mapping discovered: model outputs English (`High`/`Medium`/`Low`), dataset uses Chinese (高/中/低)
> - Majority baseline: 55.58% (always Medium) — model improvement: **+22.71pp**
> - Predictions saved to `v2_test_predictions.csv`

---

## Step 2 — Per-class precision, recall, F1

The self-reported accuracy (77.83%) hides per-class performance. With an imbalanced dataset (Medium 55%, High 36%, Low 9%), per-class metrics are critical.

```python
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Classification report
sev_map = {"高": "High", "中": "Medium", "低": "Low"}
y_true = test_df["severity"].map(sev_map)
y_pred = test_df["predicted"].map(sev_map)

print(classification_report(y_true, y_pred, digits=3))

# Confusion matrix
cm = confusion_matrix(y_true, y_pred, labels=["High", "Medium", "Low"])
fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["High", "Medium", "Low"],
            yticklabels=["High", "Medium", "Low"], ax=ax)
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")
ax.set_title("CNVD Severity Classifier — Confusion Matrix (Test Set)")
plt.tight_layout()
plt.savefig("v2_confusion_matrix.png", dpi=150)
print("Chart saved: v2_confusion_matrix.png")
```

**What to look for:**
- **Low class recall** — with only 9% of the dataset, the model may struggle to identify Low severity entries (predicts Medium instead)
- **High<->Medium confusion** — the most likely failure mode; if the model can't distinguish these reliably, its triage value is limited
- **Precision vs recall trade-offs** — for vulnerability triage, recall on High is more important than precision (missing a High is worse than a false alarm)

> [!NOTE] Step 2 — Executed 2026-03-24
>
> | Class | Precision | Recall | F1 | Support |
> |-------|-----------|--------|-----|---------|
> | High | 0.798 | 0.768 | 0.783 | 4,520 |
> | Medium | 0.785 | 0.855 | 0.819 | 7,090 |
> | **Low** | **0.660** | **0.398** | **0.497** | **1,147** |
>
> **Low recall is 39.8% — the model misclassifies 60% of Low entries (mostly as Medium).** 55.4% of Low entries predicted as Medium, 22.6% of High entries predicted as Medium. The model has a strong Medium bias.
> - Chart saved: `v2_confusion_matrix.png`

---

## Step 3 — Compare against baselines

### 3a — Majority class baseline

```python
# Always predict the majority class (Medium/中)
majority_accuracy = (test_df["severity"] == "中").mean()
print(f"Majority class baseline: {majority_accuracy:.4f}")
print(f"Model accuracy:          {accuracy:.4f}")
print(f"Improvement over random: {accuracy - majority_accuracy:+.4f}")
```

**Interpretation:** If the model only marginally beats the majority baseline (55%), the fine-tuning adds little value.

### 3b — Base model (no fine-tuning)

```python
# Load base model without fine-tuning for comparison
base_classifier = pipeline(
    "text-classification",
    model="hfl/chinese-macbert-base",
    device="mps",
    batch_size=64,
)

# Note: base model likely has different labels (not trained for this task)
# This step may require zero-shot classification instead
from transformers import pipeline as zs_pipeline

zero_shot = zs_pipeline(
    "zero-shot-classification",
    model="hfl/chinese-macbert-base",
    device="mps",
)

# Sample 200 entries (zero-shot is slow)
sample = test_df.sample(200, random_state=42)
zs_labels = ["高危漏洞", "中危漏洞", "低危漏洞"]  # High/Medium/Low vulnerability
label_map = {"高危漏洞": "高", "中危漏洞": "中", "低危漏洞": "低"}

zs_predictions = []
for desc in tqdm(sample["description"]):
    result = zero_shot(desc, candidate_labels=zs_labels, truncation=True)
    zs_predictions.append(label_map[result["labels"][0]])

sample["zs_predicted"] = zs_predictions
zs_accuracy = (sample["severity"] == sample["zs_predicted"]).mean()
print(f"Zero-shot baseline accuracy: {zs_accuracy:.4f}")
print(f"Fine-tuned accuracy:         {accuracy:.4f}")
print(f"Fine-tuning delta:           {accuracy - zs_accuracy:+.4f}")
```

> [!NOTE] Alternative baseline
> If zero-shot classification on MacBERT base doesn't work well (it's not designed for this), try a simple keyword-based heuristic: count severity-related Chinese words in the description (缓冲区溢出, 远程代码执行 → High; 信息泄露, 跨站脚本 → Medium; 拒绝服务 → Low). This tests whether the model learns anything beyond surface keywords.

> [!NOTE] Step 3 — Executed 2026-03-24 (partial)
> - **Step 3a (majority baseline):** 55.58% accuracy. Model improvement: +22.71pp — **substantial value over naive prediction.**
> - **Step 3b (zero-shot baseline):** Deprioritised — majority baseline already demonstrates fine-tuning adds meaningful value. V3 adversarial tests later proved the model is a keyword classifier, making a keyword heuristic baseline the more informative comparison (see [V3 Findings Report](../findings/V3-Bias-Detection-Findings.md)).

---

## Step 4 — Temporal stability

Does the model perform equally well across years, or is it degrading on newer entries?

```python
test_df["year"] = test_df["id"].str.extract(r"CNVD-(\d{4})-", expand=False).astype(float)

print(f"{'Year':>6s}  {'n':>5s}  {'Accuracy':>9s}")
for year in sorted(test_df["year"].unique()):
    yr = test_df[test_df["year"] == year]
    if len(yr) >= 10:
        yr_acc = (yr["severity"] == yr["predicted"]).mean()
        print(f"  {year:.0f}  {len(yr):5d}  {yr_acc:8.3f}")
```

**What to look for:**
- Accuracy dropping on post-2022 entries → the severity distribution shift (High jumping to 50%) may not be well-represented in training data
- Accuracy lower on 2019–2021 entries → the CNVD-only entries (Chinese domestic) may be harder to classify

> [!NOTE] Step 4 — Executed 2026-03-24
> - Accuracy range: 0.741–0.823 (spread: 8.2pp) — **acceptable but not stable**
> - High and Medium recall are stable across years (~0.73–0.87)
> - **Low recall collapses post-2024:** drops from ~35–50% to 18–25%
> - 2020 is the worst year (74.1% accuracy) — coincides with V1's peak of CNVD-only entries
> - Chart saved: `v2_temporal_stability.png`

---

## Step 5 — Confidence calibration

Is the model's confidence score meaningful, or does it predict everything with high confidence?

```python
# Get confidence scores
all_results = []
for i in tqdm(range(0, len(descriptions), 64)):
    batch = descriptions[i:i+64]
    results = classifier(batch, truncation=True, max_length=512)
    all_results.extend(results)

test_df["confidence"] = [r["score"] for r in all_results]

# Calibration: bin by confidence, check actual accuracy per bin
bins = [0, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.0]
test_df["conf_bin"] = pd.cut(test_df["confidence"], bins=bins)

cal = test_df.groupby("conf_bin").agg(
    count=("correct", "count"),
    accuracy=("correct", "mean"),
    mean_conf=("confidence", "mean"),
).reset_index()

print("Calibration table:")
print(cal.to_string(index=False))

# Plot calibration curve
fig, ax = plt.subplots(figsize=(8, 6))
ax.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
ax.scatter(cal["mean_conf"], cal["accuracy"], s=cal["count"]/10, alpha=0.7)
for _, row in cal.iterrows():
    ax.annotate(f'n={row["count"]:.0f}', (row["mean_conf"], row["accuracy"]),
                fontsize=8, ha="center", va="bottom")
ax.set_xlabel("Mean predicted confidence")
ax.set_ylabel("Actual accuracy")
ax.set_title("CNVD Severity Classifier — Confidence Calibration")
ax.legend()
plt.tight_layout()
plt.savefig("v2_calibration.png", dpi=150)
print("Chart saved: v2_calibration.png")
```

**What to look for:**
- **Overconfident model** — predicts 0.95+ confidence but actual accuracy is 0.75 → confidence scores are not trustworthy for downstream filtering
- **Well-calibrated** — confidence roughly matches accuracy → can use confidence thresholds to filter uncertain predictions
- **Bimodal distribution** — most predictions are either very high or very low confidence → the model is decisive but may be wrong on borderline cases

> [!NOTE] Step 5 — Executed 2026-03-24
> - **ECE (Expected Calibration Error): 0.0533** — just above the "good" threshold (0.05), rated **acceptable**
> - Model is **consistently overconfident** — every bin above 0.5 shows confidence > accuracy
> - Worst overconfidence at 0.7–0.9 range (7–9pp gap)
> - Well-calibrated at extremes: low confidence (0.4–0.6) and very high (0.95+)
> - **Confidence is directionally useful:** 0.9 threshold → 91.6% accuracy on 46% of predictions
> - Correct predictions: mean confidence 0.864 | Incorrect: 0.736
> - Chart saved: `v2_calibration.png`

---

## Step 6 — Overfitting analysis

The training log shows validation loss *increasing* from epoch 3 (1.0848 → 1.1507 → 1.2224) while training loss continues to drop. This is a classic overfitting signal.

```python
# Training loss progression (from model card)
epochs = [1, 2, 3, 4, 5]
train_loss = [1.2400, 1.1318, 1.0106, 0.6185, 0.6463]
val_loss = [1.1658, 1.1025, 1.0848, 1.1507, 1.2224]
val_accuracy = [0.7567, 0.7711, 0.7829, 0.7807, 0.7783]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

ax1.plot(epochs, train_loss, "b-o", label="Train loss")
ax1.plot(epochs, val_loss, "r-o", label="Validation loss")
ax1.axvline(x=3, color="green", linestyle="--", alpha=0.5, label="Best epoch (3)")
ax1.set_xlabel("Epoch")
ax1.set_ylabel("Loss")
ax1.set_title("Training vs Validation Loss")
ax1.legend()

ax2.plot(epochs, val_accuracy, "g-o", label="Validation accuracy")
ax2.axvline(x=3, color="green", linestyle="--", alpha=0.5, label="Best epoch (3)")
ax2.set_xlabel("Epoch")
ax2.set_ylabel("Accuracy")
ax2.set_title("Validation Accuracy by Epoch")
ax2.legend()

plt.tight_layout()
plt.savefig("v2_overfitting.png", dpi=150)
print("Chart saved: v2_overfitting.png")
print(f"\nBest epoch by val loss: 3 (accuracy: 0.7829)")
print(f"Published epoch: 5 (accuracy: 0.7783)")
print(f"Overfit penalty: {0.7829 - 0.7783:+.4f} accuracy lost")
```

**Key finding:** The published model (epoch 5) is slightly worse than epoch 3. The overfitting penalty is small (~0.5% accuracy) but indicates the training could have been stopped earlier. This is a minor concern — the model is not severely overfit, but it's not optimally trained either.

> [!NOTE] Step 6 — Executed 2026-03-24
> - Best epoch by val loss: **3** (val loss 1.0848, accuracy 78.29%)
> - Published epoch: **5** (val loss 1.2224, accuracy 77.83%)
> - Overfit penalty: **0.46pp** accuracy lost, +0.1376 validation loss divergence
> - **Assessment:** Mild overfitting. Suboptimal checkpoint published, but impact is small.
> - Chart saved: `v2_overfitting.png`

---

## Step 7 — Generate report

Compile all V2 findings into [V2 Findings Report](../findings/V2-Model-Quality-Findings.md) following the same structure as [V1 Findings Report](../findings/V1-NVD-Overlap-Findings.md).

**Sections:**
1. Executive finding
2. Reproduced accuracy vs CIRCL-reported
3. Per-class performance (precision/recall/F1 + confusion matrix)
4. Baseline comparison (majority class, zero-shot)
5. Temporal stability
6. Confidence calibration
7. Overfitting analysis
8. Verdict: is the model useful for operational triage?

---

## Interpretation Thresholds

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Accuracy vs CIRCL-reported | +/-0.5% | +/-2% | >2% delta |
| High recall | >0.80 | 0.65–0.80 | <0.65 |
| Fine-tuning delta vs baseline | >15pp | 5–15pp | <5pp |
| Temporal stability (max-min accuracy) | <5pp | 5–10pp | >10pp |
| Calibration (ECE) | <0.05 | 0.05–0.15 | >0.15 |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Prerequisites — install transformers/torch | 5 min | pip install |
| Step 1 — Reproduce accuracy | 5–10 min | 12,757 predictions, ~2 min on MPS |
| Step 2 — Per-class metrics | 5 min | sklearn classification_report |
| Step 3a — Majority baseline | 1 min | Trivial calculation |
| Step 3b — Zero-shot baseline | 30–60 min | Slow (200 samples) |
| Step 4 — Temporal stability | 5 min | Groupby + accuracy |
| Step 5 — Confidence calibration | 10 min | Already have predictions |
| Step 6 — Overfitting analysis | 5 min | Plot from model card data |
| Step 7 — Report | 15 min | Compile findings |
| **Total** | **1–2 hours** | Step 3b is the bottleneck |

---

## Next Steps After V2

- If per-class performance is poor for Low → the model is unreliable for the rarest class
- If temporal degradation is observed → the model needs periodic retraining
- If confidence is poorly calibrated → confidence scores should not be used for filtering in Vulnerability-Lookup
- If fine-tuning delta is small (<5pp) → the model adds little value over a keyword heuristic
- Regardless of outcome → update the CNVD Dataset Hugging Face Brief with V2 findings
- If V2 raises concerns → proceed to [V3 Systematic Bias Detection](V3-Systematic-Bias-Detection.md)
