from __future__ import annotations

from collections import defaultdict

from app.models.item import Item


def calculate_combinations(items: list[Item]) -> int:
    counts: dict[str, int] = defaultdict(int)
    for item in items:
        counts[item.category] += 1

    tops = counts["top"]
    bottoms = counts["bottom"]
    outers = counts["outer"]
    shoes = counts["shoes"]

    if tops == 0 or bottoms == 0:
        return 0

    return tops * bottoms * max(1, shoes) * (outers + 1)
