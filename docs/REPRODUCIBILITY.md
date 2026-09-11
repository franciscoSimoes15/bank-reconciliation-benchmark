# Reproducing the benchmark

The frozen scientific baseline is
`9ad7404d5ed8c67be4b748873939d9ccc727256f`. The current release translates
documentation, command-line messages, generated explanations, reports, and figure
labels into English. The synthetic transaction text is experimental input, not
documentation: it remains unchanged, as do the configuration, seeds, candidates,
scoring rules, and numerical metrics.

The current files under `benchmarks/`, `results/`, and `figures/` are regenerated
publication artifacts. `results/experiment_manifest.json` and its identical
`manifest.json` alias identify the clean source commit that generated them.
The subsequent artifact commit archives those outputs; its hash is necessarily
different from the source commit recorded before output files were committed.

[`results/publication_verification.json`](../results/publication_verification.json)
records the source revision, comparisons against the frozen baseline, and hashes
of the current artifacts. Reports and figures have translated labels; benchmark
JSONL and primary metric CSVs are compared without changing any data or values.
The release also adds `figures/method_comparison_by_scenario.png`, a compact
M3/M4 comparison generated from the same summary CSV. Its error bars show
sample standard deviations across seeds, not confidence intervals.
The previously added decimal half-up formatting remains in use, including
53.88% for M1 Unique Top-1 and 14.18% for M4-D Tie Rate.

## Historical provenance

The paper's English artifact snapshot is
[`1ec98d3`](https://github.com/franciscoSimoes15/bank-reconciliation-benchmark/tree/1ec98d353fcb94ad0397262cf696ba8fa21afc66),
generated from clean source `98fce0f752d6d5c5eed8994f655f0603e7c65090`.
Later housekeeping removes redundant post-hoc copies, a generated wheel, a
duplicate demo trace, directory placeholders, and a superseded plan from the
working tree. It does not rewrite the published result files, hashes or manifests.
The paper can continue to cite its immutable artifact snapshot.

The consolidated `publication_verification.json` covers every comparison and
artifact hash previously duplicated in `results/posthoc/verification.json`.
Its references such as `8ee9f98:results/posthoc/operation_diagnostics.csv` point
to historical Git blobs and remain valid after removing current duplicate files.

Original artifacts remain available in Git history at the frozen revision.
The original execution manifest is also preserved as
[`original_execution_manifest.json`](../results/reproduction/9ad7404d/original_execution_manifest.json).

That historical manifest records `d19a62c1e0695b2a062ce4eb7b2a331174622f7e`
with `git_worktree_dirty: true`. It describes the worktree used when those
artifacts were originally generated; it does not certify a clean run of the
later published revision. A fresh reproduction must record its own provenance.

The separately archived [verification record](../results/reproduction/9ad7404d/verification.json)
and [fresh manifest](../results/reproduction/9ad7404d/results/experiment_manifest.json)
document a successful clean reproduction of that published revision. Its
verification refers to that revision's Git blobs, including the original
Portuguese report, rather than the English report now at the same repository
path. The verifier can regenerate the complete historical output directory.

## Run the verifier

Use Python 3.11+ and Git on `PATH`. Install the dependencies from
`requirements-lock.txt` in the interpreter's virtual environment, following the
README. The verifier does not install packages or change configuration.

From the repository root, verify the current English release:

```powershell
python scripts/reproduce_frozen.py --revision HEAD --output-root ../english-reproduction
```

To reproduce the exact artifact snapshot cited in the paper:

```powershell
python scripts/reproduce_frozen.py --revision 1ec98d353fcb94ad0397262cf696ba8fa21afc66 --output-root ../paper-reproduction
```

To reproduce the original frozen baseline, including its historical presentation:

```powershell
python scripts/reproduce_frozen.py --output-root ../frozen-reproduction
```

The output directory must be new or empty. To reproduce another committed
experiment, supply `--revision <commit>` explicitly. That revision must contain
the final CLI, configuration, and reference artifacts. Its configuration is used
without overrides; the verifier does not tune methods or inspect evaluation
results to select settings.

The script resolves the revision to a commit, creates a clean detached Git
worktree, and runs that revision's `run-final` with the invoking Python
interpreter. Outputs and plotting cache go outside the temporary source
checkout. It checks that the source is clean before and after execution and
that the fresh manifest records the requested commit and a clean worktree.
The temporary worktree is removed afterwards. Changes in the caller's checkout
are never included in the frozen run.

The temporary checkout disables automatic Git newline conversion. Its source
hash therefore measures the committed LF source bytes and can differ from a
hash of the same revision checked out with Windows CRLF conversion enabled.

The output contains the complete regenerated benchmark, metrics, report, figure,
and fresh manifests, plus `verification.json` and `reproduction.log`.
`verification.json` records the resolved commit, configuration, Python and
installed package versions, fresh source hash, and a comparison for every
evaluation-seed JSONL, the combined JSONL, and the four CSV/Markdown artifacts.
The command exits with status 0 only when provenance and every comparison pass.

## Exact byte and text comparisons

Reference bytes are read directly from the requested commit's Git blobs, avoiding
local checkout line-ending conversion.

- **JSONL:** the generated bytes and SHA-256 must match the Git blob exactly.
- **CSV and report:** Git stores LF text, while the frozen CSV writer emits
  CRLF and the frozen Markdown writer uses platform newlines. The verifier
  converts only generated CRLF sequences to LF, then requires exact equality
  and SHA-256 equality with the Git blob. It also reports raw hashes and whether
  the original bytes matched. No numeric rounding, sorting, whitespace removal,
  or value rewriting is allowed.

These are deliberately distinct checks: LF-equivalent CSV text is not claimed
to be raw-byte-identical. The `.gitattributes` rule preserves LF for JSONL on
future checkouts, so benchmark files can also be checked directly against their
published hashes.

The fresh manifest's timestamp, Python/platform information, source hash, and
Git provenance can differ from the historical manifest. Figures can also differ
between rendering environments. Those files are preserved in the new run but
are not required to match historical bytes. Current manifests and the preserved
historical manifest are separate records.

## Scope of the evidence

A successful verification establishes numerical reproducibility of the frozen
synthetic experiment and identifies the source used for the reproduction. It
does not retrospectively prove when thresholds were selected or establish
performance on real bank data. `requirements-lock.txt` pins direct dependencies;
the fresh verification records the installed transitive packages as additional
environment evidence.
