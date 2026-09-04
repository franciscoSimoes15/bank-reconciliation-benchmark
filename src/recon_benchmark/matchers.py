from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.models import AccountingRecord, BankTransaction
from recon_benchmark.normalization import (
    normalize_amount,
    normalize_description,
    normalize_entity,
    normalize_reference,
)
from recon_benchmark.similarity import jaro_winkler_similarity, qgram_cosine_similarity

MethodName = Literal["M0", "M1", "M2", "M3", "M4", "M4-noNorm"]
METHODS: tuple[MethodName, ...] = ("M0", "M1", "M2", "M3", "M4", "M4-noNorm")
FIELD_NAMES: tuple[str, ...] = ("amount", "date", "reference", "entity", "description")


@dataclass(frozen=True, slots=True)
class ScoreBreakdown:
    method: MethodName
    total: float
    field_scores: dict[str, float]
    excluded_fields: tuple[str, ...]


def score_pair(
    transaction: BankTransaction,
    candidate: AccountingRecord,
    *,
    method: MethodName,
    config: ExperimentConfig,
) -> ScoreBreakdown:
    if method not in METHODS:
        raise ValueError(f"Método desconhecido: {method}")

    raw_text = method == "M4-noNorm"
    scores: dict[str, float] = {
        "amount": _amount_score(transaction.amount, candidate.amount, method, config),
        "date": _date_score(transaction.date, candidate.date, method, config),
    }
    excluded: list[str] = []

    text_fields = (
        (
            "reference",
            transaction.reference,
            candidate.reference,
            (lambda value: value) if raw_text else normalize_reference,
        ),
        (
            "entity",
            transaction.counterparty,
            candidate.entity,
            (lambda value: value) if raw_text else normalize_entity,
        ),
        (
            "description",
            transaction.description,
            candidate.description,
            (lambda value: value) if raw_text else normalize_description,
        ),
    )

    for field_name, left_raw, right_raw, normalizer in text_fields:
        if _is_missing(left_raw) or _is_missing(right_raw):
            excluded.append(field_name)
            continue
        left = normalizer(left_raw)
        right = normalizer(right_raw)
        if _is_missing(left) or _is_missing(right):
            excluded.append(field_name)
            continue
        if not isinstance(left, str) or not isinstance(right, str):
            raise TypeError(f"O campo {field_name} não foi normalizado para texto.")
        scores[field_name] = _text_score(field_name, left, right, method, config)

    if not scores:
        total = 0.0
    else:
        total = sum(scores.values()) / len(scores)
    return ScoreBreakdown(
        method=method,
        total=_clamp(total),
        field_scores=scores,
        excluded_fields=tuple(excluded),
    )


def _amount_score(
    bank_amount: Decimal,
    candidate_amount: Decimal,
    method: MethodName,
    config: ExperimentConfig,
) -> float:
    difference = abs(normalize_amount(bank_amount) - normalize_amount(candidate_amount))
    if method == "M0":
        return 1.0 if difference == Decimal("0.00") else 0.0
    return 1.0 if difference <= config.amount_tolerance else 0.0


def _date_score(bank_date: date, candidate_date: date, method: MethodName, config: ExperimentConfig) -> float:
    difference_days = abs((bank_date - candidate_date).days)
    if method == "M0":
        return 1.0 if difference_days == 0 else 0.0
    return 1.0 if difference_days <= config.date_tolerance_days else 0.0


def _text_score(
    field_name: str,
    left: str,
    right: str,
    method: MethodName,
    config: ExperimentConfig,
) -> float:
    if method in {"M0", "M1"}:
        return 1.0 if left == right else 0.0
    if method == "M2":
        return jaro_winkler_similarity(left, right)
    if method == "M3":
        return qgram_cosine_similarity(left, right, config.qgram_size)
    if method in {"M4", "M4-noNorm"}:
        if field_name in {"reference", "entity"}:
            return jaro_winkler_similarity(left, right)
        if field_name == "description":
            return qgram_cosine_similarity(left, right, config.qgram_size)
    raise ValueError(f"Combinação method/field não suportada: {method}/{field_name}")


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
