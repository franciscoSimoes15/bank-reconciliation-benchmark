# Fundamentação metodológica

## 1. De onde vêm as ideias

O projeto separa três origens:

| Origem | Função |
|---|---|
| Estudo dos 15 motores comerciais | Identificar sinais, tolerâncias, ruído, ambiguidade e workflows relevantes. |
| Literatura científica | Escolher famílias de comparadores e métricas públicas. |
| Decisão de projeto | Definir tamanho, seeds, perturbações, thresholds e hard negatives. |

Os produtos comerciais não são usados como baselines de performance. Muitos descrevem capacidades funcionais sem revelar fórmula, pesos ou algoritmo interno.

## 2. Record linkage

O enquadramento base vem de **Fellegi e Sunter**, que formalizaram record linkage como comparação de pares de registos através de evidências por atributo e uma regra de decisão.

Referência:

- Fellegi, I. P., & Sunter, A. B. (1969). *A Theory for Record Linkage*. Journal of the American Statistical Association, 64(328), 1183–1210. DOI: `10.1080/01621459.1969.10501049`.

No projeto, cada par produz um vetor:

```text
amount_score
date_score
reference_score
entity_score
description_score
```

## 3. Jaro-Winkler

Jaro-Winkler é uma família clássica de comparadores usada em record linkage, especialmente adequada a nomes e strings curtas com typos ou transposições.

O projeto usa a implementação mantida do `RapidFuzz`, evitando reimplementar uma fórmula sensível a erros.

Referências de contexto:

- U.S. Census Bureau, *An Adaptive String Comparator for Record Linkage*.
- U.S. Census Bureau, *Evaluating String Comparator Performance for Record Linkage*.
- Cohen, W. W., Ravikumar, P., & Fienberg, S. E. (2003). *A Comparison of String Distance Metrics for Name-Matching Tasks*.

## 4. Character q-grams

Ukkonen formalizou approximate string matching com q-grams: uma string é representada através de fragmentos locais de comprimento `q`.

Este projeto usa `q=3`, boundary markers e cosine similarity sobre contagens.

Referência:

- Ukkonen, E. (1992). *Approximate string-matching with q-grams and maximal matches*. Theoretical Computer Science, 92(1), 191–211. DOI: `10.1016/0304-3975(92)90143-4`.

## 5. Comparação de métricas

Cohen, Ravikumar e Fienberg compararam várias métricas para matching de nomes e registos. Essa literatura sustenta a decisão de não presumir que uma única métrica textual seja ideal para todos os campos.

Por isso o projeto compara:

- Jaro-Winkler aplicado uniformemente;
- q-gram aplicado uniformemente;
- uma combinação field-aware.

## 6. Métricas de ranking

MRR é usado quando interessa a posição do primeiro resultado correto. Como existe exatamente um verdadeiro, a posição usa o average rank quando há empate:

```text
RR = 1 / posição do candidato correto
MRR = média dos RR
```

A definição segue a tradição TREC/NIST. O projeto acrescenta **Unique Top-1**, porque em reconciliação financeira um empate no topo não representa uma decisão automática inequívoca.

## 7. Domínio de reconciliação bancária

Trabalho recente formula reconciliação bancária como problema de representação, record linkage e link prediction:

- Munoz, J., Jalili, M., & Tafakori, L. (2025). *Enhancing Bookkeeper Decision Support Through Graph Representation Learning for Bank Reconciliation*. The Journal of Finance and Data Science, 100170. DOI: `10.1016/j.jfds.2025.100170`.

O nosso benchmark é deliberadamente mais pequeno e transparente: não treina modelos e limita-se a matching 1:1.

## 8. O que é uma decisão específica deste projeto

Não vem diretamente de um paper:

- 8 cenários;
- 100 casos por cenário;
- 5 evaluation seeds;
- 10 candidatos por caso;
- ±0,10 €;
- ±3 dias;
- 6 natural negatives de outros eventos e 3 controlled hard negatives;
- média simples dos campos disponíveis, com disponibilidade igual dentro do caso;
- entity/legal suffix list limitada a `LDA` e `SA`.

Estas decisões são parâmetros do protocolo, congelados antes de observar os resultados finais. Não são apresentadas como valores universais para reconciliação bancária.

## 9. Separação entre geração e matching

O `FinancialEvent` latente gera independentemente uma vista bancária e uma vista contabilística. O matcher nunca recebe esse evento, o ground truth, o cenário, as perturbações ou a origem do candidato. Assim, os resultados medem apenas a compatibilidade entre campos observáveis.

Os mesmos eventos e candidate sets são reutilizados nos oito cenários. A comparação entre cenários é, por isso, emparelhada e não mistura amostras diferentes.

## 10. Proximidade e missing

M2–M4 usam proximidade gradual para amount/date, ao contrário da regra binária tolerante de M1. M4 trata a referência como estrutura prefixo/ano/número quando possível e usa Jaro-Winkler apenas como fallback.

Missing exclui o campo da agregação, não acrescenta um desacordo. O benchmark preserva a disponibilidade entre candidatos e valida explicitamente o número de campos comparados.
