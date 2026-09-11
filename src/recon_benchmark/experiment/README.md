# Experiment configuration and orchestration

This package decides which experiment runs and coordinates generation, scoring and output. It does not implement individual perturbations or similarity formulas.

| File | Responsibility |
|---|---|
| [models.py](models.py) | Frozen `ExperimentConfig`, defaults, `validate()` and `to_dict()` |
| [config.py](config.py) | Read JSON, check supplied value types and construct validated configuration |
| [pipeline.py](pipeline.py) | Execute requested seeds/methods and produce the complete output set |

## Current configuration

The project file is [config/experiment.json](../../../config/experiment.json). Important values and their consumers are:

| Setting | Default | Meaning |
|---|---|---|
| `cases_per_scenario` | 100 | Target events per seed, each repeated across the eight scenarios |
| `candidates_per_case` | 10 | One true record plus nine negatives |
| `natural_negative_count` | 6 | Ledger negatives per case |
| `controlled_hard_negative_count` | 3 | Constructed conflicting records per case |
| `development_seed` | 7 | Designated development seed |
| `evaluation_seeds` | 42, 43, 44, 45, 46 | Seeds used by the configured final run |
| `amount_tolerance` | `Decimal("0.10")` | M1's inclusive binary amount cutoff |
| `date_tolerance_days` | 3 | M1's inclusive binary date cutoff |
| `amount_similarity_absolute_scale` | `Decimal("1.00")` | Minimum gradual amount scale |
| `amount_similarity_relative_scale` | `Decimal("0.01")` | Gradual scale relative to the larger absolute amount |
| `date_similarity_scale_days` | 30 | Gap at which gradual date compatibility reaches zero |
| `qgram_size` | 3 | Fragment length for character-trigram comparison |
| `tie_epsilon` | `1e-12` | Absolute score tolerance for ties |
| `scenarios`, `methods` | Complete enum sequences | Eight scenarios and six methods including the ablation |

Descriptions of the calculations are in [ranking](../ranking/README.md) and [metrics](../metrics/README.md). Perturbation magnitudes are defined separately in [generation](../generation/README_PERTURBATIONS.md).

## Loading and validation

`load_config(None)` constructs internal defaults. A supplied file must contain a JSON object; omitted keys use loader defaults and present values are checked before construction. Money settings become `Decimal`; scenario/method names become enums. The returned configuration has been validated.

Constructing `ExperimentConfig(...)` directly does not automatically run `validate()`. The pipeline and generator call validation themselves. It checks positive sizes/scales, permitted tolerances, nonempty unique evaluation seeds, candidate composition and the required ordered scenario/method sets.

The frozen class prevents field reassignment during a run. It does not prevent editing the JSON before another run. The validator checks seed uniqueness rather than enforcing the exact five default numbers; the scientific protocol still requires the documented evaluation seeds and a configuration fixed before evaluating them.

```python
from recon_benchmark.experiment.config import load_config
from recon_benchmark.experiment.models import ExperimentConfig

config = load_config()
assert config.candidates_per_case == 10
assert config.evaluation_seeds == (42, 43, 44, 45, 46)
assert config.to_dict()["amount_tolerance"] == "0.10"
small_config = ExperimentConfig(cases_per_scenario=2)
small_config.validate()
```

## Configuration versus effective run

`run_experiment()` receives `seeds`, `cases_per_scenario` and `methods` separately from `config`. Development commands pass their CLI values; `run-final` passes the configured values.

For example, `evaluate --cases-per-scenario 3` runs three cases per scenario even if `config.cases_per_scenario` remains 100. The CLI's development seed default is explicitly 7. The manifest records both the configuration object and effective run parameters so this distinction is visible.

## Pipeline sequence

For each seed, the pipeline generates validated cases, writes a per-seed benchmark and evaluates all requested methods. It then writes the consolidated benchmark, aggregates per seed/scenario and overall, and produces metrics CSVs, report, figures and manifest. It returns a mapping of artifact names to paths. When both M3 and M4 are requested, `paper_comparison_figure` identifies the additional scenario comparison with descriptive error bars.

Artifacts go below the requested root in `benchmarks/`, `results/` and `figures/`. Existing files at the chosen paths are replaced. Source hashing includes nested Python modules and project/configuration files; it records provenance, not a guarantee that results came from a clean committed checkout.

Tests: [test_pipeline.py](../../../tests/test_pipeline.py), [test_cli.py](../../../tests/test_cli.py).

[Project guide](../../../README.md) · [CLI commands](../cli/README.md) · [Metrics outputs](../metrics/README.md)
