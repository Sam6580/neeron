# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.v1.deps import get_auth_service
from app.services.auth_service import AuthService
from app.api.v1.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.base import BaseResponse
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    UserProfileResponse,
)

router = APIRouter()


@router.post("/login", response_model=BaseResponse[LoginResponse])
async def login(
    request: Request,
    login_data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user and generate access/refresh tokens.
    """
    ip_address = request.client.host if request.client else "127.0.0.1"
    try:
        user = await service.authenticate_user(login_data, ip_address)
        response_data = await service.login(user, ip_address)
        return BaseResponse(data=response_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/refresh", response_model=BaseResponse[RefreshTokenResponse])
async def refresh(
    request: Request,
    refresh_data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
):
    """
    Refresh access and refresh tokens via rotation.
    """
    ip_address = request.client.host if request.client else "127.0.0.1"
    try:
        response_data = await service.refresh_access_token(
            refresh_data.refresh_token, ip_address
        )
        return BaseResponse(data=response_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/logout", response_model=BaseResponse[LogoutResponse])
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Logout the current authenticated user and clear their session.
    """
    ip_address = request.client.host if request.client else "127.0.0.1"
    await service.logout(current_user, ip_address)
    return BaseResponse(
        data=LogoutResponse(success=True, message="Successfully logged out.")
    )


@router.get("/me", response_model=BaseResponse[UserProfileResponse])
async def get_me(
    current_user: User = Depends(get_current_active_user),
    service: AuthService = Depends(get_auth_service),
):
    """
    Retrieve details of the currently authenticated user.
    """
    user = await service.get_current_user_profile(current_user)
    profile = UserProfileResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role_name=user.role.name if user.role else "Viewer",
        permissions=user.role.permissions if user.role else {},
    )
    return BaseResponse(data=profile)
