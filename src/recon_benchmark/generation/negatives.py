from __future__ import annotations

import random
from dataclasses import replace
from datetime import timedelta

from recon_benchmark.domain.models import (
    AccountingRecord,
    BenchmarkCandidate,
    CandidateOrigin,
    FinancialEvent,
    HardNegativeKind,
    OperationType,
)
from recon_benchmark.generation.models import CandidateIdentity, LedgerEntry
from recon_benchmark.generation.synthetic_data import (
    generate_entity_names,
    near_document_reference,
    render_accounting_record,
)


def select_natural_negatives(
    true_entry: LedgerEntry,
    ledger: tuple[LedgerEntry, ...],
    *,
    rng: random.Random,
    count: int,
) -> tuple[BenchmarkCandidate, ...]:
    """Sample other ledger events as plausible, coherent incorrect candidates.

    Require the true record's reference/entity availability pattern. Rank eligible
    records by sign, relative amount gap and date gap, then sample count records
    from a nearby pool with the supplied RNG. An insufficient pool raises.
    """
    availability = _availability_pattern(true_entry.record)
    eligible = [
        entry
        for entry in ledger
        if entry.event.event_id != true_entry.event.event_id
        and _availability_pattern(entry.record) == availability
    ]
    if len(eligible) < count:
        raise RuntimeError(
            f"Insufficient ledger entries for {count} natural negatives with availability {availability}."
        )

    eligible.sort(key=lambda entry: _retrieval_key(true_entry.record, entry.record))
    reservoir_size = min(len(eligible), max(count, count * 3))
    selected = rng.sample(eligible[:reservoir_size], k=count)
    return tuple(
        BenchmarkCandidate(
            record=entry.record,
            origin=CandidateOrigin.NATURAL_NEGATIVE,
            source_event_id=entry.event.event_id,
        )
        for entry in selected
    )


def build_controlled_hard_negatives(
    true_entry: LedgerEntry,
    identities: tuple[CandidateIdentity, CandidateIdentity, CandidateIdentity],
    *,
    rng: random.Random,
) -> tuple[BenchmarkCandidate, ...]:
    """Render three distinct events with controlled conflicts against the true entry.

    Preserve selected evidence such as amount, date or entity while changing other
    facts. Use only latent/ledger data and supplied identities; scenario and the
    perturbed bank transaction cannot influence these candidates.
    """
    true_event = true_entry.event
    alternative_legal, alternative_alias = _alternative_entity(
        true_event,
        rng,
        identities[0].generation_index,
    )
    day_direction = rng.choice((-1, 1))

    events = (
        FinancialEvent(
            event_id=identities[0].event_id,
            operation_type=true_event.operation_type,
            event_date=true_event.event_date,
            amount=true_event.amount,
            entity_legal_name=alternative_legal,
            entity_bank_alias=alternative_alias,
            document_reference=near_document_reference(true_event.document_reference, 1),
        ),
        FinancialEvent(
            event_id=identities[1].event_id,
            operation_type=true_event.operation_type,
            event_date=true_event.event_date + timedelta(days=7 * day_direction),
            amount=true_event.amount,
            entity_legal_name=true_event.entity_legal_name,
            entity_bank_alias=true_event.entity_bank_alias,
            document_reference=near_document_reference(true_event.document_reference, 17),
        ),
        FinancialEvent(
            event_id=identities[2].event_id,
            operation_type=true_event.operation_type,
            event_date=true_event.event_date + timedelta(days=day_direction),
            amount=true_event.amount,
            entity_legal_name=true_event.entity_legal_name,
            entity_bank_alias=true_event.entity_bank_alias,
            document_reference=near_document_reference(true_event.document_reference, 2),
        ),
    )
    kinds = (
        HardNegativeKind.AMOUNT_DATE_NEAR_REFERENCE,
        HardNegativeKind.SAME_ENTITY_OTHER_DOCUMENT,
        HardNegativeKind.MULTI_FIELD_CHALLENGER,
    )

    candidates: list[BenchmarkCandidate] = []
    for event, identity, kind in zip(events, identities, kinds):
        record = _render_distinct_record(
            event,
            true_entry.record,
            rng,
            record_id=identity.record_id,
        )
        candidates.append(
            BenchmarkCandidate(
                record=record,
                origin=CandidateOrigin.CONTROLLED_HARD_NEGATIVE,
                source_event_id=event.event_id,
                hard_negative_kind=kind,
            )
        )
    return tuple(candidates)


def _alternative_entity(
    event: FinancialEvent,
    rng: random.Random,
    start_index: int,
) -> tuple[str | None, str | None]:
    """Find a different generated legal name and alias, preserving bank-fee missingness.

    Try up to 100 entity combinations before reporting failure.
    """
    if event.operation_type is OperationType.BANK_FEE:
        return None, None
    for offset in range(100):
        legal_name, bank_alias = generate_entity_names(rng, start_index + offset)
        if legal_name != event.entity_legal_name:
            return legal_name, bank_alias
    raise RuntimeError("Could not generate a distinct controlled entity.")


def _render_distinct_record(
    event: FinancialEvent,
    true_record: AccountingRecord,
    rng: random.Random,
    *,
    record_id: str,
) -> AccountingRecord:
    """Render a hard-negative event without duplicating all true matching fields.

    Retry accounting renderings first. If all attempts collide, add a coherent
    alternative description label, then verify the record is distinct.
    """
    for _ in range(20):
        render_rng = random.Random(rng.getrandbits(64))
        record = render_accounting_record(event, render_rng, record_id=record_id)
        if _matching_fields(record) != _matching_fields(true_record):
            return record

    # Only bank-fee events can share every structured field; the alternative label
    # remains a coherent accounting description and prevents a duplicate candidate.
    record = render_accounting_record(event, random.Random(0), record_id=record_id)
    changed_description = f"{record.description} extraordinario"
    changed = replace(record, description=changed_description)
    if _matching_fields(changed) == _matching_fields(true_record):
        raise RuntimeError("Could not construct a distinct controlled hard negative.")
    return changed


def _availability_pattern(record: AccountingRecord) -> tuple[bool, bool]:
    """Return optional-field presence flags used to keep natural negatives comparable."""
    return (record.reference is not None, record.entity is not None)


def _retrieval_key(
    true_record: AccountingRecord,
    candidate: AccountingRecord,
) -> tuple[int, float, int, str]:
    """Order ledger candidates by sign agreement, relative amount gap, date gap and ID.

    This selects a plausible negative pool during generation; it is not a method
    being evaluated and never uses the experimentally perturbed bank record.
    """
    sign_mismatch = int((true_record.amount < 0) != (candidate.amount < 0))
    denominator = max(abs(true_record.amount), abs(candidate.amount), 1)
    relative_amount_difference = float(abs(true_record.amount - candidate.amount) / denominator)
    date_difference = abs((true_record.date - candidate.date).days)
    return (sign_mismatch, relative_amount_difference, date_difference, candidate.id)


def _matching_fields(record: AccountingRecord) -> tuple[object, ...]:
    """Return observable record fields, excluding identity, for duplicate detection."""
    return (
        record.date,
        record.amount,
        record.reference,
        record.entity,
        record.description,
    )
