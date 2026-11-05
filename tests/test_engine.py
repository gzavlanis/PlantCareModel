"""Έλεγχοι ορθότητας για το φυσικό μοντέλο και το ML pipeline."""

import pytest
from src.physics import PhysicsWateringEngine
from src.generator import SyntheticPlantDataGenerator
from src.trainer import ModelTrainer


def test_physics_baseline_bounds():
    # Έλεγχος ότι οι ημέρες δεν πέφτουν κάτω από 1 και δεν ξεπερνούν τις 45
    days = PhysicsWateringEngine.calculate_baseline(
        base_interval=7.0,
        pot_type='terracotta',
        soil_type='inorganic_succulent',
        location_type='outdoor_sun',
        mean_et0=5.5
    )
    assert 1.0 <= days <= 45.0


def test_dormancy_extension():
    normal_days = PhysicsWateringEngine.calculate_baseline(7.0, 'plastic', 'balanced_potting', 'indoor_bright', 2.0,
                                                           is_dormant=False)
    dormant_days = PhysicsWateringEngine.calculate_baseline(7.0, 'plastic', 'balanced_potting', 'indoor_bright', 2.0,
                                                            is_dormant=True)
    assert dormant_days > normal_days


def test_pipeline_training_and_gain():
    df = SyntheticPlantDataGenerator.generate(n_samples=500, seed=123)
    trainer = ModelTrainer(alpha=1.0)
    pipeline, metrics = trainer.train_and_evaluate(df)

    # Το υβριδικό μοντέλο πρέπει να έχει μικρότερο ή ίσο σφάλμα MAE από το raw baseline
    assert metrics['hybrid_mae'] <= metrics['raw_baseline_mae']
    assert pipeline is not None
