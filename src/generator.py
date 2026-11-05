"""Generator V2 με λεπτομερή προσομοίωση υδραυλικών αλληλεπιδράσεων και κύκλου λίπανσης."""

import numpy as np
import pandas as pd
from src.config import (
    PLANT_KC,
    POT_MULTIPLIERS,
    SOIL_MULTIPLIERS,
    LOCATION_MULTIPLIERS
)
from src.physics import PhysicsWateringEngineV2, FertilizerPhenologyEngine

class SyntheticPlantDataGeneratorV2:
    @staticmethod
    def _sample_realistic_base_interval(p_type: str) -> float:
        """Επιστρέφει ρεαλιστικό base interval ανά κατηγορία φυτού."""
        if p_type == 'succulent_cactus':
            return float(np.random.uniform(10.0, 18.0))
        elif p_type == 'foliage_tropical':
            return float(np.random.uniform(4.0, 8.5))
        elif p_type == 'flowering_bulb':
            return float(np.random.uniform(5.0, 9.0))
        elif p_type == 'woody_bonsai':
            return float(np.random.uniform(3.5, 7.0))
        return float(np.random.uniform(6.0, 10.0))

    @staticmethod
    def generate(n_samples: int = 5000, seed: int = 42) -> pd.DataFrame:
        np.random.seed(seed)

        plant_types = list(PLANT_KC.keys())
        pots = list(POT_MULTIPLIERS.keys())
        soils = list(SOIL_MULTIPLIERS.keys())
        locs = list(LOCATION_MULTIPLIERS.keys())

        records = []
        for _ in range(n_samples):
            p_type = np.random.choice(plant_types)
            base_interval = SyntheticPlantDataGeneratorV2._sample_realistic_base_interval(p_type)
            pot = np.random.choice(pots)
            soil = np.random.choice(soils)
            loc = np.random.choice(locs)
            pot_volume = np.random.uniform(0.8, 18.0)

            # 1. Συνεπής εποχικότητα (Seasonality coherence)
            month = int(np.random.randint(1, 13))

            # Χειμώνας (Δεκ, Ιαν, Φεβ)
            if month in [12, 1, 2]:
                day_length = np.random.uniform(9.0, 10.5)
                temp_celsius = np.random.uniform(12.0, 19.0)
                et0 = np.random.uniform(0.9, 2.2)
                is_dormant = True if p_type in ['succulent_cactus', 'flowering_bulb'] else False
            # Καλοκαίρι (Ιουν, Ιουλ, Αυγ)
            elif month in [6, 7, 8]:
                day_length = np.random.uniform(13.8, 15.0)
                temp_celsius = np.random.uniform(27.0, 38.0)
                et0 = np.random.uniform(4.5, 6.8)
                is_dormant = False
            # Άνοιξη & Φθινόπωρο
            else:
                day_length = np.random.uniform(11.0, 13.5)
                temp_celsius = np.random.uniform(18.0, 26.0)
                et0 = np.random.uniform(2.5, 4.5)
                is_dormant = False

            waterings_since_feed = int(np.random.randint(0, 7))

            # 2. Physics Baseline Ποτίσματος
            baseline_pred = PhysicsWateringEngineV2.calculate_baseline(
                base_interval=base_interval,
                plant_type=p_type,
                pot_type=pot,
                soil_type=soil,
                location_type=loc,
                mean_et0=et0,
                pot_volume_liters=pot_volume,
                day_length_hours=day_length,
                is_dormant=is_dormant
            )

            # 3. Μη-γραμμικές αλληλεπιδράσεις πραγματικότητας
            heat_wicking = -1.2 if (et0 > 5.2 and pot == 'terracotta') else 0.0
            deep_peat_stagnation = 2.1 if (pot_volume > 10.0 and soil == 'peat_heavy') else 0.0
            succulent_shade_lock = 1.8 if (p_type == 'succulent_cactus' and 'shade' in loc) else 0.0
            noise = np.random.normal(0.0, 0.25)

            actual_days = float(np.clip(
                baseline_pred + heat_wicking + deep_peat_stagnation + succulent_shade_lock + noise,
                1.0,
                45.0
            ))

            # Υπολογισμός Features Αλληλεπίδρασης (Interactions)
            heat_x_terracotta = et0 if pot == 'terracotta' else 0.0
            volume_x_peat = pot_volume if soil == 'peat_heavy' else 0.0
            succulent_x_shade = 1.0 if (p_type == 'succulent_cactus' and 'shade' in loc) else 0.0

            # 4. Αξιολόγηση Λίπανσης
            fert_eval = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
                plant_type=p_type,
                soil_type=soil,
                waterings_since_last_feed=waterings_since_feed,
                current_temp_celsius=temp_celsius,
                is_dormant=is_dormant,
                month=month
            )

            records.append({
                # Features Ποτίσματος
                'plant_type': p_type,
                'pot_type': pot,
                'soil_type': soil,
                'location_type': loc,
                'base_interval': base_interval,
                'mean_et0': et0,
                'pot_volume_liters': pot_volume,
                'day_length_hours': day_length,
                'heat_x_terracotta': heat_x_terracotta,
                'volume_x_peat': volume_x_peat,
                'succulent_x_shade': succulent_x_shade,
                'is_dormant': 1 if is_dormant else 0,
                'baseline_prediction': baseline_pred,
                'actual_days': actual_days,
                'residual_target': actual_days - baseline_pred,

                # Χαρακτηριστικά Λίπανσης & Συνθηκών
                'current_temp_celsius': temp_celsius,
                'waterings_since_last_feed': waterings_since_feed,
                'month': month,
                'should_fertilize': fert_eval['should_fertilize'],
                'fertilizer_reason': fert_eval['reason'],
                'dilution_rate': fert_eval['dilution_rate'],
                'recommended_npk': fert_eval['recommended_npk']
            })

        return pd.DataFrame(records)