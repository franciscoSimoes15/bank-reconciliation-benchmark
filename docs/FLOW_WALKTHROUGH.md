# Walkthrough do fluxo completo

Exemplo:

```bash
python -m recon_benchmark.cli demo --scenario combined_variation --method field_aware
```

## 1. Acontecimento latente

O gerador cria um `FinancialEvent` com tipo de operação, data, montante e apenas os campos aplicáveis. O objeto e o `event_id` pertencem à geração; não atravessam a fronteira do matcher.

## 2. Duas representações independentes

O mesmo evento é passado separadamente a:

```text
render_bank_transaction(event, bank_rng)
render_accounting_record(event, accounting_rng)
```

Os renderers usam convenções e templates diferentes. Portanto, o cenário P0 já contém variação natural, sem copiar descrição, referência formatada ou nome da entidade de um lado para o outro.

## 3. Ledger e candidatos

Primeiro é renderizado um ledger contabilístico. Para cada caso são escolhidos:

```text
1 true candidate
6 natural negatives de outros FinancialEvent do ledger
3 controlled hard negatives
```

Os negativos controlados cobrem amount+date com referência conflitante, mesma entidade+amount com outro documento e um concorrente plausível em múltiplas evidências. Nos tipos sem referência, a dificuldade usa apenas os campos naturalmente disponíveis.

Os dez candidatos recebem IDs opacos, são baralhados com `random.Random` e ficam congelados para o evento.

## 4. Cenários emparelhados

O mesmo movimento bancário natural e o mesmo candidate set originam P0–P7. Apenas o movimento observado recebe a perturbação experimental. Cada alteração é comparada com o valor anterior e um no-op lança `PerturbationNoOpError`.

## 5. Matching

O matcher recebe apenas um `BankTransaction`, um `AccountingRecord`, o método e a configuração. Não recebe origem, cenário, perturbações, `event_id` nem `true_candidate_id`.

M0 faz igualdade normalizada. M1 usa regras binárias tolerantes. M2–M4 usam proximidade gradual para amount/date; M4 compara a referência por componentes e aplica métricas textuais por campo.

## 6. Missing

Um campo ausente em qualquer lado é excluído:

```text
score = soma das compatibilidades / campos comparados
```

O padrão de disponibilidade dos candidatos é igual dentro de cada caso. A avaliação confirma que todos tiveram o mesmo `compared_field_count`.

## 7. Ranking e avaliação

Depois de todos os scores:

- Unique Top-1 vale 1 apenas se o verdadeiro estiver sozinho no máximo;
- MRR usa o average rank quando há empate;
- Tie Rate assinala múltiplos candidatos no maior score.

Só nesta fase o avaliador consulta o ground truth.

## 8. Outputs

O pipeline escreve o benchmark consolidado, resultados por caso, agregados por seed/cenário, média e desvio-padrão entre seeds, relatório, figura e manifest com configuração, ambiente, commit e hashes.
