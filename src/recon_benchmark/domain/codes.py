"""Mapeamento dos nomes descritivos para os códigos usados nos outputs."""

from collections.abc import Mapping

from recon_benchmark.domain.models import MatchingMethod, Scenario


_METHOD_CODES: Mapping[MatchingMethod, str] = {
    MatchingMethod.NORMALIZED_EXACT: "M0",
    MatchingMethod.TOLERANT_DETERMINISTIC: "M1",
    MatchingMethod.JARO_WINKLER_TEXT: "M2",
    MatchingMethod.CHARACTER_TRIGRAM_TEXT: "M3",
    MatchingMethod.FIELD_AWARE: "M4",
    MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION: "M4-D",
}

_SCENARIO_CODES: Mapping[Scenario, str] = {
    Scenario.NATURAL_VARIATION: "P0",
    Scenario.AMOUNT_VARIATION: "P1",
    Scenario.DATE_VARIATION: "P2",
    Scenario.REFERENCE_VARIATION: "P3",
    Scenario.ENTITY_VARIATION: "P4",
    Scenario.DESCRIPTION_VARIATION: "P5",
    Scenario.MISSING_INFORMATION: "P6",
    Scenario.COMBINED_VARIATION: "P7",
}


def method_code(method: MatchingMethod) -> str:
    """Return the publication/output code for a descriptive matching method."""
    return _METHOD_CODES[method]


def scenario_code(scenario: Scenario) -> str:
    """Return the P0-P7 output code for an experimental scenario."""
    return _SCENARIO_CODES[scenario]
