from __future__ import annotations

import json
from collections.abc import Mapping
from decimal import Decimal
from pathlib import Path

from recon_benchmark.domain.models import MatchingMethod, Scenario
from recon_benchmark.experiment.models import DEFAULT_METHODS, DEFAULT_SCENARIOS, ExperimentConfig


def load_config(path: str | Path | None = None) -> ExperimentConfig:
    if path is None:
        config = ExperimentConfig()
        config.validate()
        return config

    loaded: object = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping) or not all(isinstance(key, str) for key in loaded):
        raise ValueError("A configuração tem de ser um objeto JSON.")
    raw: Mapping[str, object] = loaded

    config = ExperimentConfig(
        cases_per_scenario=_integer(raw, "cases_per_scenario", 100),
        candidates_per_case=_integer(raw, "candidates_per_case", 10),
        natural_negative_count=_integer(raw, "natural_negative_count", 6),
        controlled_hard_negative_count=_integer(raw, "controlled_hard_negative_count", 3),
        development_seed=_integer(raw, "development_seed", 7),
        evaluation_seeds=tuple(
            _integer_value(seed, "evaluation_seeds")
            for seed in _list(raw, "evaluation_seeds", [42, 43, 44, 45, 46])
        ),
        amount_tolerance=_decimal(raw, "amount_tolerance", "0.10"),
        date_tolerance_days=_integer(raw, "date_tolerance_days", 3),
        amount_similarity_absolute_scale=_decimal(
            raw, "amount_similarity_absolute_scale", "1.00"
        ),
        amount_similarity_relative_scale=_decimal(
            raw, "amount_similarity_relative_scale", "0.01"
        ),
        date_similarity_scale_days=_integer(raw, "date_similarity_scale_days", 30),
        qgram_size=_integer(raw, "qgram_size", 3),
        tie_epsilon=_float(raw, "tie_epsilon", 1e-12),
        scenarios=tuple(
            Scenario(_string_value(item, "scenarios"))
            for item in _list(raw, "scenarios", [item.value for item in DEFAULT_SCENARIOS])
        ),
        methods=tuple(
            MatchingMethod(_string_value(item, "methods"))
            for item in _list(raw, "methods", [item.value for item in DEFAULT_METHODS])
        ),
    )
    config.validate()
    return config


def _integer(raw: Mapping[str, object], key: str, default: int) -> int:
    return _integer_value(raw.get(key, default), key)


def _integer_value(value: object, key: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} tem de ser inteiro.")
    return value


def _decimal(raw: Mapping[str, object], key: str, default: str) -> Decimal:
    value = raw.get(key, default)
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} tem de ser numérico.")
    return Decimal(str(value))


def _float(raw: Mapping[str, object], key: str, default: float) -> float:
    value = raw.get(key, default)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} tem de ser numérico.")
    return float(value)


def _list(raw: Mapping[str, object], key: str, default: list[object]) -> list[object]:
    value = raw.get(key, default)
    if not isinstance(value, list):
        raise ValueError(f"{key} tem de ser uma lista.")
    return value


def _string_value(value: object, key: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{key} só pode conter texto.")
    return value
