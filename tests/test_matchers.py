import inspect
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.ranking.matchers import (
    METHODS,
    score_pair,
    structured_reference_similarity,
)
from recon_benchmark.domain.models import AccountingRecord, BankTransaction, MatchingMethod
from recon_benchmark.domain.codes import method_code
from recon_benchmark.ranking.similarity import jaro_winkler_similarity


@pytest.fixture
def pair() -> tuple[BankTransaction, AccountingRecord]:
    transaction = BankTransaction(
        id="B1",
        date=date(2026, 5, 12),
        amount=Decimal("-1245.30"),
        reference="FT 2026 00187",
        counterparty="ÓRBITA SERVIÇOS LDA",
        description="TRF PARA ORBITA SERVICOS",
    )
    candidate = AccountingRecord(
        id="A1",
        date=date(2026, 5, 12),
        amount=Decimal("-1245.30"),
        reference="FT2026/00187",
        entity="ORBITA SERVICOS LDA",
        description="TRF PARA ÓRBITA SERVIÇOS",
    )
    return transaction, candidate


def test_methods_use_descriptive_strenum_names_and_output_codes() -> None:
    assert METHODS == tuple(MatchingMethod)
    assert [method_code(method) for method in METHODS] == [
        "M0",
        "M1",
        "M2",
        "M3",
        "M4",
        "M4-D",
    ]
    assert MatchingMethod.FIELD_AWARE.value == "field_aware"


def test_all_scores_stay_in_range(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    for method in METHODS:
        result = score_pair(transaction, candidate, method=method, config=config)
        assert 0.0 <= result.total <= 1.0
        assert all(0.0 <= score <= 1.0 for score in result.field_scores.values())


def test_normalized_exact_uses_field_normalization(
    pair: tuple[BankTransaction, AccountingRecord],
) -> None:
    transaction, candidate = pair
    result = score_pair(
        transaction,
        candidate,
        method=MatchingMethod.NORMALIZED_EXACT,
        config=ExperimentConfig(),
    )
    assert result.total == pytest.approx(1.0)


def test_tolerant_deterministic_uses_binary_amount_and_date_rules(
    pair: tuple[BankTransaction, AccountingRecord],
) -> None:
    transaction, candidate = pair
    config = ExperimentConfig()
    at_threshold = replace(
        transaction,
        amount=transaction.amount + Decimal("0.10"),
        date=transaction.date + timedelta(days=3),
    )
    outside_threshold = replace(
        transaction,
        amount=transaction.amount + Decimal("0.11"),
        date=transaction.date + timedelta(days=4),
    )
    accepted = score_pair(
        at_threshold,
        candidate,
        method=MatchingMethod.TOLERANT_DETERMINISTIC,
        config=config,
    )
    rejected = score_pair(
        outside_threshold,
        candidate,
        method=MatchingMethod.TOLERANT_DETERMINISTIC,
        config=config,
    )
    assert accepted.field_scores["amount"] == 1.0
    assert accepted.field_scores["date"] == 1.0
    assert rejected.field_scores["amount"] == 0.0
    assert rejected.field_scores["date"] == 0.0


@pytest.mark.parametrize(
    "method",
    [
        MatchingMethod.JARO_WINKLER_TEXT,
        MatchingMethod.CHARACTER_TRIGRAM_TEXT,
        MatchingMethod.FIELD_AWARE,
        MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION,
    ],
)
def test_ranking_methods_use_gradual_amount_and_date_proximity(
    pair: tuple[BankTransaction, AccountingRecord],
    method: MatchingMethod,
) -> None:
    transaction, candidate = pair
    near = replace(
        transaction,
        amount=transaction.amount + Decimal("0.25"),
        date=transaction.date + timedelta(days=5),
    )
    far = replace(
        transaction,
        amount=transaction.amount + Decimal("8.00"),
        date=transaction.date + timedelta(days=20),
    )
    exact_score = score_pair(transaction, candidate, method=method, config=ExperimentConfig())
    near_score = score_pair(near, candidate, method=method, config=ExperimentConfig())
    far_score = score_pair(far, candidate, method=method, config=ExperimentConfig())
    assert exact_score.field_scores["amount"] > near_score.field_scores["amount"] > far_score.field_scores["amount"]
    assert exact_score.field_scores["date"] > near_score.field_scores["date"] > far_score.field_scores["date"]


def test_field_aware_reference_comparison_penalizes_document_number_conflict() -> None:
    left = "ft202600187"
    wrong_number = "ft202600188"
    assert structured_reference_similarity(left, wrong_number) == pytest.approx(0.30)
    assert structured_reference_similarity(left, wrong_number) < jaro_winkler_similarity(
        left, wrong_number
    )


def test_missing_field_is_excluded_and_counted(
    pair: tuple[BankTransaction, AccountingRecord],
) -> None:
    transaction, candidate = pair
    result = score_pair(
        replace(transaction, reference=None, counterparty=None),
        candidate,
        method=MatchingMethod.FIELD_AWARE,
        config=ExperimentConfig(),
    )
    assert set(result.excluded_fields) == {"reference", "entity"}
    assert result.compared_field_count == 3
    assert result.total == pytest.approx(
        sum(result.field_scores.values()) / result.compared_field_count
    )


def test_missing_optional_fields_cannot_cause_division_by_zero(
    pair: tuple[BankTransaction, AccountingRecord],
) -> None:
    transaction, candidate = pair
    result = score_pair(
        replace(transaction, reference=None, counterparty=None),
        replace(candidate, reference=None, entity=None),
        method=MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION,
        config=ExperimentConfig(),
    )
    assert result.compared_field_count == 2
    assert 0.0 <= result.total <= 1.0


def test_field_aware_ablation_excludes_description(
    pair: tuple[BankTransaction, AccountingRecord],
) -> None:
    transaction, candidate = pair
    result = score_pair(
        transaction,
        candidate,
        method=MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION,
        config=ExperimentConfig(),
    )
    assert "description" in result.excluded_fields
    assert "description" not in result.field_scores


def test_matcher_signature_cannot_receive_ground_truth_or_generator_metadata() -> None:
    parameters = set(inspect.signature(score_pair).parameters)
    forbidden = {
        "event_id",
        "true_candidate_id",
        "scenario",
        "perturbations",
        "candidate_origin",
    }
    assert parameters == {"transaction", "candidate", "method", "config"}
    assert not parameters & forbidden
