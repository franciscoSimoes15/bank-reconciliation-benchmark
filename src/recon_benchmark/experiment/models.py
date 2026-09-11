"""Immutable experiment parameters and invariants."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from recon_benchmark.domain.models import MatchingMethod, Scenario


DEFAULT_SCENARIOS: tuple[Scenario, ...] = tuple(Scenario)
DEFAULT_METHODS: tuple[MatchingMethod, ...] = tuple(MatchingMethod)


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    """Shared parameters controlling generation, scoring and final evaluation.

    The frozen dataclass prevents field reassignment during a run. Decimal values
    configure amount comparisons; scales control gradual scores, and tie_epsilon
    is an absolute score tolerance. validate() must be called explicitly.
    Development commands can pass run-specific sizes and methods separately.
    """
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
        """Reject invalid sizes, tolerances, seeds or protocol composition with ValueError.

        Require the configured candidate split and complete ordered scenario/method
        sets. This validates parameters; it does not generate or inspect any cases.
        """
        if self.cases_per_scenario <= 0:
            raise ValueError("cases_per_scenario must be positive.")
        if self.natural_negative_count != 6:
            raise ValueError("The protocol requires exactly 6 natural negatives.")
        if self.controlled_hard_negative_count != 3:
            raise ValueError("The protocol requires exactly 3 controlled hard negatives.")
        expected_candidates = 1 + self.natural_negative_count + self.controlled_hard_negative_count
        if self.candidates_per_case != expected_candidates:
            raise ValueError(
                "The protocol requires exactly 10 candidates: "
                "1 true + 6 natural negatives + 3 controlled hard negatives."
            )
        if not self.evaluation_seeds:
            raise ValueError("At least one evaluation seed is required.")
        if len(self.evaluation_seeds) != len(set(self.evaluation_seeds)):
            raise ValueError("Evaluation seeds must not contain duplicates.")
        if self.amount_tolerance < 0:
            raise ValueError("amount_tolerance must not be negative.")
        if self.date_tolerance_days < 0:
            raise ValueError("date_tolerance_days must not be negative.")
        if self.amount_similarity_absolute_scale <= 0:
            raise ValueError("amount_similarity_absolute_scale must be positive.")
        if self.amount_similarity_relative_scale <= 0:
            raise ValueError("amount_similarity_relative_scale must be positive.")
        if self.date_similarity_scale_days <= 0:
            raise ValueError("date_similarity_scale_days must be positive.")
        if self.qgram_size < 1:
            raise ValueError("qgram_size must be >= 1.")
        if self.tie_epsilon < 0:
            raise ValueError("tie_epsilon must not be negative.")
        if self.scenarios != DEFAULT_SCENARIOS:
            raise ValueError("The protocol requires all eight scenarios in P0–P7 order.")
        if self.methods != DEFAULT_METHODS:
            raise ValueError("The protocol requires M0–M4 and the M4-D ablation to be configured.")

    def to_dict(self) -> dict[str, object]:
        """Return JSON-compatible parameters for the experiment manifest.

        Represent Decimal values as strings, enum members by their descriptive values,
        and tuples as lists so the recorded configuration can be inspected and reloaded.
        """
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
