"""Reproduce a committed experiment without changing its historical artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import distributions
from pathlib import Path
from typing import Mapping, Sequence


FROZEN_REVISION = "9ad7404d5ed8c67be4b748873939d9ccc727256f"
ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ArtifactComparison:
    """Keep raw-byte evidence separate from Git's LF text representation."""

    path: str
    git_blob_sha256: str
    generated_raw_sha256: str
    generated_lf_sha256: str
    raw_bytes_match: bool
    lf_bytes_match: bool
    comparison: str
    passed: bool


def compare_artifact(path: str, expected: bytes, generated: bytes) -> ArtifactComparison:
    """Require exact JSONL bytes; allow only CRLF-to-LF conversion for CSV/report text.

    The frozen CSV writer emits CRLF even when Git stores the file with LF. Both
    hashes remain visible, so a text-equivalent result is never called raw-identical.
    """
    canonical = generated.replace(b"\r\n", b"\n")
    raw_match = generated == expected
    lf_match = canonical == expected
    exact = path.endswith(".jsonl")
    return ArtifactComparison(
        path=path,
        git_blob_sha256=hashlib.sha256(expected).hexdigest(),
        generated_raw_sha256=hashlib.sha256(generated).hexdigest(),
        generated_lf_sha256=hashlib.sha256(canonical).hexdigest(),
        raw_bytes_match=raw_match,
        lf_bytes_match=lf_match,
        comparison="exact_bytes" if exact else "generated_CRLF_to_LF_against_git_blob",
        passed=raw_match if exact else lf_match,
    )


def prepare_output_root(path: Path) -> Path:
    """Reserve an empty output directory; never overwrite an existing experiment."""
    output = path.resolve()
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError(f"Output directory must be new or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    return output


def validate_run_manifest(manifest: Mapping[str, object], revision: str) -> None:
    """Reject provenance that does not identify the requested clean Git checkout."""
    if manifest.get("git_commit") != revision:
        raise ValueError("Fresh manifest does not record the requested Git commit.")
    if manifest.get("git_worktree_dirty") is not False:
        raise ValueError("Fresh manifest does not identify a clean source checkout.")


def _git(git: str, repository: Path, *arguments: str) -> bytes:
    """Run Git directly and return bytes without shell or newline transformations."""
    completed = subprocess.run(
        [git, "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        timeout=120,
    )
    return completed.stdout


def _read_object(data: bytes) -> dict[str, object]:
    """Read a JSON object while keeping unvalidated values out of typed operations."""
    loaded: object = json.loads(data)
    if not isinstance(loaded, dict) or not all(isinstance(key, str) for key in loaded):
        raise ValueError("Expected a JSON object with string keys.")
    return loaded


def _artifact_paths(configuration: Mapping[str, object]) -> tuple[str, ...]:
    """Select the evaluation benchmarks from the committed configuration."""
    seeds = configuration.get("evaluation_seeds")
    if not isinstance(seeds, list) or not seeds or not all(
        isinstance(seed, int) and not isinstance(seed, bool) for seed in seeds
    ):
        raise ValueError("Committed configuration must contain integer evaluation seeds.")
    return (
        *(f"benchmarks/seed_{seed}.jsonl" for seed in seeds),
        "results/benchmark.jsonl",
        "results/per_case.csv",
        "results/by_scenario.csv",
        "results/summary.csv",
        "results/report.md",
    )


def _remove_owned_worktree(git: str, repository: Path, temporary: Path, checkout: Path) -> None:
    """Remove only the worktree created inside this invocation's temporary directory."""
    if checkout.resolve().parent != temporary.resolve() or checkout.name != "source":
        raise ValueError("Refusing to remove a worktree outside the owned temporary directory.")
    _git(git, repository, "worktree", "remove", "--force", str(checkout))
    temporary.rmdir()


def reproduce(revision: str, output_root: Path) -> dict[str, object]:
    """Run the committed CLI in a clean detached worktree and save verification evidence.

    Use the invoking interpreter's installed dependencies. The checkout uses Git
    blob line endings; generated output and Matplotlib cache stay outside it.
    Historical result files and the caller's working-tree changes are never copied.
    """
    git = shutil.which("git")
    if git is None:
        raise ValueError("Git must be installed and available on PATH.")
    commit = _git(git, ROOT, "rev-parse", "--verify", "--end-of-options", f"{revision}^{{commit}}")
    resolved_revision = commit.decode("ascii").strip()
    configuration = _read_object(
        _git(git, ROOT, "show", f"{resolved_revision}:config/experiment.json")
    )
    artifact_paths = _artifact_paths(configuration)
    expected = {
        path: _git(git, ROOT, "show", f"{resolved_revision}:{path}")
        for path in artifact_paths
    }
    output = prepare_output_root(output_root)
    verification: dict[str, object] = {
        "requested_revision": revision,
        "git_commit": resolved_revision,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "configuration": configuration,
        "python": sys.version,
        "installed_distributions": dict(sorted(
            (package.metadata.get("Name", "unknown"), package.version)
            for package in distributions()
        )),
        "comparison_policy": "JSONL: exact bytes; CSV/report: generated CRLF converted to LF, then exact Git blob bytes.",
        "historical_manifests_preserved": True,
        "fresh_manifest": "results/experiment_manifest.json",
        "status": "failed",
    }
    temporary = Path(tempfile.mkdtemp(prefix=".reproduce-frozen-", dir=output.parent)).resolve()
    checkout = temporary / "source"
    worktree_added = False
    try:
        _git(git, ROOT, "-c", "core.autocrlf=false", "worktree", "add", "--detach", str(checkout), resolved_revision)
        worktree_added = True
        if _git(git, checkout, "status", "--porcelain").strip():
            raise ValueError("Temporary source checkout is not clean before execution.")
        verification["worktree_clean_before"] = True
        environment = {
            **os.environ,
            "PATH": str(Path(git).parent) + os.pathsep + os.environ.get("PATH", ""),
            "PYTHONPATH": str(checkout / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "MPLCONFIGDIR": str(output / "matplotlib-cache"),
        }
        command = [
            sys.executable, "-m", "recon_benchmark.cli",
            "--config", str(checkout / "config" / "experiment.json"),
            "run-final", "--output-root", str(output),
        ]
        completed = subprocess.run(command, cwd=checkout, env=environment, capture_output=True)
        (output / "reproduction.log").write_bytes(completed.stdout + completed.stderr)
        if completed.returncode != 0:
            raise RuntimeError(f"Frozen CLI exited with {completed.returncode}; see reproduction.log.")
        manifest = _read_object((output / "results" / "experiment_manifest.json").read_bytes())
        validate_run_manifest(manifest, resolved_revision)
        verification["source_tree_sha256"] = manifest.get("source_tree_sha256")
        clean_after = not _git(git, checkout, "status", "--porcelain").strip()
        verification["worktree_clean_after"] = clean_after
        comparisons = tuple(
            compare_artifact(path, expected[path], (output / path).read_bytes())
            for path in artifact_paths
        )
        verification["artifacts"] = [asdict(item) for item in comparisons]
        if not clean_after:
            raise ValueError("Frozen execution changed its source checkout.")
        if not all(item.passed for item in comparisons):
            raise ValueError("Generated artifacts differ from the committed experiment.")
        verification["status"] = "passed"
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        verification["error"] = str(exc)
    finally:
        try:
            if worktree_added:
                _remove_owned_worktree(git, ROOT, temporary, checkout)
            elif not checkout.exists():
                temporary.rmdir()
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            verification["cleanup_error"] = str(exc)
            verification["status"] = "failed"
        (output / "verification.json").write_text(
            json.dumps(verification, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8", newline="\n",
        )
    return verification


def main(argv: Sequence[str] | None = None) -> int:
    """Expose the frozen revision and a required, non-overwriting output location."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default=FROZEN_REVISION)
    parser.add_argument("--output-root", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        verification = reproduce(args.revision, args.output_root)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Reproduction failed: {exc}", file=sys.stderr)
        return 1
    print(f"Reproduction {verification['status']}: {args.output_root.resolve() / 'verification.json'}")
    return 0 if verification["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
