"""Gera duas explicações: um caso resolvido e um caso difícil/falhado."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recon_benchmark.config import load_config  # noqa: E402
from recon_benchmark.explanation import write_case_explanation  # noqa: E402
from recon_benchmark.generator import generate_benchmark  # noqa: E402
from recon_benchmark.serialization import write_jsonl  # noqa: E402


if __name__ == "__main__":
    config = load_config(ROOT / "config" / "experiment.json")
    cases = generate_benchmark(seed=config.development_seed, cases_per_scenario=1, config=config)
    benchmark_path = write_jsonl(cases, ROOT / "examples" / "demo_benchmark.jsonl")

    success_case = next(case for case in cases if case.scenario == "P3_REFERENCE_NOISE")
    challenging_case = next(case for case in cases if case.scenario == "P7_COMBINED")

    success_path = write_case_explanation(
        success_case,
        method="M4",
        config=config,
        output=ROOT / "examples" / "demo_success.md",
    )
    challenging_path = write_case_explanation(
        challenging_case,
        method="M4",
        config=config,
        output=ROOT / "examples" / "demo_challenging.md",
    )

    print(f"Benchmark de demonstração: {benchmark_path}")
    print(f"Caso resolvido: {success_path}")
    print(f"Caso difícil/falhado: {challenging_path}")
