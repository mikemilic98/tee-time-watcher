from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, Integer, String

from ..database import Base


class PriorityTier(str, Enum):
    PLATINUM = "PLATINUM"
    PRIORITY = "PRIORITY"
    STANDARD = "STANDARD"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    priority_tier = Column(SAEnum(PriorityTier), default=PriorityTier.STANDARD, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

