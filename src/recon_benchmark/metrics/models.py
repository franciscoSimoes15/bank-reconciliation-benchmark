"""Resultados por caso e métricas agregadas da avaliação."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import MatchingMethod, Scenario


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    """Evaluation evidence for one case and one matching method.

    Store the true candidate's score, average rank, reciprocal rank and field details.
    unique_top1 is 0 or 1; top_tie_count counts candidates tied for the maximum.
    predicted_candidate_id is None when the top position is ambiguous.
    Ground-truth metadata here is used after scoring.
    """
    seed: int
    case_id: str
    scenario: Scenario
    method: MatchingMethod
    true_candidate_id: str
    predicted_candidate_id: str | None
    true_score: float
    top_score: float
    true_rank: float
    reciprocal_rank: float
    unique_top1: int
    top_tie_count: int
    compared_field_count: int
    true_field_scores: dict[str, float]
    true_excluded_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AggregateMetrics:
    """Mean ranking performance for a method within a single seed.

    scenario=None denotes all scenarios pooled for that seed. cases is the group
    size; unique_top1 and tie_rate are proportions, and mrr is the mean reciprocal
    rank. Aggregation across evaluation seeds happens in reporting.
    """
    seed: int
    method: MatchingMethod
    scenario: Scenario | None
    cases: int
    unique_top1: float
    mrr: float
    tie_rate: float
