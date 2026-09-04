# Observações estruturais retiradas do Excel de exemplo

## Regra de utilização

O ficheiro fornecido pelo utilizador **não é um dataset do benchmark**. Foi lido apenas para perceber que formas de descrição e de estrutura bancária poderiam ser representadas sinteticamente.

O projeto não inclui o Excel e não copia:

- nomes de pessoas ou empresas;
- montantes;
- saldos;
- datas concretas;
- referências concretas;
- linhas completas.

## Padrões estruturais observados

O exemplo contém a estrutura típica de um extrato:

```text
Data de lançamento
Data valor
Descritivo
Débito
Crédito
Saldo
```

As descrições mostram famílias funcionais comuns:

- transferências de saída com prefixos abreviados;
- transferências de entrada;
- compras com cartão/terminal e identificadores numéricos;
- débitos diretos;
- pagamentos de empréstimos;
- comissões de conta ou transferência;
- imposto do selo associado a comissões;
- pagamentos a entidades públicas.

Também aparecem características relevantes para reconhecimento de padrões:

- descrições em maiúsculas e minúsculas;
- acentos e pontuação inconsistentes;
- abreviações bancárias;
- identificadores numéricos embebidos;
- nomes longos ou truncados;
- data de lançamento diferente da data-valor;
- débitos e créditos em colunas diferentes.

## Como estas observações entram no gerador

O projeto cria templates **genéricos e fictícios**, por exemplo:

```text
TRF P/ <ENTIDADE_FICTICIA> REF <REFERENCIA_FICTICIA>
TRF DE <ENTIDADE_FICTICIA> REF <REFERENCIA_FICTICIA>
MDB<IDENTIFICADOR_FICTICIO> <ENTIDADE_FICTICIA> REF <REFERENCIA_FICTICIA>
DD <ENTIDADE_FICTICIA> MANDATO <REFERENCIA_FICTICIA>
COM.MAN.CONTA PACOTE EMPRESA <PERIODO> REF <REFERENCIA_FICTICIA>
IMP. SELO COM. TRANSFERENCIA REF <REFERENCIA_FICTICIA>
PAGAMENTO EMPRESTIMO N. <IDENTIFICADOR_FICTICIO>
```

O montante é convertido para um único campo assinado:

- entrada/crédito → positivo;
- saída/débito → negativo.

O benchmark principal usa apenas `date`, não `value_date`, para manter o scope pequeno. A diferença entre essas datas fica documentada como possibilidade de future work.
