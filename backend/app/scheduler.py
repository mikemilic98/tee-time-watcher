from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.course import Course  # ensure Course is in SA registry for WatchRule relationship
from .models.user import User
from .models.watch_rule import WatchRule
from .queue import enqueue_scan_job


def _watch_rule_due(now: datetime, rule: WatchRule) -> bool:
    if not rule.active:
        return False
    if rule.created_at is None:
        return True
    last_time = rule.updated_at or rule.created_at
    # DB stores naive UTC; make aware so we can subtract from now (aware UTC)
    if last_time.tzinfo is None:
        last_time = last_time.replace(tzinfo=timezone.utc)
    return (now - last_time).total_seconds() >= rule.scan_interval_seconds


def run_scheduler_once() -> None:
    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()
    try:
        rules = db.query(WatchRule).all()
        for rule in rules:
            if not _watch_rule_due(now, rule):
                continue
            user: User | None = db.get(User, rule.user_id)
            if not user:
                continue
            enqueue_scan_job(db, rule, user.priority_tier)
    finally:
        db.close()


if __name__ == "__main__":
    run_scheduler_once()

