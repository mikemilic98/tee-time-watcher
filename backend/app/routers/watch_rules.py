from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models.watch_rule import WatchRule
from ..models.user import User
from ..schemas.watch_rule import WatchRuleCreate

router = APIRouter(prefix="/watch-rules", tags=["watch-rules"])


@router.get("", response_model=None)
def list_watch_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(WatchRule).filter(WatchRule.user_id == current_user.id).all()


@router.post("", response_model=None)
def create_watch_rule(
    payload: WatchRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Resolve day-of-week preferences into stored comma-separated string.
    days_str: str | None = None
    if payload.days_of_week:
        days_str = ",".join(payload.days_of_week)
    elif payload.weekends_only:
        days_str = "SAT,SUN"
    elif payload.weekdays_only:
        days_str = "MON,TUE,WED,THU,FRI"

    time_range: str | None = None
    if payload.time_from and payload.time_to:
        time_range = f"{payload.time_from}:{payload.time_to}"

    rule = WatchRule(
        user_id=current_user.id,
        course_id=payload.course_id,
        days_of_week=days_str,
        date_range=None,
        time_range=time_range,
        num_players=payload.num_players,
        max_price=payload.max_price,
        scan_interval_seconds=payload.scan_interval_seconds,
        active=payload.active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def delete_watch_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    rule = db.query(WatchRule).filter(WatchRule.id == rule_id, WatchRule.user_id == current_user.id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Watch rule not found")
    db.delete(rule)
    db.commit()
    return {"ok": True}

