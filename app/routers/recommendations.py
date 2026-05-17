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
from app.services.ai import BUDGET_MAX
from app.services.combination import calculate_combinations, calculate_wardrobe_combinations
from app.services.musinsa import search_first_product

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
    search_keyword = recommendation.get("search_keyword") or item_name
    brand = recommendation.get("brand", "")
    price = recommendation["price"]
    combinations = [CombinationOut(**c) for c in recommendation.get("combinations", [])]

    musinsa = await search_first_product(search_keyword)
    image_url = musinsa["image_url"] if musinsa else None
    product_url = musinsa["product_url"] if musinsa else None
    if musinsa:
        item_name = musinsa["name"] or item_name
        brand = musinsa["brand"] or brand
        budget_max = BUDGET_MAX.get(profile.budget_range)
        musinsa_price = musinsa["price"] or 0
        if budget_max is None or musinsa_price <= budget_max:
            price = musinsa_price or price

    # after_combination_count: 현재 옷장 + 추천 아이템 추가 시 조합 수
    wardrobe = dict(profile.current_wardrobe or {})
    wardrobe["top"] = list(wardrobe.get("top", [])) + [item_name]
    after_combination_count = calculate_wardrobe_combinations(wardrobe)

    if not existing_entry:
        item = Item(
            id=uuid.uuid4(),
            name=item_name,
            brand=brand,
            price=price,
            category="top",
            tags=[profile.style_mood],
            image_url=image_url,
            product_url=product_url,
        )
        db.add(item)
        await db.flush()

        db.add(WardrobeItem(
            user_id=current_user.id,
            item_id=item.id,
            month_added=1,
            is_first_item=True,
            combination_count=after_combination_count - current_combination_count,
        ))
        await db.commit()

    return FirstItemRecommendationOut(
        item_name=item_name,
        price=price,
        brand=brand,
        reason=recommendation["reason"],
        image_url=image_url,
        product_url=product_url,
        combinations=combinations,
        current_combination_count=current_combination_count,
        after_combination_count=after_combination_count,
    )
