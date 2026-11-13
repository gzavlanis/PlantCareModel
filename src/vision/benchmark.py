"""Module αξιολόγησης και επιλογής Mobile Vision Models για αναγνώριση φυτών."""

import os
import time
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from typing import Dict, List, Any
from datasets import load_dataset
from transformers import AutoImageProcessor, AutoModelForImageClassification

# 1. Υποψήφια μοντέλα από το Hugging Face Hub
CANDIDATE_MODELS: Dict[str, str] = {
    "MobileNetV3-Small": "timm/mobilenetv3_small_100.lamb_in1k",
    "MobileNetV3-Large": "timm/mobilenetv3_large_100.ra_in1k",
    "EfficientNet-B0": "google/efficientnet-b0",
    "MobileViT-Small": "apple/mobilevit-small",
    "Plant-ViT-FineTuned": "nateraw/vit-base-beans",
}


class PlantVisionBenchmark:
    """Benchmark harness για μοντέλα όρασης προσανατολισμένα σε mobile (Flutter)."""

    def __init__(
        self,
        dataset_name: str = "AI-Lab-Makerere/beans",
        split: str = "test",
        max_samples: int = 100,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        self.device = torch.device(device)
        self.dataset_name = dataset_name
        self.split = split
        self.max_samples = max_samples
        self.output_dir = "reports/vision_benchmark"
        os.makedirs(self.output_dir, exist_ok=True)

    def load_evaluation_data(self) -> List[Dict[str, Any]]:
        """Φορτώνει δείγματα από πραγματικό dataset φυτών του Hugging Face Hub."""
        print(f"[Dataset] Loading '{self.dataset_name}' ({self.split} split)...")
        try:
            ds = load_dataset(self.dataset_name, split=self.split)
            num_samples = min(len(ds), self.max_samples)
            subset = ds.select(range(num_samples))

            samples = []
            for item in subset:
                img = (
                    item["image"]
                    if isinstance(item["image"], Image.Image)
                    else Image.open(item["image"])
                )
                samples.append({
                    "image": img.convert("RGB"),
                    "label_idx": item.get("labels", item.get("label", 0)),
                })
            print(f"[Dataset] Loaded {len(samples)} plant images successfully.")
            return samples
        except Exception as e:
            print(
                f"[Dataset Warning] Hugging Face dataset download failed ({e}). Generating fallback test images..."
            )
            return self._generate_fallback_samples()

    def _generate_fallback_samples(self) -> List[Dict[str, Any]]:
        """Fallback σε τοπικά συνθετικά δείγματα εικόνας αν δεν υπάρχει σύνδεση."""
        samples = []
        for i in range(20):
            arr = np.random.randint(50, 180, (224, 224, 3), dtype=np.uint8)
            arr[:, :, 1] = np.clip(arr[:, :, 1] + 50, 0, 255)
            samples.append({"image": Image.fromarray(arr), "label_idx": i % 3})
        return samples

    def evaluate_model(
        self, model_name: str, model_id: str, samples: List[Dict[str, Any]]
    ) -> Dict[str, Any] | None:
        """Μετράει Top-1/Top-5 accuracy, inference latency και εκτιμώμενο μέγεθος."""
        print(f"\n---> Benchmarking: {model_name} [{model_id}] on {self.device}...")

        try:
            processor = AutoImageProcessor.from_pretrained(model_id)
            model = AutoModelForImageClassification.from_pretrained(model_id).to(
                self.device
            )
            model.eval()
        except Exception as e:
            print(f"     [Error loading {model_id}]: {e}")
            return None

        # 1. Υπολογισμός Παραμέτρων & Εκτιμώμενου Μεγέθους TFLite
        total_params = sum(p.numel() for p in model.parameters())
        fp32_size_mb = (total_params * 4) / (1024 * 1024)
        tflite_fp16_mb = (total_params * 2) / (1024 * 1024)

        # 2. Warmup
        dummy_tensor = torch.randn(1, 3, 224, 224).to(self.device)
        for _ in range(5):
            with torch.no_grad():
                _ = model(dummy_tensor)

        # 3. Inference Loop & Latency Measurements
        latencies_ms: List[float] = []
        top1_hits = 0
        top5_hits = 0

        with torch.no_grad():
            for sample in samples:
                img = sample["image"]
                target_idx = sample["label_idx"]

                inputs = processor(images=img, return_tensors="pt").to(self.device)

                if self.device.type == "cuda":
                    torch.cuda.synchronize()
                t_start = time.perf_counter()

                outputs = model(**inputs)

                if self.device.type == "cuda":
                    torch.cuda.synchronize()
                t_end = time.perf_counter()

                latencies_ms.append((t_end - t_start) * 1000.0)

                logits = outputs.logits
                num_classes = logits.shape[-1]
                k = min(5, num_classes)
                top_indices = torch.topk(logits, k=k, dim=-1).indices[0].cpu().tolist()

                if target_idx == top_indices[0]:
                    top1_hits += 1
                if target_idx in top_indices:
                    top5_hits += 1

        n = len(samples)
        mean_latency = float(np.mean(latencies_ms))
        p95_latency = float(np.percentile(latencies_ms, 95))
        top1_acc = (top1_hits / n) * 100.0
        top5_acc = (top5_hits / n) * 100.0

        return {
            "model_name": model_name,
            "model_id": model_id,
            "params_millions": round(total_params / 1e6, 2),
            "fp32_mb": round(fp32_size_mb, 2),
            "tflite_fp16_mb": round(tflite_fp16_mb, 2),
            "mean_latency_ms": round(mean_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "top1_acc_pct": round(top1_acc, 2),
            "top5_acc_pct": round(top5_acc, 2),
        }

    def run_all(self, models_dict: Dict[str, str]) -> pd.DataFrame:
        """Εκτελεί το benchmark σε όλα τα υποψήφια μοντέλα και εξάγει αναφορές."""
        samples = self.load_evaluation_data()
        records = []

        for name, m_id in models_dict.items():
            result = self.evaluate_model(name, m_id, samples)
            if result:
                records.append(result)

        df = pd.DataFrame(records)
        if df.empty:
            print("[Warning] No models were successfully evaluated.")
            return df

        csv_path = os.path.join(self.output_dir, "benchmark_metrics.csv")
        df.to_csv(csv_path, index=False)
        print(f"\n[Results] Saved raw benchmark metrics to: {csv_path}")

        self._plot_visualizations(df)
        return df

    def _plot_visualizations(self, df: pd.DataFrame) -> None:
        """Παράγει συγκριτικά γραφήματα απόδοσης, trade-off και μεγέθους."""
        plt.style.use(
            "seaborn-v0_8-whitegrid"
            if "seaborn-v0_8-whitegrid" in plt.style.available
            else "default"
        )
        fig = plt.figure(figsize=(16, 5), dpi=150)

        # 1. Pareto Frontier: Latency vs Top-1 Accuracy
        ax1 = fig.add_subplot(1, 3, 1)
        palette = ["#0284c7", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"]

        for i, row in df.iterrows():
            color = palette[i % len(palette)]
            ax1.scatter(
                row["mean_latency_ms"],
                row["top1_acc_pct"],
                s=min(row["tflite_fp16_mb"] * 25, 800),  # Cap bubble size για μεγάλα ViT
                color=color,
                alpha=0.7,
                edgecolors="black",
                linewidth=1.2,
                label=f"{row['model_name']} ({row['tflite_fp16_mb']} MB)",
            )
            ax1.annotate(
                row["model_name"],
                (row["mean_latency_ms"] + 1.0, row["top1_acc_pct"] + 0.5),
                fontsize=8.5,
                fontweight="bold",
            )

        ax1.set_title(
            "Pareto Front: Accuracy vs Mobile Latency", fontsize=11, fontweight="bold"
        )
        ax1.set_xlabel("Mean Inference Latency (ms) [Lower is better]", fontsize=10)
        ax1.set_ylabel("Top-1 Accuracy (%) [Higher is better]", fontsize=10)
        ax1.legend(loc="lower right", fontsize=8)

        # 2. Top-1 vs Top-5 Accuracy Breakdown
        ax2 = fig.add_subplot(1, 3, 2)
        x = np.arange(len(df))
        w = 0.35

        ax2.bar(x - w / 2, df["top1_acc_pct"], w, label="Top-1 Acc (%)", color="#0284c7")
        ax2.bar(x + w / 2, df["top5_acc_pct"], w, label="Top-5 Acc (%)", color="#38bdf8")
        ax2.set_xticks(x)
        ax2.set_xticklabels(df["model_name"], rotation=20, ha="right", fontsize=9)
        ax2.set_ylabel("Accuracy (%)", fontsize=10)
        ax2.set_title(
            "Classification Accuracy (Top-1 vs Top-5)", fontsize=11, fontweight="bold"
        )
        ax2.set_ylim(0, 108)
        ax2.legend(loc="lower right")

        for i in x:
            t1 = df.loc[i, "top1_acc_pct"]
            t5 = df.loc[i, "top5_acc_pct"]
            ax2.text(
                i - w / 2, t1 + 1.2, f"{t1:.0f}%", ha="center", fontsize=8, fontweight="bold"
            )
            ax2.text(i + w / 2, t5 + 1.2, f"{t5:.0f}%", ha="center", fontsize=8)

        # 3. Model Size Comparison (Flutter APK Impact)
        ax3 = fig.add_subplot(1, 3, 3)
        ax3.bar(
            range(len(df)),
            df["tflite_fp16_mb"],
            color=["#10b981" if m < 15 else "#f59e0b" for m in df["tflite_fp16_mb"]],
            width=0.5,
        )
        ax3.set_xticks(range(len(df)))
        ax3.axhline(
            15.0,
            color="#ef4444",
            linestyle="--",
            lw=1.2,
            label="Recommended Mobile Budget (15MB)",
        )
        ax3.set_ylabel("Exported TFLite FP16 Size (MB)", fontsize=10)
        ax3.set_title(
            "Estimated Mobile App Size Overhead", fontsize=11, fontweight="bold"
        )
        ax3.set_xticklabels(df["model_name"], rotation=20, ha="right", fontsize=9)
        ax3.legend(loc="upper left", fontsize=8.5)

        for i, val in enumerate(df["tflite_fp16_mb"]):
            ax3.text(
                i, val + 0.5, f"{val:.1f} MB", ha="center", fontsize=8.5, fontweight="bold"
            )

        plt.tight_layout()
        plot_path = os.path.join(self.output_dir, "vision_models_comparison.png")
        plt.savefig(plot_path, bbox_inches="tight")
        plt.close()
        print(f"[Plots Generated] Saved benchmark summary chart to: {plot_path}")


def main():
    benchmark = PlantVisionBenchmark(
        dataset_name="AI-Lab-Makerere/beans",
        split="test",
        max_samples=100,
    )
    df_metrics = benchmark.run_all(CANDIDATE_MODELS)

    if not df_metrics.empty:
        print("\n======================= VISION BENCHMARK REPORT =======================")
        print(
            df_metrics[
                [
                    "model_name",
                    "top1_acc_pct",
                    "top5_acc_pct",
                    "mean_latency_ms",
                    "tflite_fp16_mb",
                ]
            ].to_string(index=False)
        )
        print("=======================================================================\n")


if __name__ == "__main__":
    main()