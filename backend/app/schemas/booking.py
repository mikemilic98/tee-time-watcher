from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from ..models.booking import BookingStatus


class BookingBase(BaseModel):
    course_id: int
    tee_time: datetime
    price: Optional[int] = None
    num_players: int
    status: BookingStatus
    external_reference: Optional[str] = None
    auto_booked: bool
    must_cancel_by: Optional[datetime] = None


class BookingRead(BookingBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BookingActionResponse(BaseModel):
    booking: BookingRead

