"""Estruturas auxiliares da geração do ledger e dos candidatos."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import AccountingRecord, FinancialEvent


@dataclass(frozen=True, slots=True)
class LedgerEntry:
    event: FinancialEvent
    record: AccountingRecord


@dataclass(frozen=True, slots=True)
class CandidateIdentity:
    event_id: str
    record_id: str
    generation_index: int
