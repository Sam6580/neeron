# NEERON ML Feature Catalog

> Complete inventory of every ML feature consumed by NEERON prediction models.
> Grounded against the existing database schema — all source tables and columns verified.

---

## Feature Registry Overview

Features are organized by the `feature_group` classification used in the `ml_feature_store` table:

| Feature Group | Count | Source Layer |
|---|---|---|
| `telemetry` | 8 | `tank_environment_snapshots` |
| `biological` | 6 | `tank_production_metrics` |
| `environmental` | 6 | `tank_environment_snapshots` (aggregated) |
| `engineered` | 12 | Computed from `telemetry` + `biological` |

---

## Telemetry Features

Raw sensor-derived features pivoted per-tank from `tank_environment_snapshots`.

### `temperature`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `temperature` |
| **Data Type** | `NUMERIC(6,2)` |
| **Unit** | °C |
| **Valid Range** | −5.00 … 40.00 (enforced by `ck_env_snapshot_temp_range`) |
| **Refresh Frequency** | Every 5 seconds (MQTT sliding window) |
| **Validation Rules** | Range Check against `threshold_configs` for farm; Spike Filter z-score |
| **Used By Models** | PSI Predictor, Disease Risk Predictor, Mortality Predictor, Harvest Predictor |

### `ph`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `ph` |
| **Data Type** | `NUMERIC(4,2)` |
| **Unit** | pH units |
| **Valid Range** | 0.00 … 14.00 (enforced by `ck_env_snapshot_ph_range`) |
| **Refresh Frequency** | Every 5 seconds |
| **Validation Rules** | Range Check; Stuck Sensor Check (variance window) |
| **Used By Models** | PSI Predictor, Disease Risk Predictor |

### `dissolved_oxygen`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `dissolved_oxygen` |
| **Data Type** | `NUMERIC(6,2)` |
| **Unit** | mg/L |
| **Valid Range** | ≥ 0 (enforced by `ck_env_snapshot_do_non_negative`) |
| **Refresh Frequency** | Every 5 seconds |
| **Validation Rules** | Range Check; Drift Scan (baseline comparison); Spike Filter |
| **Used By Models** | PSI Predictor, Disease Risk Predictor, Mortality Predictor |

### `ammonia`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `ammonia` |
| **Data Type** | `NUMERIC(6,4)` |
| **Unit** | mg/L (Total Ammonia Nitrogen) |
| **Valid Range** | ≥ 0 (enforced by `ck_env_snapshot_ammonia_non_negative`) |
| **Refresh Frequency** | Every 5 seconds |
| **Validation Rules** | Range Check; Spike Filter (penalty factor 500× std dev in water quality index) |
| **Used By Models** | PSI Predictor, Disease Risk Predictor |

### `salinity`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `salinity` |
| **Data Type** | `NUMERIC(6,2)` |
| **Unit** | PSU (g/kg) |
| **Valid Range** | ≥ 0 (enforced by `ck_env_snapshot_salinity_non_negative`) |
| **Refresh Frequency** | Every 5 seconds |
| **Validation Rules** | Range Check; Drift Scan |
| **Used By Models** | PSI Predictor |

### `turbidity`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `turbidity` |
| **Data Type** | `NUMERIC(6,2)` |
| **Unit** | NTU |
| **Valid Range** | ≥ 0 (enforced by `ck_env_snapshot_turbidity_non_negative`) |
| **Refresh Frequency** | Every 5 seconds |
| **Validation Rules** | Range Check |
| **Used By Models** | PSI Predictor, Disease Risk Predictor |

### `acoustic_db`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `acoustic_db` |
| **Data Type** | `NUMERIC(6,2)` |
| **Unit** | dB (decibels) |
| **Valid Range** | Nullable; no explicit range constraint (acoustic levels can be negative) |
| **Refresh Frequency** | Every 5 seconds (when hydrophone sensor is active) |
| **Validation Rules** | Stuck Sensor Check; Drift Scan against baseline |
| **Used By Models** | Hydrophone Intelligence |

### `bio_acoustic_sync`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `bio_acoustic_sync` |
| **Data Type** | `NUMERIC(5,2)` |
| **Unit** | Percentage (0–100%) |
| **Valid Range** | 0.00 … 100.00 (enforced by `ck_env_snapshot_bio_acoustic_sync_range`) |
| **Refresh Frequency** | Every 5 seconds (when hydrophone sensor is active) |
| **Validation Rules** | Range Check (0–100) |
| **Used By Models** | Hydrophone Intelligence |

---

## Biological Features

Production metrics from `tank_production_metrics`, recorded daily or per-shift.

### `biomass_kg`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `biomass_kg` |
| **Data Type** | `NUMERIC(12,2)` |
| **Unit** | kg |
| **Valid Range** | ≥ 0 (enforced by `ck_prod_metric_biomass_non_negative`) |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Non-negative check; growth trajectory consistency |
| **Used By Models** | Harvest Predictor, Mortality Predictor |

### `average_weight_g`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `average_weight_g` |
| **Data Type** | `NUMERIC(10,2)` |
| **Unit** | g (grams per fish) |
| **Valid Range** | ≥ 0 (enforced by `ck_prod_metric_avg_weight_non_negative`) |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Non-negative check; growth rate plausibility |
| **Used By Models** | Harvest Predictor |

### `fcr`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `fcr` |
| **Data Type** | `NUMERIC(4,2)` |
| **Unit** | Ratio (kg feed / kg biomass gain) |
| **Valid Range** | ≥ 0 (enforced by `ck_prod_metric_fcr_non_negative`); industry target < 1.20 for Atlantic Salmon |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Non-negative; alarm if > 2.0 (inefficiency indicator) |
| **Used By Models** | Harvest Predictor |

### `mortality_rate`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `mortality_rate` |
| **Data Type** | `NUMERIC(6,4)` |
| **Unit** | Fraction (0.0 … 1.0) |
| **Valid Range** | 0 … 1 (enforced by `ck_prod_metric_mortality_range`) |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Range 0–1; spike detection for sudden mortality events |
| **Used By Models** | Disease Risk Predictor, Mortality Predictor |

### `feed_consumption_kg`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `feed_consumption_kg` |
| **Data Type** | `NUMERIC(10,2)` |
| **Unit** | kg |
| **Valid Range** | ≥ 0 (enforced by `ck_prod_metric_feed_non_negative`) |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Non-negative; plausibility against biomass |
| **Used By Models** | Harvest Predictor |

### `population`

| Property | Value |
|---|---|
| **Source Table** | `tank_production_metrics` |
| **Source Column** | `population` |
| **Data Type** | `INTEGER` |
| **Unit** | Count (live fish) |
| **Valid Range** | ≥ 0 (enforced by `ck_prod_metric_population_non_negative`) |
| **Refresh Frequency** | Daily / per-shift |
| **Validation Rules** | Non-negative; population decrease rate consistency with mortality_rate |
| **Used By Models** | Mortality Predictor, Harvest Predictor |

---

## Environmental Features (Aggregated)

Derived from `tank_environment_snapshots` using TimescaleDB time-bucket aggregation.

### `avg_temperature_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `temperature` (aggregated) |
| **Aggregation** | `AVG()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | PSI Predictor, Disease Risk Predictor |

### `avg_dissolved_oxygen_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `dissolved_oxygen` (aggregated) |
| **Aggregation** | `AVG()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | PSI Predictor, Mortality Predictor |

### `avg_ph_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `ph` (aggregated) |
| **Aggregation** | `AVG()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | PSI Predictor |

### `avg_ammonia_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `ammonia` (aggregated) |
| **Aggregation** | `AVG()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | PSI Predictor, Disease Risk Predictor |

### `avg_acoustic_db_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `acoustic_db` (aggregated) |
| **Aggregation** | `AVG()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | Hydrophone Intelligence |

### `acoustic_db_std_1h`

| Property | Value |
|---|---|
| **Source Table** | `tank_environment_snapshots` |
| **Source Column** | `acoustic_db` (aggregated) |
| **Aggregation** | `STDDEV()` over 1-hour time bucket |
| **Feature Group** | `environmental` |
| **Used By Models** | Hydrophone Intelligence (stability scoring) |

---

## Engineered Features

Computed features stored in `ml_feature_store` with `feature_group = 'engineered'`.

### `temp_rolling_mean_1h`

| Property | Value |
|---|---|
| **Derivation** | Rolling mean of `temperature` over trailing 1-hour window |
| **Source Feature** | `temperature` |
| **Feature Group** | `engineered` |
| **Used By Models** | PSI Predictor |

### `do_lag_15m`

| Property | Value |
|---|---|
| **Derivation** | Dissolved oxygen value lagged by 15 minutes |
| **Source Feature** | `dissolved_oxygen` |
| **Feature Group** | `engineered` |
| **Used By Models** | PSI Predictor |

### `ammonia_velocity`

| Property | Value |
|---|---|
| **Derivation** | Rate of change (first derivative) of ammonia concentration over 30-minute window |
| **Source Feature** | `ammonia` |
| **Feature Group** | `engineered` |
| **Used By Models** | Disease Risk Predictor |

### `psi_ma_7d`

| Property | Value |
|---|---|
| **Derivation** | 7-day moving average of PSI score |
| **Source Feature** | `psi_predictions.psi_score` |
| **Feature Group** | `engineered` |
| **Used By Models** | Mortality Predictor |

### `temp_do_interaction`

| Property | Value |
|---|---|
| **Derivation** | Interaction term: `temperature × dissolved_oxygen` |
| **Source Features** | `temperature`, `dissolved_oxygen` |
| **Feature Group** | `engineered` |
| **Used By Models** | PSI Predictor |

### `growth_rate_daily`

| Property | Value |
|---|---|
| **Derivation** | `(average_weight_g[t] − average_weight_g[t−1]) / 1 day` |
| **Source Feature** | `average_weight_g` |
| **Feature Group** | `engineered` |
| **Used By Models** | Harvest Predictor, Mortality Predictor |

### `biomass_trajectory`

| Property | Value |
|---|---|
| **Derivation** | Linear regression slope of `biomass_kg` over trailing 14-day window |
| **Source Feature** | `biomass_kg` |
| **Feature Group** | `engineered` |
| **Used By Models** | Harvest Predictor |

### `water_quality_index`

| Property | Value |
|---|---|
| **Derivation** | Composite score (0–100) computed from DO, pH, ammonia, temperature, salinity variance over 7 days (per `TelemetryService.calculate_water_quality_index`) |
| **Source Features** | `dissolved_oxygen`, `ph`, `ammonia`, `temperature`, `salinity` |
| **Feature Group** | `engineered` |
| **Used By Models** | Disease Risk Predictor, Mortality Predictor, Harvest Predictor |

### `mortality_trend_7d`

| Property | Value |
|---|---|
| **Derivation** | 7-day linear trend slope of `mortality_rate` |
| **Source Feature** | `mortality_rate` |
| **Feature Group** | `engineered` |
| **Used By Models** | Mortality Predictor, Disease Risk Predictor |

### `fcr_deviation`

| Property | Value |
|---|---|
| **Derivation** | `(current_fcr − baseline_fcr) / baseline_fcr` where baseline is species-specific (1.20 for Atlantic Salmon) |
| **Source Feature** | `fcr` |
| **Feature Group** | `engineered` |
| **Used By Models** | Harvest Predictor |

### `acoustic_stability_score`

| Property | Value |
|---|---|
| **Derivation** | `max(0, min(100, 100 − (acoustic_db_std × 5.0)))` (per `TelemetryService.get_acoustic_analytics_data`) |
| **Source Feature** | `acoustic_db` (std dev) |
| **Feature Group** | `engineered` |
| **Used By Models** | Hydrophone Intelligence |

### `bio_acoustic_deviation`

| Property | Value |
|---|---|
| **Derivation** | `abs(current_bio_acoustic_sync − baseline_sync)` where baseline is the tank's historical median |
| **Source Feature** | `bio_acoustic_sync` |
| **Feature Group** | `engineered` |
| **Used By Models** | Hydrophone Intelligence |

---

## Feature-to-Model Matrix

| Feature | PSI | Disease | Mortality | Harvest | Hydrophone |
|---|:---:|:---:|:---:|:---:|:---:|
| `temperature` | ● | ● | ● | ● | |
| `ph` | ● | ● | | | |
| `dissolved_oxygen` | ● | ● | ● | | |
| `ammonia` | ● | ● | | | |
| `salinity` | ● | | | | |
| `turbidity` | ● | ● | | | |
| `acoustic_db` | | | | | ● |
| `bio_acoustic_sync` | | | | | ● |
| `biomass_kg` | | | ● | ● | |
| `average_weight_g` | | | | ● | |
| `fcr` | | | | ● | |
| `mortality_rate` | | ● | ● | | |
| `feed_consumption_kg` | | | | ● | |
| `population` | | | ● | ● | |
| `temp_rolling_mean_1h` | ● | | | | |
| `do_lag_15m` | ● | | | | |
| `ammonia_velocity` | | ● | | | |
| `psi_ma_7d` | | | ● | | |
| `temp_do_interaction` | ● | | | | |
| `growth_rate_daily` | | | ● | ● | |
| `biomass_trajectory` | | | | ● | |
| `water_quality_index` | | ● | ● | ● | |
| `mortality_trend_7d` | | ● | ● | | |
| `fcr_deviation` | | | | ● | |
| `acoustic_stability_score` | | | | | ● |
| `bio_acoustic_deviation` | | | | | ● |
