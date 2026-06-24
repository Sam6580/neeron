# tests/api/test_farms.py

import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_list_farms(client, mock_services):
    farm_id = uuid4()
    mock_services["farm"].list_farms.return_value = [
        MockORM(
            id=farm_id,
            name="North Farm",
            latitude=-41.12,
            longitude=174.78,
            timezone="Pacific/Auckland",
            carrying_capacity_kg=50000.0,
        )
    ]

    response = await client.get("/api/v1/farms")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["name"] == "North Farm"
    assert json_data["data"][0]["carryingCapacityKg"] == 50000.0


async def test_get_farm_detail_success(client, mock_services):
    farm_id = uuid4()
    mock_services["farm"].get_farm.return_value = MockORM(
        id=farm_id,
        name="South Farm",
        latitude=-45.2,
        longitude=170.5,
        timezone="Pacific/Auckland",
        carrying_capacity_kg=120000.0,
    )

    response = await client.get(f"/api/v1/farms/{farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["name"] == "South Farm"


async def test_get_farm_detail_not_found(client, mock_services):
    farm_id = uuid4()
    mock_services["farm"].get_farm.return_value = None

    response = await client.get(f"/api/v1/farms/{farm_id}")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "not found" in json_data["error"]["message"]


async def test_get_farm_health_success(client, mock_services):
    farm_id = uuid4()
    mock_services["farm"].get_farm.return_value = MockORM(
        id=farm_id,
        name="South Farm",
    )
    mock_services["farm"].get_farm_health.return_value = 85.0
    mock_services["farm"].dashboard_repo.get_farm_health_snapshot.return_value = MockORM(
        risk_score=10.0, psi_average=0.5
    )

    response = await client.get(f"/api/v1/farms/{farm_id}/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["health_score"] == 85.0


async def test_get_farm_health_not_found(client, mock_services):
    farm_id = uuid4()
    mock_services["farm"].get_farm.return_value = None

    response = await client.get(f"/api/v1/farms/{farm_id}/health")
    assert response.status_code == 404
