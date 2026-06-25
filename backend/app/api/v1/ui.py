# app/api/v1/ui.py
"""
View-shaped read endpoints that power the web dashboard. Each returns data in
exactly the shape the frontend expects, sourced from the `ui_resources` table.
"""

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.ui import UiResource

router = APIRouter()


def _envelope(data: Any) -> dict:
    return {"success": True, "data": data}


async def _list(db: AsyncSession, collection: str) -> List[dict]:
    rows = (
        await db.execute(
            select(UiResource)
            .where(UiResource.collection == collection)
            .order_by(UiResource.ordinal)
        )
    ).scalars().all()
    return [row.payload for row in rows]


async def _item(db: AsyncSession, collection: str, item_id: str) -> dict:
    row = (
        await db.execute(
            select(UiResource).where(
                UiResource.collection == collection,
                UiResource.item_id == item_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{collection[:-1] if collection.endswith('s') else collection} not found",
        )
    return row.payload


@router.get("/zones")
async def get_zones(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "zones"))


@router.get("/tanks")
async def get_tanks(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "tanks"))


@router.get("/tanks/{tank_id}")
async def get_tank(tank_id: str, db: AsyncSession = Depends(get_db)):
    return _envelope(await _item(db, "tanks", tank_id))


@router.get("/alerts")
async def get_alerts(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "alerts"))


@router.get("/recommendations")
async def get_recommendations(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "recommendations"))


@router.get("/biosecurity")
async def get_biosecurity(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "biosecurity"))


@router.get("/analytics")
async def get_analytics(db: AsyncSession = Depends(get_db)):
    return _envelope(await _list(db, "analytics"))


@router.get("/dashboard")
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    return _envelope(await _item(db, "dashboard", "main"))
