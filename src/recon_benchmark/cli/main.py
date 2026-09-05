from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.experiment.config import load_config
from recon_benchmark.cli.explanation import write_case_explanation
from recon_benchmark.generation.generator import generate_benchmark, generate_to_file, validate_benchmark
from recon_benchmark.ranking.matchers import METHODS
from recon_benchmark.domain.models import MatchingMethod, Scenario
from recon_benchmark.experiment.pipeline import run_experiment
from recon_benchmark.storage.serialization import read_jsonl, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recon-benchmark",
        description="Benchmark sintético de ranking 1:1 para reconciliação bancária.",
    )
    parser.add_argument(
        "--config",
        default="config/experiment.json",
        help="Caminho para a configuração JSON (default: config/experiment.json).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="Gerar um benchmark JSONL.")
    generate_parser.add_argument("--seed", type=int, default=7)
    generate_parser.add_argument("--cases-per-scenario", type=int, default=3)
    generate_parser.add_argument("--output", default=None)

    validate_parser = subparsers.add_parser("validate", help="Validar invariantes de um benchmark.")
    validate_parser.add_argument("--input", required=True)
    validate_parser.add_argument("--cases-per-scenario", type=int, default=None)

    evaluate_parser = subparsers.add_parser(
        "evaluate",
        help="Executar uma experiência de desenvolvimento.",
    )
    evaluate_parser.add_argument("--seed", type=int, default=7)
    evaluate_parser.add_argument("--cases-per-scenario", type=int, default=3)
    evaluate_parser.add_argument("--methods", nargs="+", default=["all"])
    evaluate_parser.add_argument("--output-root", default="development_run")

    final_parser = subparsers.add_parser(
        "run-final",
        help="Executar a configuração e as evaluation seeds congeladas.",
    )
    final_parser.add_argument("--output-root", default=".")

    demo_parser = subparsers.add_parser("demo", help="Gerar e explicar um caso ponta a ponta.")
    demo_parser.add_argument("--seed", type=int, default=7)
    demo_parser.add_argument(
        "--scenario",
        default=Scenario.COMBINED_VARIATION.value,
        choices=[scenario.value for scenario in Scenario],
    )
    demo_parser.add_argument(
        "--method",
        default=MatchingMethod.FIELD_AWARE.value,
        choices=[method.value for method in METHODS],
    )
    demo_parser.add_argument("--output", default="examples/demo_trace.md")
    demo_parser.add_argument("--benchmark-output", default="examples/demo_benchmark.jsonl")

    explain_parser = subparsers.add_parser("explain", help="Explicar um caso existente.")
    explain_parser.add_argument("--input", required=True)
    explain_parser.add_argument("--case-id", default=None)
    explain_parser.add_argument("--case-index", type=int, default=0)
    explain_parser.add_argument(
        "--method",
        default=MatchingMethod.FIELD_AWARE.value,
        choices=[method.value for method in METHODS],
    )
    explain_parser.add_argument("--output", default="examples/case_explanation.md")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = _load_cli_config(args.config)

    try:
        if args.command == "generate":
            output = args.output or f"benchmarks/seed_{args.seed}.jsonl"
            path = generate_to_file(
                seed=args.seed,
                cases_per_scenario=args.cases_per_scenario,
                config=config,
                output=output,
            )
            print(f"Benchmark gerado: {path}")
            return 0

        if args.command == "validate":
            cases = read_jsonl(args.input)
            errors = validate_benchmark(
                cases,
                config=config,
                expected_cases_per_scenario=args.cases_per_scenario,
            )
            if errors:
                for error in errors:
                    print(f"ERRO: {error}", file=sys.stderr)
                return 1
            print(f"Benchmark válido: {args.input} ({len(cases)} casos)")
            return 0

        if args.command == "evaluate":
            outputs = run_experiment(
                seeds=[args.seed],
                cases_per_scenario=args.cases_per_scenario,
                methods=_parse_methods(args.methods),
                config=config,
                root=args.output_root,
            )
            _print_outputs(outputs)
            return 0

        if args.command == "run-final":
            outputs = run_experiment(
                seeds=config.evaluation_seeds,
                cases_per_scenario=config.cases_per_scenario,
                methods=config.methods,
                config=config,
                root=args.output_root,
            )
            _print_outputs(outputs)
            return 0

        if args.command == "demo":
            scenario = Scenario(args.scenario)
            if scenario not in config.scenarios:
                raise ValueError(f"Cenário desconhecido: {scenario.value}")
            cases = generate_benchmark(seed=args.seed, cases_per_scenario=1, config=config)
            write_jsonl(cases, args.benchmark_output)
            case = next(item for item in cases if item.scenario is scenario)
            output = write_case_explanation(
                case,
                method=MatchingMethod(args.method),
                config=config,
                output=args.output,
            )
            print(f"Demonstração criada: {output}")
            print(f"Benchmark de demonstração: {args.benchmark_output}")
            return 0

        if args.command == "explain":
            cases = read_jsonl(args.input)
            if not cases:
                raise ValueError("O benchmark não contém casos.")
            if args.case_id:
                selected = next((item for item in cases if item.case_id == args.case_id), None)
                if selected is None:
                    raise ValueError(f"Case ID não encontrado: {args.case_id}")
            else:
                if args.case_index < 0 or args.case_index >= len(cases):
                    raise ValueError("case-index fora do intervalo.")
                selected = cases[args.case_index]
            output = write_case_explanation(
                selected,
                method=MatchingMethod(args.method),
                config=config,
                output=args.output,
            )
            print(f"Explicação criada: {output}")
            return 0

    except (OSError, ValueError, RuntimeError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 1

    parser.error("Comando não tratado.")
    return 2


def _load_cli_config(path: str) -> ExperimentConfig:
    config_path = Path(path)
    return load_config(config_path if config_path.exists() else None)


def _parse_methods(values: Sequence[str]) -> tuple[MatchingMethod, ...]:
    if list(values) == ["all"]:
        return METHODS
    try:
        return tuple(MatchingMethod(value) for value in values)
    except ValueError as exc:
        raise ValueError(f"Método desconhecido em {list(values)}") from exc


def _print_outputs(outputs: dict[str, Path]) -> None:
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
