# app/schemas/user.py

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class UserResponse(BaseModel):
    id: UUID
    email: str = Field(..., max_length=150)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role_id: UUID

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: UUID
    time: datetime
    action: str = Field(..., max_length=100)
    user_id: UUID
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    details: Dict[str, Any]

    class Config:
        from_attributes = True
