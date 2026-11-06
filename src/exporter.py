"""Exporter V3: Παραγωγή αυτοτελούς Dart κλάσης V3 (Watering & Fertilizer για Γλάστρα & Κήπο)."""

import os
from sklearn.pipeline import Pipeline
from src.config import CATEGORICAL_FEATURES, NUMERICAL_FEATURES


class DartCodeExporterV2:
    @staticmethod
    def export(
        pipeline: Pipeline,
        output_path: str = "lib_output/smart_watering_engine.dart",
    ) -> None:
        regressor = pipeline.named_steps["regressor"]
        preprocessor = pipeline.named_steps["preprocessor"]

        scaler = preprocessor.named_transformers_["num"]
        means = scaler.mean_
        scales = scaler.scale_

        cat_encoder = preprocessor.named_transformers_["cat"]
        encoded_cat = list(
            cat_encoder.get_feature_names_out(CATEGORICAL_FEATURES)
        )
        all_features = NUMERICAL_FEATURES + encoded_cat

        weights = regressor.coef_
        intercept = regressor.intercept_

        means_str = ",\n".join(
            [f"    '{k}': {v:.6f}" for k, v in zip(NUMERICAL_FEATURES, means)]
        )
        scales_str = ",\n".join(
            [f"    '{k}': {v:.6f}" for k, v in zip(NUMERICAL_FEATURES, scales)]
        )
        weights_str = ",\n".join(
            [f"    '{k}': {v:.6f}" for k, v in zip(all_features, weights)]
        )

        dart_content = f"""// AUTO-GENERATED HYBRID ENGINE V3 (WATERING & FERTILIZER - POT & IN-GROUND)
// Generated automatically by Python training pipeline - DO NOT EDIT MANUALLY

import 'dart:math' as math;

/// Αποτέλεσμα αξιολόγησης ανάγκης λίπανσης
enum FertilizerStatus {{
  recommended,
  notNeededYet,
  windowOpenGarden,
  blockedSeasonalGarden,
  blockedHeatStress,
  blockedDormancy,
  blockedWinterRest,
}}

class FertilizerDecision {{
  final FertilizerStatus status;
  final bool shouldFertilize;
  final int wateringsRemaining;
  final double dilutionRate;
  final String recommendedNpkType;
  final String userMessage;

  const FertilizerDecision({{
    required this.status,
    required this.shouldFertilize,
    required this.wateringsRemaining,
    required this.dilutionRate,
    required this.recommendedNpkType,
    required this.userMessage,
  }});
}}

class SmartFertilizerEngine {{
  static FertilizerDecision evaluate({{
    required String plantType,
    required String soilType,
    required int wateringsSinceLastFeed,
    required double currentTempCelsius,
    String plantingEnvironment = 'pot', // 'pot' ή 'in_ground'
    bool isDormant = false,
    int? currentMonth,
  }}) {{
    final month = currentMonth ?? DateTime.now().month;

    // 1. Αυστηρή διακοπή σε λήθαργο
    if (isDormant) {{
      return const FertilizerDecision(
        status: FertilizerStatus.blockedDormancy,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Το φυτό βρίσκεται σε λήθαργο. Η λίπανση απαγορεύεται.',
      );
    }}

    // 2. Heat Stress Lock (αποφυγή εγκαύματος σε καύσωνα)
    if (currentTempCelsius >= 33.0) {{
      return const FertilizerDecision(
        status: FertilizerStatus.blockedHeatStress,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Υψηλή θερμοκρασία (>33°C). Αποφύγετε τη λίπανση λόγω θερμικού στρες.',
      );
    }}

    // 3. Χειμερινή παύση (Δεκέμβριος - Φεβρουάριος)
    if ((month == 12 || month == 1 || month == 2) && plantType != 'foliage_tropical') {{
      return const FertilizerDecision(
        status: FertilizerStatus.blockedWinterRest,
        shouldFertilize: false,
        wateringsRemaining: 0,
        dilutionRate: 0.0,
        recommendedNpkType: 'none',
        userMessage: 'Χειμερινή περίοδος ανάπαυσης. Δεν συνιστάται λίπανση.',
      );
    }}

    // 4. Εξειδίκευση για Ανοιχτό Έδαφος / Κήπο (Εποχική εφαρμογή)
    if (plantingEnvironment == 'in_ground') {{
      final isGrowingSeason = (month >= 3 && month <= 5) || (month == 9 || month == 10);
      if (!isGrowingSeason) {{
        return const FertilizerDecision(
          status: FertilizerStatus.blockedSeasonalGarden,
          shouldFertilize: false,
          wateringsRemaining: 0,
          dilutionRate: 0.0,
          recommendedNpkType: 'none',
          userMessage: 'Στο έδαφος δεν συνιστάται λίπανση αυτή την εποχή. Αναμονή για άνοιξη ή αρχές φθινοπώρου.',
        );
      }}

      String npk = 'balanced';
      if (month == 9 || month == 10 || plantType == 'flowering_bulb' || plantType == 'succulent_cactus') {{
        npk = 'high_potassium';
      }} else if (plantType == 'foliage_tropical') {{
        npk = 'balanced_or_nitrogen';
      }}

      return FertilizerDecision(
        status: FertilizerStatus.windowOpenGarden,
        shouldFertilize: true,
        wateringsRemaining: 0,
        dilutionRate: 1.0,
        recommendedNpkType: npk,
        userMessage: 'Κατάλληλη εποχή για οργανική ή κοκκώδη λίπανση εδάφους (${{npk == 'high_potassium' ? 'υψηλού Καλίου' : 'ισόρροπη'}}).',
      );
    }}

    // 5. Ροή για Γλάστρα (Κύκλος ποτισμάτων)
    int baseRequired = 3;
    if (plantType == 'succulent_cactus') baseRequired = 4;
    else if (plantType == 'foliage_tropical' || plantType == 'flowering_bulb') baseRequired = 2;

    int soilMod = 0;
    if (soilType == 'inorganic_succulent' || soilType == 'bark_orchid' || soilType == 'sandy_coastal') {{
      soilMod = -1;
    }} else if (soilType == 'peat_heavy' || soilType == 'clay_heavy') {{
      soilMod = 1;
    }}

    final target = (baseRequired + soilMod).clamp(1, 6);
    final isDue = wateringsSinceLastFeed >= target;
    final remaining = (target - wateringsSinceLastFeed).clamp(0, target);

    String npk = 'balanced';
    double dilution = 0.5;

    if (plantType == 'flowering_bulb' || plantType == 'succulent_cactus') {{
      npk = 'high_potassium';
      dilution = 0.5;
    }} else if (plantType == 'foliage_tropical') {{
      npk = 'balanced_or_nitrogen';
      dilution = 0.75;
    }}

    if (isDue) {{
      return FertilizerDecision(
        status: FertilizerStatus.recommended,
        shouldFertilize: true,
        wateringsRemaining: 0,
        dilutionRate: dilution,
        recommendedNpkType: npk,
        userMessage: 'Ώρα για λίπανση! Χρησιμοποιήστε ${{npk == 'high_potassium' ? 'λίπασμα πλούσιο σε Κάλιο' : 'ισόρροπο λίπασμα'}} σε αραίωση $dilution.',
      );
    }} else {{
      return FertilizerDecision(
        status: FertilizerStatus.notNeededYet,
        shouldFertilize: false,
        wateringsRemaining: remaining,
        dilutionRate: 0.0,
        recommendedNpkType: npk,
        userMessage: 'Επόμενη λίπανση σε $remaining ${{remaining == 1 ? "πότισμα" : "ποτίσματα"}}.',
      );
    }}
  }}
}}

class SmartWateringEngine {{
  static const double intercept = {intercept:.6f};

  static const Map<String, double> numMeans = {{
{means_str}
  }};

  static const Map<String, double> numScales = {{
{scales_str}
  }};

  static const Map<String, double> weights = {{
{weights_str}
  }};

  static double predictResidual({{
    required double baseInterval,
    required double meanEt0,
    required double potVolumeLiters,
    required double rootDepthMeters,
    required double dayLengthHours,
    required bool hasMulch,
    required String plantingEnvironment,
    required String plantType,
    required String potType,
    required String soilType,
    required String locationType,
  }}) {{
    double delta = intercept;

    final isPot = plantingEnvironment == 'pot';
    final heatXTerracotta = (isPot && potType == 'terracotta') ? meanEt0 : 0.0;
    final volumeXPeat = (isPot && soilType == 'peat_heavy') ? potVolumeLiters : 0.0;
    final isShady = locationType == 'outdoor_shade' || locationType == 'indoor_low_light';
    final succulentXShade = (plantType == 'succulent_cactus' && isShady) ? 1.0 : 0.0;
    final groundXClay = (!isPot && soilType == 'clay_heavy') ? 1.0 : 0.0;

    final rawNums = <String, double>{{
      'base_interval': baseInterval,
      'mean_et0': meanEt0,
      'pot_volume_liters': isPot ? potVolumeLiters : 0.0,
      'root_depth_meters': isPot ? 0.0 : rootDepthMeters,
      'day_length_hours': dayLengthHours,
      'has_mulch': hasMulch ? 1.0 : 0.0,
      'heat_x_terracotta': heatXTerracotta,
      'volume_x_peat': volumeXPeat,
      'succulent_x_shade': succulentXShade,
      'ground_x_clay': groundXClay,
    }};

    rawNums.forEach((key, val) {{
      final mean = numMeans[key] ?? 0.0;
      final scale = numScales[key] ?? 1.0;
      delta += ((val - mean) / scale) * (weights[key] ?? 0.0);
    }});

    delta += weights['plant_type_' + plantType] ?? 0.0;
    delta += weights['planting_environment_' + plantingEnvironment] ?? 0.0;
    delta += weights['pot_type_' + potType] ?? 0.0;
    delta += weights['soil_type_' + soilType] ?? 0.0;
    delta += weights['location_type_' + locationType] ?? 0.0;

    return delta;
  }}

  static int calculateNextIntervalDays({{
    required double baseInterval,
    required String plantType,
    String plantingEnvironment = 'pot', // 'pot' ή 'in_ground'
    String potType = 'plastic',
    String soilType = 'balanced_potting',
    String locationType = 'outdoor_sun',
    required double meanEt0,
    double potVolumeLiters = 4.0,
    double rootDepthMeters = 0.40,
    double dayLengthHours = 12.0,
    bool hasMulch = false,
    bool isDormant = false,
  }}) {{
    if (isDormant) {{
      final mult = plantingEnvironment == 'in_ground' ? 4.5 : 3.8;
      return (baseInterval * mult).round().clamp(1, 45);
    }}

    // 1. Συντελεστής Καλλιέργειας (Crop Coefficient - Kc)
    double kc = 0.90;
    if (plantType == 'succulent_cactus') kc = 0.35;
    else if (plantType == 'foliage_tropical') kc = 1.05;
    else if (plantType == 'flowering_bulb') kc = 0.85;
    else if (plantType == 'woody_bonsai') kc = 0.75;

    // 2. Τοποθεσία
    double cLoc = 1.0;
    if (locationType == 'outdoor_sun') cLoc = 0.65;
    else if (locationType == 'outdoor_shade') cLoc = 1.10;
    else if (locationType == 'indoor_low_light') cLoc = 1.50;

    final effectiveEt0 = math.max(meanEt0, 0.7);
    double baseline;

    if (plantingEnvironment == 'in_ground') {{
      // --- FAO-56 Υδρολογικός Υπολογισμός Εδάφους ---
      double taw = 150.0;
      if (soilType == 'sandy_coastal') taw = 80.0;
      else if (soilType == 'rocky_chalky') taw = 95.0;
      else if (soilType == 'clay_heavy') taw = 190.0;

      double p = 0.45;
      if (plantType == 'succulent_cactus') p = 0.70;
      else if (plantType == 'foliage_tropical') p = 0.35;
      else if (plantType == 'woody_bonsai') p = 0.55;

      final zr = rootDepthMeters > 0.0 ? rootDepthMeters : 0.40;
      final raw = p * taw * zr;
      final mulchFactor = hasMulch ? 0.70 : 1.0;
      final etc = kc * effectiveEt0 * mulchFactor;
      final photoperiodFactor = math.pow(dayLengthHours / 12.0, 0.35).toDouble();

      baseline = ((raw / math.max(etc, 0.2)) * cLoc / photoperiodFactor).clamp(1.0, 45.0);
    }} else {{
      // --- Υδραυλικός Υπολογισμός Γλάστρας / Δοχείου ---
      double cPot = 1.0;
      if (potType == 'terracotta') cPot = 0.72;
      else if (potType == 'glazed_ceramic') cPot = 1.08;
      else if (potType == 'fabric') cPot = 0.60;

      double cSoil = 1.0;
      if (soilType == 'inorganic_succulent') cSoil = 0.65;
      else if (soilType == 'bark_orchid') cSoil = 0.72;
      else if (soilType == 'peat_heavy') cSoil = 1.35;

      final etc = kc * effectiveEt0;
      final cWeather = 3.0 / etc;
      final photoperiodFactor = math.sqrt(dayLengthHours / 12.0);
      final volumeFactor = math.pow(math.max(potVolumeLiters, 0.5) / 4.0, 0.28).toDouble();

      baseline = (baseInterval * cPot * cSoil * cLoc * (cWeather / photoperiodFactor) * volumeFactor)
          .clamp(1.0, 45.0);
    }}

    // 3. ML Residual Correction
    final residual = predictResidual(
      baseInterval: baseInterval,
      meanEt0: effectiveEt0,
      potVolumeLiters: potVolumeLiters,
      rootDepthMeters: rootDepthMeters,
      dayLengthHours: dayLengthHours,
      hasMulch: hasMulch,
      plantingEnvironment: plantingEnvironment,
      plantType: plantType,
      potType: potType,
      soilType: soilType,
      locationType: locationType,
    );

    return (baseline + residual).round().clamp(1, 45);
  }}
}}
"""
        os.makedirs(
            os.path.dirname(output_path) if os.path.dirname(output_path) else ".",
            exist_ok=True,
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(dart_content)
        print(f"[Export V3 SUCCESS] Written to: {output_path}")