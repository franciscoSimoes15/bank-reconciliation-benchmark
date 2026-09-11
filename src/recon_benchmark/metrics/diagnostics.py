"""Post-hoc diagnostics of frozen scores; operation labels never enter matching."""

from __future__ import annotations

import csv
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from statistics import mean, stdev
from typing import Literal

from recon_benchmark.domain.codes import method_code
from recon_benchmark.domain.models import AccountingRecord, BenchmarkCase, MatchingMethod, OperationType, Scenario
from recon_benchmark.metrics.models import CaseEvaluation
from recon_benchmark.templates.accounting import ACCOUNTING_DESCRIPTIONS

_ABLATION_METHODS = (MatchingMethod.FIELD_AWARE, MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION)


@dataclass(frozen=True, slots=True)
class OperationDiagnostic:
    """Counts pool case variants; seed_mean metrics give each seed equal weight.

    base_events counts distinct (seed, event_id) pairs, not independent case
    variants. Standard deviations apply only to the seed_mean aggregation.
    """

    aggregation: Literal["per_seed", "pooled_cases", "seed_mean"]
    seed: int | None
    method: MatchingMethod
    operation_group: str
    seeds: int
    cases: int
    base_events: int
    unique_top1_cases: int
    top_tie_cases: int
    unique_top1: float
    mrr: float
    tie_rate: float
    unique_top1_std: float | None = None
    mrr_std: float | None = None
    tie_rate_std: float | None = None


@dataclass(frozen=True, slots=True)
class AmountPairDiagnostic:
    """Paired P0/P1 changes in recorded outcomes, not the complete candidate order."""

    aggregation: Literal["per_seed", "pooled_pairs"]
    seed: int | None
    method: MatchingMethod
    seeds: int
    pairs: int
    true_average_rank_changed: int
    unique_top1_changed: int
    top_tie_count_changed: int


def infer_operation_type(record: AccountingRecord) -> OperationType:
    """Identify a frozen accounting template and validate its optional fields.

    This reporting-only inference is deliberately restricted to the benchmark's
    known templates. Reject unsupported input rather than guess an operation.
    """
    matches = [operation for operation, templates in ACCOUNTING_DESCRIPTIONS.items()
               if record.description in templates]
    if len(matches) != 1:
        raise ValueError(f"Unsupported or ambiguous accounting template: {record.description!r}")
    operation = matches[0]
    expected = (operation not in {OperationType.CARD_PAYMENT, OperationType.BANK_FEE},
                operation is not OperationType.BANK_FEE)
    if (record.reference is not None, record.entity is not None) != expected:
        raise ValueError(f"Inconsistent field availability for {operation.value}.")
    return operation


def _join_cases(
    cases: Iterable[BenchmarkCase], evaluations: Iterable[CaseEvaluation],
) -> tuple[tuple[BenchmarkCase, CaseEvaluation], ...]:
    case_lookup: dict[tuple[int, str], BenchmarkCase] = {}
    for case in cases:
        key = (case.seed, case.case_id)
        if key in case_lookup:
            raise ValueError(f"Duplicate benchmark case: {key}")
        case_lookup[key] = case
    result: list[tuple[BenchmarkCase, CaseEvaluation]] = []
    seen: set[tuple[int, str, MatchingMethod]] = set()
    for evaluation in evaluations:
        key = (evaluation.seed, evaluation.case_id)
        case = case_lookup.get(key)
        if case is None or (case.scenario, case.true_candidate_id) != (
            evaluation.scenario, evaluation.true_candidate_id
        ):
            raise ValueError(f"Evaluation does not match its benchmark case: {key}")
        evaluation_key = (*key, evaluation.method)
        if evaluation_key in seen:
            raise ValueError(f"Duplicate case evaluation: {evaluation_key}")
        seen.add(evaluation_key)
        result.append((case, evaluation))
    return tuple(result)


def aggregate_operation_diagnostics(
    cases: Iterable[BenchmarkCase], evaluations: Iterable[CaseEvaluation],
) -> tuple[OperationDiagnostic, ...]:
    """Summarize M4/M4-D across scenarios by operation and fee exclusion.

    Per-seed and pooled rows average cases. seed_mean rows average the per-seed
    metrics and report their sample SD; their counts still describe all cases.
    Absent operation groups produce no row, never an artificial zero result.
    """
    groups: dict[tuple[MatchingMethod, str], list[tuple[BenchmarkCase, CaseEvaluation]]] = defaultdict(list)
    for case, evaluation in _join_cases(cases, evaluations):
        if evaluation.method not in _ABLATION_METHODS:
            continue
        operation = infer_operation_type(case.true_candidate())
        labels: tuple[str, ...] = (operation.value, "ALL")
        if operation is not OperationType.BANK_FEE:
            labels += ("non_bank_fee",)
        for label in labels:
            groups[(evaluation.method, label)].append((case, evaluation))

    result: list[OperationDiagnostic] = []
    for (method, label), items in sorted(groups.items(), key=lambda item: (method_code(item[0][0]), item[0][1])):
        by_seed: dict[int, list[tuple[BenchmarkCase, CaseEvaluation]]] = defaultdict(list)
        for case, evaluation in items:
            by_seed[case.seed].append((case, evaluation))
        seed_rows = [_operation_row("per_seed", seed, method, label, seed_items)
                     for seed, seed_items in sorted(by_seed.items())]
        result.extend(seed_rows)
        pooled = _operation_row("pooled_cases", None, method, label, items)
        result.append(pooled)
        result.append(OperationDiagnostic(
            aggregation="seed_mean", seed=None, method=method, operation_group=label,
            seeds=pooled.seeds, cases=pooled.cases, base_events=pooled.base_events,
            unique_top1_cases=pooled.unique_top1_cases, top_tie_cases=pooled.top_tie_cases,
            unique_top1=mean(row.unique_top1 for row in seed_rows),
            mrr=mean(row.mrr for row in seed_rows),
            tie_rate=mean(row.tie_rate for row in seed_rows),
            unique_top1_std=_sample_std(row.unique_top1 for row in seed_rows),
            mrr_std=_sample_std(row.mrr for row in seed_rows),
            tie_rate_std=_sample_std(row.tie_rate for row in seed_rows),
        ))
    return tuple(result)


def _operation_row(
    aggregation: Literal["per_seed", "pooled_cases"], seed: int | None,
    method: MatchingMethod, label: str, items: list[tuple[BenchmarkCase, CaseEvaluation]],
) -> OperationDiagnostic:
    return OperationDiagnostic(
        aggregation=aggregation, seed=seed, method=method, operation_group=label,
        seeds=len({case.seed for case, _ in items}), cases=len(items),
        base_events=len({(case.seed, case.event_id) for case, _ in items}),
        unique_top1_cases=sum(evaluation.unique_top1 for _, evaluation in items),
        top_tie_cases=sum(evaluation.top_tie_count > 1 for _, evaluation in items),
        unique_top1=mean(evaluation.unique_top1 for _, evaluation in items),
        mrr=mean(evaluation.reciprocal_rank for _, evaluation in items),
        tie_rate=mean(int(evaluation.top_tie_count > 1) for _, evaluation in items),
    )


def aggregate_amount_pair_diagnostics(
    cases: Iterable[BenchmarkCase], evaluations: Iterable[CaseEvaluation],
) -> tuple[AmountPairDiagnostic, ...]:
    """Pair P0/P1 for each evaluated method; reject missing or inconsistent pairs."""
    pairs: dict[tuple[int, str, MatchingMethod], dict[Scenario, tuple[BenchmarkCase, CaseEvaluation]]] = defaultdict(dict)
    for case, evaluation in _join_cases(cases, evaluations):
        if case.scenario not in {Scenario.NATURAL_VARIATION, Scenario.AMOUNT_VARIATION}:
            continue
        key = (case.seed, case.event_id, evaluation.method)
        if case.scenario in pairs[key]:
            raise ValueError(f"Duplicate amount scenario for event: {key}")
        pairs[key][case.scenario] = (case, evaluation)
    changes: dict[tuple[MatchingMethod, int], list[tuple[bool, bool, bool]]] = defaultdict(list)
    for (seed, event_id, method), variants in pairs.items():
        if set(variants) != {Scenario.NATURAL_VARIATION, Scenario.AMOUNT_VARIATION}:
            raise ValueError(f"Incomplete P0/P1 pair: {(seed, event_id, method)}")
        natural_case, natural = variants[Scenario.NATURAL_VARIATION]
        amount_case, amount = variants[Scenario.AMOUNT_VARIATION]
        if natural_case.candidates != amount_case.candidates or natural_case.true_candidate_id != amount_case.true_candidate_id:
            raise ValueError(f"Candidate set changed in P0/P1 pair: {(seed, event_id)}")
        if natural_case.transaction.amount == amount_case.transaction.amount:
            raise ValueError(f"Amount perturbation is a no-op: {(seed, event_id)}")
        changes[(method, seed)].append((natural.true_rank != amount.true_rank,
                                      natural.unique_top1 != amount.unique_top1,
                                      natural.top_tie_count != amount.top_tie_count))
    result: list[AmountPairDiagnostic] = []
    pooled: dict[MatchingMethod, list[tuple[bool, bool, bool]]] = defaultdict(list)
    for (method, seed), items in sorted(changes.items(), key=lambda item: (method_code(item[0][0]), item[0][1])):
        result.append(_amount_row("per_seed", seed, method, 1, items))
        pooled[method].extend(items)
    for method, items in pooled.items():
        result.append(_amount_row("pooled_pairs", None, method,
                                  sum(group_method == method for group_method, _ in changes), items))
    return tuple(result)


def _amount_row(
    aggregation: Literal["per_seed", "pooled_pairs"], seed: int | None,
    method: MatchingMethod, seeds: int, items: list[tuple[bool, bool, bool]],
) -> AmountPairDiagnostic:
    return AmountPairDiagnostic(aggregation, seed, method, seeds, len(items),
                                sum(item[0] for item in items), sum(item[1] for item in items),
                                sum(item[2] for item in items))


def _sample_std(values: Iterable[float]) -> float:
    items = tuple(values)
    return stdev(items) if len(items) > 1 else 0.0


def write_operation_diagnostics(
    cases: Iterable[BenchmarkCase], evaluations: Iterable[CaseEvaluation], path: str | Path,
) -> Path:
    """Write descriptive operation summaries without changing frozen evaluations."""
    return _write_rows(aggregate_operation_diagnostics(cases, evaluations), OperationDiagnostic, path)


def write_amount_pair_diagnostics(
    cases: Iterable[BenchmarkCase], evaluations: Iterable[CaseEvaluation], path: str | Path,
) -> Path:
    """Write paired amount outcomes with explicit event-pair denominators."""
    return _write_rows(aggregate_amount_pair_diagnostics(cases, evaluations), AmountPairDiagnostic, path)


def _write_rows(
    rows: Iterable[OperationDiagnostic | AmountPairDiagnostic],
    row_type: type[OperationDiagnostic] | type[AmountPairDiagnostic], path: str | Path,
) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[field.name for field in fields(row_type)] + ["method_code"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**asdict(row), "method_code": method_code(row.method)})
    return output
