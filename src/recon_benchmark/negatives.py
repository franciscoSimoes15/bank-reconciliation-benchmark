from __future__ import annotations

import random
import re
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from recon_benchmark.models import AccountingRecord, BankTransaction
from recon_benchmark.normalization import normalize_amount
from recon_benchmark.perturbations import perturb_reference
from recon_benchmark.synthetic_data import generate_entity, generate_reference


def generate_hard_negatives(
    true_record: AccountingRecord,
    observed_transaction: BankTransaction,
    scenario: str,
    *,
    rng: random.Random,
    seed: int,
    global_index: int,
    case_id: str,
) -> tuple[AccountingRecord, ...]:
    alternatives = _alternative_values(true_record, rng, seed, global_index)
    near_reference_1 = _near_reference(true_record.reference, 1)
    near_reference_2 = _near_reference(true_record.reference, 2)
    close_date = true_record.date + timedelta(days=rng.choice((-2, -1, 1, 2)))

    records = (
        AccountingRecord(
            id=f"{case_id}-N1",
            date=alternatives.date,
            amount=true_record.amount,
            reference=alternatives.reference,
            entity=alternatives.entity,
            description=alternatives.description,
        ),
        AccountingRecord(
            id=f"{case_id}-N2",
            date=true_record.date,
            amount=alternatives.amount,
            reference=alternatives.reference,
            entity=alternatives.entity,
            description=alternatives.description,
        ),
        AccountingRecord(
            id=f"{case_id}-N3",
            date=alternatives.date,
            amount=alternatives.amount,
            reference=near_reference_1,
            entity=alternatives.entity,
            description=_replace_reference(true_record.description, true_record.reference, near_reference_1),
        ),
        AccountingRecord(
            id=f"{case_id}-N4",
            date=alternatives.date,
            amount=alternatives.amount,
            reference=alternatives.reference,
            entity=true_record.entity,
            description=_replace_reference(true_record.description, true_record.reference, alternatives.reference),
        ),
        AccountingRecord(
            id=f"{case_id}-N5",
            date=close_date,
            amount=true_record.amount,
            reference=alternatives.reference,
            entity=alternatives.entity,
            description=alternatives.description,
        ),
        AccountingRecord(
            id=f"{case_id}-N6",
            date=alternatives.date,
            amount=true_record.amount,
            reference=alternatives.reference,
            entity=true_record.entity,
            description=_replace_reference(true_record.description, true_record.reference, alternatives.reference),
        ),
        AccountingRecord(
            id=f"{case_id}-N7",
            date=true_record.date,
            amount=true_record.amount,
            reference=near_reference_1,
            entity=alternatives.entity,
            description=_replace_reference(true_record.description, true_record.reference, near_reference_1),
        ),
        AccountingRecord(
            id=f"{case_id}-N8",
            date=alternatives.date,
            amount=alternatives.amount,
            reference=near_reference_2,
            entity=true_record.entity,
            description=_similar_wrong_description(
                true_record.description,
                true_record.reference,
                near_reference_2,
            ),
        ),
        _scenario_challenger(
            true_record=true_record,
            observed_transaction=observed_transaction,
            scenario=scenario,
            near_reference=near_reference_2,
            alternative_entity=alternatives.entity,
            candidate_id=f"{case_id}-N9",
        ),
    )

    checked: list[AccountingRecord] = []
    for record in records:
        checked.append(_ensure_not_identical(record, true_record))
    return tuple(checked)


def _scenario_challenger(
    *,
    true_record: AccountingRecord,
    observed_transaction: BankTransaction,
    scenario: str,
    near_reference: str,
    alternative_entity: str,
    candidate_id: str,
) -> AccountingRecord:
    """Cria o negativo mais difícil usando o movimento observado, não o ground truth oculto.

    A intenção é gerar uma alternativa plausível que compete diretamente com o campo
    perturbado. Isto evita um benchmark trivial em que o true candidate mantém sempre
    quatro ou cinco acordos exatos e vence todos os métodos.
    """
    if scenario == "P1_AMOUNT_NOISE":
        return AccountingRecord(
            id=candidate_id,
            date=true_record.date,
            amount=observed_transaction.amount,
            reference=near_reference,
            entity=true_record.entity,
            description=true_record.description,
        )
    if scenario == "P2_DATE_DRIFT":
        return AccountingRecord(
            id=candidate_id,
            date=observed_transaction.date,
            amount=true_record.amount,
            reference=near_reference,
            entity=true_record.entity,
            description=true_record.description,
        )
    if scenario == "P3_REFERENCE_NOISE":
        candidate_reference = observed_transaction.reference or near_reference
        return AccountingRecord(
            id=candidate_id,
            date=true_record.date,
            amount=true_record.amount,
            reference=candidate_reference,
            entity=true_record.entity,
            description=_replace_reference(
                true_record.description,
                true_record.reference,
                candidate_reference,
            ),
        )
    if scenario == "P4_ENTITY_NOISE":
        candidate_entity = observed_transaction.counterparty or alternative_entity
        return AccountingRecord(
            id=candidate_id,
            date=true_record.date,
            amount=true_record.amount,
            reference=true_record.reference,
            entity=candidate_entity,
            description=_replace_entity(
                true_record.description,
                true_record.entity,
                candidate_entity,
            ),
        )
    if scenario == "P5_DESCRIPTION_NOISE":
        return AccountingRecord(
            id=candidate_id,
            date=true_record.date,
            amount=true_record.amount,
            reference=near_reference,
            entity=true_record.entity,
            description=observed_transaction.description,
        )
    if scenario == "P6_MISSING_INFORMATION":
        if observed_transaction.reference is None:
            return AccountingRecord(
                id=candidate_id,
                date=true_record.date,
                amount=true_record.amount,
                reference=near_reference,
                entity=true_record.entity,
                description=true_record.description,
            )
        return AccountingRecord(
            id=candidate_id,
            date=true_record.date,
            amount=true_record.amount,
            reference=true_record.reference,
            entity=alternative_entity,
            description=_replace_entity(
                true_record.description,
                true_record.entity,
                alternative_entity,
            ),
        )
    if scenario == "P7_COMBINED":
        return AccountingRecord(
            id=candidate_id,
            date=observed_transaction.date,
            amount=observed_transaction.amount,
            reference=near_reference,
            entity=observed_transaction.counterparty or true_record.entity,
            description=observed_transaction.description or true_record.description,
        )
    return AccountingRecord(
        id=candidate_id,
        date=true_record.date,
        amount=true_record.amount,
        reference=near_reference,
        entity=true_record.entity,
        description=_replace_reference(true_record.description, true_record.reference, near_reference),
    )


def _replace_entity(
    description: str | None,
    old_entity: str | None,
    new_entity: str | None,
) -> str | None:
    if description is None:
        return None
    if old_entity and new_entity and old_entity in description:
        return description.replace(old_entity, new_entity)
    if new_entity:
        return f"{description} {new_entity}"
    return description


def _alternative_values(
    true_record: AccountingRecord,
    rng: random.Random,
    seed: int,
    global_index: int,
) -> AccountingRecord:
    entity = _different_entity(true_record.entity, rng, global_index + 97)
    reference = _different_reference(true_record.reference, seed, global_index + 211, rng)
    amount_delta = Decimal(rng.randint(5_000, 100_000)) / Decimal(100)
    signed_delta = amount_delta if true_record.amount < 0 else -amount_delta
    amount = normalize_amount(true_record.amount + signed_delta)
    if amount == true_record.amount:
        amount = normalize_amount(true_record.amount + Decimal("100.00"))
    occurrence_date = true_record.date + timedelta(days=rng.choice((-45, -30, -20, 20, 30, 45)))
    description = f"MOVIMENTO {entity} REF {reference}"
    return AccountingRecord(
        id="ALT",
        date=occurrence_date,
        amount=amount,
        reference=reference,
        entity=entity,
        description=description,
    )


def _different_entity(current: str | None, rng: random.Random, index: int) -> str:
    for offset in range(20):
        candidate = generate_entity(rng, index + offset)
        if candidate != current:
            return candidate
    raise RuntimeError("Não foi possível gerar uma entidade alternativa.")


def _different_reference(
    current: str | None,
    seed: int,
    index: int,
    rng: random.Random,
) -> str:
    for offset in range(20):
        candidate = generate_reference(seed + 100, index + offset, rng)
        if candidate != current:
            return candidate
    raise RuntimeError("Não foi possível gerar uma referência alternativa.")


def _near_reference(reference: str | None, offset: int) -> str:
    if reference is None:
        return f"ALT2026/{offset:05d}"
    match = re.fullmatch(r"([A-Za-z]+)(\d{4})/(\d+)", reference)
    if match:
        number = int(match.group(3)) + offset
        width = len(match.group(3))
        return f"{match.group(1)}{match.group(2)}/{number:0{width}d}"
    # Fallback mantém grande proximidade sem depender de um formato específico.
    return perturb_reference(reference, "substitute", random.Random(offset))


def _replace_reference(
    description: str | None,
    old_reference: str | None,
    new_reference: str | None,
) -> str | None:
    if description is None:
        return None
    if old_reference and new_reference and old_reference in description:
        return description.replace(old_reference, new_reference)
    if new_reference:
        return f"{description} REF {new_reference}"
    return description


def _similar_wrong_description(
    description: str | None,
    old_reference: str | None,
    new_reference: str | None,
) -> str | None:
    changed = _replace_reference(description, old_reference, new_reference)
    if changed is None:
        return None
    return f"{changed} AJUSTE"


def _ensure_not_identical(
    negative: AccountingRecord,
    true_record: AccountingRecord,
) -> AccountingRecord:
    if _matching_fields(negative) != _matching_fields(true_record):
        return negative
    replacement_reference = _near_reference(true_record.reference, 99)
    return replace(
        negative,
        reference=replacement_reference,
        description=_replace_reference(
            negative.description,
            true_record.reference,
            replacement_reference,
        ),
    )


def _matching_fields(record: AccountingRecord) -> tuple[object, ...]:
    return (
        record.date,
        record.amount,
        record.reference,
        record.entity,
        record.description,
    )
