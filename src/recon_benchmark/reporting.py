from __future__ import annotations

import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import rapidfuzz

from recon_benchmark import __version__
from recon_benchmark.config import ExperimentConfig
from recon_benchmark.evaluation import AggregateMetrics, CaseEvaluation


def write_per_case_csv(evaluations: Iterable[CaseEvaluation], path: str | Path) -> Path:
    output = _prepare_path(path)
    fieldnames = [
        "seed",
        "case_id",
        "scenario",
        "method",
        "true_candidate_id",
        "predicted_candidate_id",
        "true_score",
        "top_score",
        "true_rank",
        "reciprocal_rank",
        "unique_top1",
        "top_tie_count",
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
                    "scenario": item.scenario,
                    "method": item.method,
                    "true_candidate_id": item.true_candidate_id,
                    "predicted_candidate_id": item.predicted_candidate_id or "",
                    "true_score": f"{item.true_score:.12f}",
                    "top_score": f"{item.top_score:.12f}",
                    "true_rank": f"{item.true_rank:.6f}",
                    "reciprocal_rank": f"{item.reciprocal_rank:.12f}",
                    "unique_top1": item.unique_top1,
                    "top_tie_count": item.top_tie_count,
                    "true_field_scores": json.dumps(item.true_field_scores, sort_keys=True),
                    "true_excluded_fields": json.dumps(item.true_excluded_fields),
                }
            )
    return output


def write_aggregate_csv(metrics: Iterable[AggregateMetrics], path: str | Path) -> Path:
    output = _prepare_path(path)
    fieldnames = ["seed", "method", "scenario", "cases", "unique_top1", "mrr", "tie_rate"]
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for metric in metrics:
            writer.writerow(
                {
                    "seed": metric.seed,
                    "method": metric.method,
                    "scenario": metric.scenario,
                    "cases": metric.cases,
                    "unique_top1": f"{metric.unique_top1:.12f}",
                    "mrr": f"{metric.mrr:.12f}",
                    "tie_rate": f"{metric.tie_rate:.12f}",
                }
            )
    return output


def write_summary_csv(metrics: Iterable[AggregateMetrics], path: str | Path) -> Path:
    output = _prepare_path(path)
    groups: dict[tuple[str, str], list[AggregateMetrics]] = defaultdict(list)
    for metric in metrics:
        groups[(metric.method, metric.scenario)].append(metric)

    fieldnames = [
        "method",
        "scenario",
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
        for (method, scenario), items in sorted(groups.items()):
            writer.writerow(
                {
                    "method": method,
                    "scenario": scenario,
                    "seeds": len(items),
                    "unique_top1_mean": f"{statistics.mean(item.unique_top1 for item in items):.12f}",
                    "unique_top1_std": f"{_pstdev(item.unique_top1 for item in items):.12f}",
                    "mrr_mean": f"{statistics.mean(item.mrr for item in items):.12f}",
                    "mrr_std": f"{_pstdev(item.mrr for item in items):.12f}",
                    "tie_rate_mean": f"{statistics.mean(item.tie_rate for item in items):.12f}",
                    "tie_rate_std": f"{_pstdev(item.tie_rate for item in items):.12f}",
                }
            )
    return output


def write_manifest(
    *,
    config: ExperimentConfig,
    benchmark_digests: dict[str, str],
    seeds: list[int],
    cases_per_scenario: int,
    methods: list[str],
    path: str | Path,
) -> Path:
    output = _prepare_path(path)
    manifest = {
        "benchmark_version": __version__,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "dependencies": {
            "rapidfuzz": rapidfuzz.__version__,
            "matplotlib": _module_version("matplotlib"),
        },
        "git_commit": _git_commit(output.parent),
        "config": config.to_dict(),
        "effective_run": {
            "seeds": seeds,
            "cases_per_scenario": cases_per_scenario,
            "methods": methods,
        },
        "benchmark_sha256": benchmark_digests,
        "source_tree_sha256": _source_tree_digest(output.parent.parent),
        "notes": [
            "Ground truth, scenario and perturbation labels are excluded from scoring.",
            "The uploaded real/example spreadsheet is not included in the project or benchmark.",
            "Synthetic description templates are generic and contain no copied entity, reference or amount.",
        ],
    }
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return output


def write_markdown_report(
    *,
    summary_csv: str | Path,
    path: str | Path,
) -> Path:
    rows = _read_csv(summary_csv)
    overall = [row for row in rows if row["scenario"] == "ALL"]
    scenarios = sorted({row["scenario"] for row in rows if row["scenario"] != "ALL"})
    primary_methods = sorted({
        row["method"] for row in rows if row["method"] not in {"M4-noNorm"}
    })
    lookup = {(row["method"], row["scenario"]): row for row in rows}

    lines = [
        "# Resultados do benchmark",
        "",
        "## Resumo global",
        "",
        "| Método | Unique Top-1 | MRR | Tie rate |",
        "|---|---:|---:|---:|",
    ]
    for row in sorted(overall, key=lambda item: item["method"]):
        lines.append(
            f"| {row['method']} | {_pct(row['unique_top1_mean'])} | "
            f"{float(row['mrr_mean']):.4f} | {_pct(row['tie_rate_mean'])} |"
        )

    lines.extend(
        [
            "",
            "## Unique Top-1 por cenário",
            "",
            "| Método | " + " | ".join(scenarios) + " |",
            "|---|" + "|".join("---:" for _ in scenarios) + "|",
        ]
    )
    for method in primary_methods:
        values = [
            _pct(lookup[(method, scenario)]["unique_top1_mean"])
            for scenario in scenarios
        ]
        lines.append(f"| {method} | " + " | ".join(values) + " |")

    primary_overall = [row for row in overall if row["method"] in primary_methods]
    best_overall = max(primary_overall, key=lambda row: float(row["unique_top1_mean"]))
    m4 = lookup.get(("M4", "ALL"))
    m4_raw = lookup.get(("M4-noNorm", "ALL"))

    lines.extend(["", "## Leituras automáticas", ""])
    lines.append(
        f"- Melhor resultado global entre M0–M4: **{best_overall['method']}**, com "
        f"**{_pct(best_overall['unique_top1_mean'])}** de Unique Top-1 e "
        f"MRR **{float(best_overall['mrr_mean']):.4f}**."
    )
    for scenario in scenarios:
        scenario_rows = [lookup[(method, scenario)] for method in primary_methods]
        best_value = max(float(row["unique_top1_mean"]) for row in scenario_rows)
        winners = [row["method"] for row in scenario_rows if abs(float(row["unique_top1_mean"]) - best_value) < 1e-12]
        lines.append(
            f"- `{scenario}`: melhor resultado de **{', '.join(winners)}** "
            f"({_pct(str(best_value))})."
        )
    if m4 is not None and m4_raw is not None:
        delta = float(m4["unique_top1_mean"]) - float(m4_raw["unique_top1_mean"])
        direction = "aumentou" if delta >= 0 else "reduziu"
        lines.append(
            f"- A normalização {direction} o Unique Top-1 global do M4 em "
            f"**{abs(delta) * 100:.2f} pontos percentuais**; o efeito deve continuar a ser "
            "analisado por cenário, porque não é necessariamente uniforme."
        )
    lines.append(
        "- `P6_MISSING_INFORMATION` contém deliberadamente casos observacionalmente "
        "indistinguíveis; 100% não é um objetivo possível nesse cenário."
    )

    lines.extend(
        [
            "",
            "## Leitura correta",
            "",
            "Estes resultados medem robustez relativa num benchmark sintético controlado de matching 1:1. "
            "Não demonstram desempenho em produção, superioridade sobre produtos comerciais, nem validade para 1:N/N:N.",
        ]
    )
    output = _prepare_path(path)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def create_robustness_figure(summary_csv: str | Path, path: str | Path) -> Path:
    rows = _read_csv(summary_csv)
    rows = [row for row in rows if row["scenario"] != "ALL" and row["method"] != "M4-noNorm"]
    scenarios = sorted({row["scenario"] for row in rows})
    methods = sorted({row["method"] for row in rows})
    lookup = {(row["method"], row["scenario"]): float(row["unique_top1_mean"]) for row in rows}

    figure, axis = plt.subplots(figsize=(11, 6))
    x_values = list(range(len(scenarios)))
    for method in methods:
        axis.plot(x_values, [lookup[(method, scenario)] for scenario in scenarios], marker="o", label=method)
    axis.set_title("Robustez por cenário — Unique Top-1")
    axis.set_xlabel("Cenário")
    axis.set_ylabel("Unique Top-1")
    short_labels = {
        "P0_CLEAN": "P0 Clean",
        "P1_AMOUNT_NOISE": "P1 Amount",
        "P2_DATE_DRIFT": "P2 Date",
        "P3_REFERENCE_NOISE": "P3 Reference",
        "P4_ENTITY_NOISE": "P4 Entity",
        "P5_DESCRIPTION_NOISE": "P5 Description",
        "P6_MISSING_INFORMATION": "P6 Missing",
        "P7_COMBINED": "P7 Combined",
    }
    axis.set_xticks(x_values, [short_labels.get(scenario, scenario) for scenario in scenarios], rotation=20, ha="right")
    axis.set_ylim(0.0, 1.05)
    axis.grid(axis="y", alpha=0.3)
    axis.legend()
    figure.tight_layout()

    output = _prepare_path(path)
    figure.savefig(output, dpi=180)
    plt.close(figure)
    return output


def _prepare_path(path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _pstdev(values: Iterable[float]) -> float:
    items = list(values)
    return statistics.pstdev(items) if len(items) > 1 else 0.0


def _read_csv(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _pct(value: str) -> str:
    return f"{float(value) * 100:.2f}%"


def _module_version(module_name: str) -> str:
    module = __import__(module_name)
    return str(getattr(module, "__version__", "unknown"))


def _source_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    candidates = [
        root / "pyproject.toml",
        root / "config" / "experiment.json",
        *sorted((root / "src" / "recon_benchmark").glob("*.py")),
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
