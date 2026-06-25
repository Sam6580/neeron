# NEERON Model Specifications

> Detailed design specifications for all five NEERON prediction models.
> Aligned with existing database schema, repositories, services, and API contracts.

---

## Model 1: PSI Predictor

### Purpose

Predicts the Physiological Stress Index (PSI) for individual tanks. The PSI is a composite score (0.00–10.00) that quantifies the overall environmental stress experienced by the fish population. It is the primary health metric displayed on the Farm Command Center dashboard and drives the majority of automated recommendations.

### Database Target

**Output table:** `psi_predictions`

| Column | Type | Description |
|---|---|---|
| `psi_score` | `NUMERIC(4,2)` | Composite stress index: 0.00 (optimal) → 10.00 (critical) |
| `stress_level` | `VARCHAR(50)` | Classification: `Optimal` \| `Mild Stress` \| `Moderate Stress` \| `Severe Stress` \| `Critical Stress` |
| `confidence` | `NUMERIC(5,4)` | Model confidence: 0.0000 → 1.0000 |
| `model_version_id` | `UUID` | FK → `model_versions.id` for MLOps traceability |

**Explainability table:** `psi_factors`

| Column | Type | Description |
|---|---|---|
| `factor_name` | `VARCHAR(100)` | `temperature` \| `dissolved_oxygen` \| `pH` \| `ammonia` \| `salinity` \| `stocking_density` |
| `contribution` | `NUMERIC(6,4)` | Signed SHAP-style contribution (positive = increases stress) |
| `importance_score` | `NUMERIC(6,4)` | Absolute feature importance weight ≥ 0.0000 |

### Input Features

| Feature | Source | Type | Rationale |
|---|---|---|---|
| `temperature` | `tank_environment_snapshots.temperature` | Continuous | Primary stress driver — optimal range species-dependent |
| `ph` | `tank_environment_snapshots.ph` | Continuous | Acidosis/alkalosis stress indicator |
| `dissolved_oxygen` | `tank_environment_snapshots.dissolved_oxygen` | Continuous | Hypoxia is the leading cause of acute aquaculture stress |
| `ammonia` | `tank_environment_snapshots.ammonia` | Continuous | Toxic at elevated concentrations; interacts with pH |
| `salinity` | `tank_environment_snapshots.salinity` | Continuous | Osmoregulatory stress outside species-optimal range |
| `turbidity` | `tank_environment_snapshots.turbidity` | Continuous | High turbidity reduces gill efficiency |
| `temp_rolling_mean_1h` | `ml_feature_store` (engineered) | Continuous | Captures thermal trend vs. instantaneous reading |
| `do_lag_15m` | `ml_feature_store` (engineered) | Continuous | DO recovery dynamics post-disturbance |
| `temp_do_interaction` | `ml_feature_store` (engineered) | Continuous | DO solubility is temperature-dependent — interaction captures this |

### Outputs

| Output | Range | Description |
|---|---|---|
| `psi_score` | 0.00 – 10.00 | Primary regression target |
| `stress_level` | 5 categories | Derived from psi_score via threshold mapping |
| `confidence` | 0.0 – 1.0 | Prediction uncertainty estimate |
| `factors[]` | Per-feature breakdown | XAI SHAP contribution for each input feature |

### Stress Level Thresholds

| PSI Score Range | Classification | Action Required |
|---|---|---|
| 0.00 – 1.50 | `Optimal` | No action |
| 1.51 – 3.00 | `Mild Stress` | Monitor |
| 3.01 – 5.00 | `Moderate Stress` | Attention required |
| 5.01 – 7.50 | `Severe Stress` | Immediate intervention |
| 7.51 – 10.00 | `Critical Stress` | Emergency response |

### Candidate Models

| Algorithm | Rationale | Expected Performance |
|---|---|---|
| **XGBoost** (primary) | Gradient-boosted trees excel at structured/tabular data with mixed feature importance; handles non-linear temperature-DO interaction natively | RMSE < 0.50, R² > 0.90 |
| **Random Forest** (baseline) | Ensemble averaging provides robust uncertainty estimates for the confidence output; less prone to overfitting on small datasets | RMSE < 0.65, R² > 0.85 |

### Evaluation Metrics

| Metric | Target | Description |
|---|---|---|
| RMSE | < 0.50 | Root Mean Square Error on held-out test set |
| MAE | < 0.35 | Mean Absolute Error — average magnitude of prediction errors |
| R² | > 0.90 | Coefficient of determination — variance explained by the model |

### Training Specification

| Parameter | Value |
|---|---|
| Training frequency | Weekly (Sunday 02:00 UTC) |
| Training window | Rolling 90-day feature window from `ml_feature_store` |
| Validation split | 80/10/10 (train/val/test) — temporal split, no shuffling |
| Feature store query | `feature_group IN ('telemetry', 'environmental', 'engineered')` |
| Data quality gate | Only features with associated `data_quality_checks.result = 'Pass'` |
| Retraining trigger | `model_health_metrics.accuracy < 0.85` for 3 consecutive evaluation windows |

### Existing Infrastructure Mapping

| Component | Location | Status |
|---|---|---|
| Output table | `psi_predictions` | Exists (hypertable, 7-day chunks) |
| XAI table | `psi_factors` | Exists (hypertable, 7-day chunks) |
| Repository | `PredictionRepository.get_latest_psi()` | Exists |
| Service | `PredictionService.get_latest_predictions()` | Exists |
| API | `GET /api/v1/predictions/disease` (includes PSI) | Exists |
| Model registry | `ai_models` + `model_versions` | Exists (no PSI model registered yet) |

---

## Model 2: Disease Risk Predictor

### Purpose

Predicts the probability of disease outbreaks across multiple pathogen types. Generates per-tank, per-disease risk scores that drive biosecurity alerts, quarantine workflows, and proactive treatment recommendations.

### Database Target

**Output table:** `disease_predictions`

| Column | Type | Description |
|---|---|---|
| `disease_name` | `VARCHAR(150)` | Pathogen/syndrome label (e.g., `Amoebic Gill Disease`, `Sea Lice Infestation`) |
| `risk_score` | `NUMERIC(4,2)` | Outbreak risk: 0.00 (negligible) → 10.00 (critical) |
| `confidence` | `NUMERIC(5,4)` | Model confidence: 0.0000 → 1.0000 |
| `forecast_days` | `INTEGER` | Prediction horizon: 7, 14, or 30 days |
| `confidence_low` | `NUMERIC(5,4)` | Lower bound of 90% confidence interval |
| `confidence_high` | `NUMERIC(5,4)` | Upper bound of 90% confidence interval |
| `model_version_id` | `UUID` | FK → `model_versions.id` |

### Input Features

| Feature | Source | Type | Rationale |
|---|---|---|---|
| `temperature` | `tank_environment_snapshots` | Continuous | Pathogen growth rate is temperature-dependent |
| `ammonia` | `tank_environment_snapshots` | Continuous | Elevated ammonia weakens immune response |
| `dissolved_oxygen` | `tank_environment_snapshots` | Continuous | Hypoxia increases disease susceptibility |
| `turbidity` | `tank_environment_snapshots` | Continuous | Pathogen-carrying particulate matter |
| `mortality_rate` | `tank_production_metrics` | Continuous | Elevated mortality is an early disease indicator |
| `water_quality_index` | `ml_feature_store` (engineered) | Continuous | Composite water quality degradation signal |
| `ammonia_velocity` | `ml_feature_store` (engineered) | Continuous | Rapid ammonia spikes precede disease events |
| `mortality_trend_7d` | `ml_feature_store` (engineered) | Continuous | Sustained mortality increase signals latent infection |
| `pathogen_history` | `biosecurity_records` (aggregated) | Categorical | Count of recent detections per pathogen type per tank |
| `biosecurity_status` | `biosecurity_records` (aggregated) | Categorical | Current biosecurity risk level for the tank |

### Outputs

| Output | Range | Description |
|---|---|---|
| `risk_score` | 0.00 – 10.00 | Per-disease outbreak probability (scaled) |
| `disease_name` | Free-text label | Which pathogen the prediction applies to |
| `confidence` | 0.0 – 1.0 | Prediction certainty |
| `forecast_days` | 7 / 14 / 30 | How far ahead the prediction looks |
| `confidence_low` / `confidence_high` | 0.0 – 1.0 | 90% CI bounds |

### Candidate Models

| Algorithm | Rationale | Expected Performance |
|---|---|---|
| **XGBoost** (primary) | Handles class imbalance (disease events are rare) via `scale_pos_weight`; captures non-linear interactions between water quality and pathogen history | F1 > 0.80, ROC-AUC > 0.90 |
| **LightGBM** (alternative) | Faster training with histogram-based splitting; native categorical feature support for `disease_name` | F1 > 0.78, ROC-AUC > 0.88 |

### Evaluation Metrics

| Metric | Target | Description |
|---|---|---|
| Precision | > 0.80 | Low false positive rate — avoid unnecessary biosecurity alerts |
| Recall | > 0.85 | High true positive rate — never miss an actual outbreak |
| F1 | > 0.80 | Harmonic mean balancing precision and recall |
| ROC-AUC | > 0.90 | Discrimination ability across all threshold settings |

### Training Specification

| Parameter | Value |
|---|---|
| Training frequency | Weekly (Sunday 03:00 UTC) |
| Training window | Rolling 180-day window (disease events are sparse) |
| Validation split | 80/10/10 temporal split |
| Class balancing | `scale_pos_weight` set to negative/positive ratio |
| Multi-output | One model per disease; independent training per `disease_name` |
| Data quality gate | Features with `data_quality_checks.result IN ('Pass', 'Suspect')` |

### Existing Infrastructure Mapping

| Component | Location | Status |
|---|---|---|
| Output table | `disease_predictions` | Exists (hypertable, 14-day chunks) |
| Pathogen catalog | `pathogens` | Exists (reference table) |
| Biosecurity records | `biosecurity_records` | Exists (hypertable) |
| Repository | `PredictionRepository.get_latest_disease_prediction()` | Exists |
| Service | `PredictionService.get_latest_predictions()` | Exists |
| API | `GET /api/v1/predictions/disease` | Exists |

---

## Model 3: Mortality Predictor

### Purpose

Forecasts the probability of elevated mortality events within 7, 14, or 30-day horizons. Serves as an early warning system that combines environmental stress (PSI), disease risk, water quality degradation, and growth trajectory anomalies to predict population losses before they occur.

### Database Target

**Output table:** `mortality_predictions`

| Column | Type | Description |
|---|---|---|
| `mortality_probability` | `NUMERIC(6,4)` | Fractional probability: 0.0000 → 1.0000 |
| `confidence` | `NUMERIC(5,4)` | Model confidence: 0.0000 → 1.0000 |
| `forecast_days` | `INTEGER` | Horizon: 7 \| 14 \| 30 (constrained by CHECK) |
| `confidence_low` | `NUMERIC(6,4)` | Lower bound of 90% CI |
| `confidence_high` | `NUMERIC(6,4)` | Upper bound of 90% CI |
| `model_version_id` | `UUID` | FK → `model_versions.id` |

### Input Features

| Feature | Source | Type | Rationale |
|---|---|---|---|
| `psi_ma_7d` | `ml_feature_store` (engineered) | Continuous | Sustained high PSI precedes mortality events |
| `water_quality_index` | `ml_feature_store` (engineered) | Continuous | Composite water quality degradation indicator |
| `mortality_rate` | `tank_production_metrics` | Continuous | Current mortality baseline |
| `mortality_trend_7d` | `ml_feature_store` (engineered) | Continuous | Is mortality accelerating or decelerating? |
| `growth_rate_daily` | `ml_feature_store` (engineered) | Continuous | Growth slowdown precedes stress-related mortality |
| `temperature` | `tank_environment_snapshots` | Continuous | Thermal extremes trigger mass mortality |
| `dissolved_oxygen` | `tank_environment_snapshots` | Continuous | Hypoxia is the primary acute mortality driver |
| `population` | `tank_production_metrics` | Continuous | Stocking density context (crowding stress) |
| `biomass_kg` | `tank_production_metrics` | Continuous | Biomass trajectory anomalies |

### Outputs

| Output | Range | Description |
|---|---|---|
| `mortality_probability` | 0.0 – 1.0 | Probability of elevated mortality in the forecast window |
| `confidence` | 0.0 – 1.0 | Prediction certainty |
| `forecast_days` | 7 / 14 / 30 | Prediction horizon |

### Candidate Models

| Algorithm | Rationale | Expected Performance |
|---|---|---|
| **Random Forest** (primary) | Robust to outliers and missing data; provides natural probability calibration via out-of-bag estimates | MAE < 0.08, RMSE < 0.12 |
| **XGBoost** (alternative) | Better at capturing mortality threshold effects (e.g., DO below 4 mg/L triggers rapid escalation) | MAE < 0.07, RMSE < 0.10 |

### Evaluation Metrics

| Metric | Target | Description |
|---|---|---|
| MAE | < 0.08 | Mean absolute probability error |
| RMSE | < 0.12 | Root mean square probability error |

### Training Specification

| Parameter | Value |
|---|---|
| Training frequency | Weekly (Sunday 04:00 UTC) |
| Training window | Rolling 180-day window |
| Validation split | 80/10/10 temporal split |
| Multi-horizon | Separate models trained for 7-day, 14-day, and 30-day forecasts |
| Cascade input | Accepts PSI and disease risk scores as features (model cascading) |

### Existing Infrastructure Mapping

| Component | Location | Status |
|---|---|---|
| Output table | `mortality_predictions` | Exists (hypertable, 14-day chunks) |
| Repository | `PredictionRepository.get_latest_mortality_prediction()` | Exists |
| Service | `PredictionService.get_latest_predictions()` | Exists |
| API | `GET /api/v1/predictions/mortality` | Exists |

---

## Model 4: Harvest Predictor

### Purpose

Projects the optimal harvest date, expected total biomass yield, and mean individual fish weight for each tank. Powers the Analytics dashboard harvest timeline widget and supports farm revenue planning.

### Database Target

**Output table:** `harvest_predictions`

| Column | Type | Description |
|---|---|---|
| `predicted_harvest_date` | `DATE` | Projected optimal harvest date |
| `projected_biomass` | `NUMERIC(12,2)` | Expected total live weight (kg) at harvest |
| `projected_mean_weight_g` | `NUMERIC(10,2)` | Projected mean individual fish weight (g) |
| `growth_rate_fcr` | `NUMERIC(4,2)` | FCR trajectory used in the growth model |
| `confidence` | `NUMERIC(5,4)` | Model confidence: 0.0000 → 1.0000 |
| `revenue_projection_usd` | `NUMERIC(15,2)` | Optional estimated gross revenue (when market data available) |
| `model_version_id` | `UUID` | FK → `model_versions.id` |

### Input Features

| Feature | Source | Type | Rationale |
|---|---|---|---|
| `biomass_kg` | `tank_production_metrics` | Continuous | Current biomass baseline for trajectory projection |
| `average_weight_g` | `tank_production_metrics` | Continuous | Individual growth tracking |
| `fcr` | `tank_production_metrics` | Continuous | Feed conversion efficiency dictates growth economics |
| `feed_consumption_kg` | `tank_production_metrics` | Continuous | Feed input volume |
| `population` | `tank_production_metrics` | Continuous | Stocking count for total yield calculation |
| `growth_rate_daily` | `ml_feature_store` (engineered) | Continuous | Daily weight gain trajectory |
| `biomass_trajectory` | `ml_feature_store` (engineered) | Continuous | 14-day linear trend slope |
| `fcr_deviation` | `ml_feature_store` (engineered) | Continuous | Efficiency deviation from species baseline |
| `water_quality_index` | `ml_feature_store` (engineered) | Continuous | Environmental quality affecting growth rate |
| `temperature` | `tank_environment_snapshots` | Continuous | Temperature drives metabolic rate and growth |

### Outputs

| Output | Range | Description |
|---|---|---|
| `predicted_harvest_date` | Calendar date | When the tank reaches target weight |
| `projected_biomass` | > 0 kg | Total expected yield |
| `projected_mean_weight_g` | > 0 g | Individual fish weight at harvest |
| `growth_rate_fcr` | > 0 | Feed conversion trajectory used |
| `revenue_projection_usd` | ≥ 0 USD | Market-price-based revenue estimate |

### Candidate Models

| Algorithm | Rationale | Expected Performance |
|---|---|---|
| **XGBoost** (primary) | Captures non-linear growth curve dynamics; handles seasonal effects through engineered date features | MAE < 3 days (date), MAPE < 5% (biomass) |
| **LightGBM** (alternative) | Efficient on large feature sets with many production metric rows per tank; faster iteration during experimentation | MAE < 4 days, MAPE < 6% |

### Evaluation Metrics

| Metric | Target | Description |
|---|---|---|
| MAE (date) | < 3 days | Average error in predicted harvest date |
| MAPE (biomass) | < 5% | Mean absolute percentage error in projected biomass |

### Training Specification

| Parameter | Value |
|---|---|
| Training frequency | Weekly (Sunday 05:00 UTC) |
| Training window | Rolling 365-day window (full grow-out cycles) |
| Validation split | 80/10/10 temporal split |
| Target variable construction | Actual harvest date and actual biomass from completed grow-out cycles |
| Minimum training data | At least 10 completed grow-out cycles per species |

### Existing Infrastructure Mapping

| Component | Location | Status |
|---|---|---|
| Output table | `harvest_predictions` | Exists (hypertable, 30-day chunks) |
| Repository | `PredictionRepository.get_latest_harvest_prediction()` | Exists |
| Service | `PredictionService.get_latest_predictions()` | Exists |
| API | `GET /api/v1/predictions/harvest` | Exists |

---

## Model 5: Hydrophone Intelligence

### Purpose

Analyzes fish behavior patterns from underwater acoustic signals captured by hydrophone sensors. The model evolves through three phases: statistical baselines (Phase 1), spectrogram-based classification (Phase 2), and transformer-based audio embeddings (Phase 3).

### Phase 1: Statistical Detection (Phase 15F Target)

Phase 1 uses threshold-based statistical methods only. No trained ML model.

**Current infrastructure:**
- `acoustic_db` and `bio_acoustic_sync` columns exist in `tank_environment_snapshots`
- `GET /api/v1/telemetry/acoustic` returns current readings with status classification
- `GET /api/v1/telemetry/acoustic/history` returns time-series with aggregated summaries
- `TelemetryService.get_acoustic_analytics_data()` computes `stability_score` from standard deviation

**Phase 1 capabilities:**
- Acoustic level monitoring (dB)
- Bio-acoustic sync confidence tracking (0–100%)
- Stability scoring based on standard deviation (pure math, no ML)
- Status classification: `Normal` (sync ≥ 85%), `Warning` (70–85%), `Critical` (< 70%)

### Phase 2: CNN Spectrogram Models (Future)

**Additional database requirements:**
- `ml_feature_store` with `feature_group = 'engineered'` and `feature_vector` storing spectrogram feature vectors
- No new tables required — `feature_vector` JSON column already supports multi-dimensional features

**Planned inputs:**

| Feature | Source | Type | Description |
|---|---|---|---|
| `acoustic_db` | `tank_environment_snapshots` | Continuous | Raw dB level |
| `bio_acoustic_sync` | `tank_environment_snapshots` | Continuous | Correlation confidence |
| `spectrogram_features` | `ml_feature_store.feature_vector` | Vector (JSON) | Mel-spectrogram feature representation |
| `frequency_bands` | `ml_feature_store.feature_vector` | Vector (JSON) | Energy distribution across frequency bands |

**Planned outputs:**

| Output | Range | Description |
|---|---|---|
| `feeding_activity_score` | 0.0 – 1.0 | Probability that fish are actively feeding |
| `stress_behavior_score` | 0.0 – 1.0 | Probability of stress-induced behavioral change |
| `behavior_confidence` | 0.0 – 1.0 | Model confidence in behavioral classification |
| `anomaly_probability` | 0.0 – 1.0 | Probability of anomalous acoustic pattern |

### Phase 3: Audio Transformers (Future)

**Additional inputs:**

| Feature | Type | Description |
|---|---|---|
| `audio_embeddings` | Vector (JSON) | Transformer-derived audio embedding vectors stored in `ml_feature_store.feature_vector` |

**Architecture:** Pre-trained audio transformer fine-tuned on aquaculture acoustic datasets; embedding vectors stored in `ml_feature_store.feature_vector` for downstream classification.

### Candidate Models by Phase

| Phase | Algorithm | Complexity | Expected F1 |
|---|---|---|---|
| Phase 1 | Statistical thresholds (z-score, moving average) | Low | N/A (deterministic) |
| Phase 2 | CNN on Mel-spectrograms | Medium | > 0.75 |
| Phase 3 | Audio Transformer (fine-tuned) | High | > 0.88 |

### Evaluation Metrics

| Metric | Target | Applicable Phase |
|---|---|---|
| F1 (behavior classification) | > 0.80 | Phase 2+ |
| ROC-AUC (anomaly detection) | > 0.85 | Phase 2+ |
| Stability Score accuracy | < 3% error | Phase 1 |

### Existing Infrastructure Mapping

| Component | Location | Status |
|---|---|---|
| Columns | `tank_environment_snapshots.acoustic_db`, `bio_acoustic_sync` | Exists (Phase 10.1) |
| Migration | `002_hydrophone_support.py` | Exists |
| Repository | `TelemetryRepository.get_latest_hydrophone_reading()` | Exists |
| Service | `TelemetryService.get_acoustic_activity()` | Exists |
| Service | `TelemetryService.get_acoustic_analytics_data()` | Exists |
| Service | `AiInsightService.build_acoustic_insight()` | Exists (placeholder) |
| API | `GET /api/v1/telemetry/acoustic` | Exists |
| API | `GET /api/v1/telemetry/acoustic/history` | Exists |
| Feature store | `ml_feature_store.feature_vector` (JSON) | Exists (ready for spectrograms) |
