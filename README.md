# PlantCareModel

# 🌱 Smart Watering & Phenology Engine (V3)

> **Physics-Informed Hybrid Irrigation & Fertilization Engine for Containers & Open Soil.**  
> *Autonomous, offline-first edge deployment for Flutter with $O(1)$ runtime.*

---

## 📌 Executive Summary

Most consumer plant care applications fail in practice because they rely on **static calendars** (e.g., *"water every 7 days"*), ignoring container porosity, root depth, real-time evapotranspiration, and substrate dynamics. The inevitable result is either **root rot** from overwatering or **root burn** from mistimed fertilization.

**Smart Watering Engine V3** resolves this fundamental limitation by combining:

1. **Rigorous Hydrological Principles (FAO-56):** Complete $RAW / ET_c$ mass balance for in-ground garden beds alongside non-linear hydraulic depletion curves for containerized plantings.
2. **Machine Learning Residual Modeling (Huber Regressor):** Learns complex, non-linear physical interactions (terracotta thermal wicking, peat waterlogging, winter clay stagnation).
3. **Smart Safety Phenology Engine:** Automatically enforces biological safety gates, including heat stress locks ($>33^\circ\text{C}$), dormancy overrides, and seasonal garden fertilization windows.
4. **Zero-Latency Edge Export:** Automatically compiles the trained pipeline into a self-contained, standalone **Dart class** with zero external ML dependencies or cloud requirements.

---

## 🏛️ System Architecture

```
                     ┌───────────────────────────────────────────────┐
                     │          User & Environmental Inputs          │
                     │  (Soil, Pot Material, Volume, ET₀, Sunlight)  │
                     └──────────────────────┬────────────────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
         [ Planting: Container ]                         [ Planting: In-Ground ]
         • Non-linear Pot Volume (V^0.28)                • Readily Available Water:
         • Porosity (Terracotta vs Glazed)                 RAW = p · TAW · Zr
         • Substrate (Peat, Inorganic, Bark)             • Mulching barrier (-30% Evap)
                    │                                               │
                    └───────────────────────┬───────────────────────┘
                                            ▼
                           ┌─────────────────────────────────┐
                           │      FAO-56 Physics Baseline    │
                           │       y_base = calculate()      │
                           └────────────────┬────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │    Huber Residual Regressor     │
                           │     y_delta = ML(Features)      │
                           └────────────────┬────────────────┘
                                            │
                                            ▼
                           ┌─────────────────────────────────┐
                           │   Hybrid Interval = Base + ML   │
                           │        (MAE ~ 0.309 days)       │
                           └─────────────────────────────────┘
```

---

## 📊 Benchmark & Evaluation

The pipeline was trained and validated on a synthetic dataset of 5,000 realistic Mediterranean and temperate climate profiles:

| Metric | Raw Physics Baseline | Hybrid Engine (Physics + ML) | Delta / Gain |
| :--- | :---: | :---: | :---: |
| **Mean Absolute Error (Overall)** | `0.443 days` | **`0.309 days`** (~7.4 hours) | **+30.22%** |
| **Container / Pot MAE** | `0.448 days` | **`0.312 days`** | Balanced |
| **In-Ground Garden MAE** | `0.435 days` | **`0.303 days`** | Balanced |
| **Residual $R^2$ Score** | — | **`0.573`** | Robust Fit |

> **Key Takeaway:** The hybrid engine delivers virtually identical error metrics across containerized (`0.312d`) and garden (`0.303d`) plantings, proving zero architectural bias across environments.

---

## 🔬 Visualizations & Diagnostic Reports

All analytical charts are generated automatically and saved under `reports/figures/`:

```
reports/figures/
├── model_performance_summary.png       # Parity plot, Residual error distribution & Top-12 weights
├── tolerance_accuracy_curve.png        # REC Curve (Cumulative accuracy vs tolerance window)
├── category_error_breakdown.png        # MAE breakdown: Plant category, Container material & Environment
├── ground_hydrology_profile.png        # In-ground TAW response & Mulching evaporation reduction
├── fertilizer_decision_analysis.png    # Safety lock distribution & Temperature-gated feeding rates
├── pipeline_architecture.png           # Flowchart diagram of ColumnTransformer & Regressor stages
└── pipeline_diagram.html               # Interactive scikit-learn pipeline inspection file
```

---

## 🗂️ Repository Structure

```
PlantCareModel/
├── src/
│   ├── config.py           # Agronomic constants (Kc, TAW, Mulch, P) & feature schema
│   ├── physics.py          # FAO-56 hydrological calculation & Phenology Safety Engine
│   ├── generator.py        # Coherent synthetic data generator (65% Pots / 35% In-Ground)
│   ├── trainer.py          # Scikit-learn Pipeline (StandardScaler, OneHot, HuberRegressor)
│   ├── visualizer.py       # High-resolution Matplotlib visualizer & HTML exporter
│   └── exporter.py         # Automated code generation for standalone Dart (V3)
├── lib_output/
│   └── smart_watering_engine.dart  # Production-ready Flutter Dart engine
├── reports/
│   └── figures/            # Generated high-resolution diagnostic charts
├── main.py                 # Central execution pipeline orchestrator
├── requirements.txt
└── README.md
```

---

## 🚀 Quickstart

### 1. Environment Setup

```bash
git clone https://github.com/your-username/smart-plant-care-engine.git
cd smart-plant-care-engine
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Training, Reporting & Code Generation

```bash
# On Windows, running with UTF-8 mode enabled is recommended
python -X utf8 main.py
```

Executing `main.py` runs through all stages:
1. Generates 5,000 synthetic multi-environment plant profiles.
2. Fits the `HuberRegressor` pipeline to learn residual variance.
3. Exports diagnostic plots to `reports/figures/`.
4. Transpiles and generates `lib_output/smart_watering_engine.dart`.

---

## 📱 Flutter Integration (Edge Dart Usage)

The generated class in `lib_output/smart_watering_engine.dart` has **zero external package dependencies** and executes in pure Dart:

```dart
import 'smart_watering_engine.dart';

void main() {
  // 1. Calculate Next Watering Interval (In-Ground Garden with Mulch)
  final wateringDays = SmartWateringEngine.calculateNextIntervalDays(
    baseInterval: 7.0,
    plantType: 'woody_bonsai',
    plantingEnvironment: 'in_ground',
    soilType: 'balanced_loam',
    locationType: 'outdoor_sun',
    meanEt0: 4.2,
    rootDepthMeters: 0.50,
    dayLengthHours: 14.0,
    hasMulch: true,
  );

  print('Next watering in: $wateringDays days');

  // 2. Evaluate Fertilizer Safety Gate (Heat Stress Check)
  final fertDecision = SmartFertilizerEngine.evaluate(
    plantType: 'foliage_tropical',
    soilType: 'balanced_potting',
    wateringsSinceLastFeed: 3,
    currentTempCelsius: 34.5, // High temperature trigger
    plantingEnvironment: 'pot',
  );

  if (fertDecision.shouldFertilize) {
    print('Fertilization Approved: ${fertDecision.userMessage}');
  } else {
    // Will output: Suspended due to heat stress (>33°C)
    print('Fertilization Suspended: ${fertDecision.userMessage}');
  }
}
```

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).
