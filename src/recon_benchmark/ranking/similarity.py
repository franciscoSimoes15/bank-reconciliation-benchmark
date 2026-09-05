from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping

from rapidfuzz.distance import JaroWinkler


def jaro_winkler_similarity(left: str, right: str) -> float:
    """Measure text similarity with RapidFuzz's normalized Jaro-Winkler score in [0,1].

    Inputs are compared as provided; field-specific normalization happens upstream.
    """
    return _clamp(float(JaroWinkler.normalized_similarity(left, right)))


def qgram_counts(value: str, q: int = 3) -> Counter[str]:
    """Count overlapping character fragments after adding start/end boundary markers.

    q=3 produces trigrams. If the padded text fits within q characters, count it
    as one fragment; reject q below 1.
    """
    if q < 1:
        raise ValueError("q tem de ser >= 1.")
    padded = f"^{value}$"
    if len(padded) <= q:
        return Counter({padded: 1})
    return Counter(padded[index : index + q] for index in range(len(padded) - q + 1))


def qgram_cosine_similarity(left: str, right: str, q: int = 3) -> float:
    """Compare text by cosine similarity between boundary-marked q-gram frequency vectors."""
    left_counts = qgram_counts(left, q)
    right_counts = qgram_counts(right, q)
    return cosine_similarity(left_counts, right_counts)


def cosine_similarity(
    left: Mapping[str, int],
    right: Mapping[str, int],
) -> float:
    """Compute cosine compatibility for nonnegative feature-count mappings.

    Return zero for empty or zero-length vectors to avoid division by zero;
    otherwise normalize their dot product and bound the result to [0,1].
    """
    if not left or not right:
        return 0.0
    dot = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return _clamp(dot / (left_norm * right_norm))


def _clamp(value: float) -> float:
    """Keep the similarity result within [0,1] despite floating-point rounding."""
    return min(1.0, max(0.0, value))
