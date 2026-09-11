"""Generate explanations for a successful case and the most challenging case in the sample."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recon_benchmark.experiment.config import load_config  # noqa: E402
from recon_benchmark.metrics.evaluation import evaluate_case  # noqa: E402
from recon_benchmark.cli.explanation import write_case_explanation  # noqa: E402
from recon_benchmark.generation.generator import generate_benchmark  # noqa: E402
from recon_benchmark.domain.models import MatchingMethod, Scenario  # noqa: E402
from recon_benchmark.storage.serialization import write_jsonl  # noqa: E402


if __name__ == "__main__":
    config = load_config(ROOT / "config" / "experiment.json")
    cases = generate_benchmark(seed=config.development_seed, cases_per_scenario=1, config=config)
    benchmark_path = write_jsonl(cases, ROOT / "examples" / "demo_benchmark.jsonl")

    evaluations = {
        case.case_id: evaluate_case(
            case,
            method=MatchingMethod.FIELD_AWARE,
            config=config,
        )
        for case in cases
    }
    success_case = next(
        (case for case in cases if evaluations[case.case_id].unique_top1 == 1),
        next(case for case in cases if case.scenario is Scenario.NATURAL_VARIATION),
    )
    challenging_case = max(
        cases,
        key=lambda case: (
            evaluations[case.case_id].true_rank,
            case.scenario is Scenario.COMBINED_VARIATION,
        ),
    )

    success_path = write_case_explanation(
        success_case,
        method=MatchingMethod.FIELD_AWARE,
        config=config,
        output=ROOT / "examples" / "demo_success.md",
    )
    challenging_path = write_case_explanation(
        challenging_case,
        method=MatchingMethod.FIELD_AWARE,
        config=config,
        output=ROOT / "examples" / "demo_challenging.md",
    )

    print(f"Demo benchmark: {benchmark_path}")
    print(f"Successful case: {success_path}")
    print(f"Most challenging case in the sample: {challenging_path}")
