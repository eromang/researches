# V6 — Reproducibility

**Objective:** Independently reproduce the fine-tuning of the MacBERT severity classifier and compare the resulting model against CIRCL's published weights. Determine whether the published model matches what the public dataset and training parameters would produce.

---

## Context from V1–V5

| Track | Finding | Relevance to V6 |
|-------|---------|-----------------|
| V2 | Published model is epoch 5; epoch 3 was optimal | Reproduce and compare: does our epoch 3 match CIRCL's epoch 3 accuracy (78.29%)? |
| V2 | Overfitting: val loss diverges after epoch 3 | Confirm training dynamics are reproducible |
| V3 | Model is a keyword classifier | Reproduction should exhibit the same keyword dependency — if it doesn't, published model may have additional training data |
| V5 | Model is a UI widget, not production | Low operational stakes — this is primarily a scientific reproducibility check |

**Priority:** This is the lowest-priority track. V1–V5 provide a comprehensive picture. V6 is warranted only if:
- You suspect the published weights were trained on additional (non-public) data
- You want to verify that the training parameters (model card) are truthful
- You plan to retrain a better model (e.g., with class weighting to fix Low recall)

---

## Prerequisites

### Hardware requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU/MPS | Apple Silicon MPS | NVIDIA GPU (CUDA) or MPS |
| RAM | 16 GB | 32 GB |
| Disk | 2 GB (model + dataset) | 5 GB (with checkpoints) |
| Time | ~30 min on MPS | ~10 min on CUDA GPU |

### Additional packages

```bash
source cnvd-validation/bin/activate
pip install accelerate evaluate
```

### Training parameters (from CIRCL model card)

| Parameter | Value |
|-----------|-------|
| Base model | `hfl/chinese-macbert-base` |
| Dataset | `CIRCL/Vulnerability-CNVD` |
| Epochs | 5 |
| Learning rate | 3e-05 |
| Batch size (train) | 32 |
| Batch size (eval) | 32 |
| Optimizer | AdamW (fused), betas=(0.9, 0.999) |
| LR scheduler | Linear |
| Seed | 42 |
| Max length | 512 (assumed — not documented, standard for BERT) |

---

## Step 1 — Reproduce the fine-tuning

```python
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
import numpy as np
import evaluate
import torch

# Label mapping
label2id = {"高": 0, "中": 1, "低": 2}
id2label = {v: k for k, v in label2id.items()}

# Load dataset
ds = load_dataset("CIRCL/Vulnerability-CNVD")

# Tokenizer
tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-macbert-base")

def tokenize(examples):
    return tokenizer(
        examples["description"],
        padding="max_length",
        truncation=True,
        max_length=512,
    )

def encode_labels(examples):
    examples["label"] = [label2id[s] for s in examples["severity"]]
    return examples

ds = ds.map(encode_labels, batched=True)
ds = ds.map(tokenize, batched=True)
ds = ds.remove_columns(["id", "title", "description", "severity"])
ds.set_format("torch")

# Model
model = AutoModelForSequenceClassification.from_pretrained(
    "hfl/chinese-macbert-base",
    num_labels=3,
    id2label=id2label,
    label2id=label2id,
)

# Metrics
accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return accuracy_metric.compute(predictions=predictions, references=labels)

# Training arguments (matching CIRCL's model card)
training_args = TrainingArguments(
    output_dir="./v6_training",
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=3e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    weight_decay=0.0,  # Not specified in model card — default
    seed=42,
    lr_scheduler_type="linear",
    warmup_steps=0,  # Not specified — default
    logging_steps=100,
    load_best_model_at_end=False,  # CIRCL published epoch 5, not best
    use_mps_device=torch.backends.mps.is_available(),
)

# Trainer
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=ds["train"],
    eval_dataset=ds["test"],
    compute_metrics=compute_metrics,
)

# Train
trainer.train()

# Print per-epoch results
for log in trainer.state.log_history:
    if "eval_accuracy" in log:
        print(f"Epoch {log.get('epoch', '?')}: "
              f"eval_loss={log.get('eval_loss', '?'):.4f}, "
              f"eval_accuracy={log.get('eval_accuracy', '?'):.4f}")
```

---

## Step 2 — Compare training dynamics

```python
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# CIRCL's reported values
circl_epochs = [1, 2, 3, 4, 5]
circl_train_loss = [1.2400, 1.1318, 1.0106, 0.6185, 0.6463]
circl_val_loss = [1.1658, 1.1025, 1.0848, 1.1507, 1.2224]
circl_val_acc = [0.7567, 0.7711, 0.7829, 0.7807, 0.7783]

# Extract our values from trainer logs
our_val_loss = []
our_val_acc = []
our_train_loss = []
for log in trainer.state.log_history:
    if "eval_loss" in log:
        our_val_loss.append(log["eval_loss"])
        our_val_acc.append(log["eval_accuracy"])
    if "loss" in log and "eval_loss" not in log:
        our_train_loss.append(log["loss"])

# Average train loss per epoch (multiple logging steps per epoch)
steps_per_epoch = len(ds["train"]) // 32
logs_per_epoch = steps_per_epoch // 100  # logging_steps=100
our_epoch_train_loss = []
for e in range(5):
    start = e * logs_per_epoch
    end = start + logs_per_epoch
    if end <= len(our_train_loss):
        our_epoch_train_loss.append(np.mean(our_train_loss[start:end]))

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Val loss comparison
axes[0].plot(circl_epochs, circl_val_loss, "r-o", label="CIRCL published")
axes[0].plot(circl_epochs[:len(our_val_loss)], our_val_loss, "b-s", label="Our reproduction")
axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("Validation Loss")
axes[0].set_title("Validation Loss Comparison")
axes[0].legend()

# Val accuracy comparison
axes[1].plot(circl_epochs, circl_val_acc, "r-o", label="CIRCL published")
axes[1].plot(circl_epochs[:len(our_val_acc)], our_val_acc, "b-s", label="Our reproduction")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Validation Accuracy")
axes[1].set_title("Validation Accuracy Comparison")
axes[1].legend()

# Train loss comparison
if our_epoch_train_loss:
    axes[2].plot(circl_epochs, circl_train_loss, "r-o", label="CIRCL published")
    axes[2].plot(circl_epochs[:len(our_epoch_train_loss)], our_epoch_train_loss, "b-s", label="Our reproduction")
axes[2].set_xlabel("Epoch")
axes[2].set_ylabel("Training Loss")
axes[2].set_title("Training Loss Comparison")
axes[2].legend()

plt.suptitle("V6 — Training Dynamics Reproducibility", fontsize=14)
plt.tight_layout()
plt.savefig("v6_reproducibility_comparison.png", dpi=150)
print("Chart saved: v6_reproducibility_comparison.png")
```

---

## Step 3 — Compare model predictions

Compare predictions on the same test set between our reproduced model and CIRCL's published model.

```python
from transformers import pipeline as hf_pipeline
from sklearn.metrics import classification_report
import pandas as pd

# Load our reproduced model (epoch 5 checkpoint)
our_classifier = hf_pipeline(
    "text-classification",
    model="./v6_training/checkpoint-epoch-5",  # Adjust path
    device="mps",
    batch_size=64,
)

# Load CIRCL's published model
circl_classifier = hf_pipeline(
    "text-classification",
    model="CIRCL/vulnerability-severity-classification-chinese-macbert-base",
    device="mps",
    batch_size=64,
)

# Predict on test set
test_df = pd.DataFrame(load_dataset("CIRCL/Vulnerability-CNVD")["test"])
descriptions = test_df["description"].tolist()

our_preds = []
circl_preds = []

for i in range(0, len(descriptions), 64):
    batch = descriptions[i:i+64]
    our_results = our_classifier(batch, truncation=True, max_length=512)
    circl_results = circl_classifier(batch, truncation=True, max_length=512)
    our_preds.extend([r["label"] for r in our_results])
    circl_preds.extend([r["label"] for r in circl_results])

# Agreement rate
agreement = sum(1 for a, b in zip(our_preds, circl_preds) if a == b) / len(our_preds)
print(f"Prediction agreement: {agreement:.4f} ({agreement*100:.1f}%)")

# Where they disagree
disagreements = [(i, our_preds[i], circl_preds[i])
                 for i in range(len(our_preds)) if our_preds[i] != circl_preds[i]]
print(f"Disagreements: {len(disagreements)} / {len(our_preds)}")
```

---

## Step 4 — Adversarial comparison

Run the V3 adversarial tests on the reproduced model and compare.

```python
adversarial_tests = [
    ("远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "RCE + RCE impact"),
    ("跨站脚本漏洞，攻击者可利用该漏洞执行任意代码。", "XSS keyword + RCE impact"),
    ("存在远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "Positive: has RCE"),
    ("不存在远程代码执行漏洞。", "Negated: no RCE"),
    ("代码执行漏洞", "Minimal: code execution"),
    ("信息泄露", "Minimal: info disclosure"),
]

print(f"{'Description':45s}  {'Ours':>8s}  {'CIRCL':>8s}  {'Match':>5s}")
print("-" * 80)

for desc, note in adversarial_tests:
    our_r = our_classifier(desc, truncation=True, max_length=512)[0]
    circl_r = circl_classifier(desc, truncation=True, max_length=512)[0]
    match = "Y" if our_r["label"] == circl_r["label"] else "N"
    print(f"{desc[:43]:45s}  {our_r['label']:>8s}  {circl_r['label']:>8s}  {match:>5s}  {note}")
```

**What to look for:**
- If both models show identical keyword dependency and negation blindness → the behaviour is inherent to the architecture + data, not an artifact of specific weights
- If our model is LESS keyword-dependent → CIRCL may have used different hyperparameters or additional data
- If our model is MORE keyword-dependent → random seed variation, our training may have converged to a worse local minimum

---

## Step 5 — Generate report

Compile findings into [V6 Findings Report](../findings/V6-Reproducibility-Findings.md):

1. Training dynamics comparison (CIRCL vs reproduced: val loss, val accuracy per epoch)
2. Final accuracy comparison (epoch 5 vs epoch 5, epoch 3 vs epoch 3)
3. Prediction agreement rate on test set
4. Adversarial behaviour comparison
5. Verdict: is the published model reproducible?

---

## Interpretation Thresholds

| Metric | Reproducible | Questionable | Divergent |
|--------|-------------|-------------|-----------|
| Epoch accuracy delta | <0.5pp | 0.5–2pp | >2pp |
| Training dynamics shape | Same curve shape | Minor deviations | Different shape |
| Prediction agreement | >97% | 92–97% | <92% |
| Adversarial agreement | All match | 1–2 differ | >2 differ |

---

## Estimated Effort

| Step | Time | Notes |
|------|------|-------|
| Prerequisites — install accelerate/evaluate | 5 min | pip install |
| Step 1 — Fine-tuning | 30–60 min | 5 epochs on MPS; faster with CUDA |
| Step 2 — Training dynamics comparison | 10 min | Plotting |
| Step 3 — Prediction comparison | 10 min | ~2 min inference per model |
| Step 4 — Adversarial comparison | 5 min | 6 individual predictions |
| Step 5 — Report | 15 min | Compile findings |
| **Total** | **1–2 hours** | Step 1 dominates; GPU dependent |

---

## Next Steps After V6

- If reproducible → confirms CIRCL's model card is truthful; the keyword classifier behaviour is inherent to the data + architecture
- If divergent → the published model may have been trained on additional data, with different hyperparameters, or from a different base model checkpoint
- If our epoch 3 outperforms epoch 5 → confirms V2's overfitting finding; suggests CIRCL should publish the epoch 3 checkpoint
- Optional: retrain with class-weighted loss to fix Low recall (requires separate experiment)
