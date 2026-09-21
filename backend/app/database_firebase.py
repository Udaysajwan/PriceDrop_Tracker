import os
import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from backend.app.config import settings

logger = logging.getLogger("price_tracker.firebase")

# ---------------------------------------------------------------------------
# In-Memory Mock Firestore for zero-credential local development and tests
# ---------------------------------------------------------------------------

class MockDocumentSnapshot:
    def __init__(self, doc_id: str, data: Optional[Dict[str, Any]], ref: Any):
        self.id = doc_id
        self._data = data.copy() if data is not None else None
        self.exists = data is not None
        self.reference = ref

    def to_dict(self) -> Optional[Dict[str, Any]]:
        return self._data.copy() if self._data is not None else None


class MockDocumentReference:
    def __init__(self, doc_id: str, collection_ref: 'MockCollectionReference'):
        self.id = doc_id
        self._collection = collection_ref

    def get(self) -> MockDocumentSnapshot:
        data = self._collection._store.get(self.id)
        return MockDocumentSnapshot(self.id, data, self)

    def set(self, data: Dict[str, Any], merge: bool = False):
        if merge and self.id in self._collection._store:
            self._collection._store[self.id].update(data)
        else:
            self._collection._store[self.id] = data.copy()

    def update(self, data: Dict[str, Any]):
        if self.id not in self._collection._store:
            raise KeyError(f"Document {self.id} does not exist")
        self._collection._store[self.id].update(data)

    def delete(self):
        if self.id in self._collection._store:
            del self._collection._store[self.id]

    def collection(self, sub_name: str) -> 'MockCollectionReference':
        key = f"{self.id}/{sub_name}"
        if key not in self._collection._subcollections:
            self._collection._subcollections[key] = MockCollectionReference(sub_name)
        return self._collection._subcollections[key]


class MockCollectionReference:
    def __init__(self, name: str):
        self.name = name
        self._store: Dict[str, Dict[str, Any]] = {}
        self._subcollections: Dict[str, 'MockCollectionReference'] = {}

    def document(self, doc_id: Optional[str] = None) -> MockDocumentReference:
        if not doc_id:
            doc_id = str(uuid.uuid4())
        return MockDocumentReference(doc_id, self)

    def where(self, field: str, op: str, value: Any) -> 'MockQuery':
        return MockQuery(self).where(field, op, value)

    def order_by(self, field: str, direction: str = "ASCENDING") -> 'MockQuery':
        return MockQuery(self).order_by(field, direction)

    def stream(self) -> List[MockDocumentSnapshot]:
        return [MockDocumentSnapshot(k, v, self.document(k)) for k, v in list(self._store.items())]


class MockQuery:
    def __init__(self, collection_ref: MockCollectionReference):
        self._collection = collection_ref
        self._filters: List[tuple] = []
        self._order_by: Optional[tuple] = None

    def where(self, field: str, op: str, value: Any) -> 'MockQuery':
        self._filters.append((field, op, value))
        return self

    def order_by(self, field: str, direction: str = "ASCENDING") -> 'MockQuery':
        self._order_by = (field, direction)
        return self

    def stream(self) -> List[MockDocumentSnapshot]:
        results = []
        for k, v in self._collection._store.items():
            match = True
            for field, op, val in self._filters:
                doc_val = v.get(field)
                if op == "==" and doc_val != val:
                    match = False
                    break
                elif op == "<=" and (doc_val is None or doc_val > val):
                    match = False
                    break
                elif op == ">=" and (doc_val is None or doc_val < val):
                    match = False
                    break
            if match:
                results.append(MockDocumentSnapshot(k, v, self._collection.document(k)))

        if self._order_by:
            field, direction = self._order_by
            reverse = direction.upper() in ["DESCENDING", "DESC"]
            results.sort(
                key=lambda doc: doc.to_dict().get(field) if doc.to_dict().get(field) is not None else "",
                reverse=reverse
            )
        return results


class MockFirestoreClient:
    def __init__(self):
        self._collections: Dict[str, MockCollectionReference] = {}

    def collection(self, name: str) -> MockCollectionReference:
        if name not in self._collections:
            self._collections[name] = MockCollectionReference(name)
        return self._collections[name]


# ---------------------------------------------------------------------------
# Firebase Client Initialization
# ---------------------------------------------------------------------------

_firestore_client = None
_is_mock_mode = False


def init_firestore():
    global _firestore_client, _is_mock_mode

    import json
    import firebase_admin
    from firebase_admin import credentials, firestore

    # Check for credentials in:
    # 1. FIREBASE_CREDENTIALS_JSON environment variable (standard for Render / Heroku)
    # 2. Local file at settings.FIREBASE_CREDENTIALS_PATH
    cred_json_env = os.environ.get("FIREBASE_CREDENTIALS_JSON") or os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    cred_path = settings.FIREBASE_CREDENTIALS_PATH
    abs_cred_path = os.path.abspath(cred_path) if not os.path.isabs(cred_path) else cred_path

    cred = None
    if cred_json_env:
        try:
            cred_dict = json.loads(cred_json_env)
            cred = credentials.Certificate(cred_dict)
            logger.info("Loaded Firebase credentials from environment variable.")
        except Exception as e:
            logger.warning(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
    elif os.path.exists(abs_cred_path):
        try:
            cred = credentials.Certificate(abs_cred_path)
            logger.info(f"Loaded Firebase credentials from {abs_cred_path}")
        except Exception as e:
            logger.warning(f"Failed to load credentials from {abs_cred_path}: {e}")

    if cred is not None:
        try:
            if not firebase_admin._apps:
                options = {}
                project_id = settings.FIREBASE_PROJECT_ID or "backend--api"
                options["projectId"] = project_id
                firebase_admin.initialize_app(cred, options)
                logger.info(f"Connected to live Firebase project: {project_id}")

            _firestore_client = firestore.client()
            _is_mock_mode = False
            logger.info("Cloud Firestore client initialized successfully.")
            return _firestore_client
        except Exception as e:
            logger.warning(f"Failed to initialize live Firebase Admin SDK ({e}). Falling back to in-memory Firestore.")

    # Even without a service account key, initialize default Firebase App with projectId
    # so firebase_admin.auth can verify Google ID tokens
    if not firebase_admin._apps:
        try:
            project_id = settings.FIREBASE_PROJECT_ID or "backend--api"
            firebase_admin.initialize_app(options={"projectId": project_id})
            logger.info(f"Initialized default Firebase Admin app for project: {project_id}")
        except Exception as e:
            logger.debug(f"Default Firebase Admin app initialization: {e}")

    logger.info("Using in-memory Mock Firestore Provider.")
    _firestore_client = MockFirestoreClient()
    _is_mock_mode = True
    return _firestore_client


def get_firestore_db():
    global _firestore_client
    if _firestore_client is None:
        init_firestore()
    return _firestore_client


def is_mock_firestore() -> bool:
    return _is_mock_mode
