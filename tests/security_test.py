import jwt
import pytest

from app.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    store_jti,
    is_jti_active,
    revoke_jti,
)


def test_password_hashing():
    password = "Test@12345"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation():
    token, jti = create_access_token(1)

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["jti"] == jti
    assert payload["type"] == "access"


def test_invalid_access_token():
    with pytest.raises(jwt.PyJWTError):
        decode_access_token("invalid-token")


def test_refresh_token_generation():
    token1 = generate_refresh_token()
    token2 = generate_refresh_token()

    assert token1 != token2
    assert len(token1) > 40


def test_refresh_token_hashing():
    token = generate_refresh_token()

    hashed = hash_refresh_token(token)

    assert len(hashed) == 64
    assert hashed == hash_refresh_token(token)
    assert hashed != token


def test_jti_storage_and_revocation(fake_redis):
    jti = "test-jti"

    store_jti(fake_redis, jti, 1, 900)

    assert is_jti_active(fake_redis, jti) is True

    revoke_jti(fake_redis, jti)

    assert is_jti_active(fake_redis, jti) is False