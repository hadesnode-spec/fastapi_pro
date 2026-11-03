
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from redis import Redis, RedisError
from sqlalchemy.orm import Session

from app.database import get_db, get_redis
from app.models import User
from app.security import decode_access_token, is_jti_active


bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized(detail: str = "Not authenticated"):
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    client: Redis = Depends(get_redis),
) -> dict:

    if credentials is None:
        raise unauthorized()

    try:
        payload = decode_access_token(
            credentials.credentials
        )
    except jwt.PyJWTError:
        raise unauthorized("Invalid or expired access token")

    try:
        active = is_jti_active(
            client,
            payload["jti"]
        )

    except RedisError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )

    if not active:
        raise unauthorized("Token revoked or expired")

    return payload


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:

    try:
        user_id = int(payload["sub"])
    except (ValueError, TypeError):
        raise unauthorized("Invalid token")

    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if user is None or not user.is_active:
        raise unauthorized("User not found or inactive")

    return user
