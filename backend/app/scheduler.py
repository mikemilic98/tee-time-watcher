from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from .database import SessionLocal
from .models.user import User
from .models.watch_rule import WatchRule
from .queue import enqueue_scan_job


def _watch_rule_due(now: datetime, rule: WatchRule) -> bool:
    if not rule.active:
        return False
    if rule.created_at is None:
        return True
    last_time = rule.updated_at or rule.created_at
    return (now - last_time).total_seconds() >= rule.scan_interval_seconds


def run_scheduler_once() -> None:
    now = datetime.now(timezone.utc)
    db: Session = SessionLocal()
    try:
        rules = db.query(WatchRule).all()
        for rule in rules:
            if not _watch_rule_due(now, rule):
                continue
            user: User | None = db.query(User).get(rule.user_id)
            if not user:
                continue
            enqueue_scan_job(db, rule, user.priority_tier)
    finally:
        db.close()


if __name__ == "__main__":
    run_scheduler_once()

