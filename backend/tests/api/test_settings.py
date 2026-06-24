# tests/api/test_settings.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_sensor_status(client, mock_services):
    farm_id = uuid4()
    sensor_id = uuid4()
    tank_id = uuid4()

    mock_services["settings"].get_sensor_status.return_value = [
        {
            "sensor_id": sensor_id,
            "hardware_id": "SN-9824",
            "type": "Dissolved Oxygen",
            "status": "Active",
            "calibration_due_at": datetime.now(timezone.utc),
            "tank_id": tank_id,
        }
    ]

    response = await client.get(f"/api/v1/settings/sensors?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["hardware_id"] == "SN-9824"
    assert json_data["data"][0]["type"] == "Dissolved Oxygen"


async def test_get_threshold_configs(client, mock_services):
    farm_id = uuid4()
    config_id = uuid4()

    mock_services["settings"].get_thresholds.return_value = [
        MockORM(
            id=config_id,
            farm_id=farm_id,
            metric_name="dissolved_oxygen",
            warning_min=6.0,
            warning_max=10.0,
            critical_min=5.0,
            critical_max=12.0,
            updated_by=None,
            updated_at=datetime.now(timezone.utc),
        )
    ]

    response = await client.get(f"/api/v1/settings/thresholds?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["metric_name"] == "dissolved_oxygen"
    assert json_data["data"][0]["warning_min"] == 6.0


async def test_update_threshold_configs_success(client, mock_services):
    farm_id = uuid4()
    config_id = uuid4()

    mock_services["settings"].update_thresholds.return_value = MockORM(
        id=config_id,
        farm_id=farm_id,
        metric_name="dissolved_oxygen",
        warning_min=6.5,
        warning_max=10.0,
        critical_min=5.5,
        critical_max=12.0,
        updated_by=None,
        updated_at=datetime.now(timezone.utc),
    )

    payload = {
        "farmId": str(farm_id),
        "metricName": "dissolved_oxygen",
        "warningMin": 6.5,
        "warningMax": 10.0,
        "criticalMin": 5.5,
        "criticalMax": 12.0,
    }

    response = await client.put("/api/v1/settings/thresholds", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["warning_min"] == 6.5


async def test_update_threshold_configs_invalid_bounds(client, mock_services):
    farm_id = uuid4()

    # Raise ValueError to trigger the custom 422 exception mapping
    mock_services["settings"].update_thresholds.side_effect = ValueError(
        "critical_min must be less than warning_min"
    )

    payload = {
        "farmId": str(farm_id),
        "metricName": "dissolved_oxygen",
        "warningMin": 6.5,
        "warningMax": 10.0,
        "criticalMin": 7.0,  # Invalid: critical_min > warning_min
        "criticalMax": 12.0,
    }

    response = await client.put("/api/v1/settings/thresholds", json=payload)
    assert response.status_code == 422
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["error"]["code"] == "HTTP_EXCEPTION"
    assert "critical_min must be less than warning_min" in json_data["error"]["message"]
