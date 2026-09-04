from __future__ import annotations

import hashlib
import random
from collections import Counter
from pathlib import Path
from typing import Iterable

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.models import AccountingRecord, BenchmarkCase
from recon_benchmark.negatives import generate_hard_negatives
from recon_benchmark.perturbations import apply_perturbation
from recon_benchmark.serialization import write_jsonl
from recon_benchmark.synthetic_data import derive_bank_transaction, generate_canonical_record


def generate_benchmark(
    *,
    seed: int,
    cases_per_scenario: int,
    config: ExperimentConfig,
) -> tuple[BenchmarkCase, ...]:
    if cases_per_scenario <= 0:
        raise ValueError("cases_per_scenario tem de ser positivo.")

    cases: list[BenchmarkCase] = []
    global_index = 0
    for scenario in config.scenarios:
        for scenario_index in range(cases_per_scenario):
            case_id = f"S{seed}-{scenario}-C{scenario_index:04d}"
            rng = random.Random(_derived_seed(seed, scenario, scenario_index))
            true_candidate_id = f"{case_id}-TRUE"
            transaction_id = f"{case_id}-BANK"
            canonical_record = generate_canonical_record(
                rng,
                seed,
                global_index,
                true_candidate_id,
            )
            base_transaction = derive_bank_transaction(canonical_record, transaction_id)
            transaction, perturbations = apply_perturbation(
                base_transaction,
                scenario,
                rng,
                scenario_index,
            )
            negatives = generate_hard_negatives(
                canonical_record,
                observed_transaction=transaction,
                scenario=scenario,
                rng=rng,
                seed=seed,
                global_index=global_index,
                case_id=case_id,
            )
            candidates = [canonical_record, *negatives]
            rng.shuffle(candidates)
            case = BenchmarkCase(
                case_id=case_id,
                seed=seed,
                scenario=scenario,
                transaction=transaction,
                candidates=tuple(candidates),
                true_candidate_id=true_candidate_id,
                perturbations=perturbations,
            )
            validate_case(case, config)
            cases.append(case)
            global_index += 1

    expected = cases_per_scenario * len(config.scenarios)
    if len(cases) != expected:
        raise RuntimeError(f"Foram gerados {len(cases)} casos; eram esperados {expected}.")
    return tuple(cases)


def generate_to_file(
    *,
    seed: int,
    cases_per_scenario: int,
    config: ExperimentConfig,
    output: str | Path,
) -> Path:
    cases = generate_benchmark(
        seed=seed,
        cases_per_scenario=cases_per_scenario,
        config=config,
    )
    return write_jsonl(cases, output)


def validate_case(case: BenchmarkCase, config: ExperimentConfig) -> None:
    if len(case.candidates) != config.candidates_per_case:
        raise ValueError(
            f"{case.case_id}: {len(case.candidates)} candidatos; "
            f"esperados {config.candidates_per_case}."
        )
    candidate_ids = [candidate.id for candidate in case.candidates]
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError(f"{case.case_id}: existem candidate IDs duplicados.")
    if candidate_ids.count(case.true_candidate_id) != 1:
        raise ValueError(f"{case.case_id}: true candidate ausente ou duplicado.")
    true_candidate = case.true_candidate()
    true_fields = _record_fields(true_candidate)
    for candidate in case.candidates:
        if candidate.id == case.true_candidate_id:
            continue
        if _record_fields(candidate) == true_fields:
            raise ValueError(f"{case.case_id}: negative {candidate.id} é idêntico ao true candidate.")


def validate_benchmark(
    cases: Iterable[BenchmarkCase],
    *,
    config: ExperimentConfig,
    expected_cases_per_scenario: int | None = None,
) -> list[str]:
    errors: list[str] = []
    case_list = list(cases)
    case_ids = [case.case_id for case in case_list]
    if len(case_ids) != len(set(case_ids)):
        errors.append("Existem case IDs duplicados.")

    for case in case_list:
        try:
            validate_case(case, config)
        except ValueError as exc:
            errors.append(str(exc))

    if expected_cases_per_scenario is not None:
        counts = Counter(case.scenario for case in case_list)
        for scenario in config.scenarios:
            actual = counts.get(scenario, 0)
            if actual != expected_cases_per_scenario:
                errors.append(
                    f"{scenario}: {actual} casos; esperados {expected_cases_per_scenario}."
                )
    return errors


def benchmark_digest(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _derived_seed(seed: int, scenario: str, index: int) -> int:
    payload = f"{seed}|{scenario}|{index}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], byteorder="big", signed=False)


def _record_fields(record: AccountingRecord) -> tuple[object, ...]:
    return (
        getattr(record, "date"),
        getattr(record, "amount"),
        getattr(record, "reference"),
        getattr(record, "entity"),
        getattr(record, "description"),
    )
