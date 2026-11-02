import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
import redis

from app.config import settings

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _password_hasher.verify(hashed, plain)
    except (VerificationError, InvalidHashError):
        return False



def create_access_token(user_id: int) -> tuple[str, str]:
    now = datetime.now(timezone.utc)
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "jti"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Wrong token type")
    return payload



def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def _key(jti: str) -> str:
    return f"access_jti:{jti}"


def store_jti(r: redis.Redis, jti: str, user_id: int, ttl_seconds: int) -> None:
    r.set(_key(jti), str(user_id), ex=ttl_seconds)


def is_jti_active(r: redis.Redis, jti: str) -> bool:
    return r.exists(_key(jti)) == 1


def revoke_jti(r: redis.Redis, jti: str) -> None:
    r.delete(_key(jti))