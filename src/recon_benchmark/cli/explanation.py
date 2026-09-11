from __future__ import annotations

from pathlib import Path

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.ranking.models import CandidateScore
from recon_benchmark.ranking.ordering import rank_candidates
from recon_benchmark.ranking.matchers import score_pair
from recon_benchmark.domain.models import BenchmarkCase, MatchingMethod
from recon_benchmark.domain.codes import method_code, scenario_code
from recon_benchmark.normalization.fields import (
    normalize_description,
    normalize_entity,
    normalize_reference,
)


def explain_case(
    case: BenchmarkCase,
    *,
    method: MatchingMethod,
    config: ExperimentConfig,
) -> str:
    """Build a Markdown trace of one case scored with the selected method.

    Show raw/normalized bank fields, candidate scores, excluded fields and ranking.
    Truth is added only as an annotation after scoring, never passed to the matcher.
    Displayed row numbers are visual order, not average ranks for metric ties.
    """
    scored = tuple(
        CandidateScore(
            candidate=candidate.record,
            breakdown=score_pair(
                case.transaction,
                candidate.record,
                method=method,
                config=config,
            ),
        )
        for candidate in case.candidates
    )
    ranked = rank_candidates(scored)

    transaction = case.transaction
    lines = [
        f"# Explanation of case `{case.case_id}`",
        "",
        f"- Seed: `{case.seed}`",
        f"- Scenario: `{case.scenario.value}` ({scenario_code(case.scenario)})",
        f"- Perturbations: `{', '.join(case.perturbations) if case.perturbations else 'none'}`",
        f"- Method: `{method.value}` ({method_code(method)})",
        f"- Ground truth used only for evaluation: `{case.true_candidate_id}`",
        "",
        "## Bank transaction received by the matcher",
        "",
        "| Field | Raw | Normalized |",
        "|---|---|---|",
        f"| Amount | `{transaction.amount}` | `{transaction.amount}` |",
        f"| Date | `{transaction.date.isoformat()}` | `{transaction.date.isoformat()}` |",
        f"| Reference | `{_display(transaction.reference)}` | `{_display(normalize_reference(transaction.reference))}` |",
        f"| Counterparty | `{_display(transaction.counterparty)}` | `{_display(normalize_entity(transaction.counterparty))}` |",
        f"| Description | `{_display(transaction.description)}` | `{_display(normalize_description(transaction.description))}` |",
        "",
        "## Candidate ranking",
        "",
        "| Display rank | Candidate | True? | Score | Fields | Amount | Date | Reference | Entity | Description | Excluded |",
        "|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for index, entry in enumerate(ranked, start=1):
        scores = entry.breakdown.field_scores
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{entry.candidate.id}`",
                    "yes" if entry.candidate.id == case.true_candidate_id else "",
                    f"{entry.breakdown.total:.6f}",
                    str(entry.breakdown.compared_field_count),
                    _field_score(scores, "amount"),
                    _field_score(scores, "date"),
                    _field_score(scores, "reference"),
                    _field_score(scores, "entity"),
                    _field_score(scores, "description"),
                    ", ".join(entry.breakdown.excluded_fields) or "—",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "The final score is the unweighted mean of available fields. A field missing on either side is excluded. "
            "Generation validates that every candidate in the case is compared using the same number of fields.",
            "",
            "The matcher receives only the bank transaction and one accounting record. `event_id`, scenario, "
            "perturbations, origin and ground truth are consulted only after scoring.",
            "",
        ]
    )
    return "\n".join(lines)


def write_case_explanation(
    case: BenchmarkCase,
    *,
    method: MatchingMethod,
    config: ExperimentConfig,
    output: str | Path,
) -> Path:
    """Write a case's Markdown scoring trace, creating parent directories as needed.

    Return the path and replace existing content at that destination.
    """
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(explain_case(case, method=method, config=config), encoding="utf-8")
    return path


def _field_score(scores: dict[str, float], field: str) -> str:
    """Format a field's compatibility for the trace, using a dash for excluded fields."""
    value = scores.get(field)
    return "—" if value is None else f"{value:.4f}"


def _display(value: object) -> str:
    """Render absent values as an empty-set symbol and escape Markdown table separators."""
    if value is None:
        return "∅"
    return str(value).replace("|", "\\|")
