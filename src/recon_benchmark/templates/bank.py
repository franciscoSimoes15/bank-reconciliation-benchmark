"""Convenções textuais da fonte bancária."""

from recon_benchmark.domain.models import OperationType

BANK_DESCRIPTIONS: dict[OperationType, tuple[str, ...]] = {
    OperationType.SUPPLIER_TRANSFER: (
        "TRF SEPA EMITIDA CANAL EMPRESAS",
        "TRANSFERENCIA SEPA PARA TERCEIROS",
    ),
    OperationType.CUSTOMER_RECEIPT: (
        "CREDITO TRANSFERENCIA SEPA RECEBIDA",
        "TRF SEPA RECEBIDA CONTA EMPRESA",
    ),
    OperationType.DIRECT_DEBIT: (
        "DEBITO DIRETO SEPA AUTORIZADO",
        "COBRANCA POR DEBITO DIRETO",
    ),
    OperationType.CARD_PAYMENT: (
        "PAGAMENTO CARTAO TERMINAL POS",
        "COMPRA COM CARTAO EMPRESA",
    ),
    OperationType.BANK_FEE: (
        "COMISSAO MANUTENCAO CONTA",
        "ENCARGO BANCARIO PERIODICO",
    ),
    OperationType.TAX_PAYMENT: (
        "PAGAMENTO AO ESTADO SERVICOS PUBLICOS",
        "DEBITO PAGAMENTO FISCAL",
    ),
}

REFERENCE_TEMPLATES: tuple[str, ...] = (
    "{prefix}{year} {number}",
    "{prefix}-{year}-{number}",
)
