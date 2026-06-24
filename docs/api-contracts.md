# NEERON — REST & WebSocket API Specification
## Enterprise API Contract & Interfaces (Version 2.0)

This document establishes the official API contract between the **Next.js 15 Frontend**, the **FastAPI Backend**, the **PostgreSQL + TimescaleDB Database**, and downstream **AI/ML Inference Services** for NEERON (Neural Ecosystem Environmental Response & Optimization Network).

---

## Section 1: API Design Principles

The NEERON API follows REST conventions, using JSON for data exchange and standard HTTP status codes.

### 1.1 Base URL & Versioning Strategy
All APIs are versioned using a URL prefix to avoid breaking changes when updating schemas:
```text
https://api.neeron.ai/api/v1
```

### 1.2 Resource Naming Conventions
Endpoints represent resources using plural nouns. Nested relationships are represented by hierarchical paths:
*   `GET /api/v1/tanks` (Get all tanks)
*   `GET /api/v1/tanks/{id}/telemetry` (Get telemetry for a specific tank)

### 1.3 Pagination Structure
Endpoints returning lists use offset-based pagination. Clients control pagination via query parameters:
*   `page`: The page number, 1-indexed (Default: `1`)
*   `limit`: The number of items per page (Default: `20`, Max: `100`)

Paginated responses wrap results in a standard metadata object:
```json
{
  "success": true,
  "timestamp": "2026-06-24T04:30:00Z",
  "data": [],
  "pagination": {
    "currentPage": 1,
    "totalPages": 5,
    "limit": 20,
    "totalCount": 85
  }
}
```

### 1.4 Filtering & Sorting Conventions
*   **Filtering**: Passed as query parameters using operators: `field=op:value`. Supported operators include `eq` (equal), `gt` (greater than), `lt` (less than), and `in` (comma-separated list).
    *   *Example*: `/api/v1/alerts?severity=eq:Critical&status=eq:unresolved`
*   **Sorting**: Controlled via the `sort` parameter. Multi-field sorting uses comma-separated fields. A minus prefix (`-`) denotes descending order.
    *   *Example*: `/api/v1/tanks?sort=-current_biomass,name` (Sort by biomass descending, then name ascending)

---

## Section 2: Standard Response Format

The API uses three standard response wrappers to ensure consistent client-side parsing.

### 2.1 Success Response Schema (HTTP 200/201)
```json
{
  "success": true,
  "timestamp": "2026-06-24T04:31:00Z",
  "data": {
    "id": "8f3d6b1d-25a8-444f-8cf8-0524d77d7042",
    "name": "TNK-01-DO"
  }
}
```

### 2.2 Error Response Schema (HTTP 400/401/403/404/500)
Used for business logic errors, resource missing exceptions, and internal crashes.
```json
{
  "success": false,
  "timestamp": "2026-06-24T04:31:05Z",
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "The requested Tank resource could not be located.",
    "details": {
      "tank_id": "8f3d6b1d-25a8-444f-8cf8-0524d77d7042"
    }
  }
}
```

### 2.3 Validation Error Response Schema (HTTP 422 Unprocessable Entity)
Used when request body validation fails (e.g. invalid types or missing parameters).
```json
{
  "success": false,
  "timestamp": "2026-06-24T04:31:10Z",
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "One or more validation checks failed on the payload.",
    "fieldErrors": [
      {
        "field": "critical_min",
        "message": "critical_min must be less than or equal to warning_min."
      }
    ]
  }
}
```

---

## Section 3: Authentication & RBAC

The API uses JSON Web Tokens (JWT) for authentication and access control.

### 3.1 Authorization Workflows
*   **Access Token**: Short-lived JWT (15-minute expiry) passed in the `Authorization: Bearer <TOKEN>` header.
*   **Refresh Token**: Long-lived token (7-day expiry) stored in a secure, HTTP-only cookie (`/api/v1/auth/refresh`).

### 3.2 Role-Based Access Control (RBAC) Permissions Matrix

| Resource | Viewer | Biologist | Aquaculture Analyst | Operations Manager | Administrator |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Telemetry / Dashboards** | Read | Read | Read | Read | Read |
| **Tanks / Sensors** | Read | Read | Read | Read / Write | Read / Write |
| **Thresholds** | Read | Read | Read | Read / Write | Read / Write |
| **Biosecurity / Inspections** | Read | Read / Write | Read | Read / Write | Read / Write |
| **Recommendations (Actions)** | None | Read | Read | Read / Resolve | Read / Resolve |
| **AI Model Triggering** | None | None | Read | Read / Retrain | Read / Retrain / Deploy |
| **User Administration** | None | None | None | None | Full Access |

### 3.3 Auth Endpoint Specifications

#### POST `/api/v1/auth/login` (User Login)
*   **Request Headers**: `Content-Type: application/json`
*   **Request Body**:
    ```json
    {
      "email": "sarah.jenkins@neeron.ai",
      "password": "SecurePassword123"
    }
    ```
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:32:00Z",
      "data": {
        "accessToken": "eyJhbGciOiJIUzI1Ni...",
        "expiresIn": 900,
        "user": {
          "id": "e4e94326-6df7-4632-8dfb-b0b3d683dc75",
          "email": "sarah.jenkins@neeron.ai",
          "firstName": "Sarah",
          "lastName": "Jenkins",
          "role": "Biologist"
        }
      }
    }
    ```

#### POST `/api/v1/auth/logout` (User Logout)
*   **Request Headers**: `Authorization: Bearer <token>`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:32:15Z",
      "data": {
        "message": "User successfully logged out. Refresh token cleared."
      }
    }
    ```

#### POST `/api/v1/auth/refresh` (Token Refresh Loop)
*   **Request Cookies**: `refreshToken=<token>`
*   **Response (HTTP 200)**: Pushes a new JWT access token. Same data format as `/login`.

#### GET `/api/v1/auth/me` (Profile Lookup)
*   **Request Headers**: `Authorization: Bearer <token>`
*   **Response (HTTP 200)**: Returns current authenticated user and assigned farm mappings.

---

## Section 4: Farm & Zone Management APIs

Supports multi-tenant scaling (e.g. Scotland, Norway, Chile operations).

#### GET `/api/v1/farms` (List all Farms)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:32:30Z",
      "data": [
        {
          "id": "f101c842-9ef8-7dd9-60e2-0524d77da342",
          "name": "Hardanger Marine Farm",
          "latitude": 60.124500,
          "longitude": 6.182400,
          "timezone": "Europe/Oslo",
          "carryingCapacityKg": 250000.00
        }
      ]
    }
    ```

#### GET `/api/v1/farms/{id}` (Get Farm Details)
*   **Response (HTTP 200)**: Returns details of a specific farm.

#### GET `/api/v1/farms/{id}/zones` (List Zones in a Farm)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:32:45Z",
      "data": [
        {
          "id": "c8b4fd42-6ef8-4aa9-90d2-0524d77d7042",
          "name": "RAS Sector A",
          "description": "Recirculating Aquaculture System nursery segment."
        }
      ]
    }
    ```

#### GET `/api/v1/zones/{id}` (Get Zone Details)
*   **Response (HTTP 200)**: Returns details of a specific zone.

#### GET `/api/v1/zones/{id}/tanks` (List Tanks in a Zone)
*   **Response (HTTP 200)**: Returns all cages/tanks nested within a zone.

---

## Section 5: Dashboard API

Provides the primary data payload for the Home Command Center dashboard in a single network request.

#### GET `/api/v1/dashboard`
*   **Request Headers**: `Authorization: Bearer <token>`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:33:00Z",
      "data": {
        "farmHealthScore": {
          "score": 87.4,
          "trendPercent": 1.2,
          "classification": "Optimal"
        },
        "activeAlertsCount": 3,
        "activeRecommendationsCount": 2,
        "averagePsi": 2.14,
        "waterQualitySummary": {
          "avgTemperature": 11.2,
          "avgDissolvedOxygen": 8.4,
          "avgPh": 7.2,
          "avgSalinity": 32.1,
          "avgAmmonia": 0.012
        },
        "zoneOverview": [
          {
            "zoneId": "c8b4fd42-6ef8-4aa9-90d2-0524d77d7042",
            "name": "Bodø RAS Sector A",
            "tankCount": 4,
            "biomassKg": 12450.0,
            "status": "Warning"
          }
        ],
        "recentInsights": [
          {
            "id": "e402d842-8ef8-6cc9-70f2-0524d77d9242",
            "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
            "tankName": "Cage-05",
            "priority": "High",
            "title": "Oxygen Depletion Risk",
            "description": "Dissolved oxygen is falling. Turn on aeration controllers within 2 hours."
          }
        ]
      }
    }
    ```

---

## Section 6: Tank Management APIs

Manages configuration, status lookup, and telemetry logs for individual fish tanks and sea cages.

#### GET `/api/v1/tanks` (List Tanks)
*   **Query Parameters**: `zone_id` (filter), `type` (filter), `page`, `limit`, `sort`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:34:00Z",
      "data": [
        {
          "id": "a102d842-9ef8-7dd9-60e2-0524d77da342",
          "name": "Cage-05",
          "type": "Sea Cage",
          "volumeM3": 2500.0,
          "maxBiomassKg": 25000.0,
          "species": "Atlantic Salmon",
          "currentBiomassKg": 18200.0,
          "healthStatus": "Warning"
        }
      ],
      "pagination": {
        "currentPage": 1,
        "totalPages": 1,
        "limit": 20,
        "totalCount": 1
      }
    }
    ```

#### GET `/api/v1/tanks/{id}` (Get Tank Detail)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:34:10Z",
      "data": {
        "id": "a102d842-9ef8-7dd9-60e2-0524d77da342",
        "name": "Cage-05",
        "type": "Sea Cage",
        "volumeM3": 2500.0,
        "maxBiomassKg": 25000.0,
        "species": "Atlantic Salmon",
        "digitalTwinConfig": {
          "waterFlowRate": 1.2,
          "targetOxygenLevel": 8.0
        },
        "created_at": "2026-01-10T12:00:00Z"
      }
    }
    ```

#### GET `/api/v1/tanks/{id}/telemetry` (Get Tank Telemetry)
*   **Query Parameters**: `resolution` (5s, 1h, 1d), `start_time`, `end_time`
*   **Response (HTTP 200)**: Returns time-series environment snapshots from `tank_environment_snapshots`.

#### GET `/api/v1/tanks/{id}/production` (Get Tank Production History)
*   **Query Parameters**: `start_time`, `end_time`
*   **Response (HTTP 200)**: Returns list of historical `tank_production_metrics` rows.

---

## Section 7: Telemetry APIs

Provides aggregated environmental snapshots for the analytics engine.

#### GET `/api/v1/telemetry/latest` (Latest Tank Snapshots)
*   **Query Parameters**: `tank_id` (required)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:35:00Z",
      "data": {
        "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
        "capturedAt": "2026-06-24T04:34:55Z",
        "metrics": {
          "temperature": 11.45,
          "ph": 7.18,
          "dissolvedOxygen": 8.42,
          "salinity": 32.10,
          "ammonia": 0.0125,
          "turbidity": 4.12
        }
      }
    }
    ```

#### GET `/api/v1/telemetry/history` (Historical Range Queries)
*   **Query Parameters**: `tank_id` (required), `start_time`, `end_time`, `bucket_width` (1m, 1h, 1d)
*   **Response (HTTP 200)**: Returns aggregated environmental snapshots over the specified time range.

---

## Section 8: Analytics & Prediction APIs

Provides data for the forecasting charts and tables on the Analytics page.

#### GET `/api/v1/analytics/biomass` (Biomass Growth S-Curves)
*   **Query Parameters**: `tank_id` (required), `horizon_days` (30, 90, 180)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:36:00Z",
      "data": {
        "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
        "harvestTargetKg": 25000.0,
        "projectedHarvestWindow": {
          "startDate": "2026-08-01",
          "endDate": "2026-08-15"
        },
        "points": [
          {
            "timestamp": "2026-06-24T00:00:00Z",
            "type": "historical",
            "biomassKg": 18200.0,
            "confidenceLow": 18200.0,
            "confidenceHigh": 18200.0
          },
          {
            "timestamp": "2026-07-01T00:00:00Z",
            "type": "forecast",
            "biomassKg": 19400.0,
            "confidenceLow": 18900.0,
            "confidenceHigh": 19900.0
          }
        ]
      }
    }
    ```

#### GET `/api/v1/predictions/disease` (Disease Risk Predictions)
*   **Query Parameters**: `tank_id`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:36:15Z",
      "data": [
        {
          "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
          "pathogenId": "p101c842-9ef8-7dd9-60e2-0524d77da342",
          "scientificName": "Caligus rogercresseyi",
          "probability": 0.4215,
          "confidenceLow": 0.3800,
          "confidenceHigh": 0.4600,
          "time": "2026-06-24T04:00:00Z"
        }
      ]
    }
    ```

#### GET `/api/v1/predictions/mortality` (Mortality Risk Forecasts)
*   **Query Parameters**: `tank_id`
*   **Response (HTTP 200)**: Returns 7D, 14D, and 30D mortality rate projections.

#### GET `/api/v1/predictions/harvest` (Harvest Growth Curve Predictions)
*   **Query Parameters**: `tank_id`
*   **Response (HTTP 200)**: Returns estimated harvest weight, projected biomass, FCR metrics, and revenue predictions.

---

## Section 9: PSI (Physiological Stress Index) APIs

Provides stress level predictions and explains which environmental factors are contributing to fish stress.

#### GET `/api/v1/psi/{tankId}/history` (Historical Stress Levels)
*   **Query Parameters**: `limit` (default: 24)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:37:00Z",
      "data": {
        "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
        "history": [
          {
            "timestamp": "2026-06-24T04:00:00Z",
            "psiScore": 4.12,
            "stressLevel": "Mild Stress",
            "confidence": 0.9412
          }
        ]
      }
    }
    ```

#### GET `/api/v1/psi/{tankId}/factors` (Explainable AI Stress Factors)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:37:15Z",
      "data": {
        "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
        "psiScore": 6.80,
        "stressLevel": "Severe Stress",
        "factors": [
          {
            "factorName": "dissolved_oxygen",
            "contribution": 3.42,
            "importanceScore": 0.85
          },
          {
            "factorName": "temperature",
            "contribution": 2.18,
            "importanceScore": 0.72
          }
        ]
      }
    }
    ```

---

## Section 10: Biosecurity APIs

Provides biosecurity logs, risk assessments, and compliance information.

#### GET `/api/v1/biosecurity` (Overview Dashboard)
*   **Response (HTTP 200)**: Returns active incident counts, compliance status, and cage risk levels.

#### GET `/api/v1/biosecurity/pathogens` (Pathogen Catalog)
*   **Response (HTTP 200)**: Returns a list of pathogens (e.g. Sea lice, AGD) alongside their risk thresholds.

#### GET `/api/v1/biosecurity/outbreaks` (Active Incidents & Outbreaks)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:38:00Z",
      "data": [
        {
          "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
          "pathogenScientificName": "Caligus rogercresseyi",
          "currentPathogenCount": 8.2,
          "riskThreshold": 5.0,
          "status": "Critical",
          "quarantineActive": true
        }
      ]
    }
    ```

---

## Section 11: Case-Based Reasoning (CBR) APIs

Exposes historical case matched profiles to support resolution audits.

#### GET `/api/v1/cases` (Search Historical Cases)
*   **Query Parameters**: `scenario_type`, `search`
*   **Response (HTTP 200)**: Returns past anomalies and the action procedures taken to resolve them.

#### GET `/api/v1/cases/{id}` (Get Single Case Details)
*   **Response (HTTP 200)**: Returns title, description, outcomes, and resolution steps for a historical case.

#### GET `/api/v1/tanks/{id}/case-matches` (Matched Cases for Predictions)
*   **Query Parameters**: `prediction_id`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:38:30Z",
      "data": [
        {
          "caseId": "c101c842-9ef8-7dd9-60e2-0524d77da342",
          "title": "Dissolved Oxygen Depletion Recovery",
          "similarityScore": 0.9425,
          "resolution": "Increased aeration rate to 60Hz and restricted feeding loops by 50%."
        }
      ]
    }
    ```

---

## Section 12: Recommendation Engine APIs

Manages recommendations generated by AI models and processes feedback from operators.

#### GET `/api/v1/recommendations` (List Recommendations)
*   **Query Parameters**: `tank_id`, `status` (`pending`, `resolved`, `dismissed`)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:39:00Z",
      "data": [
        {
          "id": "b103e842-0ef8-8dd9-70e2-0524d77db442",
          "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
          "action": "Increase Aeration",
          "confidence": 0.9412,
          "priority": "High",
          "expectedOutcome": "Increase dissolved oxygen levels by 1.5 mg/L within 2 hours.",
          "status": "pending",
          "generatedAt": "2026-06-24T04:30:00Z"
        }
      ]
    }
    ```

#### POST `/api/v1/recommendations/{id}/feedback` (Submit Operator Feedback Loop)
*   **Request Body**:
    ```json
    {
      "actionTaken": "Applied Remediation",
      "effectivenessScore": 5,
      "comments": "Aerator turned on. Dissolved oxygen levels recovered in 45 minutes."
    }
    ```
*   **Response (HTTP 200)**: Returns success confirmation and writes the entry to the `recommendation_feedback` table.

---

## Section 13: AI Insights APIs

Retrieves insights from the ML models for the frontend feed.

#### GET `/api/v1/insights` (List Insights)
*   **Query Parameters**: `priority`
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:40:00Z",
      "data": [
        {
          "id": "c104f842-1ef8-9dd9-80e2-0524d77dc542",
          "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
          "priority": "High",
          "confidence": 0.92,
          "title": "FCR Divergence Detected",
          "description": "Feed conversion ratio increased by 0.15 over the last 48 hours. Consider reducing feeding duration.",
          "generatedAt": "2026-06-24T04:00:00Z",
          "expiresAt": "2026-06-25T04:00:00Z"
        }
      ]
    }
    ```

---

## Section 14: Notification Center APIs

Manages user notifications and preference overrides.

#### GET `/api/v1/notifications` (Retrieve User Notifications)
*   **Query Parameters**: `page`, `limit`, `is_read`
*   **Response (HTTP 200)**: Returns a list of notifications.

#### PUT `/api/v1/notifications/preferences` (Update Notification Channels)
*   **Request Body**:
    ```json
    {
      "emailEnabled": true,
      "smsEnabled": false,
      "pushEnabled": true,
      "criticalAlertsOnly": true
    }
    ```
*   **Response (HTTP 200)**: Updates `notification_preferences` and returns current settings.

---

## Section 15: Digital Twin APIs

Exposes simulation environments and digital twin parameter states.

#### GET `/api/v1/digital-twins/{tankId}` (Retrieve Digital Twin State)
*   **Response (HTTP 200)**: Returns the current twin configuration and simulated stocking parameters.

#### GET `/api/v1/digital-twins/{tankId}/scenarios` (List Scenario Snapshots)
*   **Response (HTTP 200)**: Returns historical simulations (biomass, oxygen levels, growth projections) run on the tank.

#### POST `/api/v1/digital-twins/{tankId}/simulate` (Trigger Simulation Run)
*   **Request Body**:
    ```json
    {
      "scenarioName": "Severe Heatwave DO Depletion",
      "simulationDays": 14,
      "customParams": {
        "waterTempOffset": 2.5,
        "oxygenFlowRate": 0.8
      }
    }
    ```
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:42:00Z",
      "data": {
        "simulatedAt": "2026-06-24T04:42:00Z",
        "results": [
          {
            "day": 1,
            "projectedOxygenMgL": 7.82,
            "criticalStatus": "Safe"
          },
          {
            "day": 7,
            "projectedOxygenMgL": 5.42,
            "criticalStatus": "Warning"
          }
        ]
      }
    }
    ```

---

## Section 16: Settings & Operations APIs

Handles thresholds, hardware calibrations, and model deployment triggers.

#### POST `/api/v1/sensors/{id}/calibrate` (Sensor Calibration)
*   **Request Body**:
    ```json
    {
      "offsetValue": -0.15,
      "variance": 0.02,
      "notes": "Calibrated temperature probe against dry block reference."
    }
    ```
*   **Response (HTTP 200)**: Logs the action in the `calibrations` table and updates `sensors.calibration_due_at`.

#### GET `/api/v1/thresholds` (Retrieve Threshold Settings)
*   **Query Parameters**: `farm_id`
*   **Response (HTTP 200)**: Returns standard thresholds defined in `threshold_configs`.

#### PUT `/api/v1/thresholds` (Modify Threshold Settings)
*   **Request Body**:
    ```json
    {
      "farmId": "f101c842-9ef8-7dd9-60e2-0524d77da342",
      "metricName": "dissolved_oxygen",
      "minimumValue": 0.0,
      "maximumValue": 20.0,
      "warningMin": 6.5,
      "warningMax": 12.0,
      "criticalMin": 5.5,
      "criticalMax": 14.0
    }
    ```
*   **Response (HTTP 200)**: Updates `threshold_configs` and writes a configuration edit to the `audit_logs` table.

---

## Section 17: User Management APIs

Manages system user registrations and role assignments.

#### GET `/api/v1/users` (List Users)
*   **Response (HTTP 200)**: Returns system user list with their role scopes.

#### POST `/api/v1/users` (Create User)
*   **Request Body**:
    ```json
    {
      "email": "alex.rivera@neeron.ai",
      "roleId": "r101c842-9ef8-7dd9-60e2-0524d77da342",
      "firstName": "Alex",
      "lastName": "Rivera"
    }
    ```
*   **Response (HTTP 201)**: Returns the newly created user resource.

---

## Section 18: Alerts APIs

Tracks and updates telemetry alert states.

#### GET `/api/v1/alerts` (List Active Alerts)
*   **Query Parameters**: `status` (`unresolved`, `resolved`), `severity`
*   **Response (HTTP 200)**: Returns a list of alerts.

#### POST `/api/v1/alerts/{id}/resolve` (Resolve Active Alert)
*   **Request Body**:
    ```json
    {
      "resolutionNotes": "Replaced faulty O2 probe with calibrated spare. Telemetry resolved."
    }
    ```
*   **Response (HTTP 200)**: Resolves the alert state in `alerts` and updates the resolving timestamp.

---

## Section 19: MLOps APIs

Tracks model accuracies, performance diagnostics, and retrainings.

#### GET `/api/v1/models/{id}/health` (Model Health Telemetry)
*   **Response (HTTP 200)**:
    ```json
    {
      "success": true,
      "timestamp": "2026-06-24T04:45:00Z",
      "data": {
        "modelId": "m105d842-2ef8-add9-90e2-0524d77dd642",
        "versionTag": "v1.2.4",
        "metrics": {
          "accuracy": 0.9842,
          "precision": 0.9780,
          "recall": 0.9902,
          "f1Score": 0.9841
        },
        "agreementScore": 0.9510,
        "dataQualityScore": 0.9870
      }
    }
    ```

---

## Section 20: WebSocket Architecture

To support real-time dashboards without polling overhead, NEERON uses a persistent WebSocket connection.

### 20.1 Connection Endpoints
```text
wss://api.neeron.ai/ws/telemetry
wss://api.neeron.ai/ws/alerts
wss://api.neeron.ai/ws/recommendations
wss://api.neeron.ai/ws/insights
```

### 20.2 Connection & Authentication Flow
1.  **Handshake**: Client establishes a WebSocket connection, passing the access JWT token as a query parameter:
    ```text
    wss://api.neeron.ai/ws/telemetry?token=eyJhbGciOiJIUzI1Ni...
    ```
2.  **Authentication**: The backend validates the token. If invalid, the connection is closed immediately with a standard close frame: `4001 (Unauthorized)`.

### 20.3 Event Payloads

#### Telemetry Frame (`/ws/telemetry`):
Broadcasts env snapshots every 5 seconds.
```json
{
  "event": "telemetry_update",
  "data": {
    "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
    "capturedAt": "2026-06-24T04:46:00Z",
    "metrics": {
      "temperature": 11.45,
      "dissolvedOxygen": 8.42,
      "ph": 7.18
    }
  }
}
```

#### Alert Frame (`/ws/alerts`):
Broadcasts critical threshold violations immediately.
```json
{
  "event": "alert_triggered",
  "data": {
    "alertId": "al82d842-3ef8-bdd9-80e2-0524d77de742",
    "tankId": "a102d842-9ef8-7dd9-60e2-0524d77da342",
    "severity": "Critical",
    "type": "O2_depletion",
    "message": "Critical dissolved oxygen level detected: 5.12 mg/L"
  }
}
```

### 20.4 Client-Side Reconnection Strategy
To handle network drops, the client uses an **Exponential Backoff with Jitter** strategy:
*   **Base Delay**: 1.5 seconds.
*   **Backoff Multiplier**: 2.0x.
*   **Max Delay**: 60 seconds.
*   **Random Jitter**: $\pm$ 20% to prevent reconnect storms from flooding the gateway.

---

## Section 21: OpenAPI Specification Strategy

FastAPI automatically generates an OpenAPI 3.0 specification from our route definitions and Pydantic models. We group and tag routes to keep the generated documentation organized:

*   **Security Schema**: All REST requests use OAuth2 with Bearer token authentication.
    ```yaml
    securitySchemes:
      BearerAuth:
        type: http
        scheme: bearer
        bearerFormat: JWT
    ```
*   **Documentation Tags**: Routes are grouped into logical tags for clean documentation layout:
    *   `Authentication`: `/auth/*`
    *   `Farms & Zones`: `/farms/*`, `/zones/*`
    *   `Tanks & Telemetry`: `/tanks/*`, `/telemetry/*`
    *   `Predictions & PSI`: `/psi/*`, `/predictions/*`, `/analytics/*`
    *   `Biosecurity & Health`: `/biosecurity/*`
    *   `MLOps & Governance`: `/models/*`, `/settings/*`, `/digital-twins/*`
*   **Auto-generated SDKs**: The frontend team generates TypeScript API clients directly from the OpenAPI schema using `openapi-generator-cli`.

---

## Section 22: Final Deliverables Summary

This specification acts as the single source of truth for integrations across all components of the NEERON platform:

```text
Next.js Frontend  <=== (JSON Models, REST API, WebSockets) ===>  FastAPI Backend
                                                                     ║
                                                                     ╠══=> TimescaleDB
                                                                     ║
                                                                     ╚══=> ML Inference
```

*   **Frontend Team**: Build UI views, dashboards, and forms by referencing these mock response payloads.
*   **Backend Team**: Implement routes and write FastAPI endpoint paths to match this URL design.
*   **ML Engineers**: Direct outputs from predictive pipelines (PSI, Disease, Mortality) to write to the specialized endpoints.
*   **IoT Engineers**: Format MQTT streams to match the sensor identifiers mapped in Section 16.
