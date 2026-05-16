from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import TokenOut, UserLoginIn, UserRegisterIn

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED,
             summary="회원가입")
async def register(body: UserRegisterIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """
    회원가입 후 즉시 `access_token`을 반환합니다.

    - 반환된 `access_token`을 우측 상단 **Authorize** 버튼에 입력하면 이후 API를 바로 사용할 수 있습니다.
    - 이미 가입된 이메일이면 `409` 에러를 반환합니다.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 사용 중인 이메일입니다.")

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        nickname=body.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(str(user.id))
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut, summary="로그인")
async def login(body: UserLoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """
    로그인 후 `access_token`을 반환합니다.

    - 반환된 `access_token`을 우측 상단 **Authorize** 버튼에 입력하세요.
    - 이메일 또는 비밀번호가 틀리면 `401` 에러를 반환합니다.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다."
        )

    token = create_access_token(str(user.id))
    return TokenOut(access_token=token)
