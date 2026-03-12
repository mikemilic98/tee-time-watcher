from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.course import Course

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=None)
def list_courses(db: Session = Depends(get_db)):
    return db.query(Course).filter(Course.is_active.is_(True)).all()

