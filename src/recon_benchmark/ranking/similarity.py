from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping

from rapidfuzz.distance import JaroWinkler


def jaro_winkler_similarity(left: str, right: str) -> float:
    return _clamp(float(JaroWinkler.normalized_similarity(left, right)))


def qgram_counts(value: str, q: int = 3) -> Counter[str]:
    if q < 1:
        raise ValueError("q tem de ser >= 1.")
    padded = f"^{value}$"
    if len(padded) <= q:
        return Counter({padded: 1})
    return Counter(padded[index : index + q] for index in range(len(padded) - q + 1))


def qgram_cosine_similarity(left: str, right: str, q: int = 3) -> float:
    left_counts = qgram_counts(left, q)
    right_counts = qgram_counts(right, q)
    return cosine_similarity(left_counts, right_counts)


def cosine_similarity(
    left: Mapping[str, int],
    right: Mapping[str, int],
) -> float:
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return _clamp(dot / (left_norm * right_norm))


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
