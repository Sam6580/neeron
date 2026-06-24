# NEERON Backend Architecture & Agent Rules

You are working on the NEERON Precision Aquaculture Intelligence Platform backend. To ensure consistency and avoid breaking the existing implementation, you MUST adhere to the following rules:

## 1. Architectural Layers & Separation of Concerns
- **Database Layer**: Models are defined in `app/models/` and database sessions are provided by `app/db/session.py`.
- **Repository Layer (`app/repositories/`)**:
  - Encapsulates all SQL / SQLAlchemy query logic.
  - All database queries, filters, soft deletes, and count operations must live in repository classes.
  - Inherit from `BaseRepository[T]` for standard CRUD operations.
- **Service Layer (`app/services/`)**:
  - Handles business logic, validations, and coordination.
  - Services must interact **exclusively** with Repositories.
  - **CRITICAL**: No raw SQL or SQLAlchemy sessions/queries (`select`, `execute`, etc.) are allowed inside the Service Layer.
  - All services must inherit from `BaseService`.
- **FastAPI API Layer (`app/api/v1/`)**:
  - Exposes REST endpoints grouped by routers.
  - Controllers must interact **exclusively** with Services via FastAPI Dependency Injection (`app/api/v1/deps.py`).
  - **CRITICAL**: Do not import or execute database sessions or query logic directly in controllers (except for direct entity catalogs like `Pathogen` or `AiModel` via `BaseRepository`).

## 2. API Schema and Response Standards
- All endpoint responses must conform to the standard wrappers defined in `app/schemas/base.py`:
  - Single Object: `BaseResponse[T]`
  - Paginated List: `PaginatedResponse[T]`
- Request-ID Correlation is handled automatically by `CorrelationIDMiddleware` in `app/main.py`. Preserve this middleware at all times.

## 3. TimescaleDB Time-Series Partitioning
- Time-series and telemetry tables use **composite primary keys** consisting of a UUID and a timestamp (e.g., `(id, time)` or `(id, recorded_at)`).
- When querying time-series records by ID, use filters or helper methods (such as `get_multi(filters={"id": id})`) to correctly scan time partitioned segments without constraint failures.

## 4. Testing & Integration Test Suite (`tests/`)
- All integration tests are located in `tests/api/`.
- **No Active DB Dependencies**: Tests must NOT require a live database container. Use the pytest fixtures in `tests/conftest.py` to:
  - Mock service dependencies using `AsyncMock` and register them via `app.dependency_overrides`.
  - Override `BaseRepository` methods using `mock_base_repo_methods` for inline repository lookups.
  - Use `MockORM` helper class to mimic SQLAlchemy models for Pydantic's `from_attributes = True` validation.
- Run tests using: `pytest tests/api/ --cov=app/api/v1/ --cov-report=term-missing`
