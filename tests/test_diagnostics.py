import csv
from dataclasses import replace
from pathlib import Path

import pytest

from recon_benchmark.domain.models import BenchmarkCase, MatchingMethod, OperationType, Scenario
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark
from recon_benchmark.metrics import evaluation as evaluation_module
from recon_benchmark.metrics.diagnostics import (
    aggregate_amount_pair_diagnostics,
    aggregate_operation_diagnostics,
    infer_operation_type,
    write_amount_pair_diagnostics,
    write_operation_diagnostics,
)
from recon_benchmark.metrics.models import CaseEvaluation


@pytest.fixture
def cases() -> tuple[BenchmarkCase, ...]:
    return tuple(case for seed in (7, 8) for case in generate_benchmark(
        seed=seed, cases_per_scenario=6, config=ExperimentConfig(),
    ))


def _result(
    case: BenchmarkCase, *, method: MatchingMethod = MatchingMethod.FIELD_AWARE,
    tied: bool = False,
) -> CaseEvaluation:
    return CaseEvaluation(
        seed=case.seed, case_id=case.case_id, scenario=case.scenario, method=method,
        true_candidate_id=case.true_candidate_id,
        predicted_candidate_id=None if tied else case.true_candidate_id,
        true_score=1.0, top_score=1.0, true_rank=1.5 if tied else 1.0,
        reciprocal_rank=2 / 3 if tied else 1.0, unique_top1=int(not tied),
        top_tie_count=2 if tied else 1, compared_field_count=3,
        true_field_scores={"amount": 1.0, "date": 1.0, "description": 1.0},
        true_excluded_fields=("reference", "entity"),
    )


def test_operation_inference_covers_all_families_and_rejects_unsupported_input(
    cases: tuple[BenchmarkCase, ...],
) -> None:
    assert {infer_operation_type(case.true_candidate()) for case in cases} == set(OperationType)
    record = cases[0].true_candidate()
    with pytest.raises(ValueError, match="Unsupported"):
        infer_operation_type(replace(record, description="UNKNOWN TEMPLATE"))
    fee = next(case.true_candidate() for case in cases
               if infer_operation_type(case.true_candidate()) is OperationType.BANK_FEE)
    with pytest.raises(ValueError, match="availability"):
        infer_operation_type(replace(fee, entity="UNEXPECTED ENTITY"))


def test_operation_metrics_distinguish_pooled_cases_from_equal_seed_means(
    cases: tuple[BenchmarkCase, ...],
) -> None:
    fee_cases = [case for case in cases
                 if infer_operation_type(case.true_candidate()) is OperationType.BANK_FEE]
    seed7 = [case for case in fee_cases if case.seed == 7][:2]
    seed8 = next(case for case in fee_cases if case.seed == 8)
    selected = (*seed7, seed8)
    evaluations = tuple(_result(case, tied=index == 1) for index, case in enumerate(selected))
    rows = aggregate_operation_diagnostics(selected, evaluations)
    fee_rows = [row for row in rows if row.operation_group == "bank_fee"]
    assert len(fee_rows) == 4  # Two seeds, pooled cases, and equal-weight seed mean.
    pooled = next(row for row in fee_rows if row.aggregation == "pooled_cases")
    seed_mean = next(row for row in fee_rows if row.aggregation == "seed_mean")
    assert (pooled.cases, pooled.base_events, pooled.seeds) == (3, 2, 2)
    assert (pooled.unique_top1_cases, pooled.top_tie_cases) == (2, 1)
    assert pooled.unique_top1 == pytest.approx(2 / 3)
    assert pooled.mrr == pytest.approx(8 / 9)
    assert pooled.tie_rate == pytest.approx(1 / 3)
    assert pooled.unique_top1_std is None
    assert seed_mean.unique_top1 == pytest.approx(0.75)
    assert seed_mean.mrr == pytest.approx(11 / 12)
    assert seed_mean.tie_rate == pytest.approx(0.25)
    assert seed_mean.unique_top1_std == pytest.approx(2 ** -1.5)
    assert not any(row.operation_group == "non_bank_fee" for row in rows)


def test_all_operation_groups_and_ablation_are_reported_without_duplicate_fee_rows(
    cases: tuple[BenchmarkCase, ...], tmp_path: Path,
) -> None:
    methods = (MatchingMethod.FIELD_AWARE, MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION)
    evaluations = tuple(_result(case, method=method) for case in cases for method in methods)
    path = write_operation_diagnostics(cases, evaluations, tmp_path / "operations.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    pooled = [row for row in rows if row["aggregation"] == "pooled_cases"]
    assert len(pooled) == 16
    assert {row["operation_group"] for row in pooled} == {
        *(operation.value for operation in OperationType), "non_bank_fee", "ALL",
    }
    for method in ("M4", "M4-D"):
        by_group = {row["operation_group"]: row for row in pooled if row["method_code"] == method}
        assert int(by_group["bank_fee"]["cases"]) == 16
        assert int(by_group["non_bank_fee"]["cases"]) == 80
        assert int(by_group["ALL"]["base_events"]) == 12


def test_amount_pair_counts_detect_changes_and_preserve_pair_denominator(
    cases: tuple[BenchmarkCase, ...], tmp_path: Path,
) -> None:
    selected = tuple(case for case in cases if case.scenario in {
        Scenario.NATURAL_VARIATION, Scenario.AMOUNT_VARIATION,
    })
    evaluations = tuple(_result(case, tied=case.scenario is Scenario.AMOUNT_VARIATION and case.seed == 7)
                        for case in selected)
    rows = aggregate_amount_pair_diagnostics(selected, evaluations)
    pooled = next(row for row in rows if row.aggregation == "pooled_pairs")
    assert (pooled.pairs, pooled.seeds) == (12, 2)
    assert pooled.true_average_rank_changed == 6
    assert pooled.unique_top1_changed == 6
    assert pooled.top_tie_count_changed == 6
    path = write_amount_pair_diagnostics(selected, evaluations, tmp_path / "amount.csv")
    with path.open(encoding="utf-8", newline="") as handle:
        written = list(csv.DictReader(handle))
    assert len(written) == 3
    assert written[-1]["aggregation"] == "pooled_pairs"
    assert written[-1]["method_code"] == "M4"


def test_diagnostics_reject_duplicate_evaluations_and_unpaired_amount_cases(
    cases: tuple[BenchmarkCase, ...],
) -> None:
    case = next(case for case in cases if case.scenario is Scenario.NATURAL_VARIATION)
    evaluation = _result(case)
    with pytest.raises(ValueError, match="Duplicate case evaluation"):
        aggregate_operation_diagnostics((case,), (evaluation, evaluation))
    with pytest.raises(ValueError, match="Incomplete P0/P1"):
        aggregate_amount_pair_diagnostics((case,), (evaluation,))
    amount = next(item for item in cases
                  if item.event_id == case.event_id and item.scenario is Scenario.AMOUNT_VARIATION)
    no_op = replace(amount, transaction=case.transaction)
    with pytest.raises(ValueError, match="no-op"):
        aggregate_amount_pair_diagnostics((case, no_op), (evaluation, _result(no_op)))


def test_operation_diagnostics_do_not_rescore_or_add_matcher_metadata(
    cases: tuple[BenchmarkCase, ...], monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reporting consumes completed evaluations and leaves observable records unchanged."""
    case = cases[0]
    before = case.to_dict()
    evaluation = evaluation_module.evaluate_case(
        case, method=MatchingMethod.FIELD_AWARE, config=ExperimentConfig(),
    )

    def forbidden_rescoring(*args: object, **kwargs: object) -> None:
        raise AssertionError("Post-hoc reporting must not call a matcher")

    monkeypatch.setattr(evaluation_module, "score_pair", forbidden_rescoring)
    rows = aggregate_operation_diagnostics((case,), (evaluation,))
    assert rows
    assert case.to_dict() == before
    assert "operation_type" not in case.transaction.to_dict()
    assert all("operation_type" not in candidate.record.to_dict() for candidate in case.candidates)
