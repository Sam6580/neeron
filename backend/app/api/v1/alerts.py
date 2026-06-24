# app/api/v1/alerts.py

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import get_alert_service
from app.services.alert_service import AlertService
from app.schemas.base import BaseResponse
from app.schemas.alert import AlertResponse

router = APIRouter()


@router.get("", response_model=BaseResponse[List[AlertResponse]])
async def list_alerts(
    farm_id: Optional[UUID] = None,
    tank_id: Optional[UUID] = None,
    status_filter: Optional[str] = "unresolved",
    severity: Optional[str] = None,
    service: AlertService = Depends(get_alert_service),
):
    """
    Retrieves active alerts, optionally filtered by farm, tank, status, or severity.
    """
    # Map 'unresolved' indicator to Active state
    db_status = "Active" if status_filter == "unresolved" else (status_filter.capitalize() if status_filter else None)

    if db_status == "Active":
        alerts = await service.get_active_alerts(farm_id=farm_id, tank_id=tank_id)
    else:
        filters = {}
        if tank_id:
            filters["tank_id"] = tank_id
        if db_status:
            filters["status"] = db_status
        alerts = await service.alert_repo.get_multi(filters=filters)

    # In-memory filtering for severity if specified
    if severity:
        alerts = [a for a in alerts if a.severity.lower() == severity.lower()]

    return BaseResponse(data=alerts)


@router.post("/{id}/acknowledge", response_model=BaseResponse[AlertResponse])
async def acknowledge_alert(
    id: UUID,
    service: AlertService = Depends(get_alert_service),
):
    """
    Acknowledges an active alert using its ID.
    """
    alerts = await service.alert_repo.get_multi(filters={"id": id}, limit=1)
    if not alerts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert not found with ID {id}",
        )
    alert = alerts[0]

    # Mock user ID for audit trails until auth setup is ready
    user_id = UUID("00000000-0000-0000-0000-000000000000")
    updated_alert = await service.acknowledge_alert(
        alert_id=alert.id, alert_time=alert.time, user_id=user_id
    )

    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to acknowledge alert. It may already be resolved.",
        )

    return BaseResponse(data=updated_alert)
