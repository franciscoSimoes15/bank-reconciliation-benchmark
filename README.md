# Bank Reconciliation Ranking Benchmark

A synthetic, reproducible Python benchmark for comparing transparent 1:1 ranking methods in bank reconciliation. The true candidate is always present; the project uses no real banking data, ML, embeddings, LLMs or learned weights.

## Workflow

```text
Latent FinancialEvent
├── render_bank_transaction()
└── render_accounting_record()
          ↓
independently rendered accounting ledger
          ↓
1 true + 6 natural negatives + 3 controlled hard negatives
          ↓
same candidate set across 8 paired scenarios
          ↓
matching using only BankTransaction + AccountingRecord
          ↓
Unique Top-1 / MRR with average rank / Tie Rate
```

`BankTransaction` and `AccountingRecord` are independent renderings of the same event. Neither is copied or derived from the other. Their templates differ from the outset, and descriptions do not systematically repeat the reference or entity.

The generator includes at least the following operation types:

- supplier transfer;
- customer receipt;
- direct debit;
- card payment;
- bank fee;
- tax payment.

Reference and entity are optional depending on the type; they are not artificially populated for every event.

## Methods

Names used in code are members of `MatchingMethod` (`StrEnum`). M0–M4 are output codes only.

| Code | Name | Amount / date | Text fields |
|---|---|---|---|
| M0 | `normalized_exact` | equality | equality after normalization |
| M1 | `tolerant_deterministic` | binary rules with ±€0.10 / ±3 days | equality after normalization |
| M2 | `jaro_winkler_text` | gradual proximity | Jaro-Winkler |
| M3 | `character_trigram_text` | gradual proximity | cosine similarity over character trigrams |
| M4 | `field_aware` | gradual proximity | structured reference comparison, Jaro-Winkler for entity and trigrams for description |
| M4-D | `field_aware_without_description` | same as M4 | ablation without description |

Scores are compatibility measures in `[0,1]`, not probabilities. Aggregation is a simple mean of the available fields, with no learned weights.

## Installation

Requires Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install "setuptools>=75" wheel
python -m pip install -e . --no-build-isolation
```

## Tests

```powershell
python -m pytest
```

Tests cover independent rendering, determinism, effective perturbations, pairing, the 1+6+3 composition, opaque IDs, missing values, scores, metrics, leakage prevention and end-to-end outputs.

## Development

Generate and validate a sample:

```powershell
python -m recon_benchmark.cli generate --seed 7 --cases-per-scenario 3 --output benchmarks/seed_7.jsonl
python -m recon_benchmark.cli validate --input benchmarks/seed_7.jsonl --cases-per-scenario 3
```

Run the development seed:

```powershell
python -m recon_benchmark.cli evaluate --seed 7 --cases-per-scenario 3 --methods all --output-root development_run
```

Create a case explanation:

```powershell
python -m recon_benchmark.cli demo --scenario combined_variation --method field_aware
```

You can also run `python start_here.py`.

## Frozen final run

```powershell
python -m recon_benchmark.cli run-final
```

`run-final` does not accept seed, size or method overrides. It uses the configuration recorded in `config/experiment.json`:

- development seed: 7;
- evaluation seeds: 42, 43, 44, 45, 46;
- 100 events per scenario;
- 8 paired scenarios;
- 10 candidates per case.

The minimum outputs are:

```text
results/
  benchmark.jsonl
  per_case.csv
  by_scenario.csv
  summary.csv
  report.md
  experiment_manifest.json
```

The run also writes `benchmarks/seed_<n>.jsonl`, `manifest.json` as a compatibility alias and `figures/robustness_by_scenario.png`. The manifest includes configuration, effective run parameters, versions, timestamp, available commit and SHA-256 hashes.

## Paired scenarios

| Code | `Scenario` | Additional experimental change |
|---|---|---|
| P0 | `natural_variation` | none; retains only the renderers' natural differences |
| P1 | `amount_variation` | absolute or proportional variation |
| P2 | `date_variation` | short, medium or long shift |
| P3 | `reference_variation` | formatting, transposition, substitution or an additional bank reference |
| P4 | `entity_variation` | truncation, typo, case/accent change or bank label |
| P5 | `description_variation` | reordering, deletion, truncation, boilerplate or abbreviation |
| P6 | `missing_information` | removal of an available reference or counterparty |
| P7 | `combined_variation` | three distinct families |

Each declared change is checked against the natural bank transaction; a no-op perturbation raises an error.

## Candidates

Each event uses exactly the same candidate set and order across all eight scenarios:

- 1 true candidate;
- 6 natural negatives: complete accounting records rendered from other `FinancialEvent` objects in the ledger;
- 3 controlled hard negatives: controlled conflicts involving amount/date/reference, entity/document and multiple pieces of evidence.

All candidate IDs have the same opaque format. Their order is shuffled deterministically. Hard negatives do not consult the perturbation or observed transaction, preventing candidate leakage across scenarios.

## Missing values and leakage prevention

A missing field is excluded from the mean. The generator preserves the same availability pattern across all ten candidates, and evaluation rejects rankings with unequal numbers of compared fields.

`score_pair()` accepts only:

```text
BankTransaction + AccountingRecord + MatchingMethod + ExperimentConfig
```

`event_id`, `true_candidate_id`, scenario, perturbations and candidate origin remain outside that boundary and are used only by generation/evaluation.

## Structure

### Component guides

The following guides explain the concepts and current implementation,
with examples and links to code and tests. To follow a case from its
origin, read domain, generation, normalization, ranking and metrics in order.

[Implementation decisions](docs/IMPLEMENTATION_DECISIONS.md) and the component
guides describe the implemented protocol. The
[legacy implementation plan](docs/archive/Legacy_Implementation_Plan_RECPAD_2026.docx)
is retained only as superseded historical documentation; its earlier design
does not define the current benchmark.

| Guide | What it explains |
|---|---|
| [Domain](src/recon_benchmark/domain/README.md) | Events, representations, candidates, cases and data boundaries |
| [Generation](src/recon_benchmark/generation/README.md) | Operation types, renderers, ledger and case assembly |
| [Templates](src/recon_benchmark/templates/README.md) | Independent banking and accounting conventions |
| [Scenarios](src/recon_benchmark/generation/README_SCENARIOS.md) | The eight scenarios and case pairing |
| [Perturbations](src/recon_benchmark/generation/README_PERTURBATIONS.md) | Available changes, tags, missing values and no-op protection |
| [Negatives](src/recon_benchmark/generation/README_NEGATIVES.md) | The 1+6+3 composition and hard-candidate construction |
| [Normalization](src/recon_benchmark/normalization/README.md) | Field-specific rules and before/after examples |
| [Ranking](src/recon_benchmark/ranking/README.md) | Methods, text similarity, gradual proximity and scores |
| [Metrics](src/recon_benchmark/metrics/README.md) | Unique Top-1, MRR, ties, aggregation and outputs |
| [Experiment](src/recon_benchmark/experiment/README.md) | Configuration, seeds, effective parameters and pipeline |
| [Storage](src/recon_benchmark/storage/README.md) | JSONL, serialization and readable inspection |
| [CLI](src/recon_benchmark/cli/README.md) | Commands, arguments and practical examples |

### Files

```text
src/recon_benchmark/
  __main__.py                 entry point for python -m recon_benchmark
  domain/
    models.py                 frozen dataclasses and StrEnum
    validation.py             field validation used by from_dict
    codes.py                  method and scenario output codes
  experiment/
    models.py                 ExperimentConfig class and its invariants
    config.py                 JSON configuration loading and conversion
    pipeline.py               complete experiment orchestration
  storage/
    serialization.py          JSONL reading and writing
  cli/
    __main__.py               entry point for python -m recon_benchmark.cli
    main.py                   arguments and command dispatch
    explanation.py            case explanations for demo/explain
  generation/
    models.py                 LedgerEntry and CandidateIdentity classes
    errors.py                 no-op perturbation exception
    synthetic_data.py         FinancialEvent and independent renderers
    negatives.py              natural and controlled hard negatives
    perturbations.py          experimental changes with no-op guards
    generator.py              paired case assembly and validation
  templates/
    bank.py                   bank descriptions and reference formats
    accounting.py             accounting descriptions and formats
  normalization/
    fields.py                 field-specific normalization
  ranking/
    models.py                 score and reference-component classes
    similarity.py             Jaro-Winkler and character n-grams
    matchers.py               transparent M0–M4 scores
    ordering.py               candidate ordering by score
  metrics/
    models.py                 CaseEvaluation and AggregateMetrics classes
    evaluation.py             ground truth, average rank and metrics
    reporting.py              CSV, cross-seed aggregation, report and manifest
```

All package directories contain `__init__.py`. The commands `recon-benchmark`,
`python -m recon_benchmark` and `python -m recon_benchmark.cli` use the same CLI.
Python imports follow the subpackages, for example
`from recon_benchmark.generation.generator import generate_benchmark`.

To study the code, start with `domain/models.py` and continue through `generation/`,
`templates/`, `normalization/`, `ranking/` and `metrics/`. The pipeline coordinates
these stages; the CLI interprets commands and calls the corresponding operations.

Data classes live in each area's `models.py` file; processing functions live in
the other modules. Object methods such as `validate()`, `to_dict()` and
`from_dict()` remain in their respective classes. For example,
`ranking/models.py` defines `ScoreBreakdown`, while
`ranking/matchers.py` contains the `score_pair()` function that calculates it.

Each class, method and function has an English docstring explaining its role.
The main operations also document relevant inputs/outputs, I/O effects and rules
for missing values, ties and ground-truth protection. Test functions describe the
behavior they verify. These descriptions appear in the editor when inspecting a
symbol and can be read with Python's `help()`.

## Post-hoc review of the frozen experiment

The generator, methods, configuration and numerical results from `9ad7404d`
are unchanged. The [post-hoc analysis](docs/POST_HOC_ANALYSIS.md) explains the
ablation by operation and amount-scenario invariance. In particular, the entire
aggregate Unique Top-1 advantage of M4 over M4-D comes from bank fees; outside
that group, M4-D achieves 90.08% and M4 achieves 88.79%.

New runs write `operation_diagnostics.csv` and
`amount_pair_diagnostics.csv` alongside the existing outputs. The
[additional report](results/posthoc/report.md) identifies these results as
post-hoc diagnostics. Current reports are regenerated in English; historical
outputs remain available through Git history and the preserved reproduction
evidence. Formatting uses explicit decimal rounding, correcting 14.175% to 14.18%.

To verify the published commit in a clean checkout and save a new manifest:

```powershell
python scripts/reproduce_frozen.py --revision HEAD --output-root ../english-reproduction
```

See the [reproduction and hashing policy](docs/REPRODUCIBILITY.md), which
distinguishes exact JSONL equality from LF/CRLF equivalence in CSVs and the report.

## Publication figure

`run-final` also generates `figures/method_comparison_by_scenario.png` directly
from `results/summary.csv`. It compares M3 and M4 in all eight scenarios using
mean Unique Top-1 and sample standard deviation across the evaluation seeds.
The error bars describe variation between generated datasets; they are not
confidence intervals or significance tests. The all-method overview remains
available as `figures/robustness_by_scenario.png`.

Documentation, reports, figure labels, and command-line messages are in English.
Portuguese strings inside synthetic transaction examples remain experimental
data and are intentionally preserved for reproducibility.

## Limitations

The benchmark does not cover 1:N, N:1, N:N, absent true candidates, fees/FX/partial payments as complex relationships, ERP integration or automatic-reconciliation calibration. Synthetic results do not establish production performance.
