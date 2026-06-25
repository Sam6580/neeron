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
    from app.api.v1.dependencies.auth import get_current_active_user
    from app.main import app
    expected_user = app.dependency_overrides[get_current_active_user]()

    rec_id = uuid4()
    action_id = uuid4()
    # Mocking the lookup
    rec = MockORM(id=rec_id, time=datetime.now(timezone.utc))
    mock_services["recommendation"].rec_repo.get_multi.return_value = [rec]
    # Mocking the action outcome
    mock_services["recommendation"].execute_recommendation.return_value = MockORM(
        id=action_id,
        executed_at=datetime.now(timezone.utc),
        recommendation_id=rec_id,
        user_id=expected_user.id,
        action="Accepted",
    )

    response = await client.post(f"/api/v1/recommendations/{rec_id}/accept")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["action"] == "Accepted"
    assert json_data["data"]["recommendation_id"] == str(rec_id)
    assert json_data["data"]["user_id"] == str(expected_user.id)

    mock_services["recommendation"].execute_recommendation.assert_called_once_with(
        recommendation_id=rec_id,
        recommendation_time=rec.time,
        user_id=expected_user.id,
        notes="Accepted via API v1 endpoint",
    )


async def test_accept_recommendation_not_found(client, mock_services):
    rec_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = []

    response = await client.post(f"/api/v1/recommendations/{rec_id}/accept")
    assert response.status_code == 404


async def test_dismiss_recommendation_success(client, mock_services):
    from app.api.v1.dependencies.auth import get_current_active_user
    from app.main import app
    expected_user = app.dependency_overrides[get_current_active_user]()

    rec_id = uuid4()
    action_id = uuid4()
    rec = MockORM(id=rec_id, time=datetime.now(timezone.utc))
    mock_services["recommendation"].rec_repo.get_multi.return_value = [rec]
    mock_services["recommendation"].dismiss_recommendation.return_value = MockORM(
        id=action_id,
        executed_at=datetime.now(timezone.utc),
        recommendation_id=rec_id,
        user_id=expected_user.id,
        action="Dismissed",
    )

    response = await client.post(f"/api/v1/recommendations/{rec_id}/dismiss")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["action"] == "Dismissed"
    assert json_data["data"]["user_id"] == str(expected_user.id)

    mock_services["recommendation"].dismiss_recommendation.assert_called_once_with(
        recommendation_id=rec_id,
        recommendation_time=rec.time,
        user_id=expected_user.id,
        notes="Dismissed via API v1 endpoint",
    )


async def test_dismiss_recommendation_not_found(client, mock_services):
    rec_id = uuid4()
    mock_services["recommendation"].rec_repo.get_multi.return_value = []

    response = await client.post(f"/api/v1/recommendations/{rec_id}/dismiss")
    assert response.status_code == 404
