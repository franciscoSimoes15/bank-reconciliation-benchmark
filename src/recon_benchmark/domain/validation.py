"""Validação dos campos recebidos pelos construtores from_dict."""

from collections.abc import Mapping


def _required_string(raw: Mapping[str, object], key: str) -> str:
    if key not in raw:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return _string_value(raw[key], key)


def _string_value(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{name} tem de ser texto.")
    return value


def _optional_string(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _string_value(value, name)


def _required_int(raw: Mapping[str, object], key: str) -> int:
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} tem de ser inteiro.")
    return value


def _required_mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    if key not in raw:
        raise ValueError(f"Campo obrigatório ausente: {key}")
    return _mapping_value(raw[key], key)


def _mapping_value(value: object, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} tem de ser um objeto.")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} só pode ter chaves de texto.")
    return value


def _required_list(raw: Mapping[str, object], key: str) -> list[object]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} tem de ser uma lista.")
    return value
