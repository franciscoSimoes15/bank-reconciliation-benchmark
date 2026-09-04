from datetime import date
from decimal import Decimal

import pytest

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.evaluation import average_rank, evaluate_case
from recon_benchmark.models import AccountingRecord, BankTransaction, BenchmarkCase


def test_average_rank_handles_ties() -> None:
    assert average_rank([1.0, 1.0, 0.5], 1.0) == pytest.approx(1.5)
    assert average_rank([1.0, 0.8, 0.8, 0.2], 0.8) == pytest.approx(2.5)


def test_unique_top1_rejects_top_tie() -> None:
    transaction = BankTransaction(
        id="B",
        date=date(2026, 1, 1),
        amount=Decimal("100.00"),
        reference=None,
        counterparty=None,
        description=None,
    )
    true_candidate = AccountingRecord(
        id="TRUE",
        date=date(2026, 1, 1),
        amount=Decimal("100.00"),
        reference="A",
        entity="X",
        description="ONE",
    )
    false_candidate = AccountingRecord(
        id="FALSE",
        date=date(2026, 1, 1),
        amount=Decimal("100.00"),
        reference="B",
        entity="Y",
        description="TWO",
    )
    case = BenchmarkCase(
        case_id="C",
        seed=7,
        scenario="P6_MISSING_INFORMATION",
        transaction=transaction,
        candidates=(true_candidate, false_candidate),
        true_candidate_id="TRUE",
        perturbations=("missing:reference", "missing:counterparty", "missing:description"),
    )
    result = evaluate_case(case, method="M0", config=ExperimentConfig())
    assert result.unique_top1 == 0
    assert result.top_tie_count == 2
    assert result.true_rank == pytest.approx(1.5)


def test_tolerance_recovers_amount_noise_that_exact_cannot_resolve_uniquely() -> None:
    from recon_benchmark.generator import generate_benchmark

    config = ExperimentConfig()
    case = next(
        item
        for item in generate_benchmark(seed=7, cases_per_scenario=1, config=config)
        if item.scenario == "P1_AMOUNT_NOISE"
    )
    exact = evaluate_case(case, method="M0", config=config)
    tolerant = evaluate_case(case, method="M1", config=config)
    assert exact.unique_top1 == 0
    assert tolerant.unique_top1 == 1
