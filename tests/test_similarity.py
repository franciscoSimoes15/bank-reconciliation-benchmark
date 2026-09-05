import pytest

from recon_benchmark.ranking.similarity import (
    jaro_winkler_similarity,
    qgram_cosine_similarity,
    qgram_counts,
)


def test_jaro_winkler_identity_and_typo() -> None:
    """Check identical strings score 1 while a transposition receives partial similarity."""
    assert jaro_winkler_similarity("acme", "acme") == 1.0
    assert 0.0 < jaro_winkler_similarity("portugal", "portugla") < 1.0


def test_qgram_counts_use_boundary_markers() -> None:
    """Verify start/end markers contribute to the exact expected trigram counts."""
    assert qgram_counts("acme", 3) == {"^ac": 1, "acm": 1, "cme": 1, "me$": 1}


def test_qgram_similarity_identity_and_difference() -> None:
    """Check q-gram cosine recognizes identical text and penalizes unrelated strings."""
    assert qgram_cosine_similarity("acme", "acme", 3) == pytest.approx(1.0)
    assert qgram_cosine_similarity("acme", "vector", 3) < 0.5


def test_qgram_rejects_invalid_q() -> None:
    """Ensure nonpositive fragment lengths raise instead of producing invalid feature counts."""
    with pytest.raises(ValueError):
        qgram_counts("abc", 0)
