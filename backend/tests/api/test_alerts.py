# tests/api/test_alerts.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_list_alerts_active(client, mock_services):
    farm_id = uuid4()
    alert_id = uuid4()
    tank_id = uuid4()

    mock_services["alert"].get_active_alerts.return_value = [
        MockORM(
            id=alert_id,
            time=datetime.now(timezone.utc),
            tank_id=tank_id,
            sensor_id=uuid4(),
            type="Oxygen Depletion",
            severity="Critical",
            status="Active",
            message="DO has dropped below critical levels.",
            acknowledged_at=None,
            resolved_at=None,
            resolved_by=None,
        )
    ]

    response = await client.get(f"/api/v1/alerts?farm_id={farm_id}&status_filter=unresolved")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["severity"] == "Critical"
    assert json_data["data"][0]["type"] == "Oxygen Depletion"


async def test_list_alerts_with_severity_filter(client, mock_services):
    farm_id = uuid4()
    alert_id = uuid4()
    tank_id = uuid4()

    mock_services["alert"].get_active_alerts.return_value = [
        MockORM(
            id=alert_id,
            time=datetime.now(timezone.utc),
            tank_id=tank_id,
            sensor_id=None,
            type="Temperature spike",
            severity="Warning",
            status="Active",
            message="Temp is 16.5C",
            acknowledged_at=None,
            resolved_at=None,
            resolved_by=None,
        )
    ]

    # Filter with severity=critical (expect 0)
    response = await client.get(f"/api/v1/alerts?farm_id={farm_id}&status_filter=unresolved&severity=critical")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 0

    # Filter with severity=warning (expect 1)
    response = await client.get(f"/api/v1/alerts?farm_id={farm_id}&status_filter=unresolved&severity=warning")
    assert response.status_code == 200
    assert len(response.json()["data"]) == 1


async def test_acknowledge_alert_success(client, mock_services):
    alert_id = uuid4()
    tank_id = uuid4()
    mock_services["alert"].alert_repo.get_multi.return_value = [
        MockORM(id=alert_id, time=datetime.now(timezone.utc))
    ]
    mock_services["alert"].acknowledge_alert.return_value = MockORM(
        id=alert_id,
        time=datetime.now(timezone.utc),
        tank_id=tank_id,
        sensor_id=None,
        type="Temperature spike",
        severity="Warning",
        status="Acknowledged",
        message="Temp is 16.5C",
        acknowledged_at=datetime.now(timezone.utc),
        resolved_at=None,
        resolved_by=None,
    )

    response = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["status"] == "Acknowledged"
    assert json_data["data"]["acknowledged_at"] is not None


async def test_acknowledge_alert_not_found(client, mock_services):
    alert_id = uuid4()
    mock_services["alert"].alert_repo.get_multi.return_value = []

    response = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert response.status_code == 404


async def test_acknowledge_alert_already_resolved(client, mock_services):
    alert_id = uuid4()
    mock_services["alert"].alert_repo.get_multi.return_value = [
        MockORM(id=alert_id, time=datetime.now(timezone.utc))
    ]
    mock_services["alert"].acknowledge_alert.return_value = None

    response = await client.post(f"/api/v1/alerts/{alert_id}/acknowledge")
    assert response.status_code == 400
    assert "may already be resolved" in response.json()["error"]["message"]
