from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from .booking_service import auto_cancel_expired_bookings
from .database import get_db
from .models.booking import Booking, BookingStatus
from .schemas.booking import BookingRead, BookingActionResponse
from .schemas.user import UserRead


router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingRead])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
) -> list[Booking]:
    bookings = (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.tee_time.asc())
        .all()
    )
    return bookings


@router.post("/{booking_id}/accept", response_model=BookingActionResponse)
def accept_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
) -> BookingActionResponse:
    booking = db.query(Booking).get(booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.PENDING_USER_CONFIRM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is not pending confirmation")

    booking.status = BookingStatus.CONFIRMED
    db.commit()
    db.refresh(booking)
    return BookingActionResponse(booking=booking)


@router.post("/{booking_id}/decline", response_model=BookingActionResponse)
def decline_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: UserRead = Depends(get_current_user),
) -> BookingActionResponse:
    booking = db.query(Booking).get(booking_id)
    if not booking or booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.PENDING_USER_CONFIRM:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Booking is not pending confirmation")

    # In a later phase this should also invoke the course adapter's cancel_booking.
    booking.status = BookingStatus.CANCELLED_BY_USER
    db.commit()
    db.refresh(booking)
    return BookingActionResponse(booking=booking)


@router.post("/auto-cancel/run", response_model=list[BookingRead])
def run_auto_cancellation(
    db: Session = Depends(get_db),
) -> list[Booking]:
    """
    Trigger auto-cancellation for all expired pending bookings.

    This endpoint is intended to be invoked by a periodic job (e.g. cron or
    an external scheduler) every few minutes.
    """
    updated = list(auto_cancel_expired_bookings(db))
    db.commit()
    return updated

