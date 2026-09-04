from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence, cast

from recon_benchmark.config import ExperimentConfig, load_config
from recon_benchmark.explanation import write_case_explanation
from recon_benchmark.generator import generate_benchmark, generate_to_file, validate_benchmark
from recon_benchmark.matchers import METHODS, MethodName
from recon_benchmark.pipeline import run_experiment
from recon_benchmark.serialization import read_jsonl, write_jsonl


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="recon-benchmark",
        description="Benchmark sintético de matching 1:1 para reconciliação bancária.",
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

    evaluate_parser = subparsers.add_parser("evaluate", help="Gerar e avaliar uma seed.")
    evaluate_parser.add_argument("--seed", type=int, default=7)
    evaluate_parser.add_argument("--cases-per-scenario", type=int, default=3)
    evaluate_parser.add_argument("--methods", nargs="+", default=["all"])
    evaluate_parser.add_argument("--output-root", default="development_run")

    final_parser = subparsers.add_parser("run-final", help="Executar as evaluation seeds congeladas.")
    final_parser.add_argument("--seeds", nargs="+", type=int, default=None)
    final_parser.add_argument("--cases-per-scenario", type=int, default=None)
    final_parser.add_argument("--methods", nargs="+", default=["all"])
    final_parser.add_argument("--output-root", default=".")

    demo_parser = subparsers.add_parser("demo", help="Gerar e explicar um caso ponta a ponta.")
    demo_parser.add_argument("--seed", type=int, default=7)
    demo_parser.add_argument("--scenario", default="P7_COMBINED")
    demo_parser.add_argument("--method", default="M4", choices=METHODS)
    demo_parser.add_argument("--output", default="examples/demo_trace.md")
    demo_parser.add_argument("--benchmark-output", default="examples/demo_benchmark.jsonl")

    explain_parser = subparsers.add_parser("explain", help="Explicar um caso existente.")
    explain_parser.add_argument("--input", required=True)
    explain_parser.add_argument("--case-id", default=None)
    explain_parser.add_argument("--case-index", type=int, default=0)
    explain_parser.add_argument("--method", default="M4", choices=METHODS)
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
            methods = _parse_methods(args.methods)
            outputs = run_experiment(
                seeds=[args.seed],
                cases_per_scenario=args.cases_per_scenario,
                methods=methods,
                config=config,
                root=args.output_root,
            )
            _print_outputs(outputs)
            return 0

        if args.command == "run-final":
            methods = _parse_methods(args.methods)
            seeds = args.seeds or list(config.evaluation_seeds)
            cases_per_scenario = args.cases_per_scenario or config.cases_per_scenario
            outputs = run_experiment(
                seeds=seeds,
                cases_per_scenario=cases_per_scenario,
                methods=methods,
                config=config,
                root=args.output_root,
            )
            _print_outputs(outputs)
            return 0

        if args.command == "demo":
            if args.scenario not in config.scenarios:
                raise ValueError(f"Cenário desconhecido: {args.scenario}")
            cases = generate_benchmark(seed=args.seed, cases_per_scenario=1, config=config)
            write_jsonl(cases, args.benchmark_output)
            case = next(case for case in cases if case.scenario == args.scenario)
            output = write_case_explanation(
                case,
                method=cast(MethodName, args.method),
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
                selected = next((case for case in cases if case.case_id == args.case_id), None)
                if selected is None:
                    raise ValueError(f"Case ID não encontrado: {args.case_id}")
            else:
                if args.case_index < 0 or args.case_index >= len(cases):
                    raise ValueError("case-index fora do intervalo.")
                selected = cases[args.case_index]
            output = write_case_explanation(
                selected,
                method=cast(MethodName, args.method),
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


def _parse_methods(values: Sequence[str]) -> tuple[MethodName, ...]:
    if values == ["all"]:
        return METHODS
    invalid = set(values) - set(METHODS)
    if invalid:
        raise ValueError(f"Métodos desconhecidos: {sorted(invalid)}")
    return tuple(cast(MethodName, value) for value in values)


def _print_outputs(outputs: dict[str, Path]) -> None:
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
