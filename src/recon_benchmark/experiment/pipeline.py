from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.metrics.models import CaseEvaluation
from recon_benchmark.metrics.diagnostics import (
    write_amount_pair_diagnostics,
    write_operation_diagnostics,
)
from recon_benchmark.metrics.evaluation import (
    aggregate_by_seed_scenario,
    aggregate_overall_by_seed,
    evaluate_cases,
)
from recon_benchmark.generation.generator import benchmark_digest, generate_benchmark
from recon_benchmark.domain.models import BenchmarkCase, MatchingMethod
from recon_benchmark.metrics.reporting import (
    create_paper_comparison_figure,
    create_robustness_figure,
    write_aggregate_csv,
    write_manifest,
    write_markdown_report,
    write_per_case_csv,
    write_summary_csv,
)
from recon_benchmark.storage.serialization import write_jsonl


def run_experiment(
    *,
    seeds: Iterable[int],
    cases_per_scenario: int,
    methods: Iterable[MatchingMethod],
    config: ExperimentConfig,
    root: str | Path,
) -> dict[str, Path]:
    """Generate and evaluate every requested seed, then write experiment artifacts.

    seeds, cases_per_scenario and methods describe the effective run; config
    supplies shared generation and scoring rules. Each seed produces paired cases.
    Write per-seed and consolidated JSONL, metrics CSVs, report, figures and manifest
    under root, replacing files at the same paths. Return output names mapped to
    paths for the CLI. Configuration and generation failures propagate.
    Include the paper comparison figure when both M3 and M4 are evaluated.
    """
    config.validate()
    seed_list = list(seeds)
    method_list = list(methods)
    if not seed_list:
        raise ValueError("At least one seed is required.")
    if len(seed_list) != len(set(seed_list)):
        raise ValueError("Run seeds must not contain duplicates.")
    if not method_list:
        raise ValueError("At least one method is required.")

    root_path = Path(root)
    benchmarks_dir = root_path / "benchmarks"
    results_dir = root_path / "results"
    figures_dir = root_path / "figures"
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    all_cases: list[BenchmarkCase] = []
    all_evaluations: list[CaseEvaluation] = []
    digests: dict[str, str] = {}

    for seed in seed_list:
        cases = generate_benchmark(
            seed=seed,
            cases_per_scenario=cases_per_scenario,
            config=config,
        )
        seed_benchmark_path = benchmarks_dir / f"seed_{seed}.jsonl"
        write_jsonl(cases, seed_benchmark_path)
        digests[seed_benchmark_path.name] = benchmark_digest(seed_benchmark_path)
        all_cases.extend(cases)
        all_evaluations.extend(evaluate_cases(cases, methods=method_list, config=config))

    benchmark_path = write_jsonl(all_cases, results_dir / "benchmark.jsonl")
    digests[benchmark_path.name] = benchmark_digest(benchmark_path)

    scenario_metrics = aggregate_by_seed_scenario(all_evaluations)
    overall_metrics = aggregate_overall_by_seed(all_evaluations)
    all_metrics = (*scenario_metrics, *overall_metrics)

    per_case_path = write_per_case_csv(all_evaluations, results_dir / "per_case.csv")
    by_scenario_path = write_aggregate_csv(
        scenario_metrics,
        results_dir / "by_scenario.csv",
    )
    summary_path = write_summary_csv(all_metrics, results_dir / "summary.csv")
    operation_path = write_operation_diagnostics(
        all_cases, all_evaluations, results_dir / "operation_diagnostics.csv",
    )
    amount_pairs_path = write_amount_pair_diagnostics(
        all_cases, all_evaluations, results_dir / "amount_pair_diagnostics.csv",
    )
    manifest_path = write_manifest(
        config=config,
        benchmark_digests=digests,
        seeds=seed_list,
        cases_per_scenario=cases_per_scenario,
        methods=method_list,
        path=results_dir / "experiment_manifest.json",
    )
    manifest_alias_path = results_dir / "manifest.json"
    manifest_alias_path.write_bytes(manifest_path.read_bytes())
    report_path = write_markdown_report(
        summary_csv=summary_path,
        operation_csv=operation_path,
        amount_pairs_csv=amount_pairs_path,
        path=results_dir / "report.md",
    )
    figure_path = create_robustness_figure(
        summary_csv=summary_path,
        path=figures_dir / "robustness_by_scenario.png",
    )

    outputs = {
        "benchmark": benchmark_path,
        "per_case": per_case_path,
        "by_scenario": by_scenario_path,
        "summary": summary_path,
        "operation_diagnostics": operation_path,
        "amount_pair_diagnostics": amount_pairs_path,
        "report": report_path,
        "experiment_manifest": manifest_path,
        "manifest": manifest_alias_path,
        "figure": figure_path,
    }
    if {MatchingMethod.CHARACTER_TRIGRAM_TEXT, MatchingMethod.FIELD_AWARE}.issubset(method_list):
        outputs["paper_comparison_figure"] = create_paper_comparison_figure(
            summary_csv=summary_path,
            path=figures_dir / "method_comparison_by_scenario.png",
        )
    return outputs
