# NEERON Backend Development Handbook

Welcome to the NEERON Precision Aquaculture Intelligence Platform backend. This handbook serves as a guide for developers and AI agents working on the codebase. It explains what has been built, the design patterns used, and how to verify changes without introducing regressions.

---

## 1. Architecture Overview

The backend uses a strict **layered architecture** to separate concerns and ensure testability:

```
┌─────────────────────────────────────────────────────────┐
│                    FastAPI Routers                      │
│                  (app/api/v1/*.py)                      │
└──────────────────────────┬──────────────────────────────┘
                           │ (Dependency Injection via deps.py)
┌──────────────────────────▼──────────────────────────────┐
│                    Service Layer                        │
│                   (app/services/*.py)                   │
└──────────────────────────┬──────────────────────────────┘
                           │ (Injected via constructor)
┌──────────────────────────▼──────────────────────────────┐
│                  Repository Layer                       │
│                 (app/repositories/*.py)                 │
└──────────────────────────┬──────────────────────────────┘
                           │ (Async SQLAlchemy)
┌──────────────────────────▼──────────────────────────────┐
│                   Database Layer                        │
│             (app/db/ & app/models/)                     │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Layer Specifications

### Database & Migrations (`app/models/` & `alembic/`)
- **SQLAlchemy 2.0**: Uses modern declarative syntax with typed `Mapped` attributes.
- **Alembic Infrastructure**: Configured for async migration cycles (`alembic/env.py`).
- **PostgreSQL / TimescaleDB partitioning**: Time-series tables utilize composite primary keys (typically `(id, time)` or `(id, recorded_at)`) and are partitioned as hypertables via custom SQL blocks in Alembic revisions.

### Repository Layer (`app/repositories/`)
- All database access is encapsulated inside repositories.
- **`BaseRepository[T]`**: Inherits common CRUD operations, soft-deletion handling (`deleted_at`), pagination, and exist checks.
- **Custom Repositories**: Implement advanced aggregated analytical queries. For example, `TankRepository.get_tank_dashboard()` calculates biomass averages and fetches active alerts; `TelemetryRepository.get_water_quality_metrics()` formats environmental parameter summaries.

### Service Layer (`app/services/`)
- Holds all business logic, validations, and coordinates actions.
- **Inherits `BaseService`**: Enables logging and tracing capabilities.
- **Service Dependency Isolation**: Under no circumstances should services contain SQLAlchemy operations. They must rely solely on injected repositories.

### API Layer (`app/api/v1/`)
- **FastAPI APIRouter**: Endpoints are organized by operational domain under `app/api/v1/`.
- **Dependency Injection (`deps.py`)**: Resolves service layer instantiations and handles database session contexts.
- **Correlation ID Middleware**: Generates and responds with `X-Request-ID` headers to trace operations across systems.
- **Unified Error Handling**: Intercepts Pydantic validation exceptions (returns standard validation JSON responses with `VALIDATION_FAILED`), ValueErrors (returns 400 Bad Request), and HTTP Exceptions.

---

## 3. Integration Testing & Verification (`tests/`)

We have implemented a mock-driven integration test suite under `tests/api/` validating all 36 registered endpoints.

### Core Testing Rule
**No database container or live database connection is required to run the test suite.** We override dependencies using FastAPI's `dependency_overrides` mapping.

- **`tests/conftest.py`**:
  - Sets up `client` using HTTPX `AsyncClient` and `ASGITransport` to run tests inside FastAPI's lifespan context.
  - Defines `mock_services` to mock out all 12 services as `AsyncMock` objects.
  - Automatically mocks `BaseRepository.get` and `BaseRepository.get_multi` methods using `mock_base_repo_methods` to simplify database fetches.
  - Uses `MockORM` to represent entities conforming to Pydantic's `from_attributes = True` loader.

### How to Run Tests
To run the full suite and view the coverage report:
```bash
# In backend/ directory
python -m pytest tests/api/ --cov=app/api/v1/ --cov-report=term-missing
```

### Coverage Status
The suite achieves **94% total coverage** across all API routes, asserting status codes, pagination headers, and validation bounds.

---

## 4. Development Workflow Checklist

When adding a new feature or endpoint:
1. **Schema**: Define the payload validation models under `app/schemas/`.
2. **Model**: Declare database fields in `app/models/` if database persistence is needed. Run `alembic revision --autogenerate` to compile migration scripts.
3. **Repository**: Implement query logic inside a repository under `app/repositories/`.
4. **Service**: Implement business logic inside a service under `app/services/`.
5. **Controller**: Expose endpoint under `app/api/v1/` and resolve service injection in `deps.py`.
6. **Tests**: Create a matching integration test case under `tests/api/test_*.py` and verify it passes.
