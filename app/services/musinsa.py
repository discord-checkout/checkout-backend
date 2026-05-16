from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.musinsa.com/api2/dp/v1/search/goods"
HEADERS = {
    "app-os": "ios",
    "app-version": "3.3.2",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0",
}


async def search_first_product(keyword: str) -> dict | None:
    """
    무신사에서 키워드로 검색해 가장 인기 있는 상품 1개를 반환합니다.
    Returns: { image_url, product_url, price, brand, name } or None
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                SEARCH_URL,
                params={"keyword": keyword, "sortCode": "POPULAR", "page": 1, "size": 1},
                headers=HEADERS,
            )
            res.raise_for_status()
            data = res.json()

        goods_list = (
            data.get("data", {}).get("goods", [])
            or data.get("data", {}).get("list", [])
        )
        if not goods_list:
            return None

        item = goods_list[0]
        goods_no = item.get("goodsNo") or item.get("no")
        thumbnail = item.get("thumbnail") or item.get("imageUrl") or item.get("img")
        brand = (item.get("brand") or {}).get("name") or item.get("brandName", "")
        name = item.get("goodsName") or item.get("name", keyword)
        price = item.get("price", 0)

        return {
            "name": name,
            "brand": brand,
            "price": price,
            "image_url": f"https:{thumbnail}" if thumbnail and thumbnail.startswith("//") else thumbnail,
            "product_url": f"https://www.musinsa.com/app/goods/{goods_no}" if goods_no else None,
        }
    except Exception as e:
        logger.warning("Musinsa search failed for '%s': %s", keyword, e)
        return None
