import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    res = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secret1234",
        "nickname": "테스터",
    })
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate(client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "pw", "nickname": "dup"}
    await client.post("/auth/register", json=payload)
    res = await client.post("/auth/register", json=payload)
    assert res.status_code == 409


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/auth/register", json={
        "email": "login@example.com",
        "password": "mypassword",
        "nickname": "로그인유저",
    })
    res = await client.post("/auth/login", json={
        "email": "login@example.com",
        "password": "mypassword",
    })
    assert res.status_code == 200
    assert "access_token" in res.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/auth/register", json={
        "email": "wrong@example.com",
        "password": "correct",
        "nickname": "유저",
    })
    res = await client.post("/auth/login", json={
        "email": "wrong@example.com",
        "password": "incorrect",
    })
    assert res.status_code == 401
