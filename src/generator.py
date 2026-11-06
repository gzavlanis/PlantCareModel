"""Generator V3 με ταυτόχρονη προσομοίωση Γλάστρας (Container) και Ανοιχτού Εδάφους (In-Ground FAO-56)."""

import numpy as np
import pandas as pd
from src.config import (
    PLANT_KC,
    POT_MULTIPLIERS,
    POTTED_SOIL_MULTIPLIERS,
    GROUND_SOIL_TAW,
    IN_GROUND_ROOT_DEPTH,
    LOCATION_MULTIPLIERS,
    MIN_WATERING_DAYS,
    MAX_WATERING_DAYS
)
from src.physics import PhysicsWateringEngineV2, FertilizerPhenologyEngine


class SyntheticPlantDataGeneratorV2:
    @staticmethod
    def _sample_realistic_base_interval(p_type: str) -> float:
        """Επιστρέφει ρεαλιστικό base interval ανά κατηγορία φυτού (για γλάστρα)."""
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
        potted_pots = list(POT_MULTIPLIERS.keys())
        potted_soils = list(POTTED_SOIL_MULTIPLIERS.keys())
        ground_soils = list(GROUND_SOIL_TAW.keys())
        all_locs = list(LOCATION_MULTIPLIERS.keys())
        outdoor_locs = ['outdoor_sun', 'outdoor_shade']

        records = []
        for _ in range(n_samples):
            p_type = np.random.choice(plant_types)
            base_interval = SyntheticPlantDataGeneratorV2._sample_realistic_base_interval(p_type)

            # 1. Επιλογή περιβάλλοντος: 65% Γλάστρα, 35% Ανοιχτό Έδαφος/Κήπος
            env = np.random.choice(['pot', 'in_ground'], p=[0.65, 0.35])

            if env == 'pot':
                pot = np.random.choice(potted_pots)
                soil = np.random.choice(potted_soils)
                loc = np.random.choice(all_locs)
                pot_volume = float(np.random.uniform(0.8, 18.0))
                root_depth = 0.0
                has_mulch_val = 0.0
            else:
                pot = 'none_ground'
                soil = np.random.choice(ground_soils)
                loc = np.random.choice(outdoor_locs)  # Το έδαφος είναι πάντα εξωτερικό
                pot_volume = 0.0
                base_depth = IN_GROUND_ROOT_DEPTH.get(p_type, 0.40)
                root_depth = float(np.clip(np.random.normal(base_depth, 0.08), 0.15, 1.20))
                has_mulch_val = float(np.random.choice([0.0, 1.0], p=[0.45, 0.55]))

            # 2. Συνεπής εποχικότητα (Seasonality coherence)
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

            # 3. Physics Baseline Ποτίσματος
            baseline_pred = PhysicsWateringEngineV2.calculate_baseline(
                base_interval=base_interval,
                plant_type=p_type,
                planting_environment=env,
                pot_type=pot,
                soil_type=soil,
                location_type=loc,
                mean_et0=et0,
                pot_volume_liters=pot_volume,
                root_depth_meters=root_depth,
                day_length_hours=day_length,
                has_mulch=(has_mulch_val == 1.0),
                is_dormant=is_dormant
            )

            # 4. Μη-γραμμικές αλληλεπιδράσεις πραγματικότητας
            if env == 'pot':
                heat_wicking = -1.2 if (et0 > 5.2 and pot == 'terracotta') else 0.0
                deep_peat_stagnation = 2.1 if (pot_volume > 10.0 and soil == 'peat_heavy') else 0.0
                ground_stagnation = 0.0
                sandy_drain = 0.0
            else:
                heat_wicking = 0.0
                deep_peat_stagnation = 0.0
                # Στο έδαφος: Βαριά αργιλώδη χώματα τον χειμώνα κρατούν νερό ακόμα περισσότερο
                ground_stagnation = 2.8 if (soil == 'clay_heavy' and et0 < 2.5) else 0.0
                # Παραθαλάσσια αμμώδη με δυνατό καύσωνα στεγνώνουν ταχύτερα
                sandy_drain = -1.5 if (soil == 'sandy_coastal' and et0 > 5.5) else 0.0

            succulent_shade_lock = 1.8 if (p_type == 'succulent_cactus' and 'shade' in loc) else 0.0
            noise = np.random.normal(0.0, 0.25)

            actual_days = float(np.clip(
                baseline_pred + heat_wicking + deep_peat_stagnation + ground_stagnation + sandy_drain + succulent_shade_lock + noise,
                MIN_WATERING_DAYS,
                MAX_WATERING_DAYS
            ))

            # 5. Υπολογισμός Features Αλληλεπίδρασης (Interactions)
            heat_x_terracotta = et0 if (env == 'pot' and pot == 'terracotta') else 0.0
            volume_x_peat = pot_volume if (env == 'pot' and soil == 'peat_heavy') else 0.0
            succulent_x_shade = 1.0 if (p_type == 'succulent_cactus' and 'shade' in loc) else 0.0
            ground_x_clay = 1.0 if (env == 'in_ground' and soil == 'clay_heavy') else 0.0

            # 6. Αξιολόγηση Λίπανσης
            fert_eval = FertilizerPhenologyEngine.evaluate_fertilizer_readiness(
                plant_type=p_type,
                soil_type=soil,
                waterings_since_last_feed=waterings_since_feed,
                current_temp_celsius=temp_celsius,
                planting_environment=env,
                is_dormant=is_dormant,
                month=month
            )

            records.append({
                # Features Ποτίσματος
                'plant_type': p_type,
                'planting_environment': env,
                'pot_type': pot,
                'soil_type': soil,
                'location_type': loc,
                'base_interval': base_interval,
                'mean_et0': et0,
                'pot_volume_liters': pot_volume,
                'root_depth_meters': root_depth,
                'day_length_hours': day_length,
                'has_mulch': has_mulch_val,
                'heat_x_terracotta': heat_x_terracotta,
                'volume_x_peat': volume_x_peat,
                'succulent_x_shade': succulent_x_shade,
                'ground_x_clay': ground_x_clay,
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