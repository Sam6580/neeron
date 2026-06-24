# NEERON — Backend Implementation Architecture
## FastAPI, Python 3.12, SQLAlchemy 2.x, TimescaleDB & Celery Specification

This document details the production-grade backend architecture for NEERON (Neural Ecosystem Environmental Response & Optimization Network). It guides backend, database, and ML engineering teams on building a scalable Python 3.12 service powered by FastAPI, SQLAlchemy 2.x, Redis, and Celery.

---

## Section 1: Project Structure

The NEERON backend codebase is organized as a modular FastAPI project.

```text
backend/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── app/
    ├── api/                 # FastAPI routers & endpoint mappings
    │   ├── auth.py
    │   ├── tanks.py
    │   └── ...
    ├── core/                # Global config, security, exceptions, and logger definitions
    │   ├── config.py
    │   ├── security.py
    │   ├── feature_flags.py # Feature flags for rolling out new modules
    │   └── exceptions.py
    ├── db/                  # Session manager, Base model, and Alembic env
    │   ├── session.py
    │   └── base.py
    ├── models/              # SQLAlchemy 2.x database models
    │   ├── user.py
    │   ├── telemetry.py
    │   └── ...
    ├── schemas/             # Pydantic v2 validation schemas
    │   ├── user.py
    │   ├── tank.py
    │   └── ...
    ├── repositories/        # Database CRUD encapsulation classes
    │   ├── base.py
    │   ├── tank.py
    │   └── ...
    ├── services/            # Business logic orchestration layers
    │   ├── dashboard.py
    │   ├── telemetry.py
    │   └── ...
    ├── events/              # Event definitions & in-memory/Redis PubSub event bus
    │   ├── bus.py
    │   └── handlers.py
    ├── ml/                  # Machine learning engines and weights
    │   ├── psi_engine/
    │   ├── disease_predictor/
    │   └── ...
    ├── websocket/           # WebSocket routers, connection managers, and loops
    │   ├── connection_manager.py
    │   └── endpoints.py
    ├── containers.py        # Dependency injection container
    ├── workers/             # Celery app, tasks, and periodic configurations
    │   ├── celery_app.py
    │   ├── tasks.py
    │   └── ...
    ├── middleware/          # Security headers, rate limiting, and CORS
    ├── utils/               # Time helpers, unit converters, and formatters
    ├── main.py              # Application entrypoint
    └── prestart.sh          # Database check & migration script
```

---

## Section 2: Application Layers & Dependency Injection

The backend uses a layered architecture to separate concerns. Each request flows downward through these layers:

```text
Client  ===>  [ API Layer ]  ===>  [ Service Layer ]  ===>  [ Repository Layer ]  ===>  Database
```

To keep components decoupled and simplify testing, we use a central dependency injection container (`dependency-injector`).

```python
# app/containers.py
from dependency_injector import containers, providers
from app.db.session import async_session_factory
from app.repositories.tank import TankRepository
from app.repositories.sensor import SensorRepository
from app.repositories.telemetry import TelemetryRepository
from app.services.telemetry import TelemetryService
from app.services.psi import PsiService

class AppContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["app.api.tanks", "app.api.telemetry"])

    # Database Session Providers
    db_session = providers.Resource(async_session_factory)

    # Repositories
    tank_repo = providers.Factory(TankRepository, session=db_session)
    sensor_repo = providers.Factory(SensorRepository, session=db_session)
    telemetry_repo = providers.Factory(TelemetryRepository, session=db_session)

    # Services
    psi_service = providers.Factory(PsiService, tank_repo=tank_repo)
    telemetry_service = providers.Factory(
        TelemetryService,
        telemetry_repo=telemetry_repo,
        sensor_repo=sensor_repo
    )
```

In routers, services are injected directly using FastAPI dependencies:
```python
# app/api/telemetry.py
from fastapi import APIRouter, Depends
from dependency_injector.wiring import inject, Provide
from app.containers import AppContainer
from app.services.telemetry import TelemetryService

router = APIRouter()

@router.post("/ingest")
@inject
async def ingest_telemetry(
    payload: dict,
    service: TelemetryService = Depends(Provide[AppContainer.telemetry_service])
):
    await service.process_raw_value(payload["hardware_id"], payload["timestamp"], payload["value"])
    return {"status": "success"}
```

---

## Section 3: Feature Flag Management

Feature flags let you enable or disable modules (like the digital twin or recommendation engines) dynamically based on client config or target deployment environments.

```python
# app/core/feature_flags.py
from pydantic_settings import BaseSettings

class FeatureFlags(BaseSettings):
    # Enable digital twin simulation models
    ENABLE_DIGITAL_TWIN: bool = True
    
    # Enable case-based reasoning recommendation matching
    ENABLE_CASE_MATCHING: bool = True
    
    # Enable automated retraining jobs on Celery Beat
    ENABLE_AUTOMATED_RETRAINING: bool = False
    
    # Enable closed-loop autonomous controller interactions
    ENABLE_AUTONOMOUS_CONTROL: bool = False

    class Config:
        env_prefix = "FEAT_" # Loaded from environment as FEAT_ENABLE_DIGITAL_TWIN=False

feature_flags = FeatureFlags()
```

---

## Section 4: Event Bus Architecture (Decoupling Ingest and Inference)

To decouple sensor ingestion from resource-heavy ML inference and recommendations, we implement an **Event Bus**.

```mermaid
graph TD
    A[Raw Ingestion API] -->|Publish Event| B[Event Bus]
    B -->|Subscribe| C[Data Quality Monitor]
    B -->|Subscribe| D[Alert Evaluation Engine]
    B -->|Subscribe| E[PSI Prediction Engine]
```

### 4.1 Event Definitions
```python
# app/events/bus.py
from typing import Callable, Dict, List
import asyncio
from pydantic import BaseModel

class TelemetryIngestedEvent(BaseModel):
    tank_id: str
    sensor_id: str
    metric: str
    value: float
    timestamp: str

class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, listener: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    async def publish(self, event_type: str, event_data: BaseModel):
        if event_type in self._listeners:
            # Dispatch event asynchronously to all registered listeners
            tasks = [asyncio.create_task(listener(event_data)) for listener in self._listeners[event_type]]
            await asyncio.gather(*tasks, return_exceptions=True)

event_bus = EventBus()
```

---

## Section 5: FastAPI Router Design

The API structure maps directly to the endpoints defined in the API contract:

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, tanks, telemetry, analytics, psi, biosecurity, settings as settings_api

app = FastAPI(title="NEERON API", version="2.0.0", openapi_url="/api/v1/openapi.json")

# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tanks.router, prefix="/api/v1/tanks", tags=["Tanks"])
app.include_router(telemetry.router, prefix="/api/v1/telemetry", tags=["Telemetry"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(psi.router, prefix="/api/v1/psi", tags=["Physiological Stress Index"])
app.include_router(biosecurity.router, prefix="/api/v1/biosecurity", tags=["Biosecurity"])
app.include_router(settings_api.router, prefix="/api/v1/settings", tags=["MLOps & Configurations"])
```

---

## Section 6: Pydantic Schema Design

We use Pydantic v2 schemas to validate payloads at the boundaries of the API layer.

```python
# app/schemas/tank.py
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class TankBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    type: str = Field(..., pattern="^(RAS Tank|Sea Cage|Nursery)$")
    volume_m3: float = Field(..., gt=0.0)
    max_biomass_kg: float = Field(..., gt=0.0)
    species: str = Field("Atlantic Salmon", max_length=100)

class TankCreate(TankBase):
    zone_id: UUID

class TankUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    volume_m3: Optional[float] = Field(None, gt=0.0)
    max_biomass_kg: Optional[float] = Field(None, gt=0.0)
    digital_twin_config: Optional[dict] = None

class TankResponse(TankBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    zone_id: UUID
    digital_twin_config: dict
    created_at: datetime
    updated_at: datetime
```

---

## Section 7: Database Layer (SQLAlchemy 2.x Async)

The database manager uses an async driver (`asyncpg`) to handle high-frequency writes to the database.

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_ASYNC_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_recycle=1800,
    pool_pre_ping=True
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def get_db_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## Section 8: Repository Layer

Repositories encapsulate database queries. All repositories extend a generic `BaseRepository` that handles basic CRUD operations.

```python
# app/repositories/tank.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional
from app.models.tank import Tank
from app.repositories.base import BaseRepository

class TankRepository(BaseRepository[Tank]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Tank, session=session)

    async def get_by_zone(self, zone_id: UUID) -> List[Tank]:
        stmt = select(self.model).where(self.model.zone_id == zone_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_alerts(self, tank_id: UUID) -> Optional[Tank]:
        stmt = select(self.model).where(self.model.id == tank_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
```

---

## Section 9: Service Layer

Services run business logic, coordinate multiple repositories, and check access control boundaries before committing changes.

```python
# app/services/telemetry.py
from uuid import UUID
from datetime import datetime
from app.repositories.telemetry import TelemetryRepository
from app.repositories.sensor import SensorRepository
from app.core.exceptions import EntityNotFoundException

class TelemetryService:
    def __init__(self, telemetry_repo: TelemetryRepository, sensor_repo: SensorRepository):
        self.telemetry_repo = telemetry_repo
        self.sensor_repo = sensor_repo

    async def process_raw_value(self, hardware_id: str, timestamp: datetime, value: float) -> None:
        sensor = await self.sensor_repo.get_by_hardware_id(hardware_id)
        if not sensor:
            raise EntityNotFoundException(f"Hardware sensor {hardware_id} not registered.")
            
        await self.telemetry_repo.create(
            time=timestamp,
            sensor_id=sensor.id,
            value=value
        )
```

---

## Section 10: Authentication & Security Middleware

The security system uses JWT access tokens and HTTP-only refresh cookies to manage user sessions.

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB
    Client->>API: POST /auth/login (credentials)
    API->>DB: Query User & Role
    DB-->>API: User Record
    API-->>Client: HTTP 200 (Access Token + Set-Cookie Refresh Token)
    Client->>API: Request with Header: Authorization: Bearer
    API-->>Client: Return Protected Resource
```

### 10.1 JWT Claims Schema
```json
{
  "sub": "e4e94326-6df7-4632-8dfb-b0b3d683dc75",
  "role": "Biologist",
  "farms": ["f101c842-9ef8-7dd9-60e2-0524d77da342"],
  "exp": 1782265661
}
```

### 10.2 Role-Based Access Control Dependency
```python
# app/core/security.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import decode_token

security = HTTPBearer()

class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, creds: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        payload = decode_token(creds.credentials)
        if not payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
            
        user_role = payload.get("role")
        if user_role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permissions missing for user role."
            )
        return payload
```

---

## Section 11: WebSocket Architecture

To support real-time dashboards, NEERON uses an asynchronous connection manager backed by **Redis Pub/Sub** to handle client connections.

```python
# app/websocket/connection_manager.py
from fastapi import WebSocket
from typing import Dict, List, Set
from uuid import UUID
import json
import asyncio
import aioredis

class WebSocketConnectionManager:
    def __init__(self):
        self.active_subscriptions: Dict[UUID, Set[WebSocket]] = {}
        self.redis_client = aioredis.from_url("redis://redis:6379/1")

    async def connect(self, websocket: WebSocket, tank_id: UUID):
        await websocket.accept()
        if tank_id not in self.active_subscriptions:
            self.active_subscriptions[tank_id] = set()
            asyncio.create_task(self._listen_redis_channel(tank_id))
            
        self.active_subscriptions[tank_id].add(websocket)

    def disconnect(self, websocket: WebSocket, tank_id: UUID):
        if tank_id in self.active_subscriptions:
            self.active_subscriptions[tank_id].discard(websocket)
            if not self.active_subscriptions[tank_id]:
                del self.active_subscriptions[tank_id]

    async def _listen_redis_channel(self, tank_id: UUID):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(f"channel:tanks:{tank_id}")
        try:
            while tank_id in self.active_subscriptions:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    payload = json.loads(message['data'])
                    futures = [ws.send_json(payload) for ws in self.active_subscriptions[tank_id]]
                    await asyncio.gather(*futures, return_exceptions=True)
                await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe(f"channel:tanks:{tank_id}")
```

---

## Section 12: ML Integration Layer

The ML integration layer loads model weights (XGBoost/LSTM) from disk during application startup, preventing performance bottlenecks during inference.

```python
# app/ml/psi_engine/predictor.py
import joblib
import numpy as np
from uuid import UUID
from typing import Dict, Tuple

class PSIPredictor:
    def __init__(self, model_path: str):
        self.model = joblib.load(model_path)

    def predict_stress(self, features: Dict[str, float]) -> Tuple[float, str]:
        """
        Inputs: {"temperature": 11.2, "ph": 7.2, "dissolved_oxygen": 8.4, "salinity": 32.0}
        Outputs: (Stress Score 0-10, Stress Level Classification)
        """
        data_vector = np.array([[
            features.get("temperature", 10.0),
            features.get("ph", 7.0),
            features.get("dissolved_oxygen", 8.0),
            features.get("salinity", 32.0)
        ]])
        
        psi_score = float(self.model.predict(data_vector)[0])
        psi_score = max(0.0, min(10.0, psi_score))
        
        if psi_score < 2.0:
            level = "Optimal"
        elif psi_score < 4.0:
            level = "Mild Stress"
        elif psi_score < 6.0:
            level = "Moderate Stress"
        elif psi_score < 8.0:
            level = "Severe Stress"
        else:
            level = "Critical Stress"
            
        return psi_score, level
```

---

## Section 13: Background Workers (Celery & Dramatiq)

Background tasks (such as telemetry aggregation, forecasting, and retraining) are processed out-of-band using Celery.

> [!NOTE]
> **Dramatiq Alternative:** For teams seeking simpler configuration, cleaner type hints, and lower resource footprints than Celery, **Dramatiq** is supported. Both use Redis as a broker and store task state keys.

```python
# app/workers/celery_app.py
from celery import Celery
from celery.schedules import crontab

celery_app = Celery(
    "neeron_workers",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)

celery_app.conf.task_routes = {
    "app.workers.tasks.process_telemetry_packet": {"queue": "telemetry-ingest"},
    "app.workers.tasks.generate_stress_predictions": {"queue": "predictions-engine"},
    "app.workers.tasks.run_model_retraining": {"queue": "mlops-compute"},
}

celery_app.conf.beat_schedule = {
    "evaluate-nightly-model-health": {
        "task": "app.workers.tasks.evaluate_model_health",
        "schedule": crontab(hour="2", minute="0"),
    }
}
```

---

## Section 14: Redis Architecture

Redis serves as the caching layer, rate limiter, and message broker for the backend.

### 14.1 Key Storage Policies

| Purpose | DB Index | Expiry Policy | Pattern Examples |
| :--- | :--- | :--- | :--- |
| **Broker (Celery)** | `0` | Managed by Celery | `celery-task-meta-*` |
| **WS Pub/Sub** | `1` | Immediate Volatile | `channel:tanks:<uuid>` |
| **Cache (Dashboard)** | `2` | 5 Minutes (Absolute) | `cache:dashboard:<farm_id>` |
| **Cache (Tanks)** | `2` | 30 Minutes (Write-through) | `cache:tanks:detail:<tank_id>` |
| **Rate Limiter** | `3` | 1 Minute (Sliding) | `rate:ip:<ip_addr>` |

### 14.2 Cache Invalidation Policy
*   **Write-Through Caching**: Updates to the `tanks` or `threshold_configs` tables trigger a cache invalidation for related query keys (`DEL cache:tanks:detail:<tank_id>`).
*   **Volatile Invalidation**: High-frequency telemetry dashboard endpoints expire after 10 seconds, forcing clients to load fresh aggregations.

---

## Section 15: Digital Twin Architecture

The digital twin engine simulates tank variables to model future growth and test "what-if" scenarios.

```mermaid
graph TD
    A[Fetch Current State] --> B[Apply Temperature & DO Simulators]
    B --> C[Compute Biological S-Curve Growth]
    C --> D[Predict Mortality & Stress Factors]
    D --> E[Write Snapshots to Database]
```

### 15.1 Execution Steps
1.  **Retrieve State**: Pulls the latest entry from `tank_production_metrics` and `tank_environment_snapshots`.
2.  **Environment Simulator**: Models changes in dissolved oxygen and salinity based on simulated weather inputs (e.g. heatwave, storm anomalies).
3.  **Growth Simulator**: Uses a logistic S-growth model to project fish weight:
    $$W_{t+1} = W_t + \left(k \cdot W_t \cdot \left(1 - \frac{W_t}{W_{\text{max}}}\right)\right)$$
4.  **Risk Simulator**: Evaluates stress index (PSI) thresholds under the simulated scenario.
5.  **Output Logs**: Writes the projected run to the `digital_twin_snapshots` hypertable.

---

## Section 16: Error Handling & Exceptions

We use a global exception handler in FastAPI to format error responses consistently.

```python
# app/core/exceptions.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from datetime import datetime

class NeeronException(Exception):
    def __init__(self, code: str, message: str, details: dict = None):
        self.code = code
        self.message = message
        self.details = details or {}

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(NeeronException)
    async def neeron_exception_handler(request: Request, exc: NeeronException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            }
        )
```

---

## Section 17: Observability & Health Checks

We collect runtime logs, metrics, and health statuses to monitor the health of the application.

*   **Structured Logging**: App records structured JSON logs to standard output using `structlog`:
    ```json
    {"timestamp": "2026-06-24T04:49:00Z", "level": "info", "event": "sensor_ingest_received", "sensor_id": "TNK-01-TEMP", "value": 11.2}
    ```
*   **Health Endpoints**:
    *   `/health`: Quick check that returns HTTP 200 to confirm the application is running.
    *   `/live`: Confirms the container is active.
    *   `/ready`: Verifies active connections to PostgreSQL, TimescaleDB, and Redis.
*   **Metrics**: Exports system metrics (requests, latency, active database connections) to Prometheus via `/metrics`.

---

## Section 18: Security Hardening

*   **Input Validation**: Strict typing enforced by Pydantic models. String variables are sanitized using regex schemas to prevent cross-site scripting (XSS).
*   **SQL Injection Protection**: We use SQLAlchemy's parameter binding default to protect queries against SQL injection attacks.
*   **Secrets Management**: Production credentials and API keys are injected at runtime using Docker environment variables. No secrets are stored in version control.
*   **Rate Limiter Middleware**: Limits public auth routes to 5 requests per minute, and standard telemetry routes to 120 requests per minute using Redis token bucket limits.

---

## Section 19: Testing Strategy

To verify the API, business logic, and ML systems, we implement a automated testing framework using `pytest` and `pytest-asyncio`.

### 19.1 Testing Folder Structure
```text
tests/
├── conftest.py          # Pytest async db session fixtures and overrides
├── unit/                # Service layer isolation tests (using mock repositories)
│   ├── test_psi_service.py
│   └── test_telemetry.py
├── integration/         # Database and TimescaleDB hypertable read/write tests
│   ├── test_repository_writes.py
│   └── test_continuous_aggregates.py
├── api/                 # Endpoints test suite using HTTPX AsyncClient
│   ├── test_auth.py
│   └── test_tanks_endpoints.py
└── ml/                  # ML inference reliability and drift target tests
    ├── test_psi_model.py
    └── test_growth_simulator.py
```

### 19.2 Endpoint Test Example using HTTPX
```python
# tests/api/test_tanks_endpoints.py
import pytest
from httpx import AsyncClient
from uuid import uuid4

@pytest.mark.asyncio
async def test_retrieve_tank_details(client: AsyncClient, token_headers: dict):
    # Query details for non-existent tank to verify 404 handler
    tank_id = str(uuid4())
    response = await client.get(f"/api/v1/tanks/{tank_id}", headers=token_headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
```

---

## Section 20: Deployment Architecture

The system is containerized using Docker, with services split into separate task nodes.

```yaml
# docker-compose.yml
version: '3.8'

services:
  web-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    ports:
      - "8000:8000"
    environment:
      - DATABASE_ASYNC_URL=postgresql+asyncpg://neeron_user:pwd@timescaledb:5432/neeron
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - timescaledb
      - redis

  celery-worker:
    build:
      context: ./backend
    command: celery -A app.workers.celery_app worker --loglevel=info -Q telemetry-ingest,predictions-engine
    depends_on:
      - redis
      - timescaledb

  timescaledb:
    image: timescale/timescaledb:latest-pg14
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=neeron_user
      - POSTGRES_PASSWORD=pwd
      - POSTGRES_DB=neeron
    volumes:
      - ts_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  ts_data:
```

---

## Section 21: Scalability Strategy

As NEERON scales to manage 1,000+ farms, we scale services horizontally across the stack:

*   **API Node Scaling**: Stateless FastAPI nodes run behind an Nginx load balancer to distribute REST and WebSocket traffic.
*   **WebSocket Scaling**: Client WebSocket subscriptions are managed using a Redis Pub/Sub cluster.
*   **Database Scaling (TimescaleDB)**:
    *   **Distributed Hypertables**: Scales telemetry writes by partitioning data chunks across a cluster of database nodes.
    *   **Read Replicas**: Directs read-heavy dashboard and analytics queries to read replicas, leaving the primary node dedicated to raw telemetry writes.

---

## Section 22: Implementation Roadmap

The backend implementation is divided into nine sequential phases:

```text
Phase 1 (Base) ──> Phase 2 (DB) ──> Phase 3 (Auth) ──> Phase 4 (Telemetry) ──> Phase 5 (Analytics)
                                                                                     │
Phase 9 (Harden) <── Phase 8 (Sockets) <── Phase 7 (Rules) <── Phase 6 (ML Models) <─┘
```

### Phase 1: Backend Foundation
*   **Goals**: Set up project boilerplate, configure Python 3.12 settings, and configure Docker configurations.
*   **Deliverables**: `requirements.txt`, Dockerfiles, logging system, and basic mock routers.
*   **Dependencies**: None.

### Phase 2: Database Integration
*   **Goals**: Configure SQLAlchemy, initialize Alembic migrations, and verify connection pools.
*   **Deliverables**: Base models, migration environment, and TimescaleDB extension setup scripts.
*   **Dependencies**: Phase 1.

### Phase 3: Authentication
*   **Goals**: Build security helper functions, user authentication, and RBAC security middleware.
*   **Deliverables**: `/auth/login`, `/auth/me` endpoints, and authorization headers check.
*   **Dependencies**: Phase 2.

### Phase 4: Telemetry APIs
*   **Goals**: Implement telemetry routes and set up background data processor queues.
*   **Deliverables**: `tank_environment_snapshots` populator and raw telemetry write triggers.
*   **Dependencies**: Phase 3.

### Phase 5: Analytics
*   **Goals**: Compile biomass historical views and harvest forecasting outputs.
*   **Deliverables**: TimescaleDB Continuous Aggregates and daily report metrics generation.
*   **Dependencies**: Phase 4.

### Phase 6: ML Integration
*   **Goals**: Integrate prediction loops (PSI, disease, mortality, harvest predictions).
*   **Deliverables**: ML modules code, model-loading strategies, and SHAP factor attribution logging.
*   **Dependencies**: Phase 5.

### Phase 7: Recommendation Engine
*   **Goals**: Deploy the hybrid recommendation engine combining rule checks with case-based reasoning.
*   **Deliverables**: Rule check processor and recommendation feedback loop tracking.
*   **Dependencies**: Phase 6.

### Phase 8: WebSockets
*   **Goals**: Deploy real-time WebSocket communication channels using Redis Pub/Sub.
*   **Deliverables**: Asynchronous subscription controller, connection managers, and broadcast routes.
*   **Dependencies**: Phase 7.

### Phase 9: Production Hardening
*   **Goals**: Add security headers, rate limiting, and observability instrumentation.
*   **Deliverables**: `/health` checks, structlog integration, and Nginx reverse proxy configs.
*   **Dependencies**: Phase 8.
