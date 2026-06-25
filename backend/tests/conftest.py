# tests/conftest.py

import asyncio
from datetime import datetime, timezone
import pytest
from unittest import mock
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
import uuid as uuid_module

from fastapi import FastAPI
from httpx import AsyncClient

from app.main import app
from app.api.v1.deps import (
    get_dashboard_service,
    get_farm_service,
    get_tank_service,
    get_telemetry_service,
    get_prediction_service,
    get_recommendation_service,
    get_recommendation_engine_service,
    get_biosecurity_service,
    get_settings_service,
    get_ai_insight_service,
    get_user_service,
    get_alert_service,
    get_auth_service,
    get_db,
)
from app.api.v1.dependencies.auth import get_current_user, get_current_active_user


class MockORM:
    """
    A helper object to mock ORM models easily.
    Since response schemas configure `from_attributes = True`,
    Pydantic reads fields via getattr(obj, field).
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def mock_services():
    """
    Set up AsyncMock objects for all services and override them in FastAPI dependencies.
    """
    mocks = {
        "dashboard": AsyncMock(),
        "farm": AsyncMock(),
        "tank": AsyncMock(),
        "telemetry": AsyncMock(),
        "prediction": AsyncMock(),
        "recommendation": AsyncMock(),
        "recommendation_engine": AsyncMock(),
        "biosecurity": AsyncMock(),
        "settings": AsyncMock(),
        "ai_insight": AsyncMock(),
        "user": AsyncMock(),
        "alert": AsyncMock(),
        "auth": AsyncMock(),
        "db": AsyncMock(),
    }

    # Configure sub-repositories/attributes used directly in routers
    mocks["farm"].dashboard_repo = AsyncMock()
    mocks["dashboard"].dashboard_repo = AsyncMock()
    mocks["tank"].tank_repo = AsyncMock()
    mocks["telemetry"].sensor_repo = AsyncMock()
    mocks["recommendation"].rec_repo = AsyncMock()
    mocks["alert"].alert_repo = AsyncMock()

    # Override service dependencies
    app.dependency_overrides[get_dashboard_service] = lambda: mocks["dashboard"]
    app.dependency_overrides[get_farm_service] = lambda: mocks["farm"]
    app.dependency_overrides[get_tank_service] = lambda: mocks["tank"]
    app.dependency_overrides[get_telemetry_service] = lambda: mocks["telemetry"]
    app.dependency_overrides[get_prediction_service] = lambda: mocks["prediction"]
    app.dependency_overrides[get_recommendation_service] = lambda: mocks["recommendation"]
    app.dependency_overrides[get_recommendation_engine_service] = lambda: mocks["recommendation_engine"]
    app.dependency_overrides[get_biosecurity_service] = lambda: mocks["biosecurity"]
    app.dependency_overrides[get_settings_service] = lambda: mocks["settings"]
    app.dependency_overrides[get_ai_insight_service] = lambda: mocks["ai_insight"]
    app.dependency_overrides[get_user_service] = lambda: mocks["user"]
    app.dependency_overrides[get_alert_service] = lambda: mocks["alert"]
    app.dependency_overrides[get_auth_service] = lambda: mocks["auth"]
    app.dependency_overrides[get_db] = lambda: mocks["db"]

    # Authenticated routes are protected by get_current_active_user (which itself
    # depends on get_current_user). Override both so data-route tests are not
    # rejected with 401. Individual auth/RBAC tests override these as needed.
    auth_user = MockORM(
        id=uuid_module.uuid4(),
        email="tester@neeron.io",
        first_name="Test",
        last_name="User",
        is_active=True,
        role=MockORM(name="Administrator", permissions={}),
    )
    app.dependency_overrides[get_current_user] = lambda: auth_user
    app.dependency_overrides[get_current_active_user] = lambda: auth_user

    yield mocks

    app.dependency_overrides.clear()


import pytest_asyncio
from httpx import ASGITransport


@pytest_asyncio.fixture(scope="function")
async def client(mock_services):
    """
    HTTPX AsyncClient executing requests against overridden FastAPI app with lifespan triggers.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(scope="function", autouse=True)
def mock_base_repo_methods():
    """
    Automatically mock BaseRepository methods globally.
    This intercepts direct DB model fetches in routers like models.py and biosecurity.py.
    """
    with mock.patch("app.repositories.base.BaseRepository.get") as mock_get, \
         mock.patch("app.repositories.base.BaseRepository.get_multi") as mock_get_multi:
        yield mock_get, mock_get_multi
