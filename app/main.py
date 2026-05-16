from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.database import Base, engine
from app.routers import items, onboarding, recommendations, wardrobe


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

### 인증 방법 (로그인 없음)

모든 요청에 `X-User-ID` 헤더를 포함하세요.

**프론트엔드 구현 방법:**
```js
// 앱 최초 실행 시 UUID 생성 후 로컬 저장
const userId = localStorage.getItem('user_id') || crypto.randomUUID();
localStorage.setItem('user_id', userId);

// 모든 요청에 헤더 포함
headers: { 'X-User-ID': userId }
```

Swagger에서 테스트하려면 우측 상단 **Authorize** 버튼 → `X-User-ID` 란에 UUID 입력.

---

### 사용 흐름

1. **온보딩** — 스타일 진단 (`X-User-ID` 헤더 필수)
2. **첫 아이템 추천** — AI가 옷장의 출발점 아이템 추천
3. **옷장 관리** — 아이템 추가, 로드맵 확인
""",
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "onboarding", "description": "스타일 진단. 최초 1회 진행합니다."},
        {"name": "recommendations", "description": "AI 기반 첫 번째 아이템 핀셋 추천."},
        {"name": "wardrobe", "description": "옷장 관리 및 월별 로드맵 조회."},
        {"name": "items", "description": "아이템 상세 정보 조회."},
    ],
)

app.include_router(onboarding.router)
app.include_router(recommendations.router)
app.include_router(wardrobe.router)
app.include_router(items.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
