from sqlalchemy import Column, ForeignKey, Integer, LargeBinary, Boolean

from ..database import Base


class UserCourseCredential(Base):
    __tablename__ = "user_course_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)

    # Encrypted blob containing username/password or token for the course site
    credential_encrypted = Column(LargeBinary, nullable=False)

    can_auto_book_if_free = Column(Boolean, nullable=False, default=False)

