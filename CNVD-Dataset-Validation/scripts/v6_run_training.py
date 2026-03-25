#!/usr/bin/env python3
"""
V6 — Reproducibility: Fine-tune MacBERT severity classifier.

Run overnight:
    source cnvd-validation/bin/activate
    python3 v6_run_training.py

Estimated: ~8.5 hours on Apple Silicon MPS (17,940 steps at ~1.7s/step)
"""

import os
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"

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
import time
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, accuracy_score
import pandas as pd

OUTDIR = os.path.dirname(os.path.abspath(__file__))
TRAIN_OUTDIR = os.path.join(OUTDIR, "v6_training")

print(f"MPS available: {torch.backends.mps.is_available()}")
print(f"Output: {OUTDIR}")

# =============================================
# STEP 1 — Fine-tune
# =============================================
label2id = {"高": 0, "中": 1, "低": 2}
id2label = {v: k for k, v in label2id.items()}
label_to_cn = {"High": "高", "Medium": "中", "Low": "低"}
cn_to_en = {"高": "High", "中": "Medium", "低": "Low"}

print("Loading dataset...")
ds = load_dataset("CIRCL/Vulnerability-CNVD")

print("Loading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained("hfl/chinese-macbert-base")

def tokenize(examples):
    return tokenizer(examples["description"], padding="max_length", truncation=True, max_length=512)

def encode_labels(examples):
    examples["label"] = [label2id[s] for s in examples["severity"]]
    return examples

print("Preprocessing...")
ds_processed = ds.map(encode_labels, batched=True)
ds_processed = ds_processed.map(tokenize, batched=True)

# Keep a copy of test descriptions before removing columns
test_descriptions = ds["test"]["description"]
test_severities = ds["test"]["severity"]
test_ids = ds["test"]["id"]

ds_processed = ds_processed.remove_columns(["id", "title", "description", "severity"])
ds_processed.set_format("torch")

print("Loading base model...")
model = AutoModelForSequenceClassification.from_pretrained(
    "hfl/chinese-macbert-base",
    num_labels=3,
    id2label=id2label,
    label2id=label2id,
)

accuracy_metric = evaluate.load("accuracy")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    predictions = np.argmax(logits, axis=-1)
    return accuracy_metric.compute(predictions=predictions, references=labels)

training_args = TrainingArguments(
    output_dir=TRAIN_OUTDIR,
    eval_strategy="epoch",
    save_strategy="epoch",
    learning_rate=3e-5,
    per_device_train_batch_size=32,
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    weight_decay=0.0,
    seed=42,
    lr_scheduler_type="linear",
    warmup_steps=0,
    logging_steps=50,
    load_best_model_at_end=False,
    report_to="none",
    fp16=False,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=ds_processed["train"],
    eval_dataset=ds_processed["test"],
    compute_metrics=compute_metrics,
)

print("Starting training...")
start_time = time.time()
trainer.train()
elapsed = time.time() - start_time
print(f"\nTraining completed in {elapsed/60:.1f} minutes ({elapsed/3600:.1f} hours)")

# Save training log
with open(os.path.join(OUTDIR, "v6_training_log.json"), "w") as f:
    json.dump(trainer.state.log_history, f, indent=2)

# =============================================
# STEP 2 — Training dynamics comparison
# =============================================
print(f"\n=== STEP 2 — TRAINING DYNAMICS ===\n")

circl_epochs = [1, 2, 3, 4, 5]
circl_train_loss = [1.2400, 1.1318, 1.0106, 0.6185, 0.6463]
circl_val_loss = [1.1658, 1.1025, 1.0848, 1.1507, 1.2224]
circl_val_acc = [0.7567, 0.7711, 0.7829, 0.7807, 0.7783]

our_val_loss = []
our_val_acc = []
our_train_loss_raw = []

for log in trainer.state.log_history:
    if "eval_loss" in log:
        our_val_loss.append(log["eval_loss"])
        our_val_acc.append(log["eval_accuracy"])
    if "loss" in log and "eval_loss" not in log:
        our_train_loss_raw.append(log["loss"])

steps_per_epoch = len(ds_processed["train"]) // 32
logs_per_epoch = max(1, steps_per_epoch // 50)
our_train_loss = []
for e in range(5):
    start = e * logs_per_epoch
    end = min(start + logs_per_epoch, len(our_train_loss_raw))
    if start < len(our_train_loss_raw):
        our_train_loss.append(np.mean(our_train_loss_raw[start:end]))

print(f"{'Epoch':>5s}  {'CIRCL val_loss':>14s}  {'Ours val_loss':>13s}  {'CIRCL acc':>9s}  {'Ours acc':>8s}  {'Delta':>6s}")
print("-" * 65)
for i in range(min(5, len(our_val_loss))):
    delta = our_val_acc[i] - circl_val_acc[i]
    print(f"  {i+1:3d}  {circl_val_loss[i]:13.4f}  {our_val_loss[i]:12.4f}  {circl_val_acc[i]:8.4f}  {our_val_acc[i]:7.4f}  {delta:+5.4f}")

# Chart
fig, axes = plt.subplots(1, 3, figsize=(18, 5))
axes[0].plot(circl_epochs, circl_val_loss, "r-o", label="CIRCL published", linewidth=2)
axes[0].plot(circl_epochs[:len(our_val_loss)], our_val_loss, "b-s", label="Our reproduction", linewidth=2)
axes[0].set_xlabel("Epoch"); axes[0].set_ylabel("Validation Loss"); axes[0].set_title("Validation loss"); axes[0].legend()
axes[1].plot(circl_epochs, circl_val_acc, "r-o", label="CIRCL published", linewidth=2)
axes[1].plot(circl_epochs[:len(our_val_acc)], our_val_acc, "b-s", label="Our reproduction", linewidth=2)
axes[1].set_xlabel("Epoch"); axes[1].set_ylabel("Validation Accuracy"); axes[1].set_title("Validation accuracy"); axes[1].legend()
if our_train_loss:
    axes[2].plot(circl_epochs, circl_train_loss, "r-o", label="CIRCL published", linewidth=2)
    axes[2].plot(circl_epochs[:len(our_train_loss)], our_train_loss, "b-s", label="Our reproduction", linewidth=2)
    axes[2].set_xlabel("Epoch"); axes[2].set_ylabel("Training Loss"); axes[2].set_title("Training loss"); axes[2].legend()
plt.suptitle("V6 — Training dynamics: CIRCL vs reproduction", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(OUTDIR, "v6_reproducibility_comparison.png"), dpi=150)
print("Chart saved: v6_reproducibility_comparison.png")

# =============================================
# STEP 3 — Prediction comparison
# =============================================
print(f"\n=== STEP 3 — PREDICTION COMPARISON ===\n")

from transformers import pipeline as hf_pipeline

# Our reproduced model (last checkpoint = epoch 5)
last_checkpoint = sorted([
    d for d in os.listdir(TRAIN_OUTDIR)
    if d.startswith("checkpoint-")
])[-1]
our_model_path = os.path.join(TRAIN_OUTDIR, last_checkpoint)
print(f"Our model checkpoint: {our_model_path}")

our_classifier = hf_pipeline(
    "text-classification",
    model=our_model_path,
    device="mps",
    batch_size=64,
)

circl_classifier = hf_pipeline(
    "text-classification",
    model="CIRCL/vulnerability-severity-classification-chinese-macbert-base",
    device="mps",
    batch_size=64,
)

our_preds = []
circl_preds = []

for i in range(0, len(test_descriptions), 64):
    batch = test_descriptions[i:i+64]
    our_results = our_classifier(batch, truncation=True, max_length=512)
    circl_results = circl_classifier(batch, truncation=True, max_length=512)
    for r in our_results:
        pred_cn = label_to_cn.get(r["label"], r["label"])
        our_preds.append(pred_cn)
    for r in circl_results:
        pred_cn = label_to_cn.get(r["label"], r["label"])
        circl_preds.append(pred_cn)

agreement = sum(1 for a, b in zip(our_preds, circl_preds) if a == b) / len(our_preds)
print(f"Prediction agreement: {agreement:.4f} ({agreement*100:.1f}%)")

disagreements = sum(1 for a, b in zip(our_preds, circl_preds) if a != b)
print(f"Disagreements: {disagreements} / {len(our_preds)}")

our_acc = accuracy_score(test_severities, our_preds)
circl_acc = accuracy_score(test_severities, circl_preds)
print(f"Our accuracy:    {our_acc:.4f}")
print(f"CIRCL accuracy:  {circl_acc:.4f}")
print(f"Delta:           {our_acc - circl_acc:+.4f}")

# =============================================
# STEP 4 — Adversarial comparison
# =============================================
print(f"\n=== STEP 4 — ADVERSARIAL COMPARISON ===\n")

adversarial_tests = [
    ("远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "RCE + RCE impact"),
    ("跨站脚本漏洞，攻击者可利用该漏洞执行任意代码。", "XSS keyword + RCE impact"),
    ("存在远程代码执行漏洞，攻击者可利用该漏洞执行任意代码。", "Positive: has RCE"),
    ("不存在远程代码执行漏洞。", "Negated: no RCE"),
    ("代码执行漏洞", "Minimal: code execution"),
    ("信息泄露", "Minimal: info disclosure"),
]

print(f"{'Description':45s}  {'Ours':>8s}  {'CIRCL':>8s}  {'Match':>5s}  {'Note'}")
print("-" * 95)

for desc, note in adversarial_tests:
    our_r = our_classifier(desc, truncation=True, max_length=512)[0]
    circl_r = circl_classifier(desc, truncation=True, max_length=512)[0]
    our_label = label_to_cn.get(our_r["label"], our_r["label"])
    circl_label = label_to_cn.get(circl_r["label"], circl_r["label"])
    match = "Y" if our_label == circl_label else "N"
    print(f"{desc[:43]:45s}  {cn_to_en.get(our_label, our_label):>8s}  {cn_to_en.get(circl_label, circl_label):>8s}  {match:>5s}  {note}")

# Save results
results = {
    "training_time_minutes": elapsed / 60,
    "our_val_loss": our_val_loss,
    "our_val_acc": our_val_acc,
    "circl_val_loss": circl_val_loss,
    "circl_val_acc": circl_val_acc,
    "prediction_agreement": agreement,
    "our_accuracy": our_acc,
    "circl_accuracy": circl_acc,
}
with open(os.path.join(OUTDIR, "v6_results.json"), "w") as f:
    json.dump(results, f, indent=2)

print(f"\n=== V6 COMPLETE ===")
print(f"Results saved to: v6_results.json")
print(f"Training log saved to: v6_training_log.json")
print(f"Chart saved to: v6_reproducibility_comparison.png")
print(f"Checkpoints in: {TRAIN_OUTDIR}/")
