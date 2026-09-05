"""Validação dos campos recebidos pelos construtores from_dict."""

from collections.abc import Mapping


def _required_string(raw: Mapping[str, object], key: str) -> str:
    """Read a required text field; report missing keys or invalid types as ValueError."""
    if key not in raw:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return _string_value(raw[key], key)


def _string_value(value: object, name: str) -> str:
    """Require a string without coercing numbers or other values into text."""
    if not isinstance(value, str):
        raise ValueError(f"{name} tem de ser texto.")
    return value


def _optional_string(value: object, name: str) -> str | None:
    """Preserve an absent field as None; otherwise require a text value."""
    if value is None:
        return None
    return _string_value(value, name)


def _required_int(raw: Mapping[str, object], key: str) -> int:
    """Read an integer field while rejecting booleans, which Python treats as integers."""
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} tem de ser inteiro.")
    return value


def _required_mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Read a required nested object and check that all its keys are strings."""
    if key not in raw:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return _mapping_value(raw[key], key)


def _mapping_value(value: object, name: str) -> Mapping[str, object]:
    """Require a mapping with text keys before reconstructing a nested model."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} tem de ser um objeto.")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} só pode ter chaves de texto.")
    return value


def _required_list(raw: Mapping[str, object], key: str) -> list[object]:
    """Require a list field before reconstructing candidates or perturbation labels."""
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} tem de ser uma lista.")
    return value
