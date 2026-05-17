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
from app.schemas.item import ItemOut
from app.schemas.wardrobe import (
    RoadmapMonthOut,
    RoadmapOut,
    WardrobeAddIn,
    WardrobeAddOut,
    WardrobeItemOut,
    WardrobeOut,
)
from app.services import ai
from app.services.ai import BUDGET_MAX
from app.services.combination import calculate_combinations
from app.services.musinsa import search_first_product

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


async def _get_wardrobe_entries(user_id: uuid.UUID, db: AsyncSession) -> list[WardrobeItem]:
    result = await db.execute(
        select(WardrobeItem)
        .where(WardrobeItem.user_id == user_id)
        .options(selectinload(WardrobeItem.item))
    )
    return list(result.scalars().all())


@router.get("", response_model=WardrobeOut, summary="내 옷장 조회")
async def get_wardrobe(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WardrobeOut:
    """
    내 옷장에 추가된 아이템 목록과 전체 코디 조합 수를 반환합니다.
    """
    entries = await _get_wardrobe_entries(current_user.id, db)

    items_out = [
        WardrobeItemOut(
            id=e.id,
            item=ItemOut.model_validate(e.item),
            month_added=e.month_added,
            is_first_item=e.is_first_item,
            combination_count=e.combination_count,
        )
        for e in entries
    ]
    total = calculate_combinations([e.item for e in entries])
    return WardrobeOut(items=items_out, total_combination_count=total)


@router.post("/add", response_model=WardrobeAddOut, status_code=status.HTTP_201_CREATED,
             summary="아이템 옷장에 추가")
async def add_to_wardrobe(
    body: WardrobeAddIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WardrobeAddOut:
    """
    추천받은 아이템을 내 옷장에 추가합니다.

    - `item_id`: 추천 API 응답에서 받은 아이템 UUID
    - `delta`: 이 아이템 추가로 새로 생긴 코디 조합 수
    """
    item_result = await db.execute(select(Item).where(Item.id == body.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="상품을 찾을 수 없습니다.")

    existing_entries = await _get_wardrobe_entries(current_user.id, db)
    prev_total = calculate_combinations([e.item for e in existing_entries])

    new_total = calculate_combinations([e.item for e in existing_entries] + [item])
    delta = new_total - prev_total

    entry = WardrobeItem(
        user_id=current_user.id,
        item_id=item.id,
        month_added=len(existing_entries) + 1,
        is_first_item=False,
        combination_count=delta,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    return WardrobeAddOut(
        added_item=WardrobeItemOut(
            id=entry.id,
            item=ItemOut.model_validate(item),
            month_added=entry.month_added,
            is_first_item=entry.is_first_item,
            combination_count=delta,
        ),
        new_combination_count=new_total,
        delta=delta,
    )


@router.get("/roadmap", response_model=RoadmapOut, summary="3개월 로드맵 조회")
async def get_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapOut:
    """
    AI가 생성한 3개월 옷장 로드맵을 반환합니다.

    - 각 달마다 추천 아이템과 추가 시 예상 코디 조합 수를 제공합니다.
    - 추천 아이템의 `id`로 `/wardrobe/add`를 호출해 옷장에 추가할 수 있습니다.
    """
    profile_result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="스타일 진단을 먼저 완료해주세요."
        )

    existing_entries = await _get_wardrobe_entries(current_user.id, db)
    current_items = [{"name": e.item.name, "category": e.item.category} for e in existing_entries]

    months_data = await ai.generate_roadmap(profile, current_items)

    months_out: list[RoadmapMonthOut] = []
    for m in months_data:
        item_result = await db.execute(
            select(Item).where(Item.name == m["item_name"], Item.brand == m.get("brand"))
        )
        item = item_result.scalar_one_or_none()

        if not item:
            search_keyword = m.get("search_keyword") or m["item_name"]
            musinsa = await search_first_product(search_keyword)
            budget_max = BUDGET_MAX.get(profile.budget_range)
            musinsa_price = musinsa["price"] or 0 if musinsa else 0
            use_musinsa_price = musinsa and (budget_max is None or musinsa_price <= budget_max)
            item = Item(
                id=uuid.uuid4(),
                name=musinsa["name"] if musinsa else m["item_name"],
                brand=musinsa["brand"] if musinsa else m.get("brand"),
                price=musinsa_price if use_musinsa_price else m.get("price", 0),
                category=m.get("category", "top"),
                tags=[profile.style_mood],
                image_url=musinsa["image_url"] if musinsa else None,
                product_url=musinsa["product_url"] if musinsa else None,
            )
            db.add(item)
            await db.flush()

        months_out.append(
            RoadmapMonthOut(
                month=m["month"],
                recommended_item=ItemOut.model_validate(item),
                reason=m["reason"],
                projected_combination_count=m["projected_combination_count"],
            )
        )

    await db.commit()
    return RoadmapOut(months=months_out)
