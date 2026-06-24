# tests/api/test_biosecurity.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_biosecurity_overview(client, mock_services):
    farm_id = uuid4()
    tank_id = uuid4()

    mock_services["biosecurity"].get_biosecurity_dashboard.return_value = {
        "total_tanks": 12,
        "quarantined_tanks_count": 1,
        "quarantined_tanks": [
            {
                "tank_id": tank_id,
                "name": "Cage-05",
                "quarantine_event": MockORM(
                    reason="Sea lice density exceeds threshold",
                    severity="Warning",
                    started_at=datetime.now(timezone.utc),
                ),
            }
        ],
        "compliance_reports": [MockORM(), MockORM()],
    }

    response = await client.get(f"/api/v1/biosecurity?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["farmId"] == str(farm_id)
    assert json_data["data"]["quarantinedTanksCount"] == 1
    assert json_data["data"]["quarantinedTanks"][0]["name"] == "Cage-05"


async def test_list_pathogens(client, mock_base_repo_methods):
    mock_get, mock_get_multi = mock_base_repo_methods
    pathogen_id = uuid4()

    mock_get_multi.return_value = [
        MockORM(
            id=pathogen_id,
            name="Caligus rogercresseyi",
            transmission_vector="Waterborne parasites",
            incubation_days=10,
        )
    ]

    response = await client.get("/api/v1/biosecurity/pathogens")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["scientificName"] == "Caligus rogercresseyi"
    assert json_data["data"][0]["incubationPeriodDays"] == 10


async def test_list_outbreaks(client, mock_services):
    farm_id = uuid4()
    tank_id = uuid4()

    mock_services["tank"].get_tank_dashboard.return_value = [
        {"tank_id": tank_id, "name": "Cage-05"}
    ]
    mock_services["biosecurity"].get_pathogen_summary.return_value = [
        MockORM(
            status="Critical",
            risk_level="High",
            pathogen_count=8.5,
            pathogen=MockORM(name="Caligus rogercresseyi"),
        )
    ]
    mock_services["biosecurity"].get_quarantine_status.return_value = {
        "is_quarantined": True
    }

    response = await client.get(f"/api/v1/biosecurity/outbreaks?farm_id={farm_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["tankName"] == "Cage-05"
    assert json_data["data"][0]["currentPathogenCount"] == 8.5
    assert json_data["data"][0]["quarantineActive"] is True
