"""Trainer V3: Huber Regression Pipeline για εκτίμηση του υπολειμματικού σφάλματος (Γλάστρα & Έδαφος)."""

from typing import Tuple, Dict, Any
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.linear_model import HuberRegressor
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, r2_score

from src.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES


class ModelTrainerV2:
    def __init__(self, alpha: float = 0.5, epsilon: float = 1.35):
        self.alpha = alpha
        self.epsilon = epsilon

    def build_pipeline(self) -> Pipeline:
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), NUMERICAL_FEATURES),
                ('cat', OneHotEncoder(drop='first', sparse_output=False, handle_unknown='ignore'), CATEGORICAL_FEATURES)
            ]
        )

        return Pipeline(steps=[
            ('preprocessor', preprocessor),
            ('regressor', HuberRegressor(alpha=self.alpha, epsilon=self.epsilon, max_iter=600))
        ])

    def train_and_evaluate(self, df: pd.DataFrame) -> Tuple[Pipeline, Dict[str, Any]]:
        # Φιλτράρουμε: εκπαιδεύουμε το ML μόνο στα ενεργά φυτά
        active_df = df[df['is_dormant'] == 0].copy() if 'is_dormant' in df.columns else df.copy()

        feature_columns = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
        X = active_df[feature_columns]
        y = active_df['residual_target']

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        pipeline = self.build_pipeline()
        pipeline.fit(X_train, y_train)

        # Αξιολόγηση στο συνολικό Test Set ενεργών φυτών
        actual_test = active_df.loc[X_test.index, 'actual_days']
        base_test = active_df.loc[X_test.index, 'baseline_prediction']
        raw_mae = mean_absolute_error(actual_test, base_test)

        predicted_residuals = pipeline.predict(X_test)
        hybrid_predictions = base_test + predicted_residuals
        hybrid_mae = mean_absolute_error(actual_test, hybrid_predictions)
        r2 = r2_score(y_test, predicted_residuals)

        # Επιμέρους έλεγχος ακρίβειας ανά περιβάλλον (Pot vs In-Ground)
        pot_mask = X_test['planting_environment'] == 'pot'
        ground_mask = X_test['planting_environment'] == 'in_ground'

        metrics = {
            'raw_baseline_mae': float(raw_mae),
            'hybrid_mae': float(hybrid_mae),
            'improvement_pct': float(((raw_mae - hybrid_mae) / raw_mae) * 100),
            'residual_r2': float(r2),
            'pot_hybrid_mae': float(mean_absolute_error(actual_test[pot_mask], hybrid_predictions[pot_mask])) if pot_mask.any() else None,
            'ground_hybrid_mae': float(mean_absolute_error(actual_test[ground_mask], hybrid_predictions[ground_mask])) if ground_mask.any() else None,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test)
        }

        return pipeline, metrics