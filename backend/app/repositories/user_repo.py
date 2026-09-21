import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.app.database_firebase import get_firestore_db


class UserRepository:
    def __init__(self):
        pass

    @property
    def collection(self):
        return get_firestore_db().collection("users")

    def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        doc = self.collection.document(str(user_id)).get()
        if not doc.exists:
            return None
        data = doc.to_dict()
        data["id"] = doc.id
        return data

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        docs = list(self.collection.where("email", "==", email.strip().lower()).stream())
        if not docs:
            return None
        data = docs[0].to_dict()
        data["id"] = docs[0].id
        return data

    def create(self, email: str, hashed_password: Optional[str] = None, user_id: Optional[str] = None, display_name: Optional[str] = None) -> Dict[str, Any]:
        uid = str(user_id) if user_id else str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        user_data = {
            "id": uid,
            "email": email.strip().lower() if email else None,
            "display_name": display_name,
            "is_active": True,
            "created_at": now_str,
        }
        if hashed_password:
            user_data["hashed_password"] = hashed_password
        self.collection.document(uid).set(user_data)
        return user_data

    def get_or_create(self, user_id: str, email: Optional[str] = None, display_name: Optional[str] = None) -> Dict[str, Any]:
        existing = self.get_by_id(str(user_id))
        if existing:
            return existing
        return self.create(email=email or "", user_id=user_id, display_name=display_name)


user_repo = UserRepository()
