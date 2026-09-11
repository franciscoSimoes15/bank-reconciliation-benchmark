# Methodological and technical references

## Record linkage

1. Fellegi, I. P., & Sunter, A. B. (1969). *A Theory for Record Linkage*. Journal of the American Statistical Association, 64(328), 1183–1210.  
   https://doi.org/10.1080/01621459.1969.10501049

2. U.S. Census Bureau — Record Linkage & Machine Learning.  
   https://www.census.gov/topics/research/stat-research/expertise/record-linkage.html

## Jaro-Winkler and string comparison

3. U.S. Census Bureau — *An Adaptive String Comparator for Record Linkage*.  
   https://www.census.gov/library/working-papers/2004/adrm/rrs2004-02.html

4. U.S. Census Bureau — *Evaluating String Comparator Performance for Record Linkage*.  
   https://www.census.gov/library/working-papers/2005/adrm/rrs2005-05.html

5. Cohen, W. W., Ravikumar, P., & Fienberg, S. E. (2003). *A Comparison of String Distance Metrics for Name-Matching Tasks*.  
   https://wwcohen.github.io/postscript/ijcai-ws-2003.pdf

## Q-grams

6. Ukkonen, E. (1992). *Approximate string-matching with q-grams and maximal matches*. Theoretical Computer Science, 92(1), 191–211.  
   https://doi.org/10.1016/0304-3975(92)90143-4

## Ranking and MRR

7. NIST/TREC — Mean Reciprocal Rank: the individual score is the reciprocal of the first correct answer's position, and the run score is the mean.
   https://trec.nist.gov/pubs/trec11/appendices/MEASURES.pdf

## Bank reconciliation as linkage/prediction

8. Munoz, J., Jalili, M., & Tafakori, L. (2025). *Enhancing Bookkeeper Decision Support Through Graph Representation Learning for Bank Reconciliation*. The Journal of Finance and Data Science, 100170.  
   https://doi.org/10.1016/j.jfds.2025.100170

## Implementation used

9. RapidFuzz — JaroWinkler documentation. The project pins `rapidfuzz==3.14.3`.
   https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html

## Industry evidence

Earlier project notes refer to **Document A — Engine Study**, a separate survey
of 15 commercial engines. That document is not included in this repository.
Its contents are external background, not public reproducibility or validation
evidence. No commercial product performance is measured by this benchmark.
