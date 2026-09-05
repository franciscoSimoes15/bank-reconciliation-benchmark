from datetime import date
from decimal import Decimal

import pytest

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.metrics.evaluation import (
    aggregate_by_seed_scenario,
    aggregate_overall_by_seed,
    average_rank,
    evaluate_case,
)
from recon_benchmark.domain.models import (
    AccountingRecord,
    BankTransaction,
    BenchmarkCandidate,
    BenchmarkCase,
    CandidateOrigin,
    MatchingMethod,
    Scenario,
)


def test_average_rank_handles_ties() -> None:
    assert average_rank([1.0, 1.0, 0.5], 1.0) == pytest.approx(1.5)
    assert average_rank([1.0, 0.8, 0.8, 0.2], 0.8) == pytest.approx(2.5)


def test_unique_top1_rejects_top_tie_and_uses_average_rank() -> None:
    result = evaluate_case(
        _case(case_id="tie", false_is_equal=True),
        method=MatchingMethod.NORMALIZED_EXACT,
        config=ExperimentConfig(),
    )
    assert result.unique_top1 == 0
    assert result.top_tie_count == 2
    assert result.true_rank == pytest.approx(1.5)
    assert result.reciprocal_rank == pytest.approx(2 / 3)


def test_unique_top1_accepts_true_candidate_alone_at_top() -> None:
    result = evaluate_case(
        _case(case_id="unique", false_is_equal=False),
        method=MatchingMethod.NORMALIZED_EXACT,
        config=ExperimentConfig(),
    )
    assert result.unique_top1 == 1
    assert result.top_tie_count == 1
    assert result.true_rank == 1.0
    assert result.reciprocal_rank == 1.0


def test_aggregate_metrics_calculate_unique_top1_mrr_and_tie_rate() -> None:
    evaluations = tuple(
        evaluate_case(
            _case(case_id=case_id, false_is_equal=is_equal),
            method=MatchingMethod.NORMALIZED_EXACT,
            config=ExperimentConfig(),
        )
        for case_id, is_equal in (("tie", True), ("unique", False))
    )
    scenario_metric = aggregate_by_seed_scenario(evaluations)[0]
    overall_metric = aggregate_overall_by_seed(evaluations)[0]
    for metric in (scenario_metric, overall_metric):
        assert metric.unique_top1 == pytest.approx(0.5)
        assert metric.mrr == pytest.approx(5 / 6)
        assert metric.tie_rate == pytest.approx(0.5)


def test_evaluation_rejects_unequal_field_availability_between_candidates() -> None:
    case = _case(case_id="unfair", false_is_equal=False)
    transaction = BankTransaction(
        id=case.transaction.id,
        date=case.transaction.date,
        amount=case.transaction.amount,
        reference="REF-1",
        counterparty=case.transaction.counterparty,
        description=case.transaction.description,
    )
    true_entry, false_entry = case.candidates
    true_with_reference = AccountingRecord(
        id=true_entry.record.id,
        date=true_entry.record.date,
        amount=true_entry.record.amount,
        reference="REF-1",
        entity=true_entry.record.entity,
        description=true_entry.record.description,
    )
    false_without_reference = AccountingRecord(
        id=false_entry.record.id,
        date=false_entry.record.date,
        amount=false_entry.record.amount,
        reference=None,
        entity=false_entry.record.entity,
        description=false_entry.record.description,
    )
    unfair = BenchmarkCase(
        case_id=case.case_id,
        seed=case.seed,
        event_id=case.event_id,
        scenario=case.scenario,
        transaction=transaction,
        candidates=(
            BenchmarkCandidate(
                record=true_with_reference,
                origin=true_entry.origin,
                source_event_id=true_entry.source_event_id,
            ),
            BenchmarkCandidate(
                record=false_without_reference,
                origin=false_entry.origin,
                source_event_id=false_entry.source_event_id,
            ),
        ),
        true_candidate_id=true_with_reference.id,
        perturbations=case.perturbations,
    )
    with pytest.raises(ValueError, match="números de campos diferentes"):
        evaluate_case(
            unfair,
            method=MatchingMethod.FIELD_AWARE,
            config=ExperimentConfig(),
        )


def _case(*, case_id: str, false_is_equal: bool) -> BenchmarkCase:
    transaction = BankTransaction(
        id="bank",
        date=date(2026, 1, 1),
        amount=Decimal("100.00"),
        reference=None,
        counterparty=None,
        description="BANK MOVEMENT",
    )
    true_candidate = AccountingRecord(
        id="true",
        date=date(2026, 1, 1),
        amount=Decimal("100.00"),
        reference="A",
        entity="X",
        description="ACCOUNTING ENTRY",
    )
    false_candidate = AccountingRecord(
        id="false",
        date=date(2026, 1, 1) if false_is_equal else date(2026, 2, 1),
        amount=Decimal("100.00") if false_is_equal else Decimal("200.00"),
        reference="B",
        entity="Y",
        description="OTHER ENTRY",
    )
    return BenchmarkCase(
        case_id=case_id,
        seed=7,
        event_id="event-true",
        scenario=Scenario.MISSING_INFORMATION,
        transaction=transaction,
        candidates=(
            BenchmarkCandidate(
                record=true_candidate,
                origin=CandidateOrigin.TRUE,
                source_event_id="event-true",
            ),
            BenchmarkCandidate(
                record=false_candidate,
                origin=CandidateOrigin.NATURAL_NEGATIVE,
                source_event_id="event-false",
            ),
        ),
        true_candidate_id="true",
        perturbations=("missing:counterparty",),
    )
