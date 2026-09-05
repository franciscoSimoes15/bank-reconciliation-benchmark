"""Resultados por caso e métricas agregadas da avaliação."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import MatchingMethod, Scenario


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
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
    seed: int
    method: MatchingMethod
    scenario: Scenario | None
    cases: int
    unique_top1: float
    mrr: float
    tie_rate: float
