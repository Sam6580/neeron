# NEERON Backend Architecture Audit

## Scope

Reviewed backend code under:

- `neeron/backend/app/models`
- `neeron/backend/alembic/versions`
- `neeron/backend/app/repositories`
- `neeron/backend/app/services`
- `neeron/backend/app/api/v1`

Validation pass:

- `pytest neeron/backend/tests/api -q` -> `55 passed, 9 warnings`

Note: the API test suite is heavily mocked, so passing tests do not prove repository, migration, transaction, or schema wiring correctness against a real database.

## Executive Summary

- No hard runtime circular import was identified. The models mostly avoid cycles with `TYPE_CHECKING` and deferred imports.
- The largest risks are security and boundary-related:
  - the API has no real authentication or authorization,
  - mutating endpoints use a hard-coded zero UUID for audit attribution,
  - transaction commits are hidden inside the DB dependency,
  - several endpoints fabricate operational data when source data is missing.
- The busiest read paths have multiple N+1 patterns that will degrade quickly as farm, zone, tank, and sensor counts grow.
- Repository and API boundaries are porous: routes reach into repositories and service internals directly, while some repositories contain business defaults and presentation shaping.

## Findings

### Critical

#### 1. No authentication/authorization on the API, and write endpoints spoof the acting user

**Why this matters**

Every router is mounted without a security dependency, and multiple write paths use `00000000-0000-0000-0000-000000000000` as the acting user. In production this means any caller can mutate operational state, and audit trails are not trustworthy.

**References**

- `neeron/backend/app/api/v1/router.py:21-35`
- `neeron/backend/app/api/v1/alerts.py:46-74`
- `neeron/backend/app/api/v1/recommendations.py:54-123`
- `neeron/backend/app/api/v1/settings.py:55-81`

**Recommended fix**

- Add a real auth dependency at router or endpoint level.
- Inject `current_user` into every mutating endpoint.
- Enforce farm/tank scoping in services before reads or writes.
- Remove the zero UUID fallback entirely.

---

### High

#### 2. Transaction boundaries are hidden inside `get_db()`, so any request can commit incidental mutations

**Why this matters**

`get_db()` commits automatically after `yield`. That makes transaction ownership implicit and fragile. A supposedly read-only endpoint can persist accidental ORM mutations, and services cannot clearly define unit-of-work boundaries.

**References**

- `neeron/backend/app/db/session.py:36-46`

**Recommended fix**

- Remove the implicit `commit()` from `get_db()`.
- Let services or explicit unit-of-work helpers own transaction scope.
- Reserve automatic rollback for uncaught exceptions only.

---

#### 3. The API leaks internals and has an unsafe CORS policy

**Why this matters**

- `allow_origins=["*"]` with `allow_credentials=True` is an unsafe configuration for a stateful API.
- The global exception handler returns `str(exc)` to clients, which can leak implementation details, SQL messages, and sensitive operational context.

**References**

- `neeron/backend/app/main.py:42-47`
- `neeron/backend/app/main.py:104-115`

**Recommended fix**

- Replace wildcard CORS with an explicit allowlist from configuration.
- Disable credentialed wildcard access.
- Return a generic 500 payload to clients and log the real exception server-side with the request ID.

---

#### 4. Several endpoints fabricate live operational values instead of reporting missing data

**Why this matters**

Routes return invented temperatures, oxygen, salinity, PSI estimates, tank names, and pathogen counts when real data is absent. For an aquaculture operations backend, fabricated telemetry is worse than an empty response.

**References**

- `neeron/backend/app/api/v1/telemetry.py:35-50`
- `neeron/backend/app/api/v1/dashboard.py:39-46`
- `neeron/backend/app/api/v1/dashboard.py:61-69`
- `neeron/backend/app/api/v1/dashboard.py:86`
- `neeron/backend/app/api/v1/biosecurity.py:92-105`

**Recommended fix**

- Return `null`, empty collections, or explicit `dataUnavailable` / `sourceMissing` markers.
- Keep demo defaults in frontend fixtures only, not backend production routes.
- Add response-level provenance so consumers know whether values are measured, inferred, or unavailable.

---

#### 5. Hot read paths contain multiple N+1 query patterns

**Why this matters**

Several farm and tank endpoints execute per-zone, per-tank, or per-sensor queries inside loops. This will scale poorly as telemetry volume and farm size grow.

**References**

- `neeron/backend/app/repositories/dashboard_repository.py:98-139`
- `neeron/backend/app/repositories/tank_repository.py:28-78`
- `neeron/backend/app/repositories/tank_repository.py:154-179`
- `neeron/backend/app/services/telemetry_service.py:30-36`
- `neeron/backend/app/services/telemetry_service.py:62-89`
- `neeron/backend/app/services/biosecurity_service.py:33-66`
- `neeron/backend/app/services/prediction_service.py:57-67`
- `neeron/backend/app/services/ai_insight_service.py:40-60`

**Recommended fix**

- Replace per-row lookups with batched aggregates, grouped subqueries, or window-function queries.
- Fetch latest-per-tank and latest-per-sensor rows in one statement.
- Precompute dashboard-grade aggregates where freshness requirements allow it.

---

#### 6. API routes bypass service boundaries and reach directly into repositories or service internals

**Why this matters**

The API layer is repeatedly doing repository work itself or using internal service attributes like `service.tank_repo` and `service.rec_repo`. That weakens encapsulation and makes policy enforcement inconsistent.

**References**

- `neeron/backend/app/api/v1/models.py:19-28`
- `neeron/backend/app/api/v1/models.py:57-72`
- `neeron/backend/app/api/v1/biosecurity.py:50-70`
- `neeron/backend/app/api/v1/tanks.py:50`
- `neeron/backend/app/api/v1/tanks.py:94-99`
- `neeron/backend/app/api/v1/tanks.py:123-128`
- `neeron/backend/app/api/v1/tanks.py:162-167`
- `neeron/backend/app/api/v1/tanks.py:194-199`
- `neeron/backend/app/api/v1/telemetry.py:79-83`
- `neeron/backend/app/api/v1/recommendations.py:29-35`
- `neeron/backend/app/api/v1/recommendations.py:62-68`
- `neeron/backend/app/api/v1/recommendations.py:98-104`
- `neeron/backend/app/api/v1/alerts.py:32-43`
- `neeron/backend/app/api/v1/alerts.py:54-60`
- `neeron/backend/app/api/v1/dashboard.py:36-37`
- `neeron/backend/app/api/v1/dashboard.py:105-107`
- `neeron/backend/app/api/v1/farms.py:83-86`

**Recommended fix**

- Make services the only API-facing application boundary.
- Add explicit service methods for existence checks, filtered lists, and snapshot DTO assembly.
- Keep routers focused on HTTP parsing, response mapping, and status codes.

---

### Medium

#### 7. Repository layer contains business defaults and presentation-shaped return values

**Why this matters**

Repositories should encapsulate data access, but several methods also decide fallback semantics, placeholder analytics, and API-shaped dictionaries. That makes behavior harder to test and reuse consistently.

**References**

- `neeron/backend/app/repositories/telemetry_repository.py:91-100`
- `neeron/backend/app/repositories/telemetry_repository.py:126-136`
- `neeron/backend/app/repositories/telemetry_repository.py:194-205`
- `neeron/backend/app/repositories/telemetry_repository.py:208-228`
- `neeron/backend/app/repositories/tank_repository.py:23-78`
- `neeron/backend/app/repositories/dashboard_repository.py:93-139`

**Recommended fix**

- Keep repositories returning entities or raw aggregate rows only.
- Move placeholder handling, defaults, and response shaping into services.
- Use dedicated DTOs for dashboard/reporting payloads.

---

#### 8. Duplicate business logic exists across services and routes

**Why this matters**

The same concepts are implemented in multiple places, which raises drift risk and makes behavior changes expensive.

**References**

- `neeron/backend/app/services/tank_service.py:79-119`
- `neeron/backend/app/services/prediction_service.py:24-38`
- `neeron/backend/app/services/telemetry_service.py:115-125`
- `neeron/backend/app/services/farm_service.py:76-103`
- `neeron/backend/app/services/farm_service.py:105-111`
- `neeron/backend/app/api/v1/dashboard.py:96-116`
- `neeron/backend/app/api/v1/farms.py:68-95`

**Examples**

- prediction aggregation exists in both `TankService` and `PredictionService`
- acoustic trend wrappers are duplicated in `TelemetryService`
- farm biomass logic is duplicated in `FarmService`
- farm health snapshot mapping is duplicated in both dashboard and farm routes

**Recommended fix**

- Consolidate prediction assembly into `PredictionService`.
- Keep one farm-health DTO builder.
- Extract repeated KPI calculations into dedicated domain helpers.

---

#### 9. Important relational paths are missing indexes or foreign keys

**Why this matters**

Some high-value references are not indexed, and one important event link is not protected by a database foreign key even though both key parts exist.

**References**

- Missing composite FK from notifications to alerts:
  - `neeron/backend/app/models/notification.py:81-93`
  - `neeron/backend/app/models/alert.py:61-70`
- Missing indexes on frequently joined/audited nullable FKs:
  - `neeron/backend/app/models/recommendation.py:88-95`
  - `neeron/backend/app/models/recommendation.py:128-142`
  - `neeron/backend/app/models/alert.py:120-124`
  - `neeron/backend/app/models/ai_insight.py:105-112`

**Recommended fix**

- Add a composite FK from `notifications(alert_id, alert_time)` to `alerts(id, time)` if TimescaleDB constraints allow it in the target deployment.
- Add indexes for:
  - `recommendations.generated_by_model`
  - `recommendations.resolved_by`
  - `alerts.resolved_by`
  - `ai_insights.source_model_id`
- Review query plans before and after to confirm benefit.

---

#### 10. Import coupling is high even though no hard circular dependency is currently present

**Why this matters**

`deps.py` imports umbrella packages that re-export nearly the whole model, repository, and service graph. This is not a live circular import today, but it increases startup cost and makes future cycles more likely.

**References**

- `neeron/backend/app/api/v1/deps.py:5-35`
- `neeron/backend/app/models/__init__.py:1-103`
- `neeron/backend/app/repositories/__init__.py:1-30`
- `neeron/backend/app/services/__init__.py:1-32`

**Recommended fix**

- Import concrete classes directly inside `deps.py` instead of package umbrellas.
- Keep package `__init__` files minimal.
- Prefer local imports in composition roots only where they reduce cycle pressure intentionally.

---

#### 11. API/schema mismatches are being hidden by mocked tests

**Why this matters**

Some routes return ORM objects directly even when the declared schema expects transformed fields that the ORM model does not expose.

**References**

- `neeron/backend/app/schemas/model.py:9-20`
- `neeron/backend/app/api/v1/models.py:19-28`
- `neeron/backend/app/api/v1/models.py:57-72`
- `neeron/backend/app/models/ai_model.py:89-94`
- `neeron/backend/app/api/v1/biosecurity.py:61-67`
- `neeron/backend/app/models/biosecurity_record.py:42-65`
- `neeron/backend/tests/conftest.py:72-93`
- `neeron/backend/tests/conftest.py:113-121`
- `neeron/backend/tests/api/test_models.py:15-25`

**Examples**

- `AiModelResponse` requires `owner: str`, but `AiModel` exposes `owner_id`, not `owner`.
- `list_pathogens()` maps `scientificName` from `p.name`, while the model fields are `scientific_name` and `common_name`.

**Recommended fix**

- Stop returning ORM objects directly when response shaping is required.
- Build explicit response DTOs in services or routers.
- Add integration tests with real SQLAlchemy models instead of only `MockORM`.

---

#### 12. The DB dependency graph uses generic repositories where domain repositories should exist

**Why this matters**

Several services are composed with `BaseRepository(...)` for domain entities like `ThresholdConfig`, `AiInsight`, `HistoricalCase`, and `QuarantineEvent`. That keeps business capabilities out of repositories and pushes domain rules up into services and routes.

**References**

- `neeron/backend/app/api/v1/deps.py:90-125`

**Recommended fix**

- Add typed repositories for domain-rich aggregates that already have non-trivial use cases.
- Reserve `BaseRepository` for truly generic CRUD-only resources.

---

### Low

#### 13. Pydantic v2 deprecation warnings indicate schema maintenance debt

**Why this matters**

The current schema layer still uses class-based `Config`, which is deprecated in Pydantic v2 and will be removed in v3.

**References**

- Warning output from `pytest neeron/backend/tests/api -q`

**Recommended fix**

- Migrate schema models from `class Config` to `model_config = ConfigDict(...)`.

---

## Cross-Cutting Recommendations

1. Introduce an explicit application boundary:
   - `router -> service -> repository`
   - no direct repository access from routers
   - no placeholder business behavior in repositories

2. Add a real unit-of-work pattern:
   - explicit transaction control in write services
   - no implicit commit in `get_db()`

3. Add security before adding features:
   - authenticated principal
   - farm/tank scoping checks
   - trustworthy actor IDs for alerts, recommendations, and settings changes

4. Rework the hottest read models:
   - batch latest-per-entity queries
   - precompute dashboard aggregates where acceptable
   - add missing indexes based on actual query plans

5. Strengthen test realism:
   - run Alembic upgrade tests against Postgres
   - add repository/service integration tests
   - add at least one end-to-end test path without `MockORM`

## Circular Dependency Conclusion

- **Current state:** no hard circular dependency was found in the present code.
- **Risk level:** elevated, because `app.api.v1.deps` imports umbrella `models`, `repositories`, and `services` packages that re-export large parts of the backend graph.
- **Action:** simplify composition imports now, before the next dependency-rich feature lands.
