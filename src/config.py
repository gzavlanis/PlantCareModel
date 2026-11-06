"""Ρυθμίσεις, συντελεστές FAO-56 και βοτανικές παράμετροι V3 (Γλάστρα & Κήπος/Έδαφος)."""

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
    'woody_bonsai': 0.75,       # Μικρογραφίες δέντρων, μεσογειακά ξυλώδη
    'standard_houseplant': 0.90 # Τυπικά φυτά εσωτερικού χώρου
}

# -------------------------------------------------------------
# 1. ΠΑΡΑΜΕΤΡΟΙ ΓΛΑΣΤΡΑΣ / ΔΟΧΕΙΟΥ (Container / Potted)
# -------------------------------------------------------------
POT_MULTIPLIERS: Dict[str, float] = {
    'terracotta': 0.72,
    'plastic': 1.00,
    'glazed_ceramic': 1.08,
    'fabric': 0.60
}

POTTED_SOIL_MULTIPLIERS: Dict[str, float] = {
    'inorganic_succulent': 0.65, # Ελαφρόπετρα, λάβα, περλίτης
    'bark_orchid': 0.72,
    'balanced_potting': 1.00,
    'peat_heavy': 1.35
}

# -------------------------------------------------------------
# 2. ΠΑΡΑΜΕΤΡΟΙ ΕΔΑΦΟΥΣ / ΚΗΠΟΥ (In-Ground FAO-56 Hydraulics)
# -------------------------------------------------------------
# Ενεργό βάθος ριζοστρώματος (Rooting Depth Zr σε μέτρα)
IN_GROUND_ROOT_DEPTH: Dict[str, float] = {
    'succulent_cactus': 0.20,
    'flowering_bulb': 0.30,
    'foliage_tropical': 0.40,
    'standard_houseplant': 0.40,
    'woody_bonsai': 0.85,       # Μεσογειακοί θάμνοι/δέντρα στο έδαφος (π.χ. ελιές, πεύκα, κυπαρίσσια)
}

# Total Available Water (TAW σε mm νερού ανά μέτρο βάθους ρίζας)
GROUND_SOIL_TAW: Dict[str, float] = {
    'sandy_coastal': 80.0,       # Παραθαλάσσια / αμμώδη / πολύ ελαφριά
    'rocky_chalky': 95.0,        # Βραχώδη / ασβεστολιθικά (τυπικά μεσογειακά πρανή)
    'balanced_loam': 150.0,      # Κηπόχωμα / ισορροπημένο κοκκινόχωμα
    'clay_heavy': 190.0          # Βαριά αργιλώδη
}

# Κλάσμα εξάντλησης νερού (Depletion Fraction p) πριν από υδατικό στρες
DEPLETION_FRACTION_P: Dict[str, float] = {
    'succulent_cactus': 0.70,   # Αντέχει μεγάλη εξάντληση
    'foliage_tropical': 0.35,   # Ευαίσθητο στην ξηρασία
    'flowering_bulb': 0.45,
    'woody_bonsai': 0.55,
    'standard_houseplant': 0.45
}

# Συντελεστής επίδρασης οργανικής κάλυψης (Mulching: φλοιός πεύκου, άχυρο, χαλίκι)
MULCH_EVAPORATION_SAVING: float = 0.30  # Μείωση επιφανειακών απωλειών κατά 30%

# -------------------------------------------------------------
# 3. ΠΕΡΙΒΑΛΛΟΝ ΚΑΙ ΤΟΠΟΘΕΣΙΑ
# -------------------------------------------------------------
LOCATION_MULTIPLIERS: Dict[str, float] = {
    'outdoor_sun': 0.65,
    'outdoor_shade': 1.10,
    'indoor_bright': 1.00,
    'indoor_low_light': 1.50
}

# -------------------------------------------------------------
# 4. FEATURES ΓΙΑ ΤΟ ML PIPELINE (Huber Regressor)
# -------------------------------------------------------------
CATEGORICAL_FEATURES: List[str] = [
    'plant_type',
    'planting_environment', # 'pot' ή 'in_ground'
    'pot_type',             # 'terracotta', 'plastic', κλπ. ή 'none_ground'
    'soil_type',            # Ενιαία λίστα υποστρωμάτων
    'location_type'
]

NUMERICAL_FEATURES: List[str] = [
    'base_interval',
    'mean_et0',
    'pot_volume_liters',    # 0.0 αν είναι στο έδαφος
    'root_depth_meters',    # Zr (π.χ. 0.2 - 0.85m)
    'day_length_hours',
    'has_mulch',            # 1.0 αν υπάρχει mulching, 0.0 αλλιώς
    # Targeted Physical Interactions:
    'heat_x_terracotta',    # Μηδέν στο έδαφος
    'volume_x_peat',        # Μηδέν στο έδαφος
    'succulent_x_shade',
    'ground_x_clay'         # Νέο interaction: αργιλώδες έδαφος σε συνθήκες χαμηλού ET0
]

# -------------------------------------------------------------
# 5. ΡΥΘΜΙΣΕΙΣ ΕΞΥΠΝΗΣ ΛΙΠΑΝΣΗΣ
# -------------------------------------------------------------
# Ρυθμός λίπανσης σε ΓΛΑΣΤΡΑ (ανά πόσα ποτίσματα)
FERTILIZER_BASE_WATERINGS: Dict[str, int] = {
    'succulent_cactus': 4,
    'foliage_tropical': 2,
    'flowering_bulb': 2,
    'woody_bonsai': 3,
    'standard_houseplant': 3
}

FERTILIZER_SOIL_MODIFIER: Dict[str, int] = {
    'inorganic_succulent': -1,
    'bark_orchid': -1,
    'balanced_potting': 0,
    'peat_heavy': +1,
    'sandy_coastal': -1,
    'rocky_chalky': 0,
    'balanced_loam': 0,
    'clay_heavy': +1
}

# Όριο θερμικού στρες για αναστολή λίπανσης
FERTILIZER_HEAT_STRESS_THRESHOLD: float = 33.0  # °C