def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "SecurePassword123!"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/auth/register",
        json={"email": test_user["email"], "password": "AnotherPassword123!"}
    )
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]


def test_login_json(client, test_user):
    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": "Password123!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client, test_user):
    response = client.post(
        "/auth/login",
        json={"email": test_user["email"], "password": "WrongPassword!"}
    )
    assert response.status_code == 401


def test_get_current_user_me(client, auth_headers, test_user):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]


def test_get_current_user_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401
