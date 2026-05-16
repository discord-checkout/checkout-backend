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

router = APIRouter(prefix="/wardrobe", tags=["wardrobe"])


@router.get("", response_model=WardrobeOut)
async def get_wardrobe(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WardrobeOut:
    result = await db.execute(
        select(WardrobeItem)
        .where(WardrobeItem.user_id == current_user.id)
        .options(selectinload(WardrobeItem.item))
    )
    entries = result.scalars().all()

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
    total = sum(e.combination_count for e in entries)
    return WardrobeOut(items=items_out, total_combination_count=total)


@router.post("/add", response_model=WardrobeAddOut, status_code=status.HTTP_201_CREATED)
async def add_to_wardrobe(
    body: WardrobeAddIn,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> WardrobeAddOut:
    item_result = await db.execute(select(Item).where(Item.id == body.item_id))
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="상품을 찾을 수 없습니다.")

    existing_result = await db.execute(
        select(WardrobeItem)
        .where(WardrobeItem.user_id == current_user.id)
        .options(selectinload(WardrobeItem.item))
    )
    existing_entries = existing_result.scalars().all()
    prev_total = sum(e.combination_count for e in existing_entries)

    new_count = max(1, len(existing_entries)) * 3
    entry = WardrobeItem(
        user_id=current_user.id,
        item_id=item.id,
        month_added=len(existing_entries) + 1,
        is_first_item=False,
        combination_count=new_count,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)

    new_total = prev_total + new_count
    return WardrobeAddOut(
        added_item=WardrobeItemOut(
            id=entry.id,
            item=ItemOut.model_validate(item),
            month_added=entry.month_added,
            is_first_item=entry.is_first_item,
            combination_count=entry.combination_count,
        ),
        new_combination_count=new_total,
        delta=new_count,
    )


@router.get("/roadmap", response_model=RoadmapOut)
async def get_roadmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RoadmapOut:
    profile_result = await db.execute(
        select(StyleProfile).where(StyleProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="스타일 진단을 먼저 완료해주세요."
        )

    wardrobe_result = await db.execute(
        select(WardrobeItem)
        .where(WardrobeItem.user_id == current_user.id)
        .options(selectinload(WardrobeItem.item))
    )
    current_items = [{"name": e.item.name} for e in wardrobe_result.scalars().all()]

    months_data = await ai.generate_roadmap(profile, current_items)

    months_out: list[RoadmapMonthOut] = []
    for m in months_data:
        placeholder_item = ItemOut(
            id=__import__("uuid").uuid4(),
            name=m["item_name"],
            brand=m.get("brand"),
            price=m.get("price", 0),
            image_url=None,
            product_url=None,
            tags=[],
        )
        months_out.append(
            RoadmapMonthOut(
                month=m["month"],
                recommended_item=placeholder_item,
                reason=m["reason"],
                projected_combination_count=m["projected_combination_count"],
            )
        )

    return RoadmapOut(months=months_out)
