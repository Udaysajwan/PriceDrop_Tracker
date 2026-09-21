def test_get_current_user_me(client, auth_headers, test_user):
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["email"] == test_user["email"]


def test_get_current_user_unauthorized(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert response.status_code == 401


def test_firebase_token_auto_provisions_user(client):
    # A new Firebase user connecting for the first time
    headers = {"Authorization": "Bearer mock-uid-newuser:newuser@firebase.com"}
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "mock-uid-newuser"
    assert data["email"] == "newuser@firebase.com"


def test_inactive_user_cannot_access(client, auth_headers, test_user):
    from backend.app.repositories.user_repo import user_repo
    # Mark user inactive in Firestore
    user_repo.collection.document(str(test_user["id"])).update({"is_active": False})
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == 401
