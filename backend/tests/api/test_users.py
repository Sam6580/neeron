# tests/api/test_users.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_get_user_profile_success(client, mock_services):
    user_id = uuid4()
    role_id = uuid4()
    mock_services["user"].get_user_profile.return_value = MockORM(
        id=user_id,
        email="sam.houston@neeron.ai",
        first_name="Sam",
        last_name="Houston",
        role_id=role_id,
    )

    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "sam.houston@neeron.ai"
    assert json_data["data"]["first_name"] == "Sam"


async def test_get_user_profile_not_found(client, mock_services):
    user_id = uuid4()
    mock_services["user"].get_user_profile.return_value = None

    response = await client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 404
    json_data = response.json()
    assert json_data["success"] is False
    assert "User not found" in json_data["error"]["message"]


async def test_get_user_audit_logs(client, mock_services):
    user_id = uuid4()
    mock_services["user"].get_user_audit_logs.return_value = [
        MockORM(
            time=datetime.now(timezone.utc),
            event_type="UPDATE_THRESHOLDS",
            action="User updated dissolved_oxygen threshold",
            user_id=user_id,
            ip_address="192.168.1.50",
            target_entity="ThresholdConfig",
            target_id=None,
            old_value={"warning_min": 6.0},
            new_value={"warning_min": 6.5},
        )
    ]

    response = await client.get(f"/api/v1/users/{user_id}/audit-logs?skip=0&limit=5")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["event_type"] == "UPDATE_THRESHOLDS"
    assert json_data["data"][0]["action"] == "User updated dissolved_oxygen threshold"
    assert json_data["data"][0]["new_value"]["warning_min"] == 6.5
