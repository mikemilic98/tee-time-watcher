from __future__ import annotations

import json
from datetime import datetime, timezone
import logging

import redis
from sqlalchemy.orm import Session

from .config import settings
from .models.scan_job import ScanJob, ScanJobStatus
from .models.user import PriorityTier
from .models.watch_rule import WatchRule


logger = logging.getLogger("tee_time_app")

SCAN_QUEUE_KEY = "scan_jobs"

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url)
        except Exception:
            logger.exception("failed_to_connect_redis", extra={"redis_url": settings.redis_url})
            raise
    return _redis_client


def _tier_to_numeric(tier: PriorityTier) -> int:
    if tier == PriorityTier.PLATINUM:
        return 1
    if tier == PriorityTier.PRIORITY:
        return 2
    return 3


def enqueue_scan_job(db: Session, watch_rule: WatchRule, tier: PriorityTier) -> ScanJob:
    job = ScanJob(
        watch_rule_id=watch_rule.id,
        scheduled_for=datetime.now(timezone.utc),
        priority_tier=tier,
        status=ScanJobStatus.PENDING,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    score = _tier_to_numeric(tier) * 1_000_000_000 + int(job.scheduled_for.timestamp())
    payload = {"job_id": job.id}
    try:
        get_redis().zadd(SCAN_QUEUE_KEY, {json.dumps(payload): score})
    except Exception:
        logger.exception("enqueue_scan_job_failed", extra={"job_id": job.id})
    return job


def dequeue_next_scan_job() -> dict | None:
    try:
        client = get_redis()
        items = client.zpopmin(SCAN_QUEUE_KEY, 1)
    except Exception:
        logger.exception("dequeue_scan_job_failed")
        return None
    if not items:
        return None
    value, _score = items[0]
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return None

