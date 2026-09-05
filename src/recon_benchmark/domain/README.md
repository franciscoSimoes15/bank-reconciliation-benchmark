# Domain models

The domain defines the objects passed between generation, ranking and evaluation. These are frozen dataclasses and descriptive `StrEnum` values; processing functions live in other modules.

## Data objects

| Class in [models.py](models.py) | Meaning | Where it is used |
|---|---|---|
| `FinancialEvent` | Underlying occurrence: signed amount, event date, operation type, legal name, bank alias and optional document reference | Generation and independent rendering |
| `BankTransaction` | Bank view: posting date, amount, reference, counterparty, description and ID | Matcher input |
| `AccountingRecord` | Accounting view: date, amount, reference, entity, description and ID | Matcher input and candidate record |
| `BenchmarkCandidate` | Accounting record plus origin, source event and optional hard-negative kind | Generation/evaluation metadata |
| `BenchmarkCase` | Bank transaction, candidate tuple, true candidate ID, scenario, seed and perturbation tags | A complete evaluation question |

The renderer functions both receive the same event directly. A bank transaction is not derived from the accounting record, and an accounting record is not derived from the bank transaction.

```text
FinancialEvent
├── bank renderer ──────── BankTransaction
└── accounting renderer ─ AccountingRecord
                              ↓ wrapped with evaluation metadata
                          BenchmarkCandidate

BenchmarkCase = one bank transaction + ten candidates + evaluation metadata
```

## Enumerations

| Enum | Role |
|---|---|
| `OperationType` | Select applicable fields and source templates; see [generation](../generation/README.md) |
| `Scenario` | Select the paired experimental variant; see [scenarios](../generation/README_SCENARIOS.md) |
| `MatchingMethod` | Select compatibility calculations; see [ranking](../ranking/README.md) |
| `CandidateOrigin` | Distinguish truth, natural negatives and controlled hard negatives |
| `HardNegativeKind` | Describe the intended controlled conflict family |

[codes.py](codes.py) maps descriptive methods/scenarios to output labels such as M4 and P2. Code and CLI arguments use descriptive enum values, not these labels.

## Model methods and boundaries

`to_dict()` creates JSON-compatible mappings; `from_dict()` restores dates, decimal amounts, enums and nested objects. [validation.py](validation.py) checks incoming field types. These checks do not replace [benchmark validation](../generation/generator.py), which checks candidate composition and scenario pairing.

`BenchmarkCase.candidate_records` exposes the observable records in stored order. `true_candidate()` and `true_candidate_entry()` are for code allowed to consult truth, never for scoring.

The JSONL benchmark retains event IDs, origins and truth for auditing. The scoring call receives only `BankTransaction`, `AccountingRecord`, a method and configuration. An ID field is available on each record, but `score_pair()` does not score identity.

`frozen=True` prevents normal field reassignment; it does not make every possible nested Python value deeply immutable. Tuples preserve candidate/scenario ordering. `Decimal` and `date` keep money and dates explicit.

Tests: [generation](../../../tests/test_generator.py), [matcher boundary](../../../tests/test_matchers.py), [serialization through the pipeline](../../../tests/test_pipeline.py).

[Project guide](../../../README.md) · [Next: generation](../generation/README.md)
