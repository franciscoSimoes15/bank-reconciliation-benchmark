# True and negative candidates

Each benchmark case asks a method to rank exactly ten accounting records. A negative is a plausible record from a different financial event, not a negative monetary amount. Implementation: [negatives.py](negatives.py), coordinated by [generator.py](generator.py).

## Candidate composition

| Origin | Count | Construction |
|---|---:|---|
| `true` | 1 | Accounting rendering of the target event |
| `natural_negative` | 6 | Existing accounting records from other events in the supporting ledger |
| `controlled_hard_negative` | 3 | Accounting renderings of deliberately constructed conflicting events |

`BenchmarkCandidate` wraps an `AccountingRecord` with origin and source-event metadata. Only the record crosses the scoring boundary; see [domain models](../domain/README.md).

## Selecting natural negatives

`select_natural_negatives()`:

1. Excludes the target event.
2. Requires the same reference/entity availability pattern as the true record.
3. Sorts eligible records by amount-sign agreement, relative amount difference, date difference and ID.
4. Samples six without replacement from a nearby pool of up to eighteen records, using its supplied RNG.

These are complete records produced independently from other ledger events. They are not copies of the true record with isolated fields changed. Selection is not uniform over the entire ledger, and candidates are not required to have the same operation type. The retrieval heuristic defines challenge data; it is not one of the ranking methods being evaluated.

## Constructing controlled hard negatives

The following relationships are defined against the target latent event and its accounting record, not against the experimentally perturbed bank transaction. One shared random direction determines the positive or negative date shifts.

| Kind | Preserved evidence | Deliberate changes when those fields exist |
|---|---|---|
| `amount_date_near_reference` | Same amount and event/accounting date | Different entity; document number +1 |
| `same_entity_other_document` | Same amount and entity | Document number +17; date shifted by ±7 days |
| `multi_field_challenger` | Same amount and entity | Document number +2; date shifted by ±1 day |

The builder creates three `FinancialEvent` objects with separate IDs and renders them as accounting records. Reference shifts preserve the prefix, year and digit width. Card-payment and bank-fee events have no document reference; the builder preserves that absence rather than inventing one.

`_render_distinct_record()` retries if all observable fields duplicate truth. If necessary, it adds an alternative accounting description ending in `extraordinario`, then verifies distinction. This matters for bank-fee events with little structured evidence. Thus a hard-negative family name does not imply that every optional conflict field exists in every operation family.

## Pairing, fairness and leakage

Candidates are constructed once per target event, shuffled deterministically and reused in the same order across all eight scenarios. Their IDs share the opaque `cand_...` format without readable origin labels. The generator knows truth to construct and validate the benchmark; the matcher does not.

All ten accounting candidates share the reference/entity presence pattern. Evaluation additionally rejects unequal counts of compared fields. Neither the natural-negative selector nor the hard-negative builder receives scenario or perturbed bank data.

```python
from collections import Counter
from recon_benchmark.domain.models import CandidateOrigin
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark

case = generate_benchmark(seed=7, cases_per_scenario=1, config=ExperimentConfig())[0]
assert Counter(candidate.origin for candidate in case.candidates) == {
    CandidateOrigin.TRUE: 1,
    CandidateOrigin.NATURAL_NEGATIVE: 6,
    CandidateOrigin.CONTROLLED_HARD_NEGATIVE: 3,
}
assert len({candidate.record.id for candidate in case.candidates}) == 10
```

Tests: [test_generator.py](../../../tests/test_generator.py) covers composition, pairing, IDs and hard-negative conflicts; [test_evaluation.py](../../../tests/test_evaluation.py) covers compared-field fairness.

[Generation overview](README.md) · [Scenarios](README_SCENARIOS.md) · [Ranking](../ranking/README.md)
