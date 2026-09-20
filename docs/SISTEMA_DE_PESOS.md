# Sistema de pesos do Copiloto de Retenção

## 1. Objetivo deste documento

Este documento explica, de ponta a ponta, como o Copiloto de Retenção transforma os dados da planilha em um índice de risco de `0` a `100` e como define a importância de cada fator nesse índice.

Há três conceitos diferentes que não devem ser confundidos:

1. **Score do sinal:** intensidade de uma evidência de risco para um cliente, de `0` a `100`.
2. **Peso:** participação de um sinal ou fator na composição de um score. Peso não é risco e não é probabilidade.
3. **Score final de risco:** média ponderada dos fatores disponíveis para um cliente, de `0` a `100`.

O score final é um **índice de severidade para priorização**. Um resultado de `60/100` não significa “60% de probabilidade de cancelamento”. O modelo atual não foi calibrado para produzir probabilidades.

## 2. Visão geral

O cálculo acontece em cinco etapas:

```text
colunas da planilha
        ↓
sinais de risco de 0 a 100
        ↓
scores dos fatores de 0 a 100
        ↓
pesos recomendados pela comparação histórica
        ↓
score final do cliente de 0 a 100
```

Os sinais são agrupados em seis fatores: Adoção, Operação, Suporte, Satisfação, Engajamento de CS e Financeiro. Dentro de um fator pode haver mais de um sinal. Por isso, o sistema possui dois níveis de ponderação:

- **pesos internos**, que combinam os sinais de um mesmo fator;
- **pesos dos fatores**, que combinam os seis fatores no score final.

## 3. De onde vêm os dados

A demonstração usa o arquivo `data/INOVAAPPS_base_de_dados.xlsx`, composto por quatro abas:

| Aba | Uso no modelo |
|---|---|
| `clientes` | Identificação, segmento, plano e valor mensal dos clientes. |
| `atendimento_mensal` | Uso da plataforma, SLA, tempo de resolução, chamados, reclamações, reuniões e atraso de pagamento. |
| `pesquisas_nps` | Resposta, nota e classificação de NPS. |
| `situacao_clientes` | Separação histórica entre clientes ativos e cancelados. |

A base contém **80 clientes**: **58 ativos** e **22 cancelados**. O histórico mensal vai de **janeiro de 2025 a junho de 2026**.

Para os indicadores mensais, cada cálculo considera duas janelas:

- **janela recente:** os três meses mais recentes disponíveis para o cliente;
- **janela anterior:** os três meses imediatamente anteriores.

A comparação entre janelas permite distinguir uma deterioração recente de um nível que já era baixo. Três meses foram usados para reduzir a influência de um único mês atípico sem apagar a mudança recente. Essa janela é uma decisão de projeto da demonstração, não um parâmetro aprendido automaticamente.

## 4. Como cada coluna vira um sinal de risco

Todos os sinais seguem a mesma direção: quanto maior o valor, maior a intensidade do risco. Os resultados são limitados ao intervalo de `0` a `100`.

Nas fórmulas abaixo, `limitar(x)` significa:

```text
0, se x < 0
x, se 0 ≤ x ≤ 100
100, se x > 100
```

### 4.1 Adoção

O fator Adoção usa dois sinais.

**Queda de uso — peso interno de 60%**

```text
queda_de_uso = média_uso_anterior − média_uso_recente
score_queda = limitar(máximo(queda_de_uso, 0) ÷ 20 × 100)
```

Uma queda de 20 pontos percentuais ou mais recebe score `100`. Se o uso ficou estável ou aumentou, esse sinal recebe `0`.

**Nível de utilização — peso interno de 40%**

```text
score_nível = limitar(máximo(70 − média_uso_recente, 0) ÷ 40 × 100)
```

Uso recente igual ou superior a 70% recebe `0`. Quanto mais o uso fica abaixo dessa referência, maior o risco; uma distância de 40 pontos ou mais recebe `100`.

```text
score_adoção = score_queda × 0,60 + score_nível × 0,40
```

O peso maior para a tendência evita que o modelo trate da mesma forma um cliente que sempre usou pouco e outro que acabou de reduzir fortemente o uso. Os valores de referência `20`, `70` e `40` são limiares heurísticos da demonstração e devem ser calibrados em produção.

### 4.2 Operação

O fator Operação combina três sinais.

**Deterioração do SLA — peso interno de 45%**

```text
queda_de_SLA = média_SLA_anterior − média_SLA_recente
score_tendência_SLA = limitar(máximo(queda_de_SLA, 0) ÷ 25 × 100)
```

**Nível atual do SLA — peso interno de 30%**

```text
score_nível_SLA = limitar(máximo(85 − média_SLA_recente, 0) ÷ 35 × 100)
```

**Aumento do tempo de resolução — peso interno de 25%**

```text
aumento_resolução = média_horas_recente − média_horas_anterior
score_resolução = limitar(máximo(aumento_resolução, 0) ÷ 15 × 100)
```

```text
score_operação =
    score_tendência_SLA × 0,45
  + score_nível_SLA × 0,30
  + score_resolução × 0,25
```

A tendência do SLA recebe a maior participação porque uma piora recente é um sinal antecipado. O nível atual preserva o contexto absoluto, e o tempo de resolução cobre uma dimensão operacional diferente do cumprimento do SLA. Os limiares são heurísticos da demonstração.

### 4.3 Suporte

O fator Suporte tem um único sinal, portanto seu peso interno é 100%.

```text
score_suporte = limitar(
    média_chamados_críticos ÷ 3 × 35
  + média_chamados_reabertos ÷ 3 × 35
  + média_reclamações_formais ÷ 2 × 30
)
```

Chamados críticos e reaberturas recebem 35 pontos máximos cada; reclamações formais recebem 30. A soma chega a `100`. A divisão por `3`, `3` e `2` define o volume médio que satura cada parcela na demonstração. Essa distribuição representa a hipótese de que gravidade e reincidência são ligeiramente mais informativas que a reclamação isolada; ela não foi aprendida estatisticamente.

### 4.4 Satisfação

O fator Satisfação usa as duas pesquisas de NPS mais recentes do cliente. Há um único sinal, com peso interno de 100%.

| Condição | Score de risco |
|---|---:|
| Não respondeu aos dois últimos ciclos | 85 |
| Não respondeu ao ciclo mais recente, mas respondeu ao anterior | 68 |
| Última resposta foi “Detrator” | 80 |
| Última resposta foi “Neutro” | 35 |
| Última resposta foi “Promotor” | 5 |
| Classificação diferente das previstas | 50 |
| Nenhuma pesquisa disponível | dado ausente |

O silêncio recebe risco porque a ausência recorrente de resposta pode indicar afastamento. Ele não é tratado como prova de insatisfação: trata-se de uma regra heurística e transparente, que deve ser validada com resultados reais.

### 4.5 Engajamento de CS

O fator Engajamento de CS tem um único sinal, com peso interno de 100%.

```text
score_CS = limitar(
    (1 − soma_reuniões_realizadas ÷ soma_reuniões_previstas) × 100
)
```

Se todas as reuniões previstas ocorreram, o score é `0`. Se nenhuma ocorreu, o score é `100`. Quando não há reunião prevista, o sinal é considerado ausente, pois não existe uma base válida para calcular a taxa.

### 4.6 Financeiro

O fator Financeiro tem um único sinal, com peso interno de 100%.

```text
score_financeiro = limitar(média_dias_de_atraso ÷ 15 × 100)
```

Sem atraso, o score é `0`; atraso médio de 15 dias ou mais recebe `100`. O limite de 15 dias é uma regra heurística da demonstração.

## 5. De onde vêm os pesos recomendados dos fatores

Os pesos recomendados **não são escolhidos por IA generativa** e não são simplesmente os pesos iniciais do preset. Eles são calculados a partir da capacidade de cada fator de separar, nesta base, os clientes que permaneceram ativos dos que cancelaram.

O procedimento é o seguinte:

1. Para cada cliente, o sistema usa o último período mensal disponível.
2. Calcula os seis scores de fator usando as regras da seção anterior.
3. Separa os clientes pelo campo `situacao`: ativos de um lado e cancelados do outro.
4. Para cada fator, calcula a média do grupo ativo e a média do grupo cancelado.
5. Calcula a diferença entre os grupos.

```text
diferença_fator = média_cancelados − média_ativos
```

Uma diferença positiva significa que, em média, os cancelados apresentaram mais intensidade de risco naquele fator. Quanto maior a diferença, maior a força de separação observada.

6. Aplica um piso técnico de `1,0` ponto:

```text
força_fator = máximo(diferença_fator, 1,0)
```

O piso impede que um fator seja eliminado definitivamente por uma amostra pequena ou por uma diferença negativa. Na base atual todas as diferenças são superiores a `1,0`; portanto, o piso não altera nenhum dos seis pesos atuais.

7. Normaliza as forças para que a soma seja 100%:

```text
peso_recomendado_fator = força_fator ÷ soma_das_forças × 100
```

### 5.1 Resultado na base atual

| Fator | Média dos ativos | Média dos cancelados | Diferença | Peso recomendado |
|---|---:|---:|---:|---:|
| Adoção | 6,4 | 51,2 | 44,7 | 21,7% |
| Operação | 23,3 | 66,0 | 42,7 | 20,7% |
| Suporte | 20,5 | 54,9 | 34,5 | 16,7% |
| Satisfação | 43,7 | 78,0 | 34,3 | 16,7% |
| Engajamento de CS | 19,0 | 47,7 | 28,8 | 14,0% |
| Financeiro | 20,3 | 41,2 | 20,9 | 10,2% |

Os valores exibidos estão arredondados para uma casa decimal. O sistema calcula a normalização com os valores completos antes de arredondar a apresentação.

### 5.2 Exemplo completo: Adoção

Na base atual:

```text
média dos cancelados = 51,16818...
média dos ativos = 6,43621...
diferença_adoção = 51,16818... − 6,43621... = 44,73197... pontos
soma das forças dos seis fatores = 205,86724... pontos
peso_adoção = 44,73197... ÷ 205,86724... × 100 = 21,72855...%
peso exibido = 21,7%
```

Em linguagem direta: de cada 100 pontos de importância distribuídos entre os fatores, 21,7 são destinados à Adoção porque ela apresentou a maior distância média entre cancelados e ativos nesta amostra.

## 6. Por que foi escolhido esse método

O projeto precisava de um método compatível com três restrições da entrega:

- uma base pequena, com 80 clientes;
- necessidade de explicar cada número para o gestor;
- possibilidade de ajustar os pesos e recalcular a fila em tempo real.

A diferença de médias normalizada atende a essas restrições porque é simples de auditar: qualquer pessoa pode reconstruir a recomendação a partir dos scores dos dois grupos. Ela também preserva a decomposição fator por fator, necessária para explicar por que um cliente entrou na fila.

Esse método foi escolhido como **ponto de partida exploratório**, e não como substituto de um modelo estatístico validado. Ele mostra associação histórica na amostra; não demonstra causalidade e não estima probabilidade de churn.

## 7. Como os pesos geram o score final de um cliente

Depois de definidos os pesos dos fatores, o score final é calculado por média ponderada:

```text
score_final =
    score_adoção × peso_adoção
  + score_operação × peso_operação
  + score_suporte × peso_suporte
  + score_satisfação × peso_satisfação
  + score_CS × peso_CS
  + score_financeiro × peso_financeiro
```

Na fórmula, cada peso percentual é usado como fração. Exemplo: `21,7% = 0,217`.

Exemplo didático, com apenas três fatores disponíveis:

```text
Adoção:   score 80, peso 50%
Operação: score 40, peso 30%
Suporte:  score 20, peso 20%

score_final = 80 × 0,50 + 40 × 0,30 + 20 × 0,20
score_final = 40 + 12 + 4 = 56/100
```

O fator que mais contribui para o risco de um cliente é identificado por:

```text
contribuição_fator = score_fator × peso_fator
```

Assim, um fator de peso alto não será necessariamente o principal vetor de risco de todos os clientes: ele só terá grande contribuição quando seu score também estiver alto naquele cliente.

## 8. Ajuste manual dos pesos

No modo **Recomendado pela base**, o sistema usa os pesos da seção 5. No modo **Ajustado pelo gestor**, os controles representam importâncias relativas. O sistema sempre normaliza os valores positivos para que a soma efetivamente usada seja 100%.

Exemplo:

```text
valores informados: Adoção 30, Operação 20, Suporte 10
soma informada: 60

pesos efetivos:
Adoção   = 30 ÷ 60 × 100 = 50,0%
Operação = 20 ÷ 60 × 100 = 33,3%
Suporte  = 10 ÷ 60 × 100 = 16,7%
```

Um fator ajustado para zero é desativado. Por ser uma decisão explícita do gestor, sua retirada não reduz a confiança do score.

O ajuste manual existe para simular conhecimento de negócio, diferenças de segmento ou cenários de decisão. Ele não altera os dados históricos nem recalibra automaticamente os limiares internos dos sinais.

## 9. O que acontece quando falta um dado

Ausência de dado e baixo risco são estados diferentes:

- `0` significa que o sinal foi calculado e não indicou risco;
- `None` significa que não havia dado suficiente para calcular o sinal.

Um dado ausente não recebe zero, pois isso reduziria artificialmente o risco. Em vez disso, o sistema remove temporariamente o item indisponível e redistribui seu peso proporcionalmente entre os itens disponíveis.

### 9.1 Redistribuição dentro de um fator

Suponha um fator com dois sinais:

```text
Sinal A: peso original 60%, score 80
Sinal B: peso original 40%, dado ausente
```

O peso usado para o Sinal A passa a 100%, e o score do fator é `80`. Entretanto, a cobertura interna do fator fica em 60%, registrando que 40% da evidência esperada estava ausente.

### 9.2 Redistribuição entre fatores

O mesmo princípio vale para os fatores. Se apenas Adoção e Operação estiverem disponíveis:

```text
peso efetivo de Adoção = peso_base_adoção ÷ (peso_base_adoção + peso_base_operação)
peso efetivo de Operação = peso_base_operação ÷ (peso_base_adoção + peso_base_operação)
```

O score continua calculável, mas a cobertura e a confiança diminuem para comunicar que a decisão foi tomada com menos evidência.

### 9.3 Cobertura e confiança

```text
cobertura = soma da parcela dos pesos configurados que possui dados
confiança = cobertura × qualidade dos dados × suficiência histórica
```

Na implementação atual, a qualidade de cada sinal é `1,0` quando ele está disponível. A suficiência histórica é a proporção entre a quantidade de meses disponíveis e os seis meses esperados, limitada a `1,0`.

Portanto, confiança não é probabilidade de acerto. É um indicador de quanto da evidência esperada estava disponível para sustentar o score.

## 10. Pesos iniciais do preset e pesos recomendados

O preset SaaS B2B também declara pesos iniciais de módulo: Operação 30%, Suporte 20%, Engajamento de CS 20%, Adoção 15%, Satisfação 10% e Financeiro 5%.

Esses valores são uma configuração de referência e um fallback técnico do motor. Na experiência principal do protótipo, eles são substituídos pelos **pesos recomendados pela base** ou pelos **pesos ajustados pelo gestor**. Portanto, os pesos iniciais do preset não devem ser apresentados como resultado da análise histórica.

Os pesos internos dos sinais, por outro lado, permanecem fixos na demonstração e são usados para formar os scores de cada fator antes da comparação entre ativos e cancelados.

## 11. O que o modelo pode e não pode afirmar

O modelo pode afirmar que:

- os seis fatores foram calculados por regras explícitas;
- na amostra analisada, os cancelados tiveram scores médios maiores que os ativos nos seis fatores;
- os pesos recomendados representam a participação de cada diferença na soma das diferenças observadas;
- o score de cada cliente pode ser decomposto e auditado.

O modelo não pode afirmar que:

- um score de `x/100` equivale a `x%` de chance de cancelamento;
- os fatores causaram o cancelamento;
- a recomendação terá o mesmo desempenho em outra empresa ou período;
- os limiares heurísticos são ótimos;
- o valor mensal multiplicado pelo score é receita esperada perdida.

## 12. Como validar e evoluir os pesos

Antes de uso produtivo, recomenda-se:

1. congelar os pesos em um período de treinamento;
2. testar o score em meses posteriores que não participaram da escolha dos pesos;
3. medir antecipação do alerta, precisão, cobertura, falsos positivos e falsos negativos;
4. verificar o desempenho por segmento, plano e faixa de receita;
5. revisar limiares e pesos internos com base nesses resultados;
6. registrar ações executadas e desfechos para criar um ciclo de aprendizagem;
7. recalibrar os pesos periodicamente, mantendo versão, data e base utilizada.

Com volume suficiente, a diferença de médias pode ser comparada a métodos estatísticos ou supervisionados. Mesmo nesse caso, a versão explicável deve ser mantida como referência para auditoria e comunicação com o gestor.

## 13. Referência na implementação

As regras descritas neste documento estão implementadas em `retention.py`:

- `InovaappsAdapter.canonical_signals`: transforma colunas em sinais de `0` a `100`;
- `Modulo.calcular`: combina sinais e redistribui pesos internos;
- `recommended_weight_evidence`: compara ativos e cancelados e recomenda os pesos dos fatores;
- `PerfilDeRisco.calcular`: combina os fatores no score final e calcula cobertura e confiança;
- `build_profiles`: calcula a fila de clientes ativos.

Os testes de normalização, ausência de dados, desativação de fatores e recomendação histórica estão em `tests/test_retention.py`.
