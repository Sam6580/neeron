# app/services/auth_service.py

from datetime import datetime, timezone, timedelta
from typing import Optional
from uuid import UUID

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.base import BaseService
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    validate_token,
)
from app.schemas.auth import LoginRequest, LoginResponse, RefreshTokenResponse


class AuthService(BaseService):
    """
    Service managing operations for Authentication, token lifecycle, and audit logs.
    """

    def __init__(self, user_repo: UserRepository, audit_log_repo: AuditLogRepository):
        self.user_repo = user_repo
        self.audit_log_repo = audit_log_repo

    async def authenticate_user(self, login_data: LoginRequest, ip_address: str) -> User:
        """
        Verify credentials. Logs 'LOGIN_FAILED' audit logs on failure.
        """
        user = await self.user_repo.get_by_email(login_data.email)
        if not user or not verify_password(login_data.password, user.password_hash):
            # Log failed login attempt
            user_id = user.id if user else None
            await self.audit_log_repo.create_audit_log(
                event_type="LOGIN_FAILED",
                action=f"Failed login attempt for email: {login_data.email}",
                ip_address=ip_address,
                user_id=user_id,
                target_entity="User",
                target_id=user_id,
            )
            raise ValueError("Invalid email or password")

        if not user.is_active:
            # Log login attempt on inactive user account
            await self.audit_log_repo.create_audit_log(
                event_type="LOGIN_FAILED",
                action=f"Failed login attempt: inactive account for email: {user.email}",
                ip_address=ip_address,
                user_id=user.id,
                target_entity="User",
                target_id=user.id,
            )
            raise ValueError("Inactive user account")

        return user

    async def login(self, user: User, ip_address: str) -> LoginResponse:
        """
        Signs in an authenticated user and creates access/refresh tokens. Logs 'LOGIN_SUCCESS'.
        """
        # Create access and refresh tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Persist refresh token in database
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.user_repo.save_refresh_token(user.id, refresh_token, expires_at)

        # Log successful login
        await self.audit_log_repo.create_audit_log(
            event_type="LOGIN_SUCCESS",
            action=f"User successfully logged in: {user.email}",
            ip_address=ip_address,
            user_id=user.id,
            target_entity="User",
            target_id=user.id,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    async def refresh_access_token(self, refresh_token: str, ip_address: str) -> RefreshTokenResponse:
        """
        Validates refresh token and issues rotated access/refresh tokens. Logs 'REFRESH_TOKEN'.
        """
        try:
            # 1. Validate JWT signature and format (raises ValueError on failure)
            # 2. Ensure token type == refresh (internally verified by validate_token)
            payload = validate_token(refresh_token, "refresh")
            user_id_str = payload.get("sub")
            if not user_id_str:
                raise ValueError("Invalid token payload structure: missing sub claim")

            try:
                user_id = UUID(user_id_str)
            except ValueError:
                raise ValueError("Invalid user ID format in token sub claim")

            # 3. Lookup stored refresh token
            user = await self.user_repo.get_by_refresh_token(refresh_token)
            if not user:
                raise ValueError("Refresh token is revoked, rotated, or invalid")

            # 4. Ensure stored token matches
            if user.refresh_token != refresh_token:
                raise ValueError("Provided refresh token does not match persisted token")

            # 5. Ensure DB expiry has not been exceeded
            if not user.refresh_token_expires_at:
                raise ValueError("Refresh token expiration missing in database")
            
            expiry = user.refresh_token_expires_at
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry < datetime.now(timezone.utc):
                raise ValueError("Refresh token has expired in database")

            # 6. Ensure user account status
            if not user.is_active:
                raise ValueError("User account is inactive")

            # 7. Rotate tokens
            new_access_token = create_access_token(data={"sub": str(user.id)})
            new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
            new_expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            # 8. Save the new refresh token (rotating / invalidating old one)
            await self.user_repo.save_refresh_token(user.id, new_refresh_token, new_expires_at)

        except ValueError as e:
            # Log failed token refresh
            await self.audit_log_repo.create_audit_log(
                event_type="REFRESH_TOKEN_FAILED",
                action=f"Failed token refresh: {str(e)}",
                ip_address=ip_address,
                target_entity="User",
            )
            raise ValueError(f"Invalid refresh token: {str(e)}")

        # Log successful token refresh
        await self.audit_log_repo.create_audit_log(
            event_type="REFRESH_TOKEN",
            action=f"User refreshed access token: {user.email}",
            ip_address=ip_address,
            user_id=user.id,
            target_entity="User",
            target_id=user.id,
        )

        return RefreshTokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    async def logout(self, user: User, ip_address: str) -> bool:
        """
        Clears user session by invalidating the refresh token. Logs 'LOGOUT'.
        """
        await self.user_repo.invalidate_refresh_token(user.id)

        await self.audit_log_repo.create_audit_log(
            event_type="LOGOUT",
            action=f"User logged out: {user.email}",
            ip_address=ip_address,
            user_id=user.id,
            target_entity="User",
            target_id=user.id,
        )
        return True

    async def get_current_user_profile(self, user: User) -> User:
        """
        Retrieves the profile of the current active user.
        """
        return user
