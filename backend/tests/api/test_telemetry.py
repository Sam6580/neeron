# tests/api/test_telemetry.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_latest_telemetry_with_data(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].get_tank_environment.return_value = MockORM(
        temperature=14.8,
        ph=7.5,
        dissolved_oxygen=8.2,
        salinity=32.1,
        ammonia=0.015,
        turbidity=3.2,
        captured_at=datetime.now(timezone.utc),
    )

    response = await client.get(f"/api/v1/telemetry/latest?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["tankId"] == str(tank_id)
    assert json_data["data"]["metrics"]["temperature"] == 14.8
    assert json_data["data"]["metrics"]["ph"] == 7.5


async def test_get_latest_telemetry_fallback(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].get_tank_environment.return_value = None

    response = await client.get(f"/api/v1/telemetry/latest?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    # Asserts the fallback values are populated
    assert json_data["data"]["metrics"]["temperature"] == 12.0
    assert json_data["data"]["metrics"]["ph"] == 7.3


async def test_get_telemetry_history(client, mock_services):
    tank_id = uuid4()
    sensor_id = uuid4()
    start = "2026-06-24T00:00:00Z"
    end = "2026-06-24T23:59:59Z"

    mock_services["telemetry"].sensor_repo.get_active_sensors.return_value = [
        MockORM(id=sensor_id)
    ]
    mock_services["telemetry"].get_time_series.return_value = [
        MockORM(time=datetime.now(timezone.utc), value=15.1)
    ]

    response = await client.get(
        f"/api/v1/telemetry/history?tank_id={tank_id}&start_time={start}&end_time={end}"
    )
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]["history"]) == 1
    assert json_data["data"]["history"][0]["value"] == 15.1
    assert json_data["data"]["history"][0]["sensor_id"] == str(sensor_id)
