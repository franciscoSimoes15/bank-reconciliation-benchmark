# Command-line interface

The CLI translates terminal arguments into calls to generation, evaluation and explanation functions. It does not implement the scoring algorithms.

| File | Role |
|---|---|
| [main.py](main.py) | Build the argument parser, load configuration and dispatch commands |
| [explanation.py](explanation.py) | Produce Markdown traces showing scores and evaluation labels |
| [__main__.py](__main__.py) | Support `python -m recon_benchmark.cli` |
| [__init__.py](__init__.py) | Preserve the exported `main` entry point |

## Start here

Run commands from the project root with the project installed in the active environment. See [installation](../../../README.md) if needed. These interfaces invoke the same CLI:

```powershell
recon-benchmark --help
python -m recon_benchmark --help
python -m recon_benchmark.cli --help
```

General syntax: `python -m recon_benchmark.cli [--config PATH] COMMAND [OPTIONS]`.
Place the global `--config` option before the command. Its default is `config/experiment.json`. Currently a nonexistent CLI config path falls back to internal defaults; check the path if unexpected settings appear.

## Commands and defaults

| Command | Purpose | Options and defaults |
|---|---|---|
| `generate` | Generate and internally validate JSONL | `--seed 7`, `--cases-per-scenario 3`, optional `--output` (otherwise `benchmarks/seed_<seed>.jsonl`) |
| `validate` | Check an existing benchmark | Required `--input`; optional expected `--cases-per-scenario` |
| `evaluate` | Generate, evaluate and report a development experiment | `--seed 7`, `--cases-per-scenario 3`, `--methods all`, `--output-root development_run` |
| `run-final` | Run the configured final seeds, size and methods | Only command-specific option: `--output-root .` |
| `demo` | Generate eight paired cases and explain one | `--seed 7`, `--scenario combined_variation`, `--method field_aware`, `--output examples/demo_trace.md`, `--benchmark-output examples/demo_benchmark.jsonl` |
| `explain` | Explain a case in an existing benchmark | Required `--input`; optional `--case-id`; `--case-index 0`, `--method field_aware`, `--output examples/case_explanation.md` |

`evaluate` generates its own data; it does not accept an input benchmark. `run-final` means the configured scientific run, not a replay of the last command. In `explain`, indices start at zero and a supplied case ID takes precedence over the index.

## Practical development sequence

The following commands use a dedicated directory so their purpose and outputs are easy to follow:

```powershell
python -m recon_benchmark.cli generate --seed 7 --cases-per-scenario 3 --output development_run/guide_sample.jsonl
python -m recon_benchmark.cli validate --input development_run/guide_sample.jsonl --cases-per-scenario 3
python -m recon_benchmark.cli explain --input development_run/guide_sample.jsonl --case-index 0 --output development_run/guide_case.md
python -m recon_benchmark.cli evaluate --seed 7 --cases-per-scenario 3 --methods normalized_exact field_aware --output-root development_run/guide_experiment
```

Use `--methods all` on its own, or list descriptive [method names](../ranking/README.md) separated by spaces. `--scenario` accepts the descriptive [scenario names](../generation/README_SCENARIOS.md), not P0-P7 codes.

For the configured final run, after freezing the experiment settings:

```powershell
python -m recon_benchmark.cli run-final
```

Output-producing commands replace existing files at their selected paths. See [metrics](../metrics/README.md) for the contents of each result artifact.

## Understanding the parser and traces

`argparse` is part of Python's standard library. `add_argument()` declares an accepted option; `parse_args()` reads its actual value. `type=int` converts text to an integer, `default` supplies an omitted value, and `nargs="+"` lets `--methods` accept one or more values. `--help` also works after an individual command.

`demo` and `explain` show raw/normalized bank fields, candidate scores, missing-field exclusions and a truth annotation added after scoring. Their visual row numbers are not the average ranks used to calculate tied-case metrics.

Successful commands return 0; handled execution/validation failures return 1; argparse reports usage errors with exit code 2. PowerShell exposes the last exit code as `$LASTEXITCODE`. Some configuration-loading failures occur before the command error handler and may show a traceback.

Tests: [test_cli.py](../../../tests/test_cli.py).

[Project guide](../../../README.md) · [Experiment configuration](../experiment/README.md)
