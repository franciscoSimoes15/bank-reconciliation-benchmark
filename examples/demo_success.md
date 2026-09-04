# Explicação do caso `S7-P3_REFERENCE_NOISE-C0000`

- Seed: `7`
- Cenário: `P3_REFERENCE_NOISE`
- Perturbações: `reference:separators`
- Método: `M4`
- Ground truth usado apenas na avaliação: `S7-P3_REFERENCE_NOISE-C0000-TRUE`

## 1. Movimento bancário recebido pelo matcher

| Campo | Raw | Normalizado |
|---|---|---|
| Amount | `-458.46` | `-458.46` |
| Date | `2026-04-10` | `2026-04-10` |
| Reference | `REC 2026 70004` | `rec202670004` |
| Counterparty | `PONTE CONSULTORIA LDA` | `ponte consultoria` |
| Description | `TRF P/ PONTE CONSULTORIA LDA REF REC2026/70004` | `trf p ponte consultoria lda ref rec2026 70004` |

## 2. Ranking dos candidatos

| Rank visual | Candidato | True? | Score | Amount | Date | Reference | Entity | Description | Excluídos |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `S7-P3_REFERENCE_NOISE-C0000-TRUE` | ✅ | 1.000000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | — |
| 2 | `S7-P3_REFERENCE_NOISE-C0000-N9` |  | 0.989484 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.9474 | — |
| 3 | `S7-P3_REFERENCE_NOISE-C0000-N7` |  | 0.934529 | 1.0000 | 1.0000 | 0.9667 | 0.7485 | 0.9574 | — |
| 4 | `S7-P3_REFERENCE_NOISE-C0000-N5` |  | 0.747143 | 1.0000 | 1.0000 | 0.7190 | 0.7485 | 0.2682 | — |
| 5 | `S7-P3_REFERENCE_NOISE-C0000-N6` |  | 0.694350 | 1.0000 | 0.0000 | 0.7190 | 1.0000 | 0.7527 | — |
| 6 | `S7-P3_REFERENCE_NOISE-C0000-N8` |  | 0.571981 | 0.0000 | 0.0000 | 0.9667 | 1.0000 | 0.8932 | — |
| 7 | `S7-P3_REFERENCE_NOISE-C0000-N1` |  | 0.547143 | 1.0000 | 0.0000 | 0.7190 | 0.7485 | 0.2682 | — |
| 8 | `S7-P3_REFERENCE_NOISE-C0000-N2` |  | 0.547143 | 0.0000 | 1.0000 | 0.7190 | 0.7485 | 0.2682 | — |
| 9 | `S7-P3_REFERENCE_NOISE-C0000-N3` |  | 0.534529 | 0.0000 | 0.0000 | 0.9667 | 0.7485 | 0.9574 | — |
| 10 | `S7-P3_REFERENCE_NOISE-C0000-N4` |  | 0.494350 | 0.0000 | 0.0000 | 0.7190 | 1.0000 | 0.7527 | — |

## 3. Como ler

O score final é a média simples dos campos disponíveis. Um campo ausente em qualquer lado é excluído, em vez de ser tratado como desacordo. O método nunca consulta o `true_candidate_id`; esse valor só é usado depois do ranking para calcular as métricas.
