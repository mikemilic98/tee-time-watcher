from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import auth
from . import bookings
from . import notifications
from .config import settings
from .database import Base, engine
from .models.user import User
from .auth import get_current_user
from .schemas.user import UserRead
from .monitoring import setup_monitoring
from .routers import bookings, courses, notifications, watch_rules


def create_app() -> FastAPI:
    Base.metadata.create_all(bind=engine)

    app = FastAPI(title=settings.app_name, debug=settings.debug)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    setup_monitoring(app)

    app.include_router(auth.router)
    app.include_router(bookings.router)
    app.include_router(notifications.router)
    app.include_router(courses.router)
    app.include_router(watch_rules.router)

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    @app.get("/me", response_model=UserRead)
    def read_me(current_user: User = Depends(get_current_user)) -> UserRead:
        return UserRead.model_validate(current_user)

    return app


app = create_app()

