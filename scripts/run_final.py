"""Executa o protocolo final a partir de qualquer diretório."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recon_benchmark.cli.main import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "--config",
                str(ROOT / "config" / "experiment.json"),
                "run-final",
                "--output-root",
                str(ROOT),
            ]
        )
    )
