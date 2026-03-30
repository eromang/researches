"""Train CyberScale Phase 3 T-model (technical severity classifier, ModernBERT 4-class).

Usage:
    cd CyberScale
    poetry run python training/scripts/train_technical.py \
        --data training/data/technical_training.csv \
        --config training/configs/technical_cls.json \
        --output data/models/technical
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from functools import partial
from pathlib import Path

# Force unbuffered output so background runs show progress
print = partial(print, flush=True)

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from torch.optim import AdamW
from torch.optim.lr_scheduler import LinearLR
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# ---------------------------------------------------------------------------
# Allow importing from src/ when running from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# ---------------------------------------------------------------------------
# Label names
# ---------------------------------------------------------------------------
LABEL_NAMES = ["T1", "T2", "T3", "T4"]


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class CVEDataset(Dataset):
    """Tokenised CVE technical inputs with integer class labels."""

    def __init__(
        self,
        texts: list[str],
        labels: list[int],
        tokenizer: AutoTokenizer,
        max_length: int = 256,
        weights: list[float] | None = None,
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.weights = weights or [1.0] * len(texts)

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict:
        encoding = self.tokenizer(
            self.texts[idx],
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long),
            "weight": torch.tensor(self.weights[idx], dtype=torch.float32),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def detect_device() -> torch.device:
    """Auto-detect best available device: MPS > CUDA > CPU."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def train(
    config: dict,
    data_path: Path,
    output_dir: Path,
    resume: bool = False,
) -> dict:
    """Run full training pipeline and return test metrics.

    Args:
        resume: If True, load model from output_dir (warm start) instead
                of base_model. Restores optimizer/scheduler state if available.
    """
    model_cfg = config["model"]
    eval_cfg = config["evaluation"]

    # Seed
    seed = model_cfg.get("seed", 42)
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = detect_device()
    print(f"Device: {device}")

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = pd.read_csv(data_path)

    # Support both column naming conventions: "input_text" or "text"
    if "input_text" not in df.columns and "text" in df.columns:
        df = df.rename(columns={"text": "input_text"})

    required_cols = {"input_text", "label"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    # Drop rows with missing input_text or label
    df = df.dropna(subset=["input_text", "label"]).reset_index(drop=True)

    texts = df["input_text"].tolist()

    # Support string labels (T1-T4) via label_map, or integer labels
    label_map = model_cfg.get("label_map", None)
    if label_map and not df["label"].dtype.kind == "i":
        labels = df["label"].map(label_map).astype(int).tolist()
    else:
        labels = df["label"].astype(int).tolist()

    # Per-sample weights (optional column)
    if "weight" in df.columns:
        weights = df["weight"].astype(float).tolist()
        print(f"Per-sample weights detected: min={min(weights):.2f}, max={max(weights):.2f}")
    else:
        weights = [1.0] * len(texts)

    # ------------------------------------------------------------------
    # Train / val / test split (stratified by label)
    # ------------------------------------------------------------------
    test_size = eval_cfg.get("test_split", 0.15)
    val_size = eval_cfg.get("val_split", 0.15)

    indices = list(range(len(texts)))

    # First split: train+val vs test
    train_val_idx, test_idx = train_test_split(
        indices, test_size=test_size, random_state=seed, stratify=labels
    )

    # Second split: train vs val (val_size relative to full dataset)
    train_val_labels = [labels[i] for i in train_val_idx]
    relative_val = val_size / (1.0 - test_size)
    train_idx, val_idx = train_test_split(
        train_val_idx, test_size=relative_val, random_state=seed, stratify=train_val_labels
    )

    print(f"Split: train={len(train_idx)}, val={len(val_idx)}, test={len(test_idx)}")

    # ------------------------------------------------------------------
    # Tokenizer and datasets
    # ------------------------------------------------------------------
    base_model = model_cfg["base_model"]
    max_length = model_cfg.get("max_length", 256)
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    def make_dataset(idxs: list[int]) -> CVEDataset:
        return CVEDataset(
            texts=[texts[i] for i in idxs],
            labels=[labels[i] for i in idxs],
            tokenizer=tokenizer,
            max_length=max_length,
            weights=[weights[i] for i in idxs],
        )

    train_ds = make_dataset(train_idx)
    val_ds = make_dataset(val_idx)
    test_ds = make_dataset(test_idx)

    batch_size = model_cfg.get("batch_size", 16)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    # ------------------------------------------------------------------
    # Class weights (inverse frequency for imbalanced datasets)
    # ------------------------------------------------------------------
    num_labels = model_cfg.get("num_labels", 4)
    use_class_weights = model_cfg.get("class_weights", True)

    train_labels = [labels[i] for i in train_idx]
    counts = Counter(train_labels)
    total = len(train_labels)

    if use_class_weights:
        weight_list = [total / (num_labels * counts[i]) if counts[i] > 0 else 1.0 for i in range(num_labels)]
        weight_tensor = torch.tensor(weight_list, dtype=torch.float32).to(device)
        print(f"Class weights: {dict(zip(LABEL_NAMES, [f'{w:.2f}' for w in weight_list]))}")
    else:
        weight_tensor = None

    label_smoothing = model_cfg.get("label_smoothing", 0.1)
    loss_fn = torch.nn.CrossEntropyLoss(weight=weight_tensor, label_smoothing=label_smoothing, reduction="none")
    print(f"Label smoothing: {label_smoothing}")

    # ------------------------------------------------------------------
    # Model (with dropout for MC dropout at inference)
    # ------------------------------------------------------------------
    dropout_rate = model_cfg.get("dropout", 0.1)
    load_from = str(output_dir) if resume else base_model
    if resume:
        print(f"Resuming from checkpoint: {output_dir}")
    model = AutoModelForSequenceClassification.from_pretrained(
        load_from,
        num_labels=num_labels,
        problem_type="single_label_classification",
        classifier_dropout=dropout_rate,
    )
    model.to(device)

    # ------------------------------------------------------------------
    # Optimiser, scheduler
    # ------------------------------------------------------------------
    lr = model_cfg.get("learning_rate", 2e-5)
    weight_decay = model_cfg.get("weight_decay", 0.01)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    epochs = model_cfg.get("epochs", 20)
    warmup_ratio = model_cfg.get("warmup_ratio", 0.1)
    total_steps = len(train_loader) * epochs
    warmup_steps = max(1, int(total_steps * warmup_ratio))
    scheduler = LinearLR(optimizer, start_factor=0.1, total_iters=warmup_steps)

    grad_clip = model_cfg.get("gradient_clip", 1.0)
    patience = model_cfg.get("patience", 5)

    # Restore optimizer/scheduler state if resuming
    start_epoch = 0
    if resume:
        state_path = output_dir / "training_state.pt"
        if state_path.exists():
            state = torch.load(str(state_path), map_location=device, weights_only=True)
            optimizer.load_state_dict(state["optimizer"])
            scheduler.load_state_dict(state["scheduler"])
            start_epoch = state.get("epoch", 0)
            print(f"Restored training state from epoch {start_epoch}")

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    best_val_acc = 0.0
    patience_counter = 0
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(start_epoch + 1, epochs + 1):
        # --- Train ---
        model.train()
        train_loss_sum = 0.0
        train_correct = 0
        train_total = 0
        train_steps = 0

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"].to(device)

            optimizer.zero_grad()
            outputs = model(input_ids=input_ids, attention_mask=attention_mask)
            raw_loss = loss_fn(outputs.logits, batch_labels)
            sample_weights = batch["weight"].to(device)
            loss = (raw_loss * sample_weights).mean()
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            scheduler.step()

            train_loss_sum += loss.item()
            train_steps += 1

            preds = outputs.logits.argmax(dim=-1)
            train_correct += (preds == batch_labels).sum().item()
            train_total += batch_labels.size(0)

        avg_train_loss = train_loss_sum / max(train_steps, 1)
        train_acc = train_correct / max(train_total, 1)

        # --- Validate ---
        model.eval()
        val_loss_sum = 0.0
        val_correct = 0
        val_total = 0
        val_steps = 0

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                batch_labels = batch["labels"].to(device)

                outputs = model(input_ids=input_ids, attention_mask=attention_mask)
                raw_loss = loss_fn(outputs.logits, batch_labels)
                sample_weights = batch["weight"].to(device)
                loss = (raw_loss * sample_weights).mean()

                val_loss_sum += loss.item()
                val_steps += 1

                preds = outputs.logits.argmax(dim=-1)
                val_correct += (preds == batch_labels).sum().item()
                val_total += batch_labels.size(0)

        avg_val_loss = val_loss_sum / max(val_steps, 1)
        val_acc = val_correct / max(val_total, 1)
        print(
            f"Epoch {epoch}/{epochs}  "
            f"train_loss={avg_train_loss:.4f}  train_acc={train_acc:.4f}  "
            f"val_loss={avg_val_loss:.4f}  val_acc={val_acc:.4f}"
        )

        # --- Early stopping (track val_acc, not val_loss) ---
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            # Save best model + optimizer/scheduler for resume
            model.save_pretrained(str(output_dir))
            tokenizer.save_pretrained(str(output_dir))
            torch.save({
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "epoch": epoch,
                "best_val_acc": best_val_acc,
            }, str(output_dir / "training_state.pt"))
            print(f"  -> Best model saved (val_acc={best_val_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  -> Early stopping at epoch {epoch} (patience={patience})")
                break

    # ------------------------------------------------------------------
    # Test evaluation
    # ------------------------------------------------------------------
    print("\n--- Test Evaluation ---")

    # Reload best model
    best_model = AutoModelForSequenceClassification.from_pretrained(
        str(output_dir), num_labels=num_labels
    )
    best_model.to(device)
    best_model.eval()

    all_preds: list[int] = []
    all_labels: list[int] = []

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            batch_labels = batch["labels"]

            outputs = best_model(input_ids=input_ids, attention_mask=attention_mask)
            preds = outputs.logits.argmax(dim=-1)

            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(batch_labels.tolist())

    # Metrics
    acc = accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average="macro")
    per_class_f1 = f1_score(all_labels, all_preds, average=None, labels=list(range(num_labels)))

    print(f"\n  Accuracy:  {acc:.4f}")
    print(f"  Macro F1:  {macro_f1:.4f}")
    print()
    print(classification_report(all_labels, all_preds, target_names=LABEL_NAMES, labels=list(range(num_labels))))

    metrics = {
        "accuracy": round(float(acc), 4),
        "macro_f1": round(float(macro_f1), 4),
        "per_class_f1": {
            LABEL_NAMES[i]: round(float(per_class_f1[i]), 4)
            for i in range(num_labels)
        },
        "test_samples": len(all_labels),
        "num_labels": num_labels,
        "targets": {
            "accuracy": "> 0.75",
            "macro_f1": "> 0.70",
        },
    }

    # Save metrics
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {metrics_path}")

    return metrics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Train CyberScale Phase 3 T-model (technical severity)")
    parser.add_argument(
        "--data",
        type=str,
        default="training/data/technical_training.csv",
        help="Path to training CSV (input_text, label)",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="training/configs/technical_cls.json",
        help="Path to technical_cls.json config",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/models/technical",
        help="Output directory for model checkpoint",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from existing checkpoint in --output dir",
    )

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    train(
        config=config,
        data_path=Path(args.data),
        output_dir=Path(args.output),
        resume=args.resume,
    )


if __name__ == "__main__":
    main()
