# Normalization

Normalization puts equivalent representations into a comparable form before a method assigns scores. It returns comparison values; it does not overwrite the raw bank or accounting records stored in a case.

Implementation: [fields.py](fields.py). Next step: [ranking](../ranking/README.md).

## Available normalizers

| Function | Input | Processing | Example output |
|---|---|---|---|
| `normalize_text()` | Text or `None` | Decompose Unicode, remove accent marks, lowercase, replace non-ASCII-alphanumeric characters with spaces, collapse whitespace | `"  Órbita & Filhos, Lda. "` → `"orbita filhos lda"` |
| `normalize_reference()` | Reference or `None` | Apply text normalization and remove all remaining spaces | `"FT-2026 / 00187"` → `"ft202600187"` |
| `normalize_entity()` | Entity or `None` | Apply text normalization and remove whole `lda` and `sa` tokens | `"ÓRBITA SERVIÇOS LDA"` → `"orbita servicos"` |
| `normalize_description()` | Description or `None` | Apply the shared text normalization, retaining word order | `"PAGAMENTO, CARTÃO"` → `"pagamento cartao"` |
| `normalize_amount()` | `Decimal` | Round to two decimal places using `ROUND_HALF_UP` | `Decimal("12.345")` → `Decimal("12.35")` |

Entity normalization removes those legal-form tokens wherever they occur, not only at the end. Description normalization does not expand abbreviations, sort words, remove boilerplate or infer meaning. Reference normalization preserves digits and leading zeros but discards separators.

Dates are already `datetime.date` objects. Equality and day differences are calculated in the matcher; there is no separate date normalizer.

## Missing information

All text normalizers return `None` for an absent input or a result with no content, such as an empty string or punctuation-only text. Entity normalization can also produce `None` if only removable legal-form tokens remain.

The matcher excludes such a field from the average. Missing is not automatically a score of zero. The [metrics layer](../metrics/README.md) checks that candidates were compared using equal numbers of fields.

## Try the actual functions

Run this in Python with the project installed:

```python
from decimal import Decimal
from recon_benchmark.normalization.fields import (
    normalize_amount, normalize_description, normalize_entity,
    normalize_reference, normalize_text,
)

assert normalize_text("  Órbita & Filhos, Lda. ") == "orbita filhos lda"
assert normalize_reference("FT-2026 / 00187") == "ft202600187"
assert normalize_entity("ÓRBITA SERVIÇOS LDA") == "orbita servicos"
assert normalize_description("PAGAMENTO, CARTÃO") == "pagamento cartao"
assert normalize_amount(Decimal("12.345")) == Decimal("12.35")
assert normalize_text("!!!") is None
assert normalize_reference(None) is None
```

## Normalization versus perturbation

A reference perturbation can change `FT-2026-00187` into `FT.2026.00187`. This is a real raw-value change even though both normalize to `ft202600187`. A method resisting a formatting perturbation is an intended observation; the no-op rule applies to the raw value.

These rules are tailored to the generated text families. They do not provide general multilingual entity resolution or prove that two different references identify the same document.

Tests: [test_normalization.py](../../../tests/test_normalization.py), [test_matchers.py](../../../tests/test_matchers.py).

[Project guide](../../../README.md) · [Perturbations](../generation/README_PERTURBATIONS.md)
