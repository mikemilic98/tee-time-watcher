from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from ..database import Base


class TeeTimeCandidate(Base):
    __tablename__ = "tee_time_candidates"

    id = Column(Integer, primary_key=True, index=True)
    watch_rule_id = Column(Integer, ForeignKey("watch_rules.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    tee_time = Column(DateTime, nullable=False)
    price = Column(Integer, nullable=True)
    num_players = Column(Integer, nullable=False, default=2)
    found_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    watch_rule = relationship("WatchRule")

