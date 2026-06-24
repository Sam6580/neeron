# app/schemas/health.py

from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    database: str
    timestamp: datetime
