# Experimental perturbations

Perturbations add controlled variation to the independently rendered bank record. They use `dataclasses.replace()` to return another record; accounting candidates remain fixed. Implementations and operation tags are in [perturbations.py](perturbations.py).

## Available operations

| Family | Current implementation | Tag examples |
|---|---|---|
| Amount | Choose ±0.05, ±0.25, or ±0.5% of the absolute amount, rounded to cents with a minimum proportional delta of 0.01 | `amount:+0.25` |
| Date | Choose a day offset from `-30, -10, -3, -1, 1, 3, 10, 30` | `date:-3d` |
| Reference | Replace separators, compact, transpose unequal adjacent digits, or substitute a digit | `reference:compact`, `reference:substitute` |
| Entity | Remove a trailing legal suffix if present, truncate to roughly 60%, introduce a typo, or change case/known accents | `entity:truncate`, `entity:typo` |
| Description | Rotate word order, delete a token, truncate to roughly 70%, prefix boilerplate, or abbreviate known words | `description:reorder`, `description:abbreviate` |
| Missing | Remove one optional field that is actually available | `missing:reference`, `missing:counterparty` |
| Combined | Sample and apply three different families from the first five rows | Three separate operation tags |

The amount/date perturbation choices are constants in this module. They are distinct from matcher tolerances and gradual-comparison scales in the experiment configuration.

Truncation retains at least four characters when the input permits. Description deletion targets a token longer than two characters. Known abbreviations include `PAGAMENTO → PAG` and `TRANSFERENCIA → TRF`.

## When information is already absent

Reference variation adds a `TRACE-...` value when no reference exists. Entity variation adds `ENTIDADE NAO IDENTIFICADA` when counterparty is absent. These bank-only labels do not invent matching accounting evidence: a field still contributes no score when it is missing on the candidate side.

Missing-information variation removes a present reference or counterparty. The supplied index rotates the selection; if neither is available, it raises `PerturbationNoOpError`. In generated bank-fee records, the generic bank counterparty label supplies an optional field that can be removed.

## No-op protection

`apply_perturbation()` returns `(transaction, tags)`. P0 is the intentional exception: it returns the original transaction with an empty tag tuple.

For experimental scenarios, `_checked()` rejects a result equal to the original record. Reference, entity and description wrappers filter unchanged alternatives before choosing one. The low-level `perturb_reference()` helper itself can return an unchanged candidate edit; callers must not label that as an applied perturbation.

The check concerns raw data, before normalization. Changing `FT-2026-00187` into `FT.2026.00187` is effective even if both later normalize to the same value.

```python
import random
from recon_benchmark.domain.models import Scenario
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark
from recon_benchmark.generation.perturbations import apply_perturbation

base = generate_benchmark(seed=7, cases_per_scenario=1, config=ExperimentConfig())[0]
changed, tags = apply_perturbation(
    base.transaction, Scenario.AMOUNT_VARIATION, random.Random(7), 0,
)
assert changed.amount != base.transaction.amount
assert changed.reference == base.transaction.reference
assert tags[0].startswith("amount:")
```

All randomized choices use the supplied `random.Random`. The generator gives each event/scenario its own derived seed, so randomness does not come from global module state.

Tests: [test_every_declared_perturbation_changes_its_field](../../../tests/test_generator.py) checks raw changes and tag counts across generated paired cases. This describes the implemented operations, not a claim that every generated variation has equal difficulty after normalization.

[Generation overview](README.md) · [Scenario catalogue](README_SCENARIOS.md) · [Normalization](../normalization/README.md)
