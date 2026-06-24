# tests/api/test_models.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_list_models(client, mock_base_repo_methods):
    mock_get, mock_get_multi = mock_base_repo_methods
    model_id = uuid4()

    mock_get_multi.return_value = [
        MockORM(
            id=model_id,
            name="Water Quality Predictor",
            algorithm="LSTM",
            status="Production",
            owner="DataScience Team",
            description="Predicts dissolved oxygen and water parameters",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    ]

    response = await client.get("/api/v1/models")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["name"] == "Water Quality Predictor"
    assert json_data["data"][0]["algorithm"] == "LSTM"


async def test_get_model_detail_success(client, mock_base_repo_methods):
    mock_get, mock_get_multi = mock_base_repo_methods
    model_id = uuid4()

    mock_get.return_value = MockORM(
        id=model_id,
        name="Disease Risk Classifier",
        algorithm="XGBoost",
        status="Production",
        owner="Biosecurity Team",
        description="Classifies disease risks based on telemetry",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = await client.get(f"/api/v1/models/{model_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["name"] == "Disease Risk Classifier"


async def test_get_model_detail_not_found(client, mock_base_repo_methods):
    mock_get, mock_get_multi = mock_base_repo_methods
    model_id = uuid4()
    mock_get.return_value = None

    response = await client.get(f"/api/v1/models/{model_id}")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "not found" in json_data["error"]["message"]


async def test_get_models_health(client, mock_services):
    metric_id = uuid4()
    version_id = uuid4()

    mock_services["settings"].get_model_health.return_value = [
        {
            "id": metric_id,
            "recorded_at": datetime.now(timezone.utc),
            "model_version_id": version_id,
            "accuracy": 0.92,
            "precision": 0.91,
            "recall": 0.93,
            "f1_score": 0.92,
            "data_quality_score": 0.99,
            "agreement_score": 0.95,
        }
    ]

    response = await client.get("/api/v1/models/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["accuracy"] == 0.92
    assert json_data["data"][0]["data_quality_score"] == 0.99
