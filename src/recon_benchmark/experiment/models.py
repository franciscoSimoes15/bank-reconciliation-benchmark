"""Parâmetros imutáveis e invariantes da experiência."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from recon_benchmark.domain.models import MatchingMethod, Scenario


DEFAULT_SCENARIOS: tuple[Scenario, ...] = tuple(Scenario)
DEFAULT_METHODS: tuple[MatchingMethod, ...] = tuple(MatchingMethod)


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    cases_per_scenario: int = 100
    candidates_per_case: int = 10
    natural_negative_count: int = 6
    controlled_hard_negative_count: int = 3
    development_seed: int = 7
    evaluation_seeds: tuple[int, ...] = (42, 43, 44, 45, 46)
    amount_tolerance: Decimal = Decimal("0.10")
    date_tolerance_days: int = 3
    amount_similarity_absolute_scale: Decimal = Decimal("1.00")
    amount_similarity_relative_scale: Decimal = Decimal("0.01")
    date_similarity_scale_days: int = 30
    qgram_size: int = 3
    tie_epsilon: float = 1e-12
    scenarios: tuple[Scenario, ...] = DEFAULT_SCENARIOS
    methods: tuple[MatchingMethod, ...] = DEFAULT_METHODS

    def validate(self) -> None:
        if self.cases_per_scenario <= 0:
            raise ValueError("cases_per_scenario tem de ser positivo.")
        if self.natural_negative_count != 6:
            raise ValueError("O protocolo exige exatamente 6 natural negatives.")
        if self.controlled_hard_negative_count != 3:
            raise ValueError("O protocolo exige exatamente 3 controlled hard negatives.")
        expected_candidates = 1 + self.natural_negative_count + self.controlled_hard_negative_count
        if self.candidates_per_case != expected_candidates:
            raise ValueError(
                "O protocolo exige exatamente 10 candidatos: "
                "1 true + 6 natural negatives + 3 controlled hard negatives."
            )
        if not self.evaluation_seeds:
            raise ValueError("É necessária pelo menos uma evaluation seed.")
        if len(self.evaluation_seeds) != len(set(self.evaluation_seeds)):
            raise ValueError("As evaluation seeds não podem estar duplicadas.")
        if self.amount_tolerance < 0:
            raise ValueError("amount_tolerance não pode ser negativa.")
        if self.date_tolerance_days < 0:
            raise ValueError("date_tolerance_days não pode ser negativo.")
        if self.amount_similarity_absolute_scale <= 0:
            raise ValueError("amount_similarity_absolute_scale tem de ser positiva.")
        if self.amount_similarity_relative_scale <= 0:
            raise ValueError("amount_similarity_relative_scale tem de ser positiva.")
        if self.date_similarity_scale_days <= 0:
            raise ValueError("date_similarity_scale_days tem de ser positivo.")
        if self.qgram_size < 1:
            raise ValueError("qgram_size tem de ser >= 1.")
        if self.tie_epsilon < 0:
            raise ValueError("tie_epsilon não pode ser negativo.")
        if self.scenarios != DEFAULT_SCENARIOS:
            raise ValueError("O protocolo exige os oito cenários na ordem P0–P7.")
        if self.methods != DEFAULT_METHODS:
            raise ValueError("O protocolo exige M0–M4 e a ablation M4-D configurados.")

    def to_dict(self) -> dict[str, object]:
        return {
            "cases_per_scenario": self.cases_per_scenario,
            "candidates_per_case": self.candidates_per_case,
            "natural_negative_count": self.natural_negative_count,
            "controlled_hard_negative_count": self.controlled_hard_negative_count,
            "development_seed": self.development_seed,
            "evaluation_seeds": list(self.evaluation_seeds),
            "amount_tolerance": format(self.amount_tolerance, "f"),
            "date_tolerance_days": self.date_tolerance_days,
            "amount_similarity_absolute_scale": format(
                self.amount_similarity_absolute_scale, "f"
            ),
            "amount_similarity_relative_scale": format(
                self.amount_similarity_relative_scale, "f"
            ),
            "date_similarity_scale_days": self.date_similarity_scale_days,
            "qgram_size": self.qgram_size,
            "tie_epsilon": self.tie_epsilon,
            "scenarios": [scenario.value for scenario in self.scenarios],
            "methods": [method.value for method in self.methods],
        }
