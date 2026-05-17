"""
로드맵 로직 테스트

검증 항목:
1. first_item이 있으면 AI 프롬프트에 month=2부터 요청하고 month 1은 직접 삽입
2. first_item이 없으면 AI가 month 1부터 생성
3. 반환된 months 순서가 올바른지
"""
import json
import pytest
import pytest_asyncio
from unittest.mock import MagicMock, patch

from app.services.ai import generate_roadmap


# conftest.py의 setup_db(autouse=True)가 PostgreSQL에 연결하려 하므로 no-op으로 override
@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    yield


def _make_profile(budget="5_to_10", style="minimal"):
    p = MagicMock()
    p.budget_range = budget
    p.style_mood = style
    return p


def _make_gemini_response(months: list[dict]) -> MagicMock:
    mock_resp = MagicMock()
    mock_resp.text = json.dumps({"months": months})
    return mock_resp


@pytest.mark.asyncio
async def test_roadmap_without_first_item_requests_from_month1():
    """first_item 없으면 AI에 month 1부터 요청"""
    ai_months = [
        {"month": 1, "item_name": "화이트 셔츠", "search_keyword": "화이트 셔츠",
         "brand": "A", "price": 29000, "category": "top",
         "reason": "이유1", "projected_combination_count": 6},
        {"month": 2, "item_name": "와이드 청바지", "search_keyword": "와이드 청바지",
         "brand": "B", "price": 35000, "category": "bottom",
         "reason": "이유2", "projected_combination_count": 12},
        {"month": 3, "item_name": "크루넥 맨투맨", "search_keyword": "크루넥 맨투맨",
         "brand": "C", "price": 45000, "category": "top",
         "reason": "이유3", "projected_combination_count": 20},
    ]
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_gemini_response(ai_months)

    with patch("app.services.ai._get_client", return_value=mock_model):
        result = await generate_roadmap(_make_profile(), current_items=[], first_item=None)

    prompt = mock_model.generate_content.call_args[0][0]
    assert "month 값은 1부터 시작" in prompt
    assert len(result) == 3
    assert result[0]["month"] == 1


@pytest.mark.asyncio
async def test_roadmap_with_first_item_requests_from_month2():
    """first_item 있으면 AI에 month 2부터 요청하고 프롬프트에 첫 아이템 포함"""
    ai_months = [
        {"month": 2, "item_name": "와이드 청바지", "search_keyword": "와이드 청바지",
         "brand": "B", "price": 35000, "category": "bottom",
         "reason": "이유2", "projected_combination_count": 12},
        {"month": 3, "item_name": "크루넥 맨투맨", "search_keyword": "크루넥 맨투맨",
         "brand": "C", "price": 45000, "category": "top",
         "reason": "이유3", "projected_combination_count": 20},
    ]
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_gemini_response(ai_months)

    first_item = {"name": "오버핏 화이트 셔츠", "category": "top"}

    with patch("app.services.ai._get_client", return_value=mock_model):
        result = await generate_roadmap(_make_profile(), current_items=[], first_item=first_item)

    prompt = mock_model.generate_content.call_args[0][0]
    assert "오버핏 화이트 셔츠" in prompt      # 첫 아이템 이름이 프롬프트에 포함
    assert "month 값은 2부터 시작" in prompt   # month 2부터 요청
    assert len(result) == 2
    assert result[0]["month"] == 2
    assert result[1]["month"] == 3


@pytest.mark.asyncio
async def test_roadmap_budget_label_in_prompt():
    """예산 레이블이 프롬프트에 정확히 포함되는지"""
    mock_model = MagicMock()
    mock_model.generate_content.return_value = _make_gemini_response([
        {"month": 2, "item_name": "청바지", "search_keyword": "와이드 청바지",
         "brand": "A", "price": 30000, "category": "bottom",
         "reason": "이유", "projected_combination_count": 10},
    ])

    with patch("app.services.ai._get_client", return_value=mock_model):
        await generate_roadmap(
            _make_profile(budget="10_to_15"),
            current_items=[],
            first_item={"name": "화이트 셔츠", "category": "top"},
        )

    prompt = mock_model.generate_content.call_args[0][0]
    assert "10~15만원" in prompt


@pytest.mark.asyncio
async def test_roadmap_fallback_with_first_item():
    """Gemini 실패 시 fallback은 month 2, 3만 반환"""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("Gemini 에러")

    with patch("app.services.ai._get_client", return_value=mock_model):
        result = await generate_roadmap(
            _make_profile(),
            current_items=[],
            first_item={"name": "화이트 셔츠", "category": "top"},
        )

    assert all(m["month"] >= 2 for m in result)
    assert len(result) == 2


@pytest.mark.asyncio
async def test_roadmap_fallback_without_first_item():
    """Gemini 실패 시 fallback은 month 1, 2, 3 반환"""
    mock_model = MagicMock()
    mock_model.generate_content.side_effect = Exception("Gemini 에러")

    with patch("app.services.ai._get_client", return_value=mock_model):
        result = await generate_roadmap(_make_profile(), current_items=[], first_item=None)

    assert result[0]["month"] == 1
    assert len(result) == 3
