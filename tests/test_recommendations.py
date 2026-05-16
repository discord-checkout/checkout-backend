import pytest
from httpx import AsyncClient

from app.services import ai

MOCK_RECOMMENDATION = {
    "item_name": "워시드 네이비 티셔츠",
    "brand": "무신사 스탠다드",
    "price": 29000,
    "reason": "테스트 추천 이유",
    "combinations": [
        {"description": "조합 1 — 아이템A + 아이템B"},
        {"description": "조합 2 — 아이템A + 아이템C"},
    ],
    "combination_count": 2,
}


@pytest.fixture
def mock_ai(monkeypatch):
    async def _mock_classify(liked, disliked):
        return ["minimal"], "미니멀"

    async def _mock_recommend(profile):
        return MOCK_RECOMMENDATION

    monkeypatch.setattr(ai, "classify_style", _mock_classify)
    monkeypatch.setattr(ai, "recommend_first_item", _mock_recommend)


@pytest.mark.asyncio
async def test_first_item_recommendation(client: AsyncClient, mock_ai):
    reg = await client.post("/auth/register", json={
        "email": "rec@example.com",
        "password": "pw",
        "nickname": "추천유저",
    })
    token = reg.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/onboarding/diagnose",
        json={
            "liked_style_cards": ["minimal"],
            "disliked_style_cards": [],
            "body_type": "slim",
            "budget_monthly": 50000,
            "lifestyle": "campus",
        },
        headers=headers,
    )

    res = await client.get("/recommendations/first-item", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["item"]["name"] == "워시드 네이비 티셔츠"
    assert len(data["combinations"]) == 2
