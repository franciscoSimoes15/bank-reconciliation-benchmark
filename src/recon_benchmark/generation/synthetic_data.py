from __future__ import annotations

import random
import re
from datetime import date, timedelta
from decimal import Decimal

from recon_benchmark.domain.models import (
    AccountingRecord,
    BankTransaction,
    FinancialEvent,
    OperationType,
)
from recon_benchmark.normalization.fields import normalize_amount
from recon_benchmark.templates.accounting import ACCOUNTING_DESCRIPTIONS
from recon_benchmark.templates.accounting import REFERENCE_TEMPLATES as ACCOUNTING_REFERENCE_TEMPLATES
from recon_benchmark.templates.bank import BANK_DESCRIPTIONS
from recon_benchmark.templates.bank import REFERENCE_TEMPLATES as BANK_REFERENCE_TEMPLATES

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

_LEGAL_SUFFIXES: tuple[str, ...] = ("LDA", "SA")
_OPERATION_TYPES: tuple[OperationType, ...] = tuple(OperationType)

_REFERENCE_PREFIX: dict[OperationType, str] = {
    OperationType.SUPPLIER_TRANSFER: "FT",
    OperationType.CUSTOMER_RECEIPT: "REC",
    OperationType.DIRECT_DEBIT: "MD",
    OperationType.TAX_PAYMENT: "DUC",
}

_AMOUNT_RANGES_CENTS: dict[OperationType, tuple[int, int]] = {
    OperationType.SUPPLIER_TRANSFER: (5_000, 1_000_000),
    OperationType.CUSTOMER_RECEIPT: (2_500, 1_500_000),
    OperationType.DIRECT_DEBIT: (1_500, 200_000),
    OperationType.CARD_PAYMENT: (300, 50_000),
    OperationType.BANK_FEE: (100, 5_000),
    OperationType.TAX_PAYMENT: (10_000, 2_000_000),
}


def generate_financial_event(
    rng: random.Random,
    *,
    seed: int,
    index: int,
    event_id: str,
) -> FinancialEvent:
    operation_type = _OPERATION_TYPES[(index + seed) % len(_OPERATION_TYPES)]
    event_date = _BASE_DATE + timedelta(days=rng.randrange(180))
    minimum, maximum = _AMOUNT_RANGES_CENTS[operation_type]
    absolute_amount = Decimal(rng.randint(minimum, maximum)) / Decimal(100)
    signed_amount = (
        absolute_amount
        if operation_type is OperationType.CUSTOMER_RECEIPT
        else -absolute_amount
    )

    if operation_type is OperationType.BANK_FEE:
        legal_name = None
        bank_alias = None
    else:
        legal_name, bank_alias = generate_entity_names(rng, index)

    reference_prefix = _REFERENCE_PREFIX.get(operation_type)
    reference = (
        None
        if reference_prefix is None
        else f"{reference_prefix}-{event_date.year}-{seed * 10_000 + index + 1:07d}"
    )
    return FinancialEvent(
        event_id=event_id,
        operation_type=operation_type,
        event_date=event_date,
        amount=normalize_amount(signed_amount),
        entity_legal_name=legal_name,
        entity_bank_alias=bank_alias,
        document_reference=reference,
    )


def generate_entity_names(rng: random.Random, index: int) -> tuple[str, str]:
    prefix = _ENTITY_PREFIXES[(index + rng.randrange(len(_ENTITY_PREFIXES))) % len(_ENTITY_PREFIXES)]
    domain = _ENTITY_DOMAINS[(index * 3 + rng.randrange(len(_ENTITY_DOMAINS))) % len(_ENTITY_DOMAINS)]
    suffix = _LEGAL_SUFFIXES[(index + rng.randrange(len(_LEGAL_SUFFIXES))) % len(_LEGAL_SUFFIXES)]
    legal_name = f"{prefix} {domain} {suffix}"
    alias = f"{prefix.title()} {domain[:5].title()}"
    return legal_name, alias


def render_bank_transaction(
    event: FinancialEvent,
    rng: random.Random,
    *,
    transaction_id: str,
) -> BankTransaction:
    posting_delay = rng.choice((0, 0, 1, 2))
    reference = _render_bank_reference(event.document_reference, rng)
    counterparty = (
        "INSTITUICAO BANCARIA"
        if event.operation_type is OperationType.BANK_FEE
        else event.entity_bank_alias
    )
    description = rng.choice(BANK_DESCRIPTIONS[event.operation_type])
    return BankTransaction(
        id=transaction_id,
        date=event.event_date + timedelta(days=posting_delay),
        amount=event.amount,
        reference=reference,
        counterparty=counterparty,
        description=description,
    )


def render_accounting_record(
    event: FinancialEvent,
    rng: random.Random,
    *,
    record_id: str,
) -> AccountingRecord:
    reference = _render_accounting_reference(event.document_reference, rng)
    description = rng.choice(ACCOUNTING_DESCRIPTIONS[event.operation_type])
    return AccountingRecord(
        id=record_id,
        date=event.event_date,
        amount=event.amount,
        reference=reference,
        entity=event.entity_legal_name,
        description=description,
    )


def near_document_reference(reference: str | None, offset: int) -> str | None:
    if reference is None:
        return None
    match = re.fullmatch(r"([A-Z]+)-(\d{4})-(\d+)", reference)
    if match is None:
        raise ValueError(f"Formato de referência latente inesperado: {reference}")
    number = int(match.group(3)) + offset
    return f"{match.group(1)}-{match.group(2)}-{number:0{len(match.group(3))}d}"


def _render_bank_reference(reference: str | None, rng: random.Random) -> str | None:
    if reference is None:
        return None
    prefix, year, number = reference.split("-")
    templates = tuple(
        template.format(prefix=prefix, year=year, number=number)
        for template in BANK_REFERENCE_TEMPLATES
    )
    return rng.choice(templates)


def _render_accounting_reference(reference: str | None, rng: random.Random) -> str | None:
    if reference is None:
        return None
    prefix, year, number = reference.split("-")
    templates = tuple(
        template.format(prefix=prefix, year=year, number=number)
        for template in ACCOUNTING_REFERENCE_TEMPLATES
    )
    return rng.choice(templates)
