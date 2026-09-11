# Structural observations from the example spreadsheet

## Usage rule

The file supplied by the user **is not a benchmark dataset**. It was inspected only to understand which description families and banking structures could be represented synthetically.

The project does not include the spreadsheet or copy:

- personal or company names;
- amounts;
- balances;
- specific dates;
- specific references;
- complete rows.

## Observed structural patterns

The example has a typical bank-statement structure:

```text
Posting date
Value date
Description
Debit
Credit
Balance
```

The descriptions show common functional families:

- outgoing transfers with abbreviated prefixes;
- incoming transfers;
- card/terminal purchases with numeric identifiers;
- direct debits;
- loan repayments;
- account or transfer fees;
- stamp duty associated with fees;
- payments to public bodies.

They also contain features relevant to pattern recognition:

- uppercase and lowercase descriptions;
- inconsistent accents and punctuation;
- banking abbreviations;
- embedded numeric identifiers;
- long or truncated names;
- posting dates that differ from value dates;
- separate debit and credit columns.

## How these observations inform the generator

The project uses only generic semantic families and creates independent banking and accounting templates, for example:

```text
BankTransaction:  TRF SEPA EMITIDA CANAL EMPRESAS
AccountingRecord: Liquidacao de compra a fornecedor

BankTransaction:  DEBITO DIRETO SEPA AUTORIZADO
AccountingRecord: Pagamento recorrente contabilizado
```

Reference and entity have dedicated fields and are not systematically repeated in the description. This avoids systematically counting the same evidence twice in the mean. The presence of these fields depends on the operation type.

Amounts are represented by a single signed field:

- incoming/credit → positive;
- outgoing/debit → negative.

The main benchmark uses only `date`, not `value_date`, to keep the scope small. The difference between these dates is documented as a possible direction for future work.
