from collections import Counter

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.generator import generate_benchmark, validate_benchmark


def test_generator_creates_expected_scenarios_and_candidate_count() -> None:
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
    assert len(cases) == 16
    assert Counter(case.scenario for case in cases) == {scenario: 2 for scenario in config.scenarios}
    assert all(len(case.candidates) == 10 for case in cases)
    assert not validate_benchmark(cases, config=config, expected_cases_per_scenario=2)


def test_generator_is_reproducible() -> None:
    config = ExperimentConfig()
    first = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    second = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    assert [case.to_dict() for case in first] == [case.to_dict() for case in second]


def test_different_seeds_produce_different_cases() -> None:
    config = ExperimentConfig()
    first = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    second = generate_benchmark(seed=8, cases_per_scenario=1, config=config)
    assert [case.to_dict() for case in first] != [case.to_dict() for case in second]


def test_isolated_scenarios_change_only_expected_transaction_fields() -> None:
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    by_scenario = {case.scenario: case for case in cases}

    amount = by_scenario["P1_AMOUNT_NOISE"]
    amount_true = amount.true_candidate()
    assert amount.transaction.amount != amount_true.amount
    assert amount.transaction.date == amount_true.date
    assert amount.transaction.reference == amount_true.reference
    assert amount.transaction.counterparty == amount_true.entity
    assert amount.transaction.description == amount_true.description

    date = by_scenario["P2_DATE_DRIFT"]
    date_true = date.true_candidate()
    assert date.transaction.date != date_true.date
    assert date.transaction.amount == date_true.amount

    reference = by_scenario["P3_REFERENCE_NOISE"]
    reference_true = reference.true_candidate()
    assert reference.transaction.reference != reference_true.reference
    assert reference.transaction.amount == reference_true.amount
    assert reference.transaction.date == reference_true.date

    entity = by_scenario["P4_ENTITY_NOISE"]
    entity_true = entity.true_candidate()
    assert entity.transaction.counterparty != entity_true.entity
    assert entity.transaction.reference == entity_true.reference

    description = by_scenario["P5_DESCRIPTION_NOISE"]
    description_true = description.true_candidate()
    assert description.transaction.description != description_true.description
    assert description.transaction.counterparty == description_true.entity


def test_missing_scenario_alternates_reference_and_counterparty() -> None:
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
    missing = [case for case in cases if case.scenario == "P6_MISSING_INFORMATION"]
    assert missing[0].transaction.reference is None
    assert missing[0].transaction.counterparty is not None
    assert missing[1].transaction.counterparty is None
    assert missing[1].transaction.reference is not None


def test_combined_applies_three_distinct_families() -> None:
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    combined = next(case for case in cases if case.scenario == "P7_COMBINED")
    families = {tag.split(":", 1)[0] for tag in combined.perturbations}
    assert len(families) == 3


def test_scenario_aware_n9_competes_with_observed_amount_and_date() -> None:
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=1, config=config)
    by_scenario = {case.scenario: case for case in cases}

    amount_case = by_scenario["P1_AMOUNT_NOISE"]
    amount_n9 = next(candidate for candidate in amount_case.candidates if candidate.id.endswith("-N9"))
    assert amount_n9.amount == amount_case.transaction.amount
    assert amount_n9.reference != amount_case.true_candidate().reference

    date_case = by_scenario["P2_DATE_DRIFT"]
    date_n9 = next(candidate for candidate in date_case.candidates if candidate.id.endswith("-N9"))
    assert date_n9.date == date_case.transaction.date
    assert date_n9.reference != date_case.true_candidate().reference
