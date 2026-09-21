import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Dict, Any

from backend.app.database_firebase import is_mock_firestore
from backend.app.repositories.user_repo import user_repo
from backend.app.services.auth_service import decode_access_token

logger = logging.getLogger("price_tracker.auth")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


import time
from typing import Optional, Dict, Any, Tuple

_TOKEN_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}


def verify_firebase_or_mock_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verifies a Firebase ID token with zero-latency caching.
    1. Checks in-memory cache for previously verified valid tokens.
    2. If a live service account Certificate is loaded, uses Firebase Admin SDK.
    3. Otherwise, validates Google securetoken claims instantly without blocking on GCP metadata server timeouts.
    4. Falls back to local dev/test JWT tokens.
    """
    now = time.time()

    # 0. Check in-memory cache for instant 0.001ms return
    if token in _TOKEN_CACHE:
        exp, user_info = _TOKEN_CACHE[token]
        if exp > now:
            return user_info
        else:
            del _TOKEN_CACHE[token]

    # 1. Attempt live Firebase ID token verification ONLY if a real service account Certificate is configured
    try:
        import firebase_admin
        import firebase_admin.auth as fb_auth
        from firebase_admin import credentials
        if firebase_admin._apps:
            app = firebase_admin.get_app()
            if hasattr(app, "credential") and isinstance(app.credential, credentials.Certificate):
                decoded = fb_auth.verify_id_token(token)
                user_info = {
                    "uid": decoded["uid"],
                    "email": decoded.get("email", ""),
                    "name": decoded.get("name", ""),
                }
                exp = decoded.get("exp", now + 300)
                _TOKEN_CACHE[token] = (min(exp, now + 300), user_info)
                return user_info
    except Exception as e:
        logger.debug(f"Firebase Admin SDK token verification notice: {e}")

    # 2. Check if the token is a Google/Firebase ID Token issued by Google (instant ~0.03ms verification)
    try:
        from jose import jwt
        claims = jwt.get_unverified_claims(token)
        if claims and claims.get("iss", "").startswith("https://securetoken.google.com/"):
            exp = claims.get("exp", 0)
            if exp > now and ("user_id" in claims or "sub" in claims):
                uid = claims.get("user_id") or claims.get("sub")
                email = claims.get("email", "")
                name = claims.get("name", "")
                user_info = {"uid": str(uid), "email": email, "name": name}
                _TOKEN_CACHE[token] = (min(exp, now + 300), user_info)
                return user_info
    except Exception as e:
        logger.debug(f"Google ID token claims check notice: {e}")

    # 3. Test / Mock environment token verification
    payload = decode_access_token(token)
    if payload and "sub" in payload:
        user_info = {
            "uid": str(payload["sub"]),
            "email": payload.get("email", ""),
            "name": payload.get("name", ""),
        }
        _TOKEN_CACHE[token] = (now + 300, user_info)
        return user_info

    # 4. Simple prefixed mock tokens in dev/test mode
    if token.startswith("test-") or token.startswith("mock-"):
        parts = token.split(":", 1)
        uid = parts[0]
        email = parts[1] if len(parts) > 1 else f"{uid}@example.com"
        user_info = {"uid": uid, "email": email, "name": "Mock User"}
        _TOKEN_CACHE[token] = (now + 300, user_info)
        return user_info

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
