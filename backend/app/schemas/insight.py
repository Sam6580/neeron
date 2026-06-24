# app/schemas/insight.py

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AiInsightResponse(BaseModel):
    id: UUID
    tankId: UUID
    priority: str = Field(..., max_length=50)
    confidence: float
    title: str = Field(..., max_length=150)
    description: str
    generatedAt: datetime
    expiresAt: Optional[datetime] = None
