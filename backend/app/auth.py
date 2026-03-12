from datetime import datetime, timedelta
from typing import Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models.user import User, PriorityTier
from .schemas.user import Token, UserCreate, UserRead, TokenData
from .rate_limit import auth_rate_limiter

logger = logging.getLogger("auth")

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
# Use PBKDF2-SHA256 to avoid bcrypt's 72-byte password limit and backend quirks.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email=email)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        sub = payload.get("sub")
        user_id: int | None = int(sub) if isinstance(sub, str) and sub.isdigit() else None
        if user_id is None:
            logger.warning("auth.get_current_user: missing 'sub' in JWT payload")
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError as exc:
        logger.warning("auth.get_current_user: JWT decode failed: %s", exc)
        raise credentials_exception
    user = db.query(User).get(token_data.user_id)
    if user is None:
        logger.info("auth.get_current_user: user id %s not found", token_data.user_id)
        raise credentials_exception
    return user


@router.post("/register", response_model=UserRead, dependencies=[Depends(auth_rate_limiter())])
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = get_user_by_email(db, payload.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=payload.email,
        password_hash=get_password_hash(payload.password),
        priority_tier=PriorityTier.STANDARD,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/token", response_model=Token, dependencies=[Depends(auth_rate_limiter())])
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = create_access_token(data={"sub": str(user.id)})
    return Token(access_token=access_token)

