from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.schemas.style_profile import OnboardingIn, OnboardingOut
from app.services import ai
from app.services.combination import calculate_wardrobe_combinations

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("/diagnose", response_model=OnboardingOut, summary="스타일 진단")
async def diagnose(
    body: OnboardingIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OnboardingOut:
    """
    스타일 진단을 진행하고 프로필을 생성합니다. 이미 진단한 경우 재진단(덮어쓰기)합니다.

    - `style_mood`: 선호 스타일 무드 (minimal / casual / dandy / sports / vintage / street)
    - `fit_preference`: 선호 핏 (slim / regular / overfit)
    - `lifestyle`: 생활 패턴 (campus / office / daily / freelance)
    - `budget_range`: 월 예산 (under_5 / 5_to_10 / 10_to_15 / 15_to_20 / over_20)
    - `current_wardrobe`: 현재 보유 옷장. 없는 카테고리는 빈 배열 `[]`로 전송

    응답의 `current_combination_count`는 현재 옷장으로 만들 수 있는 코디 수입니다.
    """
    result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()

    profile_summary = await ai.generate_profile_summary(
        body.style_mood, body.lifestyle, body.budget_range
    )
    wardrobe_dict = body.current_wardrobe.model_dump()
    current_combination_count = calculate_wardrobe_combinations(wardrobe_dict)

    if existing:
        await db.execute(delete(WardrobeItem).where(WardrobeItem.user_id == current_user.id))
        existing.style_mood = body.style_mood
        existing.fit_preference = body.fit_preference
        existing.lifestyle = body.lifestyle
        existing.budget_range = body.budget_range
        existing.current_wardrobe = wardrobe_dict
        existing.profile_summary = profile_summary
        await db.commit()
        await db.refresh(existing)
        profile = existing
    else:
        profile = StyleProfile(
            user_id=current_user.id,
            style_mood=body.style_mood,
            fit_preference=body.fit_preference,
            lifestyle=body.lifestyle,
            budget_range=body.budget_range,
            current_wardrobe=wardrobe_dict,
            profile_summary=profile_summary,
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    return OnboardingOut(
        profile_id=profile.id,
        profile_summary=profile_summary,
        current_combination_count=current_combination_count,
        style_mood=body.style_mood,
    )
