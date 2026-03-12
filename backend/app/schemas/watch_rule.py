from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


DayAbbrev = Literal["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]


class WatchRuleCreate(BaseModel):
    course_id: int
    num_players: int = 2
    max_price: Optional[int] = None
    scan_interval_seconds: int = Field(default=60, ge=30, le=3600)
    active: bool = True

    # Either provide explicit days, or use weekends_only / weekdays_only helpers.
    days_of_week: Optional[list[DayAbbrev]] = None
    weekends_only: bool | None = None
    weekdays_only: bool | None = None

    # Time window for tee start, 24h HH:MM (e.g. "06:00").
    time_from: Optional[str] = None
    time_to: Optional[str] = None

