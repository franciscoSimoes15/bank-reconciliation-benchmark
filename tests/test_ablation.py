"""Characterize limitations of the frozen generator using development data only."""

import random
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

import pytest

from recon_benchmark.domain.models import (
    BenchmarkCase,
    CandidateOrigin,
    HardNegativeKind,
    MatchingMethod,
    OperationType,
    Scenario,
)
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark
from recon_benchmark.generation.synthetic_data import (
    generate_financial_event,
    near_document_reference,
    render_accounting_record,
    render_bank_transaction,
)
from recon_benchmark.metrics.evaluation import evaluate_case
from recon_benchmark.ranking.matchers import score_pair
from recon_benchmark.templates.accounting import ACCOUNTING_DESCRIPTIONS


@pytest.fixture(scope="module")
def development_cases() -> tuple[BenchmarkCase, ...]:
    return generate_benchmark(seed=7, cases_per_scenario=12, config=ExperimentConfig())


def test_bank_fee_truth_cannot_be_unique_without_description(
    development_cases: tuple[BenchmarkCase, ...],
) -> None:
    """Removing description makes truth and the first fee hard negative indistinguishable.

    A tied truth can rank below another candidate, so this checks non-uniqueness
    rather than incorrectly requiring the tie to occur at the top in every scenario.
    """
    config = ExperimentConfig()
    method = MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION
    fee_cases = tuple(case for case in development_cases if case.true_candidate().entity is None)
    assert len({case.event_id for case in fee_cases}) == 2
    assert {case.scenario for case in fee_cases} == set(Scenario)
    for case in fee_cases:
        true_record = case.true_candidate()
        hard_record = next(
            candidate.record
            for candidate in case.candidates
            if candidate.hard_negative_kind is HardNegativeKind.AMOUNT_DATE_NEAR_REFERENCE
        )
        assert true_record.description != hard_record.description
        true_score = score_pair(case.transaction, true_record, method=method, config=config)
        hard_score = score_pair(case.transaction, hard_record, method=method, config=config)
        assert true_score.field_scores == hard_score.field_scores
        assert true_score.compared_field_count == hard_score.compared_field_count == 2
        assert true_score.total == hard_score.total
        result = evaluate_case(case, method=method, config=config)
        assert result.unique_top1 == 0
        assert result.true_rank >= 1.5


def test_amount_contribution_is_equal_for_truth_and_all_hard_negatives(
    development_cases: tuple[BenchmarkCase, ...],
) -> None:
    """Amount perturbations cannot separate truth from the three equal-amount hard negatives."""
    config = ExperimentConfig()
    covered: set[tuple[OperationType, Scenario]] = set()
    for case in development_cases:
        if case.scenario not in {Scenario.NATURAL_VARIATION, Scenario.AMOUNT_VARIATION}:
            continue
        operation = next(
            operation
            for operation, descriptions in ACCOUNTING_DESCRIPTIONS.items()
            if case.true_candidate().description in descriptions
        )
        covered.add((operation, case.scenario))
        competitors = tuple(
            candidate.record
            for candidate in case.candidates
            if candidate.origin in {CandidateOrigin.TRUE, CandidateOrigin.CONTROLLED_HARD_NEGATIVE}
        )
        assert len(competitors) == 4
        for method in MatchingMethod:
            amount_scores = {
                score_pair(case.transaction, record, method=method, config=config).field_scores["amount"]
                for record in competitors
            }
            assert len(amount_scores) == 1
            if case.scenario is Scenario.NATURAL_VARIATION:
                assert amount_scores == {1.0}
            elif method is MatchingMethod.FIELD_AWARE:
                assert next(iter(amount_scores)) < 1.0
    assert covered == {
        (operation, scenario)
        for operation in OperationType
        for scenario in (Scenario.NATURAL_VARIATION, Scenario.AMOUNT_VARIATION)
    }


def test_descriptions_do_not_encode_event_specific_facts() -> None:
    """Fixed template choices ignore changed event facts within each operation family.

    This characterizes the published generator; a description ablation therefore
    cannot establish that narratives contain event-specific identifying evidence.
    """
    operations: set[OperationType] = set()
    for index in range(6):
        event = generate_financial_event(random.Random(index), seed=7, index=index, event_id="first")
        operations.add(event.operation_type)
        changed_event = replace(
            event,
            event_id="second",
            event_date=event.event_date + timedelta(days=14),
            amount=event.amount * Decimal("2"),
            entity_legal_name=None if event.entity_legal_name is None else "OUTRA ENTIDADE LDA",
            entity_bank_alias=None if event.entity_bank_alias is None else "Outra Entid",
            document_reference=near_document_reference(event.document_reference, 100),
        )
        bank = render_bank_transaction(event, random.Random(7), transaction_id="bank-first")
        other_bank = render_bank_transaction(changed_event, random.Random(7), transaction_id="bank-second")
        accounting = render_accounting_record(event, random.Random(7), record_id="record-first")
        other_accounting = render_accounting_record(changed_event, random.Random(7), record_id="record-second")
        assert bank.amount != other_bank.amount
        assert bank.date != other_bank.date
        assert accounting.amount != other_accounting.amount
        assert accounting.date != other_accounting.date
        assert bank.description == other_bank.description
        assert accounting.description == other_accounting.description
    assert operations == set(OperationType)
