from sqlalchemy import Boolean, Column, Integer, String

from ..database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    booking_window_days = Column(Integer, nullable=False, default=7)
    cancellation_policy_hours_before = Column(Integer, nullable=False, default=24)
    booking_fee_threshold = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)

