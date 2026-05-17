from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_URL = "https://api.musinsa.com/api2/dp/v1/plp/goods"
_HEADERS = {
    "Referer": "https://www.musinsa.com",
    "Accept": "application/json",
    "app-os": "web",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}


def _keyword_candidates(keyword: str) -> list[str]:
    import re
    clean = re.sub(r"\([^)]*\)", "", keyword)
    clean = re.sub(r"\s*[-–]\s*\S+.*$", "", clean)
    clean = clean.strip()
    words = clean.split()
    candidates = [clean]
    if len(words) > 2:
        candidates.append(" ".join(words[-2:]))  # 마지막 2단어
    if len(words) > 1:
        candidates.append(words[-1])             # 마지막 1단어 (최후 수단)
    return candidates


async def _do_search(client: httpx.AsyncClient, keyword: str) -> dict | None:
    params = {"keyword": keyword, "caller": "SEARCH", "page": 1, "size": 1, "gf": "M"}
    res = await client.get(_URL, params=params, headers=_HEADERS)
    if res.status_code != 200:
        logger.warning("Musinsa: status=%s body=%s", res.status_code, res.text[:200])
        return None
    items = res.json().get("data", {}).get("list", [])
    if not items:
        return None
    item = items[0]
    thumbnail = item.get("thumbnail", "")
    return {
        "name": item.get("goodsName", keyword),
        "brand": item.get("brandName", ""),
        "price": item.get("price") or item.get("normalPrice", 0),
        "image_url": f"https:{thumbnail}" if thumbnail.startswith("//") else thumbnail or None,
        "product_url": item.get("goodsLinkUrl"),
    }


async def search_first_product(keyword: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            for query in _keyword_candidates(keyword):
                result = await _do_search(client, query)
                if result:
                    return result
        logger.warning("Musinsa: no results for keyword=%s", keyword)
        return None
    except Exception as e:
        logger.warning("Musinsa search failed: %s", e)
        return None
