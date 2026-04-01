"""Train CyberScale v6 multi-task severity scorer.

Trains a shared ModernBERT encoder with a primary band head (4-class)
and 8 auxiliary CVSS component heads.  Early stopping is on band val_acc
(the primary metric).

Usage:
    cd CyberScale
    poetry run python training/scripts/train_scorer_multitask.py \
        --data training/data/training_cves_v6.csv \
        --config training/configs/scorer_multitask.json \
        --output data/models/scorer_v6
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

# ---------------------------------------------------------------------------
# Allow importing from src/ when running from project root
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from cyberscale.models.scorer_multitask import MultiTaskScorer  # noqa: E402

# ---------------------------------------------------------------------------
# Label names
# ---------------------------------------------------------------------------
LABEL_NAMES = ["Low", "Medium", "High", "Critical"]

COMPONENT_NAMES = ["av", "ac", "pr", "ui", "scope", "conf", "integ", "avail"]


# ---------------------------------------------------------------------------
# Label conversion
# ---------------------------------------------------------------------------
def score_to_label(score: float) -> int:
    """Convert CVSS score to class index."""
    if score >= 9.0:
        return 3  # Critical
    if score >= 7.0:
        return 2  # High
    if score >= 4.0:
        return 1  # Medium
    return 0  # Low


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class CVEMultiTaskDataset(Dataset):
    """Tokenised CVE descriptions with band label + 8 component labels."""

    def __init__(
        self,
        descriptions: list[str],
        cwes: list[str | None],
        band_labels: list[int],
        component_labels: dict[str, list[int]],
        component_masks: dict[str, list[bool]],
        tokenizer,
        max_length: int = 256,
        vendors: list[str | None] | None = None,
        products: list[str | None] | None = None,
    ):
        self.descriptions = descriptions
        self.cwes = cwes
        self.band_labels = band_labels
        self.component_labels = component_labels
        self.component_masks = component_masks
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.vendors = vendors or [None] * len(descriptions)
        self.products = products or [None] * len(descriptions)

    def __len__(self) -> int:
        return len(self.descriptions)

    def __getitem__(self, idx: int) -> dict:
        desc = self.descriptions[idx]
        cwe = self.cwes[idx]
        vendor = self.vendors[idx]
        product = self.products[idx]

        # Build enriched input: description [SEP] cwe: X vendor: Y product: Z
        suffixes = []
        if cwe and str(cwe).strip() and str(cwe).lower() not in ("nan", "none", ""):
            suffixes.append(f"cwe: {cwe}")
        if vendor and str(vendor).strip() and str(vendor).lower() not in ("nan", "none", ""):
            suffixes.append(f"vendor: {vendor}")
        if product and str(product).strip() and str(product).lower() not in ("nan", "none", ""):
            suffixes.append(f"product: {product}")

        if suffixes:
            text = f"{desc} [SEP] {' '.join(suffixes)}"
        else:
            text = desc

        encoding = self.tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt",
        )

        item = {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "band_label": torch.tensor(self.band_labels[idx], dtype=torch.long),
        }

        for comp in COMPONENT_NAMES:
            item[f"{comp}_label"] = torch.tensor(
                self.component_labels[comp][idx], dtype=torch.long
            )
            item[f"{comp}_mask"] = torch.tensor(
                self.component_masks[comp][idx], dtype=torch.bool
            )

        return item


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def detect_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def encode_component_labels(
    df: pd.DataFrame,
    label_maps: dict[str, dict[str, int]],
) -> tuple[dict[str, list[int]], dict[str, list[bool]]]:
    """Convert component string labels to integer labels + validity masks."""
    component_labels: dict[str, list[int]] = {}
    component_masks: dict[str, list[bool]] = {}

    for comp in COMPONENT_NAMES:
        labels = []
        masks = []
        lmap = label_maps[comp]
        col = df[comp] if comp in df.columns else pd.Series([None] * len(df))
        for val in col:
            val_str = str(val).strip().upper() if pd.notna(val) else ""
            if val_str in lmap:
                labels.append(lmap[val_str])
                masks.append(True)
            else:
                labels.append(0)  # placeholder — masked out in loss
                masks.append(False)
        component_labels[comp] = labels
        component_masks[comp] = masks

    return component_labels, component_masks


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def train(
    config: dict,
    data_path: Path,
    output_dir: Path,
) -> dict:
    """Run full multi-task training pipeline and return test metrics."""
    model_cfg = config["model"]
    eval_cfg = config["evaluation"]

    seed = model_cfg.get("seed", 42)
    torch.manual_seed(seed)
    np.random.seed(seed)

    device = detect_device()
    print(f"Device: {device}")

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = pd.read_csv(data_path)
    required_cols = {"cve_id", "description", "cvss_score"}
    if not required_cols.issubset(set(df.columns)):
        raise ValueError(f"CSV must contain columns: {required_cols}")

    df = df.dropna(subset=["description", "cvss_score"]).reset_index(drop=True)

    descriptions = df["description"].tolist()
    cwes = df["cwe"].tolist() if "cwe" in df.columns else [None] * len(df)
    vendors = df["cpe_vendor"].tolist() if "cpe_vendor" in df.columns else [None] * len(df)
    products = df["cpe_product"].tolist() if "cpe_product" in df.columns else [None] * len(df)
    scores = df["cvss_score"].astype(float).tolist()

    # Report CPE coverage
    vendor_valid = sum(1 for v in vendors if v and str(v).lower() not in ("nan", "none", ""))
    print(f"  CPE vendor coverage: {vendor_valid}/{len(df)} ({vendor_valid/len(df)*100:.1f}%)")
    product_valid = sum(1 for p in products if p and str(p).lower() not in ("nan", "none", ""))
    print(f"  CPE product coverage: {product_valid}/{len(df)} ({product_valid/len(df)*100:.1f}%)")

    band_labels = [score_to_label(s) for s in scores]

    # Component labels from CSV columns
    label_maps = MultiTaskScorer.COMPONENT_LABEL_MAPS
    component_labels, component_masks = encode_component_labels(df, label_maps)

    # Report component coverage
    for comp in COMPONENT_NAMES:
        valid = sum(component_masks[comp])
        print(f"  {comp}: {valid}/{len(df)} valid ({valid/len(df)*100:.1f}%)")

    # ------------------------------------------------------------------
    # Train / val / test split (stratified by band label)
    # ------------------------------------------------------------------
    test_size = eval_cfg.get("test_split", 0.15)
    val_size = eval_cfg.get("val_split", 0.15)

    indices = list(range(len(descriptions)))

    train_val_idx, test_idx = train_test_split(
        indices, test_size=test_size, random_state=seed, stratify=band_labels
    )

    train_val_labels = [band_labels[i] for i in train_val_idx]
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

    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    def make_dataset(idxs: list[int]) -> CVEMultiTaskDataset:
        return CVEMultiTaskDataset(
            descriptions=[descriptions[i] for i in idxs],
            cwes=[cwes[i] for i in idxs],
            band_labels=[band_labels[i] for i in idxs],
            component_labels={
                comp: [component_labels[comp][i] for i in idxs]
                for comp in COMPONENT_NAMES
            },
            component_masks={
                comp: [component_masks[comp][i] for i in idxs]
                for comp in COMPONENT_NAMES
            },
            tokenizer=tokenizer,
            max_length=max_length,
            vendors=[vendors[i] for i in idxs],
            products=[products[i] for i in idxs],
        )

    train_ds = make_dataset(train_idx)
    val_ds = make_dataset(val_idx)
    test_ds = make_dataset(test_idx)

    batch_size = model_cfg.get("batch_size", 16)
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size)
    test_loader = DataLoader(test_ds, batch_size=batch_size)

    # ------------------------------------------------------------------
    # Class weights for band head (inverse frequency)
    # ------------------------------------------------------------------
    num_band_labels = 4
    train_band_labels = [band_labels[i] for i in train_idx]
    counts = Counter(train_band_labels)
    total = len(train_band_labels)

    weight_list = [
        total / (num_band_labels * counts[i]) if counts[i] > 0 else 1.0
        for i in range(num_band_labels)
    ]
    weight_tensor = torch.tensor(weight_list, dtype=torch.float32).to(device)
    print(f"Band class weights: {dict(zip(LABEL_NAMES, [f'{w:.2f}' for w in weight_list]))}")

    label_smoothing = model_cfg.get("label_smoothing", 0.1)
    band_loss_fn = torch.nn.CrossEntropyLoss(
        weight=weight_tensor, label_smoothing=label_smoothing
    )

    # Component loss functions (no class weights — simpler auxiliary tasks)
    comp_loss_fns = {
        comp: torch.nn.CrossEntropyLoss(label_smoothing=label_smoothing)
        for comp in COMPONENT_NAMES
    }

    # Component loss weights from config
    comp_cfg = model_cfg.get("component_configs", {})
    comp_weights = {
        comp: comp_cfg.get(comp, {}).get("weight", 1.0)
        for comp in COMPONENT_NAMES
    }
    lambda_components = model_cfg.get("lambda_components", 0.3)
    print(f"Lambda components: {lambda_components}")

    # ------------------------------------------------------------------
    # Model
    # ------------------------------------------------------------------
    dropout_rate = model_cfg.get("dropout", 0.3)
    # Build component_configs for model (num_labels only)
    model_comp_configs = {
        comp: {"num_labels": comp_cfg.get(comp, {}).get("num_labels", lm_size)}
        for comp, lm_size in [
            (c, len(MultiTaskScorer.COMPONENT_LABEL_MAPS[c]))
            for c in COMPONENT_NAMES
        ]
    }

    model = MultiTaskScorer(
        base_model=base_model,
        num_band_labels=num_band_labels,
        component_configs=model_comp_configs,
        dropout=dropout_rate,
    )
    model.to(device)

    # ------------------------------------------------------------------
    # Optimiser, scheduler
    # ------------------------------------------------------------------
    lr = model_cfg.get("learning_rate", 1e-5)
    weight_decay = model_cfg.get("weight_decay", 0.01)
    optimizer = AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    epochs = model_cfg.get("epochs", 20)
    warmup_ratio = model_cfg.get("warmup_ratio", 0.1)
    total_steps = len(train_loader) * epochs
    warmup_steps = max(1, int(total_steps * warmup_ratio))
    scheduler = LinearLR(optimizer, start_factor=0.1, total_iters=warmup_steps)

    grad_clip = model_cfg.get("gradient_clip", 1.0)
    patience = model_cfg.get("patience", 5)

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    best_val_acc = 0.0
    patience_counter = 0
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, epochs + 1):
        # --- Train ---
        model.train()
        train_loss_sum = 0.0
        train_band_correct = 0
        train_band_total = 0
        train_comp_correct = {comp: 0 for comp in COMPONENT_NAMES}
        train_comp_total = {comp: 0 for comp in COMPONENT_NAMES}
        train_steps = 0

        for batch in train_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            b_labels = batch["band_label"].to(device)

            optimizer.zero_grad()
            band_logits, comp_logits = model(input_ids, attention_mask)

            # Band loss (primary)
            loss = band_loss_fn(band_logits, b_labels)

            # Component losses (auxiliary, masked)
            for comp in COMPONENT_NAMES:
                c_labels = batch[f"{comp}_label"].to(device)
                c_mask = batch[f"{comp}_mask"].to(device)

                if c_mask.any():
                    c_logits = comp_logits[comp][c_mask]
                    c_targets = c_labels[c_mask]
                    c_loss = comp_loss_fns[comp](c_logits, c_targets)
                    loss = loss + lambda_components * comp_weights[comp] * c_loss

                    # Track component accuracy
                    c_preds = c_logits.argmax(dim=-1)
                    train_comp_correct[comp] += (c_preds == c_targets).sum().item()
                    train_comp_total[comp] += c_targets.size(0)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
            optimizer.step()
            scheduler.step()

            train_loss_sum += loss.item()
            train_steps += 1

            preds = band_logits.argmax(dim=-1)
            train_band_correct += (preds == b_labels).sum().item()
            train_band_total += b_labels.size(0)

        avg_train_loss = train_loss_sum / max(train_steps, 1)
        train_band_acc = train_band_correct / max(train_band_total, 1)

        # --- Validate ---
        model.eval()
        val_band_correct = 0
        val_band_total = 0
        val_comp_correct = {comp: 0 for comp in COMPONENT_NAMES}
        val_comp_total = {comp: 0 for comp in COMPONENT_NAMES}

        with torch.no_grad():
            for batch in val_loader:
                input_ids = batch["input_ids"].to(device)
                attention_mask = batch["attention_mask"].to(device)
                b_labels = batch["band_label"].to(device)

                band_logits, comp_logits = model(input_ids, attention_mask)

                preds = band_logits.argmax(dim=-1)
                val_band_correct += (preds == b_labels).sum().item()
                val_band_total += b_labels.size(0)

                for comp in COMPONENT_NAMES:
                    c_labels = batch[f"{comp}_label"].to(device)
                    c_mask = batch[f"{comp}_mask"].to(device)
                    if c_mask.any():
                        c_preds = comp_logits[comp][c_mask].argmax(dim=-1)
                        c_targets = c_labels[c_mask]
                        val_comp_correct[comp] += (c_preds == c_targets).sum().item()
                        val_comp_total[comp] += c_targets.size(0)

        val_band_acc = val_band_correct / max(val_band_total, 1)

        # Compute per-component val accuracy
        comp_accs = {}
        for comp in COMPONENT_NAMES:
            if val_comp_total[comp] > 0:
                comp_accs[comp] = val_comp_correct[comp] / val_comp_total[comp]

        avg_comp_acc = np.mean(list(comp_accs.values())) if comp_accs else 0.0

        print(
            f"Epoch {epoch}/{epochs}  "
            f"loss={avg_train_loss:.4f}  "
            f"train_band={train_band_acc:.4f}  "
            f"val_band={val_band_acc:.4f}  "
            f"val_comp_avg={avg_comp_acc:.4f}"
        )

        # --- Early stopping (track val band accuracy — primary metric) ---
        if val_band_acc > best_val_acc:
            best_val_acc = val_band_acc
            patience_counter = 0
            model.save_pretrained(str(output_dir))
            tokenizer.save_pretrained(str(output_dir))
            torch.save({
                "optimizer": optimizer.state_dict(),
                "scheduler": scheduler.state_dict(),
                "epoch": epoch,
                "best_val_acc": best_val_acc,
            }, str(output_dir / "training_state.pt"))
            print(f"  -> Best model saved (val_band_acc={best_val_acc:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"  -> Early stopping at epoch {epoch} (patience={patience})")
                break

    # ------------------------------------------------------------------
    # Test evaluation
    # ------------------------------------------------------------------
    print("\n--- Test Evaluation ---")

    best_model = MultiTaskScorer.from_pretrained(str(output_dir))
    best_model.to(device)
    best_model.eval()

    all_band_preds: list[int] = []
    all_band_labels: list[int] = []
    all_comp_preds: dict[str, list[int]] = {c: [] for c in COMPONENT_NAMES}
    all_comp_labels: dict[str, list[int]] = {c: [] for c in COMPONENT_NAMES}

    with torch.no_grad():
        for batch in test_loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            b_labels = batch["band_label"]

            band_logits, comp_logits = best_model(input_ids, attention_mask)
            preds = band_logits.argmax(dim=-1).cpu()

            all_band_preds.extend(preds.tolist())
            all_band_labels.extend(b_labels.tolist())

            for comp in COMPONENT_NAMES:
                c_labels = batch[f"{comp}_label"]
                c_mask = batch[f"{comp}_mask"]
                if c_mask.any():
                    c_preds = comp_logits[comp][c_mask].argmax(dim=-1).cpu()
                    c_targets = c_labels[c_mask]
                    all_comp_preds[comp].extend(c_preds.tolist())
                    all_comp_labels[comp].extend(c_targets.tolist())

    # Band metrics
    band_acc = accuracy_score(all_band_labels, all_band_preds)
    macro_f1 = f1_score(all_band_labels, all_band_preds, average="macro")
    per_class_f1 = f1_score(
        all_band_labels, all_band_preds, average=None, labels=list(range(4))
    )

    print(f"\n  Band Accuracy:  {band_acc:.4f}")
    print(f"  Band Macro F1:  {macro_f1:.4f}")
    print()
    print(classification_report(
        all_band_labels, all_band_preds,
        target_names=LABEL_NAMES, labels=list(range(4))
    ))

    # Component metrics
    comp_accuracies = {}
    print("  Per-component accuracy:")
    for comp in COMPONENT_NAMES:
        if all_comp_labels[comp]:
            comp_acc = accuracy_score(all_comp_labels[comp], all_comp_preds[comp])
            comp_accuracies[comp] = round(float(comp_acc), 4)
            print(f"    {comp:6s}: {comp_acc:.4f} (n={len(all_comp_labels[comp])})")

    avg_comp_acc = float(np.mean(list(comp_accuracies.values()))) if comp_accuracies else 0.0
    print(f"\n  Avg component accuracy: {avg_comp_acc:.4f}")

    metrics = {
        "band_accuracy": round(float(band_acc), 4),
        "band_macro_f1": round(float(macro_f1), 4),
        "per_class_f1": {
            LABEL_NAMES[i]: round(float(per_class_f1[i]), 4)
            for i in range(4)
        },
        "component_accuracies": comp_accuracies,
        "avg_component_accuracy": round(avg_comp_acc, 4),
        "test_samples": len(all_band_labels),
        "targets": {
            "band_accuracy": "> 0.70",
            "band_macro_f1": "> 0.65",
            "avg_component_accuracy": "> 0.80",
        },
    }

    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nMetrics saved to {metrics_path}")

    return metrics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Train CyberScale v6 multi-task scorer")
    parser.add_argument("--data", type=str, required=True, help="Training CSV path")
    parser.add_argument("--config", type=str, required=True, help="Config JSON path")
    parser.add_argument("--output", type=str, required=True, help="Output model directory")

    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    train(
        config=config,
        data_path=Path(args.data),
        output_dir=Path(args.output),
    )


if __name__ == "__main__":
    main()
