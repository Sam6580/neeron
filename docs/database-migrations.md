# NEERON Database Migrations Guide

This document describes the **Alembic migration infrastructure** used to govern the PostgreSQL + TimescaleDB schema for the NEERON backend.

---

## 1. Migration Overview

All database tables (including core entity tables, predictions, audits, and time-series hypertables) are initialized via a single, consolidated migration revision to prevent circular dependency resolution problems and ensure correct table creation ordering.

* **Configuration File**: [alembic.ini](file:///c:/Users/Sam%20Houston/Desktop/neeron/neeron/backend/alembic.ini)
* **Migration Runner**: [env.py](file:///c:/Users/Sam%20Houston/Desktop/neeron/neeron/backend/alembic/env.py)
* **Initial Migration Script**: [8f8107ac11cc_initial_migration.py](file:///c:/Users/Sam%20Houston/Desktop/neeron/neeron/backend/alembic/versions/8f8107ac11cc_initial_migration.py)
* **Declarative Metadata Source**: [base.py](file:///c:/Users/Sam%20Houston/Desktop/neeron/neeron/backend/app/db/base.py)

---

## 2. Table Dependency Graph & Ordering

The creation order is organized into layers to guarantee that all parent tables exist before child foreign keys are declared.

```
Layer 0 (No Deps)            : roles, ai_models, historical_cases, pathogens, system_health_snapshots
  │
  ├─► Layer 1                : users (→ roles), farms
  │    │
  │    ├─► Layer 2           : user_farm_mappings (→ users, farms)
  │    │                       zones (→ farms)
  │    │                       farm_health_snapshots (→ farms)
  │    │
  │    └─► Layer 3           : tanks (→ zones)
  │         │
  │         ├─► Layer 4      : sensors (→ tanks), quarantine_events (→ tanks),
  │         │                  inspections (→ tanks), threshold_configs (→ farms, users),
  │         │                  vaccination_records (→ tanks, users), compliance_records (→ farms, tanks)
  │         │
  │         ├─► Layer 5      : sensor_health (→ sensors), calibrations (→ sensors, users),
  │         │                  model_versions (→ ai_models), notification_preferences (→ users)
  │         │
  │         ├─► Layer 6      : telemetry (→ sensors), tank_environment_snapshots (→ tanks),
  │         │                  tank_production_metrics (→ tanks)
  │         │
  │         ├─► Layer 7      : alerts (→ tanks), recommendations (→ tanks),
  │         │                  psi_predictions (→ tanks, model_versions),
  │         │                  disease_predictions (→ tanks, model_versions),
  │         │                  mortality_predictions (→ tanks, model_versions),
  │         │                  harvest_predictions (→ tanks, model_versions)
  │         │
  │         └─► Layer 8      : psi_factors (→ psi_predictions)
  │                            recommendation_feedback (→ recommendations, users)
  │                            recommendation_actions (→ recommendations, users)
  │                            notifications (→ users)
  │                            ai_insights (→ tanks, model_versions, historical_cases)
  │                            case_matches (→ historical_cases)
  │                            biosecurity_records (→ tanks, pathogens, inspections)
  │                            model_health_metrics (→ model_versions)
  │                            ml_feature_store (→ model_versions)
  │                            data_quality_checks (→ sensors, model_versions)
  │                            digital_twin_snapshots (→ tanks, model_versions)
  │                            audit_logs (→ users)
```

---

## 3. TimescaleDB Hypertables Configuration

TimescaleDB hypertables are set up dynamically in the migration revision using composite primary keys `(id, <time_column>)` to comply with TimescaleDB unique constraint constraints.

The initial migration converts **24** tables into hypertables upon upgrade (skipping them when executing on SQLite):

| Table Name | Partition Time Column | Chunk Interval | Purpose |
| :--- | :--- | :--- | :--- |
| `telemetry` | `time` | `1 day` | Raw IoT sensor ingestion stream |
| `calibrations` | `time` | `30 days` | Sensor calibration histories |
| `audit_logs` | `time` | `30 days` | Administrative database audits |
| `tank_environment_snapshots` | `captured_at` | `7 days` | Pivoted, environment datasets per tank |
| `tank_production_metrics` | `recorded_at` | `30 days` | Live biological growth metrics per tank |
| `alerts` | `time` | `7 days` | Ingestion threshold/AI-generated alerts |
| `recommendations` | `time` | `30 days` | AI-generated operational recommendations |
| `recommendation_feedback` | `recommendation_time` | `30 days` | Closed feedback loop ratings (1-5) |
| `recommendation_actions` | `executed_at` | `30 days` | Real-time UI operator selections (Accept/Reject/Ignore) |
| `notifications` | `time` | `30 days` | Platform notification inbox |
| `psi_predictions` | `generated_at` | `7 days` | Predicted Stress Index |
| `psi_factors` | `prediction_time` | `7 days` | Contribution break down per PSI prediction |
| `disease_predictions` | `time` | `14 days` | Projected risk for pathogen outbreaks |
| `mortality_predictions` | `time` | `14 days` | Projected stocking mortality risks |
| `harvest_predictions` | `time` | `30 days` | Projected optimum harvest window |
| `case_matches` | `matched_at` | `30 days` | CBR similarity case matches |
| `ai_insights` | `generated_at` | `30 days` | Synthesised analytics narratives |
| `biosecurity_records` | `time` | `14 days` | Pathogen counts and risk tracking |
| `model_health_metrics` | `recorded_at` | `90 days` | Production ML accuracy metrics |
| `ml_feature_store` | `feature_timestamp` | `7 days` | Model retraining features |
| `data_quality_checks` | `time` | `7 days` | Outlier and anomaly metrics |
| `digital_twin_snapshots` | `simulation_time` | `30 days` | Projected scenario snapshots |
| `farm_health_snapshots` | `recorded_at` | `30 days` | Aggregated farm KPI historical trends |
| `system_health_snapshots` | `recorded_at` | `30 days` | Global infrastructure latency and system health |

---

## 4. Run Instructions

### Prerequisites

Ensure you have your environment variables configured. Alembic will prioritize `DATABASE_URL` if set, otherwise falling back to the developmental defaults in [session.py](file:///c:/Users/Sam%20Houston/Desktop/neeron/neeron/backend/app/db/session.py).

```bash
# PostgreSQL dynamic configuration
export DATABASE_URL="postgresql+asyncpg://neeron_user:pwd@localhost:5432/neeron"
```

### Apply Upgrades

Apply all migrations up to the latest head:

```bash
cd backend
alembic upgrade head
```

### Rollback (Downgrade)

Revert all changes back to a clean state:

```bash
cd backend
alembic downgrade base
```

### Dry Run (Compile SQL Offline)

Generate raw DDL compilation output without opening a live database connection:

```bash
cd backend
alembic upgrade --sql head
```

---

## 5. Verification Metrics

* **Upgrade Verification**: Confirmed working. Tested successfully against developmental schemas (tables successfully registered and created).
* **Downgrade Verification**: Confirmed working. All foreign key drops resolved in exact reverse order (no constraint issues).
* **Final Database Table Count**: **42 tables** successfully created and verified.
