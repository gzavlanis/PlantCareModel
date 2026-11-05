"""Κεντρικό entrypoint εκπαίδευσης, visualization και export."""

from sklearn.model_selection import train_test_split
from src.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES
from src.generator import SyntheticPlantDataGeneratorV2
from src.trainer import ModelTrainerV2
from src.exporter import DartCodeExporterV2
from src.visualizer import ModelVisualizer, AccuracyVisualizer


def main():
    print("1/4 Generating synthetic plant dataset...")
    df = SyntheticPlantDataGeneratorV2.generate(n_samples=5000)

    print("2/4 Training Hybrid Pipeline...")
    trainer = ModelTrainerV2(alpha=0.1)
    pipeline, metrics = trainer.train_and_evaluate(df)

    print("\n--- Pipeline Evaluation Metrics ---")
    print(f"Physics Baseline MAE : {metrics['raw_baseline_mae']:.3f} days")
    print(f"Hybrid Engine MAE    : {metrics['hybrid_mae']:.3f} days")
    print(f"Accuracy Gain        : {metrics['improvement_pct']:.2f}%")
    print(f"Residual R² Score    : {metrics['residual_r2']:.3f}")
    print("-----------------------------------\n")

    print("3/4 Generating Evaluation Plots...")
    # Κρατάμε το ίδιο test split για τη σχεδίαση των γραφημάτων
    X = df[CATEGORICAL_FEATURES + NUMERICAL_FEATURES]
    _, X_test, _, _ = train_test_split(
        X, df["residual_target"], test_size=0.2, random_state=42
    )

    actual_test = df.loc[X_test.index, "actual_days"]
    baseline_test = df.loc[X_test.index, "baseline_prediction"]
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

    # 3. Ανάλυση σφάλματος ανά κατηγορία φυτού και υλικό γλάστρας
    test_df = df.loc[X_test.index].copy()
    test_df["hybrid_prediction"] = hybrid_test
    ModelVisualizer.plot_category_error_breakdown(
        test_df=test_df,
        output_dir="reports/figures",
    )

    # 4. Ανάλυση αποφάσεων λίπανσης & θερμοκρασιακών δικλείδων ασφαλείας
    ModelVisualizer.plot_fertilizer_summary(
        df=df,
        output_dir="reports/figures",
    )

    print("\n4/4 Exporting to Dart for Flutter...")
    DartCodeExporterV2.export(
        pipeline, output_path="lib_output/smart_watering_engine.dart"
    )
    print("\n[COMPLETE] Όλα τα στάδια ολοκληρώθηκαν επιτυχώς!")


if __name__ == "__main__":
    main()