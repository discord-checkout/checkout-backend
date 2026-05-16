import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.item import Item
from app.models.style_profile import StyleProfile
from app.models.user import User
from app.models.wardrobe import WardrobeItem
from app.schemas.item import CombinationOut, FirstItemRecommendationOut, ItemOut
from app.services import ai

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/first-item", response_model=FirstItemRecommendationOut)
async def get_first_item(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FirstItemRecommendationOut:
    profile_result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스타일 진단을 먼저 완료해주세요.",
        )

    recommendation = await ai.recommend_first_item(profile)

    item = Item(
        id=uuid.uuid4(),
        name=recommendation["item_name"],
        brand=recommendation.get("brand"),
        price=recommendation["price"],
        category="top",
        tags=profile.style_tags,
        product_url=f"https://www.musinsa.com/search/goods?keyword={recommendation['item_name'].replace(' ', '+')}",
    )
    db.add(item)
    await db.flush()

    wardrobe_entry = WardrobeItem(
        user_id=current_user.id,
        item_id=item.id,
        month_added=1,
        is_first_item=True,
        combination_count=recommendation.get("combination_count", 3),
    )
    db.add(wardrobe_entry)
    await db.commit()
    await db.refresh(item)

    item_out = ItemOut(
        id=item.id,
        name=item.name,
        brand=item.brand,
        price=item.price,
        image_url=item.image_url,
        product_url=item.product_url,
        tags=item.tags,
    )
    combinations = [CombinationOut(**c) for c in recommendation.get("combinations", [])]

    return FirstItemRecommendationOut(
        item=item_out,
        reason=recommendation["reason"],
        combinations=combinations,
        combination_count=recommendation.get("combination_count", len(combinations)),
    )
