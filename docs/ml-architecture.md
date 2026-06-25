# NEERON ML Architecture — End-to-End Pipeline Design

> Enterprise Precision Aquaculture Intelligence Platform
> Phase 15 Preparation — Architecture Documentation

---

## 1. System Overview

NEERON's ML system operates as a closed-loop intelligence pipeline. Sensor data enters through IoT telemetry streams, flows through feature engineering and quality validation, feeds into specialized prediction models, and produces actionable operational recommendations that are presented to farm operators. Operator feedback on those recommendations closes the loop, improving future model performance.

The architecture is designed around six foundational principles:

1. **Point-in-time correctness** — Feature timestamps record when observations occurred, not when computations ran, preventing data leakage during retraining.
2. **Full MLOps traceability** — Every prediction, insight, and recommendation links back to a specific model version through the chain: `AiModel → ModelVersion → Prediction → AiInsight → Recommendation`.
3. **TimescaleDB-native time-series** — All high-volume ML tables use composite primary keys `(id, time)` with hypertable partitioning for efficient time-range queries and automatic data lifecycle management.
4. **Additive evolution** — New models, features, and capabilities are added without modifying existing schema, APIs, or services.
5. **Infrastructure-first** — Database tables, repositories, services, and API endpoints are built before any training code, ensuring production readiness from day one.
6. **Human-in-the-loop** — Operators always have final authority over recommendations. The system learns from their acceptance, rejection, and effectiveness feedback.

---

## 2. End-to-End Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        NEERON ML Pipeline Architecture                       │
└──────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
  │   Sensors   │────▶│  Telemetry   │────▶│   Data Quality      │
  │  (IoT/MQTT) │     │  Hypertable  │     │   Validation        │
  └─────────────┘     └──────────────┘     └─────────┬───────────┘
                                                     │
                                                     │ Pass / Fail / Suspect
                                                     ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                     FEATURE ENGINEERING LAYER                            │
  │                                                                          │
  │  ┌───────────────────┐  ┌────────────────────┐  ┌────────────────────┐  │
  │  │ tank_environment_  │  │ tank_production_   │  │  ml_feature_store  │  │
  │  │ snapshots          │  │ metrics            │  │  (engineered)      │  │
  │  │                    │  │                    │  │                    │  │
  │  │ temperature        │  │ biomass_kg         │  │ temp_rolling_mean  │  │
  │  │ ph                 │  │ average_weight_g   │  │ do_lag_15m         │  │
  │  │ dissolved_oxygen   │  │ fcr                │  │ psi_ma_7d          │  │
  │  │ ammonia            │  │ mortality_rate     │  │ ammonia_velocity   │  │
  │  │ salinity           │  │ feed_consumption   │  │ acoustic_spectral  │  │
  │  │ turbidity          │  │ population         │  │                    │  │
  │  │ acoustic_db        │  │                    │  │                    │  │
  │  │ bio_acoustic_sync  │  │                    │  │                    │  │
  │  └───────────────────┘  └────────────────────┘  └────────────────────┘  │
  └──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                       PREDICTION ENGINE LAYER                            │
  │                                                                          │
  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
  │  │ PSI          │  │ Disease      │  │ Mortality    │  │ Harvest    │  │
  │  │ Predictor    │  │ Risk         │  │ Predictor    │  │ Predictor  │  │
  │  │              │  │ Predictor    │  │              │  │            │  │
  │  │ psi_score    │  │ risk_score   │  │ probability  │  │ date       │  │
  │  │ stress_level │  │ confidence   │  │ confidence   │  │ biomass    │  │
  │  │ factors[]    │  │ disease_name │  │ forecast_7d  │  │ weight     │  │
  │  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘  │
  │                                                                          │
  │  ┌──────────────────────────────────────────────────────────────────┐    │
  │  │            Hydrophone Intelligence (Phase 15F)                   │    │
  │  │  feeding_activity_score │ stress_behavior_score │ anomaly_prob   │    │
  │  └──────────────────────────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                    AI INSIGHT GENERATION LAYER                           │
  │                                                                          │
  │  ┌─────────────────────┐     ┌──────────────────────┐                   │
  │  │ Case-Based Reasoning│────▶│  AiInsight            │                   │
  │  │ (CBR) Engine        │     │  - title              │                   │
  │  │                     │     │  - description         │                   │
  │  │ case_matches        │     │  - priority            │                   │
  │  │ historical_cases    │     │  - confidence          │                   │
  │  └─────────────────────┘     └──────────┬───────────┘                   │
  └─────────────────────────────────────────┼───────────────────────────────┘
                                            │
                                            ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                   RECOMMENDATION ENGINE LAYER                            │
  │                                                                          │
  │  Risk Assessment → Historical Case Matching → Recommendation Ranking     │
  │                                                                          │
  │  ┌─────────────────┐  ┌───────────────────────┐  ┌──────────────────┐   │
  │  │ recommendations │  │ recommendation_actions │  │ recommendation_  │   │
  │  │ - action        │  │ - Accepted/Rejected/   │  │ feedback         │   │
  │  │ - confidence    │  │   Ignored              │  │ - effectiveness  │   │
  │  │ - priority      │  │                        │  │   score          │   │
  │  │ - status        │  │                        │  │ - action_taken   │   │
  │  └─────────────────┘  └───────────────────────┘  └──────────────────┘   │
  └──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                         DASHBOARD LAYER                                  │
  │                                                                          │
  │  Farm Command Center │ Analytics │ Biosecurity │ Settings/Operations     │
  │                                                                          │
  │  GET /api/v1/dashboard/overview     GET /api/v1/telemetry/acoustic       │
  │  GET /api/v1/predictions/*          GET /api/v1/recommendations/*        │
  │  GET /api/v1/alerts/*               GET /api/v1/insights/*               │
  └──────────────────────────────────────────────────────────────────────────┘
                                            │
                                            │  Operator Actions
                                            ▼
  ┌──────────────────────────────────────────────────────────────────────────┐
  │                         FEEDBACK LOOP                                    │
  │                                                                          │
  │  recommendation_actions + recommendation_feedback                        │
  │                    ↓                                                     │
  │  Aggregated into model retraining datasets                               │
  │  Effectiveness scores weight future recommendation confidence            │
  └──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Pipeline Stage Descriptions

### Stage 1: Sensor Ingestion

Physical IoT sensors attached to tanks transmit raw readings via MQTT. Each sensor is registered in the `sensors` table with a unique `hardware_id` and a `type` from the supported set: `temperature`, `pH`, `dissolved_oxygen`, `ammonia`, `salinity`, `feeder`, `aerator`, `hydrophone`.

The ingestion worker validates hardware identity, applies calibration offsets from the `calibrations` table, and writes to the `telemetry` hypertable (1-day chunk intervals). Each row contains a single scalar `value` and the optional full MQTT `raw_payload` for audit purposes.

**Source table:** `sensors` (registry), `calibrations` (offset history)
**Destination table:** `telemetry` (composite PK: `id`, `time`)

### Stage 2: Data Quality Validation

Every ingested telemetry batch passes through four automated validation checks before entering the feature store:

| Validation Type | Method | Failure Mode |
|---|---|---|
| Range Check | Value within `threshold_configs` min/max bands | Immediate alert if value exceeds critical bounds |
| Stuck Sensor Check | Rolling window variance near zero | Sensor status degraded to `Warning` |
| Drift Scan | Running drift index compared to historical baseline | `Suspect` classification; data accepted with flag |
| Spike Filter | Z-score outlier detection on trailing window | `Fail` classification; data rejected from feature store |

Each check produces a `DataQualityCheck` record with an `anomaly_score` ∈ [0.0, 1.0]. Only `Pass`-classified data enters the `ml_feature_store`. `Suspect` data is accepted with a quality flag. `Fail` data is quarantined and triggers a sensor health alert.

**Source table:** `telemetry`, `threshold_configs`
**Destination table:** `data_quality_checks` (composite PK: `id`, `time`)

### Stage 3: Feature Engineering

Raw telemetry readings are consolidated into two intermediate representations:

**Tank Environment Snapshots** — A 5-second sliding window MQTT worker pivots all active sensor streams for a single tank into a single analytics-ready row in `tank_environment_snapshots`. Columns include `temperature`, `ph`, `dissolved_oxygen`, `ammonia`, `salinity`, `turbidity`, `acoustic_db`, and `bio_acoustic_sync`.

**Tank Production Metrics** — Daily or per-shift biological production snapshots recording `population`, `biomass_kg`, `average_weight_g`, `fcr`, `feed_consumption_kg`, and `mortality_rate`.

**ML Feature Store** — Pre-computed engineered features ready for model inference and retraining. Each row stores one feature value for a specific `tank_id` at a specific `feature_timestamp`. Features are organized into groups:

| Feature Group | Source | Examples |
|---|---|---|
| `telemetry` | `tank_environment_snapshots` | Raw temperature, pH, DO readings |
| `biological` | `tank_production_metrics` | Biomass, FCR, mortality rate |
| `environmental` | `tank_environment_snapshots` | Aggregated water quality indices |
| `engineered` | Computed from above | Rolling means, lag features, interaction terms, embedding vectors |

The `feature_vector` JSON column supports multi-dimensional features (embeddings, frequency-domain features) alongside scalar `feature_value` storage.

**Destination tables:** `tank_environment_snapshots`, `tank_production_metrics`, `ml_feature_store`

### Stage 4: Model Training and Registry

Models are trained offline using historical feature store data. The training pipeline:

1. Queries `ml_feature_store` for a time range with `feature_group` and `tank_id` filters.
2. Validates data quality by checking associated `data_quality_checks` pass rates.
3. Trains candidate algorithms (XGBoost, Random Forest, LightGBM, etc.).
4. Evaluates against held-out validation sets.
5. Registers the winning model in `ai_models` → `model_versions`.

The **Model Registry** stores:
- `ai_models`: Named model identity (e.g., "PSI Predictor"), algorithm family, operational status (`Development` → `Staging` → `Production` → `Deprecated`).
- `model_versions`: Versioned artefacts with `artifact_uri` (S3/MLflow path), `hyperparameters` (JSON), `metrics` (JSON), `version_tag` (semver), and `is_active` flag.
- `model_health_metrics`: Periodic production monitoring — accuracy, precision, recall, F1, data quality score, and inter-model agreement score.

### Stage 5: Prediction Services

Deployed models run inference against current feature store data and write predictions to their respective hypertables:

| Prediction Table | Outputs | Partition Interval |
|---|---|---|
| `psi_predictions` | `psi_score` (0–10), `stress_level`, `confidence` | 7 days |
| `disease_predictions` | `risk_score` (0–10), `disease_name`, `confidence`, `forecast_days` | 14 days |
| `mortality_predictions` | `mortality_probability` (0–1), `confidence`, `forecast_days` | 14 days |
| `harvest_predictions` | `predicted_harvest_date`, `projected_biomass`, `projected_mean_weight_g`, `growth_rate_fcr`, `confidence` | 30 days |

Every prediction carries a `model_version_id` FK enabling full provenance tracing.

The PSI Predictor additionally writes `psi_factors` rows — SHAP-style explainability breakdowns showing each factor's signed contribution and importance score.

### Stage 6: AI Insight Generation

The `AiInsightService` synthesizes predictions into human-readable narratives stored in the `ai_insights` hypertable. Each insight carries:

- `source_model_id` FK → `model_versions.id` (MLOps traceability)
- `historical_case_id` FK → `historical_cases.id` (if surfaced by CBR engine)
- `priority`: `Info` | `Medium` | `High` | `Critical`
- `confidence`: model confidence ∈ [0.0, 1.0]
- `expires_at`: optional TTL for transient insights

Insights are the structured intermediate between raw predictions and operator-facing recommendations.

### Stage 7: Recommendation Engine

The `RecommendationEngineService` orchestrates the full recommendation pipeline:

1. **Risk Assessment** — Evaluates latest PSI and disease predictions against threshold severity mappings.
2. **Historical Case Matching** — The CBR engine queries `historical_cases` by `scenario_type` and calculates cosine/embedding `similarity_score` against active predictions. Matches are stored in `case_matches`.
3. **Recommendation Generation** — Creates `Recommendation` records with `action`, `expected_outcome`, `confidence`, and `priority`. Links back to `model_version_id` via `generated_by_model`.
4. **Operator Action** — Operators accept, reject, or ignore recommendations via `recommendation_actions`.
5. **Feedback Collection** — `recommendation_feedback` captures `effectiveness_score` (1–5), `action_taken`, and `comments`.

### Stage 8: Dashboard Delivery

All prediction, insight, and recommendation data flows through the existing FastAPI v1 API layer:

| Endpoint Group | Service | Key Endpoints |
|---|---|---|
| Dashboard | `DashboardService` | `/overview`, `/health`, `/trends` |
| Telemetry | `TelemetryService` | `/latest`, `/history`, `/acoustic`, `/acoustic/history` |
| Predictions | `PredictionService` | `/disease`, `/mortality`, `/harvest` |
| Recommendations | `RecommendationService` | `/list`, `/accept`, `/dismiss` |
| Insights | `AiInsightService` | `/dashboard`, `/tank` |
| Settings | `SettingsService` | `/sensors`, `/thresholds` |

---

## 4. Data Flow Contracts

### Ingestion → Feature Store

```
telemetry.value (raw scalar)
    ↓ pivot by tank_id, 5s window
tank_environment_snapshots.{temperature, ph, dissolved_oxygen, ...}
    ↓ quality gate (data_quality_checks.result == 'Pass')
ml_feature_store.feature_value (feature_group = 'telemetry')
    ↓ engineered transforms
ml_feature_store.feature_value (feature_group = 'engineered')
```

### Feature Store → Prediction

```
ml_feature_store WHERE tank_id = ? AND feature_timestamp = latest
    ↓ model inference (model_versions.artifact_uri)
psi_predictions / disease_predictions / mortality_predictions / harvest_predictions
    ↓ XAI extraction
psi_factors (SHAP values per prediction)
```

### Prediction → Recommendation

```
psi_predictions WHERE psi_score > 2.0
    ↓ risk assessment
case_matches (CBR similarity search against historical_cases)
    ↓ insight synthesis
ai_insights (priority, confidence, narrative)
    ↓ recommendation ranking
recommendations (action, expected_outcome, priority)
    ↓ operator action
recommendation_actions (Accepted | Rejected | Ignored)
    ↓ effectiveness feedback
recommendation_feedback (score 1-5, action_taken)
    ↓ retraining signal
ml_feature_store (enriched with outcome labels)
```

---

## 5. TimescaleDB Hypertable Registry

Every high-volume ML table is a TimescaleDB hypertable with a composite primary key `(UUID, timestamp)` where the timestamp is the partition key.

| Table | Partition Column | Chunk Interval | Purpose |
|---|---|---|---|
| `telemetry` | `time` | 1 day | Raw IoT sensor readings |
| `tank_environment_snapshots` | `captured_at` | 7 days | Pivoted per-tank water quality |
| `tank_production_metrics` | `recorded_at` | 30 days | Biological production snapshots |
| `ml_feature_store` | `feature_timestamp` | 7 days | Pre-computed ML features |
| `data_quality_checks` | `time` | 7 days | Sensor data validation results |
| `psi_predictions` | `generated_at` | 7 days | PSI inference outputs |
| `psi_factors` | `prediction_time` | 7 days | XAI factor breakdowns |
| `disease_predictions` | `time` | 14 days | Disease risk forecasts |
| `mortality_predictions` | `time` | 14 days | Mortality probability forecasts |
| `harvest_predictions` | `time` | 30 days | Harvest readiness forecasts |
| `ai_insights` | `generated_at` | 30 days | AI-synthesised insights |
| `case_matches` | `matched_at` | 30 days | CBR prediction-to-case matches |
| `recommendations` | `time` | 30 days | AI-generated recommendations |
| `recommendation_actions` | `executed_at` | 30 days | Operator UI actions |
| `recommendation_feedback` | `recommendation_time` | 30 days | Operator effectiveness feedback |
| `model_health_metrics` | `recorded_at` | 90 days | MLOps performance snapshots |
| `digital_twin_snapshots` | `simulation_time` | 30 days | Digital Twin scenario outputs |
| `farm_health_snapshots` | `recorded_at` | 30 days | Farm aggregate health KPIs |

---

## 6. MLOps Traceability Chain

The complete traceability chain from model registration to operator feedback:

```
ai_models
  └── model_versions (version_tag, artifact_uri, hyperparameters, metrics)
        ├── psi_predictions.model_version_id
        ├── disease_predictions.model_version_id
        ├── mortality_predictions.model_version_id
        ├── harvest_predictions.model_version_id
        ├── ai_insights.source_model_id
        └── recommendations.generated_by_model
              ├── recommendation_actions (operator response)
              └── recommendation_feedback (effectiveness score)
```

Given any recommendation shown to an operator, the system can answer:
- Which model version generated it?
- What were that version's training hyperparameters and evaluation metrics?
- Which predictions triggered it?
- Which historical cases were matched?
- How did the operator respond?
- Was the recommendation effective?

This chain is critical for regulatory compliance, SIH reporting, and continuous model improvement.

---

## 7. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| Database | PostgreSQL 16 + TimescaleDB | Native time-series partitioning, hypertable compression, continuous aggregates |
| ORM | SQLAlchemy 2.0 (async) | Mapped ORM models with composite PKs and relationship management |
| Migrations | Alembic | Versioned, additive-only schema evolution |
| API | FastAPI | Async REST API with Pydantic v2 validation and OpenAPI generation |
| ML Training | XGBoost, LightGBM, Random Forest | Gradient boosted trees for tabular aquaculture data |
| ML Serving | In-process Python inference | Low-latency serving within the FastAPI application process |
| Feature Store | `ml_feature_store` hypertable | Custom point-in-time correct feature retrieval |
| Model Registry | `ai_models` + `model_versions` tables | Application-managed model lifecycle |
| Monitoring | `model_health_metrics` hypertable | Periodic accuracy, F1, data quality, and agreement scoring |
| XAI | SHAP values via `psi_factors` | Per-prediction factor contribution breakdowns |
| CBR Engine | `historical_cases` + `case_matches` | Curated case catalog with cosine similarity matching |

---

## 8. Security and Access Control

ML pipeline components inherit NEERON's authentication and authorization infrastructure:

- **Model Registry writes** — restricted to users with data scientist or admin roles.
- **Prediction reads** — available to all authenticated operators via the existing API layer.
- **Recommendation actions** — `recommendation_actions.user_id` and `recommendation_feedback.user_id` enforce FK → `users.id` with `RESTRICT` to preserve audit trails.
- **Threshold configuration** — `threshold_configs.updated_by` tracks which operator modified alert boundaries.
- **Calibration records** — `calibrations.operator_id` enforces FK → `users.id` with `RESTRICT`.

All ML-generated data flows through the same API authentication middleware as existing operational data.

---

## 9. Failure Modes and Resilience

| Failure | Detection | Recovery |
|---|---|---|
| Sensor offline | `sensor_health.status` → `Offline` | Feature store continues with last known values; data quality score degrades |
| Data quality failure rate exceeds threshold | `data_quality_checks` aggregated pass rate | Alert generated; affected features flagged in `model_health_metrics.data_quality_score` |
| Model prediction confidence drops below minimum | `model_health_metrics` periodic evaluation | Automatic fallback to previous `is_active` model version |
| Model training produces worse metrics than current production | Training pipeline comparison gate | New version stays in `Testing` status; not promoted to `Active` |
| Recommendation feedback indicates sustained poor effectiveness | Aggregated `recommendation_feedback.effectiveness_score` trends | Model retraining triggered with updated outcome labels |
