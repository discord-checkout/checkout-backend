from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


async def search_first_product(keyword: str) -> dict | None:
    """
    무신사에서 키워드로 검색해 가장 인기 있는 상품 1개를 반환합니다.
    Returns: { image_url, product_url, price, brand, name } or None
    """
    urls = [
        "https://www.musinsa.com/search/goods",
        "https://api.musinsa.com/api2/dp/v1/search",
    ]
    params = {
        "keyword": keyword,
        "orderby": "pop",
        "page": 1,
        "size": 1,
    }
    headers = {
        "Referer": "https://www.musinsa.com",
        "Accept": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        ),
    }

    for url in urls:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, params=params, headers=headers)
                logger.info("Musinsa [%s] status=%s", url, res.status_code)
                if res.status_code != 200:
                    continue

                data = res.json()
                logger.info("Musinsa response keys: %s", list(data.keys())[:10])

                goods_list = (
                    data.get("data", {}).get("goods", [])
                    or data.get("data", {}).get("list", [])
                    or data.get("goods", [])
                    or data.get("list", [])
                    or data.get("data", [])
                )
                if not goods_list or not isinstance(goods_list, list):
                    logger.warning("Musinsa: no goods list found")
                    continue

                item = goods_list[0]
                goods_no = item.get("goodsNo") or item.get("no") or item.get("goodsCode")
                thumbnail = (
                    item.get("thumbnail") or item.get("imageUrl")
                    or item.get("img") or item.get("goodsImage")
                )
                brand = (
                    (item.get("brand") or {}).get("name")
                    or item.get("brandName") or item.get("brand", "")
                )
                name = item.get("goodsName") or item.get("name", keyword)
                price = item.get("price") or item.get("goodsPrice", 0)

                if not thumbnail or not goods_no:
                    logger.warning("Musinsa: item keys=%s", list(item.keys()))
                    continue

                return {
                    "name": name,
                    "brand": brand,
                    "price": price,
                    "image_url": f"https:{thumbnail}" if thumbnail.startswith("//") else thumbnail,
                    "product_url": f"https://www.musinsa.com/app/goods/{goods_no}",
                }
        except Exception as e:
            logger.warning("Musinsa search failed [%s]: %s", url, e)

    return None
