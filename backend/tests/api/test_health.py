# tests/api/test_health.py

import pytest
from unittest.mock import AsyncMock

pytestmark = pytest.mark.asyncio


async def test_health_success(client, mock_services):
    """
    Test GET /api/v1/health when the database is online.
    """
    mock_db = mock_services["db"]
    mock_db.execute = AsyncMock()

    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["database"] == "online"
    assert "timestamp" in json_data["data"]
    assert "X-Request-ID" in response.headers


async def test_health_db_offline(client, mock_services):
    """
    Test GET /api/v1/health when the database is offline.
    """
    mock_db = mock_services["db"]
    mock_db.execute.side_effect = Exception("DB Connection Timeout")

    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "healthy"
    assert json_data["data"]["database"] == "offline"
