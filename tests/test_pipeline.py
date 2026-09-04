from pathlib import Path

from recon_benchmark.config import ExperimentConfig
from recon_benchmark.pipeline import run_experiment


def test_small_pipeline_writes_all_outputs(tmp_path: Path) -> None:
    config = ExperimentConfig()
    outputs = run_experiment(
        seeds=[7],
        cases_per_scenario=1,
        methods=("M0", "M4", "M4-noNorm"),
        config=config,
        root=tmp_path,
    )
    assert (tmp_path / "benchmarks" / "seed_7.jsonl").exists()
    assert set(outputs) == {"per_case", "by_scenario", "summary", "manifest", "report", "figure"}
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs.values())
