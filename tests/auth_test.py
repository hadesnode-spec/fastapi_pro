def test_login_success(client, user):
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, user):
    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "WrongPassword",
        },
    )

    assert response.status_code == 401


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "unknown@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 401


def test_login_inactive_user(client, user, db_session):
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 401


def test_login_invalid_email(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "invalid-email",
            "password": "Test@12345",
        },
    )

    assert response.status_code == 422


def test_refresh_token_rotation(client, user):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    new_tokens = refresh_response.json()

    assert new_tokens["access_token"]
    assert new_tokens["refresh_token"]
    assert new_tokens["refresh_token"] != old_refresh_token


def test_refresh_token_reuse_detection(client, user):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    old_refresh_token = login_response.json()["refresh_token"]

    refresh_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert refresh_response.status_code == 200

    new_refresh_token = refresh_response.json()["refresh_token"]

    reuse_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": old_refresh_token,
        },
    )

    assert reuse_response.status_code == 401

    new_token_response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": new_refresh_token,
        },
    )

    assert new_token_response.status_code == 401


def test_refresh_invalid_token(client):
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": "invalid-refresh-token",
        },
    )

    assert response.status_code == 401


def test_logout_success(client, user):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    tokens = login_response.json()

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
        },
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Logged out"


def test_logout_without_access_token(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "some-refresh-token",
        },
    )

    assert response.status_code == 401


def test_logout_revokes_access_token(client, user, product):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    tokens = login_response.json()

    headers = {
        "Authorization": f"Bearer {tokens['access_token']}",
    }

    logout_response = client.post(
        "/auth/logout",
        json={
            "refresh_token": tokens["refresh_token"],
        },
        headers=headers,
    )

    assert logout_response.status_code == 200

    product_response = client.get(
        f"/products/{product.id}",
        headers=headers,
    )

    assert product_response.status_code == 401