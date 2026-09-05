"""Dados observáveis e resultados de scoring, sem ground truth."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import AccountingRecord, MatchingMethod


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    method: MatchingMethod
    total: float
    field_scores: dict[str, float]
    excluded_fields: tuple[str, ...]
    compared_field_count: int


@dataclass(frozen=True, slots=True)
class ReferenceComponents:
    prefix: str
    year: str
    number: str


@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate: AccountingRecord
    breakdown: ScoreBreakdown
