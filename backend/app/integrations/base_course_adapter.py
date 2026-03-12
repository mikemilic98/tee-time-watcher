from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Protocol


@dataclass
class TeeTimeResult:
    external_id: str
    tee_time: datetime
    price_cents: int
    num_players: int


class CourseCredentials(Protocol):
    username: str
    password: str


class BaseCourseAdapter(ABC):
    course_id: int

    def __init__(self, course_id: int) -> None:
        self.course_id = course_id

    @abstractmethod
    def search_tee_times(
        self,
        date_from: datetime,
        date_to: datetime,
        time_from: str | None,
        time_to: str | None,
        num_players: int,
    ) -> Iterable[TeeTimeResult]:
        raise NotImplementedError

    @abstractmethod
    def book_tee_time(self, tee_time_id: str, credentials: CourseCredentials) -> str:
        """Return external booking reference on success."""
        raise NotImplementedError

    @abstractmethod
    def cancel_booking(self, booking_reference: str, credentials: CourseCredentials) -> None:
        raise NotImplementedError

