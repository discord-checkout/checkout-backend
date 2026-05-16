import json
import logging

import google.generativeai as genai

from app.core.config import settings
from app.models.style_profile import StyleProfile

logger = logging.getLogger(__name__)


def _get_client() -> genai.GenerativeModel:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


async def classify_style(liked: list[str], disliked: list[str]) -> tuple[list[str], str]:
    """
    좋아요/싫어요 카드 목록으로 style_tags와 profile_summary 반환.
    Returns: (style_tags, profile_summary)
    """
    prompt = f"""
당신은 패션 스타일리스트입니다. 사용자의 스타일 선호도를 분석해주세요.

좋아하는 스타일: {liked}
싫어하는 스타일: {disliked}

다음 JSON 형식으로만 응답하세요:
{{
  "style_tags": ["tag1", "tag2", "tag3"],
  "profile_summary": "한 줄 스타일 요약 (20자 이내)"
}}

style_tags는 2-4개, 영문 소문자와 언더스코어 사용.
"""
    try:
        model = _get_client()
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return data["style_tags"], data["profile_summary"]
    except Exception as e:
        logger.warning("Gemini classify_style failed: %s", e)
        return ["minimal", "casual"], "깔끔하고 편안한 스타일"


async def recommend_first_item(profile: StyleProfile) -> dict:
    """
    StyleProfile 기반 첫 번째 아이템 추천.
    Returns dict with: item_name, brand, price, reason, combinations, combination_count
    """
    prompt = f"""
당신은 패션 큐레이터입니다. 아래 프로필을 가진 대학생에게 옷장의 첫 번째 아이템을 추천해주세요.

스타일 태그: {profile.style_tags}
체형: {profile.body_type}
월 예산: {profile.budget_monthly}원
라이프스타일: {profile.lifestyle}

다음 JSON 형식으로만 응답하세요:
{{
  "item_name": "아이템 이름",
  "brand": "브랜드명",
  "price": 29000,
  "reason": "이 옷을 첫 번째로 추천하는 이유 (2-3문장)",
  "combinations": [
    {{"description": "상황 — 아이템1 + 아이템2 + 아이템3"}},
    {{"description": "상황 — 아이템1 + 아이템2 + 아이템3"}},
    {{"description": "상황 — 아이템1 + 아이템2 + 아이템3"}}
  ],
  "combination_count": 3
}}
"""
    try:
        model = _get_client()
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception as e:
        logger.warning("Gemini recommend_first_item failed: %s", e)
        return {
            "item_name": "워시드 네이비 하프 티셔츠",
            "brand": "무신사 스탠다드",
            "price": 29000,
            "reason": "베이직 아이템으로 다양한 코디가 가능합니다.",
            "combinations": [
                {"description": "스터디 모임 — 이 티 + 슬랙스 + 스니커즈"},
                {"description": "조별 발표 — 이 티 + 면 바지 + 로퍼"},
                {"description": "주말 외출 — 이 티 + 데님 + 캔버스화"},
            ],
            "combination_count": 3,
        }


async def generate_roadmap(profile: StyleProfile, current_items: list[dict]) -> list[dict]:
    """
    3개월 로드맵 추천.
    Returns list of month dicts: month, item_name, brand, price, reason, projected_combination_count
    """
    prompt = f"""
당신은 패션 스타일리스트입니다. 아래 프로필을 가진 대학생의 3개월 옷장 로드맵을 만들어주세요.

스타일 태그: {profile.style_tags}
월 예산: {profile.budget_monthly}원
현재 보유 아이템 수: {len(current_items)}개

다음 JSON 형식으로만 응답하세요:
{{
  "months": [
    {{
      "month": 1,
      "item_name": "아이템명",
      "brand": "브랜드",
      "price": 29000,
      "reason": "이 달 추천 이유",
      "projected_combination_count": 6
    }}
  ]
}}
"""
    try:
        model = _get_client()
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        data = json.loads(text)
        return data["months"]
    except Exception as e:
        logger.warning("Gemini generate_roadmap failed: %s", e)
        return [
            {"month": 1, "item_name": "베이직 슬랙스", "brand": "무신사 스탠다드",
             "price": 35000, "reason": "코디 범용성이 가장 높습니다.", "projected_combination_count": 6},
            {"month": 2, "item_name": "오버핏 셔츠", "brand": "커버낫",
             "price": 59000, "reason": "레이어드 코디로 활용 폭이 넓습니다.", "projected_combination_count": 12},
            {"month": 3, "item_name": "카고 팬츠", "brand": "디스이즈네버댓",
             "price": 89000, "reason": "캐주얼 무드를 완성합니다.", "projected_combination_count": 20},
        ]
