from __future__ import annotations

import json
import logging

import google.generativeai as genai

from app.core.config import settings
from app.models.style_profile import StyleProfile

logger = logging.getLogger(__name__)


def _get_client() -> genai.GenerativeModel:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel(settings.GEMINI_MODEL)


_BUDGET_LABEL: dict[str, str] = {
    "under_5": "월 5만원 이하",
    "5_to_10": "월 5~10만원",
    "10_to_15": "월 10~15만원",
    "15_to_20": "월 15~20만원",
    "over_20": "월 20만원 이상",
}
_LIFESTYLE_LABEL: dict[str, str] = {
    "campus": "캠퍼스",
    "office": "오피스",
    "daily": "일상",
    "freelance": "재택",
}
_MOOD_LABEL: dict[str, str] = {
    "minimal": "미니멀",
    "casual": "캐주얼",
    "dandy": "댄디",
    "sports": "스포츠",
    "vintage": "빈티지",
    "street": "스트릿",
}


async def generate_profile_summary(
    style_mood: str, lifestyle: str, budget_range: str
) -> str:
    budget_label = _BUDGET_LABEL.get(budget_range, budget_range)

    prompt = f"""
패션 스타일 프로필을 한 줄(20자 이내)로 요약해주세요.

스타일: {_MOOD_LABEL.get(style_mood, style_mood)}
라이프스타일: {_LIFESTYLE_LABEL.get(lifestyle, lifestyle)}
예산: {budget_label}

예시: "캠퍼스 라이프 · 월 10만원 · 미니멀 캐주얼"
응답은 요약 문장만 출력하세요.
"""
    try:
        model = _get_client()
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.warning("Gemini generate_profile_summary failed: %s", e)
        return f"{_LIFESTYLE_LABEL.get(lifestyle, lifestyle)} · {budget_label} · {_MOOD_LABEL.get(style_mood, style_mood)}"


async def recommend_first_item(profile: StyleProfile) -> dict:
    budget_label = _BUDGET_LABEL.get(profile.budget_range, profile.budget_range).replace("월 ", "")
    mood_label = _MOOD_LABEL.get(profile.style_mood, profile.style_mood)
    lifestyle_label = _LIFESTYLE_LABEL.get(profile.lifestyle, profile.lifestyle)

    current_wardrobe = profile.current_wardrobe or {}
    wardrobe_summary = {
        "상의": current_wardrobe.get("top", []),
        "하의": current_wardrobe.get("bottom", []),
        "아우터": current_wardrobe.get("outer", []),
    }

    prompt = f"""
당신은 패션 큐레이터입니다. 아래 프로필의 대학생에게 옷장의 핵심 첫 번째 아이템을 추천해주세요.

스타일: {mood_label}
핏 선호: {profile.fit_preference}
라이프스타일: {lifestyle_label}
월 예산: {budget_label}
현재 보유 옷장: {wardrobe_summary}

[중요 지침]
- 추천 아이템의 가격은 반드시 월 예산({budget_label}) 이내여야 합니다.
- 스타일({mood_label})에 맞는 아이템을 추천하세요.
- 조합(combinations)은 반드시 현재 보유 옷장의 아이템들과 추천 아이템을 엮은 실제 코디여야 합니다.
- 보유 옷장이 비어있으면 앞으로 갖춰나갈 기본 아이템들과의 조합을 제시하세요.
- 모든 텍스트는 반드시 한국어로만 작성하세요.

다음 JSON 형식으로만 응답하세요:
{{
  "item_name": "아이템 이름",
  "brand": "브랜드명",
  "price": 29000,
  "reason": "이 옷을 첫 번째로 추천하는 이유 (2-3문장)",
  "combinations": [
    {{"label": "조합 1", "description": "화이트 셔츠 + 청바지 + 흰 스니커즈"}},
    {{"label": "조합 2", "description": "화이트 셔츠 + 카고팬츠 + 뉴발란스"}},
    {{"label": "조합 3", "description": "화이트 셔츠 + 슬랙스 + 로퍼"}}
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
        return json.loads(text)
    except Exception as e:
        logger.warning("Gemini recommend_first_item failed: %s", e)
        return {
            "item_name": "오버핏 화이트 셔츠",
            "brand": "무신사 스탠다드",
            "price": 29000,
            "reason": "어떤 스타일에도 잘 어울리는 기본 아이템입니다. 가진 하의 모두와 바로 연결됩니다.",
            "combinations": [
                {"label": "조합 1", "description": "화이트 셔츠 + 청바지 + 흰 스니커즈"},
                {"label": "조합 2", "description": "화이트 셔츠 + 카고팬츠 + 뉴발란스"},
                {"label": "조합 3", "description": "화이트 셔츠 + 슬랙스 + 로퍼"},
            ],
        }


async def generate_roadmap(profile: StyleProfile, current_items: list[dict]) -> list[dict]:
    budget_label = _BUDGET_LABEL.get(profile.budget_range, profile.budget_range).replace("월 ", "")
    mood_label = _MOOD_LABEL.get(profile.style_mood, profile.style_mood)

    prompt = f"""
당신은 패션 스타일리스트입니다. 아래 프로필을 가진 대학생의 3개월 옷장 로드맵을 만들어주세요.

스타일: {mood_label}
월 예산: {budget_label}
현재 보유 아이템 수: {len(current_items)}개

[중요 지침]
- 각 달 추천 아이템의 가격은 반드시 월 예산({budget_label}) 이내여야 합니다.
- {mood_label} 스타일에 맞는 아이템만 추천하세요.
- 앞 달 아이템과 조합이 잘 되는 아이템 위주로 구성하세요.

다음 JSON 형식으로만 응답하세요:
{{
  "months": [
    {{
      "month": 1,
      "item_name": "아이템명",
      "brand": "브랜드",
      "price": 29000,
      "category": "top",
      "reason": "이 달 추천 이유",
      "projected_combination_count": 6
    }}
  ]
}}

category는 top/bottom/outer/shoes 중 하나.
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
            {"month": 1, "item_name": "베이직 슬랙스", "brand": "무신사 스탠다드", "price": 35000,
             "category": "bottom", "reason": "코디 범용성이 가장 높습니다.", "projected_combination_count": 6},
            {"month": 2, "item_name": "오버핏 셔츠", "brand": "커버낫", "price": 59000,
             "category": "top", "reason": "레이어드 코디로 활용 폭이 넓습니다.", "projected_combination_count": 12},
            {"month": 3, "item_name": "카고 팬츠", "brand": "디스이즈네버댓", "price": 89000,
             "category": "bottom", "reason": "캐주얼 무드를 완성합니다.", "projected_combination_count": 20},
        ]
