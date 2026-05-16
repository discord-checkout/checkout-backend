from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel


class ItemOut(BaseModel):
    id: uuid.UUID
    name: str
    brand: Optional[str]
    price: int
    image_url: Optional[str]
    product_url: Optional[str]
    tags: list[str]

    model_config = {"from_attributes": True}


class CombinationOut(BaseModel):
    description: str


class FirstItemRecommendationOut(BaseModel):
    item: ItemOut
    reason: str
    combinations: list[CombinationOut]
    combination_count: int
