from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..integrations import DemoCourseAdapter
from ..models.booking import Booking, BookingStatus
from ..models.course import Course
from ..models.user import User
from ..models.user_course_credential import UserCourseCredential

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=None)
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.tee_time.asc())
        .all()
    )


@router.post("/{booking_id}/accept", response_model=None)
def accept_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id, Booking.user_id == current_user.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.PENDING_USER_CONFIRM:
        raise HTTPException(status_code=400, detail="Booking is not pending confirmation")
    booking.status = BookingStatus.CONFIRMED
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.post("/{booking_id}/decline", response_model=None)
def decline_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id, Booking.user_id == current_user.id)
        .first()
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.PENDING_USER_CONFIRM:
        raise HTTPException(status_code=400, detail="Booking is not pending confirmation")

    course: Course | None = db.query(Course).get(booking.course_id)
    creds: UserCourseCredential | None = (
        db.query(UserCourseCredential)
        .filter(
            UserCourseCredential.user_id == current_user.id,
            UserCourseCredential.course_id == booking.course_id,
        )
        .first()
    )
    if course and creds and booking.external_reference:
        adapter = DemoCourseAdapter(course_id=course.id)
        adapter.cancel_booking(booking.external_reference, creds)  # type: ignore[arg-type]

    booking.status = BookingStatus.AUTO_CANCELLED
    booking.updated_at = datetime.now(timezone.utc)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking

