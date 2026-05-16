from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User


async def get_current_user(
    x_user_id: str = Header(
        ...,
        description=(
            "클라이언트가 생성한 고유 사용자 UUID. "
            "앱 최초 실행 시 UUID를 생성해 로컬에 저장하고 모든 요청에 포함하세요. "
            "예: 550e8400-e29b-41d4-a716-446655440000"
        ),
    ),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        user_id = uuid.UUID(x_user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-User-ID가 올바른 UUID 형식이 아닙니다.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(id=user_id, nickname="사용자")
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return user
