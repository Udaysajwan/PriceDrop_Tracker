import pytest
from fastapi.testclient import TestClient

from backend.app.database_firebase import get_firestore_db, MockFirestoreClient
from backend.app.repositories.user_repo import user_repo
from backend.app.repositories.product_repo import product_repo
from backend.app.services.auth_service import hash_password, create_access_token
from backend.app.main import app


@pytest.fixture(autouse=True)
def clean_firestore_db(monkeypatch):
    """Ensure tests always run against a fresh in-memory Mock Firestore instance."""
    import backend.app.database_firebase as db_fb
    mock_db = MockFirestoreClient()
    monkeypatch.setattr(db_fb, "_firestore_client", mock_db)
    monkeypatch.setattr(db_fb, "_is_mock_mode", True)
    monkeypatch.setattr(db_fb, "get_firestore_db", lambda: mock_db)
    monkeypatch.setattr(db_fb, "init_firestore", lambda: mock_db)
    monkeypatch.setattr("backend.app.main.init_firestore", lambda: mock_db)
    monkeypatch.setattr("backend.app.main.start_scheduler", lambda: None)
    monkeypatch.setattr("backend.app.main.stop_scheduler", lambda: None)
    yield mock_db


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user():
    user = user_repo.create(
        email="tester@example.com",
        display_name="Test User"
    )
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user["id"]), "email": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}
