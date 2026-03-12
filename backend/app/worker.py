from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.scan_job import ScanJob, ScanJobStatus
from .models.watch_rule import WatchRule
from .queue import dequeue_next_scan_job


logger = logging.getLogger(__name__)


def _get_db() -> Session:
    return SessionLocal()


def _load_scan_job(db: Session, job_id: int) -> Optional[ScanJob]:
    return db.query(ScanJob).get(job_id)


def _process_scan_job(db: Session, job: ScanJob) -> None:
    job.status = ScanJobStatus.IN_PROGRESS
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    db.commit()

    try:
        rule: WatchRule | None = db.query(WatchRule).get(job.watch_rule_id)
        if not rule or not rule.active:
            job.status = ScanJobStatus.DONE
            job.finished_at = datetime.now(timezone.utc)
            db.add(job)
            db.commit()
            return

        # TODO: Integrate with real course adapters and scraping/booking flows.
        logger.info("Processed placeholder scan job %s for watch rule %s", job.id, job.watch_rule_id)

        job.status = ScanJobStatus.DONE
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.exception("Error while processing scan job %s: %s", job.id, exc)
        job.status = ScanJobStatus.FAILED
        job.finished_at = datetime.now(timezone.utc)
        job.last_error = str(exc)
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

    db = _get_db()
    try:
        job = _load_scan_job(db, int(job_id))
        if not job:
            logger.warning("ScanJob %s not found in database", job_id)
            return True
        _process_scan_job(db, job)
        return True
    finally:
        db.close()


def run_worker_forever(poll_interval_seconds: float = 1.0) -> None:
    """
    Run a simple loop that continuously polls Redis for scan jobs.
    """
    logger.info("Worker started with poll interval %.2f seconds", poll_interval_seconds)
    while True:
        had_job = run_worker_once()
        if not had_job:
            time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_worker_forever()

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy.orm import Session

from .database import SessionLocal
from .integrations import DemoCourseAdapter
from .models.booking import Booking, BookingStatus
from .models.course import Course
from .models.scan_job import ScanJob, ScanJobStatus
from .models.tee_time_candidate import TeeTimeCandidate
from .models.user_course_credential import UserCourseCredential
from .models.watch_rule import WatchRule
from .queue import dequeue_next_scan_job
from .security import DecryptedCourseCredentials, decrypt_credential_payload


logger = logging.getLogger("tee_time_app")


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
    job: ScanJob | None = db.query(ScanJob).get(job_id)
    if not job:
        return
    job.status = ScanJobStatus.IN_PROGRESS
    job.started_at = datetime.now(timezone.utc)
    db.add(job)
    db.commit()

    try:
        rule: WatchRule | None = db.query(WatchRule).get(job.watch_rule_id)
        if not rule:
            job.status = ScanJobStatus.FAILED
            job.last_error = "WatchRule not found"
            return

        course: Course | None = db.query(Course).get(rule.course_id)
        if not course:
            job.status = ScanJobStatus.FAILED
            job.last_error = "Course not found"
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
                    continue

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

        job.status = ScanJobStatus.DONE
    except Exception as exc:
        logger.exception("scan_job_failed", extra={"job_id": job.id})
        job.status = ScanJobStatus.FAILED
        job.last_error = str(exc)
    finally:
        job.finished_at = datetime.now(timezone.utc)
        db.add(job)
        db.commit()


def run_worker_once() -> None:
    payload = dequeue_next_scan_job()
    if not payload:
        return
    job_id = payload.get("job_id")
    if not isinstance(job_id, int):
        return
    db: Session = SessionLocal()
    try:
        _process_single_job(db, job_id)
    finally:
        db.close()


if __name__ == "__main__":
    run_worker_once()

