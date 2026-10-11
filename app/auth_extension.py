"""Password hashing and JWT helpers."""

from datetime import UTC, datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.base.config import AuthConfig

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def _jwt_settings() -> tuple[str, str]:
    if not AuthConfig.JWT_SECRET or not AuthConfig.JWT_ALGORITHM:
        raise RuntimeError("SECRET_KEY and HASHING_ALGORITHM must be configured.")
    return AuthConfig.JWT_SECRET, AuthConfig.JWT_ALGORITHM


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    secret, algorithm = _jwt_settings()
    now = datetime.now(UTC)
    lifetime = (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRES_MINUTES)
    )
    expire = now + lifetime
    payload = {"sub": str(subject), "iat": now, "exp": expire}
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_token(token: str) -> dict:
    secret, algorithm = _jwt_settings()
    return jwt.decode(token, secret, algorithms=[algorithm])
