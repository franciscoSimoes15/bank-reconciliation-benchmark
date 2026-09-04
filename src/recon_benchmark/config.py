from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


DEFAULT_SCENARIOS: tuple[str, ...] = (
    "P0_CLEAN",
    "P1_AMOUNT_NOISE",
    "P2_DATE_DRIFT",
    "P3_REFERENCE_NOISE",
    "P4_ENTITY_NOISE",
    "P5_DESCRIPTION_NOISE",
    "P6_MISSING_INFORMATION",
    "P7_COMBINED",
)

DEFAULT_METHODS: tuple[str, ...] = ("M0", "M1", "M2", "M3", "M4", "M4-noNorm")


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    cases_per_scenario: int = 100
    candidates_per_case: int = 10
    development_seed: int = 7
    evaluation_seeds: tuple[int, ...] = (42, 43, 44, 45, 46)
    amount_tolerance: Decimal = Decimal("0.10")
    date_tolerance_days: int = 3
    qgram_size: int = 3
    scenarios: tuple[str, ...] = DEFAULT_SCENARIOS
    methods: tuple[str, ...] = DEFAULT_METHODS

    def validate(self) -> None:
        if self.cases_per_scenario <= 0:
            raise ValueError("cases_per_scenario tem de ser positivo.")
        if self.candidates_per_case != 10:
            raise ValueError("O protocolo exige exatamente 10 candidatos por caso.")
        if self.amount_tolerance < 0:
            raise ValueError("amount_tolerance não pode ser negativa.")
        if self.date_tolerance_days < 0:
            raise ValueError("date_tolerance_days não pode ser negativo.")
        if self.qgram_size < 1:
            raise ValueError("qgram_size tem de ser >= 1.")
        unknown_scenarios = set(self.scenarios) - set(DEFAULT_SCENARIOS)
        if unknown_scenarios:
            raise ValueError(f"Cenários desconhecidos: {sorted(unknown_scenarios)}")
        unknown_methods = set(self.methods) - set(DEFAULT_METHODS)
        if unknown_methods:
            raise ValueError(f"Métodos desconhecidos: {sorted(unknown_methods)}")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["amount_tolerance"] = format(self.amount_tolerance, "f")
        result["evaluation_seeds"] = list(self.evaluation_seeds)
        result["scenarios"] = list(self.scenarios)
        result["methods"] = list(self.methods)
        return result


def load_config(path: str | Path | None = None) -> ExperimentConfig:
    if path is None:
        config = ExperimentConfig()
        config.validate()
        return config

    config_path = Path(path)
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    config = ExperimentConfig(
        cases_per_scenario=int(raw.get("cases_per_scenario", 100)),
        candidates_per_case=int(raw.get("candidates_per_case", 10)),
        development_seed=int(raw.get("development_seed", 7)),
        evaluation_seeds=tuple(int(seed) for seed in raw.get("evaluation_seeds", [42, 43, 44, 45, 46])),
        amount_tolerance=Decimal(str(raw.get("amount_tolerance", "0.10"))),
        date_tolerance_days=int(raw.get("date_tolerance_days", 3)),
        qgram_size=int(raw.get("qgram_size", 3)),
        scenarios=tuple(str(item) for item in raw.get("scenarios", DEFAULT_SCENARIOS)),
        methods=tuple(str(item) for item in raw.get("methods", DEFAULT_METHODS)),
    )
    config.validate()
    return config
