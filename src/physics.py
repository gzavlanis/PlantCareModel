"""Physics Engine V2: Ενσωμάτωση Kc, μη-γραμμικού υδραυλικού ρυθμού και κανόνων λίπανσης."""

import numpy as np
from src.config import (
    PLANT_KC,
    POT_MULTIPLIERS,
    SOIL_MULTIPLIERS,
    LOCATION_MULTIPLIERS,
    FERTILIZER_BASE_WATERINGS,
    FERTILIZER_SOIL_MODIFIER,
    MIN_WATERING_DAYS,
    MAX_WATERING_DAYS,
    ET0_REFERENCE_BASELINE,
)


class PhysicsWateringEngineV2:
    @staticmethod
    def calculate_baseline(
        base_interval: float,
        plant_type: str,
        pot_type: str,
        soil_type: str,
        location_type: str,
        mean_et0: float,
        pot_volume_liters: float,
        day_length_hours: float = 12.0,
        is_dormant: bool = False,
    ) -> float:
        if is_dormant:
            return float(
                np.clip(
                    base_interval * 3.8, MIN_WATERING_DAYS, MAX_WATERING_DAYS
                )
            )

        kc = PLANT_KC.get(plant_type, 0.90)
        c_pot = POT_MULTIPLIERS.get(pot_type, 1.0)
        c_soil = SOIL_MULTIPLIERS.get(soil_type, 1.0)
        c_loc = LOCATION_MULTIPLIERS.get(location_type, 1.0)

        # Πραγματική εξατμισοδιαπνοή φυτού (ETc)
        effective_et0 = max(mean_et0, 0.7)
        etc = kc * effective_et0

        # Καιρικός συντελεστής σε σχέση με το baseline (3.0 mm/day)
        c_weather = ET0_REFERENCE_BASELINE / etc

        # Φωτοπερίοδος (ώρες ημέρας: 9h χειμώνας, 15h καλοκαίρι σε μεσογειακό γεωγραφικό πλάτος)
        photoperiod_factor = (day_length_hours / 12.0) ** 0.5

        # Μη-γραμμική επίδραση όγκου γλάστρας:
        # Μικρή γλάστρα (2L) στεγνώνει γρήγορα (factor < 1.0), μεγάλη (12L) στεγνώνει αργά (factor > 1.0)
        volume_factor = (pot_volume_liters / 4.0) ** 0.28

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
        is_dormant: bool = False,
        month: int = 4,  # 1-12
    ) -> dict:
        """Εκτιμά αν επιτρέπεται και αν συστήνεται λίπανση στο τρέχον πότισμα."""
        # 1. Αυστηροί κανόνες απαγόρευσης (Safety Gates)
        if is_dormant:
            return {
                "should_fertilize": False,
                "reason": "dormancy_freeze",
                "dilution_rate": 0.0,
                "recommended_npk": "none",
            }

        # Heat stress lock: Πάνω από 33-34°C απαγορεύεται η λίπανση (κίνδυνος εγκαύματος)
        if current_temp_celsius >= 33.0:
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

        # 2. Υπολογισμός απαραίτητων ποτισμάτων
        base_req = FERTILIZER_BASE_WATERINGS.get(plant_type, 3)
        soil_mod = FERTILIZER_SOIL_MODIFIER.get(soil_type, 0)
        target_waterings = max(1, base_req + soil_mod)

        # 3. Έλεγχος αν συμπληρώθηκε ο κύκλος
        is_due = waterings_since_last_feed >= target_waterings

        # 4. Επιλογή κατάλληλου NPK & αραίωσης (dilution)
        if plant_type == "flowering_bulb" or plant_type == "succulent_cactus":
            npk = "high_potassium"  # π.χ. 7-10-42 ή χαμηλού αζώτου
            dilution = 0.5  # 50% της δοσολογίας (μισή δόση)
        elif plant_type == "foliage_tropical":
            npk = "balanced_or_nitrogen"  # π.χ. 20-20-20
            dilution = 0.75
        else:
            npk = "balanced"
            dilution = 0.5

        return {
            "should_fertilize": is_due,
            "reason": "cycle_reached" if is_due else "waiting_cycle",
            "waterings_remaining": max(
                0, target_waterings - waterings_since_last_feed
            ),
            "dilution_rate": dilution if is_due else 0.0,
            "recommended_npk": npk,
        }