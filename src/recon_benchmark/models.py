from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any


@dataclass(frozen=True, slots=True)
class BankTransaction:
    id: str
    date: date
    amount: Decimal
    reference: str | None
    counterparty: str | None
    description: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": format(self.amount, "f"),
            "reference": self.reference,
            "counterparty": self.counterparty,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> BankTransaction:
        return cls(
            id=str(value["id"]),
            date=date.fromisoformat(str(value["date"])),
            amount=Decimal(str(value["amount"])),
            reference=_optional_string(value.get("reference")),
            counterparty=_optional_string(value.get("counterparty")),
            description=_optional_string(value.get("description")),
        )


@dataclass(frozen=True, slots=True)
class AccountingRecord:
    id: str
    date: date
    amount: Decimal
    reference: str | None
    entity: str | None
    description: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "amount": format(self.amount, "f"),
            "reference": self.reference,
            "entity": self.entity,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> AccountingRecord:
        return cls(
            id=str(value["id"]),
            date=date.fromisoformat(str(value["date"])),
            amount=Decimal(str(value["amount"])),
            reference=_optional_string(value.get("reference")),
            entity=_optional_string(value.get("entity")),
            description=_optional_string(value.get("description")),
        )


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    case_id: str
    seed: int
    scenario: str
    transaction: BankTransaction
    candidates: tuple[AccountingRecord, ...]
    true_candidate_id: str
    perturbations: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "seed": self.seed,
            "scenario": self.scenario,
            "transaction": self.transaction.to_dict(),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "true_candidate_id": self.true_candidate_id,
            "perturbations": list(self.perturbations),
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> BenchmarkCase:
        candidates_raw = value.get("candidates")
        if not isinstance(candidates_raw, list):
            raise ValueError("'candidates' tem de ser uma lista.")
        perturbations_raw = value.get("perturbations", [])
        if not isinstance(perturbations_raw, list):
            raise ValueError("'perturbations' tem de ser uma lista.")
        return cls(
            case_id=str(value["case_id"]),
            seed=int(value["seed"]),
            scenario=str(value["scenario"]),
            transaction=BankTransaction.from_dict(_expect_dict(value["transaction"])),
            candidates=tuple(
                AccountingRecord.from_dict(_expect_dict(item)) for item in candidates_raw
            ),
            true_candidate_id=str(value["true_candidate_id"]),
            perturbations=tuple(str(item) for item in perturbations_raw),
        )

    def true_candidate(self) -> AccountingRecord:
        matches = [candidate for candidate in self.candidates if candidate.id == self.true_candidate_id]
        if len(matches) != 1:
            raise ValueError(
                f"O caso {self.case_id} deveria conter exatamente um true candidate; "
                f"encontrados {len(matches)}."
            )
        return matches[0]


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text != "" else None


def _expect_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("Era esperado um objeto JSON.")
    return value
