# NEERON Database Architecture — Version 2.0 (Enhanced)
## PostgreSQL + TimescaleDB Enterprise Review & Specification

This document details the refined database architecture (Version 2.0) for NEERON (Neural Ecosystem Environmental Response & Optimization Network). Based on a senior database architecture review, these improvements preserve existing configurations while expanding capabilities for threshold configuration, Physiological Stress Index (PSI) attribution, prediction specialization, real-time analytics acceleration, sensor diagnostics, and digital twin models.

Additionally, this enhanced specification incorporates optimized telemetry snapshots, tank production metrics, case-based reasoning matching, AI insights persistence, and MLOps historical health tracking to match all frontend requirements.

---

## 1. Architectural Review & Improvements

The refined database schema introduces five major additions to improve telemetric, biological, and MLOps performance:

1.  **Tank Environment Snapshots (`tank_environment_snapshots`)**:
    *   *Problem*: Telemetry in V1 was generic IoT stream data, requiring multiple table joins and pivot transformations on every query (e.g., matching Temperature and Dissolved Oxygen in a single tank for a model run).
    *   *Solution*: Created a consolidated snapshot table. Dashboard widgets, analytics charts, and predictive models query this table for ML-ready telemetry. Raw sensor telemetry is kept for raw data ingestion and audit verification.
2.  **Tank Production Metrics (`tank_production_metrics`)**:
    *   *Problem*: Analytics and growth forecast pages track biomass trends and FCR ratios, but there was no dedicated historical table for biological growth.
    *   *Solution*: Added a dedicated production metrics table tracking fish population, biomass (kg), average weight (g), FCR, mortality rate, and feed consumption.
3.  **Case-Based Reasoning (`historical_cases` & `case_matches`)**:
    *   *Problem*: The Tank Detail view features a "Historical Case Match" card (e.g., Scenario #SCN-912), but the database lacked a mechanism to link and retrieve historical cases.
    *   *Solution*: Added a catalog of historical cases alongside a similarity match table linked directly to predictions to provide recommendations.
4.  **AI Insights Storage (`ai_insights`)**:
    *   *Problem*: Predictive insights displayed on dashboards were volatile and lacked audit trails or historical tracking.
    *   *Solution*: Added a dedicated insight table with expiry timestamps, priority categories, and confidence indexes.
5.  **MLOps Metrics (`model_health_metrics`)**:
    *   *Problem*: MLOps parameters like forecast reliability, model agreement coefficients, and sensor coverages were not stored historically.
    *   *Solution*: Added MLOps logs tracking accuracy, F1 score, data quality, and model agreement over time.

---

## 2. Updated Relationship Hierarchy & ER Diagram

The database uses relational tables for master data and TimescaleDB hypertables for time-series logs.

### 2.1 Entity Relationship Hierarchy (Text Format)

```text
Farm
├── threshold_configs (1:N)
└── Zones (1:N)
    └── Tanks (1:N)
        ├── Sensors (1:N)
        │   ├── telemetry (1:N) [TimescaleDB Hypertable]
        │   ├── calibrations (1:N) [TimescaleDB Hypertable]
        │   ├── sensor_health (1:1)
        │   └── data_quality_checks (1:N) [TimescaleDB Hypertable]
        ├── tank_environment_snapshots (1:N) [TimescaleDB Hypertable]
        ├── tank_production_metrics (1:N) [TimescaleDB Hypertable]
        ├── psi_predictions (1:N) [TimescaleDB Hypertable]
        │   └── psi_factors (1:N) [TimescaleDB Hypertable]
        ├── disease_predictions (1:N) [TimescaleDB Hypertable]
        │   └── case_matches (1:N) [TimescaleDB Hypertable]
        ├── mortality_predictions (1:N) [TimescaleDB Hypertable]
        ├── harvest_predictions (1:N) [TimescaleDB Hypertable]
        ├── digital_twin_snapshots (1:N) [TimescaleDB Hypertable]
        ├── ai_insights (1:N) [TimescaleDB Hypertable]
        ├── recommendations (1:N) [TimescaleDB Hypertable]
        │   └── recommendation_feedback (1:1) [TimescaleDB Hypertable]
        ├── ml_feature_store (1:N) [TimescaleDB Hypertable]
        └── Alerts (1:N) [TimescaleDB Hypertable]

Roles
└── Users (1:N)
    ├── notification_preferences (1:1)
    └── Audit Logs (1:N) [TimescaleDB Hypertable]

AI Models
└── Model Versions (1:N)
    ├── Predictions (1:N)
    └── model_health_metrics (1:N) [TimescaleDB Hypertable]

historical_cases
└── case_matches (1:N)
```

---

## 3. Database Table Definitions

### 3.1 Relational & Configuration Tables

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Core Role & User Administration
CREATE TABLE roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    permissions JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    two_factor_secret VARCHAR(128),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Infrastructure Mapping
CREATE TABLE farms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    latitude NUMERIC(9, 6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude NUMERIC(9, 6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    timezone VARCHAR(50) NOT NULL DEFAULT 'UTC',
    carrying_capacity_kg NUMERIC(12, 2) NOT NULL CHECK (carrying_capacity_kg > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE user_farm_mappings (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, farm_id)
);

CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (farm_id, name)
);

CREATE TABLE tanks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('RAS Tank', 'Sea Cage', 'Nursery')),
    volume_m3 NUMERIC(10, 2) NOT NULL CHECK (volume_m3 > 0),
    max_biomass_kg NUMERIC(12, 2) NOT NULL CHECK (max_biomass_kg > 0),
    species VARCHAR(100) NOT NULL DEFAULT 'Atlantic Salmon',
    digital_twin_config JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (zone_id, name)
);

CREATE TABLE sensors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tank_id UUID REFERENCES tanks(id) ON DELETE SET NULL,
    hardware_id VARCHAR(100) UNIQUE NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('temperature', 'pH', 'dissolved_oxygen', 'ammonia', 'salinity', 'feeder', 'aerator')),
    status VARCHAR(50) NOT NULL DEFAULT 'Active' CHECK (status IN ('Active', 'Warning', 'Calibration Overdue', 'Offline')),
    calibration_due_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- AI/ML Governance
CREATE TABLE ai_models (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE model_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES ai_models(id) ON DELETE CASCADE,
    version_tag VARCHAR(50) NOT NULL,
    hyperparameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'Archived' CHECK (status IN ('Active', 'Testing', 'Archived')),
    trained_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deployed_at TIMESTAMPTZ,
    UNIQUE (model_id, version_tag)
);

-- Biosecurity Registries
CREATE TABLE pathogens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scientific_name VARCHAR(150) UNIQUE NOT NULL,
    common_name VARCHAR(100) NOT NULL,
    risk_threshold_count NUMERIC(6, 2) NOT NULL CHECK (risk_threshold_count >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quarantine_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    cleared_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    inspector_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    notes TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Threshold Management
CREATE TABLE threshold_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    farm_id UUID NOT NULL REFERENCES farms(id) ON DELETE CASCADE,
    metric_name VARCHAR(100) NOT NULL CHECK (metric_name IN ('temperature', 'pH', 'dissolved_oxygen', 'ammonia', 'salinity')),
    minimum_value NUMERIC(10, 4) NOT NULL,
    maximum_value NUMERIC(10, 4) NOT NULL,
    warning_min NUMERIC(10, 4) NOT NULL,
    warning_max NUMERIC(10, 4) NOT NULL,
    critical_min NUMERIC(10, 4) NOT NULL,
    critical_max NUMERIC(10, 4) NOT NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (farm_id, metric_name),
    CONSTRAINT chk_threshold_logical_order CHECK (
        minimum_value <= critical_min AND
        critical_min <= warning_min AND
        warning_min <= warning_max AND
        warning_max <= critical_max AND
        critical_max <= maximum_value
    )
);

-- Sensor Health Monitoring
CREATE TABLE sensor_health (
    sensor_id UUID PRIMARY KEY REFERENCES sensors(id) ON DELETE CASCADE,
    signal_strength VARCHAR(50) NOT NULL CHECK (signal_strength IN ('Strong', 'Medium', 'Weak', 'Offline')),
    battery_level NUMERIC(5, 2) CHECK (battery_level BETWEEN 0 AND 100),
    drift_score NUMERIC(5, 4) NOT NULL DEFAULT 0.0000 CHECK (drift_score >= 0),
    health_status VARCHAR(50) NOT NULL CHECK (health_status IN ('Optimal', 'Warning', 'Maintenance Required', 'Fault')),
    last_seen TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Notification Settings
CREATE TABLE notification_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    sms_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    critical_alerts_only BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--------------------------------------------------------------------------------
-- NEW TABLE: historical_cases (Improvement 3)
-- Purpose: Catalog of past operational anomalies and resolution actions.
--------------------------------------------------------------------------------
CREATE TABLE historical_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    scenario_type VARCHAR(100) NOT NULL, -- e.g., "Dissolved Oxygen Depletion", "Sea Lice Influx"
    outcome TEXT NOT NULL,                -- e.g., "FCR restored, zero mortalities"
    resolution TEXT NOT NULL,             -- e.g., "Increased aeration and reduced feed input"
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 3.2 Time-Series & Hypertable Schemas

```sql
-- Legacy Telemetry hypertable setup
CREATE TABLE telemetry (
    time TIMESTAMPTZ NOT NULL,
    sensor_id UUID NOT NULL REFERENCES sensors(id) ON DELETE RESTRICT,
    value NUMERIC(10, 4) NOT NULL,
    raw_payload JSONB,
    PRIMARY KEY (time, sensor_id)
);

-- Legacy Recommendations hypertable setup
CREATE TABLE recommendations (
    time TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    action VARCHAR(150) NOT NULL,
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('Routine', 'High', 'Emergency')),
    expected_outcome TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'resolved', 'dismissed')),
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT,
    PRIMARY KEY (time, id)
);

-- Legacy Alerts hypertable setup
CREATE TABLE alerts (
    time TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    sensor_id UUID REFERENCES sensors(id) ON DELETE SET NULL,
    type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL CHECK (severity IN ('Safe', 'Warning', 'Critical')),
    message TEXT NOT NULL,
    resolved_at TIMESTAMPTZ,
    PRIMARY KEY (time, tank_id, type)
);

-- Legacy Biosecurity records hypertable setup
CREATE TABLE biosecurity_records (
    time TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    pathogen_id UUID NOT NULL REFERENCES pathogens(id) ON DELETE RESTRICT,
    detection_method VARCHAR(100) NOT NULL CHECK (detection_method IN ('qPCR Test', 'Visual Count', 'Microscopy')),
    value NUMERIC(10, 4) NOT NULL,
    risk_level VARCHAR(50) NOT NULL CHECK (risk_level IN ('Safe', 'Warning', 'Critical')),
    PRIMARY KEY (time, tank_id, pathogen_id)
);

-- Legacy Calibrations hypertable setup
CREATE TABLE calibrations (
    time TIMESTAMPTZ NOT NULL,
    sensor_id UUID NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    operator_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    offset_value NUMERIC(10, 4) NOT NULL,
    variance NUMERIC(10, 4) NOT NULL,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'failed')),
    notes TEXT,
    PRIMARY KEY (time, sensor_id)
);

-- Legacy Audit Logs hypertable setup
CREATE TABLE audit_logs (
    time TIMESTAMPTZ NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    event_type VARCHAR(100) NOT NULL,
    action TEXT NOT NULL,
    target_entity VARCHAR(100),
    target_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45) NOT NULL,
    PRIMARY KEY (time, event_type)
);

-- Legacy Notifications hypertable setup
CREATE TABLE notifications (
    time TIMESTAMPTZ NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_time TIMESTAMPTZ NOT NULL,
    alert_tank_id UUID NOT NULL,
    alert_type VARCHAR(100) NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (time, user_id, alert_time, alert_type)
);

-- Legacy predictions hypertable (Kept for backward compatibility)
CREATE TABLE predictions (
    time TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    metric VARCHAR(100) NOT NULL,
    value NUMERIC(12, 4) NOT NULL,
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    features_importance JSONB,
    explainability JSONB,
    PRIMARY KEY (time, tank_id, model_version_id, metric)
);

-- PSI Predictions
CREATE TABLE psi_predictions (
    generated_at TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    psi_score NUMERIC(4, 2) NOT NULL CHECK (psi_score BETWEEN 0.00 AND 10.00),
    stress_level VARCHAR(50) NOT NULL CHECK (stress_level IN ('Optimal', 'Mild Stress', 'Moderate Stress', 'Severe Stress', 'Critical Stress')),
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    PRIMARY KEY (generated_at, id)
);

-- PSI Explainable AI Factors
CREATE TABLE psi_factors (
    prediction_time TIMESTAMPTZ NOT NULL,
    prediction_id UUID NOT NULL,
    factor_name VARCHAR(100) NOT NULL CHECK (factor_name IN ('temperature', 'dissolved_oxygen', 'pH', 'ammonia', 'salinity', 'stocking_density')),
    contribution NUMERIC(6, 4) NOT NULL,
    importance_score NUMERIC(6, 4) NOT NULL CHECK (importance_score >= 0),
    PRIMARY KEY (prediction_time, prediction_id, factor_name),
    FOREIGN KEY (prediction_time, prediction_id) REFERENCES psi_predictions(generated_at, id) ON DELETE CASCADE
);

-- Specialized Prediction Tables
CREATE TABLE disease_predictions (
    time TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    pathogen_id UUID NOT NULL REFERENCES pathogens(id) ON DELETE RESTRICT,
    probability NUMERIC(5, 4) NOT NULL CHECK (probability BETWEEN 0 AND 1),
    confidence_low NUMERIC(5, 4) NOT NULL,
    confidence_high NUMERIC(5, 4) NOT NULL,
    PRIMARY KEY (time, id)
);

CREATE TABLE mortality_predictions (
    time TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    forecast_horizon_days INTEGER NOT NULL CHECK (forecast_horizon_days IN (7, 14, 30)),
    mortality_rate_projected NUMERIC(6, 4) NOT NULL CHECK (mortality_rate_projected BETWEEN 0 AND 1),
    confidence_low NUMERIC(6, 4) NOT NULL,
    confidence_high NUMERIC(6, 4) NOT NULL,
    PRIMARY KEY (time, id)
);

CREATE TABLE harvest_predictions (
    time TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE RESTRICT,
    estimated_harvest_date DATE NOT NULL,
    projected_mean_weight_g NUMERIC(10, 2) NOT NULL CHECK (projected_mean_weight_g > 0),
    projected_biomass_kg NUMERIC(12, 2) NOT NULL CHECK (projected_biomass_kg > 0),
    growth_rate_fcr NUMERIC(4, 2) NOT NULL CHECK (growth_rate_fcr > 0),
    revenue_projection_usd NUMERIC(15, 2),
    PRIMARY KEY (time, id)
);

-- Recommendation Loop Feedback
CREATE TABLE recommendation_feedback (
    recommendation_time TIMESTAMPTZ NOT NULL,
    recommendation_id UUID NOT NULL,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    action_taken VARCHAR(100) NOT NULL CHECK (action_taken IN ('Applied Remediation', 'Alternative Action Taken', 'Ignored - False Alarm', 'Ignored - Operational Constraints')),
    effectiveness_score INTEGER NOT NULL CHECK (effectiveness_score BETWEEN 1 AND 5),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (recommendation_time, recommendation_id),
    FOREIGN KEY (recommendation_time, recommendation_id) REFERENCES recommendations(time, id) ON DELETE CASCADE
);

-- Digital Twin Snapshots
CREATE TABLE digital_twin_snapshots (
    time TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    simulated_biomass NUMERIC(12, 2) NOT NULL CHECK (simulated_biomass >= 0),
    simulated_oxygen NUMERIC(10, 4) NOT NULL CHECK (simulated_oxygen >= 0),
    simulated_growth NUMERIC(10, 4) NOT NULL CHECK (simulated_growth >= 0),
    scenario_name VARCHAR(100) NOT NULL,
    PRIMARY KEY (time, tank_id, scenario_name)
);

-- ML Retraining Feature Store
CREATE TABLE ml_feature_store (
    time TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    telemetry_features JSONB NOT NULL,
    biological_features JSONB NOT NULL,
    environmental_features JSONB NOT NULL,
    engineered_features JSONB NOT NULL,
    PRIMARY KEY (time, tank_id)
);

-- Ingest Validation & Data Quality Logs
CREATE TABLE data_quality_checks (
    time TIMESTAMPTZ NOT NULL,
    sensor_id UUID NOT NULL REFERENCES sensors(id) ON DELETE CASCADE,
    validation_type VARCHAR(100) NOT NULL CHECK (validation_type IN ('Range Check', 'Stuck Sensor Check', 'Drift Scan', 'Spike Filter')),
    result VARCHAR(50) NOT NULL CHECK (result IN ('Pass', 'Fail', 'Suspect')),
    anomaly_score NUMERIC(5, 4) NOT NULL CHECK (anomaly_score BETWEEN 0 AND 1),
    PRIMARY KEY (time, sensor_id, validation_type)
);

--------------------------------------------------------------------------------
-- NEW TIMESCALEDB HYPERTABLE: tank_environment_snapshots (Improvement 1)
-- Purpose: Pre-pivoted, clean parameters for immediate AI consumption.
--------------------------------------------------------------------------------
CREATE TABLE tank_environment_snapshots (
    captured_at TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    temperature NUMERIC(6, 2) CHECK (temperature BETWEEN -5.00 AND 40.00),
    ph NUMERIC(4, 2) CHECK (ph BETWEEN 0.00 AND 14.00),
    dissolved_oxygen NUMERIC(6, 2) CHECK (dissolved_oxygen >= 0),
    salinity NUMERIC(6, 2) CHECK (salinity >= 0),
    ammonia NUMERIC(6, 4) CHECK (ammonia >= 0),
    turbidity NUMERIC(6, 2) CHECK (turbidity >= 0),
    PRIMARY KEY (captured_at, tank_id, id)
);

--------------------------------------------------------------------------------
-- NEW TIMESCALEDB HYPERTABLE: tank_production_metrics (Improvement 2)
-- Purpose: Tracks fish biomass and FCR trends.
--------------------------------------------------------------------------------
CREATE TABLE tank_production_metrics (
    recorded_at TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    population INTEGER NOT NULL CHECK (population >= 0),
    biomass_kg NUMERIC(12, 2) NOT NULL CHECK (biomass_kg >= 0),
    average_weight_g NUMERIC(10, 2) NOT NULL CHECK (average_weight_g >= 0),
    fcr NUMERIC(4, 2) NOT NULL CHECK (fcr >= 0),
    mortality_rate NUMERIC(6, 4) NOT NULL CHECK (mortality_rate BETWEEN 0 AND 1),
    feed_consumption_kg NUMERIC(10, 2) NOT NULL CHECK (feed_consumption_kg >= 0),
    PRIMARY KEY (recorded_at, tank_id)
);

--------------------------------------------------------------------------------
-- NEW TIMESCALEDB HYPERTABLE: case_matches (Improvement 3)
-- Purpose: Links predictive models to historical resolution profiles.
--------------------------------------------------------------------------------
CREATE TABLE case_matches (
    time TIMESTAMPTZ NOT NULL,
    prediction_id UUID NOT NULL, -- References a specialized prediction run
    case_id UUID NOT NULL REFERENCES historical_cases(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL CHECK (similarity_score BETWEEN 0.0000 AND 1.0000),
    PRIMARY KEY (time, prediction_id, case_id)
);

--------------------------------------------------------------------------------
-- NEW TIMESCALEDB HYPERTABLE: ai_insights (Improvement 4)
-- Purpose: Stores active AI predictions displayed on dashboards.
--------------------------------------------------------------------------------
CREATE TABLE ai_insights (
    generated_at TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    priority VARCHAR(50) NOT NULL CHECK (priority IN ('Info', 'Medium', 'High', 'Critical')),
    confidence NUMERIC(5, 4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    expires_at TIMESTAMPTZ,
    PRIMARY KEY (generated_at, id)
);

--------------------------------------------------------------------------------
-- NEW TIMESCALEDB HYPERTABLE: model_health_metrics (Improvement 5)
-- Purpose: MLOps performance and reliability logs.
--------------------------------------------------------------------------------
CREATE TABLE model_health_metrics (
    recorded_at TIMESTAMPTZ NOT NULL,
    model_version_id UUID NOT NULL REFERENCES model_versions(id) ON DELETE CASCADE,
    accuracy NUMERIC(5, 4) CHECK (accuracy BETWEEN 0 AND 1),
    precision NUMERIC(5, 4) CHECK (precision BETWEEN 0 AND 1),
    recall NUMERIC(5, 4) CHECK (recall BETWEEN 0 AND 1),
    f1_score NUMERIC(5, 4) CHECK (f1_score BETWEEN 0 AND 1),
    data_quality_score NUMERIC(5, 4) CHECK (data_quality_score BETWEEN 0 AND 1),
    agreement_score NUMERIC(5, 4) CHECK (agreement_score BETWEEN 0 AND 1),
    PRIMARY KEY (recorded_at, model_version_id)
);
```

---

## 4. TimescaleDB Design & Ingestion

### 4.1 Hypertable Configuration

We add the five new tables to TimescaleDB's hypertable system to ensure high-frequency queries execute efficiently.

| Table Name | Partitioning Column | Interval | Reason |
| :--- | :--- | :--- | :--- |
| `tank_environment_snapshots` | `captured_at` | 7 Days | Highly active, consolidated sensor snapshot table. |
| `tank_production_metrics` | `recorded_at` | 30 Days | Medium-frequency biological indicators. |
| `case_matches` | `time` | 30 Days | Pairs active predictions with historical cases. |
| `ai_insights` | `generated_at` | 30 Days | Dashboard and analytics insights. |
| `model_health_metrics` | `recorded_at` | 90 Days | Low-frequency model health logs. |

```sql
SELECT create_hypertable('tank_environment_snapshots', 'captured_at', chunk_time_interval => INTERVAL '7 days');
SELECT create_hypertable('tank_production_metrics', 'recorded_at', chunk_time_interval => INTERVAL '30 days');
SELECT create_hypertable('case_matches', 'time', chunk_time_interval => INTERVAL '30 days');
SELECT create_hypertable('ai_insights', 'generated_at', chunk_time_interval => INTERVAL '30 days');
SELECT create_hypertable('model_health_metrics', 'recorded_at', chunk_time_interval => INTERVAL '90 days');
```

### 4.2 Snapshot Ingestion Pipeline Design

To avoid expensive client joins, the `tank_environment_snapshots` table is populated in real time using one of two strategies:

1.  **Ingestion Worker (Application Layer)**:
    An MQTT ingestion service collects raw sensor payloads, groups them using a 5-second sliding window per tank, and writes a consolidated snapshot row.
2.  **Database Trigger (Database Layer)**:
    A trigger updates a tank state record on every insert to the raw `telemetry` table:

```sql
-- Procedure: update_tank_environment_snapshot
CREATE OR REPLACE FUNCTION trigger_populate_environment_snapshot()
RETURNS TRIGGER AS $$
DECLARE
    v_tank_id UUID;
    v_type VARCHAR(50);
BEGIN
    -- Resolve tank and sensor context
    SELECT tank_id, type INTO v_tank_id, v_type FROM sensors WHERE id = NEW.sensor_id;
    
    IF v_tank_id IS NOT NULL THEN
        -- Insert snapshot using an UPSERT rule
        INSERT INTO tank_environment_snapshots (captured_at, tank_id, temperature, ph, dissolved_oxygen, salinity, ammonia)
        VALUES (
            time_bucket('5 seconds', NEW.time),
            v_tank_id,
            CASE WHEN v_type = 'temperature' THEN NEW.value ELSE NULL END,
            CASE WHEN v_type = 'pH' THEN NEW.value ELSE NULL END,
            CASE WHEN v_type = 'dissolved_oxygen' THEN NEW.value ELSE NULL END,
            CASE WHEN v_type = 'salinity' THEN NEW.value ELSE NULL END,
            CASE WHEN v_type = 'ammonia' THEN NEW.value ELSE NULL END
        )
        ON CONFLICT (captured_at, tank_id) 
        DO UPDATE SET
            temperature = COALESCE(EXCLUDED.temperature, tank_environment_snapshots.temperature),
            ph = COALESCE(EXCLUDED.ph, tank_environment_snapshots.ph),
            dissolved_oxygen = COALESCE(EXCLUDED.dissolved_oxygen, tank_environment_snapshots.dissolved_oxygen),
            salinity = COALESCE(EXCLUDED.salinity, tank_environment_snapshots.salinity),
            ammonia = COALESCE(EXCLUDED.ammonia, tank_environment_snapshots.ammonia);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

---

## 5. Telemetry Analytics Layer & Dashboard Optimization

We use **TimescaleDB Continuous Aggregates** to pre-compute environmental stats on hourly and daily intervals, speeding up historical charts.

```sql
-- Hourly environment snapshot aggregate
CREATE MATERIALIZED VIEW hourly_environment_stats
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', captured_at) AS bucket,
    tank_id,
    AVG(temperature) AS avg_temp,
    AVG(ph) AS avg_ph,
    AVG(dissolved_oxygen) AS avg_do,
    AVG(salinity) AS avg_salinity,
    AVG(ammonia) AS avg_ammonia
FROM tank_environment_snapshots
GROUP BY bucket, tank_id;

SELECT add_continuous_aggregate_policy('hourly_environment_stats',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

### 5.2 Materialized Views for Dashboard Performance

We use a materialized view to compile metrics from across the database into a single, quickly accessible structure for the dashboard.

```sql
-- View: dashboard_summary_v2
CREATE MATERIALIZED VIEW dashboard_summary_v2 AS
SELECT 
    t.id AS tank_id,
    t.name AS tank_name,
    z.name AS zone_name,
    f.name AS farm_name,
    COALESCE(env.temperature, 0.0) AS last_temperature,
    COALESCE(env.dissolved_oxygen, 0.0) AS last_do,
    COALESCE(env.ph, 0.0) AS last_ph,
    COALESCE(prod.biomass_kg, 0.0) AS current_biomass,
    COALESCE(prod.fcr, 0.0) AS current_fcr,
    COALESCE(psi.psi_score, 0.00) AS current_psi,
    (SELECT COUNT(*) FROM alerts WHERE tank_id = t.id AND resolved_at IS NULL) AS active_alerts_count
FROM tanks t
JOIN zones z ON t.zone_id = z.id
JOIN farms f ON z.farm_id = f.id
LEFT JOIN LATERAL (
    SELECT temperature, dissolved_oxygen, ph 
    FROM tank_environment_snapshots 
    WHERE tank_id = t.id 
    ORDER BY captured_at DESC LIMIT 1
) env ON TRUE
LEFT JOIN LATERAL (
    SELECT biomass_kg, fcr 
    FROM tank_production_metrics 
    WHERE tank_id = t.id 
    ORDER BY recorded_at DESC LIMIT 1
) prod ON TRUE
LEFT JOIN LATERAL (
    SELECT psi_score 
    FROM psi_predictions 
    WHERE tank_id = t.id 
    ORDER BY generated_at DESC LIMIT 1
) psi ON TRUE;
```

---

## 6. Indexing Strategy

```sql
-- Optimize Snapshot lookups
CREATE INDEX idx_env_snapshots_tank_time ON tank_environment_snapshots (tank_id, captured_at DESC);

-- Optimize Production Metrics lookups
CREATE INDEX idx_production_metrics_tank_time ON tank_production_metrics (tank_id, recorded_at DESC);

-- Optimize case reasoning & insights lookups
CREATE INDEX idx_case_matches_prediction ON case_matches (prediction_id, similarity_score DESC);
CREATE INDEX idx_ai_insights_tank_active ON ai_insights (tank_id, generated_at DESC) WHERE expires_at IS NULL OR expires_at > NOW();

-- Optimize model health logs
CREATE INDEX idx_model_health_version_time ON model_health_metrics (model_version_id, recorded_at DESC);
```

---

## 7. Migration Strategy: Version 1.0 to Version 2.0 (Enhanced)

Follow this migration path to transition from Version 1.0 to Version 2.0 (Enhanced) without data loss or application downtime.

### 7.1 Migration Scripts

```sql
-- Step 1: Add new tables
CREATE TABLE IF NOT EXISTS historical_cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    scenario_type VARCHAR(100) NOT NULL,
    outcome TEXT NOT NULL,
    resolution TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Step 2: Set up new time-series tables
CREATE TABLE IF NOT EXISTS tank_environment_snapshots (
    captured_at TIMESTAMPTZ NOT NULL,
    id UUID NOT NULL DEFAULT uuid_generate_v4(),
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    temperature NUMERIC(6, 2),
    ph NUMERIC(4, 2),
    dissolved_oxygen NUMERIC(6, 2),
    salinity NUMERIC(6, 2),
    ammonia NUMERIC(6, 4),
    turbidity NUMERIC(6, 2),
    PRIMARY KEY (captured_at, tank_id, id)
);
SELECT create_hypertable('tank_environment_snapshots', 'captured_at', chunk_time_interval => INTERVAL '7 days', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS tank_production_metrics (
    recorded_at TIMESTAMPTZ NOT NULL,
    tank_id UUID NOT NULL REFERENCES tanks(id) ON DELETE CASCADE,
    population INTEGER NOT NULL,
    biomass_kg NUMERIC(12, 2) NOT NULL,
    average_weight_g NUMERIC(10, 2) NOT NULL,
    fcr NUMERIC(4, 2) NOT NULL,
    mortality_rate NUMERIC(6, 4) NOT NULL,
    feed_consumption_kg NUMERIC(10, 2) NOT NULL,
    PRIMARY KEY (recorded_at, tank_id)
);
SELECT create_hypertable('tank_production_metrics', 'recorded_at', chunk_time_interval => INTERVAL '30 days', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS case_matches (
    time TIMESTAMPTZ NOT NULL,
    prediction_id UUID NOT NULL,
    case_id UUID REFERENCES historical_cases(id) ON DELETE CASCADE,
    similarity_score NUMERIC(5, 4) NOT NULL,
    PRIMARY KEY (time, prediction_id, case_id)
);
SELECT create_hypertable('case_matches', 'time', chunk_time_interval => INTERVAL '30 days', if_not_exists => TRUE);

-- Step 3: Backfill environment snapshots from legacy telemetry
-- This query aggregates and pivots legacy telemetry into clean snapshots.
INSERT INTO tank_environment_snapshots (captured_at, tank_id, temperature, ph, dissolved_oxygen, salinity, ammonia)
SELECT 
    time_bucket('5 seconds', t.time) AS captured_at,
    s.tank_id,
    AVG(CASE WHEN s.type = 'temperature' THEN t.value ELSE NULL END) AS temperature,
    AVG(CASE WHEN s.type = 'pH' THEN t.value ELSE NULL END) AS ph,
    AVG(CASE WHEN s.type = 'dissolved_oxygen' THEN t.value ELSE NULL END) AS dissolved_oxygen,
    AVG(CASE WHEN s.type = 'salinity' THEN t.value ELSE NULL END) AS salinity,
    AVG(CASE WHEN s.type = 'ammonia' THEN t.value ELSE NULL END) AS ammonia
FROM telemetry t
JOIN sensors s ON t.sensor_id = s.id
GROUP BY captured_at, s.tank_id
ON CONFLICT DO NOTHING;
```
