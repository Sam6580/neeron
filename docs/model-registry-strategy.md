# NEERON Model Registry Strategy

> Design specification for model lifecycle management using the existing
> `ai_models`, `model_versions`, and `model_health_metrics` tables.

---

## 1. Registry Architecture

NEERON's model registry is a database-native system built on three tables that together provide full MLOps traceability from model registration through deployment, monitoring, and retirement.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        MODEL REGISTRY                                  │
│                                                                        │
│  ┌─────────────┐     ┌─────────────────┐     ┌────────────────────┐   │
│  │ ai_models   │────▶│ model_versions  │────▶│ model_health_      │   │
│  │             │     │                 │     │ metrics            │   │
│  │ name        │     │ version_tag     │     │                    │   │
│  │ algorithm   │     │ artifact_uri    │     │ accuracy           │   │
│  │ description │     │ hyperparameters │     │ precision          │   │
│  │ status      │     │ metrics         │     │ recall             │   │
│  │ owner_id    │     │ status          │     │ f1_score           │   │
│  │             │     │ is_active       │     │ data_quality_score │   │
│  │             │     │ trained_at      │     │ agreement_score    │   │
│  │             │     │ deployed_at     │     │                    │   │
│  └─────────────┘     └─────────────────┘     └────────────────────┘   │
│                                                                        │
│  Relational             Relational              TimescaleDB Hypertable │
│                                                 90-day chunks          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Model Lifecycle

Every model in the NEERON registry follows a four-stage lifecycle:

```
Development ──▶ Staging ──▶ Production ──▶ Deprecated
    │                           │
    │                           ├──▶ Rollback to previous version
    │                           │
    └── (training failure) ──▶ stays in Development
```

### Stage Definitions

| Stage | `ai_models.status` | `model_versions.status` | `is_active` | Description |
|---|---|---|---|---|
| **Development** | `Development` | `Testing` | `false` | Model is being trained and evaluated. Not exposed to any API consumers. |
| **Staging** | `Staging` | `Testing` | `false` | Model has passed validation metrics. Running shadow-mode predictions alongside the production model for comparison. Predictions are written to the database but not surfaced in the UI. |
| **Production** | `Production` | `Active` | `true` | Model is the single active version serving live predictions. All API endpoints return this version's outputs. |
| **Deprecated** | `Deprecated` | `Archived` | `false` | Model version has been superseded. Predictions remain in the database for historical analysis but the version is no longer used for new inference. |

### Lifecycle Transitions

| Transition | Trigger | Validation Required |
|---|---|---|
| Development → Staging | Training metrics exceed minimum thresholds | All evaluation metrics meet model specification targets |
| Staging → Production | Shadow-mode comparison confirms parity or improvement | Staging version metrics ≥ current production version metrics for 7 consecutive evaluation windows |
| Production → Deprecated | New version promoted to Production | Automatic — only one `is_active = true` per model |
| Any → Development | Rollback or retrain decision | Manual operator approval |

---

## 3. Versioning Strategy

### Semantic Version Tags

Model versions use semantic versioning stored in `model_versions.version_tag`:

```
v{MAJOR}.{MINOR}.{PATCH}

Examples:
  v1.0.0  — initial production release
  v1.1.0  — added new feature (e.g., turbidity input)
  v1.1.1  — retrained with updated data, no architecture change
  v2.0.0  — algorithm change (e.g., Random Forest → XGBoost)
```

| Version Component | When to Increment | Example |
|---|---|---|
| **MAJOR** | Algorithm family change, input feature set redesign, or output schema change | Random Forest → XGBoost |
| **MINOR** | New feature added to input set, hyperparameter tuning strategy change, or training window adjustment | Added `turbidity` as input feature |
| **PATCH** | Retrained with same architecture on updated data | Weekly retrain with fresh 90-day window |

### Uniqueness Constraint

The `uq_model_version_tag` constraint enforces uniqueness of `(model_id, version_tag)` — no two versions of the same model can share a version tag.

### Artifact URI Convention

Serialized model artefacts are stored at URIs following this pattern:

```
s3://neeron-models/{model-name}/{version-tag}/model.pkl
```

Examples:
- `s3://neeron-models/psi-predictor/v1.0.0/model.pkl`
- `s3://neeron-models/disease-risk/v2.1.0/model.pkl`
- `mlflow://experiments/42/runs/abc123/artifacts/model`

The `artifact_uri` column supports both S3 paths and MLflow artifact URIs for flexibility.

---

## 4. Deployment Strategy

### Single Active Version

At any point in time, only one version per model has `is_active = true`. This is enforced at the application layer (not by a database unique constraint) to allow brief overlap during graceful rollover.

### Deployment Procedure

```
Step 1: Training
  - Train new version in Development
  - Store artifact_uri, hyperparameters, metrics
  - Set status = 'Testing', is_active = false

Step 2: Shadow Mode
  - Promote ai_models.status to 'Staging'
  - Run inference in parallel with production version
  - Write predictions to database (not surfaced in UI)
  - Compare model_health_metrics for 7 evaluation windows

Step 3: Promotion
  - Set previous production version: is_active = false, status = 'Archived'
  - Set new version: is_active = true, status = 'Active', deployed_at = now()
  - Promote ai_models.status to 'Production'

Step 4: Verification
  - Monitor model_health_metrics for first 24 hours
  - Verify API responses use new version (check model_version_id in predictions)
  - Confirm no degradation in accuracy, F1, or data quality scores
```

### Zero-Downtime Rollover

The `is_active` flag swap is atomic at the application layer:

1. New version is marked `is_active = true` before the old version is marked `false`.
2. During the brief overlap, the inference service selects the version with the most recent `deployed_at`.
3. Old version is then set to `is_active = false`, `status = 'Archived'`.

---

## 5. Rollback Strategy

### Automatic Rollback Triggers

| Condition | Detection | Response |
|---|---|---|
| Accuracy drops below minimum threshold for 3 consecutive windows | `model_health_metrics.accuracy < 0.85` | Revert `is_active` to previous `Archived` version |
| Data quality score drops below 0.70 | `model_health_metrics.data_quality_score < 0.70` | Pause predictions; alert data engineering team |
| F1 score drops below minimum for 3 windows | `model_health_metrics.f1_score < 0.75` | Revert to previous version |
| API error rate exceeds 1% on prediction endpoints | FastAPI middleware monitoring | Circuit breaker: return cached predictions; revert model |

### Manual Rollback Procedure

```
Step 1: Identify the rollback target version
  SELECT id, version_tag, metrics, deployed_at
  FROM model_versions
  WHERE model_id = <model_id>
    AND status = 'Archived'
  ORDER BY deployed_at DESC
  LIMIT 5;

Step 2: Swap active versions
  UPDATE model_versions SET is_active = false, status = 'Archived'
    WHERE model_id = <model_id> AND is_active = true;
  UPDATE model_versions SET is_active = true, status = 'Active', deployed_at = now()
    WHERE id = <rollback_target_id>;

Step 3: Record rollback reason in model_versions.description
```

### Rollback History Preservation

Rolled-back versions retain their `metrics` JSON and `hyperparameters` JSON, enabling post-mortem analysis of what went wrong. The `description` field is updated with rollback reason and the original deployment window.

---

## 6. Monitoring Strategy

### Model Health Metrics

The `model_health_metrics` table is a TimescaleDB hypertable (90-day chunk intervals) that stores periodic performance snapshots for each deployed model version:

| Metric | Column | Type | Range | Description |
|---|---|---|---|---|
| Accuracy | `accuracy` | `NUMERIC(5,4)` | 0.0 – 1.0 | Classification accuracy |
| Precision | `precision` | `NUMERIC(5,4)` | 0.0 – 1.0 | Positive predictive value |
| Recall | `recall` | `NUMERIC(5,4)` | 0.0 – 1.0 | Sensitivity / true positive rate |
| F1 Score | `f1_score` | `NUMERIC(5,4)` | 0.0 – 1.0 | Harmonic mean of precision and recall |
| Data Quality | `data_quality_score` | `NUMERIC(5,4)` | 0.0 – 1.0 | Fraction of inputs that passed quality checks |
| Agreement | `agreement_score` | `NUMERIC(5,4)` | 0.0 – 1.0 | Inter-model agreement for ensemble members |

### Evaluation Schedule

| Model | Evaluation Frequency | Metrics Recorded |
|---|---|---|
| PSI Predictor | Every 6 hours | accuracy, f1_score, data_quality_score |
| Disease Risk | Every 6 hours | precision, recall, f1_score, data_quality_score |
| Mortality Predictor | Every 12 hours | accuracy, f1_score, data_quality_score |
| Harvest Predictor | Daily | accuracy, data_quality_score |
| Hydrophone Intelligence | Every 6 hours (Phase 2+) | f1_score, agreement_score |

### Alerting Thresholds

| Metric | Warning Threshold | Critical Threshold | Action |
|---|---|---|---|
| `accuracy` | < 0.88 | < 0.80 | Trigger retraining investigation |
| `f1_score` | < 0.82 | < 0.75 | Automatic rollback if critical for 3 windows |
| `data_quality_score` | < 0.80 | < 0.70 | Alert data engineering; pause predictions |
| `agreement_score` | < 0.85 | < 0.75 | Ensemble consensus breaking down; review sub-models |

### Dashboard Integration

Model health metrics power the **Settings & Operations Control** page AI Operations Monitor:

- Accuracy bar charts showing current vs. historical accuracy per model
- F1 trend line charts (trailing 30 days from `model_health_metrics` hypertable)
- Data quality heatmap per sensor type
- Agreement score radar chart for ensemble models

These are served via `GET /api/v1/models/health` which queries the `model_health_metrics` table through the `ModelService`.

---

## 7. Model Registry Records

### Expected Registry Entries

| Model Name | Algorithm | Status (Initial) | Description |
|---|---|---|---|
| PSI Predictor | XGBoost | Development | Predicts Physiological Stress Index from water quality features |
| Disease Risk Classifier | XGBoost | Development | Forecasts disease outbreak probability per pathogen |
| Mortality Forecaster | Random Forest | Development | Projects mortality probability over 7/14/30-day horizons |
| Harvest Yield Model | XGBoost | Development | Predicts optimal harvest date and expected biomass yield |
| Hydrophone Analyzer | Rule-Based | Development | Statistical acoustic pattern detection (Phase 1) |

### Version 1.0.0 Metadata Template

```json
{
  "version_tag": "v1.0.0",
  "artifact_uri": "s3://neeron-models/psi-predictor/v1.0.0/model.pkl",
  "hyperparameters": {
    "algorithm": "xgboost",
    "n_estimators": 200,
    "max_depth": 6,
    "learning_rate": 0.1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "training_window_days": 90,
    "validation_split": "temporal_80_10_10"
  },
  "metrics": {
    "rmse": 0.42,
    "mae": 0.31,
    "r2": 0.93,
    "training_samples": 45000,
    "validation_samples": 5625,
    "test_samples": 5625,
    "training_duration_seconds": 127
  },
  "status": "Testing",
  "is_active": false,
  "trained_at": "2026-07-15T02:00:00Z",
  "deployed_at": null
}
```
