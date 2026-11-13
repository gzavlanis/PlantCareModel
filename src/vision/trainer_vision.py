"""Module Transfer Learning (Fine-Tuning) για Mobile Vision Models αναγνώρισης φυτών."""

import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from datasets import load_dataset
from transformers import AutoImageProcessor, AutoModelForImageClassification


class PlantVisionTrainer:
    """Εκπαιδεύει ένα mobile backbone (MobileNetV3 / EfficientNet-B0) σε φυτικό dataset."""

    def __init__(
        self,
        base_model_id: str = "timm/mobilenetv3_small_100.lamb_in1k",
        dataset_name: str = "AI-Lab-Makerere/beans",
        output_dir: str = "models/vision_finetuned",
        batch_size: int = 32,
        epochs: int = 5,
        lr: float = 3e-4,
    ):
        self.base_model_id = base_model_id
        self.dataset_name = dataset_name
        self.output_dir = output_dir
        self.batch_size = batch_size
        self.epochs = epochs
        self.lr = lr
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def train(self) -> str:
        os.makedirs(self.output_dir, exist_ok=True)
        print(f"\n[Vision Trainer] Loading dataset '{self.dataset_name}'...")
        ds = load_dataset(self.dataset_name)

        # Εντοπισμός ονόματος στήλης label ('labels' ή 'label')
        label_col = "labels" if "labels" in ds["train"].features else "label"
        class_names = ds["train"].features[label_col].names
        num_classes = len(class_names)

        id2label = {i: name for i, name in enumerate(class_names)}
        label2id = {name: i for i, name in enumerate(class_names)}

        print(f"[Vision Trainer] Found {num_classes} classes: {class_names}")
        print(f"[Vision Trainer] Initializing backbone '{self.base_model_id}' on {self.device}...")

        processor = AutoImageProcessor.from_pretrained(self.base_model_id)
        model = AutoModelForImageClassification.from_pretrained(
            self.base_model_id,
            num_labels=num_classes,
            id2label=id2label,
            label2id=label2id,
            ignore_mismatched_sizes=True,
        ).to(self.device)

        # Normalization parameters από τον processor
        size = getattr(processor, "size", {}).get("height", 224) if isinstance(getattr(processor, "size", {}), dict) else 224
        mean = getattr(processor, "image_mean", [0.485, 0.456, 0.406])
        std = getattr(processor, "image_std", [0.229, 0.224, 0.225])

        train_tf = transforms.Compose([
            transforms.Resize((size, size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(15),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])

        val_tf = transforms.Compose([
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=mean, std=std),
        ])

        def apply_train_transforms(batch):
            batch["pixel_values"] = [train_tf(img.convert("RGB")) for img in batch["image"]]
            batch["target"] = batch[label_col]
            return batch

        def apply_val_transforms(batch):
            batch["pixel_values"] = [val_tf(img.convert("RGB")) for img in batch["image"]]
            batch["target"] = batch[label_col]
            return batch

        val_split = "validation" if "validation" in ds else "test"
        train_ds = ds["train"].with_transform(apply_train_transforms)
        val_ds = ds[val_split].with_transform(apply_val_transforms)

        def collate_fn(examples):
            pixel_values = torch.stack([ex["pixel_values"] for ex in examples])
            labels = torch.tensor([ex["target"] for ex in examples], dtype=torch.long)
            return {"pixel_values": pixel_values, "labels": labels}

        train_loader = DataLoader(train_ds, batch_size=self.batch_size, shuffle=True, collate_fn=collate_fn)
        val_loader = DataLoader(val_ds, batch_size=self.batch_size, shuffle=False, collate_fn=collate_fn)

        optimizer = torch.optim.AdamW(model.parameters(), lr=self.lr, weight_decay=1e-4)
        criterion = nn.CrossEntropyLoss()

        best_val_acc = 0.0

        for epoch in range(1, self.epochs + 1):
            model.train()
            train_loss = 0.0
            for batch in train_loader:
                optimizer.zero_grad()
                inputs = batch["pixel_values"].to(self.device)
                targets = batch["labels"].to(self.device)

                outputs = model(inputs)
                loss = criterion(outputs.logits, targets)
                loss.backward()
                optimizer.step()
                train_loss += loss.item() * inputs.size(0)

            train_loss /= len(train_ds)

            # Validation
            model.eval()
            correct = 0
            total = 0
            with torch.no_grad():
                for batch in val_loader:
                    inputs = batch["pixel_values"].to(self.device)
                    targets = batch["labels"].to(self.device)
                    outputs = model(inputs)
                    preds = outputs.logits.argmax(dim=-1)
                    correct += (preds == targets).sum().item()
                    total += targets.size(0)

            val_acc = (correct / total) * 100.0
            print(f"Epoch [{epoch}/{self.epochs}] | Train Loss: {train_loss:.4f} | Val Acc: {val_acc:.2f}%")

            if val_acc >= best_val_acc:
                best_val_acc = val_acc
                model.save_pretrained(self.output_dir)
                processor.save_pretrained(self.output_dir)

        print(f"\n[Vision Trainer] Best Val Accuracy: {best_val_acc:.2f}% -> Saved to '{self.output_dir}'")
        return self.output_dir