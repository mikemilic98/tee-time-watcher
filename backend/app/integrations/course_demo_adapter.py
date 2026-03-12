from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from .base_course_adapter import BaseCourseAdapter, CourseCredentials, TeeTimeResult


class DemoCourseAdapter(BaseCourseAdapter):
    """
    Demo adapter that simulates tee times instead of real scraping.
    Replace this with a real Playwright/Selenium implementation for a concrete course.
    """

    def search_tee_times(
        self,
        date_from: datetime,
        date_to: datetime,
        time_from: str | None,
        time_to: str | None,
        num_players: int,
    ) -> Iterable[TeeTimeResult]:
        base = datetime.combine(date_from.date(), datetime.min.time()) + timedelta(hours=8)
        for i in range(3):
            yield TeeTimeResult(
                external_id=f"demo-{int(base.timestamp())}-{i}",
                tee_time=base + timedelta(minutes=30 * i),
                price_cents=5000,
                num_players=num_players,
            )

    def book_tee_time(self, tee_time_id: str, credentials: CourseCredentials) -> str:
        return f"booking-{tee_time_id}"

    def cancel_booking(self, booking_reference: str, credentials: CourseCredentials) -> None:
        return None

