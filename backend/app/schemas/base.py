# app/schemas/base.py

from datetime import datetime, timezone
from typing import Any, Generic, List, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Standard top-level JSON response wrapper for NEERON API v1 endpoints.
    """
    success: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: T


class PaginationMeta(BaseModel):
    """
    Metadata carrying pagination attributes.
    """
    currentPage: int
    totalPages: int
    limit: int
    totalCount: int


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Standard top-level paginated list response wrapper.
    """
    success: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: List[T]
    pagination: PaginationMeta
