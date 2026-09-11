from __future__ import annotations

import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

import matplotlib
import rapidfuzz

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from recon_benchmark import __version__
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.metrics.models import AggregateMetrics, CaseEvaluation
from recon_benchmark.domain.models import MatchingMethod, Scenario
from recon_benchmark.domain.codes import method_code, scenario_code


def write_per_case_csv(evaluations: Iterable[CaseEvaluation], path: str | Path) -> Path:
    """Write one CSV row per case-method result with ranks, scores and missing-field details.

    Include labels for auditing after scoring; create parent folders and return the
    output path, replacing an existing file.
    """
    output = _prepare_path(path)
    fieldnames = [
        "seed",
        "case_id",
        "scenario",
        "scenario_code",
        "method",
        "method_code",
        "true_candidate_id",
        "predicted_candidate_id",
        "true_score",
        "top_score",
        "true_rank",
        "reciprocal_rank",
        "unique_top1",
        "top_tie_count",
        "compared_field_count",
        "true_field_scores",
        "true_excluded_fields",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in evaluations:
            writer.writerow(
                {
                    "seed": item.seed,
                    "case_id": item.case_id,
                    "scenario": item.scenario.value,
                    "scenario_code": scenario_code(item.scenario),
                    "method": item.method.value,
                    "method_code": method_code(item.method),
                    "true_candidate_id": item.true_candidate_id,
                    "predicted_candidate_id": item.predicted_candidate_id or "",
                    "true_score": f"{item.true_score:.12f}",
                    "top_score": f"{item.top_score:.12f}",
                    "true_rank": f"{item.true_rank:.6f}",
                    "reciprocal_rank": f"{item.reciprocal_rank:.12f}",
                    "unique_top1": item.unique_top1,
                    "top_tie_count": item.top_tie_count,
                    "compared_field_count": item.compared_field_count,
                    "true_field_scores": json.dumps(item.true_field_scores, sort_keys=True),
                    "true_excluded_fields": json.dumps(item.true_excluded_fields),
                }
            )
    return output


def write_aggregate_csv(metrics: Iterable[AggregateMetrics], path: str | Path) -> Path:
    """Write per-seed aggregate metrics with descriptive names and publication codes."""
    output = _prepare_path(path)
    fieldnames = [
        "seed",
        "method",
        "method_code",
        "scenario",
        "scenario_code",
        "cases",
        "unique_top1",
        "mrr",
        "tie_rate",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(_aggregate_row(metric))
    return output


def write_summary_csv(metrics: Iterable[AggregateMetrics], path: str | Path) -> Path:
    """Group per-seed metrics by method/scenario and write their mean and sample deviation.

    Each seed contributes one supplied aggregate. Overall groups retain scenario=None;
    a single seed has a reported deviation of zero.
    """
    output = _prepare_path(path)
    groups: dict[tuple[MatchingMethod, Scenario | None], list[AggregateMetrics]] = defaultdict(list)
    for metric in metrics:
        groups[(metric.method, metric.scenario)].append(metric)

    fieldnames = [
        "method",
        "method_code",
        "scenario",
        "scenario_code",
        "seeds",
        "unique_top1_mean",
        "unique_top1_std",
        "mrr_mean",
        "mrr_std",
        "tie_rate_mean",
        "tie_rate_std",
    ]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        ordered = sorted(
            groups.items(),
            key=lambda item: (
                method_code(item[0][0]),
                "ZZ" if item[0][1] is None else scenario_code(item[0][1]),
            ),
        )
        for (method, scenario), items in ordered:
            writer.writerow(
                {
                    "method": method.value,
                    "method_code": method_code(method),
                    "scenario": _scenario_value(scenario),
                    "scenario_code": _scenario_output_code(scenario),
                    "seeds": len(items),
                    "unique_top1_mean": f"{statistics.mean(item.unique_top1 for item in items):.12f}",
                    "unique_top1_std": f"{_sample_std(item.unique_top1 for item in items):.12f}",
                    "mrr_mean": f"{statistics.mean(item.mrr for item in items):.12f}",
                    "mrr_std": f"{_sample_std(item.mrr for item in items):.12f}",
                    "tie_rate_mean": f"{statistics.mean(item.tie_rate for item in items):.12f}",
                    "tie_rate_std": f"{_sample_std(item.tie_rate for item in items):.12f}",
                }
            )
    return output


def write_manifest(
    *,
    config: ExperimentConfig,
    benchmark_digests: dict[str, str],
    seeds: list[int],
    cases_per_scenario: int,
    methods: list[MatchingMethod],
    path: str | Path,
) -> Path:
    """Write the configuration, effective run and provenance needed to inspect a run.

    Record supplied benchmark hashes, Python/dependency versions, UTC timestamp,
    available Git state and a recursive source hash. Effective run parameters are
    recorded separately because development commands can override config defaults.
    """
    output = _prepare_path(path)
    project_root = Path(__file__).resolve().parents[3]
    manifest: dict[str, object] = {
        "benchmark_version": __version__,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": {
            "rapidfuzz": rapidfuzz.__version__,
            "matplotlib": _module_version("matplotlib"),
        },
        "git_commit": _git_commit(project_root),
        "git_worktree_dirty": _git_worktree_dirty(project_root),
        "configuration": config.to_dict(),
        "effective_run": {
            "seeds": seeds,
            "cases_per_scenario": cases_per_scenario,
            "methods": [
                {"name": method.value, "output_code": method_code(method)}
                for method in methods
            ],
        },
        "benchmark_sha256": benchmark_digests,
        "source_tree_sha256": _source_tree_digest(project_root),
        "standard_deviation": "sample (n-1); zero when only one seed is present",
        "notes": [
            "FinancialEvent metadata and ground truth are excluded from every matcher call.",
            "Scores are compatibility measures in [0,1], not probabilities.",
            "The candidate order is deterministic and shared by paired scenarios.",
            "The reference spreadsheet is not included and no transaction was copied from it.",
        ],
    }
    output.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def write_markdown_report(
    *,
    summary_csv: str | Path,
    path: str | Path,
    operation_csv: str | Path | None = None,
    amount_pairs_csv: str | Path | None = None,
) -> Path:
    """Render summary CSV metrics as a Markdown report with global and scenario tables.

    Show the description ablation globally but keep the scenario comparison to the
    five primary methods. Optional diagnostics describe the frozen cases after
    evaluation; they never change the primary metrics. Write and return the path.
    """
    rows = _read_csv(summary_csv)
    overall = [row for row in rows if row["scenario"] == "ALL"]
    scenarios = sorted(
        {row["scenario_code"] for row in rows if row["scenario"] != "ALL"}
    )
    lookup = {
        (row["method_code"], row["scenario_code"]): row
        for row in rows
    }
    primary_method_codes = sorted(
        {
            row["method_code"]
            for row in rows
            if row["method"]
            != MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION.value
        }
    )

    lines = [
        "# Resultados do benchmark",
        "",
        "Os valores são médias entre evaluation seeds; o desvio-padrão amostral está em `summary.csv`.",
        "",
        "## Resumo global",
        "",
        "| Método | Código | Unique Top-1 | MRR | Tie Rate |",
        "|---|---|---:|---:|---:|",
    ]
    for row in sorted(overall, key=lambda item: item["method_code"]):
        lines.append(
            f"| `{row['method']}` | {row['method_code']} | "
            f"{_pct(row['unique_top1_mean'])} | {_decimal(row['mrr_mean'])} | "
            f"{_pct(row['tie_rate_mean'])} |"
        )

    lines.extend(
        [
            "",
            "## Unique Top-1 por cenário",
            "",
            "| Método | " + " | ".join(scenarios) + " |",
            "|---|" + "---:|" * len(scenarios),
        ]
    )
    for code in primary_method_codes:
        values = [_pct(lookup[(code, scenario)]["unique_top1_mean"]) for scenario in scenarios]
        lines.append(f"| {code} | " + " | ".join(values) + " |")

    lines.extend(_diagnostic_report_lines(operation_csv, amount_pairs_csv))

    lines.extend(
        [
            "",
            "## Interpretação",
            "",
            "Unique Top-1 exige que o candidato verdadeiro seja o único no maior score. "
            "MRR usa a posição média nos empates e Tie Rate mede a proporção de casos com "
            "mais de um candidato no maior score.",
            "",
            "O benchmark mede ranking sintético 1:1 quando o candidato verdadeiro está presente. "
            "Não mede auto-reconciliação, calibração, relações 1:N/N:1/N:N nem desempenho em produção.",
            "",
        ]
    )
    output = _prepare_path(path)
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def _diagnostic_report_lines(
    operation_csv: str | Path | None,
    amount_pairs_csv: str | Path | None,
) -> list[str]:
    """Explain post-hoc operation strata and paired amount outcomes from diagnostic CSVs."""
    lines: list[str] = []
    if operation_csv is not None:
        rows = [row for row in _read_csv(operation_csv) if row["aggregation"] == "pooled_cases"]
        lookup = {(row["operation_group"], row["method_code"]): row for row in rows}
        labels = {
            "supplier_transfer": "Transferência a fornecedor",
            "customer_receipt": "Recebimento de cliente",
            "direct_debit": "Débito direto",
            "card_payment": "Pagamento com cartão",
            "bank_fee": "Comissões bancárias",
            "tax_payment": "Pagamento fiscal",
            "non_bank_fee": "Restantes operações (subtotal)",
            "ALL": "Total",
        }
        lines.extend([
            "", "## Análise diagnóstica posterior por operação", "",
            "Proporções agrupadas dos casos existentes, incluindo os cenários emparelhados. "
            "São uma análise descritiva posterior ao freeze; não são novas amostras independentes. "
            "O CSV inclui também resultados por seed e média/desvio-padrão entre seeds. "
            "Os subtotais sobrepõem-se às linhas por operação.", "",
            "| Operação | Eventos base | Casos | M4 Unique Top-1 | M4-D Unique Top-1 |",
            "|---|---:|---:|---:|---:|",
        ])
        for group, label in labels.items():
            available = next((lookup[(group, code)] for code in ("M4", "M4-D") if (group, code) in lookup), None)
            if available is None:
                continue
            values = [
                _pct(lookup[(group, code)]["unique_top1"]) if (group, code) in lookup else "—"
                for code in ("M4", "M4-D")
            ]
            lines.append(f"| {label} | {available['base_events']} | {available['cases']} | " + " | ".join(values) + " |")
        lines.extend([
            "",
            "Nas comissões, um hard negative partilha montante, data, referência ausente e "
            "entidade ausente com o verdadeiro, mas a descrição é forçada a diferir. M4-D "
            "empata necessariamente esses candidatos. Cada fonte escolhe apenas dois templates "
            "por operação, sem um facto narrativo específico do evento. Desempatar com descrição "
            "não demonstra, por si só, informação identificadora adicional.",
        ])
    if amount_pairs_csv is not None:
        rows = [row for row in _read_csv(amount_pairs_csv) if row["aggregation"] == "pooled_pairs"]
        lines.extend([
            "", "## Diagnóstico emparelhado de montante", "",
            "Comparação de cada variante de montante com o seu caso natural. As contagens "
            "referem-se à posição média do verdadeiro, Unique Top-1 e tamanho do empate no topo; "
            "não medem alterações de toda a ordenação.", "",
            "| Método | Pares | Posição alterada | Unique Top-1 alterado | Empate no topo alterado |",
            "|---|---:|---:|---:|---:|",
        ])
        for row in rows:
            lines.append(f"| {row['method_code']} | {row['pairs']} | {row['true_average_rank_changed']} | {row['unique_top1_changed']} | {row['top_tie_count_changed']} |")
        lines.extend([
            "",
            "Os três hard negatives preservam o montante verdadeiro. Uma alteração bancária "
            "modifica igualmente essa componente no verdadeiro e nesses concorrentes. "
            "A invariância observada depende também desta construção dos candidatos.",
        ])
    return lines


def create_robustness_figure(summary_csv: str | Path, path: str | Path) -> Path:
    """Plot mean Unique Top-1 across scenarios for the five primary methods.

    Read summary CSV rows, exclude overall/ablation rows, save the figure at path
    and close it so batch runs do not retain plotting resources.
    """
    rows = [
        row
        for row in _read_csv(summary_csv)
        if row["scenario"] != "ALL"
        and row["method"] != MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION.value
    ]
    scenarios = sorted({row["scenario_code"] for row in rows})
    methods = sorted({row["method_code"] for row in rows})
    lookup = {
        (row["method_code"], row["scenario_code"]): float(row["unique_top1_mean"])
        for row in rows
    }

    figure, axis = plt.subplots(figsize=(11, 6))
    x_values = list(range(len(scenarios)))
    for method in methods:
        axis.plot(
            x_values,
            [lookup[(method, scenario)] for scenario in scenarios],
            marker="o",
            label=method,
        )
    axis.set_title("Robustez por cenário — Unique Top-1")
    axis.set_xlabel("Cenário")
    axis.set_ylabel("Unique Top-1")
    axis.set_xticks(x_values, scenarios)
    axis.set_ylim(0.0, 1.05)
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()

    output = _prepare_path(path)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _aggregate_row(metric: AggregateMetrics) -> dict[str, object]:
    """Convert one per-seed aggregate into a CSV row with stable names and numeric formatting."""
    return {
        "seed": metric.seed,
        "method": metric.method.value,
        "method_code": method_code(metric.method),
        "scenario": _scenario_value(metric.scenario),
        "scenario_code": _scenario_output_code(metric.scenario),
        "cases": metric.cases,
        "unique_top1": f"{metric.unique_top1:.12f}",
        "mrr": f"{metric.mrr:.12f}",
        "tie_rate": f"{metric.tie_rate:.12f}",
    }


def _scenario_value(scenario: Scenario | None) -> str:
    """Return a descriptive scenario name, using ALL for pooled results."""
    return "ALL" if scenario is None else scenario.value


def _scenario_output_code(scenario: Scenario | None) -> str:
    """Return the scenario's publication code, using ALL for pooled results."""
    return "ALL" if scenario is None else scenario_code(scenario)


def _prepare_path(path: str | Path) -> Path:
    """Create missing parent directories and return a Path without writing the file itself."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _sample_std(values: Iterable[float]) -> float:
    """Compute sample standard deviation with n-1 denominator, or zero for fewer than two values."""
    items = list(values)
    return statistics.stdev(items) if len(items) > 1 else 0.0


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV into dictionaries keyed by its header names."""
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _pct(value: str) -> str:
    """Format stored decimal text with explicit half-up percentage rounding."""
    percentage = (Decimal(value) * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{percentage:.2f}%"


def _decimal(value: str) -> str:
    """Format a stored metric to four places with the same half-up convention."""
    rounded = Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return f"{rounded:.4f}"


def _module_version(module_name: str) -> str:
    """Import a dependency and read its version, using unknown when that attribute is absent."""
    module = __import__(module_name)
    return str(getattr(module, "__version__", "unknown"))


def _source_tree_digest(root: Path) -> str:
    """Hash project settings and all nested package sources in a stable path order.

    Include relative filenames and file bytes, so both code edits and module moves
    change the digest. Skip missing files and exclude generated result artifacts.
    """
    digest = hashlib.sha256()
    candidates = [
        root / "pyproject.toml",
        root / "config" / "experiment.json",
        *sorted((root / "src" / "recon_benchmark").rglob("*.py")),
    ]
    for path in candidates:
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(relative)
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _git_commit(start_path: Path) -> str | None:
    """Read the current Git commit from the given directory, or None when unavailable."""
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=start_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip() or None


def _git_worktree_dirty(start_path: Path) -> bool | None:
    """Report whether Git sees local changes, or None if Git cannot be queried."""
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=start_path,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return bool(completed.stdout.strip())
