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
        f"# Explicação do caso `{case.case_id}`",
        "",
        f"- Seed: `{case.seed}`",
        f"- Cenário: `{case.scenario.value}` ({scenario_code(case.scenario)})",
        f"- Perturbações: `{', '.join(case.perturbations) if case.perturbations else 'nenhuma'}`",
        f"- Método: `{method.value}` ({method_code(method)})",
        f"- Ground truth usado apenas na avaliação: `{case.true_candidate_id}`",
        "",
        "## Movimento bancário recebido pelo matcher",
        "",
        "| Campo | Raw | Normalizado |",
        "|---|---|---|",
        f"| Amount | `{transaction.amount}` | `{transaction.amount}` |",
        f"| Date | `{transaction.date.isoformat()}` | `{transaction.date.isoformat()}` |",
        f"| Reference | `{_display(transaction.reference)}` | `{_display(normalize_reference(transaction.reference))}` |",
        f"| Counterparty | `{_display(transaction.counterparty)}` | `{_display(normalize_entity(transaction.counterparty))}` |",
        f"| Description | `{_display(transaction.description)}` | `{_display(normalize_description(transaction.description))}` |",
        "",
        "## Ranking dos candidatos",
        "",
        "| Rank visual | Candidato | True? | Score | Campos | Amount | Date | Reference | Entity | Description | Excluídos |",
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
                    "sim" if entry.candidate.id == case.true_candidate_id else "",
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
            "O score final é a média simples dos campos disponíveis. Um campo ausente em qualquer lado é excluído. "
            "A geração valida que todos os candidatos do caso são comparados no mesmo número de campos.",
            "",
            "O matcher recebe apenas o movimento bancário e um registo contabilístico. `event_id`, cenário, "
            "perturbações, origem e ground truth só são consultados depois do scoring.",
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
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(explain_case(case, method=method, config=config), encoding="utf-8")
    return path


def _field_score(scores: dict[str, float], field: str) -> str:
    value = scores.get(field)
    return "—" if value is None else f"{value:.4f}"


def _display(value: object) -> str:
    if value is None:
        return "∅"
    return str(value).replace("|", "\\|")
