# tests/api/test_dashboard.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_dashboard_overview(client, mock_services):
    farm_id = uuid4()
    zone_id = uuid4()
    rec_id = uuid4()
    tank_id = uuid4()

    mock_services["dashboard"].get_dashboard_overview.return_value = {
        "farm_id": farm_id,
        "health_score": 88.5,
        "active_alerts_count": 3,
        "alert_summary": {"total": 3, "severities": {"Info": 1, "Warning": 1, "Critical": 1}},
        "zone_overview": [
            {
                "zone_id": zone_id,
                "name": "Zone A",
                "tank_count": 4,
                "average_psi": 1.2,
            }
        ],
        "recent_recommendations": [
            MockORM(
                id=rec_id,
                tank_id=tank_id,
                action="Increase DO aeration",
                confidence=0.92,
                priority="Critical",
                expected_outcome="Avoid hypoxia risk",
                status="Pending",
                time=datetime.now(timezone.utc),
            )
        ],
    }

    mock_services["dashboard"].dashboard_repo.get_farm_health_snapshot.return_value = MockORM(
        psi_average=2.1
    )

    response = await client.get(f"/api/v1/dashboard/overview?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["farmHealthScore"]["score"] == 88.5
    assert data["farmHealthScore"]["classification"] == "Optimal"
    assert data["activeAlertsCount"] == 3
    assert data["activeRecommendationsCount"] == 1
    assert data["averagePsi"] == 2.1
    assert len(data["zoneOverview"]) == 1
    assert data["zoneOverview"][0]["name"] == "Zone A"
    assert len(data["recentInsights"]) == 1
    assert data["recentInsights"][0]["title"] == "Increase DO aeration"


async def test_get_dashboard_health(client, mock_services):
    farm_id = uuid4()
    mock_services["dashboard"].get_global_health_score.return_value = 75.0
    mock_services["dashboard"].dashboard_repo.get_farm_health_snapshot.return_value = MockORM(
        risk_score=45.2, psi_average=1.8
    )

    response = await client.get(f"/api/v1/dashboard/health?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    data = json_data["data"]
    assert data["health_score"] == 75.0
    assert data["risk_score"] == 45.2
    assert data["psi_average"] == 1.8


async def test_get_dashboard_trends(client, mock_services):
    farm_id = uuid4()
    mock_services["dashboard"].get_risk_trends.return_value = [
        {"recorded_at": datetime.now(timezone.utc), "risk_score": 15.4}
    ]

    response = await client.get(f"/api/v1/dashboard/trends?farm_id={farm_id}&days=7")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]["trends"]) == 1
    assert json_data["data"]["trends"][0]["risk_score"] == 15.4


async def test_get_dashboard_recommendations(client, mock_services):
    farm_id = uuid4()
    tank_id = uuid4()
    rec_id = uuid4()

    mock_services["dashboard"].get_recent_recommendations.return_value = [
        MockORM(
            id=rec_id,
            tank_id=tank_id,
            action="Harvest early",
            confidence=0.88,
            priority="Medium",
            expected_outcome="Maximize ROI",
            status="Pending",
            time=datetime.now(timezone.utc),
        )
    ]

    response = await client.get(f"/api/v1/dashboard/recommendations?farm_id={farm_id}&limit=5")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["action"] == "Harvest early"
