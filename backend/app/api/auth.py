from datetime import timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from backend.app.repositories.user_repo import user_repo
from backend.app.schemas.user import UserCreate, UserResponse, Token
from backend.app.services.auth_service import hash_password, verify_password, create_access_token
from backend.app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate):
    """Register a new user account in Firestore."""
    existing_user = user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )

    user = user_repo.create(
        email=user_in.email,
        hashed_password=hash_password(user_in.password)
    )
    return user


@router.post("/login", response_model=Token)
def login_json(body: LoginRequest):
    """Log in with JSON payload (used by Frontend fetch)."""
    user = user_repo.get_by_email(body.email)
    if not user or not verify_password(body.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user account")

    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": user["email"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 compatible token login for Swagger UI documentation (/docs)."""
    user = user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": str(user["id"]), "email": user["email"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retrieve details of current authenticated user from Firestore."""
    return current_user
