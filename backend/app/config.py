from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    app_name: str = "Tee Time Watcher"
    debug: bool = True

    # Note: '@' in password must be URL-encoded as %40
    database_url: str = "postgresql+psycopg://mike:Mike2you%40@127.0.0.1:5432/tee_time_db"

    jwt_secret_key: str = "CHANGE_ME_SECRET"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    redis_url: str = "redis://localhost:6379/0"

    max_scans_per_minute_per_course: int = 60

    # Key used to encrypt course credential blobs.
    # In production this must be a strong, secret value provided via environment variables.
    credential_encryption_key: str = "CHANGE_ME_CREDENTIAL_KEY"

    # Testing flag: when true, the worker will create a booking for each
    # found tee time even if credentials are missing/bad.
    # Controlled via env var RELAXED_WORKER_BOOKINGS=1
    relaxed_worker_bookings: bool = True

    class Config:
        env_file = ".env"


settings = Settings()

