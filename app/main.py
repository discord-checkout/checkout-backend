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
    description="AI 기반 패션 가이드 앱 — 대학생 옷장 솔루션",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(recommendations.router)
app.include_router(wardrobe.router)
app.include_router(items.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
