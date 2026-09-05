from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum

from recon_benchmark.domain.validation import (
    _mapping_value,
    _optional_string,
    _required_int,
    _required_list,
    _required_mapping,
    _required_string,
    _string_value,
)


class OperationType(StrEnum):
    SUPPLIER_TRANSFER = "supplier_transfer"
    CUSTOMER_RECEIPT = "customer_receipt"
    DIRECT_DEBIT = "direct_debit"
    CARD_PAYMENT = "card_payment"
    BANK_FEE = "bank_fee"
    TAX_PAYMENT = "tax_payment"


class Scenario(StrEnum):
    NATURAL_VARIATION = "natural_variation"
    AMOUNT_VARIATION = "amount_variation"
    DATE_VARIATION = "date_variation"
    REFERENCE_VARIATION = "reference_variation"
    ENTITY_VARIATION = "entity_variation"
    DESCRIPTION_VARIATION = "description_variation"
    MISSING_INFORMATION = "missing_information"
    COMBINED_VARIATION = "combined_variation"


class MatchingMethod(StrEnum):
    NORMALIZED_EXACT = "normalized_exact"
    TOLERANT_DETERMINISTIC = "tolerant_deterministic"
    JARO_WINKLER_TEXT = "jaro_winkler_text"
    CHARACTER_TRIGRAM_TEXT = "character_trigram_text"
    FIELD_AWARE = "field_aware"
    FIELD_AWARE_WITHOUT_DESCRIPTION = "field_aware_without_description"


class CandidateOrigin(StrEnum):
    TRUE = "true"
    NATURAL_NEGATIVE = "natural_negative"
    CONTROLLED_HARD_NEGATIVE = "controlled_hard_negative"


class HardNegativeKind(StrEnum):
    AMOUNT_DATE_NEAR_REFERENCE = "amount_date_near_reference"
    SAME_ENTITY_OTHER_DOCUMENT = "same_entity_other_document"
    MULTI_FIELD_CHALLENGER = "multi_field_challenger"


@dataclass(frozen=True, slots=True)
class FinancialEvent:
    """Latent event used only while generating the two independent views."""

    event_id: str
    operation_type: OperationType
    event_date: date
    amount: Decimal
    entity_legal_name: str | None
    entity_bank_alias: str | None
    document_reference: str | None


@dataclass(frozen=True, slots=True)
class BankTransaction:
    id: str
    date: date
    amount: Decimal
    reference: str | None
    counterparty: str | None
    description: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": format(self.amount, "f"),
            "reference": self.reference,
            "counterparty": self.counterparty,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> BankTransaction:
        return cls(
            id=_required_string(raw, "id"),
            date=date.fromisoformat(_required_string(raw, "date")),
            amount=Decimal(_required_string(raw, "amount")),
            reference=_optional_string(raw.get("reference"), "reference"),
            counterparty=_optional_string(raw.get("counterparty"), "counterparty"),
            description=_required_string(raw, "description"),
        )


@dataclass(frozen=True, slots=True)
class AccountingRecord:
    id: str
    date: date
    amount: Decimal
    reference: str | None
    entity: str | None
    description: str

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": format(self.amount, "f"),
            "reference": self.reference,
            "entity": self.entity,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> AccountingRecord:
        return cls(
            id=_required_string(raw, "id"),
            date=date.fromisoformat(_required_string(raw, "date")),
            amount=Decimal(_required_string(raw, "amount")),
            reference=_optional_string(raw.get("reference"), "reference"),
            entity=_optional_string(raw.get("entity"), "entity"),
            description=_required_string(raw, "description"),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkCandidate:
    """Generator/evaluator metadata kept outside the record passed to a matcher."""

    record: AccountingRecord
    origin: CandidateOrigin
    source_event_id: str
    hard_negative_kind: HardNegativeKind | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "record": self.record.to_dict(),
            "origin": self.origin.value,
            "source_event_id": self.source_event_id,
            "hard_negative_kind": (
                self.hard_negative_kind.value if self.hard_negative_kind is not None else None
            ),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> BenchmarkCandidate:
        record_raw = _required_mapping(raw, "record")
        kind_raw = raw.get("hard_negative_kind")
        kind = (
            None
            if kind_raw is None
            else HardNegativeKind(_string_value(kind_raw, "hard_negative_kind"))
        )
        return cls(
            record=AccountingRecord.from_dict(record_raw),
            origin=CandidateOrigin(_required_string(raw, "origin")),
            source_event_id=_required_string(raw, "source_event_id"),
            hard_negative_kind=kind,
        )


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    seed: int
    event_id: str
    scenario: Scenario
    transaction: BankTransaction
    candidates: tuple[BenchmarkCandidate, ...]
    true_candidate_id: str
    perturbations: tuple[str, ...]

    @property
    def candidate_records(self) -> tuple[AccountingRecord, ...]:
        return tuple(candidate.record for candidate in self.candidates)

    def true_candidate_entry(self) -> BenchmarkCandidate:
        matches = tuple(
            candidate for candidate in self.candidates if candidate.record.id == self.true_candidate_id
        )
        if len(matches) != 1:
            raise ValueError(
                f"{self.case_id}: eram esperados 1 true candidate, foram encontrados {len(matches)}."
            )
        return matches[0]

    def true_candidate(self) -> AccountingRecord:
        return self.true_candidate_entry().record

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "seed": self.seed,
            "event_id": self.event_id,
            "scenario": self.scenario.value,
            "transaction": self.transaction.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "true_candidate_id": self.true_candidate_id,
            "perturbations": list(self.perturbations),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, object]) -> BenchmarkCase:
        transaction_raw = _required_mapping(raw, "transaction")
        candidate_items = _required_list(raw, "candidates")
        perturbation_items = _required_list(raw, "perturbations")
        candidates = tuple(
            BenchmarkCandidate.from_dict(_mapping_value(item, "candidate"))
            for item in candidate_items
        )
        return cls(
            case_id=_required_string(raw, "case_id"),
            seed=_required_int(raw, "seed"),
            event_id=_required_string(raw, "event_id"),
            scenario=Scenario(_required_string(raw, "scenario")),
            transaction=BankTransaction.from_dict(transaction_raw),
            candidates=candidates,
            true_candidate_id=_required_string(raw, "true_candidate_id"),
            perturbations=tuple(
                _string_value(item, "perturbation") for item in perturbation_items
            ),
        )
