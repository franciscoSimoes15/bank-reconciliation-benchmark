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
    """Financial operation families that determine available fields and templates."""
    SUPPLIER_TRANSFER = "supplier_transfer"
    CUSTOMER_RECEIPT = "customer_receipt"
    DIRECT_DEBIT = "direct_debit"
    CARD_PAYMENT = "card_payment"
    BANK_FEE = "bank_fee"
    TAX_PAYMENT = "tax_payment"


class Scenario(StrEnum):
    """Experimental variants of the same event and candidate set.

    Natural variation keeps the independently rendered bank record unchanged;
    the other variants add controlled changes to that record.
    """
    NATURAL_VARIATION = "natural_variation"
    AMOUNT_VARIATION = "amount_variation"
    DATE_VARIATION = "date_variation"
    REFERENCE_VARIATION = "reference_variation"
    ENTITY_VARIATION = "entity_variation"
    DESCRIPTION_VARIATION = "description_variation"
    MISSING_INFORMATION = "missing_information"
    COMBINED_VARIATION = "combined_variation"


class MatchingMethod(StrEnum):
    """Transparent scoring strategies selected by descriptive names.

    Short labels such as M0 and M4 are output codes, not method identifiers.
    FIELD_AWARE_WITHOUT_DESCRIPTION isolates the contribution of description.
    """
    NORMALIZED_EXACT = "normalized_exact"
    TOLERANT_DETERMINISTIC = "tolerant_deterministic"
    JARO_WINKLER_TEXT = "jaro_winkler_text"
    CHARACTER_TRIGRAM_TEXT = "character_trigram_text"
    FIELD_AWARE = "field_aware"
    FIELD_AWARE_WITHOUT_DESCRIPTION = "field_aware_without_description"


class CandidateOrigin(StrEnum):
    """Evaluation-only label distinguishing truth, ledger negatives and hard negatives.

    This label must stay outside the records supplied to the matcher.
    """
    TRUE = "true"
    NATURAL_NEGATIVE = "natural_negative"
    CONTROLLED_HARD_NEGATIVE = "controlled_hard_negative"


class HardNegativeKind(StrEnum):
    """Controlled conflict families used to construct plausible incorrect candidates."""
    AMOUNT_DATE_NEAR_REFERENCE = "amount_date_near_reference"
    SAME_ENTITY_OTHER_DOCUMENT = "same_entity_other_document"
    MULTI_FIELD_CHALLENGER = "multi_field_challenger"


@dataclass(frozen=True, slots=True)
class FinancialEvent:
    """Underlying financial occurrence from which both source records are rendered.

    The signed amount, event date, legal entity, bank alias and document reference
    represent shared facts. Optional fields depend on the operation type.
    The event and its identity are generation metadata, never matcher inputs.
    """

    event_id: str
    operation_type: OperationType
    event_date: date
    amount: Decimal
    entity_legal_name: str | None
    entity_bank_alias: str | None
    document_reference: str | None


@dataclass(frozen=True, slots=True)
class BankTransaction:
    """Observable bank-side representation of a financial event.

    Its date may include a posting delay, counterparty uses bank naming conventions,
    and reference can be absent. No ground-truth or scenario metadata is stored here.
    """
    id: str
    date: date
    amount: Decimal
    reference: str | None
    counterparty: str | None
    description: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible bank record with ISO date and decimal amount strings."""
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
        """Reconstruct a bank record from serialized fields, checking required value types."""
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
    """Observable accounting-side representation and unit of candidate comparison.

    The renderer uses the event date, legal entity name and accounting templates.
    Reference and entity can be absent; candidate origin is stored separately.
    """
    id: str
    date: date
    amount: Decimal
    reference: str | None
    entity: str | None
    description: str

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-compatible accounting record without benchmark metadata."""
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
        """Reconstruct an accounting record, restoring date and Decimal field types."""
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
    """Accounting record accompanied by labels for generation and evaluation.

    Origin, source_event_id and hard_negative_kind explain how the candidate was
    created. Only record is passed across the matcher boundary.
    """

    record: AccountingRecord
    origin: CandidateOrigin
    source_event_id: str
    hard_negative_kind: HardNegativeKind | None = None

    def to_dict(self) -> dict[str, object]:
        """Serialize the record and its evaluation metadata, using descriptive enum values."""
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
        """Restore a candidate record and its origin labels from a serialized mapping."""
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
    """One ranking question: a bank transaction and its accounting candidates.

    A generated case contains ten candidates including the true match. Event,
    scenario and perturbation metadata allow paired comparisons and evaluation;
    they are not features available to the matcher.
    """
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
        """Return only the observable records, preserving the stored candidate order."""
        return tuple(candidate.record for candidate in self.candidates)

    def true_candidate_entry(self) -> BenchmarkCandidate:
        """Find the labelled true candidate for validation or evaluation.

        Raise ValueError unless true_candidate_id identifies exactly one candidate.
        """
        matches = tuple(
            candidate for candidate in self.candidates if candidate.record.id == self.true_candidate_id
        )
        if len(matches) != 1:
            raise ValueError(
                f"{self.case_id}: expected 1 true candidate, found {len(matches)}."
            )
        return matches[0]

    def true_candidate(self) -> AccountingRecord:
        """Return the true accounting record for checks that are allowed to use labels."""
        return self.true_candidate_entry().record

    def to_dict(self) -> dict[str, object]:
        """Serialize the complete case, including nested records and evaluation labels."""
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
        """Reconstruct a complete case and its typed nested records from JSON data.

        This checks field shapes and enum values; generator validation checks the
        benchmark-wide composition and pairing rules separately.
        """
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
