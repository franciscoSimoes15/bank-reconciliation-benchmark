# Implementation decisions before the freeze

This file records protocol decisions implemented using development seed `7`, before evaluation seeds `42–46`.

## Latent event and rendering

The old model first constructed an `AccountingRecord` and copied it into a `BankTransaction`. That model was removed. A latent `FinancialEvent` now feeds two independent renderers with separate randomness sources.

Descriptions represent source conventions, not a shared hidden identifier. In particular, they do not systematically include reference/entity, avoiding double counting of these signals during aggregation.

## Candidate sets

Candidate sets are constructed before perturbations and reused without changing their contents or order across the eight scenarios. This removes the previous dependence of a negative on scenario-observed values.

The composition is fixed at 1+6+3:

- the true candidate is the event's accounting rendering;
- six natural negatives are existing records from other events in the synthetic ledger;
- three controlled hard negatives are new coherent events that share specific evidence.

IDs use the same opaque format regardless of origin.

## Availability and missing values

Operation types determine whether reference/entity exist. To prevent a candidate from benefiting from fewer compared fields, all ten candidates in a case retain the same availability pattern. The missing-information scenario removes bank-side information, affecting all candidates equally.

In addition to recording `compared_field_count`, evaluation fails when these counts differ across candidates.

## Scores

M0 and M1 retain exact/binary rules. M2–M4 use linear functions bounded to `[0,1]` for amount/date proximity. The amount scale is the maximum of 1 euro and 1% of the larger absolute amount; the temporal scale is 30 days. These values are explicit in the configuration because the protocol requires graduality but does not specify the function.

M4 decomposes recognized references into prefix, year and number. The transparent combination is 15% prefix, 15% year and 70% number; the number comparison requires exact equality. Jaro-Winkler is the fallback when the format is not recognized. These weights are internal to the structured comparator, not learned field-aggregation weights.

The mean of available fields uses no trained weights. `FIELD_AWARE_WITHOUT_DESCRIPTION` remains a simple ablation.

The aggregate standard deviation is the sample standard deviation (`n-1`) and equals zero when a run contains only one seed.

## Cases without reference/entity

Not all types have a document or accounting entity. In these cases, a hard negative uses only possible conflicts without inventing fields. In `reference_variation`, an originally absent reference may receive a bank trace; in `entity_variation`, an absent entity may receive a source label. Both are effective changes, but neither creates artificial accounting evidence.

## Freeze

`run-final` uses `config/experiment.json` directly and exposes no seed, size or method overrides. The manifest records the effective configuration, versions, timestamp, commit and hashes. After seeds `42–46`, methodological changes require a new protocol; only confirmed bugs can justify corrections to this version.
