from pathlib import Path

import pytest

from scripts.reproduce_frozen import compare_artifact, prepare_output_root, validate_run_manifest


def test_csv_verification_distinguishes_line_endings_from_changed_metrics() -> None:
    """Accept the frozen CSV writer's CRLF, but reject even one altered result value."""
    expected = b"method,unique_top1\nM4,0.798\n"
    same = compare_artifact("results/summary.csv", expected, expected.replace(b"\n", b"\r\n"))
    assert same.passed
    assert not same.raw_bytes_match
    assert same.lf_bytes_match
    assert same.git_blob_sha256 != same.generated_raw_sha256
    assert same.git_blob_sha256 == same.generated_lf_sha256
    changed = compare_artifact("results/summary.csv", expected, b"method,unique_top1\r\nM4,0.799\r\n")
    assert not changed.passed


def test_jsonl_verification_requires_exact_bytes() -> None:
    """Do not silently normalize a benchmark whose published hash covers LF bytes."""
    expected = b'{"seed":42}\n'
    assert compare_artifact("results/benchmark.jsonl", expected, expected).passed
    converted = compare_artifact("results/benchmark.jsonl", expected, b'{"seed":42}\r\n')
    assert converted.lf_bytes_match
    assert not converted.passed


def test_reproduction_never_overwrites_existing_outputs(tmp_path: Path) -> None:
    """Protect existing experimental evidence before a reproduction reserves its output root."""
    output = prepare_output_root(tmp_path / "run")
    historical = output / "experiment_manifest.json"
    historical.write_bytes(b"original evidence")
    with pytest.raises(ValueError, match="new or empty"):
        prepare_output_root(output)
    assert historical.read_bytes() == b"original evidence"


@pytest.mark.parametrize("dirty", [True, None])
def test_reproduction_rejects_dirty_or_unknown_provenance(dirty: bool | None) -> None:
    """Matching metrics cannot compensate for unavailable or dirty source provenance."""
    with pytest.raises(ValueError, match="clean source"):
        validate_run_manifest({"git_commit": "revision", "git_worktree_dirty": dirty}, "revision")


def test_reproduction_rejects_wrong_commit() -> None:
    """Require the manifest's exact resolved commit, not merely a clean checkout."""
    with pytest.raises(ValueError, match="requested Git commit"):
        validate_run_manifest({"git_commit": "other", "git_worktree_dirty": False}, "revision")
    validate_run_manifest({"git_commit": "revision", "git_worktree_dirty": False}, "revision")
