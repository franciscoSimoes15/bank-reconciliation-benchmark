from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.domain.models import AccountingRecord, BankTransaction, MatchingMethod
from recon_benchmark.normalization.fields import (
    normalize_amount,
    normalize_description,
    normalize_entity,
    normalize_reference,
)
from recon_benchmark.ranking.models import ReferenceComponents, ScoreBreakdown
from recon_benchmark.ranking.similarity import jaro_winkler_similarity, qgram_cosine_similarity

METHODS: tuple[MatchingMethod, ...] = tuple(MatchingMethod)
FIELD_NAMES: tuple[str, ...] = ("amount", "date", "reference", "entity", "description")
_STRUCTURED_REFERENCE = re.compile(
    r"(?P<prefix>[a-z]+)(?P<year>\d{4})(?P<number>\d+)\Z"
)


def score_pair(
    transaction: BankTransaction,
    candidate: AccountingRecord,
    *,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> ScoreBreakdown:
    if method not in METHODS:
        raise ValueError(f"Método desconhecido: {method}")

    scores: dict[str, float] = {
        "amount": _amount_score(transaction.amount, candidate.amount, method, config),
        "date": _date_score(transaction.date, candidate.date, method, config),
    }
    excluded: list[str] = []

    text_fields = (
        ("reference", transaction.reference, candidate.reference, normalize_reference),
        ("entity", transaction.counterparty, candidate.entity, normalize_entity),
        ("description", transaction.description, candidate.description, normalize_description),
    )
    for field_name, left_raw, right_raw, normalizer in text_fields:
        if (
            field_name == "description"
            and method is MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION
        ):
            excluded.append(field_name)
            continue
        if _is_missing(left_raw) or _is_missing(right_raw):
            excluded.append(field_name)
            continue
        left = normalizer(left_raw)
        right = normalizer(right_raw)
        if left is None or right is None:
            excluded.append(field_name)
            continue
        scores[field_name] = _text_score(field_name, left, right, method, config)

    if not scores:
        raise ValueError("Não existem campos disponíveis para calcular o score.")
    total = sum(scores.values()) / len(scores)
    return ScoreBreakdown(
        method=method,
        total=_clamp(total),
        field_scores=scores,
        excluded_fields=tuple(excluded),
        compared_field_count=len(scores),
    )


def amount_proximity(
    bank_amount: Decimal,
    candidate_amount: Decimal,
    config: ExperimentConfig,
) -> float:
    normalized_bank = normalize_amount(bank_amount)
    normalized_candidate = normalize_amount(candidate_amount)
    difference = abs(normalized_bank - normalized_candidate)
    relative_base = max(abs(normalized_bank), abs(normalized_candidate))
    scale = max(
        config.amount_similarity_absolute_scale,
        relative_base * config.amount_similarity_relative_scale,
    )
    return _clamp(1.0 - float(difference / scale))


def date_proximity(
    bank_date: date,
    candidate_date: date,
    config: ExperimentConfig,
) -> float:
    difference_days = abs((bank_date - candidate_date).days)
    return _clamp(1.0 - difference_days / config.date_similarity_scale_days)


def structured_reference_similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    left_components = _parse_reference(left)
    right_components = _parse_reference(right)
    if left_components is None or right_components is None:
        return jaro_winkler_similarity(left, right)

    prefix_score = jaro_winkler_similarity(
        left_components.prefix,
        right_components.prefix,
    )
    year_score = 1.0 if left_components.year == right_components.year else 0.0
    number_score = 1.0 if left_components.number == right_components.number else 0.0
    # The document number is the critical component; prefix/year cannot mask a conflict.
    return _clamp(0.15 * prefix_score + 0.15 * year_score + 0.70 * number_score)


def _amount_score(
    bank_amount: Decimal,
    candidate_amount: Decimal,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> float:
    difference = abs(normalize_amount(bank_amount) - normalize_amount(candidate_amount))
    if method is MatchingMethod.NORMALIZED_EXACT:
        return 1.0 if difference == Decimal("0.00") else 0.0
    if method is MatchingMethod.TOLERANT_DETERMINISTIC:
        return 1.0 if difference <= config.amount_tolerance else 0.0
    return amount_proximity(bank_amount, candidate_amount, config)


def _date_score(
    bank_date: date,
    candidate_date: date,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> float:
    difference_days = abs((bank_date - candidate_date).days)
    if method is MatchingMethod.NORMALIZED_EXACT:
        return 1.0 if difference_days == 0 else 0.0
    if method is MatchingMethod.TOLERANT_DETERMINISTIC:
        return 1.0 if difference_days <= config.date_tolerance_days else 0.0
    return date_proximity(bank_date, candidate_date, config)


def _text_score(
    field_name: str,
    left: str,
    right: str,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> float:
    if method in {
        MatchingMethod.NORMALIZED_EXACT,
        MatchingMethod.TOLERANT_DETERMINISTIC,
    }:
        return 1.0 if left == right else 0.0
    if method is MatchingMethod.JARO_WINKLER_TEXT:
        return jaro_winkler_similarity(left, right)
    if method is MatchingMethod.CHARACTER_TRIGRAM_TEXT:
        return qgram_cosine_similarity(left, right, config.qgram_size)
    if method in {
        MatchingMethod.FIELD_AWARE,
        MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION,
    }:
        if field_name == "reference":
            return structured_reference_similarity(left, right)
        if field_name == "entity":
            return jaro_winkler_similarity(left, right)
        if field_name == "description":
            return qgram_cosine_similarity(left, right, config.qgram_size)
    raise ValueError(f"Combinação method/field não suportada: {method.value}/{field_name}")


def _parse_reference(value: str) -> ReferenceComponents | None:
    match = _STRUCTURED_REFERENCE.fullmatch(value)
    if match is None:
        return None
    return ReferenceComponents(
        prefix=match.group("prefix"),
        year=match.group("year"),
        number=match.group("number"),
    )


def _is_missing(value: object) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _clamp(value: float) -> float:
    return min(1.0, max(0.0, value))
