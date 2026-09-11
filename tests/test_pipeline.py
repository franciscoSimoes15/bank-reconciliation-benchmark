import csv
import json
from pathlib import Path

from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import validate_benchmark
from recon_benchmark.domain.models import MatchingMethod
from recon_benchmark.experiment.pipeline import run_experiment
from recon_benchmark.storage.serialization import read_jsonl
from recon_benchmark.metrics.reporting import _source_tree_digest
from recon_benchmark.metrics.reporting import _decimal, _pct


def test_small_pipeline_writes_and_validates_all_required_outputs(tmp_path: Path) -> None:
    """Run a small experiment and verify artifacts, benchmark invariants, metric dimensions and
    manifest provenance.
    """
    config = ExperimentConfig()
    methods = (
        MatchingMethod.NORMALIZED_EXACT,
        MatchingMethod.CHARACTER_TRIGRAM_TEXT,
        MatchingMethod.FIELD_AWARE,
        MatchingMethod.FIELD_AWARE_WITHOUT_DESCRIPTION,
    )
    outputs = run_experiment(
        seeds=[7],
        cases_per_scenario=1,
        methods=methods,
        config=config,
        root=tmp_path,
    )
    assert set(outputs) == {
        "benchmark",
        "per_case",
        "by_scenario",
        "summary",
        "operation_diagnostics",
        "amount_pair_diagnostics",
        "report",
        "experiment_manifest",
        "manifest",
        "figure",
        "paper_comparison_figure",
    }
    assert all(path.exists() and path.stat().st_size > 0 for path in outputs.values())
    assert (tmp_path / "benchmarks" / "seed_7.jsonl").exists()
    assert outputs["experiment_manifest"].read_bytes() == outputs["manifest"].read_bytes()

    cases = read_jsonl(outputs["benchmark"])
    assert len(cases) == 8
    assert not validate_benchmark(
        cases,
        config=config,
        expected_cases_per_scenario=1,
    )

    per_case_rows = _csv_rows(outputs["per_case"])
    assert len(per_case_rows) == 8 * len(methods)
    assert all(int(row["compared_field_count"]) >= 2 for row in per_case_rows)
    assert {row["method_code"] for row in per_case_rows} == {"M0", "M3", "M4", "M4-D"}

    scenario_rows = _csv_rows(outputs["by_scenario"])
    assert len(scenario_rows) == 8 * len(methods)
    assert all(row["scenario"] != "ALL" for row in scenario_rows)

    summary_rows = _csv_rows(outputs["summary"])
    assert len(summary_rows) == 9 * len(methods)
    assert sum(row["scenario"] == "ALL" for row in summary_rows) == len(methods)
    assert _csv_rows(outputs["operation_diagnostics"])
    assert _csv_rows(outputs["amount_pair_diagnostics"])
    assert "Post-hoc diagnostics" in outputs["report"].read_text(encoding="utf-8")

    manifest = json.loads(outputs["experiment_manifest"].read_text(encoding="utf-8"))
    assert manifest["effective_run"]["seeds"] == [7]
    assert manifest["configuration"]["natural_negative_count"] == 6
    assert "benchmark.jsonl" in manifest["benchmark_sha256"]
    assert manifest["python"]
    assert manifest["created_at_utc"]
    assert isinstance(manifest["git_worktree_dirty"], (bool, type(None)))
    assert manifest["source_tree_sha256"] == _source_tree_digest(
        Path(__file__).resolve().parents[1]
    )


def test_source_digest_includes_nested_modules_and_templates(tmp_path: Path) -> None:
    """Check nested template edits change the source hash while unrelated report outputs do not."""
    source = tmp_path / "src" / "recon_benchmark"
    templates = source / "templates"
    templates.mkdir(parents=True)
    bank = templates / "bank.py"
    bank.write_text('DESCRIPTION = "TRANSFER"\n', encoding="utf-8")
    initial = _source_tree_digest(tmp_path)
    bank.write_text('DESCRIPTION = "PAYMENT"\n', encoding="utf-8")
    updated = _source_tree_digest(tmp_path)
    assert updated != initial
    (tmp_path / "report.md").write_text("Output does not change source", encoding="utf-8")
    assert _source_tree_digest(tmp_path) == updated


def test_report_rounds_decimal_ties_consistently_with_the_paper() -> None:
    """Protect percentage and metric ties from a binary-float rounding discrepancy."""
    assert _pct("0.141750000000") == "14.18%"
    assert _pct("0.012250000000") == "1.23%"
    assert _pct("0.141749999999") == "14.17%"
    assert _decimal("0.888750000000") == "0.8888"


def _csv_rows(path: Path) -> list[dict[str, str]]:
    """Read generated CSV rows as dictionaries for pipeline-output assertions."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
