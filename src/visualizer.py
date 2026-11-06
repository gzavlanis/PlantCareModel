"""Module παραγωγής διαγραμμάτων αξιολόγησης για το υβριδικό μοντέλο ποτίσματος και λίπανσης V3."""

import os
from typing import List
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.pipeline import Pipeline


class ModelVisualizer:
    """Οπτικοποίηση απόδοσης, ερμηνείας βαρών και κατανομής σφαλμάτων (Γλάστρα & Έδαφος)."""

    @staticmethod
    def plot_evaluation(
        actual_days: pd.Series,
        baseline_pred: pd.Series,
        hybrid_pred: pd.Series,
        pipeline: Pipeline,
        categorical_features: List[str],
        numerical_features: List[str],
        output_dir: str = "reports/figures",
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)

        plt.style.use(
            "seaborn-v0_8-whitegrid"
            if "seaborn-v0_8-whitegrid" in plt.style.available
            else "default"
        )
        fig = plt.figure(figsize=(18, 5.5), dpi=150)

        # 1. Parity Plot
        ax1 = fig.add_subplot(1, 3, 1)
        ax1.scatter(
            actual_days,
            baseline_pred,
            alpha=0.25,
            color="#94a3b8",
            label="Physics Baseline",
            s=18,
        )
        ax1.scatter(
            actual_days,
            hybrid_pred,
            alpha=0.45,
            color="#0284c7",
            label="Hybrid (Physics + ML)",
            s=18,
        )

        min_val = min(actual_days.min(), hybrid_pred.min())
        max_val = max(actual_days.max(), hybrid_pred.max())
        ax1.plot(
            [min_val, max_val],
            [min_val, max_val],
            "r--",
            lw=1.8,
            label="Perfect Fit (y = x)",
        )
        ax1.set_title(
            "Actual vs Predicted Watering Days",
            fontsize=11,
            fontweight="bold",
            pad=10,
        )
        ax1.set_xlabel("Ground Truth (Actual Days)", fontsize=10)
        ax1.set_ylabel("Predicted Days", fontsize=10)
        ax1.legend(loc="upper left", frameon=True)

        # 2. Residual Distribution
        ax2 = fig.add_subplot(1, 3, 2)
        baseline_residuals = actual_days - baseline_pred
        hybrid_residuals = actual_days - hybrid_pred

        bins = np.linspace(-4, 4, 35)
        ax2.hist(
            baseline_residuals,
            bins=bins,
            alpha=0.4,
            color="#94a3b8",
            label=f"Baseline (Std: {baseline_residuals.std():.2f}d)",
            edgecolor="none",
        )
        ax2.hist(
            hybrid_residuals,
            bins=bins,
            alpha=0.65,
            color="#10b981",
            label=f"Hybrid (Std: {hybrid_residuals.std():.2f}d)",
            edgecolor="none",
        )
        ax2.axvline(0, color="black", linestyle=":", lw=1.2)
        ax2.set_title(
            "Residual Error Distribution (Days)",
            fontsize=11,
            fontweight="bold",
            pad=10,
        )
        ax2.set_xlabel("Prediction Error (Actual - Predicted)", fontsize=10)
        ax2.set_ylabel("Sample Frequency", fontsize=10)
        ax2.legend(loc="upper right", frameon=True)

        # 3. Top Feature Weights
        ax3 = fig.add_subplot(1, 3, 3)
        regressor = pipeline.named_steps["regressor"]
        preprocessor = pipeline.named_steps["preprocessor"]

        cat_encoder = preprocessor.named_transformers_["cat"]
        encoded_cat = list(
            cat_encoder.get_feature_names_out(categorical_features)
        )
        all_features = numerical_features + encoded_cat
        weights = regressor.coef_

        sorted_indices = np.argsort(np.abs(weights))[-12:]
        top_features = [all_features[i] for i in sorted_indices]
        top_weights = weights[sorted_indices]

        colors = ["#ef4444" if w < 0 else "#3b82f6" for w in top_weights]
        ax3.barh(top_features, top_weights, color=colors, height=0.65)
        ax3.axvline(0, color="gray", linestyle="--", lw=0.8)
        ax3.set_title(
            "Top 12 ML Feature Weights (Impact on Residual)",
            fontsize=11,
            fontweight="bold",
            pad=10,
        )
        ax3.set_xlabel(
            "Weight Value (Red: Reduces Days, Blue: Increases)", fontsize=10
        )

        plt.tight_layout()
        save_path = os.path.join(output_dir, "model_performance_summary.png")
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[Plots Generated] Saved summary to: {save_path}")

    @staticmethod
    def plot_category_error_breakdown(
        test_df: pd.DataFrame,
        actual_col: str = "actual_days",
        baseline_col: str = "baseline_prediction",
        hybrid_col: str = "hybrid_prediction",
        output_dir: str = "reports/figures",
    ) -> None:
        """Συγκριτικό MAE ανά κατηγορία φυτού, υλικό δοχείου και περιβάλλον (Γλάστρα vs Έδαφος)."""
        os.makedirs(output_dir, exist_ok=True)
        fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5), dpi=150)

        test_df = test_df.copy()
        test_df["base_ae"] = (test_df[actual_col] - test_df[baseline_col]).abs()
        test_df["hybr_ae"] = (test_df[actual_col] - test_df[hybrid_col]).abs()

        # 1. Σφάλμα ανά Plant Type
        plant_grp = (
            test_df.groupby("plant_type")[["base_ae", "hybr_ae"]]
            .mean()
            .reset_index()
        )
        x = np.arange(len(plant_grp))
        width = 0.35

        ax1.bar(
            x - width / 2,
            plant_grp["base_ae"],
            width,
            label="Baseline MAE",
            color="#94a3b8",
        )
        ax1.bar(
            x + width / 2,
            plant_grp["hybr_ae"],
            width,
            label="Hybrid MAE",
            color="#0284c7",
        )
        ax1.set_xticks(x)
        ax1.set_xticklabels(
            plant_grp["plant_type"], rotation=25, ha="right", fontsize=9
        )
        ax1.set_ylabel("Mean Absolute Error (Days)", fontsize=10)
        ax1.set_title(
            "Error per Plant Category", fontsize=11, fontweight="bold"
        )
        ax1.legend()

        # 2. Σφάλμα ανά Pot Type (Μόνο για όσα έχουν γλάστρα)
        pot_df = test_df[test_df["pot_type"] != "none_ground"]
        pot_grp = (
            pot_df.groupby("pot_type")[["base_ae", "hybr_ae"]]
            .mean()
            .reset_index()
        )
        x_pot = np.arange(len(pot_grp))

        ax2.bar(
            x_pot - width / 2,
            pot_grp["base_ae"],
            width,
            label="Baseline MAE",
            color="#94a3b8",
        )
        ax2.bar(
            x_pot + width / 2,
            pot_grp["hybr_ae"],
            width,
            label="Hybrid MAE",
            color="#10b981",
        )
        ax2.set_xticks(x_pot)
        ax2.set_xticklabels(
            pot_grp["pot_type"], rotation=25, ha="right", fontsize=9
        )
        ax2.set_ylabel("Mean Absolute Error (Days)", fontsize=10)
        ax2.set_title(
            "Error per Container Material", fontsize=11, fontweight="bold"
        )
        ax2.legend()

        # 3. Σφάλμα ανά Περιβάλλον (Pot vs In-Ground)
        env_grp = (
            test_df.groupby("planting_environment")[["base_ae", "hybr_ae"]]
            .mean()
            .reset_index()
        )
        x_env = np.arange(len(env_grp))

        ax3.bar(
            x_env - width / 2,
            env_grp["base_ae"],
            width,
            label="Baseline MAE",
            color="#94a3b8",
        )
        ax3.bar(
            x_env + width / 2,
            env_grp["hybr_ae"],
            width,
            label="Hybrid MAE",
            color="#f59e0b",
        )
        ax3.set_xticks(x_env)
        ax3.set_xticklabels(
            ["In-Ground (Κήπος)", "Potted (Γλάστρα)"], fontsize=10
        )
        ax3.set_ylabel("Mean Absolute Error (Days)", fontsize=10)
        ax3.set_title(
            "Error: Pot vs In-Ground Environment",
            fontsize=11,
            fontweight="bold",
        )
        ax3.legend()

        plt.tight_layout()
        save_path = os.path.join(output_dir, "category_error_breakdown.png")
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[Plots Generated] Saved category breakdown to: {save_path}")

    @staticmethod
    def plot_ground_hydrology_profile(
        df: pd.DataFrame, output_dir: str = "reports/figures"
    ) -> None:
        """Οπτικοποίηση υδρολογικής απόκρισης του ανοιχτού εδάφους (In-Ground Hydraulics)."""
        ground_df = df[df["planting_environment"] == "in_ground"].copy()
        if ground_df.empty:
            return

        os.makedirs(output_dir, exist_ok=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), dpi=150)

        # 1. Επίδραση Τύπου Εδάφους στο Διάστημα Ποτίσματος
        soil_order = ["sandy_coastal", "rocky_chalky", "balanced_loam", "clay_heavy"]
        existing_soils = [s for s in soil_order if s in ground_df["soil_type"].unique()]
        soil_means = ground_df.groupby("soil_type")["actual_days"].mean().reindex(existing_soils)

        colors = ["#f59e0b", "#94a3b8", "#10b981", "#6366f1"][:len(soil_means)]
        ax1.bar(soil_means.index, soil_means.values, color=colors, width=0.55)
        ax1.set_ylabel("Mean Watering Interval (Days)", fontsize=10)
        ax1.set_title(
            "In-Ground Watering Interval by Soil Type (TAW)",
            fontsize=11,
            fontweight="bold",
        )
        for i, val in enumerate(soil_means.values):
            ax1.text(i, val + 0.4, f"{val:.1f}d", ha="center", fontsize=9, fontweight="bold")

        # 2. Επίδραση Οργανικής Κάλυψης (Mulching) ανά Εποχή
        summer_ground = ground_df[ground_df["month"].isin([6, 7, 8])]
        if not summer_ground.empty:
            mulch_summary = summer_ground.groupby("has_mulch")["actual_days"].mean()
            labels = ["Χωρίς Mulch", "Με Mulch (Φλοιός/Άχυρο)"]
            vals = [mulch_summary.get(0.0, 0), mulch_summary.get(1.0, 0)]

            ax2.bar(labels, vals, color=["#cbd5e1", "#0284c7"], width=0.45)
            ax2.set_ylabel("Mean Summer Interval (Days)", fontsize=10)
            ax2.set_title(
                "Summer Evaporation Reduction via Mulching",
                fontsize=11,
                fontweight="bold",
            )
            for i, val in enumerate(vals):
                ax2.text(i, val + 0.3, f"{val:.1f}d", ha="center", fontsize=9, fontweight="bold")
            if vals[0] > 0:
                saving_pct = ((vals[1] - vals[0]) / vals[0]) * 100
                ax2.annotate(
                    f"+{saving_pct:.1f}% παράταση υγρασίας",
                    xy=(1, vals[1]),
                    xytext=(0.5, vals[1] + 1.2),
                    arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.2),
                    fontsize=9,
                    fontweight="bold",
                    color="#0f172a",
                )

        plt.tight_layout()
        save_path = os.path.join(output_dir, "ground_hydrology_profile.png")
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[Plots Generated] Saved ground hydrology profile to: {save_path}")

    @staticmethod
    def plot_fertilizer_summary(
        df: pd.DataFrame, output_dir: str = "reports/figures"
    ) -> None:
        """Οπτικοποίηση κατανομής αποφάσεων λίπανσης & δικλείδων ασφαλείας."""
        if "fertilizer_reason" not in df.columns:
            return

        os.makedirs(output_dir, exist_ok=True)
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2), dpi=150)

        # 1. Κατανομή Αιτιών Απόφασης (Safety Blocks vs Due vs Garden Windows)
        reason_counts = df["fertilizer_reason"].value_counts()
        labels_map = {
            "cycle_reached": "Εγκρίθηκε Γλάστρα (Cycle)",
            "waiting_cycle": "Αναμονή Κύκλου (Γλάστρα)",
            "seasonal_window_open": "Εποχικό Παράθυρο (Κήπος)",
            "seasonal_pause": "Αναστολή Εποχής (Κήπος)",
            "heat_stress_lock": "Μπλοκάρισμα: Καύσωνας (>33°C)",
            "winter_rest": "Μπλοκάρισμα: Χειμώνας",
            "dormancy_freeze": "Μπλοκάρισμα: Λήθαργος",
        }
        labels = [labels_map.get(k, k) for k in reason_counts.index]
        colors = [
            "#10b981", "#0284c7", "#60a5fa", "#cbd5e1",
            "#ef4444", "#a855f7", "#f59e0b"
        ][: len(reason_counts)]

        ax1.pie(
            reason_counts,
            labels=labels,
            autopct="%1.1f%%",
            startangle=140,
            colors=colors,
            wedgeprops={"edgecolor": "white", "linewidth": 1.5},
            textprops={"fontsize": 8.5},
        )
        ax1.set_title(
            "Fertilizer Decisions & Safety Locks (Pot & Garden)",
            fontsize=11,
            fontweight="bold",
        )

        # 2. Λίπανση συναρτήσει Θερμοκρασίας
        bins = [10, 20, 28, 33, 40]
        temp_labels = ["10-20°C", "20-28°C", "28-33°C", ">33°C (Stress)"]
        df_temp = df.copy()
        df_temp["temp_bin"] = pd.cut(
            df_temp["current_temp_celsius"], bins=bins, labels=temp_labels
        )
        fert_by_temp = (
            df_temp.groupby("temp_bin", observed=False)["should_fertilize"]
            .mean()
            .fillna(0.0)
            * 100.0
        )

        bar_colors = ["#38bdf8", "#22c55e", "#eab308", "#ef4444"]
        ax2.bar(
            temp_labels,
            fert_by_temp.values,
            color=bar_colors,
            edgecolor="none",
            width=0.55,
        )
        ax2.set_ylabel("% Feed Allowed", fontsize=10)
        ax2.set_title(
            "Fertilization Rate vs Ambient Temperature",
            fontsize=11,
            fontweight="bold",
        )
        ax2.set_ylim(0, max(fert_by_temp.max() * 1.25, 25))
        for i, val in enumerate(fert_by_temp.values):
            ax2.text(
                i,
                val + 1.0,
                f"{val:.1f}%",
                ha="center",
                fontsize=9,
                fontweight="bold",
            )

        plt.tight_layout()
        save_path = os.path.join(output_dir, "fertilizer_decision_analysis.png")
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[Plots Generated] Saved fertilizer analysis to: {save_path}")


class AccuracyVisualizer:
    @staticmethod
    def plot_tolerance_accuracy(
        actual_days: pd.Series,
        baseline_pred: pd.Series,
        hybrid_pred: pd.Series,
        output_dir: str = "reports/figures",
        max_tolerance_days: float = 2.5,
    ) -> None:
        os.makedirs(output_dir, exist_ok=True)

        baseline_errors = np.abs(actual_days - baseline_pred)
        hybrid_errors = np.abs(actual_days - hybrid_pred)

        tolerances = np.linspace(0.0, max_tolerance_days, 150)
        n_samples = len(actual_days)

        baseline_acc = [
            (np.sum(baseline_errors <= t) / n_samples) * 100 for t in tolerances
        ]
        hybrid_acc = [
            (np.sum(hybrid_errors <= t) / n_samples) * 100 for t in tolerances
        ]

        plt.figure(figsize=(9, 5.5), dpi=150)
        plt.plot(
            tolerances,
            hybrid_acc,
            label="Hybrid Engine (Physics + ML)",
            color="#0284c7",
            lw=2.5,
        )
        plt.plot(
            tolerances,
            baseline_acc,
            label="Physics Baseline Only",
            color="#94a3b8",
            lw=2.0,
            linestyle="--",
        )

        for tol_mark, name in [(0.5, "12 hours"), (1.0, "1 full day")]:
            idx = np.abs(tolerances - tol_mark).argmin()
            h_val = hybrid_acc[idx]
            b_val = baseline_acc[idx]

            plt.scatter(
                [tol_mark, tol_mark],
                [b_val, h_val],
                color=["#64748b", "#0284c7"],
                zorder=5,
            )
            plt.axvline(tol_mark, color="#cbd5e1", linestyle=":", lw=1.0)
            plt.annotate(
                f"±{name}: {h_val:.1f}% vs {b_val:.1f}%",
                xy=(tol_mark, h_val),
                xytext=(tol_mark + 0.08, h_val - 7),
                arrowprops=dict(arrowstyle="->", color="#0284c7", lw=1.2),
                fontsize=9,
                fontweight="bold",
                color="#0f172a",
            )

        plt.title(
            "Cumulative Prediction Accuracy vs Tolerance Window (REC Curve)",
            fontsize=12,
            fontweight="bold",
            pad=12,
        )
        plt.xlabel("Acceptable Error Margin (± Days)", fontsize=10)
        plt.ylabel("Accuracy (% of predictions within margin)", fontsize=10)
        plt.xlim(0, max_tolerance_days)
        plt.ylim(0, 105)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.legend(loc="lower right", frameon=True, fontsize=10)

        save_path = os.path.join(output_dir, "tolerance_accuracy_curve.png")
        plt.savefig(save_path, bbox_inches="tight")
        plt.close()
        print(f"[Accuracy Plot Generated] Saved to: {save_path}")