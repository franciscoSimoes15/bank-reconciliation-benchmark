from __future__ import annotations

from pathlib import Path

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.evaluation import CandidateScore, rank_candidates
from recon_benchmark.matchers import MethodName, score_pair
from recon_benchmark.models import BenchmarkCase
from recon_benchmark.normalization import (
    normalize_description,
    normalize_entity,
    normalize_reference,
)


def explain_case(
    case: BenchmarkCase,
    *,
    method: MethodName,
    config: ExperimentConfig,
) -> str:
    scored = tuple(
        CandidateScore(
            candidate=candidate,
            breakdown=score_pair(case.transaction, candidate, method=method, config=config),
        )
        for candidate in case.candidates
    )
    ranked = rank_candidates(scored)

    tx = case.transaction
    lines = [
        f"# Explicação do caso `{case.case_id}`",
        "",
        f"- Seed: `{case.seed}`",
        f"- Cenário: `{case.scenario}`",
        f"- Perturbações: `{', '.join(case.perturbations) if case.perturbations else 'nenhuma'}`",
        f"- Método: `{method}`",
        f"- Ground truth usado apenas na avaliação: `{case.true_candidate_id}`",
        "",
        "## 1. Movimento bancário recebido pelo matcher",
        "",
        "| Campo | Raw | Normalizado |",
        "|---|---|---|",
        f"| Amount | `{tx.amount}` | `{tx.amount}` |",
        f"| Date | `{tx.date.isoformat()}` | `{tx.date.isoformat()}` |",
        f"| Reference | `{_display(tx.reference)}` | `{_display(normalize_reference(tx.reference))}` |",
        f"| Counterparty | `{_display(tx.counterparty)}` | `{_display(normalize_entity(tx.counterparty))}` |",
        f"| Description | `{_display(tx.description)}` | `{_display(normalize_description(tx.description))}` |",
        "",
        "## 2. Ranking dos candidatos",
        "",
        "| Rank visual | Candidato | True? | Score | Amount | Date | Reference | Entity | Description | Excluídos |",
        "|---:|---|:---:|---:|---:|---:|---:|---:|---:|---|",
    ]

    for index, entry in enumerate(ranked, start=1):
        scores = entry.breakdown.field_scores
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{entry.candidate.id}`",
                    "✅" if entry.candidate.id == case.true_candidate_id else "",
                    f"{entry.breakdown.total:.6f}",
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
            "## 3. Como ler",
            "",
            "O score final é a média simples dos campos disponíveis. Um campo ausente em qualquer lado é excluído, "
            "em vez de ser tratado como desacordo. O método nunca consulta o `true_candidate_id`; esse valor só é "
            "usado depois do ranking para calcular as métricas.",
            "",
        ]
    )
    return "\n".join(lines)


def write_case_explanation(
    case: BenchmarkCase,
    *,
    method: MethodName,
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
