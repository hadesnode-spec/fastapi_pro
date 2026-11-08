def test_get_product_success(client, user, product):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        f"/products/{product.id}",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == product.id
    assert data["name"] == "Laptop"
    assert data["description"] == "Test laptop"


def test_get_product_without_token(client, product):
    response = client.get(f"/products/{product.id}")

    assert response.status_code == 401


def test_get_nonexistent_product(client, user):
    login_response = client.post(
        "/auth/login",
        json={
            "email": "test@example.com",
            "password": "Test@12345",
        },
    )

    access_token = login_response.json()["access_token"]

    response = client.get(
        "/products/99999",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert response.status_code == 404


def test_get_product_with_invalid_token(client, product):
    response = client.get(
        f"/products/{product.id}",
        headers={
            "Authorization": "Bearer invalid-token",
        },
    )

    assert response.status_code == 401