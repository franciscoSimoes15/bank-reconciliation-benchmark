from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.matchers import METHODS, score_pair
from recon_benchmark.models import AccountingRecord, BankTransaction


@pytest.fixture
def pair() -> tuple[BankTransaction, AccountingRecord]:
    transaction = BankTransaction(
        id="B1",
        date=date(2026, 5, 12),
        amount=Decimal("-1245.30"),
        reference="FT 2026 00187",
        counterparty="ÓRBITA SERVIÇOS LDA",
        description="TRF P/ ÓRBITA SERVIÇOS, LDA REF FT2026/00187",
    )
    candidate = AccountingRecord(
        id="A1",
        date=date(2026, 5, 12),
        amount=Decimal("-1245.30"),
        reference="FT2026/00187",
        entity="ORBITA SERVICOS LDA",
        description="TRF P/ ORBITA SERVICOS LDA REF FT2026/00187",
    )
    return transaction, candidate


def test_all_scores_stay_in_range(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    for method in METHODS:
        result = score_pair(transaction, candidate, method=method, config=config)
        assert 0.0 <= result.total <= 1.0
        assert all(0.0 <= score <= 1.0 for score in result.field_scores.values())


def test_m0_benefits_from_normalization(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    result = score_pair(transaction, candidate, method="M0", config=config)
    assert result.total == pytest.approx(1.0)


def test_m1_accepts_protocol_amount_and_date_tolerances(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    changed = replace(
        transaction,
        amount=transaction.amount + Decimal("0.10"),
        date=transaction.date + timedelta(days=3),
    )
    result = score_pair(changed, candidate, method="M1", config=config)
    assert result.total == pytest.approx(1.0)


def test_missing_text_field_is_excluded_not_zero(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    missing = replace(transaction, reference=None)
    result = score_pair(missing, candidate, method="M4", config=config)
    assert "reference" in result.excluded_fields
    assert "reference" not in result.field_scores
    assert result.total == pytest.approx(sum(result.field_scores.values()) / len(result.field_scores))


def test_m4_no_norm_exposes_preprocessing_effect(pair: tuple[BankTransaction, AccountingRecord]) -> None:
    config = ExperimentConfig()
    transaction, candidate = pair
    normalized = score_pair(transaction, candidate, method="M4", config=config)
    raw = score_pair(transaction, candidate, method="M4-noNorm", config=config)
    assert normalized.total >= raw.total
