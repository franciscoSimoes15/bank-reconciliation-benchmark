# Compatibility scoring and ranking

This area assigns each accounting candidate a compatibility score against a bank transaction, then orders candidates. It does not use the known answer to calculate scores.

| File | Responsibility |
|---|---|
| [models.py](models.py) | `ScoreBreakdown`, parsed `ReferenceComponents`, and `CandidateScore` |
| [matchers.py](matchers.py) | `score_pair()` and field-specific comparisons |
| [similarity.py](similarity.py) | Jaro-Winkler and character q-gram cosine |
| [ordering.py](ordering.py) | Descending score order, with ID as deterministic secondary key |

## Methods

| Output | Descriptive method name | Amount/date | Text |
|---|---|---|---|
| M0 | `normalized_exact` | Equality | Equality after normalization |
| M1 | `tolerant_deterministic` | Binary tolerance | Equality after normalization |
| M2 | `jaro_winkler_text` | Gradual proximity | Jaro-Winkler on every text field |
| M3 | `character_trigram_text` | Gradual proximity | Character-trigram cosine on every text field |
| M4 | `field_aware` | Gradual proximity | Structured reference, Jaro-Winkler entity, trigram description |
| M4-D | `field_aware_without_description` | Same as M4 | Same as M4, excluding description |

M0 requires exact normalized evidence. M1 permits absolute amount differences up to 0.10 and date differences up to three days under the default configuration. M2-M4-D use gradual amount/date scores rather than those binary tolerance cutoffs.

## Gradual comparisons

Amounts are rounded to cents first. With normalized amounts `a` and `b`:

```text
scale = max(absolute_scale, relative_scale × max(abs(a), abs(b)))
amount_score = clamp(1 - abs(a - b) / scale, 0, 1)
date_score = clamp(1 - abs(day_difference) / date_scale_days, 0, 1)
```

Defaults are absolute scale 1.00, relative scale 0.01 and date scale 30 days. Amounts 100.00 and 99.75 therefore score 0.75. A five-day date gap scores approximately 0.8333. These are compatibility measures, not probabilities.

Jaro-Winkler uses the normalized similarity from RapidFuzz. Trigram cosine counts overlapping fragments with start/end markers: `acme` produces `^ac`, `acm`, `cme`, `me$`. Cosine compares the resulting frequency vectors and returns zero for empty or zero-norm vectors. Normalization happens before these text comparisons.

## Structured references

M4 parses compact normalized references into a letter prefix, four-digit year and numeric document identifier. It uses:

```text
reference_score = 0.15 × prefix_Jaro_Winkler
                + 0.15 × year_equality
                + 0.70 × document_number_equality
```

These fixed contributions are not learned weights. Year and document-number comparisons within this structured reference calculation are binary. If either reference does not fit the structure, comparison falls back to Jaro-Winkler. Exact reference equality scores 1.

```python
from datetime import date
from decimal import Decimal
from math import isclose
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.normalization.fields import normalize_reference
from recon_benchmark.ranking.matchers import (
    amount_proximity, date_proximity, structured_reference_similarity,
)

config = ExperimentConfig()
assert amount_proximity(Decimal("100.00"), Decimal("99.75"), config) == 0.75
assert isclose(date_proximity(date(2026, 1, 1), date(2026, 1, 6), config), 5 / 6)
left = normalize_reference("FT-2026-00187")
right = normalize_reference("FT-2026-00188")
assert left is not None and right is not None
assert isclose(structured_reference_similarity(left, right), 0.30)
```

## Aggregation and ordering

`score_pair()` calculates the simple mean of available field scores. Fields missing on either side are excluded; description is also excluded for M4-D. `ScoreBreakdown` records the total, per-field scores, excluded fields and count. For example, scores `1.0, 0.9, 0.3, 0.8, 0.6` average to 0.72.

`rank_candidates()` sorts by descending total and then ID. IDs do not contribute to compatibility. Equal scores still represent a tie for [evaluation](../metrics/README.md), regardless of their display order. Evaluation rejects candidates compared with different field counts.

Tests: [test_matchers.py](../../../tests/test_matchers.py), [test_similarity.py](../../../tests/test_similarity.py), [test_evaluation.py](../../../tests/test_evaluation.py).

[Project guide](../../../README.md) · [Normalization](../normalization/README.md) · [Metrics](../metrics/README.md)
