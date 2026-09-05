# Paired scenarios

A scenario specifies the experimental variant of a bank transaction. Its definition is the `Scenario` enum in [domain/models.py](../domain/models.py); [apply_perturbation()](perturbations.py) implements it.

## Scenario catalogue

| Output code | Enum value used in code/CLI | Additional change beyond natural rendering |
|---|---|---|
| P0 | `natural_variation` | None |
| P1 | `amount_variation` | One nonzero fixed or proportional amount delta |
| P2 | `date_variation` | One nonzero posting-date shift |
| P3 | `reference_variation` | Reference formatting/digit edit, or a trace added when absent |
| P4 | `entity_variation` | Counterparty presentation/spelling edit, or a bank label when absent |
| P5 | `description_variation` | Reorder, token removal, truncation, boilerplate or abbreviation |
| P6 | `missing_information` | Remove one available reference or counterparty |
| P7 | `combined_variation` | Apply three distinct families from amount, date, reference, entity and description |

Use names such as `amount_variation` in the CLI. P0-P7 are output codes. Combined variation does not select missing removal as a family.

## What pairing preserves

For each target `FinancialEvent`, [generate_benchmark()](generator.py) constructs the candidate set once. All eight variants retain:

- the same event identity and underlying facts;
- the same ten accounting candidates in the same shuffled order;
- the same true candidate;
- the same bank record ID, while observed fields can change.

Each scenario receives a different case ID. Experimental variants start from the natural bank record, not the previous scenario's output. Within P7, its three changes are applied sequentially.

This makes scenario comparisons controlled: a ranking difference is not caused by a new candidate set. Natural variation is not a perfect-match case; independent renderers already use different descriptions, entity names and reference formats, and the bank can have a posting delay.

## Case counts

`cases_per_scenario=3` selects three target events and produces `3 × 8 = 24` cases for one seed. The supporting ledger can contain more events so natural negatives remain available. The final configuration produces `100 × 8 × 5 = 4000` cases across evaluation seeds.

```python
from recon_benchmark.domain.models import Scenario
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark

cases = generate_benchmark(seed=7, cases_per_scenario=1, config=ExperimentConfig())
assert len(cases) == 8
assert {case.scenario for case in cases} == set(Scenario)
assert len({case.event_id for case in cases}) == 1
assert all(case.candidates is cases[0].candidates for case in cases)
assert len({case.true_candidate_id for case in cases}) == 1
```

## Validation and interpretation

`validate_case()` checks labels and candidate composition. `validate_benchmark()` checks scenario coverage, candidate/truth consistency and experimental records unchanged from P0. [The generator tests](../../../tests/test_generator.py) additionally compare each tagged field with the natural baseline.

An effective raw perturbation may disappear under normalization. That is expected for some formatting changes; it does not make the raw perturbation a no-op.

[Generation overview](README.md) · [Perturbation operations](README_PERTURBATIONS.md) · [Negative candidates](README_NEGATIVES.md)
