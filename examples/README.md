# Execution examples

- `demo_success.md`: a case where `field_aware` achieves Unique Top-1, when one exists in the sample.
- `demo_challenging.md`: the case with the largest true rank across the sample's eight scenarios; it may contain a failure or tie, without fabricating either.
- `demo_benchmark.jsonl`: eight cases, one per scenario, generated using development seed `7`.

Both reports show raw values, normalized values, field scores and the ranking of all 10 candidates.

Run `python start_here.py` from the repository root to regenerate these three
curated files. The `scripts/run_demo.bat` and `scripts/run_demo.sh` launchers
perform the same operation.

The CLI's `demo` command generates a separate `demo_trace.md` by default. For the
default seed and scenario, it duplicates the challenging example, so that trace
is generated on demand and ignored by Git. `explain` similarly creates an ignored
`case_explanation.md` unless an explicit output path is supplied. See the
[CLI guide](../src/recon_benchmark/cli/README.md) for custom examples.
