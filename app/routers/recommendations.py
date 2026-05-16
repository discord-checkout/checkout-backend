from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.item import Item
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.schemas.item import CombinationOut, FirstItemRecommendationOut
from app.services import ai
from app.services.combination import calculate_combinations, calculate_wardrobe_combinations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/first-item", response_model=FirstItemRecommendationOut, summary="첫 번째 아이템 추천")
async def get_first_item(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FirstItemRecommendationOut:
    """
    스타일 프로필 기반으로 옷장의 첫 번째 아이템을 AI가 추천합니다.

    - 온보딩(`/onboarding/diagnose`) 완료 후 호출하세요.
    - 여러 번 호출해도 동일한 아이템을 반환합니다. (멱등성 보장)
    - `search_url`로 무신사에서 바로 해당 상품을 검색할 수 있습니다.
    - `current_combination_count` → `after_combination_count`: 이 아이템 추가 전후 코디 수 변화
    """
    profile_result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스타일 진단을 먼저 완료해주세요.",
        )

    current_combination_count = calculate_wardrobe_combinations(profile.current_wardrobe or {})

    existing_result = await db.execute(
        select(WardrobeItem)
        .where(WardrobeItem.user_id == current_user.id, WardrobeItem.is_first_item == True)  # noqa: E712
        .options(selectinload(WardrobeItem.item))
    )
    existing_entry = existing_result.scalar_one_or_none()

    recommendation = await ai.recommend_first_item(profile)
    item_name = recommendation["item_name"]
    brand = recommendation.get("brand", "")
    price = recommendation["price"]
    search_url = f"https://www.musinsa.com/search/goods?keyword={item_name.replace(' ', '+')}"
    combinations = [CombinationOut(**c) for c in recommendation.get("combinations", [])]

    if existing_entry:
        wardrobe_entries_result = await db.execute(
            select(WardrobeItem)
            .where(WardrobeItem.user_id == current_user.id)
            .options(selectinload(WardrobeItem.item))
        )
        all_items = [e.item for e in wardrobe_entries_result.scalars().all()]
        after_combination_count = calculate_combinations(all_items)
    else:
        item = Item(
            id=uuid.uuid4(),
            name=item_name,
            brand=brand,
            price=price,
            category="top",
            tags=[profile.style_mood],
            product_url=search_url,
        )
        db.add(item)
        await db.flush()

        wardrobe_entry = WardrobeItem(
            user_id=current_user.id,
            item_id=item.id,
            month_added=1,
            is_first_item=True,
            combination_count=0,
        )
        db.add(wardrobe_entry)
        await db.commit()

        wardrobe_entries_result = await db.execute(
            select(WardrobeItem)
            .where(WardrobeItem.user_id == current_user.id)
            .options(selectinload(WardrobeItem.item))
        )
        all_items = [e.item for e in wardrobe_entries_result.scalars().all()]
        after_combination_count = calculate_combinations(all_items)

    return FirstItemRecommendationOut(
        item_name=item_name,
        price=price,
        brand=brand,
        reason=recommendation["reason"],
        search_url=search_url,
        combinations=combinations,
        current_combination_count=current_combination_count,
        after_combination_count=after_combination_count,
    )
