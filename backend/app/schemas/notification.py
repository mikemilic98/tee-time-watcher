from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: int
    user_id: int
    type: str
    payload_json: str
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationsListResponse(BaseModel):
    notifications: list[NotificationRead]

