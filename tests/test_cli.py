import os
import subprocess
import sys
from collections.abc import Iterable
from importlib import import_module
from pathlib import Path

import pytest

from recon_benchmark.cli.main import main
from recon_benchmark.domain.models import MatchingMethod
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.storage.serialization import read_jsonl


@pytest.mark.parametrize("module", ["recon_benchmark", "recon_benchmark.cli"])
def test_module_entry_points_keep_existing_commands(module: str) -> None:
    source = Path(__file__).resolve().parents[1] / "src"
    completed = subprocess.run(
        [sys.executable, "-m", module, "--help"],
        env={**os.environ, "PYTHONPATH": str(source)},
        capture_output=True,
        text=True,
        check=True,
    )
    for command in ("generate", "validate", "evaluate", "run-final", "demo", "explain"):
        assert command in completed.stdout
    assert not completed.stderr


def test_cli_generates_validates_explains_and_evaluates(tmp_path: Path) -> None:
    benchmark = tmp_path / "benchmark.jsonl"
    assert main([
        "generate", "--cases-per-scenario", "1", "--output", str(benchmark),
    ]) == 0
    assert main([
        "validate", "--input", str(benchmark), "--cases-per-scenario", "1",
    ]) == 0
    assert len(read_jsonl(benchmark)) == 8

    demo_benchmark = tmp_path / "demo.jsonl"
    demo_trace = tmp_path / "demo.md"
    explanation = tmp_path / "explanation.md"
    assert main([
        "demo", "--benchmark-output", str(demo_benchmark), "--output", str(demo_trace),
    ]) == 0
    case = read_jsonl(demo_benchmark)[-1]
    assert main([
        "explain", "--input", str(demo_benchmark), "--case-id", case.case_id,
        "--output", str(explanation),
    ]) == 0
    assert explanation.read_text(encoding="utf-8") == demo_trace.read_text(encoding="utf-8")
    assert case.true_candidate_id in explanation.read_text(encoding="utf-8")

    output_root = tmp_path / "development"
    assert main([
        "evaluate", "--cases-per-scenario", "1", "--methods", "field_aware",
        "--output-root", str(output_root),
    ]) == 0
    assert (output_root / "results" / "per_case.csv").is_file()


def test_run_final_passes_frozen_configuration_to_pipeline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def run_experiment(
        *, seeds: Iterable[int], cases_per_scenario: int,
        methods: Iterable[MatchingMethod], config: ExperimentConfig, root: str | Path,
    ) -> dict[str, Path]:
        nonlocal calls
        calls += 1
        assert tuple(seeds) == config.evaluation_seeds == (42, 43, 44, 45, 46)
        assert cases_per_scenario == config.cases_per_scenario == 100
        assert tuple(methods) == config.methods
        assert Path(root) == tmp_path
        return {}

    monkeypatch.setattr(import_module("recon_benchmark.cli.main"), "run_experiment", run_experiment)
    assert main(["run-final", "--output-root", str(tmp_path)]) == 0
    assert calls == 1
