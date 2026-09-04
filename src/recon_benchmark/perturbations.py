from __future__ import annotations

import random
import re
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from recon_benchmark.models import BankTransaction
from recon_benchmark.normalization import normalize_amount

_AMOUNT_DELTAS: tuple[Decimal, ...] = tuple(
    Decimal(value) for value in ("-0.10", "-0.05", "-0.01", "0.01", "0.05", "0.10")
)
_DATE_DRIFTS: tuple[int, ...] = (-3, -2, -1, 1, 2, 3)

_ACCENT_VARIANTS: dict[str, str] = {
    "ATLANTICO": "ATLÂNTICO",
    "ORBITA": "ÓRBITA",
    "SERVICOS": "SERVIÇOS",
    "LOGISTICA": "LOGÍSTICA",
    "COMERCIO": "COMÉRCIO",
    "CONSTRUCOES": "CONSTRUÇÕES",
    "GESTAO": "GESTÃO",
    "MANUTENCAO": "MANUTENÇÃO",
    "IMOBILIARIA": "IMOBILIÁRIA",
}


def apply_perturbation(
    transaction: BankTransaction,
    scenario: str,
    rng: random.Random,
    scenario_index: int,
) -> tuple[BankTransaction, tuple[str, ...]]:
    if scenario == "P0_CLEAN":
        return transaction, ()
    if scenario == "P1_AMOUNT_NOISE":
        return _amount_noise(transaction, rng)
    if scenario == "P2_DATE_DRIFT":
        return _date_drift(transaction, rng)
    if scenario == "P3_REFERENCE_NOISE":
        return _reference_noise(transaction, rng)
    if scenario == "P4_ENTITY_NOISE":
        return _entity_noise(transaction, rng)
    if scenario == "P5_DESCRIPTION_NOISE":
        return _description_noise(transaction, rng)
    if scenario == "P6_MISSING_INFORMATION":
        return _missing_information(transaction, scenario_index)
    if scenario == "P7_COMBINED":
        return _combined_noise(transaction, rng)
    raise ValueError(f"Cenário desconhecido: {scenario}")


def _amount_noise(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    delta = rng.choice(_AMOUNT_DELTAS)
    changed = replace(transaction, amount=normalize_amount(transaction.amount + delta))
    return changed, (f"amount:{delta:+}",)


def _date_drift(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    days = rng.choice(_DATE_DRIFTS)
    changed = replace(transaction, date=transaction.date + timedelta(days=days))
    return changed, (f"date:{days:+d}d",)


def _reference_noise(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    if transaction.reference is None:
        return transaction, ("reference:none",)
    operation = rng.choice(("separators", "compact", "transpose", "substitute"))
    changed_reference = perturb_reference(transaction.reference, operation, rng)
    return replace(transaction, reference=changed_reference), (f"reference:{operation}",)


def perturb_reference(reference: str, operation: str, rng: random.Random) -> str:
    if operation == "separators":
        match = re.fullmatch(r"([A-Za-z]+)(\d{4})/(\d+)", reference)
        if match:
            return f"{match.group(1)} {match.group(2)} {match.group(3)}"
        return reference.replace("/", " ").replace("-", " ")
    if operation == "compact":
        return "".join(char for char in reference if char.isalnum())

    digit_positions = [index for index, char in enumerate(reference) if char.isdigit()]
    if not digit_positions:
        return reference + "X"

    if operation == "transpose" and len(digit_positions) >= 2:
        adjacent_pairs = [
            (left, right)
            for left, right in zip(digit_positions, digit_positions[1:])
            if right == left + 1 and reference[left] != reference[right]
        ]
        if adjacent_pairs:
            left, right = rng.choice(adjacent_pairs)
            chars = list(reference)
            chars[left], chars[right] = chars[right], chars[left]
            return "".join(chars)
        operation = "substitute"

    if operation == "substitute":
        position = rng.choice(digit_positions)
        original = reference[position]
        replacement = str((int(original) + rng.randint(1, 9)) % 10)
        chars = list(reference)
        chars[position] = replacement
        return "".join(chars)

    raise ValueError(f"Operação de referência desconhecida: {operation}")


def _entity_noise(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    if transaction.counterparty is None:
        return transaction, ("entity:none",)
    operation = rng.choice(("remove_suffix", "truncate", "typo", "case_accent"))
    value = transaction.counterparty
    if operation == "remove_suffix":
        tokens = value.split()
        if tokens and tokens[-1].upper() in {"LDA", "SA"}:
            value = " ".join(tokens[:-1])
    elif operation == "truncate":
        cutoff = max(4, int(len(value) * 0.60))
        value = value[:cutoff].rstrip()
    elif operation == "typo":
        value = _transpose_word_character(value, rng)
    elif operation == "case_accent":
        for source, target in _ACCENT_VARIANTS.items():
            value = value.replace(source, target)
        value = value.title()
    return replace(transaction, counterparty=value), (f"entity:{operation}",)


def _description_noise(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    if transaction.description is None:
        return transaction, ("description:none",)
    operation = rng.choice(("reorder", "delete_token", "truncate", "boilerplate", "abbreviate"))
    value = transaction.description
    tokens = value.split()
    if operation == "reorder" and len(tokens) >= 4:
        pivot = max(1, len(tokens) // 2)
        value = " ".join(tokens[pivot:] + tokens[:pivot])
    elif operation == "delete_token" and len(tokens) >= 3:
        removable = [index for index, token in enumerate(tokens) if len(token) > 2]
        if removable:
            del tokens[rng.choice(removable)]
        value = " ".join(tokens)
    elif operation == "truncate":
        cutoff = max(8, int(len(value) * 0.75))
        value = value[:cutoff].rstrip()
    elif operation == "boilerplate":
        prefix = rng.choice(("OPERACAO PROCESSADA", "MOVIMENTO BANCARIO", "PAGAMENTO SEPA"))
        value = f"{prefix} {value}"
    elif operation == "abbreviate":
        replacements = {
            "PAGAMENTO": "PAG",
            "TRANSFERENCIA": "TRF",
            "COMISSAO": "COM",
            "SERVICO": "SRV",
            "ENTIDADE": "ENT",
            "PUBLICA": "PUB",
        }
        for source, target in replacements.items():
            value = re.sub(rf"\b{source}\b", target, value, flags=re.IGNORECASE)
    return replace(transaction, description=value), (f"description:{operation}",)


def _missing_information(
    transaction: BankTransaction, scenario_index: int
) -> tuple[BankTransaction, tuple[str, ...]]:
    if scenario_index % 2 == 0:
        return replace(transaction, reference=None), ("missing:reference",)
    return replace(transaction, counterparty=None), ("missing:counterparty",)


def _combined_noise(
    transaction: BankTransaction, rng: random.Random
) -> tuple[BankTransaction, tuple[str, ...]]:
    families = rng.sample(("amount", "date", "reference", "entity", "description"), k=3)
    current = transaction
    tags: list[str] = []
    for family in families:
        if family == "amount":
            current, new_tags = _amount_noise(current, rng)
        elif family == "date":
            current, new_tags = _date_drift(current, rng)
        elif family == "reference":
            current, new_tags = _reference_noise(current, rng)
        elif family == "entity":
            current, new_tags = _entity_noise(current, rng)
        else:
            current, new_tags = _description_noise(current, rng)
        tags.extend(new_tags)
    return current, tuple(tags)


def _transpose_word_character(value: str, rng: random.Random) -> str:
    words = value.split()
    candidates = [index for index, word in enumerate(words) if len(word) >= 5]
    if not candidates:
        return value + "X"
    word_index = rng.choice(candidates)
    word = words[word_index]
    position = rng.randrange(1, len(word) - 1)
    if word[position] == word[position + 1]:
        position = max(0, position - 1)
    chars = list(word)
    chars[position], chars[position + 1] = chars[position + 1], chars[position]
    words[word_index] = "".join(chars)
    return " ".join(words)
