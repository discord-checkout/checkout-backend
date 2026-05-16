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


async def search_first_product(keyword: str) -> dict | None:
    params = {"keyword": keyword, "caller": "SEARCH", "page": 1, "size": 1}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(_URL, params=params, headers=_HEADERS)
            if res.status_code != 200:
                logger.warning("Musinsa: status=%s body=%s", res.status_code, res.text[:200])
                return None

            data = res.json()
            items = data.get("data", {}).get("list", [])
            if not items:
                logger.warning("Musinsa: empty list for keyword=%s", keyword)
                return None

            item = items[0]
            thumbnail = item.get("thumbnail", "")
            return {
                "name": item.get("goodsName", keyword),
                "brand": item.get("brandName", ""),
                "price": item.get("price") or item.get("normalPrice", 0),
                "image_url": f"https:{thumbnail}" if thumbnail.startswith("//") else thumbnail,
                "product_url": item.get("goodsLinkUrl"),
            }
    except Exception as e:
        logger.warning("Musinsa search failed: %s", e)
        return None
