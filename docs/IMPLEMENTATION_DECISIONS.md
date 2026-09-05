# Decisões de implementação antes do freeze

Este ficheiro regista decisões do protocolo implementadas com a development seed `7`, antes das evaluation seeds `42–46`.

## Evento latente e renderização

O modelo antigo construía primeiro o `AccountingRecord` e copiava-o para `BankTransaction`. Foi removido. Agora um `FinancialEvent` latente alimenta dois renderers independentes com fontes de aleatoriedade separadas.

As descrições representam convenções da fonte, não um identificador oculto comum. Em particular, não incluem sistematicamente reference/entity, para evitar dupla contagem desses sinais na agregação.

## Candidate sets

Os candidate sets são construídos antes das perturbações e reutilizados sem alteração de conteúdo ou ordem nos oito cenários. Isto elimina a antiga dependência de um negativo em valores observados no cenário.

A composição fica fixa em 1+6+3:

- o true candidate é a renderização contabilística do evento;
- seis natural negatives são registos reais do ledger sintético, provenientes de outros eventos;
- três controlled hard negatives são novos eventos coerentes que partilham evidências específicas.

Os IDs usam o mesmo formato opaco independentemente da origem.

## Disponibilidade e missing

Os tipos de operação determinam se reference/entity existem. Para impedir que um candidato beneficie por ter menos evidências comparadas, os dez candidatos de um caso conservam o mesmo padrão de disponibilidade. O cenário missing remove informação do lado bancário, afetando todos de forma igual.

Além do registo de `compared_field_count`, a avaliação falha quando as contagens diferem entre candidatos.

## Scores

M0 e M1 mantêm as regras exatas/binárias. M2–M4 usam funções lineares e limitadas a `[0,1]` para proximidade de amount/date. A escala de amount é o máximo entre 1 euro e 1% do maior montante absoluto; a escala temporal é 30 dias. Estes valores estão explícitos na configuração porque o protocolo exige gradualidade, mas não fixa a função.

M4 decompõe referências reconhecidas em prefixo, ano e número. A combinação transparente é 15% prefixo, 15% ano e 70% número; o número tem de ser exatamente igual. Jaro-Winkler é fallback quando o formato não é reconhecido. Estes pesos são internos ao comparador estruturado, não pesos aprendidos da agregação de campos.

A média dos campos disponíveis não usa pesos treinados. `FIELD_AWARE_WITHOUT_DESCRIPTION` mantém-se apenas como ablation simples.

O desvio-padrão agregado é amostral (`n-1`) e vale zero quando a execução contém apenas uma seed.

## Casos sem reference/entity

Nem todos os tipos têm documento ou entidade contabilística. Nesses casos, um hard negative usa apenas os conflitos possíveis sem inventar campos. Em `reference_variation`, uma referência originalmente ausente pode receber um trace bancário; em `entity_variation`, uma entidade ausente pode receber uma label da fonte. Ambas são alterações reais, mas não passam a criar evidência contabilística artificial.

## Freeze

`run-final` usa diretamente `config/experiment.json` e não disponibiliza overrides de seeds, tamanho ou métodos. O manifest regista a configuração efetiva, versões, timestamp, commit e hashes. Depois das seeds `42–46`, mudanças metodológicas exigem um novo protocolo; apenas bugs confirmados podem justificar correções desta versão.
