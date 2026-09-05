# Resultados do benchmark

Os valores são médias entre evaluation seeds; o desvio-padrão amostral está em `summary.csv`.

## Resumo global

| Método | Código | Unique Top-1 | MRR | Tie Rate |
|---|---|---:|---:|---:|
| `normalized_exact` | M0 | 49.43% | 0.7519 | 47.23% |
| `tolerant_deterministic` | M1 | 53.87% | 0.7656 | 45.12% |
| `jaro_winkler_text` | M2 | 62.18% | 0.7983 | 1.38% |
| `character_trigram_text` | M3 | 75.90% | 0.8658 | 1.20% |
| `field_aware` | M4 | 79.80% | 0.8850 | 1.23% |
| `field_aware_without_description` | M4-D | 74.95% | 0.8887 | 14.17% |

## Unique Top-1 por cenário

| Método | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M0 | 59.00% | 57.20% | 60.00% | 29.60% | 59.00% | 59.00% | 30.00% | 41.60% |
| M1 | 66.40% | 66.40% | 58.80% | 33.80% | 66.40% | 66.40% | 33.20% | 39.60% |
| M2 | 68.40% | 68.40% | 45.60% | 69.00% | 68.40% | 70.20% | 52.40% | 55.00% |
| M3 | 81.80% | 81.80% | 66.00% | 80.20% | 81.80% | 82.60% | 62.80% | 70.20% |
| M4 | 84.40% | 84.40% | 77.80% | 78.00% | 84.40% | 87.40% | 67.00% | 75.00% |

## Interpretação

Unique Top-1 exige que o candidato verdadeiro seja o único no maior score. MRR usa a posição média nos empates e Tie Rate mede a proporção de casos com mais de um candidato no maior score.

O benchmark mede ranking sintético 1:1 quando o candidato verdadeiro está presente. Não mede auto-reconciliação, calibração, relações 1:N/N:1/N:N nem desempenho em produção.
