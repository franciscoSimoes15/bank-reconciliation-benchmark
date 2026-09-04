# Decisões e correções antes do freeze

Este ficheiro regista alterações feitas durante a development seed `7`, antes de executar as evaluation seeds `42–46`.

## 1. Problema detetado no primeiro smoke run

A primeira versão dos hard negatives produziu `100%` de Unique Top-1 em todos os métodos e cenários.

### Causa confirmada

As perturbações alteravam um ou mais campos do movimento bancário, mas os negativos eram gerados apenas a partir do registo contabilístico canónico. Como consequência, o true candidate continuava geralmente a ter mais acordos exatos do que qualquer candidato falso.

Exemplo simplificado:

```text
True candidate: 4 de 5 campos exatos
Melhor negative: 3 de 5 campos exatos
```

Assim, mesmo o M0 conseguia vencer sem precisar de robustez à perturbação. O benchmark não estava a testar a hipótese pretendida.

## 2. Correção aplicada

O candidato `N9` passou a ser **scenario-aware**: é construído também a partir do movimento bancário observado, para competir diretamente com a família de ruído aplicada.

Exemplos:

- `P1_AMOUNT_NOISE`: N9 tem o montante observado exato, mas uma referência próxima e errada.
- `P2_DATE_DRIFT`: N9 tem a data observada exata, mas uma referência próxima e errada.
- `P3_REFERENCE_NOISE`: N9 usa a referência ruidosa exata, mas a descrição acompanha essa referência errada.
- `P4_ENTITY_NOISE`: N9 usa a entidade ruidosa exata, mas a descrição acompanha a entidade errada.
- `P5_DESCRIPTION_NOISE`: N9 usa a descrição observada exata, mas uma referência próxima e errada.
- `P7_COMBINED`: N9 preserva vários valores observados e mantém pelo menos uma evidência forte incorreta.

Esta alteração afeta todos os métodos igualmente. Não foi introduzida para fazer o M4 vencer; foi introduzida para evitar que o M0 resolvesse o problema sem enfrentar a perturbação.

## 3. Missing information

No cenário `P6_MISSING_INFORMATION`:

- metade dos casos remove `reference` e cria uma alternativa que difere apenas nessa evidência invisível, produzindo ambiguidade irreduzível;
- metade remove `counterparty`, mas mantém informação suficiente na descrição/referência para que o true candidate possa ser recuperado.

O objetivo é distinguir:

```text
missing mas ainda resolúvel
```

 de:

```text
missing que torna dois candidatos observacionalmente indistinguíveis
```

## 4. Critério para aceitar a correção

Depois da alteração:

- M0 já não resolve automaticamente os cenários com ruído;
- M1 isola o benefício de tolerâncias de amount/date;
- M2 e M3 exibem comportamentos diferentes perante texto;
- M4 melhora alguns tipos de campo, mas não vence necessariamente todos os cenários;
- P6 mantém uma fração deliberadamente ambígua;
- os testes e invariantes continuam a passar.

A partir da execução das seeds `42–46`, estas escolhas ficam congeladas salvo bug confirmado e documentado.
