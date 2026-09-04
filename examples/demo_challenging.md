# Explicação do caso `S7-P7_COMBINED-C0000`

- Seed: `7`
- Cenário: `P7_COMBINED`
- Perturbações: `entity:truncate, reference:transpose, amount:+0.01`
- Método: `M4`
- Ground truth usado apenas na avaliação: `S7-P7_COMBINED-C0000-TRUE`

## 1. Movimento bancário recebido pelo matcher

| Campo | Raw | Normalizado |
|---|---|---|
| Amount | `-9820.84` | `-9820.84` |
| Date | `2026-04-13` | `2026-04-13` |
| Reference | `REC0226/70008` | `rec022670008` |
| Counterparty | `PONTE IMOBIL` | `ponte imobil` |
| Description | `DD PONTE IMOBILIARIA SA MANDATO REC2026/70008` | `dd ponte imobiliaria sa mandato rec2026 70008` |

## 2. Ranking dos candidatos

| Rank visual | Candidato | True? | Score | Amount | Date | Reference | Entity | Description | Excluídos |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `S7-P7_COMBINED-C0000-N9` |  | 0.987980 | 1.0000 | 1.0000 | 0.9399 | 1.0000 | 1.0000 | — |
| 2 | `S7-P7_COMBINED-C0000-TRUE` | ✅ | 0.984346 | 1.0000 | 1.0000 | 0.9806 | 0.9412 | 1.0000 | — |
| 3 | `S7-P7_COMBINED-C0000-N7` |  | 0.882001 | 1.0000 | 1.0000 | 0.9399 | 0.5146 | 0.9556 | — |
| 4 | `S7-P7_COMBINED-C0000-N5` |  | 0.662889 | 1.0000 | 1.0000 | 0.6120 | 0.5146 | 0.1879 | — |
| 5 | `S7-P7_COMBINED-C0000-N6` |  | 0.660100 | 1.0000 | 0.0000 | 0.6120 | 0.9412 | 0.7473 | — |
| 6 | `S7-P7_COMBINED-C0000-N8` |  | 0.549864 | 0.0000 | 0.0000 | 0.9399 | 0.9412 | 0.8682 | — |
| 7 | `S7-P7_COMBINED-C0000-N3` |  | 0.482001 | 0.0000 | 0.0000 | 0.9399 | 0.5146 | 0.9556 | — |
| 8 | `S7-P7_COMBINED-C0000-N1` |  | 0.462889 | 1.0000 | 0.0000 | 0.6120 | 0.5146 | 0.1879 | — |
| 9 | `S7-P7_COMBINED-C0000-N2` |  | 0.462889 | 0.0000 | 1.0000 | 0.6120 | 0.5146 | 0.1879 | — |
| 10 | `S7-P7_COMBINED-C0000-N4` |  | 0.460100 | 0.0000 | 0.0000 | 0.6120 | 0.9412 | 0.7473 | — |

## 3. Como ler

O score final é a média simples dos campos disponíveis. Um campo ausente em qualquer lado é excluído, em vez de ser tratado como desacordo. O método nunca consulta o `true_candidate_id`; esse valor só é usado depois do ranking para calcular as métricas.
