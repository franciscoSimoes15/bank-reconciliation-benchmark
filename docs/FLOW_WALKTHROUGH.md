# Complete workflow walkthrough

Example:

```bash
python -m recon_benchmark.cli demo --scenario combined_variation --method field_aware
```

## 1. Latent event

The generator creates a `FinancialEvent` with an operation type, date, amount and only the applicable fields. The object and `event_id` belong to generation; they do not cross the matcher boundary.

## 2. Two independent representations

The same event is passed separately to:

```text
render_bank_transaction(event, bank_rng)
render_accounting_record(event, accounting_rng)
```

The renderers use different conventions and templates. Scenario P0 therefore already contains natural variation, without copying the description, formatted reference or entity name from one side to the other.

## 3. Ledger and candidates

An accounting ledger is rendered first. Each case selects:

```text
1 true candidate
6 natural negatives from other FinancialEvent objects in the ledger
3 controlled hard negatives
```

Controlled negatives cover amount+date with a conflicting reference, the same entity+amount with another document, and a plausible competitor across multiple fields. For types without a reference, difficulty uses only the naturally available fields.

The ten candidates receive opaque IDs, are shuffled using `random.Random` and remain fixed for the event.

## 4. Paired scenarios

The same natural bank transaction and candidate set produce P0–P7. Only the observed bank transaction receives the experimental perturbation. Each change is compared with the previous value, and a no-op raises `PerturbationNoOpError`.

## 5. Matching

The matcher receives only a `BankTransaction`, an `AccountingRecord`, the method and configuration. It does not receive origin, scenario, perturbations, `event_id` or `true_candidate_id`.

M0 uses normalized equality. M1 uses tolerant binary rules. M2–M4 use gradual proximity for amount/date; M4 compares reference components and applies field-specific text metrics.

## 6. Missing values

A field missing on either side is excluded:

```text
score = sum of compatibility scores / number of compared fields
```

Candidates share the same availability pattern within each case. Evaluation confirms that all have the same `compared_field_count`.

## 7. Ranking and evaluation

After all scores have been calculated:

- Unique Top-1 equals 1 only if the true candidate is alone at the maximum;
- MRR uses average rank for ties;
- Tie Rate records multiple candidates sharing the maximum score.

Only at this stage does the evaluator consult ground truth.

## 8. Outputs

The pipeline writes per-seed and consolidated benchmarks, per-case results,
seed/scenario aggregates, cross-seed means and standard deviations, operation and
paired amount diagnostics, a report, and a manifest containing configuration,
environment, commit and hashes. It generates an overview figure for the primary
methods and, when M3 and M4 are both evaluated, the paper's scenario comparison
with sample standard deviations. See the [output guide](../src/recon_benchmark/metrics/README.md).

The `demo` command above exercises generation and one scoring explanation. Use
`run-final --output-root ../fresh-run` for the complete configured experiment;
the `scripts/run_final.*` shortcuts write into the repository's output folders.
