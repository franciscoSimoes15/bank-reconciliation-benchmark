from __future__ import annotations

import random
import re
from dataclasses import replace
from datetime import timedelta
from decimal import Decimal

from recon_benchmark.domain.models import BankTransaction, Scenario
from recon_benchmark.generation.errors import PerturbationNoOpError
from recon_benchmark.normalization.fields import normalize_amount

_FIXED_AMOUNT_DELTAS: tuple[Decimal, ...] = (
    Decimal("-0.25"),
    Decimal("-0.05"),
    Decimal("0.05"),
    Decimal("0.25"),
)
_DATE_DRIFTS: tuple[int, ...] = (-30, -10, -3, -1, 1, 3, 10, 30)

_ACCENT_VARIANTS: dict[str, str] = {
    "Atlantico": "Atlântico",
    "Orbita": "Órbita",
    "Servi": "Serví",
    "Logis": "Logís",
    "Comer": "Comér",
}


def apply_perturbation(
    transaction: BankTransaction,
    scenario: Scenario,
    rng: random.Random,
    scenario_index: int,
) -> tuple[BankTransaction, tuple[str, ...]]:
    if scenario is Scenario.NATURAL_VARIATION:
        return transaction, ()
    if scenario is Scenario.AMOUNT_VARIATION:
        return _amount_variation(transaction, rng)
    if scenario is Scenario.DATE_VARIATION:
        return _date_variation(transaction, rng)
    if scenario is Scenario.REFERENCE_VARIATION:
        return _reference_variation(transaction, rng)
    if scenario is Scenario.ENTITY_VARIATION:
        return _entity_variation(transaction, rng)
    if scenario is Scenario.DESCRIPTION_VARIATION:
        return _description_variation(transaction, rng)
    if scenario is Scenario.MISSING_INFORMATION:
        return _missing_information(transaction, scenario_index)
    if scenario is Scenario.COMBINED_VARIATION:
        return _combined_variation(transaction, rng)
    raise ValueError(f"Cenário desconhecido: {scenario}")


def perturb_reference(reference: str, operation: str, rng: random.Random) -> str:
    if operation == "separators":
        separated = re.sub(r"[\s/._-]+", ".", reference).strip(".")
        if separated == reference:
            match = re.fullmatch(r"([A-Za-z]+)(\d{4})(\d+)", reference)
            if match is not None:
                separated = ".".join(match.groups())
        return separated
    if operation == "compact":
        return "".join(character for character in reference if character.isalnum())

    digit_positions = [index for index, character in enumerate(reference) if character.isdigit()]
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
            characters = list(reference)
            characters[left], characters[right] = characters[right], characters[left]
            return "".join(characters)
        operation = "substitute"

    if operation == "substitute":
        position = rng.choice(digit_positions)
        original = reference[position]
        replacement = str((int(original) + rng.randint(1, 9)) % 10)
        characters = list(reference)
        characters[position] = replacement
        return "".join(characters)

    raise ValueError(f"Operação de referência desconhecida: {operation}")


def _amount_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    relative_delta = normalize_amount(max(Decimal("0.01"), abs(transaction.amount) * Decimal("0.005")))
    deltas = (*_FIXED_AMOUNT_DELTAS, -relative_delta, relative_delta)
    delta = rng.choice(tuple(item for item in deltas if item != Decimal("0.00")))
    changed = replace(transaction, amount=normalize_amount(transaction.amount + delta))
    return _checked(transaction, changed, f"amount:{delta:+f}")


def _date_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    days = rng.choice(_DATE_DRIFTS)
    changed = replace(transaction, date=transaction.date + timedelta(days=days))
    return _checked(transaction, changed, f"date:{days:+d}d")


def _reference_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    if transaction.reference is None:
        trace_reference = f"TRACE-{rng.randrange(100_000_000):08d}"
        changed = replace(transaction, reference=trace_reference)
        return _checked(transaction, changed, "reference:add_bank_trace")

    alternatives = tuple(
        (operation, value)
        for operation in ("separators", "compact", "transpose", "substitute")
        if (value := perturb_reference(transaction.reference, operation, rng))
        != transaction.reference
    )
    if not alternatives:
        raise PerturbationNoOpError("Nenhuma perturbação de referência alterou o valor.")
    operation, value = rng.choice(alternatives)
    changed = replace(transaction, reference=value)
    return _checked(transaction, changed, f"reference:{operation}")


def _entity_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    if transaction.counterparty is None:
        changed = replace(transaction, counterparty="ENTIDADE NAO IDENTIFICADA")
        return _checked(transaction, changed, "entity:add_bank_label")

    value = transaction.counterparty
    alternatives: list[tuple[str, str]] = []
    tokens = value.split()
    if tokens and tokens[-1].upper() in {"LDA", "SA"}:
        alternatives.append(("remove_suffix", " ".join(tokens[:-1])))
    cutoff = max(4, int(len(value) * 0.60))
    alternatives.append(("truncate", value[:cutoff].rstrip()))
    alternatives.append(("typo", _transpose_word_character(value, rng)))
    accented = value
    for source, target in _ACCENT_VARIANTS.items():
        accented = accented.replace(source, target)
    alternatives.append(("case_accent", accented.swapcase()))
    changed_alternatives = tuple(item for item in alternatives if item[1] != value)
    if not changed_alternatives:
        raise PerturbationNoOpError("Nenhuma perturbação de entidade alterou o valor.")
    operation, changed_value = rng.choice(changed_alternatives)
    changed = replace(transaction, counterparty=changed_value)
    return _checked(transaction, changed, f"entity:{operation}")


def _description_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    value = transaction.description
    tokens = value.split()
    alternatives: list[tuple[str, str]] = []
    if len(tokens) >= 2:
        pivot = max(1, len(tokens) // 2)
        alternatives.append(("reorder", " ".join(tokens[pivot:] + tokens[:pivot])))
    removable = [index for index, token in enumerate(tokens) if len(token) > 2]
    if removable:
        shortened = tokens.copy()
        del shortened[rng.choice(removable)]
        alternatives.append(("delete_token", " ".join(shortened)))
    cutoff = max(4, int(len(value) * 0.70))
    alternatives.append(("truncate", value[:cutoff].rstrip()))
    alternatives.append(("boilerplate", f"MOVIMENTO PROCESSADO {value}"))
    abbreviated = value
    replacements = {
        "PAGAMENTO": "PAG",
        "TRANSFERENCIA": "TRF",
        "COMISSAO": "COM",
        "SERVICOS": "SRV",
        "EMPRESA": "EMP",
    }
    for source, target in replacements.items():
        abbreviated = re.sub(rf"\b{source}\b", target, abbreviated, flags=re.IGNORECASE)
    alternatives.append(("abbreviate", abbreviated))

    changed_alternatives = tuple(item for item in alternatives if item[1] != value)
    if not changed_alternatives:
        raise PerturbationNoOpError("Nenhuma perturbação de descrição alterou o valor.")
    operation, changed_value = rng.choice(changed_alternatives)
    changed = replace(transaction, description=changed_value)
    return _checked(transaction, changed, f"description:{operation}")


def _missing_information(
    transaction: BankTransaction,
    scenario_index: int,
) -> tuple[BankTransaction, tuple[str, ...]]:
    alternatives: list[tuple[str, BankTransaction]] = []
    if transaction.reference is not None:
        alternatives.append(("missing:reference", replace(transaction, reference=None)))
    if transaction.counterparty is not None:
        alternatives.append(("missing:counterparty", replace(transaction, counterparty=None)))
    if not alternatives:
        raise PerturbationNoOpError("O movimento não contém informação opcional removível.")
    tag, changed = alternatives[scenario_index % len(alternatives)]
    return _checked(transaction, changed, tag)


def _combined_variation(
    transaction: BankTransaction,
    rng: random.Random,
) -> tuple[BankTransaction, tuple[str, ...]]:
    families = rng.sample(("amount", "date", "reference", "entity", "description"), k=3)
    current = transaction
    tags: list[str] = []
    for family in families:
        if family == "amount":
            current, new_tags = _amount_variation(current, rng)
        elif family == "date":
            current, new_tags = _date_variation(current, rng)
        elif family == "reference":
            current, new_tags = _reference_variation(current, rng)
        elif family == "entity":
            current, new_tags = _entity_variation(current, rng)
        else:
            current, new_tags = _description_variation(current, rng)
        tags.extend(new_tags)
    if current == transaction or len(tags) != 3:
        raise PerturbationNoOpError("A perturbação combinada não alterou três famílias.")
    return current, tuple(tags)


def _checked(
    original: BankTransaction,
    changed: BankTransaction,
    tag: str,
) -> tuple[BankTransaction, tuple[str, ...]]:
    if changed == original:
        raise PerturbationNoOpError(f"Perturbação no-op detetada: {tag}")
    return changed, (tag,)


def _transpose_word_character(value: str, rng: random.Random) -> str:
    words = value.split()
    candidates = [index for index, word in enumerate(words) if len(word) >= 4]
    if not candidates:
        return value + "X"
    word_index = rng.choice(candidates)
    word = words[word_index]
    pairs = [index for index in range(len(word) - 1) if word[index] != word[index + 1]]
    if not pairs:
        return value + "X"
    position = rng.choice(pairs)
    characters = list(word)
    characters[position], characters[position + 1] = (
        characters[position + 1],
        characters[position],
    )
    words[word_index] = "".join(characters)
    return " ".join(words)
