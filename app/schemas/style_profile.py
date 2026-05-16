import uuid
from typing import Literal

from pydantic import BaseModel


class OnboardingIn(BaseModel):
    liked_style_cards: list[str]
    disliked_style_cards: list[str]
    body_type: Literal["slim", "regular", "large"]
    budget_monthly: int
    lifestyle: Literal["campus", "work", "social"]


class OnboardingOut(BaseModel):
    style_tags: list[str]
    profile_summary: str
    profile_id: uuid.UUID


class StyleProfileOut(BaseModel):
    id: uuid.UUID
    style_tags: list[str]
    body_type: str
    budget_monthly: int
    lifestyle: str
    profile_summary: str | None

    model_config = {"from_attributes": True}
