# Referências metodológicas e técnicas

## Record linkage

1. Fellegi, I. P., & Sunter, A. B. (1969). *A Theory for Record Linkage*. Journal of the American Statistical Association, 64(328), 1183–1210.  
   https://doi.org/10.1080/01621459.1969.10501049

2. U.S. Census Bureau — Record Linkage & Machine Learning.  
   https://www.census.gov/topics/research/stat-research/expertise/record-linkage.html

## Jaro-Winkler e comparação de strings

3. U.S. Census Bureau — *An Adaptive String Comparator for Record Linkage*.  
   https://www.census.gov/library/working-papers/2004/adrm/rrs2004-02.html

4. U.S. Census Bureau — *Evaluating String Comparator Performance for Record Linkage*.  
   https://www.census.gov/library/working-papers/2005/adrm/rrs2005-05.html

5. Cohen, W. W., Ravikumar, P., & Fienberg, S. E. (2003). *A Comparison of String Distance Metrics for Name-Matching Tasks*.  
   https://wwcohen.github.io/postscript/ijcai-ws-2003.pdf

## Q-grams

6. Ukkonen, E. (1992). *Approximate string-matching with q-grams and maximal matches*. Theoretical Computer Science, 92(1), 191–211.  
   https://doi.org/10.1016/0304-3975(92)90143-4

## Ranking e MRR

7. NIST/TREC — Mean Reciprocal Rank: o score individual é o inverso da posição da primeira resposta correta e o score do run é a média.  
   https://trec.nist.gov/pubs/trec11/appendices/MEASURES.pdf

## Reconciliação bancária como linkage/prediction

8. Munoz, J., Jalili, M., & Tafakori, L. (2025). *Enhancing Bookkeeper Decision Support Through Graph Representation Learning for Bank Reconciliation*. The Journal of Finance and Data Science, 100170.  
   https://doi.org/10.1016/j.jfds.2025.100170

## Implementação utilizada

9. RapidFuzz — JaroWinkler documentation. O projeto fixa `rapidfuzz==3.14.3`.  
   https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html

## Evidência industrial

O detalhe completo das fontes e validações dos 15 motores comerciais pertence ao **Documento A — Estudo dos motores**. Neste projeto, essa evidência serve para motivar campos, cenários de ruído, tolerâncias, ambiguidade e separação entre matching e decisão; não serve para comparar performance de produtos.
