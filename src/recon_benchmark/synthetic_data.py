from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from recon_benchmark.models import AccountingRecord, BankTransaction
from recon_benchmark.normalization import normalize_amount

_BASE_DATE = date(2026, 1, 1)

_ENTITY_PREFIXES: tuple[str, ...] = (
    "ATLANTICO",
    "ORBITA",
    "VECTOR",
    "NOVA",
    "PRISMA",
    "LUSITANIA",
    "HORIZONTE",
    "VERTICE",
    "SOLAR",
    "AURORA",
    "PINHEIRO",
    "RIBEIRA",
    "MONTE",
    "TEJO",
    "DOURO",
    "SERRA",
    "FAROL",
    "PONTE",
    "LITORAL",
    "VALE",
)

_ENTITY_DOMAINS: tuple[str, ...] = (
    "SERVICOS",
    "LOGISTICA",
    "INDUSTRIA",
    "TECNOLOGIA",
    "COMERCIO",
    "ENERGIA",
    "CONSULTORIA",
    "CONSTRUCOES",
    "DISTRIBUICAO",
    "SOLUCOES",
    "GESTAO",
    "ENGENHARIA",
    "MANUTENCAO",
    "TRANSPORTES",
    "ALIMENTAR",
    "IMOBILIARIA",
)

_REFERENCE_PREFIXES: tuple[str, ...] = ("FT", "FR", "INV", "REC", "PG")
_LEGAL_SUFFIXES: tuple[str, ...] = ("LDA", "SA")

_OPERATION_TYPES: tuple[str, ...] = (
    "TRANSFER_OUT",
    "TRANSFER_IN",
    "CARD_PURCHASE",
    "DIRECT_DEBIT",
    "ACCOUNT_FEE",
    "TRANSFER_FEE",
    "STAMP_DUTY",
    "LOAN_PAYMENT",
    "PUBLIC_PAYMENT",
)


def generate_entity(rng: random.Random, index: int) -> str:
    prefix = _ENTITY_PREFIXES[(index + rng.randrange(len(_ENTITY_PREFIXES))) % len(_ENTITY_PREFIXES)]
    domain = _ENTITY_DOMAINS[(index * 3 + rng.randrange(len(_ENTITY_DOMAINS))) % len(_ENTITY_DOMAINS)]
    suffix = _LEGAL_SUFFIXES[(index + rng.randrange(2)) % 2]
    return f"{prefix} {domain} {suffix}"


def generate_reference(seed: int, index: int, rng: random.Random) -> str:
    prefix = _REFERENCE_PREFIXES[(index + rng.randrange(len(_REFERENCE_PREFIXES))) % len(_REFERENCE_PREFIXES)]
    sequence = seed * 10_000 + index + 1
    return f"{prefix}2026/{sequence:05d}"


def generate_amount(rng: random.Random, operation_type: str) -> Decimal:
    cents = rng.randint(1_000, 1_000_000)
    amount = Decimal(cents) / Decimal(100)
    if operation_type == "TRANSFER_IN":
        return normalize_amount(amount)
    return normalize_amount(-amount)


def generate_date(rng: random.Random) -> date:
    return _BASE_DATE + timedelta(days=rng.randrange(180))


def select_operation_type(index: int, rng: random.Random) -> str:
    return _OPERATION_TYPES[(index + rng.randrange(len(_OPERATION_TYPES))) % len(_OPERATION_TYPES)]


def build_description(
    operation_type: str,
    entity: str,
    reference: str,
    index: int,
    occurrence_date: date,
) -> str:
    numeric_reference = "".join(char for char in reference if char.isdigit())
    card_hint = f"{(index * 7919) % 10_000_000:07d}"
    month_token = occurrence_date.strftime("%m%Y")

    templates: dict[str, str] = {
        "TRANSFER_OUT": f"TRF P/ {entity} REF {reference}",
        "TRANSFER_IN": f"TRF DE {entity} REF {reference}",
        "CARD_PURCHASE": f"MDB{card_hint} {entity} REF {reference}",
        "DIRECT_DEBIT": f"DD {entity} MANDATO {reference}",
        "ACCOUNT_FEE": f"COM.MAN.CONTA PACOTE EMPRESA {month_token} REF {reference}",
        "TRANSFER_FEE": f"COMISSAO PROC. TRANSFERENCIA REF {reference}",
        "STAMP_DUTY": f"IMP. SELO COM. TRANSFERENCIA REF {reference}",
        "LOAN_PAYMENT": f"PAGAMENTO EMPRESTIMO N. {numeric_reference}",
        "PUBLIC_PAYMENT": f"PAGAMENTO ENTIDADE PUBLICA REF {reference}",
    }
    return templates[operation_type]


def generate_canonical_record(
    rng: random.Random,
    seed: int,
    global_index: int,
    record_id: str,
) -> AccountingRecord:
    operation_type = select_operation_type(global_index, rng)
    entity = generate_entity(rng, global_index)
    reference = generate_reference(seed, global_index, rng)
    occurrence_date = generate_date(rng)
    amount = generate_amount(rng, operation_type)
    description = build_description(operation_type, entity, reference, global_index, occurrence_date)
    return AccountingRecord(
        id=record_id,
        date=occurrence_date,
        amount=amount,
        reference=reference,
        entity=entity,
        description=description,
    )


def derive_bank_transaction(record: AccountingRecord, transaction_id: str) -> BankTransaction:
    return BankTransaction(
        id=transaction_id,
        date=record.date,
        amount=record.amount,
        reference=record.reference,
        counterparty=record.entity,
        description=record.description,
    )
