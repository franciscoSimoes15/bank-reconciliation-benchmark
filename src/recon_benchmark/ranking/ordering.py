"""Ordenação dos candidatos pelos scores observáveis, sem ground truth."""

from __future__ import annotations

from collections.abc import Iterable

from recon_benchmark.ranking.models import CandidateScore


def rank_candidates(scored: Iterable[CandidateScore]) -> tuple[CandidateScore, ...]:
    """Return candidates sorted by descending total score, then ID for deterministic display.

    The ID orders equal scores only; it does not make a tie a unique prediction.
    Evaluation computes average-rank ties from scores independently of this order.
    """
    return tuple(
        sorted(
            scored,
            key=lambda entry: (-entry.breakdown.total, entry.candidate.id),
        )
    )
