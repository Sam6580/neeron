# NEERON Recommendation Engine Architecture

> Design specification for the AI-driven recommendation engine.
> Grounded against existing tables: `recommendations`, `recommendation_actions`,
> `recommendation_feedback`, `historical_cases`, `case_matches`, `ai_insights`.

---

## 1. System Overview

The recommendation engine is the final stage of the NEERON ML pipeline. It transforms raw predictions into actionable operational guidance for farm operators. The engine operates as a multi-stage pipeline that evaluates risk, matches historical precedents, generates human-readable insights, and ranks recommendations by urgency and confidence.

The engine is designed around a closed feedback loop: operators respond to recommendations, rate their effectiveness, and this feedback is aggregated to improve future recommendation quality during model retraining.

---

## 2. Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   RECOMMENDATION ENGINE PIPELINE                         │
└──────────────────────────────────────────────────────────────────────────┘

  Stage 1                Stage 2                  Stage 3
  ┌─────────────┐        ┌───────────────────┐    ┌──────────────────┐
  │ Prediction  │───────▶│ Risk Assessment   │───▶│ Historical Case  │
  │ Models      │        │                   │    │ Matching (CBR)   │
  │             │        │ PSI > 2.0?        │    │                  │
  │ PSI         │        │ Disease > 0.35?   │    │ case_matches     │
  │ Disease     │        │                   │    │ historical_cases │
  │ Mortality   │        │                   │    │                  │
  │ Harvest     │        │                   │    │ similarity_score │
  └─────────────┘        └───────────────────┘    └────────┬─────────┘
                                                           │
  Stage 6                Stage 5                  Stage 4  │
  ┌─────────────┐        ┌───────────────────┐    ┌───────▼──────────┐
  │ Feedback    │◀───────│ Operator Action   │◀───│ AI Insight       │
  │ Loop        │        │                   │    │ Generation       │
  │             │        │ recommendation_   │    │                  │
  │ recommend-  │        │ actions           │    │ ai_insights      │
  │ ation_      │        │                   │    │                  │
  │ feedback    │        │ Accept / Reject / │    │ title            │
  │             │        │ Ignore            │    │ description      │
  │ effective-  │        │                   │    │ priority         │
  │ ness_score  │        │                   │    │ confidence       │
  └─────────────┘        └───────────────────┘    └──────────────────┘
                                                           │
                                                           ▼
                                                  ┌──────────────────┐
                                                  │ Recommendation   │
                                                  │ Ranking &        │
                                                  │ Delivery         │
                                                  │                  │
                                                  │ recommendations  │
                                                  │ - action         │
                                                  │ - confidence     │
                                                  │ - priority       │
                                                  │ - status         │
                                                  └──────────────────┘
```

---

## 3. Stage Descriptions

### Stage 1: Prediction Ingestion

The recommendation engine is triggered by the `RecommendationEngineService.generate_recommendations(tank_id)` method. It queries the latest predictions from:

| Prediction Source | Trigger Condition | Priority Mapping |
|---|---|---|
| `PsiPrediction` | `psi_score > 2.0` (Mild Stress threshold) | 2.0–3.0: Medium, 3.0–4.0: High, ≥ 4.0: Critical |
| `DiseasePrediction` | `probability > 0.35` | 0.25–0.50: Medium, 0.50–0.75: High, ≥ 0.75: Critical |
| `MortalityPrediction` | Future: `mortality_probability > 0.15` | Planned |
| `HarvestPrediction` | Future: approaching harvest date | Planned |

The `PredictionRepository` provides the latest prediction for each type:
- `get_latest_psi(tank_id)`
- `get_latest_disease_prediction(tank_id)`
- `get_latest_mortality_prediction(tank_id)`
- `get_latest_harvest_prediction(tank_id)`

### Stage 2: Risk Assessment

The `score_recommendation_priority()` method evaluates prediction severity and maps it to the recommendation priority level:

```
Priority Scoring Algorithm:

PSI-based:
  psi_score ≥ 4.0  → "Critical"
  psi_score ≥ 3.0  → "High"
  psi_score ≥ 2.0  → "Medium"
  otherwise        → "Low"

Disease-based:
  probability ≥ 0.75  → "Critical"
  probability ≥ 0.50  → "High"
  probability ≥ 0.25  → "Medium"
  otherwise           → "Low"
```

The `calculate_expected_impact()` method estimates the improvement that following the recommendation would produce:

| Prediction Type | Impact Formula | Example |
|---|---|---|
| PSI | `score × 0.12` | PSI 5.0 → 60% expected improvement |
| Disease | `probability × 0.60` | Prob 0.80 → 48% reduction in outbreak risk |

### Stage 3: Historical Case Matching (CBR Engine)

The Case-Based Reasoning engine searches the `historical_cases` catalog for past incidents similar to the current prediction context.

**How matching works:**

The `match_historical_cases(tank_id, prediction_id, prediction_type)` method:

1. Retrieves up to 50 historical cases from the `historical_cases` table.
2. Filters by `scenario_type` relevance to the prediction type:

| Prediction Type | Matched Scenario Types |
|---|---|
| `psi` | `Dissolved Oxygen Depletion`, `High Ammonia Event`, `Thermal Stress` |
| `disease` | `Gill Disease`, `Sea Lice Influx` |
| `mortality` | All scenarios |
| `harvest` | All scenarios |

3. Calculates a `similarity_score` ∈ [0.0, 1.0] for each matched case.
4. Writes `CaseMatch` records to the `case_matches` hypertable with:
   - `prediction_id` — UUID of the source prediction (polymorphic reference)
   - `prediction_type` — discriminator: `psi` | `disease` | `mortality` | `harvest`
   - `case_id` — FK → `historical_cases.id`
   - `similarity_score` — computed similarity

**Case catalog structure:**

Each `HistoricalCase` contains:
- `title`: Human-readable case title
- `description`: Detailed incident narrative
- `scenario_type`: Machine-readable category for matching
- `severity`: `Low` | `Medium` | `High` | `Critical`
- `outcome`: What happened (observable result)
- `resolution`: Step-by-step corrective actions taken

The resolution text from matched cases is used as the basis for recommendation action text.

### Stage 4: AI Insight Generation

The `AiInsightService` synthesizes predictions, risk assessments, and case matches into structured human-readable insights:

| Field | Source | Description |
|---|---|---|
| `title` | Derived from prediction type and severity | Short actionable headline (≤ 150 chars) |
| `description` | Template-based narrative using prediction values | Full explanation with supporting evidence |
| `priority` | Mapped from risk assessment | `Info` \| `Medium` \| `High` \| `Critical` |
| `confidence` | From source prediction model | 0.0000 → 1.0000 |
| `source_model_id` | FK → `model_versions.id` | MLOps traceability |
| `historical_case_id` | FK → `historical_cases.id` | CBR linkage (if applicable) |
| `expires_at` | Calculated TTL based on priority | Transient insights auto-suppress |

Insights are stored in the `ai_insights` hypertable (30-day chunk partitioning) and are exposed via:
- `GET /api/v1/insights/dashboard` — farm-level summary
- `GET /api/v1/insights/tank` — per-tank detail

### Stage 5: Recommendation Generation and Ranking

The engine produces `Recommendation` records with the following fields:

| Field | Type | Description |
|---|---|---|
| `action` | `VARCHAR(200)` | Imperative action title (e.g., "Adjust aeration flow rate") |
| `expected_outcome` | `TEXT` | Narrative description of expected improvement |
| `confidence` | `NUMERIC(5,4)` | Model confidence score |
| `priority` | `VARCHAR(50)` | `Low` \| `Medium` \| `High` \| `Critical` |
| `status` | `VARCHAR(50)` | Lifecycle: `Pending` → `Accepted` \| `Dismissed` \| `Completed` |
| `generated_by_model` | `UUID` | FK → `model_versions.id` |

**Recommendation ranking algorithm:**

Recommendations are ranked for display using a composite score:

```
display_rank = priority_weight × confidence × recency_factor

Where:
  priority_weight = { Critical: 4, High: 3, Medium: 2, Low: 1 }
  confidence     = recommendation.confidence (0.0 – 1.0)
  recency_factor = 1.0 − (hours_since_generation / 168)  # decays over 7 days
```

Critical-priority recommendations always appear first regardless of recency.

### Stage 6: Operator Actions and Feedback Loop

**Operator actions** (`recommendation_actions` table):

When an operator responds to a recommendation in the UI, a `RecommendationAction` record is created:

| Field | Type | Description |
|---|---|---|
| `action` | `VARCHAR` | `Accepted` \| `Rejected` \| `Ignored` |
| `user_id` | `UUID` FK → `users.id` | Which operator responded (RESTRICT delete) |
| `executed_at` | `TIMESTAMPTZ` | When the action was taken |

**Operator feedback** (`recommendation_feedback` table):

After a recommendation is completed or dismissed, the operator provides structured feedback:

| Field | Type | Description |
|---|---|---|
| `action_taken` | `VARCHAR(100)` | `Applied Remediation` \| `Alternative Action Taken` \| `Ignored - False Alarm` \| `Ignored - Operational Constraints` |
| `effectiveness_score` | `INTEGER` | 1 (not effective) … 5 (highly effective) |
| `comments` | `TEXT` | Optional free-text narrative |
| `user_id` | `UUID` FK → `users.id` | Feedback author (RESTRICT delete) |

---

## 4. Confidence Scoring

Confidence is propagated through the pipeline from model output to final recommendation:

```
Model Output Confidence
  ↓ (0.0 – 1.0)
Prediction Confidence (stored in prediction table)
  ↓
CBR Similarity Score (0.0 – 1.0, stored in case_matches)
  ↓ combined
Insight Confidence = prediction_confidence × similarity_weight
  ↓
Recommendation Confidence = insight_confidence × impact_factor
```

Where:
- `similarity_weight` = average `similarity_score` of top-3 matched cases (1.0 if no cases matched)
- `impact_factor` = `calculate_expected_impact()` output, capped at 1.0

### Confidence Calibration

Model confidence is validated against actual outcomes during model retraining:

| Confidence Range | Expected Accuracy | Calibration Action |
|---|---|---|
| 0.90 – 1.00 | > 90% of recommendations effective | Well calibrated |
| 0.75 – 0.89 | > 75% of recommendations effective | Acceptable |
| < 0.75 | Recommendation flagged as uncertain | UI displays confidence warning |

---

## 5. Priority Ranking

Priorities are assigned based on the severity of the triggering prediction and the urgency of the recommended action:

| Priority | Trigger Criteria | SLA | UI Treatment |
|---|---|---|---|
| `Critical` | PSI ≥ 4.0 or Disease prob ≥ 0.75 | Immediate operator notification | Red badge, push notification, audible alert |
| `High` | PSI ≥ 3.0 or Disease prob ≥ 0.50 | Within 4 hours | Orange badge, dashboard banner |
| `Medium` | PSI ≥ 2.0 or Disease prob ≥ 0.25 | Within 24 hours | Yellow indicator in recommendations panel |
| `Low` | Below all thresholds | Advisory | Listed in recommendations panel, no alert |

---

## 6. Recommendation Learning Cycle

The feedback loop operates as a continuous improvement system:

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDATION LEARNING CYCLE                          │
│                                                                           │
│  Week N:                                                                  │
│    1. Model generates predictions → Recommendations created               │
│    2. Operators respond (Accept/Reject/Ignore)                            │
│    3. Operators rate effectiveness (1-5 scale)                            │
│                                                                           │
│  Week N+1:                                                                │
│    4. Retraining pipeline queries recommendation_feedback                 │
│    5. Recommendations with effectiveness_score ≥ 4 → positive labels      │
│    6. Recommendations with effectiveness_score ≤ 2 → negative labels      │
│    7. Model weights adjusted based on outcome labels                      │
│    8. Updated model version deployed to Production                        │
│                                                                           │
│  Continuous:                                                              │
│    9. model_health_metrics tracks recommendation acceptance rate           │
│   10. Declining acceptance triggers retraining investigation              │
└───────────────────────────────────────────────────────────────────────────┘
```

### Feedback Aggregation

During model retraining, `recommendation_feedback` is aggregated to create outcome labels:

| Feedback Category | effectiveness_score | Training Label |
|---|---|---|
| `Applied Remediation` | 4–5 | Strong positive (weight 1.0) |
| `Applied Remediation` | 1–3 | Weak positive (weight 0.5) |
| `Alternative Action Taken` | 4–5 | Moderate positive (weight 0.7) — the problem was real but the action was suboptimal |
| `Ignored - False Alarm` | Any | Strong negative (weight 1.0) — model produced a false positive |
| `Ignored - Operational Constraints` | Any | Neutral (weight 0.0) — excluded from retraining |

### Acceptance Rate Monitoring

The percentage of recommendations that are `Accepted` or receive `Applied Remediation` feedback is tracked as a key MLOps metric:

| Acceptance Rate | Interpretation | Action |
|---|---|---|
| > 70% | Healthy system — operators trust recommendations | Continue normal operations |
| 50–70% | Declining trust — possible model drift | Increase retraining frequency |
| < 50% | System credibility at risk | Manual model audit; halt automated recommendations |

---

## 7. Table Mapping

Every table referenced by the recommendation engine:

| Table | Role | Hypertable | Chunk Interval |
|---|---|---|---|
| `recommendations` | Stores generated recommendations | Yes | 30 days |
| `recommendation_actions` | Records operator Accept/Reject/Ignore | Yes | 30 days |
| `recommendation_feedback` | Captures effectiveness ratings | Yes | 30 days |
| `historical_cases` | CBR case catalog (curated) | No | N/A |
| `case_matches` | Prediction-to-case similarity links | Yes | 30 days |
| `ai_insights` | Intermediate structured insights | Yes | 30 days |
| `psi_predictions` | PSI input to recommendation engine | Yes | 7 days |
| `disease_predictions` | Disease risk input | Yes | 14 days |
| `mortality_predictions` | Mortality input (future) | Yes | 14 days |
| `harvest_predictions` | Harvest input (future) | Yes | 30 days |
| `model_versions` | MLOps traceability FK target | No | N/A |

---

## 8. API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/v1/recommendations/` | GET | List recommendations with status and priority filters |
| `POST /api/v1/recommendations/{id}/accept` | POST | Operator accepts a pending recommendation |
| `POST /api/v1/recommendations/{id}/dismiss` | POST | Operator dismisses a recommendation |
| `GET /api/v1/insights/dashboard` | GET | Farm-level AI insight summary |
| `GET /api/v1/insights/tank` | GET | Per-tank AI insight detail |
