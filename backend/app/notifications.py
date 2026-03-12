from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .auth import get_current_user
from .database import get_db
from .models.notification import InAppNotification
from .schemas.notification import NotificationRead, NotificationsListResponse
from .schemas.user import UserRead


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=NotificationsListResponse)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
) -> NotificationsListResponse:
    notifications = (
        db.query(InAppNotification)
        .filter(InAppNotification.user_id == current_user.id)
        .order_by(InAppNotification.created_at.desc())
        .all()
    )
    return NotificationsListResponse(notifications=notifications)

