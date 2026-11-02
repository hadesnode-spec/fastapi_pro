from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import redis
from app.database import get_db, get_redis
from app.config import settings
from app.database import get_db
from app.dependencies import get_token_payload
from app.models import RefreshToken, User
from app.schemas import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.security import (
    create_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
    revoke_jti,
    store_jti,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
    )


def issue_tokens(db: Session, r: redis.Redis, user: User) -> TokenResponse:
    access_token, jti = create_access_token(user.id)

    store_jti(r, jti, user.id, ttl_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    raw_refresh = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    user = db.query(User).filter(User.email == data.email).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise invalid_credentials()
    if not user.is_active:
        raise invalid_credentials()

    tokens = issue_tokens(db, r, user)
    db.commit()
    return tokens


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest, db: Session = Depends(get_db), r: redis.Redis = Depends(get_redis)):
    token_hash = hash_refresh_token(data.refresh_token)
    now = datetime.now(timezone.utc)

    r: redis.Redis = Depends(get_redis)
    stored = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    if stored is None:
        raise invalid_credentials()

    if stored.revoked_at is not None:
        db.query(RefreshToken).filter(
            RefreshToken.user_id == stored.user_id,
            RefreshToken.revoked_at.is_(None),
        ).update({"revoked_at": now})
        db.commit()
        raise invalid_credentials()

    if stored.expires_at <= now:
        raise invalid_credentials()

    user = db.query(User).filter(User.id == stored.user_id).first()
    if user is None or not user.is_active:
        raise invalid_credentials()

    stored.revoked_at = now
    r: redis.Redis = Depends(get_redis)
    tokens = issue_tokens(db, r, user)
    db.commit()
    return tokens


@router.post("/logout")
def logout(
    data: LogoutRequest,
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
):

    r: redis.Redis = Depends(get_redis)
    stored = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == hash_refresh_token(data.refresh_token),
            RefreshToken.user_id == int(payload["sub"]),
            RefreshToken.revoked_at.is_(None),
        )
        .first()
    )
    if stored is not None:
        stored.revoked_at = datetime.now(timezone.utc)
        db.commit()

    return {"detail": "Logged out"}