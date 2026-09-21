from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Union, Any


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(BaseModel):
    id: Union[str, int]
    email: Optional[str] = None
    display_name: Optional[str] = None
    is_active: bool = True
    created_at: Union[str, Any] = None

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
