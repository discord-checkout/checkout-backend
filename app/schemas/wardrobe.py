from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.item import ItemOut


class WardrobeItemOut(BaseModel):
    id: uuid.UUID = Field(description="옷장 항목 ID")
    item: ItemOut = Field(description="아이템 상세 정보")
    month_added: Optional[int] = Field(description="몇 번째 달에 추가했는지")
    is_first_item: bool = Field(description="첫 번째 추천 아이템 여부")
    combination_count: int = Field(description="이 아이템 추가로 늘어난 조합 수")

    model_config = {"from_attributes": True}


class WardrobeOut(BaseModel):
    items: list[WardrobeItemOut] = Field(description="옷장에 추가된 아이템 목록")
    total_combination_count: int = Field(description="현재 옷장 전체 코디 조합 수")


class WardrobeAddIn(BaseModel):
    item_id: uuid.UUID = Field(description="추가할 아이템의 UUID (추천 아이템의 id 값)")


class WardrobeAddOut(BaseModel):
    added_item: WardrobeItemOut = Field(description="추가된 아이템 정보")
    new_combination_count: int = Field(description="추가 후 전체 코디 조합 수")
    delta: int = Field(description="이 아이템으로 새로 생긴 조합 수")


class RoadmapMonthOut(BaseModel):
    month: int = Field(description="몇 번째 달 추천인지", examples=[1])
    recommended_item: ItemOut = Field(description="해당 달 추천 아이템")
    reason: str = Field(description="이 달에 이 아이템을 추천하는 이유")
    projected_combination_count: int = Field(description="이 아이템 추가 시 예상 코디 조합 수")


class RoadmapOut(BaseModel):
    months: list[RoadmapMonthOut] = Field(description="월별 추천 로드맵 (3개월)")
