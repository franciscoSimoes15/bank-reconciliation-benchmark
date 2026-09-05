"""Ordenação dos candidatos pelos scores observáveis, sem ground truth."""

from __future__ import annotations

from collections.abc import Iterable

from recon_benchmark.ranking.models import CandidateScore


def rank_candidates(scored: Iterable[CandidateScore]) -> tuple[CandidateScore, ...]:
    return tuple(
        sorted(
            scored,
            key=lambda entry: (-entry.breakdown.total, entry.candidate.id),
        )
    )
