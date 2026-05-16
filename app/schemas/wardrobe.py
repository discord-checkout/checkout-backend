from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel

from app.schemas.item import ItemOut


class WardrobeItemOut(BaseModel):
    id: uuid.UUID
    item: ItemOut
    month_added: Optional[int]
    is_first_item: bool
    combination_count: int

    model_config = {"from_attributes": True}


class WardrobeOut(BaseModel):
    items: list[WardrobeItemOut]
    total_combination_count: int


class WardrobeAddIn(BaseModel):
    item_id: uuid.UUID


class WardrobeAddOut(BaseModel):
    added_item: WardrobeItemOut
    new_combination_count: int
    delta: int


class RoadmapMonthOut(BaseModel):
    month: int
    recommended_item: ItemOut
    reason: str
    projected_combination_count: int


class RoadmapOut(BaseModel):
    months: list[RoadmapMonthOut]
