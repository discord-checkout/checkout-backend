import pytest
from httpx import AsyncClient

from app.services import ai


@pytest.fixture
def mock_classify_style(monkeypatch):
    async def _mock(liked, disliked):
        return ["minimal", "casual"], "깔끔한 미니멀 캐주얼"
    monkeypatch.setattr(ai, "classify_style", _mock)


@pytest.mark.asyncio
async def test_onboarding_diagnose(client: AsyncClient, mock_classify_style):
    reg = await client.post("/auth/register", json={
        "email": "onboard@example.com",
        "password": "pw",
        "nickname": "온보딩유저",
    })
    token = reg.json()["access_token"]

    res = await client.post(
        "/onboarding/diagnose",
        json={
            "liked_style_cards": ["minimal", "casual"],
            "disliked_style_cards": ["sporty"],
            "body_type": "regular",
            "budget_monthly": 80000,
            "lifestyle": "campus",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert "profile_id" in data
    assert data["style_tags"] == ["minimal", "casual"]


@pytest.mark.asyncio
async def test_onboarding_requires_auth(client: AsyncClient):
    res = await client.post("/onboarding/diagnose", json={
        "liked_style_cards": [],
        "disliked_style_cards": [],
        "body_type": "slim",
        "budget_monthly": 50000,
        "lifestyle": "campus",
    })
    assert res.status_code == 403
