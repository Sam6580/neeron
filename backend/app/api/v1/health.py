# app/api/v1/health.py

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.base import BaseResponse
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get("", response_model=BaseResponse[HealthResponse])
async def check_health(db: AsyncSession = Depends(get_db)):
    """
    Returns API operational status and validates the core database connection.
    """
    db_status = "offline"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "online"
    except Exception:
        pass

    return BaseResponse(
        data=HealthResponse(
            status="healthy",
            database=db_status,
            timestamp=datetime.now(timezone.utc),
        )
    )
