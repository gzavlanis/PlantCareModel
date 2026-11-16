"""Κεντρικό ενοποιημένο entrypoint: Engine Training, Full Visualizations, Vision Benchmark & Export."""

import argparse
from sklearn.model_selection import train_test_split

from src.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from src.generator import SyntheticPlantDataGeneratorV2
from src.trainer import ModelTrainerV2
from src.exporter import DartCodeExporterV2
from src.visualizer import ModelVisualizer, AccuracyVisualizer

RANDOM_SEED = 42

def run_engine_pipeline():
    print("\n=== [1/2] RUNNING SMART WATERING & FERTILIZER PIPELINE ===")

    print("1/4 Generating synthetic plant dataset (Pot & In-Ground FAO-56)...")
    df = SyntheticPlantDataGeneratorV2.generate(n_samples=5000, seed=RANDOM_SEED)

    print("2/4 Training Hybrid Pipeline...")
    trainer = ModelTrainerV2(alpha=0.5, epsilon=1.35)
    pipeline, metrics = trainer.train_and_evaluate(df)

    print("\n--- Pipeline Evaluation Metrics ---")
    print(f"Physics Baseline MAE : {metrics['raw_baseline_mae']:.3f} days")
    print(f"Hybrid Engine MAE    : {metrics['hybrid_mae']:.3f} days")
    print(f"Accuracy Gain        : {metrics['improvement_pct']:.2f}%")
    print(f"Residual R² Score    : {metrics['residual_r2']:.3f}")
    if metrics.get("pot_hybrid_mae") is not None:
        print(f"  • Potted Hybrid MAE: {metrics['pot_hybrid_mae']:.3f} days")
    if metrics.get("ground_hybrid_mae") is not None:
        print(f"  • Ground Hybrid MAE: {metrics['ground_hybrid_mae']:.3f} days")
    print("-----------------------------------\n")

    print("3/4 Generating Evaluation Plots...")
    active_df = (
        df[df["is_dormant"] == 0].copy() if "is_dormant" in df.columns else df.copy()
    )

    X = active_df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
    _, X_test, _, _ = train_test_split(
        X, active_df["residual_target"], test_size=0.2, random_state=RANDOM_SEED
    )

    actual_test = active_df.loc[X_test.index, "actual_days"]
    baseline_test = active_df.loc[X_test.index, "baseline_prediction"]
    hybrid_test = baseline_test + pipeline.predict(X_test)

    # 1. Βασικά διαγράμματα παλινδρόμησης (Parity, Residual distribution, Feature weights)
    ModelVisualizer.plot_evaluation(
        actual_days=actual_test,
        baseline_pred=baseline_test,
        hybrid_pred=hybrid_test,
        pipeline=pipeline,
        categorical_features=CATEGORICAL_FEATURES,
        numerical_features=NUMERICAL_FEATURES,
        output_dir="reports/figures",
    )

    # 2. Tolerance Accuracy (REC Curve)
    AccuracyVisualizer.plot_tolerance_accuracy(
        actual_days=actual_test,
        baseline_pred=baseline_test,
        hybrid_pred=hybrid_test,
        output_dir="reports/figures",
    )

    # 3. Ανάλυση σφάλματος ανά κατηγορία φυτού, υλικό γλάστρας και περιβάλλον (Pot vs In-Ground)
    test_df = active_df.loc[X_test.index].copy()
    test_df["hybrid_prediction"] = hybrid_test
    ModelVisualizer.plot_category_error_breakdown(
        test_df=test_df,
        output_dir="reports/figures",
    )

    # 4. Υδρολογική απόκριση εδάφους & επίδραση mulching
    ModelVisualizer.plot_ground_hydrology_profile(
        df=df,
        output_dir="reports/figures",
    )

    # 5. Ανάλυση αποφάσεων λίπανσης & θερμοκρασιακών δικλείδων ασφαλείας
    ModelVisualizer.plot_fertilizer_summary(
        df=df,
        output_dir="reports/figures",
    )

    # 6. Αρχιτεκτονικό διάγραμμα Pipeline (PNG & Interactive HTML diagram)
    ModelVisualizer.plot_pipeline_architecture(output_dir="reports/figures")
    ModelVisualizer.export_pipeline_html(pipeline, output_dir="reports/figures")

    print("\n4/4 Exporting to Dart for Flutter...")
    DartCodeExporterV2.export(
        pipeline, output_path="lib_output/smart_watering_engine.dart"
    )
    print("\n[COMPLETE] Smart Watering Engine Pipeline ολοκληρώθηκε επιτυχώς!")


def run_vision_benchmark():
    print("\n=== [2/2] RUNNING VISION MODEL BENCHMARK ===")
    from src.vision.benchmark import PlantVisionBenchmark, CANDIDATE_MODELS

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

    print("Benchmark Finished. Artifacts saved in reports/vision_benchmark/.")

def run_vision_train_and_export(base_model: str, dataset_name: str, epochs: int):
    print("\n=== [3/3] FINE-TUNING & EXPORTING MOBILE VISION MODEL ===")
    from src.vision.trainer_vision import PlantVisionTrainer
    from src.vision.exporter_tflite import VisionTFLiteExporter

    # 1. Εκπαίδευση (Transfer Learning) του ελαφριού mobile backbone
    trainer = PlantVisionTrainer(
        base_model_id=base_model,
        dataset_name=dataset_name,
        output_dir="models/vision_finetuned",
        epochs=epochs,
    )
    saved_model_dir = trainer.train()

    # 2. Μετατροπή σε TFLite + εξαγωγή labels.txt & plant_species_db.json
    VisionTFLiteExporter.export(
        model_id=saved_model_dir,
        output_dir="lib_output",
    )


def main():
    parser = argparse.ArgumentParser(description="Plant Care Model Unified Pipeline CLI")
    parser.add_argument(
        "--engine",
        action="store_true",
        help="Εκπαίδευση, όλα τα visualizers & export του Dart Engine",
    )
    parser.add_argument(
        "--vision",
        action="store_true",
        help="Εκτέλεση benchmark για τα υποψήφια Vision Models",
    )
    parser.add_argument(
        "--train-vision",
        action="store_true",
        help="Fine-tuning του επιλεγμένου mobile μοντέλου & export σε TFLite + Species DB",
    )
    parser.add_argument(
        "--base-model",
        type=str,
        default="timm/mobilenetv3_small_100.lamb_in1k",
        help="Το backbone μοντέλο που θα εκπαιδευτεί (π.χ. MobileNetV3-Small ή google/efficientnet-b0)",
    )
    parser.add_argument(
        "--vision-dataset",
        type=str,
        default="AI-Lab-Makerere/beans",
        help="Το Hugging Face dataset φυτών για εκπαίδευση",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Αριθμός εποχών (epochs) για το fine-tuning",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Εκτέλεση ολόκληρης της σουίτας (Engine + Vision Benchmark + Vision Train/Export)",
    )

    args = parser.parse_args()

    # Default συμπεριφορά αν τρέξει σκέτο `python main.py`
    if not (args.engine or args.vision or args.train_vision or args.all):
        args.engine = True

    if args.engine or args.all:
        run_engine_pipeline()

    if args.vision or args.all:
        run_vision_benchmark()

    if args.train_vision or args.all:
        run_vision_train_and_export(
            base_model=args.base_model,
            dataset_name=args.vision_dataset,
            epochs=args.epochs,
        )

if __name__ == "__main__":
    main()