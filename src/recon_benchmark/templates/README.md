# Independent source templates

Templates describe how the same financial event is expressed by two source systems. They supply natural variation before any experimental perturbation is applied.

| File | Contents | Consumer |
|---|---|---|
| [bank.py](bank.py) | `BANK_DESCRIPTIONS`, bank `REFERENCE_TEMPLATES` | `render_bank_transaction()` |
| [accounting.py](accounting.py) | `ACCOUNTING_DESCRIPTIONS`, accounting `REFERENCE_TEMPLATES` | `render_accounting_record()` |

Both renderers live in [synthetic_data.py](../generation/synthetic_data.py). The template files contain patterns, not event-generation or scoring functions.

## Description families

Each operation has two description alternatives per source. For example:

| Operation | One bank description | One accounting description |
|---|---|---|
| Supplier transfer | `TRF SEPA EMITIDA CANAL EMPRESAS` | `Liquidacao de compra a fornecedor` |
| Customer receipt | `CREDITO TRANSFERENCIA SEPA RECEBIDA` | `Recebimento de documento de vendas` |
| Direct debit | `DEBITO DIRETO SEPA AUTORIZADO` | `Liquidacao automatica de despesa` |
| Card payment | `PAGAMENTO CARTAO TERMINAL POS` | `Despesa paga com cartao empresarial` |
| Bank fee | `COMISSAO MANUTENCAO CONTA` | `Gasto com servicos bancarios` |
| Tax payment | `PAGAMENTO AO ESTADO SERVICOS PUBLICOS` | `Liquidacao de obrigacao fiscal` |

These are operation-level labels. They do not interpolate the entity or document reference into every description, avoiding systematic double counting of the same evidence in scoring. A description may therefore be shared by many different events.

## Reference formats

For a latent reference `FT-2026-00187`, the available outputs are:

| Source | Patterns after substitution |
|---|---|
| Bank | `FT2026 00187` or `FT-2026-00187` |
| Accounting | `FT 2026/00187` or `FT/2026/00187` |

Each renderer selects its own pattern using its own RNG. An absent latent reference stays absent. Formatting uses the latent prefix, year and document number directly; neither renderer receives the other source record.

```python
from recon_benchmark.templates.bank import REFERENCE_TEMPLATES as BANK_REFERENCES
from recon_benchmark.templates.accounting import REFERENCE_TEMPLATES as ACCOUNTING_REFERENCES

parts = {"prefix": "FT", "year": "2026", "number": "00187"}
assert BANK_REFERENCES[0].format(**parts) == "FT2026 00187"
assert ACCOUNTING_REFERENCES[0].format(**parts) == "FT 2026/00187"
```

## Relationship to the experiment

The alias/legal-name distinction and posting delay are renderer decisions, not description-template fields. Extra typos, truncations, amount shifts and missing values belong to [perturbations](../generation/README_PERTURBATIONS.md).

Changing a template can change scores and generated benchmark hashes even when the seed stays fixed. Template definitions should therefore remain fixed during final evaluation, like the rest of the generation setup.

Tests: [test_financial_event_has_two_independent_renderers](../../../tests/test_generator.py) checks distinct descriptions across the operation families.

[Project guide](../../../README.md) · [Generation](../generation/README.md)
