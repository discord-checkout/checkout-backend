from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.schemas.style_profile import OnboardingIn, OnboardingOut
from app.services import ai

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/diagnose", response_model=OnboardingOut, status_code=status.HTTP_201_CREATED)
async def diagnose(
    body: OnboardingIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingOut:
    result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="이미 스타일 진단이 완료되었습니다."
        )

    style_tags, profile_summary = await ai.classify_style(
        body.liked_style_cards, body.disliked_style_cards
    )

    profile = StyleProfile(
        user_id=current_user.id,
        style_tags=style_tags,
        body_type=body.body_type,
        budget_monthly=body.budget_monthly,
        lifestyle=body.lifestyle,
        profile_summary=profile_summary,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return OnboardingOut(
        style_tags=style_tags,
        profile_summary=profile_summary,
        profile_id=profile.id,
    )
