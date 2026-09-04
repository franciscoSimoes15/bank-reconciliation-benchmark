from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import mean
from typing import Iterable

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.matchers import METHODS, MethodName, ScoreBreakdown, score_pair
from recon_benchmark.models import AccountingRecord, BenchmarkCase

_SCORE_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate: AccountingRecord
    breakdown: ScoreBreakdown


@dataclass(frozen=True, slots=True)
class CaseEvaluation:
    seed: int
    case_id: str
    scenario: str
    method: MethodName
    true_candidate_id: str
    predicted_candidate_id: str | None
    true_score: float
    top_score: float
    true_rank: float
    reciprocal_rank: float
    unique_top1: int
    top_tie_count: int
    true_field_scores: dict[str, float]
    true_excluded_fields: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AggregateMetrics:
    seed: int
    method: str
    scenario: str
    cases: int
    unique_top1: float
    mrr: float
    tie_rate: float


def evaluate_case(
    case: BenchmarkCase,
    *,
    method: MethodName,
    config: ExperimentConfig,
) -> CaseEvaluation:
    scored = tuple(
        CandidateScore(
            candidate=candidate,
            breakdown=score_pair(case.transaction, candidate, method=method, config=config),
        )
        for candidate in case.candidates
    )
    ranked = rank_candidates(scored)
    true_entry = next(entry for entry in ranked if entry.candidate.id == case.true_candidate_id)
    scores = [entry.breakdown.total for entry in ranked]
    top_score = max(scores)
    true_score = true_entry.breakdown.total
    top_tie_count = sum(_same_score(score, top_score) for score in scores)
    unique_top1 = int(_same_score(true_score, top_score) and top_tie_count == 1)
    predicted_candidate_id = ranked[0].candidate.id if top_tie_count == 1 else None
    true_rank = average_rank(scores, true_score)

    return CaseEvaluation(
        seed=case.seed,
        case_id=case.case_id,
        scenario=case.scenario,
        method=method,
        true_candidate_id=case.true_candidate_id,
        predicted_candidate_id=predicted_candidate_id,
        true_score=true_score,
        top_score=top_score,
        true_rank=true_rank,
        reciprocal_rank=1.0 / true_rank,
        unique_top1=unique_top1,
        top_tie_count=top_tie_count,
        true_field_scores=true_entry.breakdown.field_scores,
        true_excluded_fields=true_entry.breakdown.excluded_fields,
    )


def evaluate_cases(
    cases: Iterable[BenchmarkCase],
    *,
    methods: Iterable[MethodName],
    config: ExperimentConfig,
) -> tuple[CaseEvaluation, ...]:
    method_list = tuple(methods)
    unknown = set(method_list) - set(METHODS)
    if unknown:
        raise ValueError(f"Métodos desconhecidos: {sorted(unknown)}")
    return tuple(
        evaluate_case(case, method=method, config=config)
        for case in cases
        for method in method_list
    )


def rank_candidates(scored: Iterable[CandidateScore]) -> tuple[CandidateScore, ...]:
    return tuple(
        sorted(
            scored,
            key=lambda entry: (-entry.breakdown.total, entry.candidate.id),
        )
    )


def average_rank(scores: Iterable[float], target_score: float) -> float:
    score_list = list(scores)
    better = sum(score > target_score and not _same_score(score, target_score) for score in score_list)
    equal = sum(_same_score(score, target_score) for score in score_list)
    if equal == 0:
        raise ValueError("O target_score não existe na lista de scores.")
    first_position = better + 1
    last_position = better + equal
    return (first_position + last_position) / 2.0


def aggregate_by_seed_scenario(
    evaluations: Iterable[CaseEvaluation],
) -> tuple[AggregateMetrics, ...]:
    groups: dict[tuple[int, str, str], list[CaseEvaluation]] = {}
    for evaluation in evaluations:
        key = (evaluation.seed, evaluation.method, evaluation.scenario)
        groups.setdefault(key, []).append(evaluation)

    results: list[AggregateMetrics] = []
    for (seed, method, scenario), items in sorted(groups.items()):
        results.append(
            AggregateMetrics(
                seed=seed,
                method=method,
                scenario=scenario,
                cases=len(items),
                unique_top1=mean(item.unique_top1 for item in items),
                mrr=mean(item.reciprocal_rank for item in items),
                tie_rate=mean(int(item.top_tie_count > 1) for item in items),
            )
        )
    return tuple(results)


def aggregate_overall_by_seed(
    evaluations: Iterable[CaseEvaluation],
) -> tuple[AggregateMetrics, ...]:
    groups: dict[tuple[int, str], list[CaseEvaluation]] = {}
    for evaluation in evaluations:
        groups.setdefault((evaluation.seed, evaluation.method), []).append(evaluation)

    results: list[AggregateMetrics] = []
    for (seed, method), items in sorted(groups.items()):
        results.append(
            AggregateMetrics(
                seed=seed,
                method=method,
                scenario="ALL",
                cases=len(items),
                unique_top1=mean(item.unique_top1 for item in items),
                mrr=mean(item.reciprocal_rank for item in items),
                tie_rate=mean(int(item.top_tie_count > 1) for item in items),
            )
        )
    return tuple(results)


def _same_score(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=_SCORE_EPSILON)
