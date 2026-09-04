from __future__ import annotations

from pathlib import Path
from typing import Iterable

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.evaluation import (
    CaseEvaluation,
    aggregate_by_seed_scenario,
    aggregate_overall_by_seed,
    evaluate_cases,
)
from recon_benchmark.generator import benchmark_digest, generate_benchmark
from recon_benchmark.matchers import MethodName
from recon_benchmark.reporting import (
    create_robustness_figure,
    write_aggregate_csv,
    write_manifest,
    write_markdown_report,
    write_per_case_csv,
    write_summary_csv,
)
from recon_benchmark.serialization import write_jsonl


def run_experiment(
    *,
    seeds: Iterable[int],
    cases_per_scenario: int,
    methods: Iterable[MethodName],
    config: ExperimentConfig,
    root: str | Path,
) -> dict[str, Path]:
    root_path = Path(root)
    benchmarks_dir = root_path / "benchmarks"
    results_dir = root_path / "results"
    figures_dir = root_path / "figures"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    seed_list = list(seeds)
    method_list = list(methods)
    all_evaluations: list[CaseEvaluation] = []
    digests: dict[str, str] = {}

    for seed in seed_list:
        cases = generate_benchmark(
            seed=seed,
            cases_per_scenario=cases_per_scenario,
            config=config,
        )
        benchmark_path = benchmarks_dir / f"seed_{seed}.jsonl"
        write_jsonl(cases, benchmark_path)
        digests[benchmark_path.name] = benchmark_digest(benchmark_path)
        all_evaluations.extend(evaluate_cases(cases, methods=method_list, config=config))

    scenario_metrics = aggregate_by_seed_scenario(all_evaluations)
    overall_metrics = aggregate_overall_by_seed(all_evaluations)
    all_metrics = (*scenario_metrics, *overall_metrics)

    per_case_path = write_per_case_csv(all_evaluations, results_dir / "per_case.csv")
    by_scenario_path = write_aggregate_csv(all_metrics, results_dir / "by_scenario.csv")
    summary_path = write_summary_csv(all_metrics, results_dir / "summary.csv")
    manifest_path = write_manifest(
        config=config,
        benchmark_digests=digests,
        seeds=seed_list,
        cases_per_scenario=cases_per_scenario,
        methods=[str(method) for method in method_list],
        path=results_dir / "manifest.json",
    )
    report_path = write_markdown_report(summary_csv=summary_path, path=results_dir / "report.md")
    figure_path = create_robustness_figure(
        summary_csv=summary_path,
        path=figures_dir / "robustness_by_scenario.png",
    )

    return {
        "per_case": per_case_path,
        "by_scenario": by_scenario_path,
        "summary": summary_path,
        "manifest": manifest_path,
        "report": report_path,
        "figure": figure_path,
    }
