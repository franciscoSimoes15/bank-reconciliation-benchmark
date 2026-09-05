# Explicação do caso `case_4a8fef496eea5c328099`

- Seed: `7`
- Cenário: `combined_variation` (P7)
- Perturbações: `entity:typo, amount:+0.25, reference:separators`
- Método: `field_aware` (M4)
- Ground truth usado apenas na avaliação: `cand_fa3851642bc36ebf11d8`

## Movimento bancário recebido pelo matcher

| Campo | Raw | Normalizado |
|---|---|---|
| Amount | `5261.52` | `5261.52` |
| Date | `2026-01-11` | `2026-01-11` |
| Reference | `REC2026.0070001` | `rec20260070001` |
| Counterparty | `Horizonte Enegr` | `horizonte enegr` |
| Description | `TRF SEPA RECEBIDA CONTA EMPRESA` | `trf sepa recebida conta empresa` |

## Ranking dos candidatos

| Rank visual | Candidato | True? | Score | Campos | Amount | Date | Reference | Entity | Description | Excluídos |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `cand_fa3851642bc36ebf11d8` | sim | 0.812416 | 5 | 0.9952 | 1.0000 | 1.0000 | 0.9631 | 0.1037 | — |
| 2 | `cand_977c5ed6919d0ab4ac0d` |  | 0.665750 | 5 | 0.9952 | 0.9667 | 0.3000 | 0.9631 | 0.1037 | — |
| 3 | `cand_15b9caea5a85c994de52` |  | 0.625750 | 5 | 0.9952 | 0.7667 | 0.3000 | 0.9631 | 0.1037 | — |
| 4 | `cand_039c54d96f5cce081eca` |  | 0.546461 | 5 | 0.9952 | 1.0000 | 0.3000 | 0.4037 | 0.0334 | — |
| 5 | `cand_0d8f0b07aacdd66b55e9` |  | 0.298629 | 5 | 0.0000 | 0.6333 | 0.3000 | 0.5265 | 0.0334 | — |
| 6 | `cand_0783ddf1d37cad2cc9fd` |  | 0.188636 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5395 | 0.1037 | — |
| 7 | `cand_d2511cec5475c6191369` |  | 0.183598 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5846 | 0.0334 | — |
| 8 | `cand_189f01097059892c0870` |  | 0.178734 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5603 | 0.0334 | — |
| 9 | `cand_032b72743ce978f4687f` |  | 0.169945 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5164 | 0.0334 | — |
| 10 | `cand_c54a4c0d3e32b17fa882` |  | 0.150921 | 5 | 0.0000 | 0.0000 | 0.1500 | 0.4250 | 0.1796 | — |

O score final é a média simples dos campos disponíveis. Um campo ausente em qualquer lado é excluído. A geração valida que todos os candidatos do caso são comparados no mesmo número de campos.

O matcher recebe apenas o movimento bancário e um registo contabilístico. `event_id`, cenário, perturbações, origem e ground truth só são consultados depois do scoring.
