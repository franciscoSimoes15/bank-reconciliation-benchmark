"""Dados observáveis e resultados de scoring, sem ground truth."""

from __future__ import annotations

from dataclasses import dataclass

from recon_benchmark.domain.models import AccountingRecord, MatchingMethod


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    """Compatibility result for one bank/accounting pair under one method.

    field_scores contains the evidence actually compared; excluded_fields records
    missing or ablated evidence. total is the simple mean of compared fields in
    [0,1], not a probability, and compared_field_count supports fairness checks.
    """
    method: MatchingMethod
    total: float
    field_scores: dict[str, float]
    excluded_fields: tuple[str, ...]
    compared_field_count: int


@dataclass(frozen=True, slots=True)
class ReferenceComponents:
    """Parsed document prefix, four-digit year and number from a normalized reference.

    Keep the number as text so leading zeros remain part of document identity.
    """
    prefix: str
    year: str
    number: str


@dataclass(frozen=True, slots=True)
class CandidateScore:
    """Associate an observable accounting candidate with its ScoreBreakdown for ordering.

    No truth, scenario or candidate-origin label is needed to construct the ranking.
    """
    candidate: AccountingRecord
    breakdown: ScoreBreakdown
