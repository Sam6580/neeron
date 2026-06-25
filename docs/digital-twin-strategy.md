# NEERON Digital Twin Strategy

> Architecture design for the Digital Twin simulation capability.
> Grounded against the existing `digital_twin_snapshots` hypertable
> and `tanks.digital_twin_config` JSON column.

---

## 1. Overview

The NEERON Digital Twin is a forward-simulation engine that creates virtual replicas of physical tanks. Operators use it to run what-if scenarios — testing hypothetical interventions (increased feed, reduced stocking, aeration adjustments) against simulated future states before committing to real-world operational changes.

The Digital Twin does not replace the prediction models. Instead, it consumes their outputs as baseline projections and extends them by simulating the downstream effects of operator-defined parameter modifications.

---

## 2. Existing Infrastructure

### `digital_twin_snapshots` Table

The database table already exists as a TimescaleDB hypertable with 30-day chunk partitioning.

| Column | Type | Description |
|---|---|---|
| `id` | `UUID` | Surrogate primary key |
| `simulation_time` | `TIMESTAMPTZ` | Simulated point in time (partition key) — distinct from wall-clock time |
| `tank_id` | `UUID` FK → `tanks.id` | Which tank is being simulated |
| `scenario_name` | `VARCHAR(100)` | Simulation scenario label |
| `simulated_biomass` | `NUMERIC(12,2)` | Projected total live weight (kg) ≥ 0 |
| `simulated_growth` | `NUMERIC(10,4)` | Projected daily growth rate (g/fish/day) ≥ 0 |
| `simulated_oxygen` | `NUMERIC(10,4)` | Projected dissolved oxygen (mg/L) ≥ 0 |

**Indexes:**
- `ix_digital_twin_tank_sim_time` → `(tank_id, simulation_time)` — per-tank simulation queries
- `ix_digital_twin_scenario` → `(scenario_name, simulation_time)` — scenario comparison queries

**Constraints:**
- `ck_dt_biomass_non_negative` — `simulated_biomass >= 0`
- `ck_dt_growth_non_negative` — `simulated_growth >= 0`
- `ck_dt_oxygen_non_negative` — `simulated_oxygen >= 0`

### `tanks.digital_twin_config` Column

Each tank has a `digital_twin_config` JSON column that stores optional simulation parameters:

```json
{
  "growth_model": "von_bertalanffy",
  "oxygen_model": "saturation_curve",
  "feed_efficiency_baseline": 1.15,
  "stocking_density_limit": 25.0,
  "simulation_horizon_days": 90,
  "time_step_hours": 6
}
```

This column is already part of the `Tank` ORM model and can be populated per-tank to customize simulation behavior.

---

## 3. Simulation Architecture

### System Design

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      DIGITAL TWIN ENGINE                                 │
│                                                                          │
│  ┌─────────────┐     ┌────────────────────┐     ┌──────────────────┐    │
│  │ Current     │     │ Scenario           │     │ Simulation       │    │
│  │ State       │────▶│ Parameters         │────▶│ Engine           │    │
│  │             │     │                    │     │                  │    │
│  │ telemetry   │     │ feed_rate_delta    │     │ Growth Model     │    │
│  │ production  │     │ stocking_change    │     │ Oxygen Model     │    │
│  │ predictions │     │ aeration_boost     │     │ FCR Model        │    │
│  │             │     │ temp_adjustment    │     │ Mortality Model  │    │
│  └─────────────┘     └────────────────────┘     └────────┬─────────┘    │
│                                                          │              │
│                                                          ▼              │
│                                              ┌──────────────────────┐   │
│                                              │ digital_twin_        │   │
│                                              │ snapshots            │   │
│                                              │                      │   │
│                                              │ Per time step:       │   │
│                                              │ simulated_biomass    │   │
│                                              │ simulated_growth     │   │
│                                              │ simulated_oxygen     │   │
│                                              └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Input Sources:
  tank_environment_snapshots  → current water quality state
  tank_production_metrics     → current biomass, FCR, population
  psi_predictions             → current stress baseline
  disease_predictions         → current disease risk baseline
  biosecurity_records         → active quarantine / pathogen context

Scenario Definition:
  Operator defines parameter deltas via API
  Stored as scenario_name + configuration JSON

Simulation Loop:
  FOR each time_step FROM now TO (now + horizon):
    1. Apply scenario parameter modifications
    2. Run growth model: project biomass and weight
    3. Run oxygen model: project DO based on biomass load
    4. Run FCR model: project feed efficiency
    5. Run mortality adjustment: apply stress-based mortality overlay
    6. Write DigitalTwinSnapshot row

Output:
  Time-series of simulated states stored in digital_twin_snapshots
  Queryable by (tank_id, scenario_name, simulation_time range)
```

---

## 4. Simulation Models

### Growth Model

Simulates biomass accumulation using the von Bertalanffy growth function, parameterized per-species:

```
W(t+1) = W(t) + growth_rate × feed_efficiency × (1 - mortality_factor) × temp_adjustment

Where:
  growth_rate       = base species growth rate (g/fish/day)
  feed_efficiency   = FCR-derived efficiency factor
  mortality_factor  = daily mortality rate applied to population
  temp_adjustment   = temperature-dependent metabolic scaling factor
```

Input features consumed from current state:
- `average_weight_g` from `tank_production_metrics`
- `temperature` from `tank_environment_snapshots`
- `fcr` from `tank_production_metrics`

### Oxygen Model

Simulates dissolved oxygen dynamics based on biomass oxygen demand:

```
DO(t+1) = DO(t) - oxygen_consumption + aeration_input - decay

Where:
  oxygen_consumption = biomass(t) × respiration_rate_per_kg
  aeration_input     = aeration_capacity × aeration_efficiency
  decay              = organic_matter_decomposition_rate
```

Input features:
- `dissolved_oxygen` from `tank_environment_snapshots`
- `simulated_biomass` from previous time step
- `aeration_boost` from scenario parameters

### FCR Model

Simulates feed conversion trajectory:

```
FCR(t+1) = FCR(t) × (1 + stress_penalty + feed_change_effect)

Where:
  stress_penalty     = f(psi_score) — elevated PSI degrades FCR
  feed_change_effect = operator-defined feed rate delta impact
```

### Mortality Overlay

Applies stress-related mortality adjustment:

```
mortality(t) = baseline_mortality + stress_mortality + disease_mortality

Where:
  baseline_mortality = tank_production_metrics.mortality_rate
  stress_mortality   = f(psi_score) — threshold-based escalation
  disease_mortality  = f(disease_risk_score) — pathogen impact
```

---

## 5. Scenario Management

### Predefined Scenarios

| Scenario Name | Parameters Modified | Purpose |
|---|---|---|
| `Baseline` | None — current trajectory projection | Reference scenario for comparison |
| `Increased Feed +10%` | feed_rate × 1.10 | Evaluate growth acceleration vs. FCR degradation |
| `Reduced Stocking` | population × 0.85 | Evaluate density reduction impact on mortality |
| `Aeration Boost` | aeration_capacity × 1.25 | Evaluate DO improvement under high biomass load |
| `Temperature Stress` | temperature + 2.0°C | Evaluate heat event resilience |
| `Feed Reduction -15%` | feed_rate × 0.85 | Evaluate cost reduction vs. growth impact |

### Custom Scenarios

Operators define custom scenarios via an API endpoint specifying parameter deltas:

```json
{
  "scenario_name": "Summer Heat + Extra Aeration",
  "tank_id": "uuid",
  "horizon_days": 30,
  "parameters": {
    "temperature_delta_c": 3.0,
    "aeration_multiplier": 1.5,
    "feed_rate_multiplier": 0.95
  }
}
```

### Scenario Comparison

Multiple scenarios for the same tank can be compared by querying:

```sql
SELECT scenario_name, simulation_time, simulated_biomass, simulated_growth, simulated_oxygen
FROM digital_twin_snapshots
WHERE tank_id = <tank_id>
  AND simulation_time BETWEEN <start> AND <end>
ORDER BY scenario_name, simulation_time;
```

This produces parallel time-series for charting on the Analytics dashboard.

---

## 6. Validation Strategy

### Back-testing

Validation is performed by running simulations against historical data and comparing predicted vs. actual outcomes:

```
Step 1: Select a completed grow-out cycle (120+ days)
Step 2: Use state at Day 30 as initial conditions
Step 3: Run Baseline scenario for 90 days forward
Step 4: Compare simulated outcomes against actual:
  - simulated_biomass vs. actual biomass_kg at Day 120
  - simulated_growth vs. actual average_weight_g growth rate
  - simulated_oxygen vs. actual dissolved_oxygen range
Step 5: Calculate prediction accuracy metrics:
  - MAPE for biomass projection
  - MAE for growth rate
  - RMSE for DO projection
```

### Validation Acceptance Criteria

| Metric | Target | Description |
|---|---|---|
| Biomass MAPE | < 10% | Simulated biomass within 10% of actual at horizon |
| Growth Rate MAE | < 0.5 g/fish/day | Daily growth rate accuracy |
| DO RMSE | < 0.8 mg/L | Dissolved oxygen projection accuracy |
| Scenario ranking preservation | 100% | If Scenario A is better than B in simulation, it must be better in reality |

### Calibration

Simulation model parameters are calibrated per-farm using historical data:

```
tanks.digital_twin_config = {
  "growth_model": "von_bertalanffy",
  "calibrated_at": "2026-06-01T00:00:00Z",
  "growth_rate_base": 2.8,
  "respiration_rate_per_kg": 0.015,
  "aeration_efficiency": 0.72,
  "organic_decay_rate": 0.003
}
```

Calibration is re-run monthly using the most recent 90-day window of production data.

---

## 7. Integration Points

### Data Sources Consumed

| Source | Table | Columns Used |
|---|---|---|
| Current water quality | `tank_environment_snapshots` | `temperature`, `dissolved_oxygen`, `ph`, `ammonia`, `salinity` |
| Current production state | `tank_production_metrics` | `biomass_kg`, `average_weight_g`, `fcr`, `population`, `mortality_rate` |
| Current stress baseline | `psi_predictions` | `psi_score`, `stress_level` |
| Current disease risk | `disease_predictions` | `risk_score`, `disease_name` |
| Active biosecurity events | `biosecurity_records` | `risk_level`, `pathogen_id` |
| Tank configuration | `tanks` | `volume_m3`, `max_biomass_kg`, `species`, `digital_twin_config` |

### Data Outputs Produced

| Output | Table | Consumed By |
|---|---|---|
| Simulated future states | `digital_twin_snapshots` | Analytics dashboard (scenario comparison charts) |
| Scenario rankings | Derived from `digital_twin_snapshots` | Recommendation engine (future: optimal action selection) |

### API Endpoints (Future)

| Endpoint | Method | Description |
|---|---|---|
| `POST /api/v1/digital-twin/simulate` | POST | Run a simulation scenario for a tank |
| `GET /api/v1/digital-twin/scenarios` | GET | List available scenarios for a tank |
| `GET /api/v1/digital-twin/results` | GET | Retrieve simulation results for comparison |
| `DELETE /api/v1/digital-twin/scenarios/{id}` | DELETE | Remove a custom scenario and its snapshots |

---

## 8. Future Evolution

### Phase 1: Single-Tank Simulation (Current Design)

- One tank at a time
- Deterministic simulation (single trajectory per scenario)
- Growth + Oxygen + FCR + Mortality models

### Phase 2: Multi-Tank Interaction

- Simulate interactions between tanks sharing water systems
- Model cross-contamination dynamics for biosecurity scenarios
- Zone-level aggregate simulations

### Phase 3: Probabilistic Simulation

- Monte Carlo sampling over parameter distributions
- Output confidence intervals instead of point estimates
- Risk quantile charts (P10 / P50 / P90 biomass projections)

### Phase 4: Recommendation Integration

- Digital Twin feeds optimal scenarios into the recommendation engine
- "If you do X, the Digital Twin projects Y improvement in Z days"
- Automated scenario generation based on current prediction alerts
