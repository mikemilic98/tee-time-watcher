from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String

from ..database import Base
from .user import PriorityTier


class ScanJobStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    FAILED = "FAILED"


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(Integer, primary_key=True, index=True)
    watch_rule_id = Column(Integer, ForeignKey("watch_rules.id"), nullable=False, index=True)
    scheduled_for = Column(DateTime, nullable=False, default=datetime.utcnow)
    priority_tier = Column(SAEnum(PriorityTier), nullable=False)
    status = Column(SAEnum(ScanJobStatus), nullable=False, default=ScanJobStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)

