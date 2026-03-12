from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class WatchRule(Base):
    __tablename__ = "watch_rules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    # Comma-separated days of week like "MON,TUE,WED"
    days_of_week = Column(String, nullable=True)
    # ISO date range strings "2024-01-01:2024-01-31"
    date_range = Column(String, nullable=True)
    # time range "06:00:12:00"
    time_range = Column(String, nullable=True)

    num_players = Column(Integer, nullable=False, default=2)
    max_price = Column(Integer, nullable=True)
    scan_interval_seconds = Column(Integer, nullable=False, default=60)
    active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User")
    course = relationship("Course")

