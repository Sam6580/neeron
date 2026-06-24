# tests/api/test_predictions.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_disease_predictions_success(client, mock_services):
    tank_id = uuid4()
    pathogen_id = uuid4()
    mock_services["prediction"].get_latest_predictions.return_value = {
        "disease": MockORM(
            tank_id=tank_id,
            pathogen_id=pathogen_id,
            pathogen="Vibrio anguillarum",
            probability=0.75,
            time=datetime.now(timezone.utc),
        )
    }

    response = await client.get(f"/api/v1/predictions/disease?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["scientificName"] == "Vibrio anguillarum"
    assert json_data["data"][0]["probability"] == 0.75
    # Asserts confidence mapping limits logic
    assert json_data["data"][0]["confidenceLow"] == 0.75 * 0.9
    assert json_data["data"][0]["confidenceHigh"] == 0.75 * 1.1


async def test_get_disease_predictions_empty(client, mock_services):
    tank_id = uuid4()
    mock_services["prediction"].get_latest_predictions.return_value = {}

    response = await client.get(f"/api/v1/predictions/disease?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"] == []


async def test_get_mortality_predictions_success(client, mock_services):
    tank_id = uuid4()
    mock_services["prediction"].get_latest_predictions.return_value = {
        "mortality": MockORM(
            tank_id=tank_id,
            mortality_rate=0.045,
            predicted_loss_kg=550.0,
            confidence=0.88,
            time=datetime.now(timezone.utc),
        )
    }

    response = await client.get(f"/api/v1/predictions/mortality?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["mortality_rate"] == 0.045
    assert json_data["data"]["predicted_loss_kg"] == 550.0


async def test_get_mortality_predictions_empty(client, mock_services):
    tank_id = uuid4()
    mock_services["prediction"].get_latest_predictions.return_value = {}

    response = await client.get(f"/api/v1/predictions/mortality?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["mortality_rate"] == 0.0
    assert json_data["data"]["predicted_loss_kg"] == 0.0


async def test_get_harvest_predictions_success(client, mock_services):
    tank_id = uuid4()
    harvest_date = datetime.now(timezone.utc)
    mock_services["prediction"].get_latest_predictions.return_value = {
        "harvest": MockORM(
            tank_id=tank_id,
            projected_harvest_date=harvest_date,
            projected_biomass=12000.0,
            avg_weight_g=450.0,
            fcr=1.25,
            revenue_projection_usd=85000.0,
            confidence=0.9,
            time=datetime.now(timezone.utc),
        )
    }

    response = await client.get(f"/api/v1/predictions/harvest?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["projectedBiomassKg"] == 12000.0
    assert json_data["data"]["revenueProjectionUsd"] == 85000.0


async def test_get_harvest_predictions_empty(client, mock_services):
    tank_id = uuid4()
    mock_services["prediction"].get_latest_predictions.return_value = {}

    response = await client.get(f"/api/v1/predictions/harvest?tank_id={tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"] == {}
