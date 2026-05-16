from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app.routers import auth, items, onboarding, recommendations, wardrobe


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="CheckOut API",
    description="""
## CheckOut — AI 기반 패션 가이드 앱 백엔드

옷장이 빈 대학생을 위한 **스타일 진단 → 핀셋 추천 → 단계별 로드맵** 3단계 서비스입니다.

---

### 사용 흐름

1. **회원가입 / 로그인** — `access_token` 발급
2. **Authorize 버튼** 클릭 → `Bearer {access_token}` 입력 (이후 인증 자동 처리)
3. **온보딩** — 스타일 진단 후 프로필 생성
4. **첫 아이템 추천** — AI가 옷장의 출발점 아이템 추천
5. **옷장 관리** — 아이템 추가, 로드맵 확인

---

### 인증 방법

모든 `/onboarding`, `/recommendations`, `/wardrobe` 엔드포인트는 **Bearer 토큰** 필요합니다.

로그인 후 받은 `access_token`을 우측 상단 **Authorize** 버튼에 입력하세요.
""",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "회원가입 및 로그인. 발급된 `access_token`을 Authorize에 입력하세요."},
        {"name": "onboarding", "description": "스타일 진단. 로그인 후 최초 1회 진행합니다."},
        {"name": "recommendations", "description": "AI 기반 첫 번째 아이템 핀셋 추천."},
        {"name": "wardrobe", "description": "옷장 관리 및 월별 로드맵 조회."},
        {"name": "items", "description": "아이템 상세 정보 조회."},
    ],
)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(recommendations.router)
app.include_router(wardrobe.router)
app.include_router(items.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
