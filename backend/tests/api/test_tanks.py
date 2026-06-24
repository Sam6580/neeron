# tests/api/test_tanks.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_list_tanks(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].list_tanks.return_value = [
        MockORM(
            id=tank_id,
            name="Cage-01",
            type="Cage",
            volume_m3=1000.0,
            max_biomass_kg=15000.0,
            species="Atlantic Salmon",
        )
    ]
    mock_services["tank"].tank_repo.count.return_value = 1
    mock_services["tank"].get_tank_health.return_value = {
        "stress_level": "Optimal",
        "psi_score": 1.1,
    }

    response = await client.get("/api/v1/tanks?page=1&limit=10")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["pagination"]["currentPage"] == 1
    assert json_data["pagination"]["totalCount"] == 1
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["name"] == "Cage-01"
    assert json_data["data"][0]["healthStatus"] == "Optimal"


async def test_get_tank_detail_success(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].tank_repo.get.return_value = MockORM(
        id=tank_id,
        name="Cage-01",
        type="Cage",
        volume_m3=1000.0,
        max_biomass_kg=15000.0,
        species="Atlantic Salmon",
        digital_twin_config={"alert_delay_seconds": 30},
        created_at=datetime.now(timezone.utc),
    )

    response = await client.get(f"/api/v1/tanks/{tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["name"] == "Cage-01"
    assert json_data["data"]["digitalTwinConfig"]["alert_delay_seconds"] == 30


async def test_get_tank_detail_not_found(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].tank_repo.get.return_value = None

    response = await client.get(f"/api/v1/tanks/{tank_id}")
    assert response.status_code == 404


async def test_get_tank_health(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].tank_repo.get.return_value = MockORM(id=tank_id)
    mock_services["tank"].get_tank_health.return_value = {
        "psi_score": 2.4,
        "stress_level": "Warning",
        "psi_generated_at": datetime.now(timezone.utc),
        "stability": {
            "temperature": "Stable",
            "dissolved_oxygen": "Fluctuating",
            "ph": "Stable",
        },
        "averages_7d": {
            "temperature": 14.5,
            "dissolved_oxygen": 7.8,
            "ph": 7.6,
        },
    }

    response = await client.get(f"/api/v1/tanks/{tank_id}/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["stress_level"] == "Warning"
    assert json_data["data"]["stability"]["dissolved_oxygen"] == "Fluctuating"
    assert json_data["data"]["averages_7d"]["temperature"] == 14.5


async def test_get_tank_environment(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].tank_repo.get.return_value = MockORM(id=tank_id)
    mock_services["tank"].get_tank_environment.return_value = MockORM(
        temperature=15.2,
        ph=7.8,
        dissolved_oxygen=8.1,
        salinity=32.0,
        ammonia=0.01,
        turbidity=2.5,
        captured_at=datetime.now(timezone.utc),
    )

    response = await client.get(f"/api/v1/tanks/{tank_id}/environment")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["temperature"] == 15.2
    assert json_data["data"]["ph"] == 7.8


async def test_get_tank_predictions(client, mock_services):
    tank_id = uuid4()
    mock_services["tank"].tank_repo.get.return_value = MockORM(id=tank_id)
    mock_services["tank"].get_tank_predictions.return_value = {
        "psi": {"score": 2.5},
        "disease": {"risk": "Low"},
        "mortality": {"rate": 0.01},
        "harvest": {"estimated_date": "2026-12-01"},
    }

    response = await client.get(f"/api/v1/tanks/{tank_id}/predictions")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["psi"]["score"] == 2.5
    assert json_data["data"]["disease"]["risk"] == "Low"
