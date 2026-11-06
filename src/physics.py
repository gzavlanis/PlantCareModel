"""Physics Engine V3: Ενοποιημένο υδρολογικό μοντέλο FAO-56 για Γλάστρα και Ανοιχτό Έδαφος/Κήπο."""

import numpy as np
from src.config import (
    PLANT_KC,
    POT_MULTIPLIERS,
    POTTED_SOIL_MULTIPLIERS,
    IN_GROUND_ROOT_DEPTH,
    GROUND_SOIL_TAW,
    DEPLETION_FRACTION_P,
    MULCH_EVAPORATION_SAVING,
    LOCATION_MULTIPLIERS,
    FERTILIZER_BASE_WATERINGS,
    FERTILIZER_SOIL_MODIFIER,
    FERTILIZER_HEAT_STRESS_THRESHOLD,
    MIN_WATERING_DAYS,
    MAX_WATERING_DAYS,
    ET0_REFERENCE_BASELINE,
)

class PhysicsWateringEngineV2:
    @staticmethod
    def calculate_baseline(
        base_interval: float,
        plant_type: str,
        planting_environment: str = "pot",  # 'pot' ή 'in_ground'
        pot_type: str = "plastic",           # Αγνοείται αν είναι 'in_ground'
        soil_type: str = "balanced_potting", # 'balanced_potting', 'balanced_loam', κλπ.
        location_type: str = "outdoor_sun",
        mean_et0: float = 3.0,
        pot_volume_liters: float = 4.0,      # Αγνοείται αν είναι 'in_ground'
        root_depth_meters: float = 0.40,     # Χρησιμοποιείται αν είναι 'in_ground'
        day_length_hours: float = 12.0,
        has_mulch: bool = False,
        is_dormant: bool = False,
    ) -> float:
        # 1. Απόλυτος κανόνας ληθάργου
        if is_dormant:
            dormant_mult = 3.8 if planting_environment == "pot" else 4.5
            return float(
                np.clip(
                    base_interval * dormant_mult,
                    MIN_WATERING_DAYS,
                    MAX_WATERING_DAYS,
                )
            )

        kc = PLANT_KC.get(plant_type, 0.90)
        c_loc = LOCATION_MULTIPLIERS.get(location_type, 1.0)
        effective_et0 = max(mean_et0, 0.7)

        # ---------------------------------------------------------
        # ΣΕΝΑΡΙΟ Α: ΑΝΟΙΧΤΟ ΕΔΑΦΟΣ / ΚΗΠΟΣ (In-Ground FAO-56 RAW)
        # ---------------------------------------------------------
        if planting_environment == "in_ground":
            zr = root_depth_meters if root_depth_meters > 0 else IN_GROUND_ROOT_DEPTH.get(plant_type, 0.40)
            taw = GROUND_SOIL_TAW.get(soil_type, 150.0)
            p = DEPLETION_FRACTION_P.get(plant_type, 0.45)

            # Readily Available Water (RAW σε mm διαθέσιμου νερού στο ριζόστρωμα)
            raw = p * taw * zr

            # Επίδραση mulching στην άμεση επιφανειακή εξάτμιση
            mulch_factor = (1.0 - MULCH_EVAPORATION_SAVING) if has_mulch else 1.0

            # Πραγματική κατανάλωση ETc ανά ημέρα
            etc = kc * effective_et0 * mulch_factor

            # Φωτοπερίοδος
            photoperiod_factor = (day_length_hours / 12.0) ** 0.35

            # Ημέρες εξάντλησης του RAW
            raw_estimate = (raw / max(etc, 0.2)) * c_loc / photoperiod_factor
            return float(np.clip(raw_estimate, MIN_WATERING_DAYS, MAX_WATERING_DAYS))

        # ---------------------------------------------------------
        # ΣΕΝΑΡΙΟ Β: ΓΛΑΣΤΡΑ / ΔΟΧΕΙΟ (Container Hydraulics)
        # ---------------------------------------------------------
        c_pot = POT_MULTIPLIERS.get(pot_type, 1.0)
        c_soil = POTTED_SOIL_MULTIPLIERS.get(soil_type, 1.0)

        etc = kc * effective_et0
        c_weather = ET0_REFERENCE_BASELINE / etc
        photoperiod_factor = (day_length_hours / 12.0) ** 0.5

        # Μη-γραμμική επίδραση όγκου γλάστρας
        volume_factor = (max(pot_volume_liters, 0.5) / 4.0) ** 0.28

        raw_estimate = (
            base_interval
            * c_pot
            * c_soil
            * c_loc
            * (c_weather / photoperiod_factor)
            * volume_factor
        )

        return float(np.clip(raw_estimate, MIN_WATERING_DAYS, MAX_WATERING_DAYS))


class FertilizerPhenologyEngine:
    @staticmethod
    def evaluate_fertilizer_readiness(
        plant_type: str,
        soil_type: str,
        waterings_since_last_feed: int,
        current_temp_celsius: float,
        planting_environment: str = "pot",
        is_dormant: bool = False,
        month: int = 4,  # 1-12
    ) -> dict:
        """Εκτιμά αν επιτρέπεται και αν συστήνεται λίπανση για γλάστρα ή κήπο."""
        # 1. Αυστηροί κανόνες ασφαλείας (Safety Gates)
        if is_dormant:
            return {
                "should_fertilize": False,
                "reason": "dormancy_freeze",
                "dilution_rate": 0.0,
                "recommended_npk": "none",
            }

        # Heat stress lock: Πάνω από 33°C απαγορεύεται η λίπανση (κίνδυνος εγκαύματος)
        if current_temp_celsius >= FERTILIZER_HEAT_STRESS_THRESHOLD:
            return {
                "should_fertilize": False,
                "reason": "heat_stress_lock",
                "dilution_rate": 0.0,
                "recommended_npk": "none",
            }

        # Χειμερινή παύση (Δεκέμβριος - Φεβρουάριος) για μη-τροπικά
        if month in [12, 1, 2] and plant_type not in ["foliage_tropical"]:
            return {
                "should_fertilize": False,
                "reason": "winter_rest",
                "dilution_rate": 0.0,
                "recommended_npk": "none",
            }

        # 2. Εξειδίκευση για Ανοιχτό Έδαφος / Κήπο (Εποχική λίπανση, όχι ανά πότισμα)
        if planting_environment == "in_ground":
            # Εποχικά παράθυρα λίπανσης εδάφους: Άνοιξη (Μαρ-Μάιος) & Φθινόπωρο (Σεπ-Οκτ)
            is_growing_season = month in [3, 4, 5, 9, 10]
            if not is_growing_season:
                return {
                    "should_fertilize": False,
                    "reason": "seasonal_pause",
                    "waterings_remaining": 0,
                    "dilution_rate": 0.0,
                    "recommended_npk": "none",
                }

            # Επιλογή NPK για έδαφος
            if month in [9, 10] or plant_type in ["flowering_bulb", "succulent_cactus"]:
                npk = "high_potassium"  # Ενίσχυση ριζών/αντοχής στο κρύο
            elif plant_type == "foliage_tropical":
                npk = "balanced_or_nitrogen"
            else:
                npk = "balanced"

            return {
                "should_fertilize": True,
                "reason": "seasonal_window_open",
                "waterings_remaining": 0,
                "dilution_rate": 1.0,  # Στο έδαφος εφαρμόζεται κανονική δόση βραδείας αποδέσμευσης
                "recommended_npk": npk,
            }

        # 3. Ροή για Γλάστρα (Κύκλος ποτισμάτων)
        base_req = FERTILIZER_BASE_WATERINGS.get(plant_type, 3)
        soil_mod = FERTILIZER_SOIL_MODIFIER.get(soil_type, 0)
        target_waterings = max(1, base_req + soil_mod)

        is_due = waterings_since_last_feed >= target_waterings

        if plant_type in ["flowering_bulb", "succulent_cactus"]:
            npk = "high_potassium"
            dilution = 0.5
        elif plant_type == "foliage_tropical":
            npk = "balanced_or_nitrogen"
            dilution = 0.75
        else:
            npk = "balanced"
            dilution = 0.5

        return {
            "should_fertilize": is_due,
            "reason": "cycle_reached" if is_due else "waiting_cycle",
            "waterings_remaining": max(0, target_waterings - waterings_since_last_feed),
            "dilution_rate": dilution if is_due else 0.0,
            "recommended_npk": npk,
        }