"""Έλεγχοι ορθότητας για το φυσικό μοντέλο, το ML pipeline και τον κανόνα λίπανσης V2."""

import pytest
from src.physics import PhysicsWateringEngineV2, FertilizerPhenologyEngine
from src.generator import SyntheticPlantDataGeneratorV2
from src.trainer import ModelTrainerV2
from src.config import MIN_WATERING_DAYS, MAX_WATERING_DAYS

# =====================================================================
# 1. Έλεγχοι Φυσικού Μοντέλου Ποτίσματος (Physics Baseline V2)
# =====================================================================

def test_physics_baseline_bounds():
    """Έλεγχος ότι οι υπολογισμένες ημέρες τηρούν αυστηρά τα όρια [MIN_WATERING_DAYS, MAX_WATERING_DAYS]."""
    days = PhysicsWateringEngineV2.calculate_baseline(
        base_interval=7.0,
        plant_type='succulent_cactus',
        pot_type='terracotta',
        soil_type='inorganic_succulent',
        location_type='outdoor_sun',
        mean_et0=5.5,
        pot_volume_liters=2.5,
        day_length_hours=14.0,
        is_dormant=False
    )
    assert MIN_WATERING_DAYS <= days <= MAX_WATERING_DAYS


def test_dormancy_extension():
    """Έλεγχος ότι ο λήθαργος επιμηκύνει σημαντικά το διάστημα ποτίσματος (x3.8 κανόνας)."""
    normal_days = PhysicsWateringEngineV2.calculate_baseline(
        base_interval=7.0,
        plant_type='standard_houseplant',
        pot_type='plastic',
        soil_type='balanced_potting',
        location_type='indoor_bright',
        mean_et0=2.0,
        pot_volume_liters=4.0,
        is_dormant=False
    )
    dormant_days = PhysicsWateringEngineV2.calculate_baseline(
        base_interval=7.0,
        plant_type='standard_houseplant',
        pot_type='plastic',
        soil_type='balanced_potting',
        location_type='indoor_bright',
        mean_et0=2.0,
        pot_volume_liters=4.0,
        is_dormant=True
    )
    assert dormant_days > normal_days
    assert dormant_days == pytest.approx(min(7.0 * 3.8, float(MAX_WATERING_DAYS)), rel=1e-2)


def test_pot_volume_dynamics():
    """Μεγαλύτερος όγκος γλάστρας πρέπει να αυξάνει τις ημέρες αναμονής μεταξύ ποτισμάτων."""
    small_pot_days = PhysicsWateringEngineV2.calculate_baseline(
        base_interval=6.0,
        plant_type='foliage_tropical',
        pot_type='plastic',
        soil_type='balanced_potting',
        location_type='indoor_bright',
        mean_et0=3.0,
        pot_volume_liters=1.5
    )
    large_pot_days = PhysicsWateringEngineV2.calculate_baseline(
        base_interval=6.0,
        plant_type='foliage_tropical',
        pot_type='plastic',
        soil_type='balanced_potting',
        location_type='indoor_bright',
        mean_et0=3.0,
        pot_volume_liters=12.0
    )
    assert large_pot_days > small_pot_days

# =====================================================================
# 2. Έλεγχοι Δικλείδων Ασφαλείας Λίπανσης (Fertilizer Safety Gates)
# =====================================================================

def test_fertilizer_heat_stress_lock():
    """Σε θερμοκρασίες >= 33°C η λίπανση πρέπει να απαγορεύεται αυστηρά."""
    decision = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
        plant_type='foliage_tropical',
        soil_type='balanced_potting',
        waterings_since_last_feed=10,  # Έχει περάσει ο κύκλος
        current_temp_celsius=35.0,     # Καύσωνας
        is_dormant=False,
        month=7
    )
    assert decision['should_fertilize'] is False
    assert decision['reason'] == 'heat_stress_lock'
    assert decision['dilution_rate'] == 0.0


def test_fertilizer_dormancy_lock():
    """Σε κατάσταση ληθάργου η λίπανση απαγορεύεται ανεξαρτήτως ιστορικού ποτισμάτων."""
    decision = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
        plant_type='succulent_cactus',
        soil_type='inorganic_succulent',
        waterings_since_last_feed=8,
        current_temp_celsius=20.0,
        is_dormant=True,
        month=1
    )
    assert decision['should_fertilize'] is False
    assert decision['reason'] == 'dormancy_freeze'


def test_fertilizer_winter_rest():
    """Τον χειμώνα (μήνες 12, 1, 2) για μη-τροπικά φυτά η λίπανση αναστέλλεται."""
    decision = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
        plant_type='flowering_bulb',
        soil_type='balanced_potting',
        waterings_since_last_feed=5,
        current_temp_celsius=18.0,
        is_dormant=False,
        month=1  # Ιανουάριος
    )
    assert decision['should_fertilize'] is False
    assert decision['reason'] == 'winter_rest'


def test_fertilizer_cycle_approval():
    """Υπό κανονικές συνθήκες, μόλις συμπληρωθεί ο απαιτούμενος αριθμός ποτισμάτων δίνεται έγκριση."""
    decision = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
        plant_type='foliage_tropical',  # base required: 2
        soil_type='balanced_potting',   # modifier: 0 -> target: 2
        waterings_since_last_feed=2,
        current_temp_celsius=24.0,
        is_dormant=False,
        month=5  # Μάιος
    )
    assert decision['should_fertilize'] is True
    assert decision['reason'] == 'cycle_reached'
    assert decision['waterings_remaining'] == 0
    assert decision['dilution_rate'] > 0.0

# =====================================================================
# 3. Έλεγχοι Synthetic Generator & ML Training Pipeline
# =====================================================================

def test_generator_data_integrity():
    """Έλεγχος ότι ο generator παράγει όλες τις απαραίτητες στήλες και συνεπή δεδομένα."""
    df = SyntheticPlantDataGeneratorV2.generate(n_samples=200, seed=42)

    expected_cols = {
        'plant_type', 'pot_type', 'soil_type', 'location_type',
        'base_interval', 'mean_et0', 'pot_volume_liters', 'day_length_hours',
        'heat_x_terracotta', 'volume_x_peat', 'succulent_x_shade',
        'is_dormant', 'baseline_prediction', 'actual_days', 'residual_target',
        'current_temp_celsius', 'waterings_since_last_feed', 'month',
        'should_fertilize', 'fertilizer_reason'
    }
    assert expected_cols.issubset(df.columns)
    assert len(df) == 200
    assert df['actual_days'].min() >= MIN_WATERING_DAYS
    assert df['actual_days'].max() <= MAX_WATERING_DAYS


def test_pipeline_training_and_gain():
    """Το υβριδικό μοντέλο Huber με τα interactions πρέπει να προσφέρει καθαρή βελτίωση MAE."""
    df = SyntheticPlantDataGeneratorV2.generate(n_samples=1000, seed=123)
    trainer = ModelTrainerV2(alpha=0.5)
    pipeline, metrics = trainer.train_and_evaluate(df)

    assert pipeline is not None
    # Επιβεβαίωση θετικού κέρδους ακρίβειας
    assert metrics['hybrid_mae'] < metrics['raw_baseline_mae']
    assert metrics['improvement_pct'] > 0.0
    assert metrics['residual_r2'] > 0.30