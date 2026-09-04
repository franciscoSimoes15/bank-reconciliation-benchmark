from decimal import Decimal

from recon_benchmark.normalization import (
    normalize_amount,
    normalize_description,
    normalize_entity,
    normalize_reference,
    normalize_text,
)


def test_normalize_text_removes_accents_punctuation_and_extra_spaces() -> None:
    assert normalize_text("  Órbita & Filhos,  Lda. ") == "orbita filhos lda"


def test_normalize_reference_compacts_separators() -> None:
    assert normalize_reference("FT-2026 / 00187") == "ft202600187"


def test_normalize_entity_removes_only_generated_legal_suffixes() -> None:
    assert normalize_entity("ÓRBITA SERVIÇOS LDA") == "orbita servicos"
    assert normalize_entity("NOVA SA") == "nova"


def test_normalizers_preserve_missing() -> None:
    assert normalize_text(None) is None
    assert normalize_reference(None) is None
    assert normalize_entity(None) is None
    assert normalize_description(None) is None


def test_normalize_amount_uses_two_decimal_places() -> None:
    assert normalize_amount(Decimal("12.345")) == Decimal("12.35")
