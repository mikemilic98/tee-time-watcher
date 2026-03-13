from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .database import SessionLocal, engine, Base
from .integrations import DemoCourseAdapter
from .models.booking import Booking, BookingStatus
from .models.course import Course
from .models.scan_job import ScanJob, ScanJobStatus
from .models.tee_time_candidate import TeeTimeCandidate
from .models.user_course_credential import UserCourseCredential
from .models.watch_rule import WatchRule
from .queue import dequeue_next_scan_job
from .security import DecryptedCourseCredentials, decrypt_credential_payload
from .config import settings


logger = logging.getLogger(__name__)


def _load_decrypted_credentials(creds: UserCourseCredential | None) -> DecryptedCourseCredentials | None:
    if creds is None:
        return None
    try:
        payload = decrypt_credential_payload(creds.credential_encrypted)
    except ValueError:
        logger.warning(
            "credential_decrypt_failed",
            extra={"user_id": creds.user_id, "course_id": creds.course_id},
        )
        return None
    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        logger.warning(
            "credential_payload_invalid",
            extra={"user_id": creds.user_id, "course_id": creds.course_id},
        )
        return None
    return DecryptedCourseCredentials(username=username, password=password)


def _process_single_job(db: Session, job_id: int) -> None:
    job: ScanJob | None = db.get(ScanJob, job_id)
    if not job:
        return
    job.status = ScanJobStatus.IN_PROGRESS
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    db.commit()

    try:
        rule: WatchRule | None = db.get(WatchRule, job.watch_rule_id)
        if not rule:
            job.status = ScanJobStatus.FAILED
            job.last_error = "WatchRule not found"
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return

        course: Course | None = db.get(Course, rule.course_id)
        if not course:
            job.status = ScanJobStatus.FAILED
            job.last_error = "Course not found"
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return

        adapter = DemoCourseAdapter(course_id=course.id)
        date_from = datetime.now(timezone.utc)
        date_to = date_from + timedelta(days=1)

        creds_row: UserCourseCredential | None = (
            db.query(UserCourseCredential)
            .filter(
                UserCourseCredential.user_id == rule.user_id,
                UserCourseCredential.course_id == course.id,
            )
            .first()
        )
        decrypted_creds = _load_decrypted_credentials(creds_row)

        for result in adapter.search_tee_times(
            date_from=date_from,
            date_to=date_to,
            time_from=None,
            time_to=None,
            num_players=rule.num_players,
        ):
            candidate = TeeTimeCandidate(
                watch_rule_id=rule.id,
                course_id=course.id,
                tee_time=result.tee_time,
                price=result.price_cents,
                num_players=result.num_players,
            )
            db.add(candidate)
            db.flush()

            # Normal path: require valid decrypted credentials and threshold
            created_booking = False
            if (
                decrypted_creds
                and creds_row
                and creds_row.can_auto_book_if_free
                and result.price_cents <= course.booking_fee_threshold
            ):
                try:
                    external_ref = adapter.book_tee_time(result.external_id, decrypted_creds)
                except Exception:
                    logger.exception(
                        "auto_booking_failed",
                        extra={
                            "job_id": job.id,
                            "watch_rule_id": rule.id,
                            "course_id": course.id,
                        },
                    )
                    booking = Booking(
                        user_id=rule.user_id,
                        course_id=course.id,
                        tee_time=result.tee_time,
                        price=result.price_cents,
                        num_players=result.num_players,
                        status=BookingStatus.FAILED,
                        auto_booked=True,
                    )
                    db.add(booking)
                else:
                    must_cancel_by = datetime.now(timezone.utc) + timedelta(
                        hours=max(course.cancellation_policy_hours_before - 1, 1)
                    )
                    booking = Booking(
                        user_id=rule.user_id,
                        course_id=course.id,
                        tee_time=result.tee_time,
                        price=result.price_cents,
                        num_players=result.num_players,
                        status=BookingStatus.PENDING_USER_CONFIRM,
                        external_reference=external_ref,
                        auto_booked=True,
                        must_cancel_by=must_cancel_by,
                    )
                    db.add(booking)
                    created_booking = True

            # Testing feature flag: if enabled, always create a pending booking
            # even when credentials/threshold conditions are not met.
            if settings.relaxed_worker_bookings and not created_booking:
                booking = Booking(
                    user_id=rule.user_id,
                    course_id=course.id,
                    tee_time=result.tee_time,
                    price=result.price_cents,
                    num_players=result.num_players,
                    status=BookingStatus.PENDING_USER_CONFIRM,
                    auto_booked=False,
                )
                db.add(booking)

        job.status = ScanJobStatus.DONE
    except Exception as exc:
        job_id_cur = job.id
        logger.exception("scan_job_failed", extra={"job_id": job_id_cur})
        db.rollback()
        job = db.get(ScanJob, job_id_cur)
        if job:
            job.status = ScanJobStatus.FAILED
            job.last_error = str(exc)
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
        return
    finally:
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()


def run_worker_once() -> bool:
    """
    Dequeue and process a single scan job.
    Returns True if a job was processed, False if the queue was empty.
    """
    payload = dequeue_next_scan_job()
    if not payload:
        return False
    job_id = payload.get("job_id")
    if job_id is None:
        logger.warning("Dequeued payload without job_id: %s", payload)
        return False
    try:
        job_id = int(job_id)
    except (TypeError, ValueError):
        logger.warning("Invalid job_id in payload: %s", payload)
        return False

    db: Session = SessionLocal()
    try:
        _process_single_job(db, job_id)
        return True
    finally:
        db.close()


def run_worker_forever(poll_interval_seconds: float = 1.0) -> None:
    """Poll Redis and process jobs until interrupted."""
    logger.info("Worker started with poll interval %.2f seconds", poll_interval_seconds)
    while True:
        had_job = run_worker_once()
        if not had_job:
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    Base.metadata.create_all(bind=engine)  # ensure all tables exist when run standalone
    run_worker_once()
