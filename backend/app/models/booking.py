from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship

from ..database import Base


class BookingStatus(str, Enum):
    PENDING_USER_CONFIRM = "PENDING_USER_CONFIRM"
    CONFIRMED = "CONFIRMED"
    AUTO_CANCELLED = "AUTO_CANCELLED"
    CANCELLED_BY_USER = "CANCELLED_BY_USER"
    FAILED = "FAILED"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    tee_time = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=True)
    num_players = Column(Integer, nullable=False, default=2)

    status = Column(SAEnum(BookingStatus), nullable=False, default=BookingStatus.PENDING_USER_CONFIRM)
    external_reference = Column(String, nullable=True)
    auto_booked = Column(Boolean, nullable=False, default=False)
    must_cancel_by = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    course = relationship("Course")

