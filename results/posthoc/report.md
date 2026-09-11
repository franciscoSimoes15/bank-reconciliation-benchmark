# Resultados do benchmark

Os valores são médias entre evaluation seeds; o desvio-padrão amostral está em `summary.csv`.

## Resumo global

| Método | Código | Unique Top-1 | MRR | Tie Rate |
|---|---|---:|---:|---:|
| `normalized_exact` | M0 | 49.43% | 0.7519 | 47.23% |
| `tolerant_deterministic` | M1 | 53.88% | 0.7656 | 45.13% |
| `jaro_winkler_text` | M2 | 62.18% | 0.7983 | 1.38% |
| `character_trigram_text` | M3 | 75.90% | 0.8658 | 1.20% |
| `field_aware` | M4 | 79.80% | 0.8850 | 1.23% |
| `field_aware_without_description` | M4-D | 74.95% | 0.8887 | 14.18% |

## Unique Top-1 por cenário

| Método | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| M0 | 59.00% | 57.20% | 60.00% | 29.60% | 59.00% | 59.00% | 30.00% | 41.60% |
| M1 | 66.40% | 66.40% | 58.80% | 33.80% | 66.40% | 66.40% | 33.20% | 39.60% |
| M2 | 68.40% | 68.40% | 45.60% | 69.00% | 68.40% | 70.20% | 52.40% | 55.00% |
| M3 | 81.80% | 81.80% | 66.00% | 80.20% | 81.80% | 82.60% | 62.80% | 70.20% |
| M4 | 84.40% | 84.40% | 77.80% | 78.00% | 84.40% | 87.40% | 67.00% | 75.00% |

## Análise diagnóstica posterior por operação

Proporções agrupadas dos casos existentes, incluindo os cenários emparelhados. São uma análise descritiva posterior ao freeze; não são novas amostras independentes. O CSV inclui também resultados por seed e média/desvio-padrão entre seeds. Os subtotais sobrepõem-se às linhas por operação.

| Operação | Eventos base | Casos | M4 Unique Top-1 | M4-D Unique Top-1 |
|---|---:|---:|---:|---:|
| Transferência a fornecedor | 83 | 664 | 97.44% | 97.59% |
| Recebimento de cliente | 83 | 664 | 95.33% | 96.54% |
| Débito direto | 83 | 664 | 95.48% | 95.33% |
| Pagamento com cartão | 84 | 672 | 59.67% | 63.54% |
| Comissões bancárias | 84 | 672 | 35.27% | 0.00% |
| Pagamento fiscal | 83 | 664 | 96.39% | 97.74% |
| Restantes operações (subtotal) | 416 | 3328 | 88.79% | 90.08% |
| Total | 500 | 4000 | 79.80% | 74.95% |

Nas comissões, um hard negative partilha montante, data, referência ausente e entidade ausente com o verdadeiro, mas a descrição é forçada a diferir. M4-D empata necessariamente esses candidatos. Cada fonte escolhe apenas dois templates por operação, sem um facto narrativo específico do evento. Desempatar com descrição não demonstra, por si só, informação identificadora adicional.

## Diagnóstico emparelhado de montante

Comparação de cada variante de montante com o seu caso natural. As contagens referem-se à posição média do verdadeiro, Unique Top-1 e tamanho do empate no topo; não medem alterações de toda a ordenação.

| Método | Pares | Posição alterada | Unique Top-1 alterado | Empate no topo alterado |
|---|---:|---:|---:|---:|
| M0 | 500 | 90 | 9 | 82 |
| M1 | 500 | 22 | 0 | 22 |
| M2 | 500 | 1 | 0 | 0 |
| M3 | 500 | 0 | 0 | 0 |
| M4 | 500 | 0 | 0 | 0 |
| M4-D | 500 | 1 | 0 | 1 |

Os três hard negatives preservam o montante verdadeiro. Uma alteração bancária modifica igualmente essa componente no verdadeiro e nesses concorrentes. A invariância observada depende também desta construção dos candidatos.

## Interpretação

Unique Top-1 exige que o candidato verdadeiro seja o único no maior score. MRR usa a posição média nos empates e Tie Rate mede a proporção de casos com mais de um candidato no maior score.

O benchmark mede ranking sintético 1:1 quando o candidato verdadeiro está presente. Não mede auto-reconciliação, calibração, relações 1:N/N:1/N:N nem desempenho em produção.
