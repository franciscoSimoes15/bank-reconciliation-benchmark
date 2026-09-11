# Benchmark results

Values are means across evaluation seeds; sample standard deviations are recorded in `summary.csv`.

## Overall summary

| Method | Code | Unique Top-1 | MRR | Tie Rate |
|---|---|---:|---:|---:|
| `normalized_exact` | M0 | 49.43% | 0.7519 | 47.23% |
| `tolerant_deterministic` | M1 | 53.88% | 0.7656 | 45.13% |
| `jaro_winkler_text` | M2 | 62.18% | 0.7983 | 1.38% |
| `character_trigram_text` | M3 | 75.90% | 0.8658 | 1.20% |
| `field_aware` | M4 | 79.80% | 0.8850 | 1.23% |
| `field_aware_without_description` | M4-D | 74.95% | 0.8887 | 14.18% |

## Unique Top-1 by scenario

| Method | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M0 | 59.00% | 57.20% | 60.00% | 29.60% | 59.00% | 59.00% | 30.00% | 41.60% |
| M1 | 66.40% | 66.40% | 58.80% | 33.80% | 66.40% | 66.40% | 33.20% | 39.60% |
| M2 | 68.40% | 68.40% | 45.60% | 69.00% | 68.40% | 70.20% | 52.40% | 55.00% |
| M3 | 81.80% | 81.80% | 66.00% | 80.20% | 81.80% | 82.60% | 62.80% | 70.20% |
| M4 | 84.40% | 84.40% | 77.80% | 78.00% | 84.40% | 87.40% | 67.00% | 75.00% |

## Post-hoc diagnostics by operation

Pooled proportions from the existing cases, including paired scenarios. This is a descriptive analysis performed after the protocol freeze, not new independent samples. The CSV also includes per-seed results and means/sample standard deviations across seeds. Subtotals overlap with the individual operation rows.

| Operation | Base events | Cases | M4 Unique Top-1 | M4-D Unique Top-1 |
|---|---:|---:|---:|---:|
| Supplier transfer | 83 | 664 | 97.44% | 97.59% |
| Customer receipt | 83 | 664 | 95.33% | 96.54% |
| Direct debit | 83 | 664 | 95.48% | 95.33% |
| Card payment | 84 | 672 | 59.67% | 63.54% |
| Bank fees | 84 | 672 | 35.27% | 0.00% |
| Tax payment | 83 | 664 | 96.39% | 97.74% |
| Other operations (subtotal) | 416 | 3328 | 88.79% | 90.08% |
| Total | 500 | 4000 | 79.80% | 74.95% |

For bank fees, one hard negative shares the true candidate's amount, date, absent reference, and absent entity, while its description is forced to differ. M4-D necessarily ties these candidates. Each source samples from only two templates per operation, without an event-specific narrative fact. Breaking a tie using description does not, by itself, demonstrate additional identifying information.

## Paired amount diagnostics

Each amount variant is compared with its natural-variation case. Counts refer to the true candidate's average rank, Unique Top-1, and the number of candidates tied at the top; they do not measure changes to the complete ordering.

| Method | Pairs | Rank changed | Unique Top-1 changed | Top tie size changed |
|---|---:|---:|---:|---:|
| M0 | 500 | 90 | 9 | 82 |
| M1 | 500 | 22 | 0 | 22 |
| M2 | 500 | 1 | 0 | 0 |
| M3 | 500 | 0 | 0 | 0 |
| M4 | 500 | 0 | 0 | 0 |
| M4-D | 500 | 1 | 0 | 1 |

All three hard negatives retain the true amount. A bank-side amount change affects this score component equally for the true candidate and these competitors. The observed invariance also depends on this candidate construction.

## Interpretation

Unique Top-1 requires the true candidate to be the sole highest-scoring candidate. MRR uses the average rank for ties, and Tie Rate measures the proportion of cases with multiple candidates sharing the highest score.

The benchmark measures synthetic 1:1 ranking with the true candidate present. It does not measure automatic reconciliation, calibration, 1:N/N:1/N:N relations, or production performance.
