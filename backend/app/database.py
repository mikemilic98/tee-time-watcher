from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(settings.database_url, echo=settings.debug, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

