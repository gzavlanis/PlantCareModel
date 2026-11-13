"""Module αντιστοίχισης ταξινομίας φυτών στις παραμέτρους της μηχανής FAO-56."""

import json
import os
from typing import Dict, Any

# Βασικοί κανόνες αντιστοίχισης ανά οικογένεια/γένος
TAXONOMY_RULES = {
    "succulent": {
        "plant_type": "succulent_cactus",
        "base_interval": 14.0,
        "default_soil": "inorganic_succulent",
        "default_pot": "terracotta",
        "kc_factor": 0.35,
    },
    "tropical": {
        "plant_type": "foliage_tropical",
        "base_interval": 7.0,
        "default_soil": "balanced_potting",
        "default_pot": "plastic",
        "kc_factor": 1.05,
    },
    "woody": {
        "plant_type": "woody_bonsai",
        "base_interval": 4.0,
        "default_soil": "balanced_potting",
        "default_pot": "glazed_ceramic",
        "kc_factor": 0.85,
    },
    "mediterranean": {
        "plant_type": "mediterranean_herb",
        "base_interval": 8.0,
        "default_soil": "balanced_loam",
        "default_pot": "terracotta",
        "kc_factor": 0.65,
    },
}


class PlantTaxonomyMapper:
    """Δημιουργεί τη βάση δεδομένων χαρακτηριστικών για το Flutter app."""

    @staticmethod
    def generate_species_database(labels_path: str, output_path: str) -> None:
        if not os.path.exists(labels_path):
            raise FileNotFoundError(f"Labels file not found: {labels_path}")

        with open(labels_path, "r", encoding="utf-8") as f:
            labels = [line.strip() for line in f if line.strip()]

        database: Dict[str, Any] = {}

        for label in labels:
            clean_name = label.replace("_", " ").lower()

            # Ευρετική αντιστοίχιση βάσει ονόματος (επεκτάσιμο με εξειδικευμένο λεξικό)
            if any(w in clean_name for w in ["cactus", "succulent", "aloe", "crassula", "sansevieria"]):
                profile = TAXONOMY_RULES["succulent"].copy()
            elif any(w in clean_name for w in ["ficus", "citrus", "olive", "bonsai", "acer"]):
                profile = TAXONOMY_RULES["woody"].copy()
            elif any(w in clean_name for w in ["lavender", "rosemary", "thyme", "oregano"]):
                profile = TAXONOMY_RULES["mediterranean"].copy()
            else:
                profile = TAXONOMY_RULES["tropical"].copy()

            profile["common_name"] = label.replace("_", " ").title()
            database[label] = profile

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(database, f, ensure_ascii=False, indent=2)

        print(f"[Taxonomy Mapper] Generated species DB for {len(database)} plants at: {output_path}")