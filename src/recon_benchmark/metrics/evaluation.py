from __future__ import annotations

import math
from collections.abc import Iterable
from statistics import mean

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.metrics.models import AggregateMetrics, CaseEvaluation
from recon_benchmark.ranking.matchers import METHODS, score_pair
from recon_benchmark.ranking.models import CandidateScore
from recon_benchmark.ranking.ordering import rank_candidates
from recon_benchmark.domain.models import BenchmarkCase, MatchingMethod, Scenario


def evaluate_case(
    case: BenchmarkCase,
    *,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> CaseEvaluation:
    # Only the two observable records cross the matcher boundary.
    scored = tuple(
        CandidateScore(
            candidate=candidate.record,
            breakdown=score_pair(
                case.transaction,
                candidate.record,
                method=method,
                config=config,
            ),
        )
        for candidate in case.candidates
    )
    compared_counts = {entry.breakdown.compared_field_count for entry in scored}
    if len(compared_counts) != 1:
        raise ValueError(
            f"{case.case_id}: candidatos comparados com números de campos diferentes: "
            f"{sorted(compared_counts)}."
        )

    ranked = rank_candidates(scored)
    true_entry = next(entry for entry in ranked if entry.candidate.id == case.true_candidate_id)
    scores = [entry.breakdown.total for entry in ranked]
    top_score = max(scores)
    true_score = true_entry.breakdown.total
    top_tie_count = sum(
        _same_score(score, top_score, config.tie_epsilon) for score in scores
    )
    unique_top1 = int(
        _same_score(true_score, top_score, config.tie_epsilon) and top_tie_count == 1
    )
    predicted_candidate_id = ranked[0].candidate.id if top_tie_count == 1 else None
    true_rank = average_rank(scores, true_score, epsilon=config.tie_epsilon)

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
        compared_field_count=true_entry.breakdown.compared_field_count,
        true_field_scores=true_entry.breakdown.field_scores,
        true_excluded_fields=true_entry.breakdown.excluded_fields,
    )


def evaluate_cases(
    cases: Iterable[BenchmarkCase],
    *,
    methods: Iterable[MatchingMethod],
    config: ExperimentConfig,
) -> tuple[CaseEvaluation, ...]:
    method_list = tuple(methods)
    unknown = set(method_list) - set(METHODS)
    if unknown:
        raise ValueError(f"Métodos desconhecidos: {sorted(str(item) for item in unknown)}")
    return tuple(
        evaluate_case(case, method=method, config=config)
        for case in cases
        for method in method_list
    )


def average_rank(
    scores: Iterable[float],
    target_score: float,
    *,
    epsilon: float = 1e-12,
) -> float:
    score_list = list(scores)
    better = sum(
        score > target_score and not _same_score(score, target_score, epsilon)
        for score in score_list
    )
    equal = sum(_same_score(score, target_score, epsilon) for score in score_list)
    if equal == 0:
        raise ValueError("O target_score não existe na lista de scores.")
    first_position = better + 1
    last_position = better + equal
    return (first_position + last_position) / 2.0


def aggregate_by_seed_scenario(
    evaluations: Iterable[CaseEvaluation],
) -> tuple[AggregateMetrics, ...]:
    groups: dict[tuple[int, MatchingMethod, Scenario], list[CaseEvaluation]] = {}
    for evaluation in evaluations:
        key = (evaluation.seed, evaluation.method, evaluation.scenario)
        groups.setdefault(key, []).append(evaluation)

    results: list[AggregateMetrics] = []
    for (seed, method, scenario), items in sorted(
        groups.items(),
        key=lambda item: (item[0][0], item[0][1].value, item[0][2].value),
    ):
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
    groups: dict[tuple[int, MatchingMethod], list[CaseEvaluation]] = {}
    for evaluation in evaluations:
        groups.setdefault((evaluation.seed, evaluation.method), []).append(evaluation)

    results: list[AggregateMetrics] = []
    for (seed, method), items in sorted(
        groups.items(),
        key=lambda item: (item[0][0], item[0][1].value),
    ):
        results.append(
            AggregateMetrics(
                seed=seed,
                method=method,
                scenario=None,
                cases=len(items),
                unique_top1=mean(item.unique_top1 for item in items),
                mrr=mean(item.reciprocal_rank for item in items),
                tie_rate=mean(int(item.top_tie_count > 1) for item in items),
            )
        )
    return tuple(results)


def _same_score(left: float, right: float, epsilon: float) -> bool:
    return math.isclose(left, right, rel_tol=0.0, abs_tol=epsilon)
