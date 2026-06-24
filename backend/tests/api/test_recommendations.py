# tests/api/test_recommendations.py

from datetime import datetime, timezone
import pytest
from uuid import uuid4, UUID
from tests.conftest import MockORM

pytestmark = pytest.mark.asyncio


async def test_list_recommendations_pending(client, mock_services):
    tank_id = uuid4()
    rec_id = uuid4()
    mock_services["recommendation"].get_active_recommendations.return_value = [
        MockORM(
            id=rec_id,
            tank_id=tank_id,
            action="Adjust salinity",
            confidence=0.88,
            priority="Low",
            expected_outcome="Reduce gill stress",
            status="Pending",
            time=datetime.now(timezone.utc),
        )
    ]

    response = await client.get(f"/api/v1/recommendations?tank_id={tank_id}&status_filter=pending")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["action"] == "Adjust salinity"
    assert json_data["data"][0]["status"] == "pending"


async def test_list_recommendations_non_pending(client, mock_services):
    tank_id = uuid4()
    rec_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = [
        MockORM(
            id=rec_id,
            tank_id=tank_id,
            action="Adjust pH",
            confidence=0.95,
            priority="High",
            expected_outcome="Mitigate acid stress",
            status="Accepted",
            time=datetime.now(timezone.utc),
        )
    ]

    response = await client.get(f"/api/v1/recommendations?tank_id={tank_id}&status_filter=accepted")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) == 1
    assert json_data["data"][0]["action"] == "Adjust pH"
    assert json_data["data"][0]["status"] == "accepted"


async def test_accept_recommendation_success(client, mock_services):
    rec_id = uuid4()
    action_id = uuid4()
    # Mocking the lookup
    mock_services["recommendation"].rec_repo.get_multi.return_value = [
        MockORM(id=rec_id, time=datetime.now(timezone.utc))
    ]
    # Mocking the action outcome
    mock_services["recommendation"].execute_recommendation.return_value = MockORM(
        id=action_id,
        executed_at=datetime.now(timezone.utc),
        recommendation_id=rec_id,
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        action="Accepted",
    )

    response = await client.post(f"/api/v1/recommendations/{rec_id}/accept")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["action"] == "Accepted"
    assert json_data["data"]["recommendation_id"] == str(rec_id)


async def test_accept_recommendation_not_found(client, mock_services):
    rec_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = []

    response = await client.post(f"/api/v1/recommendations/{rec_id}/accept")
    assert response.status_code == 404


async def test_dismiss_recommendation_success(client, mock_services):
    rec_id = uuid4()
    action_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = [
        MockORM(id=rec_id, time=datetime.now(timezone.utc))
    ]
    mock_services["recommendation"].dismiss_recommendation.return_value = MockORM(
        id=action_id,
        executed_at=datetime.now(timezone.utc),
        recommendation_id=rec_id,
        user_id=UUID("00000000-0000-0000-0000-000000000000"),
        action="Dismissed",
    )

    response = await client.post(f"/api/v1/recommendations/{rec_id}/dismiss")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["action"] == "Dismissed"


async def test_dismiss_recommendation_not_found(client, mock_services):
    rec_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = []

    response = await client.post(f"/api/v1/recommendations/{rec_id}/dismiss")
    assert response.status_code == 404
