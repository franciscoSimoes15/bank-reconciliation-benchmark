# Storage and JSONL

[serialization.py](serialization.py) reads and writes benchmark cases. It handles file I/O at the edge of the pipeline; field conversion belongs to the [domain models](../domain/README.md).

## Why JSONL?

JSONL contains one complete JSON object per line. Each line in a benchmark is a `BenchmarkCase`, including the bank transaction, ten candidate records, seed, scenario and evaluation metadata.

The following is a format-only illustration, not a complete benchmark schema:

```jsonl
{"case_id":"example_a","seed":7}
{"case_id":"example_b","seed":7}
```

There are no commas between lines and no surrounding array. A standard JSON formatter expecting one document may reject the second object as extra data.

## Writing and reading

| Function | Input | Result |
|---|---|---|
| `write_jsonl(cases, path)` | Iterable of typed cases and destination | Writes compact UTF-8 JSONL and returns a `Path` |
| `read_jsonl(path)` | Existing JSONL file | Returns a tuple of reconstructed cases in file order |

The writer uses sorted keys, fixed `\n` newlines and compact separators for reproducible bytes. It creates parent directories and replaces existing content. Dates become ISO strings, amounts become decimal strings, enum members use descriptive names and absent fields become JSON `null`.

The reader skips blank lines and parses each remaining line separately. It restores `date`, `Decimal`, enums and nested model objects. Invalid JSON or field types raise errors; full candidate composition and scenario pairing require `validate_benchmark()` after reading.

```python
from recon_benchmark.domain.models import BenchmarkCase
from recon_benchmark.experiment.models import ExperimentConfig
from recon_benchmark.generation.generator import generate_benchmark

case = generate_benchmark(seed=7, cases_per_scenario=1, config=ExperimentConfig())[0]
serialized = case.to_dict()
restored = BenchmarkCase.from_dict(serialized)
assert restored == case
```

This in-memory example demonstrates the conversion used by file storage without writing an artifact.

## Viewing one case in PowerShell

After producing a demo benchmark, run this from the project root:

```powershell
Get-Content examples\demo_benchmark.jsonl -TotalCount 1 |
    ConvertFrom-Json |
    ConvertTo-Json -Depth 20
```

This displays an indented version. Keep the benchmark file itself line-oriented: writing multiline pretty JSON back to it would break the current reader. `demo` and `explain` also produce a [Markdown trace](../cli/README.md) for easier inspection.

Truth and origin labels are intentionally serialized for auditing. Their presence in the JSONL does not make them matcher features; the evaluator passes only observable records to scoring.

Tests: [test_pipeline.py](../../../tests/test_pipeline.py) and [test_cli.py](../../../tests/test_cli.py) exercise file round trips and validation.

[Project guide](../../../README.md) · [Generation](../generation/README.md)
