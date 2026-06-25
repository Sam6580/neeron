# tests/api/test_auth.py

from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest import mock
import pytest
from fastapi import APIRouter, Depends, HTTPException, status
from tests.conftest import MockORM

from app.main import app
from app.api.v1.dependencies.auth import get_current_user, get_current_active_user
from app.core.security import create_access_token, create_refresh_token
from app.core.rbac import require_roles, require_permissions
from app.schemas.auth import LoginRequest, RefreshTokenRequest

pytestmark = pytest.mark.asyncio

# Create a test router to verify role and permission check dependencies
test_router = APIRouter(prefix="/api/v1/test-auth-gating", tags=["TestAuthGating"])


@test_router.get("/role-admin", dependencies=[Depends(require_roles("Administrator"))])
async def role_admin_endpoint():
    return {"message": "success"}


@test_router.get("/perm-write-tanks", dependencies=[Depends(require_permissions("write:tanks"))])
async def perm_write_tanks_endpoint():
    return {"message": "success"}


# Mount the test router to the main application
app.include_router(test_router)


# ── LOGIN ENDPOINT TESTS ─────────────────────────────────────────────────────

async def test_login_success(client, mock_services):
    """Test successful user login."""
    user_id = uuid4()
    mock_user = MockORM(
        id=user_id,
        email="test@neeron.ai",
        password_hash="hashed_pw",
        is_active=True,
    )
    
    mock_services["auth"].authenticate_user.return_value = mock_user
    mock_services["auth"].login.return_value = MockORM(
        access_token="mock_access",
        refresh_token="mock_refresh",
        token_type="bearer",
    )

    payload = {"email": "test@neeron.ai", "password": "password123"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["access_token"] == "mock_access"
    assert json_data["data"]["refresh_token"] == "mock_refresh"


async def test_login_invalid_credentials(client, mock_services):
    """Test login failure with invalid email or password."""
    mock_services["auth"].authenticate_user.side_effect = ValueError("Invalid email or password")

    payload = {"email": "bad@neeron.ai", "password": "wrongpassword"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert "Invalid email or password" in json_data["error"]["message"]


async def test_login_inactive_user(client, mock_services):
    """Test login failure with inactive user account."""
    mock_services["auth"].authenticate_user.side_effect = ValueError("Inactive user account")

    payload = {"email": "inactive@neeron.ai", "password": "password123"}
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert "Inactive user account" in json_data["error"]["message"]


# ── TOKEN REFRESH TESTS ─────────────────────────────────────────────────────

async def test_refresh_success(client, mock_services):
    """Test successful token refresh flow."""
    mock_services["auth"].refresh_access_token.return_value = MockORM(
        access_token="new_access",
        refresh_token="new_refresh",
        token_type="bearer",
    )

    payload = {"refresh_token": "valid_refresh_token"}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["access_token"] == "new_access"
    assert json_data["data"]["refresh_token"] == "new_refresh"


async def test_refresh_invalid_token(client, mock_services):
    """Test refresh token failure with invalid token."""
    mock_services["auth"].refresh_access_token.side_effect = ValueError("Invalid refresh token")

    payload = {"refresh_token": "invalid_refresh_token"}
    response = await client.post("/api/v1/auth/refresh", json=payload)
    assert response.status_code == 401
    json_data = response.json()
    assert json_data["success"] is False
    assert "Invalid refresh token" in json_data["error"]["message"]


# ── LOGOUT ENDPOINT TESTS ────────────────────────────────────────────────────

async def test_logout_success(client, mock_services):
    """Test successful user logout."""
    user_id = uuid4()
    mock_user = MockORM(
        id=user_id,
        email="test@neeron.ai",
        is_active=True,
    )
    
    # Override authentication dependencies
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "Successfully logged out" in json_data["data"]["message"]

    # Clear overrides
    del app.dependency_overrides[get_current_active_user]


# ── PROFILE RETRIEVAL / GET ME TESTS ─────────────────────────────────────────

async def test_get_me_success(client, mock_services):
    """Test retrieving profile of current authenticated user."""
    user_id = uuid4()
    mock_user = MockORM(
        id=user_id,
        email="test@neeron.ai",
        first_name="Jane",
        last_name="Doe",
        is_active=True,
        role=MockORM(
            name="Aquaculture Analyst",
            permissions={"read:tanks": True},
        )
    )
    
    mock_services["auth"].get_current_user_profile.return_value = mock_user
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["email"] == "test@neeron.ai"
    assert json_data["data"]["role_name"] == "Aquaculture Analyst"
    assert json_data["data"]["permissions"]["read:tanks"] is True

    # Clear overrides
    del app.dependency_overrides[get_current_active_user]


# ── JWT LIFECYCLE & SECURITY DEPENDENCY VALIDATION ────────────────────────────

async def test_get_current_user_valid_token(mock_services):
    """Test that valid JWT access token resolves to the correct user."""
    user_id = uuid4()
    mock_user = MockORM(
        id=user_id,
        email="jwt@neeron.ai",
        is_active=True,
    )
    
    mock_services["user"].get_user_profile.return_value = mock_user
    
    token = create_access_token(data={"sub": str(user_id)})
    resolved_user = await get_current_user(token=token, user_service=mock_services["user"])
    
    assert resolved_user.id == user_id
    assert resolved_user.email == "jwt@neeron.ai"


async def test_get_current_user_expired_token(mock_services):
    """Test that expired JWT access token is rejected."""
    user_id = uuid4()
    # Issue a token expired in the past
    token = create_access_token(data={"sub": str(user_id)}, expires_delta=timedelta(minutes=-5))
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(token=token, user_service=mock_services["user"])
        
    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in exc_info.value.detail.lower()


# ── RBAC & PERMISSION CHECK ENFORCEMENT ──────────────────────────────────────

async def test_rbac_require_roles_success(client):
    """Test that user with correct role is allowed access."""
    mock_user = MockORM(
        email="admin@neeron.ai",
        is_active=True,
        role=MockORM(name="Administrator", permissions={}),
    )
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/test-auth-gating/role-admin")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}

    del app.dependency_overrides[get_current_active_user]


async def test_rbac_require_roles_forbidden(client):
    """Test that user with incorrect role is denied access."""
    mock_user = MockORM(
        email="viewer@neeron.ai",
        is_active=True,
        role=MockORM(name="Viewer", permissions={}),
    )
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/test-auth-gating/role-admin")
    assert response.status_code == 403
    assert "Forbidden" in response.json()["error"]["message"] or response.status_code == 403

    del app.dependency_overrides[get_current_active_user]


async def test_rbac_require_permissions_success(client):
    """Test that user with correct permission is allowed access."""
    mock_user = MockORM(
        email="op@neeron.ai",
        is_active=True,
        role=MockORM(name="Operations Manager", permissions={"write:tanks": True}),
    )
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/test-auth-gating/perm-write-tanks")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}

    del app.dependency_overrides[get_current_active_user]


async def test_rbac_require_permissions_forbidden(client):
    """Test that user without correct permission is denied access."""
    mock_user = MockORM(
        email="biologist@neeron.ai",
        is_active=True,
        role=MockORM(name="Biologist", permissions={"write:tanks": False}),
    )
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/test-auth-gating/perm-write-tanks")
    assert response.status_code == 403

    del app.dependency_overrides[get_current_active_user]


async def test_rbac_administrator_bypass(client):
    """Test that Administrator bypasses permission check even if not granted explicitly."""
    mock_user = MockORM(
        email="admin@neeron.ai",
        is_active=True,
        role=MockORM(name="Administrator", permissions={"write:tanks": False}),
    )
    app.dependency_overrides[get_current_active_user] = lambda: mock_user

    response = await client.get("/api/v1/test-auth-gating/perm-write-tanks")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}

    del app.dependency_overrides[get_current_active_user]


# ── SERVICE LAYER PERSISTENCE & ROTATION TESTS ──────────────────────────────────

async def test_auth_service_login_persists_token():
    """Verify that AuthService.login generates and persists refresh token in DB."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    mock_user = MockORM(id=user_id, email="persist@neeron.io")

    response = await auth_service.login(mock_user, "127.0.0.1")
    assert response.access_token is not None
    assert response.refresh_token is not None

    # Assert that save_refresh_token was called with expected arguments
    user_repo.save_refresh_token.assert_called_once()
    call_args = user_repo.save_refresh_token.call_args[0]
    assert call_args[0] == user_id
    assert call_args[1] == response.refresh_token
    # Expiry should be around 7 days from now
    assert isinstance(call_args[2], datetime)
    assert call_args[2] > datetime.now(timezone.utc) + timedelta(days=6)


async def test_auth_service_refresh_rotation_success():
    """Verify that AuthService.refresh_access_token rotates the token and returns new pair."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    # Generate a valid JWT refresh token matching user_id
    token = create_refresh_token(data={"sub": str(user_id)}, expires_delta=timedelta(days=4))

    mock_user = MockORM(
        id=user_id,
        email="rotate@neeron.io",
        refresh_token=token,
        refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
        is_active=True,
    )
    user_repo.get_by_refresh_token.return_value = mock_user

    response = await auth_service.refresh_access_token(token, "127.0.0.1")
    assert response.access_token is not None
    assert response.refresh_token is not None
    assert response.refresh_token != token

    # Check rotation
    user_repo.save_refresh_token.assert_called_once()
    rotated_user_id, rotated_token, rotated_expiry = user_repo.save_refresh_token.call_args[0]
    assert rotated_user_id == user_id
    assert rotated_token == response.refresh_token
    assert rotated_expiry > datetime.now(timezone.utc) + timedelta(days=6)


async def test_auth_service_refresh_mismatched_token():
    """Verify that refresh raises ValueError if token doesn't match the one in DB."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    token = create_refresh_token(data={"sub": str(user_id)})

    # Mock user having a different refresh token in DB
    mock_user = MockORM(
        id=user_id,
        email="mismatch@neeron.io",
        refresh_token="different_token",
        refresh_token_expires_at=datetime.now(timezone.utc) + timedelta(days=5),
        is_active=True,
    )
    user_repo.get_by_refresh_token.return_value = mock_user

    with pytest.raises(ValueError) as exc_info:
        await auth_service.refresh_access_token(token, "127.0.0.1")
    assert "does not match" in str(exc_info.value)
    
    # Audit log should log failure
    audit_log_repo.create_audit_log.assert_called_once_with(
        event_type="REFRESH_TOKEN_FAILED",
        action=mock.ANY,
        ip_address="127.0.0.1",
        target_entity="User",
    )


async def test_auth_service_refresh_expired_db_token():
    """Verify that refresh raises ValueError if refresh token is expired in database."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    token = create_refresh_token(data={"sub": str(user_id)})

    # Mock user having expired token in DB
    mock_user = MockORM(
        id=user_id,
        email="expired@neeron.io",
        refresh_token=token,
        refresh_token_expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        is_active=True,
    )
    user_repo.get_by_refresh_token.return_value = mock_user

    with pytest.raises(ValueError) as exc_info:
        await auth_service.refresh_access_token(token, "127.0.0.1")
    assert "expired in database" in str(exc_info.value)


async def test_auth_service_refresh_revoked_token():
    """Verify that refresh raises ValueError if token is not found (revoked/rotated)."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    token = create_refresh_token(data={"sub": str(user_id)})

    # Mock get_by_refresh_token returning None (token revoked)
    user_repo.get_by_refresh_token.return_value = None

    with pytest.raises(ValueError) as exc_info:
        await auth_service.refresh_access_token(token, "127.0.0.1")
    assert "revoked, rotated, or invalid" in str(exc_info.value)


async def test_auth_service_logout_invalidates_token():
    """Verify that logout invalidates token in DB."""
    from unittest.mock import AsyncMock
    from app.services.auth_service import AuthService

    user_repo = AsyncMock()
    audit_log_repo = AsyncMock()
    auth_service = AuthService(user_repo=user_repo, audit_log_repo=audit_log_repo)

    user_id = uuid4()
    mock_user = MockORM(id=user_id, email="logout@neeron.io")

    result = await auth_service.logout(mock_user, "127.0.0.1")
    assert result is True
    user_repo.invalidate_refresh_token.assert_called_once_with(user_id)

