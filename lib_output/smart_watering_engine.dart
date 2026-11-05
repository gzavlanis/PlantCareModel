// AUTO-GENERATED HYBRID ENGINE V2 (WATERING & FERTILIZER)
// Generated automatically by Python training pipeline - DO NOT EDIT MANUALLY

import 'dart:math' as math;

/// Αποτέλεσμα αξιολόγησης ανάγκης λίπανσης
enum FertilizerStatus {
  recommended,
  notNeededYet,
  blockedHeatStress,
  blockedDormancy,
  blockedWinterRest,
}

class FertilizerDecision {
  final FertilizerStatus status;
  final bool shouldFertilize;
  final int wateringsRemaining;
  final double dilutionRate;
  final String recommendedNpkType;
  final String userMessage;

  const FertilizerDecision({
    required this.status,
    required this.shouldFertilize,
    required this.wateringsRemaining,
    required this.dilutionRate,
    required this.recommendedNpkType,
    required this.userMessage,
  });
}

class SmartFertilizerEngine {
  static FertilizerDecision evaluate({
    required String plantType,
    required String soilType,
    required int wateringsSinceLastFeed,
    required double currentTempCelsius,
    bool isDormant = false,
    int? currentMonth,
  }) {
    final month = currentMonth ?? DateTime.now().month;

    // 1. Αυστηρή διακοπή σε λήθαργο
    if (isDormant) {
      return const FertilizerDecision(
        status: FertilizerStatus.blockedDormancy,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Το φυτό βρίσκεται σε λήθαργο. Η λίπανση απαγορεύεται.',
      );
    }

    // 2. Heat Stress Lock (αποφυγή εγκαύματος σε καύσωνα)
    if (currentTempCelsius >= 33.0) {
      return const FertilizerDecision(
        status: FertilizerStatus.blockedHeatStress,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Υψηλή θερμοκρασία (>33°C). Αποφύγετε τη λίπανση λόγω θερμικού στρες.',
      );
    }

    // 3. Χειμερινή παύση (Δεκέμβριος - Φεβρουάριος)
    if ((month == 12 || month == 1 || month == 2) && plantType != 'foliage_tropical') {
      return const FertilizerDecision(
        status: FertilizerStatus.blockedWinterRest,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Χειμερινή περίοδος ανάπαυσης. Δεν συνιστάται λίπανση.',
      );
    }

    // 4. Υπολογισμός απαραίτητων ποτισμάτων
    int baseRequired = 3;
    if (plantType == 'succulent_cactus') baseRequired = 4;
    else if (plantType == 'foliage_tropical' || plantType == 'flowering_bulb') baseRequired = 2;

    int soilMod = 0;
    if (soilType == 'inorganic_succulent' || soilType == 'bark_orchid') soilMod = -1;
    else if (soilType == 'peat_heavy') soilMod = 1;

    final target = (baseRequired + soilMod).clamp(1, 6);
    final isDue = wateringsSinceLastFeed >= target;
    final remaining = (target - wateringsSinceLastFeed).clamp(0, target);

    String npk = 'balanced';
    double dilution = 0.5;

    if (plantType == 'flowering_bulb' || plantType == 'succulent_cactus') {
      npk = 'high_potassium';
      dilution = 0.5;
    } else if (plantType == 'foliage_tropical') {
      npk = 'balanced_or_nitrogen';
      dilution = 0.75;
    }

    if (isDue) {
      return FertilizerDecision(
        status: FertilizerStatus.recommended,
        shouldFertilize: true,
        wateringsRemaining: 0,
        dilutionRate: dilution,
        recommendedNpkType: npk,
        userMessage: 'Ώρα για λίπανση! Χρησιμοποιήστε ${npk == 'high_potassium' ? 'λίπασμα πλούσιο σε Κάλιο' : 'ισόρροπο λίπασμα'} σε αραίωση $dilution.',
      );
    } else {
      return FertilizerDecision(
        status: FertilizerStatus.notNeededYet,
        shouldFertilize: false,
        wateringsRemaining: remaining,
        dilutionRate: 0.0,
        recommendedNpkType: npk,
        userMessage: 'Επόμενη λίπανση σε $remaining ${remaining == 1 ? "πότισμα" : "ποτίσματα"}.',
      );
    }
  }
}

class SmartWateringEngine {
  static const double intercept = 0.353073;

  static const Map<String, double> numMeans = {
    'base_interval': 7.778266,
    'mean_et0': 3.751781,
    'pot_volume_liters': 9.416959,
    'day_length_hours': 12.421850,
    'heat_x_terracotta': 0.950455,
    'volume_x_peat': 2.499373,
    'succulent_x_shade': 0.042366
  };

  static const Map<String, double> numScales = {
    'base_interval': 3.232661,
    'mean_et0': 1.462811,
    'pot_volume_liters': 4.909627,
    'day_length_hours': 1.632730,
    'heat_x_terracotta': 1.790971,
    'volume_x_peat': 4.881756,
    'succulent_x_shade': 0.201422
  };

  static const Map<String, double> weights = {
    'base_interval': -0.011569,
    'mean_et0': -0.000085,
    'pot_volume_liters': -0.000947,
    'day_length_hours': 0.015877,
    'heat_x_terracotta': -0.289281,
    'volume_x_peat': 0.847038,
    'succulent_x_shade': 0.353964,
    'plant_type_foliage_tropical': -0.008606,
    'plant_type_standard_houseplant': -0.061721,
    'plant_type_succulent_cactus': -0.037557,
    'plant_type_woody_bonsai': -0.034031,
    'pot_type_glazed_ceramic': -0.012477,
    'pot_type_plastic': -0.001686,
    'pot_type_terracotta': 0.448581,
    'soil_type_bark_orchid': 0.034542,
    'soil_type_inorganic_succulent': 0.018116,
    'soil_type_peat_heavy': -0.668087,
    'location_type_indoor_low_light': -0.002285,
    'location_type_outdoor_shade': -0.011556,
    'location_type_outdoor_sun': 0.056628
  };

  static double predictResidual({
    required double baseInterval,
    required double meanEt0,
    required double potVolumeLiters,
    required double dayLengthHours,
    required String plantType,
    required String potType,
    required String soilType,
    required String locationType,
  }) {
    double delta = intercept;

    // Υπολογισμός των στοχευμένων αλληλεπιδράσεων (Zero runtime cost)
    final heatXTerracotta = potType == 'terracotta' ? meanEt0 : 0.0;
    final volumeXPeat = soilType == 'peat_heavy' ? potVolumeLiters : 0.0;
    final isShady = locationType == 'outdoor_shade' || locationType == 'indoor_low_light';
    final succulentXShade = (plantType == 'succulent_cactus' && isShady) ? 1.0 : 0.0;

    final rawNums = <String, double>{
      'base_interval': baseInterval,
      'mean_et0': meanEt0,
      'pot_volume_liters': potVolumeLiters,
      'day_length_hours': dayLengthHours,
      'heat_x_terracotta': heatXTerracotta,
      'volume_x_peat': volumeXPeat,
      'succulent_x_shade': succulentXShade,
    };

    rawNums.forEach((key, val) {
      final mean = numMeans[key] ?? 0.0;
      final scale = numScales[key] ?? 1.0;
      delta += ((val - mean) / scale) * (weights[key] ?? 0.0);
    });

    delta += weights['plant_type_' + plantType] ?? 0.0;
    delta += weights['pot_type_' + potType] ?? 0.0;
    delta += weights['soil_type_' + soilType] ?? 0.0;
    delta += weights['location_type_' + locationType] ?? 0.0;

    return delta;
  }

  static int calculateNextIntervalDays({
    required double baseInterval,
    required String plantType,     // 'succulent_cactus', 'foliage_tropical', 'flowering_bulb', 'woody_bonsai', 'standard_houseplant'
    required String potType,       // 'terracotta', 'plastic', 'glazed_ceramic', 'fabric'
    required String soilType,      // 'inorganic_succulent', 'bark_orchid', 'balanced_potting', 'peat_heavy'
    required String locationType,  // 'outdoor_sun', 'outdoor_shade', 'indoor_bright', 'indoor_low_light'
    required double meanEt0,
    required double potVolumeLiters,
    double dayLengthHours = 12.0,
    bool isDormant = false,
  }) {
    if (isDormant) {
      return (baseInterval * 3.8).round().clamp(1, 45);
    }

    // 1. Crop Coefficient (Kc)
    double kc = 0.90;
    if (plantType == 'succulent_cactus') kc = 0.35;
    else if (plantType == 'foliage_tropical') kc = 1.05;
    else if (plantType == 'flowering_bulb') kc = 0.85;
    else if (plantType == 'woody_bonsai') kc = 0.75;

    // 2. Pot & Soil Multipliers
    double cPot = 1.0;
    if (potType == 'terracotta') cPot = 0.72;
    else if (potType == 'glazed_ceramic') cPot = 1.08;
    else if (potType == 'fabric') cPot = 0.60;

    double cSoil = 1.0;
    if (soilType == 'inorganic_succulent') cSoil = 0.65;
    else if (soilType == 'bark_orchid') cSoil = 0.72;
    else if (soilType == 'peat_heavy') cSoil = 1.35;

    double cLoc = 1.0;
    if (locationType == 'outdoor_sun') cLoc = 0.65;
    else if (locationType == 'outdoor_shade') cLoc = 1.10;
    else if (locationType == 'indoor_low_light') cLoc = 1.50;

    // 3. Weather & Physical Dynamics
    final effectiveEt0 = math.max(meanEt0, 0.7);
    final etc = kc * effectiveEt0;
    final cWeather = 3.0 / etc;
    final photoperiodFactor = math.sqrt(dayLengthHours / 12.0);
    final volumeFactor = math.pow(potVolumeLiters / 4.0, 0.28).toDouble();

    final baseline = (baseInterval * cPot * cSoil * cLoc * (cWeather / photoperiodFactor) * volumeFactor)
        .clamp(1.0, 45.0);

    // 4. ML Residual Correction
    final residual = predictResidual(
      baseInterval: baseInterval,
      meanEt0: effectiveEt0,
      potVolumeLiters: potVolumeLiters,
      dayLengthHours: dayLengthHours,
      plantType: plantType,
      potType: potType,
      soilType: soilType,
      locationType: locationType,
    );

    return (baseline + residual).round().clamp(1, 45);
  }
}
