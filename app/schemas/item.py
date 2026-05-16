from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, Field


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
    label: str = Field(description="조합 번호", examples=["조합 1"])
    description: str = Field(description="코디 설명", examples=["화이트 셔츠 + 청바지 + 흰 스니커즈"])


class FirstItemRecommendationOut(BaseModel):
    item_name: str = Field(description="추천 아이템명", examples=["오버핏 화이트 셔츠"])
    price: int = Field(description="가격 (원 단위)", examples=[29000])
    brand: str = Field(description="브랜드명", examples=["무신사 스탠다드"])
    reason: str = Field(description="이 아이템을 첫 번째로 추천하는 이유")
    image_url: Optional[str] = Field(description="상품 이미지 URL")
    product_url: str = Field(description="무신사 상품 페이지 URL (없을 경우 검색 URL)")
    combinations: list[CombinationOut] = Field(description="이 아이템으로 만들 수 있는 코디 조합 목록")
    current_combination_count: int = Field(description="현재 옷장 기준 코디 조합 수")
    after_combination_count: int = Field(description="이 아이템 추가 후 코디 조합 수")
