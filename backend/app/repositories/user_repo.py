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

    def create(self, email: str, hashed_password: str) -> Dict[str, Any]:
        user_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()
        user_data = {
            "id": user_id,
            "email": email.strip().lower(),
            "hashed_password": hashed_password,
            "is_active": True,
            "created_at": now_str,
        }
        self.collection.document(user_id).set(user_data)
        return user_data


user_repo = UserRepository()
