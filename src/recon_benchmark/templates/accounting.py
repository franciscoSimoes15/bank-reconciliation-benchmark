"""Text conventions for the accounting source."""

from recon_benchmark.domain.models import OperationType

ACCOUNTING_DESCRIPTIONS: dict[OperationType, tuple[str, ...]] = {
    OperationType.SUPPLIER_TRANSFER: (
        "Liquidacao de compra a fornecedor",
        "Pagamento de documento de compras",
    ),
    OperationType.CUSTOMER_RECEIPT: (
        "Recebimento de documento de vendas",
        "Cobranca de cliente registada",
    ),
    OperationType.DIRECT_DEBIT: (
        "Liquidacao automatica de despesa",
        "Pagamento recorrente contabilizado",
    ),
    OperationType.CARD_PAYMENT: (
        "Despesa paga com cartao empresarial",
        "Compra por cartao contabilizada",
    ),
    OperationType.BANK_FEE: (
        "Gasto com servicos bancarios",
        "Encargo de manutencao contabilizado",
    ),
    OperationType.TAX_PAYMENT: (
        "Liquidacao de obrigacao fiscal",
        "Pagamento de imposto registado",
    ),
}

REFERENCE_TEMPLATES: tuple[str, ...] = (
    "{prefix} {year}/{number}",
    "{prefix}/{year}/{number}",
)
