from __future__ import annotations

import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field

OuterItem = Literal[
    "코트", "트렌치코트", "패딩", "자켓", "블레이저",
    "가디건", "후드집업", "점퍼", "바람막이",
]
TopItem = Literal[
    "베이직 셔츠", "니트", "티셔츠", "긴팔티", "맨투맨",
    "후드티", "반팔셔츠", "린넨셔츠", "폴로셔츠",
]
BottomItem = Literal[
    "슬랙스", "청바지", "조거팬츠", "반바지", "면바지",
    "와이드팬츠", "카고팬츠",
]


class WardrobeIn(BaseModel):
    outer: list[OuterItem] = Field(
        default=[],
        description="보유 중인 아우터 목록 (복수 선택 가능). 없으면 빈 배열.",
        examples=[["자켓", "바람막이"]],
    )
    top: list[TopItem] = Field(
        default=[],
        description="보유 중인 상의 목록 (복수 선택 가능). 없으면 빈 배열.",
        examples=[["티셔츠", "맨투맨", "니트"]],
    )
    bottom: list[BottomItem] = Field(
        default=[],
        description="보유 중인 하의 목록 (복수 선택 가능). 없으면 빈 배열.",
        examples=[["청바지", "슬랙스"]],
    )


class OnboardingIn(BaseModel):
    style_mood: Literal["minimal", "casual", "dandy", "sports", "vintage", "street"] = Field(
        description=(
            "선호 스타일 무드.\n"
            "- `minimal`: 미니멀 (깔끔, 단색, 군더더기 없는 스타일)\n"
            "- `casual`: 캐주얼 (편안하고 일상적인 스타일)\n"
            "- `dandy`: 댄디 (클래식하고 세련된 신사 스타일)\n"
            "- `sports`: 스포츠 (스포티, 애슬레저)\n"
            "- `vintage`: 빈티지 (레트로, 구제 감성)\n"
            "- `street`: 스트릿 (힙한 스트리트·그래픽 감성)"
        ),
        examples=["minimal"],
    )
    fit_preference: Literal["slim", "regular", "overfit"] = Field(
        description=(
            "선호하는 핏.\n"
            "- `slim`: 슬림핏 (몸에 딱 맞는)\n"
            "- `regular`: 레귤러핏 (표준 사이즈)\n"
            "- `overfit`: 오버핏 (크고 여유 있는)"
        ),
        examples=["regular"],
    )
    lifestyle: Literal["campus", "office", "daily", "freelance"] = Field(
        description=(
            "주요 생활 패턴.\n"
            "- `campus`: 캠퍼스/학교 생활 중심\n"
            "- `office`: 직장/오피스 생활 중심\n"
            "- `daily`: 전역 후/일상 생활 중심\n"
            "- `freelance`: 자유직/재택 근무 중심"
        ),
        examples=["campus"],
    )
    current_wardrobe: WardrobeIn = Field(
        description="현재 보유 중인 옷장. 카테고리별로 아이템을 복수 선택하세요. 없는 카테고리는 빈 배열로 보내세요."
    )
    budget_range: Literal["under_5", "5_to_10", "10_to_15", "15_to_20", "over_20"] = Field(
        description=(
            "월 의류 예산 (만원 단위).\n"
            "- `under_5`: 5만원 이하\n"
            "- `5_to_10`: 5~10만원\n"
            "- `10_to_15`: 10~15만원\n"
            "- `15_to_20`: 15~20만원\n"
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
