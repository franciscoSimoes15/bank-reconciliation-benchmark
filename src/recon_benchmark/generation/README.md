# Generation: from events to benchmark cases

Generation creates coherent synthetic financial events, their independent source representations and paired ranking cases. Nothing here depends on real transactions or a trained model.

## Read this area in order

| File | Responsibility |
|---|---|
| [models.py](models.py) | `LedgerEntry` associates an event with an accounting record; `CandidateIdentity` supplies hard-negative identities |
| [synthetic_data.py](synthetic_data.py) | Generate latent facts and render independent bank/accounting records |
| [negatives.py](negatives.py) | Select natural negatives and construct controlled hard negatives |
| [perturbations.py](perturbations.py) | Apply effective experimental changes to the bank record |
| [generator.py](generator.py) | Coordinate randomness, pairing, candidate order and validation |
| [errors.py](errors.py) | Define `PerturbationNoOpError` |

Detailed guides: [scenarios](README_SCENARIOS.md), [perturbations](README_PERTURBATIONS.md), [negative candidates](README_NEGATIVES.md), [source templates](../templates/README.md).

## Operation families and available fields

These are the current generator conventions, not universal rules for banking data:

| Operation | Amount sign | Document prefix | Accounting entity |
|---|---|---|---|
| `supplier_transfer` | Negative | `FT` | Generated legal name |
| `customer_receipt` | Positive | `REC` | Generated legal name |
| `direct_debit` | Negative | `MD` | Generated legal name |
| `card_payment` | Negative | None | Generated legal name |
| `bank_fee` | Negative | None | None |
| `tax_payment` | Negative | `DUC` | Generated legal name |

The bank uses shorter aliases and gives bank fees the generic label `INSTITUICAO BANCARIA`. The accounting renderer retains the event date; the bank samples a delay from `(0, 0, 1, 2)` days. Dates start from 2026-01-01 with an event offset between 0 and 179 days. Operation-specific amount ranges and generated entity word families are defined in `synthetic_data.py`.

## What generate_benchmark() does

1. Validate configuration and build a supporting ledger of `max(cases_per_scenario, 60)` events and accounting records.
2. Use the first `cases_per_scenario` ledger entries as target events.
3. Render each target's bank record independently.
4. Assemble one true, six natural and three controlled hard candidates; shuffle once.
5. Produce all eight scenario variants using that same candidate tuple and truth.
6. Validate each case and the paired collection, then return a tuple of cases.

The function works in memory. `generate_to_file()` adds the [JSONL writing](../storage/README.md) step. Supporting ledger entries that are not targets can still supply negatives.

## Reproducibility

The generator derives separate integer seeds for event generation, each renderer, negative selection, hard-negative construction, candidate shuffling and each event/scenario perturbation. Every randomized operation uses an explicit `random.Random` instance.

The same seed, configuration and implementation reproduce the same cases and order. Changing a seed changes generated facts. Opaque IDs are hashes of deterministic generation inputs; all candidate origins share the same visible ID format.

```python
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark, validate_benchmark

config = ExperimentConfig()
first = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
again = generate_benchmark(seed=7, cases_per_scenario=2, config=config)
assert len(first) == 16
assert first == again
assert validate_benchmark(first, config=config, expected_cases_per_scenario=2) == []
```

## What validation establishes

Per-case checks cover IDs, the single true candidate, the 1+6+3 split, hard-negative kinds, optional-field availability and negative records distinct from truth. Collection checks cover duplicate case IDs, requested counts, scenario coverage, paired candidate/truth consistency and raw no-op variants. The tests also check that declared perturbation fields actually changed.

Tests: [test_generator.py](../../../tests/test_generator.py).

[Project guide](../../../README.md) · [Next: normalization](../normalization/README.md)
