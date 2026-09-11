"""Supporting structures for ledger and candidate generation."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import AccountingRecord, FinancialEvent


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    """Pair a latent event with its independently rendered accounting record.

    The generator uses this ledger entry to identify truth and select other events
    as natural negatives; the matcher receives only the accounting record.
    """
    event: FinancialEvent
    record: AccountingRecord


@dataclass(frozen=True, slots=True)
class CandidateIdentity:
    """Preallocated IDs and generation index for one controlled hard negative.

    The index supports deterministic synthetic values; IDs identify objects without
    putting readable truth or origin labels in candidate identifiers.
    """
    event_id: str
    record_id: str
    generation_index: int
