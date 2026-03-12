from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models.notification import InAppNotification
from ..models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=None)
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(InAppNotification)
        .filter(InAppNotification.user_id == current_user.id)
        .order_by(InAppNotification.created_at.desc())
        .all()
    )

