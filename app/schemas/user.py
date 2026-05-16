import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRegisterIn(BaseModel):
    email: EmailStr
    password: str
    nickname: str


class UserLoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    nickname: str
    created_at: datetime

    model_config = {"from_attributes": True}
