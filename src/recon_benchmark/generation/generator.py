from __future__ import annotations

import hashlib
import random
import re
from collections import Counter, defaultdict
from collections.abc import Iterable
from pathlib import Path

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.domain.models import (
    AccountingRecord,
    BenchmarkCandidate,
    BenchmarkCase,
    CandidateOrigin,
    HardNegativeKind,
    Scenario,
)
from recon_benchmark.generation.models import CandidateIdentity, LedgerEntry
from recon_benchmark.generation.negatives import (
    build_controlled_hard_negatives,
    select_natural_negatives,
)
from recon_benchmark.generation.perturbations import apply_perturbation
from recon_benchmark.storage.serialization import write_jsonl
from recon_benchmark.generation.synthetic_data import (
    generate_financial_event,
    render_accounting_record,
    render_bank_transaction,
)

_MINIMUM_LEDGER_EVENTS = 60
_OPAQUE_CANDIDATE_ID = re.compile(r"cand_[0-9a-f]{20}\Z")


def generate_benchmark(
    *,
    seed: int,
    cases_per_scenario: int,
    config: ExperimentConfig,
) -> tuple[BenchmarkCase, ...]:
    """Build validated, reproducible ranking cases for one seed.

    Generate a supporting ledger, then one bank record and a shuffled 1+6+3
    candidate set per target event. Reuse that set across all configured scenarios,
    perturbing only the bank record. Return cases_per_scenario times the number
    of scenarios as an immutable tuple; invalid cases raise before return.
    """
    if cases_per_scenario <= 0:
        raise ValueError("cases_per_scenario must be positive.")
    config.validate()

    ledger_size = max(cases_per_scenario, _MINIMUM_LEDGER_EVENTS)
    ledger = _generate_ledger(seed=seed, event_count=ledger_size)
    cases: list[BenchmarkCase] = []

    for event_index, true_entry in enumerate(ledger[:cases_per_scenario]):
        transaction_rng = random.Random(_derived_seed(seed, "bank_renderer", event_index))
        base_transaction = render_bank_transaction(
            true_entry.event,
            transaction_rng,
            transaction_id=_opaque_id("bank", seed, event_index),
        )

        natural_negatives = select_natural_negatives(
            true_entry,
            ledger,
            rng=random.Random(_derived_seed(seed, "natural_negatives", event_index)),
            count=config.natural_negative_count,
        )
        identities = tuple(
            CandidateIdentity(
                event_id=_opaque_id("event", seed, "hard", event_index, hard_index),
                record_id=_opaque_id("candidate", seed, "hard", event_index, hard_index),
                generation_index=ledger_size + event_index * 3 + hard_index,
            )
            for hard_index in range(config.controlled_hard_negative_count)
        )
        if len(identities) != 3:
            raise RuntimeError("The protocol requires three hard-negative identities.")
        hard_negatives = build_controlled_hard_negatives(
            true_entry,
            (identities[0], identities[1], identities[2]),
            rng=random.Random(_derived_seed(seed, "hard_negatives", event_index)),
        )
        true_candidate = BenchmarkCandidate(
            record=true_entry.record,
            origin=CandidateOrigin.TRUE,
            source_event_id=true_entry.event.event_id,
        )
        candidates = [true_candidate, *natural_negatives, *hard_negatives]
        random.Random(_derived_seed(seed, "candidate_shuffle", event_index)).shuffle(candidates)
        paired_candidates = tuple(candidates)

        for scenario in config.scenarios:
            perturbation_rng = random.Random(
                _derived_seed(seed, "perturbation", event_index, scenario.value)
            )
            transaction, perturbations = apply_perturbation(
                base_transaction,
                scenario,
                perturbation_rng,
                event_index,
            )
            case = BenchmarkCase(
                case_id=_opaque_id("case", seed, event_index, scenario.value),
                seed=seed,
                event_id=true_entry.event.event_id,
                scenario=scenario,
                transaction=transaction,
                candidates=paired_candidates,
                true_candidate_id=true_entry.record.id,
                perturbations=perturbations,
            )
            validate_case(case, config)
            cases.append(case)

    expected = cases_per_scenario * len(config.scenarios)
    if len(cases) != expected:
        raise RuntimeError(f"Generated {len(cases)} cases; expected {expected}.")
    errors = validate_benchmark(
        cases,
        config=config,
        expected_cases_per_scenario=cases_per_scenario,
    )
    if errors:
        raise RuntimeError("Invalid benchmark: " + " | ".join(errors))
    return tuple(cases)


def generate_to_file(
    *,
    seed: int,
    cases_per_scenario: int,
    config: ExperimentConfig,
    output: str | Path,
) -> Path:
    """Generate validated cases for one seed and write them to a JSONL file.

    Return the output path; existing content at that path is replaced.
    """
    cases = generate_benchmark(
        seed=seed,
        cases_per_scenario=cases_per_scenario,
        config=config,
    )
    return write_jsonl(cases, output)


def validate_case(case: BenchmarkCase, config: ExperimentConfig) -> None:
    """Check one case's candidate composition, IDs, labels and field availability.

    Also reject negatives identical to truth and inconsistent perturbation labels.
    Raise ValueError on the first violation; cross-scenario checks are separate.
    """
    if len(case.candidates) != config.candidates_per_case:
        raise ValueError(
            f"{case.case_id}: {len(case.candidates)} candidates; "
            f"expected {config.candidates_per_case}."
        )
    candidate_ids = [candidate.record.id for candidate in case.candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError(f"{case.case_id}: duplicate candidate IDs exist.")
    if not all(_OPAQUE_CANDIDATE_ID.fullmatch(candidate_id) for candidate_id in candidate_ids):
        raise ValueError(f"{case.case_id}: candidate ID is not opaque or has an unexpected format.")
    if candidate_ids.count(case.true_candidate_id) != 1:
        raise ValueError(f"{case.case_id}: true candidate is missing or duplicated.")

    origin_counts = Counter(candidate.origin for candidate in case.candidates)
    expected_origins = {
        CandidateOrigin.TRUE: 1,
        CandidateOrigin.NATURAL_NEGATIVE: config.natural_negative_count,
        CandidateOrigin.CONTROLLED_HARD_NEGATIVE: config.controlled_hard_negative_count,
    }
    if origin_counts != expected_origins:
        raise ValueError(f"{case.case_id}: invalid candidate composition: {origin_counts}.")

    true_entry = case.true_candidate_entry()
    if true_entry.origin is not CandidateOrigin.TRUE:
        raise ValueError(f"{case.case_id}: true_candidate_id does not point to a candidate with true origin.")
    if true_entry.source_event_id != case.event_id:
        raise ValueError(f"{case.case_id}: true candidate does not belong to the case's FinancialEvent.")

    hard_kinds = Counter(
        candidate.hard_negative_kind
        for candidate in case.candidates
        if candidate.origin is CandidateOrigin.CONTROLLED_HARD_NEGATIVE
    )
    if hard_kinds != Counter({kind: 1 for kind in HardNegativeKind}):
        raise ValueError(f"{case.case_id}: invalid controlled hard-negative types.")

    true_fields = _record_fields(true_entry.record)
    availability = _availability_pattern(true_entry.record)
    for candidate in case.candidates:
        if _availability_pattern(candidate.record) != availability:
            raise ValueError(
                f"{case.case_id}: inconsistent availability pattern across candidates."
            )
        if candidate.origin is CandidateOrigin.NATURAL_NEGATIVE:
            if candidate.source_event_id == case.event_id:
                raise ValueError(
                    f"{case.case_id}: natural negative belongs to the true FinancialEvent."
                )
            if candidate.hard_negative_kind is not None:
                raise ValueError(f"{case.case_id}: natural negative is marked as controlled.")
        if candidate.origin is not CandidateOrigin.TRUE:
            if _record_fields(candidate.record) == true_fields:
                raise ValueError(
                    f"{case.case_id}: negative {candidate.record.id} is identical to the true candidate."
                )

    if case.scenario is Scenario.NATURAL_VARIATION and case.perturbations:
        raise ValueError(f"{case.case_id}: natural variation cannot declare perturbations.")
    if case.scenario is not Scenario.NATURAL_VARIATION and not case.perturbations:
        raise ValueError(f"{case.case_id}: experimental scenario has no declared perturbation.")


def validate_benchmark(
    cases: Iterable[BenchmarkCase],
    *,
    config: ExperimentConfig,
    expected_cases_per_scenario: int | None = None,
) -> list[str]:
    """Collect case and cross-scenario validation errors without stopping at the first.

    Check duplicate case IDs, optional expected scenario counts, paired candidate
    sets and truth, and experimental records unchanged from natural variation.
    Return an empty list when these checks find no violations.
    """
    errors: list[str] = []
    case_list = list(cases)
    case_ids = [case.case_id for case in case_list]
    if len(case_ids) != len(set(case_ids)):
        errors.append("Duplicate case IDs exist.")

    for case in case_list:
        try:
            validate_case(case, config)
        except ValueError as exc:
            errors.append(str(exc))

    scenario_counts = Counter(case.scenario for case in case_list)
    if expected_cases_per_scenario is not None:
        for scenario in config.scenarios:
            actual = scenario_counts.get(scenario, 0)
            if actual != expected_cases_per_scenario:
                errors.append(
                    f"{scenario.value}: {actual} cases; expected {expected_cases_per_scenario}."
                )

    grouped: dict[str, list[BenchmarkCase]] = defaultdict(list)
    for case in case_list:
        grouped[case.event_id].append(case)
    for event_id, paired_cases in grouped.items():
        scenario_set = {case.scenario for case in paired_cases}
        if scenario_set != set(config.scenarios):
            errors.append(f"{event_id}: incomplete set of paired scenarios.")
            continue
        baseline = paired_cases[0]
        for paired in paired_cases[1:]:
            if paired.candidates != baseline.candidates:
                errors.append(f"{event_id}: candidate set or order changed between scenarios.")
                break
            if paired.true_candidate_id != baseline.true_candidate_id:
                errors.append(f"{event_id}: ground truth changed between scenarios.")
                break
        natural_case = next(
            case for case in paired_cases if case.scenario is Scenario.NATURAL_VARIATION
        )
        for paired in paired_cases:
            if (
                paired.scenario is not Scenario.NATURAL_VARIATION
                and paired.transaction == natural_case.transaction
            ):
                errors.append(f"{event_id}: no-op perturbation in {paired.scenario.value}.")

    return errors


def benchmark_digest(path: str | Path) -> str:
    """Hash the exact JSONL file bytes with SHA-256, reading in bounded-size chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _generate_ledger(*, seed: int, event_count: int) -> tuple[LedgerEntry, ...]:
    """Create latent events and accounting records using separate derived RNG streams.

    Return generation-only LedgerEntry objects from which target events and
    natural-negative records can be selected.
    """
    entries: list[LedgerEntry] = []
    for index in range(event_count):
        event = generate_financial_event(
            random.Random(_derived_seed(seed, "financial_event", index)),
            seed=seed,
            index=index,
            event_id=_opaque_id("event", seed, "ledger", index),
        )
        record = render_accounting_record(
            event,
            random.Random(_derived_seed(seed, "accounting_renderer", index)),
            record_id=_opaque_id("candidate", seed, "ledger", index),
        )
        entries.append(LedgerEntry(event=event, record=record))
    return tuple(entries)


def _derived_seed(seed: int, *parts: object) -> int:
    """Derive a stable integer seed from a base seed and operation-specific labels.

    Separate labels isolate renderer, selection, perturbation and shuffle streams
    without relying on global randomness or Python's process-dependent hash().
    """
    payload = "|".join((str(seed), *(str(part) for part in parts))).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], byteorder="big", signed=False)


def _opaque_id(kind: str, seed: int, *parts: object) -> str:
    """Create a deterministic typed ID whose hash hides readable generation labels.

    All candidate origins share the cand_ format. This is an opaque benchmark
    identifier, not a security or anonymization mechanism.
    """
    namespace = "candidate" if kind == "candidate" else kind
    payload = "|".join(("benchmark-v2", namespace, str(seed), *(str(part) for part in parts)))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    prefix = {
        "bank": "bank",
        "candidate": "cand",
        "case": "case",
        "event": "event",
    }.get(kind)
    if prefix is None:
        raise ValueError(f"Unknown identifier type: {kind}")
    return f"{prefix}_{digest}"


def _availability_pattern(record: AccountingRecord) -> tuple[bool, bool]:
    """Return reference/entity presence flags for candidate-availability checks."""
    return (record.reference is not None, record.entity is not None)


def _record_fields(record: AccountingRecord) -> tuple[object, ...]:
    """Return comparable accounting fields without the ID to detect copied negatives."""
    return (
        record.date,
        record.amount,
        record.reference,
        record.entity,
        record.description,
    )
