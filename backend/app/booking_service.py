from __future__ import annotations

from datetime import datetime, timedelta
from typing import Iterable

from sqlalchemy.orm import Session

from .models.booking import Booking, BookingStatus
from .models.notification import InAppNotification
from .models.course import Course


def compute_must_cancel_by(course: Course, tee_time: datetime) -> datetime:
    """
    Compute the latest time we should cancel a booking so that we are at least
    one hour ahead of the course cancellation policy.
    """
    hours_before = max(course.cancellation_policy_hours_before - 1, 0)
    return tee_time - timedelta(hours=hours_before)


def create_booking_with_notification(
    db: Session,
    *,
    user_id: int,
    course: Course,
    tee_time: datetime,
    price: int | None,
    num_players: int,
    external_reference: str | None,
    auto_booked: bool,
) -> Booking:
    """
    Create a Booking row and a corresponding InAppNotification in a single
    transactional unit. Caller is responsible for committing.
    """
    must_cancel_by = compute_must_cancel_by(course, tee_time)

    booking = Booking(
        user_id=user_id,
        course_id=course.id,
        tee_time=tee_time,
        price=price,
        num_players=num_players,
        status=BookingStatus.PENDING_USER_CONFIRM,
        external_reference=external_reference,
        auto_booked=auto_booked,
        must_cancel_by=must_cancel_by,
    )
    db.add(booking)
    db.flush()

    notification = InAppNotification(
        user_id=user_id,
        type="BOOKING_CREATED",
        payload_json=str(
            {
                "booking_id": booking.id,
                "course_id": booking.course_id,
                "tee_time": booking.tee_time.isoformat(),
                "price": booking.price,
                "num_players": booking.num_players,
            }
        ),
    )
    db.add(notification)

    return booking


def _cancel_on_course_if_possible(external_reference: str | None) -> None:
    """
    Placeholder for integration with course adapters.

    Once course-specific adapters are implemented, this function should look
    up the appropriate adapter and user credentials and invoke
    adapter.cancel_booking(external_reference, credentials).
    """
    if not external_reference:
        return
    # Integration hook for future implementation.


def auto_cancel_expired_bookings(db: Session, *, now: datetime | None = None) -> Iterable[Booking]:
    """
    Find all PENDING_USER_CONFIRM bookings whose must_cancel_by has passed,
    cancel them on the external course if possible, and mark them as
    AUTO_CANCELLED. Returns the updated bookings.
    """
    if now is None:
        now = datetime.utcnow()

    pending = (
        db.query(Booking)
        .filter(
            Booking.status == BookingStatus.PENDING_USER_CONFIRM,
            Booking.must_cancel_by != None,  # noqa: E711
            Booking.must_cancel_by <= now,
        )
        .all()
    )

    updated: list[Booking] = []
    for booking in pending:
        _cancel_on_course_if_possible(booking.external_reference)
        booking.status = BookingStatus.AUTO_CANCELLED
        updated.append(booking)

        notification = InAppNotification(
            user_id=booking.user_id,
            type="BOOKING_AUTO_CANCELLED",
            payload_json=str(
                {
                    "booking_id": booking.id,
                    "course_id": booking.course_id,
                    "tee_time": booking.tee_time.isoformat(),
                }
            ),
        )
        db.add(notification)

    return updated

