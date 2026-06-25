# app/schemas/user.py

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class UserResponse(BaseModel):
    id: UUID
    email: str = Field(..., max_length=150)
    first_name: str = Field(..., max_length=100)
    last_name: str = Field(..., max_length=100)
    role_id: UUID

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    time: datetime
    event_type: str
    action: str
    user_id: Optional[UUID] = None
    target_entity: Optional[str] = None
    target_id: Optional[UUID] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: str

    model_config = ConfigDict(from_attributes=True)
