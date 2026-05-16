from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegisterIn(BaseModel):
    email: EmailStr = Field(description="이메일 주소", examples=["user@example.com"])
    password: str = Field(description="비밀번호 (8자 이상 권장)", examples=["mypassword123"])
    nickname: str = Field(description="닉네임", examples=["멋쟁이"])


class UserLoginIn(BaseModel):
    email: EmailStr = Field(description="가입한 이메일 주소", examples=["user@example.com"])
    password: str = Field(description="비밀번호", examples=["mypassword123"])


class TokenOut(BaseModel):
    access_token: str = Field(description="JWT 액세스 토큰. 이후 모든 요청의 Authorization 헤더에 'Bearer {token}' 형식으로 포함하세요.")
    token_type: str = Field(default="bearer", description="토큰 타입 (항상 'bearer')")


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    nickname: str
    created_at: datetime

    model_config = {"from_attributes": True}
