# Post-hoc analysis of the frozen experiment

This analysis was added after reviewing the published experiment at
`9ad7404d5ed8c67be4b748873939d9ccc727256f`. It uses the same generated cases,
candidate sets, scores, methods, configuration, and evaluation seeds. No threshold
or generator decision was selected or changed using these diagnostics.

The current English release regenerates reports and execution manifests in
`results/` and `benchmarks/`, with the additional analysis also available in
[`results/posthoc/`](../results/posthoc/). Historical outputs remain available
through Git history and the [reproduction evidence](REPRODUCIBILITY.md).
`run-final` writes the diagnostic CSVs alongside its primary outputs and includes
the breakdown in its report. Use a separate output directory to retain the
checked-in release artifacts:

```powershell
python -m recon_benchmark.cli run-final --output-root ../reviewed-run
```

## Description ablation by operation

The following proportions pool the eight paired scenarios and five seeds. They
are descriptive case proportions, not independent-event estimates or significance
tests. The CSV also provides each seed's result and equal-seed means with sample
standard deviations; those need not equal pooled proportions for unequal strata.

| Subset | Target events | Paired cases | M4 successes | M4-D successes | M4 Unique Top-1 | M4-D Unique Top-1 |
|---|---:|---:|---:|---:|---:|---:|
| Bank fees | 84 | 672 | 237 | 0 | 35.27% | 0.00% |
| Other operations | 416 | 3,328 | 2,955 | 2,998 | 88.79% | 90.08% |
| All | 500 | 4,000 | 3,192 | 2,998 | 79.80% | 74.95% |

The aggregate description advantage is 194 successes: 237 additional successes
on bank fees and 43 fewer on other operations. It does not establish that
descriptions generally provide useful event-identifying information.

For bank fees, the first hard negative has the same amount, date, missing
reference, and missing entity as the truth. The generator requires its description
to differ. Each source independently chooses from two fixed descriptions for the
operation; no event-specific narrative fact connects those choices. Consequently,
M4-D must give that candidate and the truth equal scores. They can tie below a
third candidate, so this does not imply a top-score tie in every fee case. Adding
description can break this ambiguity without establishing additional identifying
evidence. The aggregate MRR/uniqueness trade-off remains numerically correct.

Operation labels are inferred after evaluation from the true accounting record's
known template, with its optional-field availability checked. Unsupported
templates fail explicitly. Labels remain outside all matcher inputs and no
benchmark record schema is extended.

## Amount invariance and candidate construction

All three hard negatives retain the true amount. A bank-side amount change
therefore changes that field's contribution equally for truth and the hard
competitors. Natural negatives can still affect the outcome.

For M4, all 500 natural/amount pairs retain the same true average rank, Unique
Top-1, and top-tie count. These three outcomes do not establish that every
candidate retains its complete ordering. The invariance partly follows from
candidate construction and is not general evidence of robustness to amount errors.
`amount_pair_diagnostics.csv` reports the paired outcome counts for every method.

## Corrections and validation

- Displayed percentages and four-place metrics now use decimal `ROUND_HALF_UP`.
  The stored proportion 0.14175 therefore displays as 14.18%, consistently with
  the paper. Historical report bytes remain available through Git history;
  primary metric values are unchanged.
- Hard-negative semantic checks cover all six operations and eight scenarios.
  Development-seed characterization tests document the bank-fee ambiguity and
  equal amount contributions without tuning evaluation results.
- Diagnostic aggregation tests distinguish pooled case proportions, distinct
  target-event counts, and equal-seed statistics using hand-computed outcomes.
- [Reproducibility evidence](REPRODUCIBILITY.md) preserves historical provenance
  and separately verifies a clean checkout of the frozen revision.

A future generator with meaningful latent narrative facts or different
competitor amounts would require a separately versioned protocol. It must not
silently replace this experiment after its evaluation results were observed.
