# Bank Reconciliation Pattern-Matching Benchmark

Projeto Python executável de ponta a ponta para estudar **reconciliação bancária 1:1 como problema de reconhecimento de padrões e ranking de candidatos**.

O projeto não usa dados bancários reais. Gera pares sintéticos com ground truth conhecido, introduz ruído controlado, cria candidatos falsos difíceis, executa cinco estratégias de matching e produz métricas, tabelas, um relatório e uma figura.

## O que este projeto permite perceber

```text
Registo contabilístico canónico
        ↓
Movimento bancário derivado
        ↓
Perturbação controlada
        ↓
1 candidato correto + 9 hard negatives
        ↓
Normalização por campo
        ↓
M0 / M1 / M2 / M3 / M4
        ↓
Ranking dos 10 candidatos
        ↓
Unique Top-1 / MRR / Tie Rate
```

A demonstração `demo` mostra este fluxo campo a campo, incluindo os scores de cada candidato.

## Relação com o Excel fornecido

O ficheiro de exemplo foi usado **apenas para observar formas estruturais comuns em descrições bancárias portuguesas**, como abreviações de transferências, compras com cartão, débitos diretos, comissões, imposto do selo, identificadores embebidos, truncation e diferenças entre data e data-valor.

Não foi usado para:

- gerar ground truth;
- treinar qualquer modelo;
- copiar nomes, montantes, referências ou movimentos;
- avaliar os algoritmos;
- integrar dados reais no repositório.

Os templates do gerador usam apenas entidades e referências fictícias. Ver [`docs/EXAMPLE_SPREADSHEET_OBSERVATIONS.md`](docs/EXAMPLE_SPREADSHEET_OBSERVATIONS.md).

## Métodos implementados

| Método | Amount / Date | Reference | Entity | Description |
|---|---|---|---|---|
| **M0 Normalized Exact** | igualdade exata | exato | exato | exato |
| **M1 Tolerant Deterministic** | ±0,10 € / ±3 dias | exato | exato | exato |
| **M2 Jaro-Winkler** | tolerante | Jaro-Winkler | Jaro-Winkler | Jaro-Winkler |
| **M3 Character 3-gram** | tolerante | 3-gram cosine | 3-gram cosine | 3-gram cosine |
| **M4 Field-Aware Hybrid** | tolerante | Jaro-Winkler | Jaro-Winkler | 3-gram cosine |
| **M4-noNorm** | igual ao M4 | raw | raw | raw |

Todos os campos disponíveis têm peso igual. Um campo ausente é excluído do numerador e do denominador; não é tratado automaticamente como desacordo.

## Requisitos

- Python 3.11+
- `pip`

## Instalação

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-lock.txt
pip install -e .
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-lock.txt
pip install -e .
```

### Instalação sem build isolation (ambientes restritos)

Se o ambiente já tiver `setuptools` instalado mas bloquear downloads durante o build:

```bash
pip install -e . --no-build-isolation
```

## 1. Executar testes

```bash
pytest
```

## 2. Ver o fluxo completo num único caso

```bash
python start_here.py
```

Equivalente com o CLI instalado:

```bash
python -m recon_benchmark.cli demo
```

Outputs:

- `examples/demo_benchmark.jsonl`
- `examples/demo_success.md`
- `examples/demo_challenging.md`

Abrir os dois relatórios para comparar um caso resolvido com um caso difícil em que o método falha. Ambos mostram:

- movimento bancário raw e normalizado;
- perturbações aplicadas;
- os 10 candidatos;
- score por campo;
- ranking final;
- candidato correto, usado apenas na avaliação.

Também existem scripts diretos:

```bash
./scripts/run_demo.sh
```

ou, em Windows:

```bat
scripts\run_demo.bat
```

## 3. Smoke run de desenvolvimento

```bash
python -m recon_benchmark.cli evaluate \
  --seed 7 \
  --cases-per-scenario 3 \
  --methods all \
  --output-root development_run
```

Isto executa 24 casos: 8 cenários × 3 casos.

## 4. Gerar e validar um benchmark

```bash
python -m recon_benchmark.cli generate \
  --seed 7 \
  --cases-per-scenario 3 \
  --output benchmarks/seed_7.jsonl

python -m recon_benchmark.cli validate \
  --input benchmarks/seed_7.jsonl \
  --cases-per-scenario 3
```

## 5. Executar o protocolo final

```bash
python -m recon_benchmark.cli run-final
```

A configuração congelada usa:

- seeds `42, 43, 44, 45, 46`;
- 100 casos por cenário;
- 8 cenários;
- 4 000 casos no total;
- 10 candidatos por caso;
- 6 variantes de método, incluindo a ablation.

Outputs:

```text
benchmarks/seed_42.jsonl
...
benchmarks/seed_46.jsonl
results/per_case.csv
results/by_scenario.csv
results/summary.csv
results/manifest.json
results/report.md
figures/robustness_by_scenario.png
```

## 6. Explicar um caso de um benchmark existente

```bash
python -m recon_benchmark.cli explain \
  --input benchmarks/seed_42.jsonl \
  --case-index 0 \
  --method M4 \
  --output examples/case_explanation.md
```

## Cenários

| Cenário | Alteração aplicada ao movimento bancário |
|---|---|
| `P0_CLEAN` | nenhuma |
| `P1_AMOUNT_NOISE` | ±0,01 €, ±0,05 € ou ±0,10 € |
| `P2_DATE_DRIFT` | ±1, ±2 ou ±3 dias |
| `P3_REFERENCE_NOISE` | separadores, compactação, transposição ou substituição de dígitos |
| `P4_ENTITY_NOISE` | sufixo, truncation, typo ou casing/acento |
| `P5_DESCRIPTION_NOISE` | reorder, remoção de token, truncation, boilerplate ou abreviação |
| `P6_MISSING_INFORMATION` | 50% sem reference; 50% sem counterparty |
| `P7_COMBINED` | três famílias distintas de ruído |

A perturbação é aplicada apenas ao lado bancário. O registo contabilístico correto permanece canónico.

## Hard negatives

Cada caso contém um candidato correto e nove candidatos incorretos mas plausíveis. Os negativos preservam evidências como:

- mesmo montante;
- mesma data;
- referência próxima;
- mesma entidade;
- montante + data próxima;
- montante + entidade;
- montante + data + referência próxima;
- descrição semelhante + entidade;
- montante + data + entidade, mas referência errada e próxima.

O N9 é ajustado ao cenário e preserva, quando aplicável, valores do movimento bancário observado. Esta decisão evita que o baseline exato permaneça artificialmente dominante depois de uma perturbação. O racional está documentado em [`docs/IMPLEMENTATION_DECISIONS.md`](docs/IMPLEMENTATION_DECISIONS.md).

Assim o benchmark mede ambiguidade realista e não apenas a capacidade de separar pares totalmente diferentes.

## Métricas

**Unique Top-1 Accuracy:** só conta como correto quando o true candidate tem o maior score sem empate.

**MRR:** mede quão perto do topo ficou o candidato correto, usando average rank em empates.

**Tie Rate:** percentagem de casos em que existem vários candidatos com o score máximo.

## Estrutura do código

```text
src/recon_benchmark/
  models.py            modelos imutáveis
  config.py            protocolo e configuração
  synthetic_data.py    entidades, referências e descrições fictícias
  perturbations.py     ruído controlado
  negatives.py         nove hard negatives
  normalization.py     preparação por campo
  similarity.py        Jaro-Winkler e q-gram cosine
  matchers.py          M0-M4 e ablation
  evaluation.py        ranking e métricas
  reporting.py         CSV, manifest, relatório e figura
  explanation.py       walkthrough de um caso
  pipeline.py          execução ponta a ponta
  cli.py               interface de linha de comandos
```

## Guardrails científicos

- O matcher não recebe `true_candidate_id`, `scenario` nem `perturbations`.
- Todos os métodos recebem os mesmos casos e candidatos.
- Os candidatos são baralhados deterministicamente.
- Não existem pesos aprendidos ou arbitrários.
- A seed de desenvolvimento é separada das cinco seeds finais.
- A configuração final fica registada em `manifest.json`.
- Resultados sintéticos não permitem afirmar desempenho em produção.

## Leitura recomendada

1. [`docs/FLOW_WALKTHROUGH.md`](docs/FLOW_WALKTHROUGH.md)
2. [`docs/METHODOLOGY.md`](docs/METHODOLOGY.md)
3. [`docs/IMPLEMENTATION_DECISIONS.md`](docs/IMPLEMENTATION_DECISIONS.md)
4. [`docs/REFERENCES.md`](docs/REFERENCES.md)
5. `src/recon_benchmark/generator.py`
6. `src/recon_benchmark/matchers.py`
7. `src/recon_benchmark/evaluation.py`

