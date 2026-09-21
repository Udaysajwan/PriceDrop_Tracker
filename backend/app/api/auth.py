from typing import Dict, Any
from fastapi import APIRouter, Depends

from backend.app.schemas.user import UserResponse
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve profile details of the current authenticated Firebase user.
    Authenticates via Firebase ID token passed in 'Authorization: Bearer <token>'.
    """
    return current_user
