from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from recon_benchmark.domain.models import BenchmarkCase


def write_jsonl(cases: Iterable[BenchmarkCase], path: str | Path) -> Path:
    """Write each BenchmarkCase as one compact JSON object on its own UTF-8 line.

    Use sorted keys and fixed newlines for reproducible bytes. Create parent folders,
    replace existing content and return the output path.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for case in cases:
            handle.write(
                json.dumps(
                    case.to_dict(),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            handle.write("\n")
    return output


def read_jsonl(path: str | Path) -> tuple[BenchmarkCase, ...]:
    """Read nonblank JSONL lines and reconstruct typed BenchmarkCase objects.

    Require one object per line; pretty-printed multiline JSON is not this format.
    Return cases in file order. Field parsing errors propagate, while benchmark
    composition and scenario pairing are checked separately by the generator.
    """
    input_path = Path(path)
    cases: list[BenchmarkCase] = []
    with input_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            raw = json.loads(stripped)
            if not isinstance(raw, dict):
                raise ValueError(f"Line {line_number}: expected a JSON object.")
            cases.append(BenchmarkCase.from_dict(raw))
    return tuple(cases)
