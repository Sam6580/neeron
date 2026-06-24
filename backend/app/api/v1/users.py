# app/api/v1/users.py

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_user_service
from app.services.user_service import UserService
from app.schemas.base import BaseResponse
from app.schemas.user import UserResponse, AuditLogResponse

router = APIRouter()


@router.get("/{user_id}", response_model=BaseResponse[UserResponse])
async def get_user_profile(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
):
    """
    Retrieves the registration properties for a single user.
    """
    user = await service.get_user_profile(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found with ID {user_id}",
        )
    return BaseResponse(data=user)


@router.get("/{user_id}/audit-logs", response_model=BaseResponse[List[AuditLogResponse]])
async def get_user_audit_logs(
    user_id: UUID,
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
):
    """
    Retrieves security and operations edit audit trails logged for the user.
    """
    logs = await service.get_user_audit_logs(user_id=user_id, skip=skip, limit=limit)
    return BaseResponse(data=logs)
