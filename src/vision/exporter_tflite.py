"""Module εξαγωγής Mobile Vision Model σε TFLite και δημιουργίας Species DB για το Flutter."""

import os
import shutil
import subprocess
import sys
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

from src.vision.taxonomy_mapper import PlantTaxonomyMapper


class VisionTFLiteExporter:
    """Μετατρέπει ένα Vision checkpoint (τοπικό ή HF) σε TFLite (FP16) + Labels + Species DB."""

    DEFAULT_MODEL_PATH = "models/vision_finetuned"

    @classmethod
    def export(
        cls,
        model_id: str = DEFAULT_MODEL_PATH,
        output_dir: str = "lib_output",
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)
        temp_dir = os.path.join(output_dir, "_temp_vision_export")
        os.makedirs(temp_dir, exist_ok=True)

        print(f"\n[1/4] Loading Vision Model from: {model_id}...")
        processor = AutoImageProcessor.from_pretrained(model_id)
        model = AutoModelForImageClassification.from_pretrained(model_id)
        model.eval()

        # 1. Εξαγωγή Labels (labels.txt)
        labels_path = os.path.join(output_dir, "labels.txt")
        num_classes = len(model.config.id2label)
        with open(labels_path, "w", encoding="utf-8") as f:
            for i in range(num_classes):
                f.write(f"{model.config.id2label[i]}\n")
        print(f"[2/4] Exported {num_classes} plant classes to: {labels_path}")

        # 2. Δημιουργία Plant Species Database (plant_species_db.json)
        db_path = os.path.join(output_dir, "plant_species_db.json")
        PlantTaxonomyMapper.generate_species_database(
            labels_path=labels_path, output_path=db_path
        )

        # 3. Export PyTorch -> ONNX
        print("[3/4] Exporting PyTorch graph to ONNX...")
        size_cfg = getattr(processor, "size", {})
        img_size = size_cfg.get("height", 224) if isinstance(size_cfg, dict) else 224
        dummy_input = torch.randn(1, 3, img_size, img_size)
        onnx_path = os.path.join(temp_dir, "plant_model.onnx")

        torch.onnx.export(
            model,
            dummy_input,
            onnx_path,
            input_names=["input"],
            output_names=["output"],
            opset_version=14,
            do_constant_folding=True,
        )

        # 4. Μετατροπή ONNX -> TFLite (FP16) μέσω onnx2tf
        print("[4/4] Converting ONNX to TensorFlow Lite (.tflite)...")
        tf_out_dir = os.path.join(temp_dir, "saved_model")
        cmd = [
            sys.executable,
            "-m",
            "onnx2tf",
            "-i",
            onnx_path,
            "-o",
            tf_out_dir,
            "-osd",
            "-qt",
            "per-tensor",
        ]

        try:
            subprocess.run(cmd, check=True)
            generated_tflite = None
            for candidate in [
                os.path.join(tf_out_dir, "plant_model_float16.tflite"),
                os.path.join(tf_out_dir, "plant_model_float32.tflite"),
            ]:
                if os.path.exists(candidate):
                    generated_tflite = candidate
                    break

            if not generated_tflite:
                raise FileNotFoundError(
                    "Could not locate converted .tflite file in temp output."
                )

            final_tflite_path = os.path.join(output_dir, "plant_classifier.tflite")
            shutil.copy2(generated_tflite, final_tflite_path)

            size_mb = os.path.getsize(final_tflite_path) / (1024 * 1024)
            print(
                f"\n[COMPLETE] TFLite model saved to: {final_tflite_path} ({size_mb:.2f} MB)"
            )

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)