from __future__ import annotations

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field


class WardrobeIn(BaseModel):
    top: list[str] = Field(
        default=[],
        description="상의 목록. 현재 가지고 있는 상의 아이템명을 입력하세요. 없으면 빈 배열.",
        examples=[["white_black_tee", "hoodie", "knit"]],
    )
    bottom: list[str] = Field(
        default=[],
        description="하의 목록. 현재 가지고 있는 하의 아이템명을 입력하세요. 없으면 빈 배열.",
        examples=[["black_slacks", "wide_denim", "cargo_pants"]],
    )
    outer: list[str] = Field(
        default=[],
        description="아우터 목록. 자켓, 코트 등. 없으면 빈 배열.",
        examples=[["coach_jacket", "windbreaker"]],
    )
    shoes: list[str] = Field(
        default=[],
        description="신발 목록. 없으면 빈 배열.",
        examples=[["white_sneakers", "new_balance"]],
    )


class OnboardingIn(BaseModel):
    style_mood: Literal["minimal", "casual", "cityboy", "amekaji", "sports", "vintage"] = Field(
        description=(
            "선호 스타일 무드.\n"
            "- `minimal`: 미니멀 (깔끔, 단색, 군더더기 없는 스타일)\n"
            "- `casual`: 캐주얼 (편안하고 일상적인 스타일)\n"
            "- `cityboy`: 시티보이 (도시적, 스트릿 감성)\n"
            "- `amekaji`: 아메카지 (아메리칸 캐주얼, 데님·워크웨어)\n"
            "- `sports`: 스포츠 (스포티, 애슬레저)\n"
            "- `vintage`: 빈티지 (레트로, 구제 감성)"
        ),
        examples=["minimal"],
    )
    fit_preference: Literal["slim", "regular", "overfit", "unknown"] = Field(
        description=(
            "선호하는 핏.\n"
            "- `slim`: 슬림핏 (몸에 딱 맞는)\n"
            "- `regular`: 레귤러핏 (표준 사이즈)\n"
            "- `overfit`: 오버핏 (크고 여유 있는)\n"
            "- `unknown`: 잘 모르겠음"
        ),
        examples=["regular"],
    )
    lifestyle: Literal["campus", "office", "daily", "freelance"] = Field(
        description=(
            "주요 생활 패턴.\n"
            "- `campus`: 캠퍼스 (학교생활 중심)\n"
            "- `office`: 오피스 (직장생활 중심)\n"
            "- `daily`: 데일리 (일상·약속 중심)\n"
            "- `freelance`: 프리랜서 (재택·카페 중심)"
        ),
        examples=["campus"],
    )
    current_wardrobe: WardrobeIn = Field(
        description="현재 보유 중인 옷장. 카테고리별로 아이템명을 입력하세요. 아이템이 없는 카테고리는 빈 배열로 보내세요."
    )
    budget_range: Literal["under_5", "5_to_10", "10_to_20", "over_20"] = Field(
        description=(
            "월 의류 예산 (만원 단위).\n"
            "- `under_5`: 5만원 미만\n"
            "- `5_to_10`: 5~10만원\n"
            "- `10_to_20`: 10~20만원\n"
            "- `over_20`: 20만원 이상"
        ),
        examples=["5_to_10"],
    )


class OnboardingOut(BaseModel):
    profile_id: uuid.UUID = Field(description="생성된 스타일 프로필 ID")
    profile_summary: str = Field(
        description="AI가 생성한 한 줄 스타일 요약",
        examples=["캠퍼스 라이프 · 월 5~10만원 · 미니멀"],
    )
    current_combination_count: int = Field(
        description="현재 옷장 기준으로 만들 수 있는 코디 조합 수"
    )
    style_mood: str = Field(description="선택한 스타일 무드", examples=["minimal"])


class StyleProfileOut(BaseModel):
    id: uuid.UUID
    style_mood: str
    fit_preference: str
    lifestyle: str
    budget_range: str
    profile_summary: Optional[str]

    model_config = {"from_attributes": True}
