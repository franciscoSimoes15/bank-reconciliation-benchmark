"""Validate fields received by from_dict constructors."""

from collections.abc import Mapping


def _required_string(raw: Mapping[str, object], key: str) -> str:
    """Read a required text field; report missing keys or invalid types as ValueError."""
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    return _string_value(raw[key], key)


def _string_value(value: object, name: str) -> str:
    """Require a string without coercing numbers or other values into text."""
    if not isinstance(value, str):
        raise ValueError(f"{name} must be text.")
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
        raise ValueError(f"{key} must be an integer.")
    return value


def _required_mapping(raw: Mapping[str, object], key: str) -> Mapping[str, object]:
    """Read a required nested object and check that all its keys are strings."""
    if key not in raw:
        raise ValueError(f"Missing required field: {key}")
    return _mapping_value(raw[key], key)


def _mapping_value(value: object, name: str) -> Mapping[str, object]:
    """Require a mapping with text keys before reconstructing a nested model."""
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object.")
    if not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} may have only text keys.")
    return value


def _required_list(raw: Mapping[str, object], key: str) -> list[object]:
    """Require a list field before reconstructing candidates or perturbation labels."""
    value = raw.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list.")
    return value
