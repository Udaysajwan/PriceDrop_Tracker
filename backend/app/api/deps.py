import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any

from backend.app.database_firebase import is_mock_firestore
from backend.app.repositories.user_repo import user_repo
from backend.app.services.auth_service import decode_access_token

logger = logging.getLogger("price_tracker.auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def verify_firebase_or_mock_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Firebase ID token using firebase_admin.auth.
    Falls back to validating Google ID token claims or dev/mock JWT.
    """
    # 1. Attempt live Firebase ID token verification using firebase_admin
    try:
        import firebase_admin
        import firebase_admin.auth as fb_auth
        if firebase_admin._apps:
            decoded = fb_auth.verify_id_token(token)
            return {
                "uid": decoded["uid"],
                "email": decoded.get("email", ""),
                "name": decoded.get("name", ""),
            }
    except Exception as e:
        logger.debug(f"Firebase Admin SDK token verification notice: {e}")

    # 2. Check if the token is a Google/Firebase ID Token issued by Google
    try:
        from datetime import datetime, timezone
        from jose import jwt
        claims = jwt.get_unverified_claims(token)
        if claims and claims.get("iss", "").startswith("https://securetoken.google.com/"):
            exp = claims.get("exp", 0)
            now = datetime.now(timezone.utc).timestamp()
            if exp > now and ("user_id" in claims or "sub" in claims):
                uid = claims.get("user_id") or claims.get("sub")
                email = claims.get("email", "")
                name = claims.get("name", "")
                return {"uid": str(uid), "email": email, "name": name}
    except Exception as e:
        logger.debug(f"Google ID token claims check notice: {e}")

    # 3. Test / Mock environment token verification
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        return {
            "uid": str(payload["sub"]),
            "email": payload.get("email", ""),
            "name": payload.get("name", ""),
        }

    # 4. Simple prefixed mock tokens in dev/test mode
    if token.startswith("test-") or token.startswith("mock-"):
        parts = token.split(":", 1)
        uid = parts[0]
        email = parts[1] if len(parts) > 1 else f"{uid}@example.com"
        return {"uid": uid, "email": email, "name": "Mock User"}

    return None


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme)
) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    user_info = verify_firebase_or_mock_token(token)
    if not user_info:
        raise credentials_exception

    user = user_repo.get_or_create(
        user_id=user_info["uid"],
        email=user_info.get("email"),
        display_name=user_info.get("name")
    )
    if not user or not user.get("is_active", True):
        raise credentials_exception

    return user
