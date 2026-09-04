# Resultados do benchmark

## Resumo global

| Método | Unique Top-1 | MRR | Tie rate |
|---|---:|---:|---:|
| M0 | 31.35% | 0.7517 | 57.55% |
| M1 | 59.03% | 0.8568 | 37.28% |
| M2 | 66.20% | 0.8444 | 8.03% |
| M3 | 71.05% | 0.8687 | 8.05% |
| M4 | 73.42% | 0.8805 | 8.00% |
| M4-noNorm | 70.40% | 0.8622 | 6.35% |

## Unique Top-1 por cenário

| Método | P0_CLEAN | P1_AMOUNT_NOISE | P2_DATE_DRIFT | P3_REFERENCE_NOISE | P4_ENTITY_NOISE | P5_DESCRIPTION_NOISE | P6_MISSING_INFORMATION | P7_COMBINED |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M0 | 100.00% | 0.00% | 0.00% | 50.80% | 37.20% | 12.80% | 50.00% | 0.00% |
| M1 | 100.00% | 100.00% | 100.00% | 50.80% | 37.20% | 12.80% | 50.00% | 21.40% |
| M2 | 100.00% | 100.00% | 100.00% | 56.00% | 58.40% | 20.60% | 50.00% | 44.60% |
| M3 | 100.00% | 100.00% | 100.00% | 50.80% | 40.00% | 69.40% | 50.00% | 58.20% |
| M4 | 100.00% | 100.00% | 100.00% | 94.60% | 87.20% | 14.00% | 50.00% | 41.60% |

## Leituras automáticas

- Melhor resultado global entre M0–M4: **M4**, com **73.42%** de Unique Top-1 e MRR **0.8805**.
- `P0_CLEAN`: melhor resultado de **M0, M1, M2, M3, M4** (100.00%).
- `P1_AMOUNT_NOISE`: melhor resultado de **M1, M2, M3, M4** (100.00%).
- `P2_DATE_DRIFT`: melhor resultado de **M1, M2, M3, M4** (100.00%).
- `P3_REFERENCE_NOISE`: melhor resultado de **M4** (94.60%).
- `P4_ENTITY_NOISE`: melhor resultado de **M4** (87.20%).
- `P5_DESCRIPTION_NOISE`: melhor resultado de **M3** (69.40%).
- `P6_MISSING_INFORMATION`: melhor resultado de **M0, M1, M2, M3, M4** (50.00%).
- `P7_COMBINED`: melhor resultado de **M3** (58.20%).
- A normalização aumentou o Unique Top-1 global do M4 em **3.02 pontos percentuais**; o efeito deve continuar a ser analisado por cenário, porque não é necessariamente uniforme.
- `P6_MISSING_INFORMATION` contém deliberadamente casos observacionalmente indistinguíveis; 100% não é um objetivo possível nesse cenário.

## Leitura correta

Estes resultados medem robustez relativa num benchmark sintético controlado de matching 1:1. Não demonstram desempenho em produção, superioridade sobre produtos comerciais, nem validade para 1:N/N:N.
