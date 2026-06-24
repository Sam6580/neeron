# tests/api/test_insights.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_dashboard_insights(client, mock_services):
    farm_id = uuid4()
    tank_id = uuid4()
    insight_id = uuid4()

    mock_services["ai_insight"].generate_dashboard_insights.return_value = [
        MockORM(
            id=insight_id,
            tank_id=tank_id,
            priority="Critical",
            confidence=0.94,
            title="Hypoxia Risk Detected",
            description="Dissolved oxygen levels show a steady downward trend in Cage-05.",
            generated_at=datetime.now(timezone.utc),
            expires_at=None,
        )
    ]

    response = await client.get(f"/api/v1/insights/dashboard?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["title"] == "Hypoxia Risk Detected"
    assert json_data["data"][0]["priority"] == "Critical"
    assert json_data["data"][0]["confidence"] == 0.94


async def test_get_tank_insights(client, mock_services):
    tank_id = uuid4()
    insight_id = uuid4()

    mock_services["ai_insight"].generate_tank_insights.return_value = [
        MockORM(
            id=insight_id,
            tank_id=tank_id,
            priority="Warning",
            confidence=0.81,
            title="Slight Temp Rise",
            description="Temperature is climbing slowly but stable.",
            generated_at=datetime.now(timezone.utc),
            expires_at=None,
        )
    ]

    response = await client.get(f"/api/v1/insights/tanks/{tank_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["title"] == "Slight Temp Rise"
    assert json_data["data"][0]["priority"] == "Warning"
