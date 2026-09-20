from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.api.deps import get_current_user
from backend.app.repositories.product_repo import product_repo

router = APIRouter(prefix="/alerts", tags=["Alerts"])


class AlertStatusUpdate(BaseModel):
    status: str = Field(..., pattern=r"^(active|resolved|dismissed)$")


@router.get("", response_model=List[Dict[str, Any]])
def list_alerts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List all alerts for the authenticated user, newest first."""
    return product_repo.get_alerts_for_user(current_user["id"])


@router.get("/active", response_model=List[Dict[str, Any]])
def list_active_alerts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """List only active alerts for the authenticated user."""
    return product_repo.get_alerts_for_user(current_user["id"], status="active")


@router.patch("/{alert_id}", response_model=Dict[str, Any])
def update_alert_status(
    alert_id: str,
    payload: AlertStatusUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Update an alert status, e.g. resolved or dismissed."""
    alert = product_repo.get_alert_by_id(alert_id, user_id=current_user["id"])
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    updated = product_repo.update_alert_status(
        alert_id=alert_id,
        user_id=current_user["id"],
        status=payload.status,
    )
    return updated
