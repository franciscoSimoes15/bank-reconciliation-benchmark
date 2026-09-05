# Bank Reconciliation Ranking Benchmark

Benchmark Python sintético e reproduzível para comparar métodos transparentes de ranking 1:1 em reconciliação bancária. O candidato verdadeiro está sempre presente; o projeto não usa dados bancários reais, ML, embeddings, LLMs nem pesos aprendidos.

## Fluxo

```text
FinancialEvent latente
├── render_bank_transaction()
└── render_accounting_record()
          ↓
ledger contabilístico independente
          ↓
1 true + 6 natural negatives + 3 controlled hard negatives
          ↓
mesmo candidate set em 8 cenários emparelhados
          ↓
matching apenas com BankTransaction + AccountingRecord
          ↓
Unique Top-1 / MRR com average rank / Tie Rate
```

`BankTransaction` e `AccountingRecord` são renderizações independentes do mesmo acontecimento. Nenhuma é copiada ou derivada da outra. Os seus templates começam de forma diferente e as descrições não repetem sistematicamente referência ou entidade.

O gerador inclui pelo menos estes tipos de operação:

- supplier transfer;
- customer receipt;
- direct debit;
- card payment;
- bank fee;
- tax payment.

Referência e entidade são opcionais conforme o tipo; não são preenchidas artificialmente em todos os eventos.

## Métodos

Os nomes usados pelo código são membros de `MatchingMethod` (`StrEnum`). M0–M4 são apenas códigos de output.

| Código | Nome | Amount / date | Campos textuais |
|---|---|---|---|
| M0 | `normalized_exact` | igualdade | igualdade após normalização |
| M1 | `tolerant_deterministic` | regras binárias de ±0,10 € / ±3 dias | igualdade após normalização |
| M2 | `jaro_winkler_text` | proximidade gradual | Jaro-Winkler |
| M3 | `character_trigram_text` | proximidade gradual | cosine sobre character trigrams |
| M4 | `field_aware` | proximidade gradual | referência estruturada, Jaro-Winkler para entidade e trigrams para descrição |
| M4-D | `field_aware_without_description` | igual a M4 | ablation sem descrição |

Os scores são compatibilidades em `[0,1]`, não probabilidades. A agregação é uma média simples dos campos disponíveis, sem pesos aprendidos.

## Instalação

Requer Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install "setuptools>=75" wheel
python -m pip install -e . --no-build-isolation
```

## Testes

```powershell
python -m pytest
```

Os testes cobrem renderização independente, determinismo, perturbações sem no-op, emparelhamento, composição 1+6+3, IDs opacos, missing, scores, métricas, anti-leakage e outputs ponta a ponta.

## Desenvolvimento

Gerar e validar uma amostra:

```powershell
python -m recon_benchmark.cli generate --seed 7 --cases-per-scenario 3 --output benchmarks/seed_7.jsonl
python -m recon_benchmark.cli validate --input benchmarks/seed_7.jsonl --cases-per-scenario 3
```

Executar a seed de desenvolvimento:

```powershell
python -m recon_benchmark.cli evaluate --seed 7 --cases-per-scenario 3 --methods all --output-root development_run
```

Criar uma explicação de um caso:

```powershell
python -m recon_benchmark.cli demo --scenario combined_variation --method field_aware
```

Também é possível executar `python start_here.py`.

## Execução final congelada

```powershell
python -m recon_benchmark.cli run-final
```

`run-final` não aceita overrides de seeds, tamanho ou métodos. Usa a configuração registada em `config/experiment.json`:

- development seed: 7;
- evaluation seeds: 42, 43, 44, 45, 46;
- 100 eventos por cenário;
- 8 cenários emparelhados;
- 10 candidatos por caso.

Os outputs mínimos são:

```text
results/
  benchmark.jsonl
  per_case.csv
  by_scenario.csv
  summary.csv
  report.md
  experiment_manifest.json
```

São ainda escritos `benchmarks/seed_<n>.jsonl`, `manifest.json` como alias compatível e `figures/robustness_by_scenario.png`. O manifest inclui configuração, execução efetiva, versões, timestamp, commit disponível e hashes SHA-256.

## Cenários emparelhados

| Código | `Scenario` | Alteração experimental adicional |
|---|---|---|
| P0 | `natural_variation` | nenhuma; conserva apenas as diferenças naturais dos renderers |
| P1 | `amount_variation` | variação absoluta ou proporcional |
| P2 | `date_variation` | deslocamento curto, médio ou longo |
| P3 | `reference_variation` | formato, transposição, substituição ou referência bancária adicional |
| P4 | `entity_variation` | truncation, typo, casing/acento ou label bancária |
| P5 | `description_variation` | reorder, remoção, truncation, boilerplate ou abreviação |
| P6 | `missing_information` | remoção de reference ou counterparty disponível |
| P7 | `combined_variation` | três famílias distintas |

Cada alteração declarada é verificada contra o movimento bancário natural; uma perturbação no-op lança erro.

## Candidatos

Cada evento usa exatamente o mesmo candidate set e a mesma ordem nos oito cenários:

- 1 candidato verdadeiro;
- 6 natural negatives: registos contabilísticos completos, renderizados de outros `FinancialEvent` do ledger;
- 3 controlled hard negatives: conflitos controlados em amount/date/reference, entity/documento e múltiplas evidências.

Todos os IDs dos candidatos têm o mesmo formato opaco. A ordem é baralhada de forma determinística. Os hard negatives não consultam a perturbação nem o movimento observado, evitando candidate leakage entre cenários.

## Missing e proteção contra leakage

Um campo ausente é excluído da média. O gerador preserva o mesmo padrão de disponibilidade entre os dez candidatos e a avaliação rejeita rankings com números de campos comparados diferentes.

`score_pair()` aceita apenas:

```text
BankTransaction + AccountingRecord + MatchingMethod + ExperimentConfig
```

`event_id`, `true_candidate_id`, cenário, perturbações e origem do candidato permanecem fora dessa fronteira e só são usados pelo gerador/avaliador.

## Estrutura

### Guias por componente

Os guias seguintes, em inglês, explicam os conceitos e a implementação atual,
com exemplos, ligações ao código e aos testes. Para acompanhar um caso desde a
origem, seguir domínio, geração, normalização, ranking e métricas.

| Guia | O que explica |
|---|---|
| [Domain](src/recon_benchmark/domain/README.md) | Eventos, representações, candidatos, casos e fronteiras de dados |
| [Generation](src/recon_benchmark/generation/README.md) | Tipos de operação, renderers, ledger e montagem dos casos |
| [Templates](src/recon_benchmark/templates/README.md) | Convenções bancárias e contabilísticas independentes |
| [Scenarios](src/recon_benchmark/generation/README_SCENARIOS.md) | Os oito cenários e o emparelhamento dos casos |
| [Perturbations](src/recon_benchmark/generation/README_PERTURBATIONS.md) | Alterações disponíveis, tags, missing e proteção contra no-op |
| [Negatives](src/recon_benchmark/generation/README_NEGATIVES.md) | Composição 1+6+3 e construção de candidatos difíceis |
| [Normalization](src/recon_benchmark/normalization/README.md) | Regras por campo e exemplos antes/depois |
| [Ranking](src/recon_benchmark/ranking/README.md) | Métodos, semelhança textual, proximidade gradual e scores |
| [Metrics](src/recon_benchmark/metrics/README.md) | Unique Top-1, MRR, empates, agregação e outputs |
| [Experiment](src/recon_benchmark/experiment/README.md) | Configuração, seeds, parâmetros efetivos e pipeline |
| [Storage](src/recon_benchmark/storage/README.md) | JSONL, serialização e inspeção legível |
| [CLI](src/recon_benchmark/cli/README.md) | Comandos, argumentos e exemplos práticos |

### Ficheiros

```text
src/recon_benchmark/
  __main__.py                 entrada para python -m recon_benchmark
  domain/
    models.py                 dataclasses imutáveis e StrEnum
    validation.py             validação dos campos usados por from_dict
    codes.py                  códigos de métodos e cenários para os outputs
  experiment/
    models.py                 classe ExperimentConfig e respetivas invariantes
    config.py                 leitura e conversão da configuração JSON
    pipeline.py               coordenação da experiência completa
  storage/
    serialization.py          leitura e escrita de JSONL
  cli/
    __main__.py               entrada para python -m recon_benchmark.cli
    main.py                   argumentos e encaminhamento dos comandos
    explanation.py            explicações de casos para demo/explain
  generation/
    models.py                 classes LedgerEntry e CandidateIdentity
    errors.py                 exceção de perturbação no-op
    synthetic_data.py         FinancialEvent e renderers independentes
    negatives.py              natural e controlled hard negatives
    perturbations.py          alterações experimentais com guardas no-op
    generator.py              montagem e validação dos casos emparelhados
  templates/
    bank.py                   descrições e formatos de referência bancários
    accounting.py             descrições e formatos contabilísticos
  normalization/
    fields.py                 normalização por campo
  ranking/
    models.py                 classes de scores e componentes de referência
    similarity.py             Jaro-Winkler e character n-grams
    matchers.py               scores transparentes M0–M4
    ordering.py               ordenação dos candidatos por score
  metrics/
    models.py                 classes CaseEvaluation e AggregateMetrics
    evaluation.py             ground truth, average rank e métricas
    reporting.py              CSV, agregação entre seeds, relatório e manifest
```

Todas as pastas do pacote contêm `__init__.py`. Os comandos `recon-benchmark`,
`python -m recon_benchmark` e `python -m recon_benchmark.cli` usam a mesma CLI.
Os imports Python seguem agora os subpacotes, por exemplo
`from recon_benchmark.generation.generator import generate_benchmark`.

Para estudar o código, começar em `domain/models.py` e seguir `generation/`,
`templates/`, `normalization/`, `ranking/` e `metrics/`. O pipeline coordena
essas etapas; a CLI interpreta os comandos e chama as operações correspondentes.

As classes de dados ficam nos ficheiros `models.py` de cada área; as funções de
processamento ficam nos restantes módulos. Métodos próprios dos objetos, como
`validate()`, `to_dict()` e `from_dict()`, permanecem nas respetivas classes.
Por exemplo, `ranking/models.py` define `ScoreBreakdown`, enquanto
`ranking/matchers.py` contém a função `score_pair()` que calcula esse resultado.

Cada classe, método e função tem uma docstring em inglês que explica o seu papel.
As operações principais documentam também entradas/saídas relevantes, efeitos de
I/O e regras como missing, empates ou proteção do ground truth. As funções de
teste descrevem o comportamento que verificam. Estas descrições aparecem no
editor ao consultar um símbolo e podem ser lidas com `help()` no Python.

## Limites

O benchmark não cobre 1:N, N:1, N:N, ausência do candidato verdadeiro, fees/FX/partial payments como relações complexas, integração ERP ou calibração de auto-reconciliação. Resultados sintéticos não demonstram desempenho em produção.
