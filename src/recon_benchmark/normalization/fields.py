from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")
_LEGAL_SUFFIXES = frozenset({"lda", "sa"})
_CENT = Decimal("0.01")


def normalize_text(value: str | None) -> str | None:
    """Normalize optional text for comparison by removing accents and unifying spacing/case.

    Keep ASCII letters and digits, replace other characters with spaces, and return
    None for absent input or a result with no remaining content.
    """
    if value is None:
        return None
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    lowered = without_accents.lower()
    punctuation_as_space = _NON_ALNUM_RE.sub(" ", lowered)
    normalized = _WHITESPACE_RE.sub(" ", punctuation_as_space).strip()
    return normalized or None


def normalize_reference(value: str | None) -> str | None:
    """Normalize a reference and remove spaces so formatting separators do not cause
    disagreement.

    Preserve an absent or empty normalized reference as None.
    """
    normalized = normalize_text(value)
    if normalized is None:
        return None
    compact = normalized.replace(" ", "")
    return compact or None


def normalize_entity(value: str | None) -> str | None:
    """Normalize an entity name and remove the generated legal-form tokens lda and sa.

    Preserve the remaining word order and return None when no content remains.
    """
    normalized = normalize_text(value)
    if normalized is None:
        return None
    tokens = [token for token in normalized.split() if token not in _LEGAL_SUFFIXES]
    result = " ".join(tokens).strip()
    return result or None


def normalize_description(value: str | None) -> str | None:
    """Apply shared text normalization while preserving description word order and content
    tokens.
    """
    return normalize_text(value)


def normalize_amount(value: Decimal) -> Decimal:
    """Round a Decimal amount to cents with ROUND_HALF_UP for consistent money comparisons."""
    return value.quantize(_CENT, rounding=ROUND_HALF_UP)
