import random
import re
from collections import Counter, defaultdict

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark, validate_benchmark
from recon_benchmark.domain.models import (
    BankTransaction,
    BenchmarkCase,
    CandidateOrigin,
    HardNegativeKind,
    OperationType,
    Scenario,
)
from recon_benchmark.normalization.fields import normalize_description, normalize_reference
from recon_benchmark.generation.synthetic_data import (
    generate_financial_event,
    render_accounting_record,
    render_bank_transaction,
)
from recon_benchmark.templates.accounting import ACCOUNTING_DESCRIPTIONS


def test_financial_event_has_two_independent_renderers() -> None:
    """Check operation coverage, naturally missing fields and distinct bank/accounting
    descriptions.
    """
    events = tuple(
        generate_financial_event(
            random.Random(index),
            seed=7,
            index=index,
            event_id=f"event-{index}",
        )
        for index in range(6)
    )
    assert {event.operation_type for event in events} == set(OperationType)
    assert any(event.document_reference is None for event in events)
    assert any(event.entity_legal_name is None for event in events)

    for index, event in enumerate(events):
        transaction = render_bank_transaction(
            event,
            random.Random(100 + index),
            transaction_id=f"bank-{index}",
        )
        record = render_accounting_record(
            event,
            random.Random(200 + index),
            record_id=f"record-{index}",
        )
        assert normalize_description(transaction.description) != normalize_description(
            record.description
        )
        assert transaction.description != record.description


def test_generator_creates_paired_scenarios_and_exact_candidate_composition() -> None:
    """Verify scenario counts, 1+6+3 composition, hard-negative families and independent natural
    origins.
    """
    config = ExperimentConfig()
    cases = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
    assert len(cases) == 16
    assert Counter(case.scenario for case in cases) == {
        scenario: 2 for scenario in config.scenarios
    }
    assert not validate_benchmark(cases, config=config, expected_cases_per_scenario=2)

    for case in cases:
        origins = Counter(candidate.origin for candidate in case.candidates)
        assert origins == {
            CandidateOrigin.TRUE: 1,
            CandidateOrigin.NATURAL_NEGATIVE: 6,
            CandidateOrigin.CONTROLLED_HARD_NEGATIVE: 3,
        }
        assert {candidate.hard_negative_kind for candidate in case.candidates if candidate.origin is CandidateOrigin.CONTROLLED_HARD_NEGATIVE} == set(HardNegativeKind)
        assert all(
            candidate.source_event_id != case.event_id
            for candidate in case.candidates
            if candidate.origin is CandidateOrigin.NATURAL_NEGATIVE
        )


def test_same_event_and_candidate_set_are_reused_across_scenarios() -> None:
    """Ensure paired variants share the identical candidate tuple and true-candidate identity."""
    cases = generate_benchmark(seed=7, cases_per_scenario=3, config=ExperimentConfig())
    grouped: dict[str, list[BenchmarkCase]] = defaultdict(list)
    for case in cases:
        grouped[case.event_id].append(case)

    for paired in grouped.values():
        first = paired[0]
        assert {case.scenario for case in paired} == set(Scenario)
        assert all(case.candidates is first.candidates for case in paired)
        assert all(case.true_candidate_id == first.true_candidate_id for case in paired)


def test_every_declared_perturbation_changes_its_field() -> None:
    """Compare each variant to its natural baseline so changed fields exactly match declared
    tags.
    """
    cases = generate_benchmark(seed=7, cases_per_scenario=12, config=ExperimentConfig())
    grouped: dict[str, list[BenchmarkCase]] = defaultdict(list)
    for case in cases:
        grouped[case.event_id].append(case)

    family_to_field = {
        "amount": "amount",
        "date": "date",
        "reference": "reference",
        "entity": "counterparty",
        "description": "description",
    }
    for paired in grouped.values():
        baseline = next(
            case for case in paired if case.scenario is Scenario.NATURAL_VARIATION
        )
        baseline_fields = _transaction_fields(baseline.transaction)
        assert baseline.perturbations == ()
        for case in paired:
            if case.scenario is Scenario.NATURAL_VARIATION:
                continue
            changed_fields = {
                name
                for name, value in _transaction_fields(case.transaction).items()
                if value != baseline_fields[name]
            }
            if case.scenario is Scenario.MISSING_INFORMATION:
                expected = {case.perturbations[0].split(":", 1)[1]}
                expected = {"counterparty" if item == "counterparty" else item for item in expected}
            else:
                expected = {
                    family_to_field[tag.split(":", 1)[0]]
                    for tag in case.perturbations
                }
            assert changed_fields == expected
            assert len(case.perturbations) == (
                3 if case.scenario is Scenario.COMBINED_VARIATION else 1
            )


def test_generator_is_reproducible_and_seed_sensitive() -> None:
    """Check that identical seeds reproduce cases and a different seed changes the generated
    data.
    """
    config = ExperimentConfig()
    first = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
    repeated = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
    different = generate_benchmark(seed=8, cases_per_scenario=2, config=config)
    assert [case.to_dict() for case in first] == [case.to_dict() for case in repeated]
    assert [case.to_dict() for case in first] != [case.to_dict() for case in different]


def test_candidate_ids_are_opaque_and_do_not_encode_origin() -> None:
    """Check candidate IDs share one opaque format without readable truth or origin markers."""
    cases = generate_benchmark(seed=7, cases_per_scenario=1, config=ExperimentConfig())
    case = cases[0]
    candidate_ids = [candidate.record.id for candidate in case.candidates]
    assert all(re.fullmatch(r"cand_[0-9a-f]{20}", candidate_id) for candidate_id in candidate_ids)
    assert all(
        marker not in candidate_id.lower()
        for candidate_id in candidate_ids
        for marker in ("true", "natural", "hard", "negative")
    )
    assert case.true_candidate_id in candidate_ids
    assert case.true_candidate_id != case.transaction.id
    assert case.true_candidate_id not in case.case_id


def test_controlled_hard_negatives_guarantee_declared_conflicts() -> None:
    """Check all operation families and paired scenarios, including absent conflict fields.

    Bank fees intentionally have a first hard negative that differs only in its
    description; reference conflicts cannot be asserted when references are absent.
    """
    cases = generate_benchmark(seed=7, cases_per_scenario=6, config=ExperimentConfig())
    covered: set[tuple[OperationType, Scenario]] = set()
    for case in cases:
        true_record = case.true_candidate()
        operation = next(
            operation
            for operation, descriptions in ACCOUNTING_DESCRIPTIONS.items()
            if true_record.description in descriptions
        )
        covered.add((operation, case.scenario))
        hard = {
            candidate.hard_negative_kind: candidate.record
            for candidate in case.candidates
            if candidate.origin is CandidateOrigin.CONTROLLED_HARD_NEGATIVE
        }

        amount_date = hard[HardNegativeKind.AMOUNT_DATE_NEAR_REFERENCE]
        assert amount_date.amount == true_record.amount
        assert amount_date.date == true_record.date
        if operation is OperationType.BANK_FEE:
            assert amount_date.entity is true_record.entity is None
            assert amount_date.description != true_record.description
        else:
            assert amount_date.entity != true_record.entity

        same_entity = hard[HardNegativeKind.SAME_ENTITY_OTHER_DOCUMENT]
        assert same_entity.amount == true_record.amount
        assert same_entity.entity == true_record.entity
        assert abs((same_entity.date - true_record.date).days) == 7

        multi_field = hard[HardNegativeKind.MULTI_FIELD_CHALLENGER]
        assert multi_field.amount == true_record.amount
        assert multi_field.entity == true_record.entity
        assert abs((multi_field.date - true_record.date).days) == 1

        for record, offset in ((amount_date, 1), (same_entity, 17), (multi_field, 2)):
            if operation in {OperationType.CARD_PAYMENT, OperationType.BANK_FEE}:
                assert record.reference is true_record.reference is None
            else:
                assert record.reference is not None
                assert true_record.reference is not None
                true_reference = normalize_reference(true_record.reference)
                assert true_reference is not None
                match = re.fullmatch(r"([a-z]+\d{4})(\d+)", true_reference)
                assert match is not None
                number = match.group(2)
                expected = f"{match.group(1)}{int(number) + offset:0{len(number)}d}"
                assert normalize_reference(record.reference) == expected

    assert covered == {(operation, scenario) for operation in OperationType for scenario in Scenario}


def _transaction_fields(transaction: BankTransaction) -> dict[str, object]:
    """Collect observable bank fields so perturbation tests can identify exactly what changed."""
    return {
        "amount": transaction.amount,
        "date": transaction.date,
        "reference": transaction.reference,
        "counterparty": transaction.counterparty,
        "description": transaction.description,
    }
