import pytest
from fastapi.testclient import TestClient

from backend.app.database_firebase import get_firestore_db, MockFirestoreClient
from backend.app.repositories.user_repo import user_repo
from backend.app.repositories.product_repo import product_repo
from backend.app.services.auth_service import hash_password, create_access_token
from backend.app.main import app


@pytest.fixture(autouse=True)
def clean_firestore_db():
    """Clear in-memory Firestore collections before each test run."""
    db = get_firestore_db()
    if isinstance(db, MockFirestoreClient):
        db._collections.clear()
    yield


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def test_user():
    user = user_repo.create(
        email="tester@example.com",
        hashed_password=hash_password("Password123!")
    )
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user["id"]), "email": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}
