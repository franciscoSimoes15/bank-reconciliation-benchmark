# Walkthrough do fluxo completo

Este documento explica o que acontece quando se executa:

```bash
python -m recon_benchmark.cli demo --scenario P7_COMBINED --method M4
```

## Passo 1 — Criar o registo contabilístico canónico

O gerador cria um objeto fictício:

```text
AccountingRecord
  id
  date
  signed amount
  reference
  entity
  description
```

A entidade e a referência são totalmente sintéticas. A descrição é criada através de um template bancário genérico.

## Passo 2 — Derivar o movimento bancário

Inicialmente, o `BankTransaction` contém os mesmos cinco sinais do registo correto:

```text
AccountingRecord.entity      → BankTransaction.counterparty
AccountingRecord.reference   → BankTransaction.reference
AccountingRecord.description → BankTransaction.description
```

Nesse momento o par é perfeito e constitui o ground truth.

## Passo 3 — Aplicar ruído apenas ao lado bancário

No cenário `P7_COMBINED`, o gerador escolhe três famílias distintas entre:

```text
amount
date
reference
entity
description
```

O AccountingRecord correto não é alterado.

Isso simula a situação em que o ERP mantém um registo canónico, enquanto o banco comunica a mesma operação com diferenças de formato, timing ou texto.

## Passo 4 — Criar nove hard negatives

Os falsos candidatos não são aleatórios. Cada um preserva evidências diferentes:

```text
N1  mesmo amount
N2  mesma date
N3  reference próxima
N4  mesma entity
N5  mesmo amount + date próxima
N6  mesmo amount + entity
N7  mesmo amount + date + reference próxima
N8  description semelhante + entity
N9  mesmo amount + date + entity; reference errada mas próxima
```

O candidato correto e os nove negativos são baralhados deterministicamente.

## Passo 5 — Normalizar

A normalização é distinta por tipo de campo.

### Reference

```text
FT-2026 / 00187 → ft202600187
```

### Entity

```text
ÓRBITA SERVIÇOS LDA → orbita servicos
```

### Description

```text
TRF P/ ÓRBITA SERVIÇOS, LDA. → trf p orbita servicos lda
```

M4-noNorm salta esta fase nos campos textuais, permitindo medir a contribuição do preprocessing.

## Passo 6 — Calcular score por campo

No M4:

```text
Amount      → tolerância de ±0,10 €
Date        → tolerância de ±3 dias
Reference   → Jaro-Winkler
Entity      → Jaro-Winkler
Description → character 3-gram cosine
```

Cada score fica entre `0` e `1`.

## Passo 7 — Tratar missing

Quando `reference` ou `counterparty` está ausente, o campo é excluído:

```text
score = soma dos scores disponíveis / número de campos disponíveis
```

Missing não significa mismatch.

## Passo 8 — Ordenar candidatos

Todos os candidatos são ordenados por score decrescente. O ID só serve como desempate visual estável; não altera o average rank usado nas métricas.

## Passo 9 — Avaliar

Só depois do ranking é consultado o `true_candidate_id`.

- **Unique Top-1:** 1 apenas se o verdadeiro for o único candidato com score máximo.
- **MRR:** `1 / average rank` do verdadeiro.
- **Tie Rate:** indica se mais de um candidato ficou no topo.

## Passo 10 — Produzir outputs

O pipeline final escreve:

- benchmark reproduzível;
- resultados por caso;
- agregação por cenário e seed;
- média/desvio-padrão entre seeds;
- manifest com configuração e hashes;
- relatório Markdown;
- figura PNG.
