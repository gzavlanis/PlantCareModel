// AUTO-GENERATED HYBRID WATERING ENGINE
// Generated on build - DO NOT EDIT DIRECTLY

class SmartWateringEngine {
  static const double intercept = 1.1672702;

  static const Map<String, double> numMeans = {
    'base_interval': 8.9305284,
    'mean_et0': 3.7272745,
    'pot_volume_liters': 8.5695122,
    'baseline_prediction': 7.9329157
  };

  static const Map<String, double> numScales = {
    'base_interval': 2.8647622,
    'mean_et0': 1.6072951,
    'pot_volume_liters': 4.3357311,
    'baseline_prediction': 6.6796165
  };

  static const Map<String, double> weights = {
    'base_interval': 0.1327788,
    'mean_et0': -0.7222097,
    'pot_volume_liters': 0.6917787,
    'baseline_prediction': -0.3657980,
    'pot_type_glazed_ceramic': 0.1902005,
    'pot_type_plastic': 0.1084217,
    'pot_type_terracotta': 0.0219571,
    'soil_type_bark_orchid': -0.0757938,
    'soil_type_inorganic_succulent': -0.1147993,
    'soil_type_peat_heavy': 0.1202857,
    'location_type_indoor_low_light': 0.1767461,
    'location_type_outdoor_shade': -0.0490300,
    'location_type_outdoor_sun': -0.1732965
  };

  /// Υπολογίζει τη διόρθωση σφάλματος (residual) μέσω του γραμμικού μοντέλου
  static double predictResidual({
    required double baseInterval,
    required double meanEt0,
    required double potVolumeLiters,
    required double baselinePrediction,
    required String potType,
    required String soilType,
    required String locationType,
  }) {
    double delta = intercept;

    // Κανονικοποίηση αριθμητικών παραμέτρων
    final rawNums = <String, double>{
      'base_interval': baseInterval,
      'mean_et0': meanEt0,
      'pot_volume_liters': potVolumeLiters,
      'baseline_prediction': baselinePrediction,
    };

    rawNums.forEach((key, val) {
      final mean = numMeans[key] ?? 0.0;
      final scale = numScales[key] ?? 1.0;
      final normalized = (val - mean) / scale;
      delta += normalized * (weights[key] ?? 0.0);
    });

    // One-Hot ενεργοποίηση συντελεστών
    delta += weights['pot_type_' + potType] ?? 0.0;
    delta += weights['soil_type_' + soilType] ?? 0.0;
    delta += weights['location_type_' + locationType] ?? 0.0;

    return delta;
  }

  /// Κεντρική μέθοδος: Physics baseline + ML correction
  static int calculateNextIntervalDays({
    required double baseInterval,
    required String potType,
    required String soilType,
    required String locationType,
    required double meanEt0,
    required double potVolumeLiters,
    bool isDormant = false,
  }) {
    if (isDormant) {
      return (baseInterval * 3.5).round().clamp(1, 45);
    }

    // 1. Φυσικοί συντελεστές
    double cPot = 1.0;
    if (potType == 'terracotta') cPot = 0.75;
    else if (potType == 'glazed_ceramic') cPot = 1.05;
    else if (potType == 'fabric') cPot = 0.65;

    double cSoil = 1.0;
    if (soilType == 'inorganic_succulent') cSoil = 0.70;
    else if (soilType == 'bark_orchid') cSoil = 0.75;
    else if (soilType == 'peat_heavy') cSoil = 1.30;

    double cLoc = 1.0;
    if (locationType == 'outdoor_sun') cLoc = 0.70;
    else if (locationType == 'outdoor_shade') cLoc = 1.10;
    else if (locationType == 'indoor_low_light') cLoc = 1.45;

    final effectiveEt0 = meanEt0 < 0.8 ? 0.8 : meanEt0;
    final cWeather = 3.0 / effectiveEt0;

    final baseline = (baseInterval * cPot * cSoil * cLoc * cWeather).clamp(1.0, 45.0);

    // 2. ML Residual Correction
    final residual = predictResidual(
      baseInterval: baseInterval,
      meanEt0: effectiveEt0,
      potVolumeLiters: potVolumeLiters,
      baselinePrediction: baseline,
      potType: potType,
      soilType: soilType,
      locationType: locationType,
    );

    return (baseline + residual).round().clamp(1, 45);
  }
}
