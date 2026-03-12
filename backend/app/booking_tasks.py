from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .database import SessionLocal
from .integrations import DemoCourseAdapter
from .models.booking import Booking, BookingStatus
from .models.course import Course
from .models.user_course_credential import UserCourseCredential


def auto_cancel_expired_bookings_once() -> None:
    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()
    try:
        to_cancel = (
            db.query(Booking)
            .filter(
                Booking.status == BookingStatus.PENDING_USER_CONFIRM,
                Booking.must_cancel_by != None,  # noqa: E711
                Booking.must_cancel_by <= now,
            )
            .all()
        )
        for booking in to_cancel:
            course: Course | None = db.query(Course).get(booking.course_id)
            creds: UserCourseCredential | None = (
                db.query(UserCourseCredential)
                .filter(
                    UserCourseCredential.user_id == booking.user_id,
                    UserCourseCredential.course_id == booking.course_id,
                )
                .first()
            )
            if course and creds and booking.external_reference:
                adapter = DemoCourseAdapter(course_id=course.id)
                adapter.cancel_booking(booking.external_reference, creds)  # type: ignore[arg-type]
            booking.status = BookingStatus.AUTO_CANCELLED
            booking.updated_at = now
            db.add(booking)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    auto_cancel_expired_bookings_once()

