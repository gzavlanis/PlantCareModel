"""Ρυθμίσεις, συντελεστές FAO-56 και βοτανικές παράμετροι V2."""

from typing import Dict, List

# Γενικές σταθερές αναφοράς & ορίων ασφαλείας
ET0_REFERENCE_BASELINE: float = 3.0  # mm/day (ουδέτερη τιμή άνοιξης/φθινοπώρου)
MIN_WATERING_DAYS: int = 1
MAX_WATERING_DAYS: int = 45

# Συντελεστής Καλλιέργειας (Crop Coefficient - Kc)
# Καθορίζει τη διαπνοή του φυλλώματος σε σχέση με το ET0 αναφοράς
PLANT_KC: Dict[str, float] = {
    'succulent_cactus': 0.35,   # CAM φωτοσύνθεση (ελάχιστη διαπνοή)
    'foliage_tropical': 1.05,   # Μεγάλη φυλλική επιφάνεια (Monstera, Ficus, Calathea)
    'flowering_bulb': 0.85,     # Βολβοί σε πλήρη ανάπτυξη
    'woody_bonsai': 0.75,       # Μικρογραφίες δέντρων, μέτρια διαπνοή
    'standard_houseplant': 0.90 # Τυπικά φυτά εσωτερικού χώρου
}

POT_MULTIPLIERS: Dict[str, float] = {
    'terracotta': 0.72,
    'plastic': 1.00,
    'glazed_ceramic': 1.08,
    'fabric': 0.60
}

SOIL_MULTIPLIERS: Dict[str, float] = {
    'inorganic_succulent': 0.65, # Ελαφρόπετρα, λάβα, περλίτης
    'bark_orchid': 0.72,
    'balanced_potting': 1.00,
    'peat_heavy': 1.35
}

LOCATION_MULTIPLIERS: Dict[str, float] = {
    'outdoor_sun': 0.65,
    'outdoor_shade': 1.10,
    'indoor_bright': 1.00,
    'indoor_low_light': 1.50
}

CATEGORICAL_FEATURES: List[str] = [
    'plant_type',
    'pot_type',
    'soil_type',
    'location_type'
]

NUMERICAL_FEATURES: List[str] = [
    'base_interval',
    'mean_et0',
    'pot_volume_liters',
    'day_length_hours',
    # Targeted Physical Interactions:
    'heat_x_terracotta',
    'volume_x_peat',
    'succulent_x_shade'
]

# --- Ρυθμίσεις Έξυπνης Λίπανσης ---
FERTILIZER_BASE_WATERINGS: Dict[str, int] = {
    'succulent_cactus': 4,      # Κάθε 4ο πότισμα
    'foliage_tropical': 2,      # Κάθε 2ο πότισμα
    'flowering_bulb': 2,        # Κάθε 2ο πότισμα στην περίοδο ανάπτυξης
    'woody_bonsai': 3,          # Κάθε 3ο πότισμα
    'standard_houseplant': 3    # Τυπικά κάθε 3ο πότισμα
}

FERTILIZER_SOIL_MODIFIER: Dict[str, int] = {
    'inorganic_succulent': -1,  # Γρήγορη έκπλυση -> πιο συχνά (αραιωμένο)
    'bark_orchid': -1,
    'balanced_potting': 0,
    'peat_heavy': +1            # Κατακράτηση αλάτων -> πιο αραιά
}

# Όριο θερμικού στρες για αναστολή λίπανσης
FERTILIZER_HEAT_STRESS_THRESHOLD: float = 33.0  # °C