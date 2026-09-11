# Methodological foundations

## 1. Sources of the ideas

The project distinguishes three sources:

| Source | Role |
|---|---|
| External domain background | Motivate signals, tolerances, noise, ambiguity and workflows; not part of the public verification evidence. |
| Scientific literature | Choose public comparator families and metrics. |
| Project design decisions | Define size, seeds, perturbations, thresholds and hard negatives. |

Commercial products are not used as performance baselines. Many describe functional capabilities without disclosing their formula, weights or internal algorithm.

Earlier project notes refer to a separate study of 15 commercial engines. That
study is not distributed with this repository and should not be treated as
independently verifiable evidence for the benchmark's results. The implemented
protocol is documented in [implementation decisions](IMPLEMENTATION_DECISIONS.md)
and the component guides.

## 2. Record linkage

The basic framework comes from **Fellegi and Sunter**, who formalized record linkage as the comparison of record pairs through attribute-level evidence and a decision rule.

Reference:

- Fellegi, I. P., & Sunter, A. B. (1969). *A Theory for Record Linkage*. Journal of the American Statistical Association, 64(328), 1183–1210. DOI: `10.1080/01621459.1969.10501049`.

In this project, each pair produces a vector:

```text
amount_score
date_score
reference_score
entity_score
description_score
```

## 3. Jaro-Winkler

Jaro-Winkler is a classical family of comparators used in record linkage, particularly for names and short strings with typos or transpositions.

The project uses the maintained `RapidFuzz` implementation to avoid reimplementing an error-prone formula.

Background references:

- U.S. Census Bureau, *An Adaptive String Comparator for Record Linkage*.
- U.S. Census Bureau, *Evaluating String Comparator Performance for Record Linkage*.
- Cohen, W. W., Ravikumar, P., & Fienberg, S. E. (2003). *A Comparison of String Distance Metrics for Name-Matching Tasks*.

## 4. Character q-grams

Ukkonen formalized approximate string matching with q-grams: a string is represented through local fragments of length `q`.

This project uses `q=3`, boundary markers and cosine similarity over counts.

Reference:

- Ukkonen, E. (1992). *Approximate string-matching with q-grams and maximal matches*. Theoretical Computer Science, 92(1), 191–211. DOI: `10.1016/0304-3975(92)90143-4`.

## 5. Comparing metrics

Cohen, Ravikumar and Fienberg compared several metrics for matching names and records. This literature supports the decision not to assume that a single text metric is ideal for every field.

The project therefore compares:

- uniformly applied Jaro-Winkler;
- uniformly applied q-grams;
- a field-aware combination.

## 6. Ranking metrics

MRR is used when the position of the first correct result matters. As there is exactly one true candidate, its position uses average rank for ties:

```text
RR = 1 / position of the correct candidate
MRR = mean of RR values
```

The reciprocal-rank metric follows the TREC/NIST tradition; using average rank
within a tie is this benchmark's explicit convention. **Unique Top-1** measures
whether the correct candidate is alone at the top of the ranking. It does not
calibrate an automatic-reconciliation decision.

## 7. Bank reconciliation domain

Recent work formulates bank reconciliation as a representation, record-linkage and link-prediction problem:

- Munoz, J., Jalili, M., & Tafakori, L. (2025). *Enhancing Bookkeeper Decision Support Through Graph Representation Learning for Bank Reconciliation*. The Journal of Finance and Data Science, 100170. DOI: `10.1016/j.jfds.2025.100170`.

This benchmark is deliberately smaller and transparent: it trains no models and is limited to 1:1 matching.

## 8. Project-specific decisions

The following choices do not come directly from a paper:

- 8 scenarios;
- 100 cases per scenario;
- 5 evaluation seeds;
- 10 candidates per case;
- ±€0.10;
- ±3 days;
- 6 natural negatives from other events and 3 controlled hard negatives;
- a simple mean of available fields, with equal availability within a case;
- an entity legal-suffix list limited to `LDA` and `SA`.

These decisions are protocol parameters, frozen before observing the final results. They are not presented as universal values for bank reconciliation.

## 9. Separation of generation and matching

The latent `FinancialEvent` independently generates a bank view and an accounting view. The matcher never receives that event, ground truth, scenario, perturbations or candidate origin. Results therefore measure only compatibility between observable fields.

The same events and candidate sets are reused across all eight scenarios. Scenario comparisons are therefore paired and do not mix different samples.

## 10. Proximity and missing values

M2–M4 use gradual proximity for amount/date, unlike M1's tolerant binary rule. M4 treats the reference as a prefix/year/number structure where possible and uses Jaro-Winkler only as a fallback.

A missing value excludes the field from aggregation rather than adding a disagreement. The benchmark preserves availability across candidates and explicitly validates the number of compared fields.
