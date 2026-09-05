# Ranking evaluation and metrics

This layer answers: **where did the true candidate finish, and how ambiguous was the ranking?** It evaluates synthetic 1:1 cases where the true accounting candidate is present.

| File | Responsibility |
|---|---|
| [models.py](models.py) | `CaseEvaluation` for one case/method; `AggregateMetrics` for a seed/method group |
| [evaluation.py](evaluation.py) | Call the matcher, evaluate truth, handle ties and aggregate within seeds |
| [reporting.py](reporting.py) | Aggregate across seeds and write CSVs, report, figure and manifest |

## From compatibility to an evaluation result

`evaluate_case()` scores every candidate using only the observable bank/accounting pair. It rejects unequal `compared_field_count` values across candidates, orders scores, and then consults `true_candidate_id` to calculate the result. See [ranking](../ranking/README.md) for the score formulas.

A score describes compatibility. A metric measures how successfully that compatibility ranks the known true candidate.

## The three metrics

| Metric | Definition | Interpretation |
|---|---|---|
| Unique Top-1 | Mean of an indicator equal to 1 only when truth is alone at the maximum score | How often there is an unambiguous correct winner; higher is better |
| Mean Reciprocal Rank (MRR) | Mean of `1 / true_rank` | How near the top truth appears; higher is better |
| Tie Rate | Mean of an indicator equal to 1 when multiple candidates share the maximum | How often the top position is ambiguous |

Tie Rate concerns the top candidates even when truth is not among them. A low Tie Rate alone does not imply accuracy: a method can confidently select the wrong candidate.

## Average rank and tolerance

Rank is one-based. If tied candidates occupy positions 2 and 3, each receives `(2 + 3) / 2 = 2.5`. Their reciprocal rank is `1 / 2.5 = 0.4`, not the average of `1/2` and `1/3`.

`average_rank()` counts scores within the absolute `tie_epsilon` of the target as equal. The default is `1e-12`, with no relative tolerance. Top ties use the same tolerance against the maximum. The ID used to order equal-score rows for display never converts a tie into a unique success.

Illustrative three-candidate rankings below can be embedded in ten-candidate cases by placing the remaining candidates lower:

| Scores in descending order (`T` is truth) | True rank | Reciprocal rank | Unique Top-1 | Top tie? |
|---|---:|---:|---:|---:|
| T: 0.9, A: 0.8, B: 0.7 | 1 | 1 | 1 | 0 |
| A: 0.9, T: 0.8, B: 0.7 | 2 | 0.5 | 0 | 0 |
| T: 0.9, A: 0.9, B: 0.7 | 1.5 | 2/3 | 0 | 1 |
| A: 0.9, B: 0.9, T: 0.7 | 3 | 1/3 | 0 | 1 |

Across these four examples: Unique Top-1 = 0.25, MRR = 0.625, Tie Rate = 0.5.

```python
from math import isclose
from recon_benchmark.metrics.evaluation import average_rank

assert average_rank([0.9, 0.9, 0.7], 0.9) == 1.5
assert average_rank([1.0, 0.8, 0.8, 0.2], 0.8) == 2.5
assert isclose(1 / average_rank([0.9, 0.9, 0.7], 0.9), 2 / 3)
assert isclose((1 + 0.5 + 2 / 3 + 1 / 3) / 4, 0.625)
```

## Grouping and outputs

1. `evaluate_cases()` produces one result per case/method.
2. `aggregate_by_seed_scenario()` groups by seed, scenario and method.
3. `aggregate_overall_by_seed()` pools all scenarios per seed/method; `scenario=None` becomes `ALL` in outputs.
4. `write_summary_csv()` averages the per-seed groups and calculates sample standard deviation with denominator `n-1`. A single seed is reported with standard deviation zero.

| Output | Contents |
|---|---|
| `per_case.csv` | Scores, true ranks, top-tie counts, compared fields and per-case indicators |
| `by_scenario.csv` | Metrics for each seed/scenario/method |
| `summary.csv` | Means and standard deviations across seeds, including `ALL` groups |
| `report.md` | Readable global results and primary-method scenario comparisons |
| `robustness_by_scenario.png` | Mean Unique Top-1 by scenario for the five primary methods |
| `experiment_manifest.json` | Configuration, effective run, versions, hashes and available Git state |

`predicted_candidate_id` is `None` for a top tie. M4-D is included in the metric CSVs and global report, but excluded from the primary-method scenario table and figure. Standard deviations across seeds are not confidence intervals, and synthetic results do not establish production performance.

Tests: [test_evaluation.py](../../../tests/test_evaluation.py), [test_pipeline.py](../../../tests/test_pipeline.py).

[Project guide](../../../README.md) · [Experiment configuration](../experiment/README.md)
