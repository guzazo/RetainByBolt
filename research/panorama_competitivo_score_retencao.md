# Deep research — sistemas de pontuação para retenção B2B

**Data da pesquisa:** 19 de setembro de 2026  
**Projeto analisado:** Radar de Retenção / Copiloto de Retenção B2B  
**Objetivo:** identificar soluções semelhantes, medir o grau de novidade da proposta e recomendar um recorte implementável e defensável para o hackathon.

## 1. Resumo executivo

A ideia resolve um problema real, mas **a categoria de produto não é nova**. Health score configurável, alertas de churn, segmentação, histórico, priorização de contas e playbooks já aparecem em plataformas maduras como Gainsight, ChurnZero, Totango, Planhat, Vitally, Custify e ClientSuccess. No Brasil, SenseData, TW Solutions, WeON, SoftCS e outras já comunicam propostas semelhantes.

O maior risco para o pitch é apresentar como inovação algo que o mercado considera funcionalidade padrão: “juntar uso, suporte, NPS e engajamento em uma nota e disparar uma ação”. A própria TW Solutions descreve um score formado por uso, engajamento, chamados, atrasos e NPS, seguido de prioridade e playbooks — praticamente o mesmo núcleo funcional do protótipo.

Isso não invalida o projeto. Para o hackathon, a oportunidade é reposicioná-lo como:

> **Uma camada de decisão auditável para empresas B2B de serviços tecnológicos, que detecta deterioração persistente em contratos com SLA, comprova o alerta com trajetória e benchmark, e transforma capacidade limitada do time em uma fila de intervenção de maior impacto financeiro.**

O diferencial defensável deve ser a combinação de:

1. **Trajetória e persistência**, não uma fotografia mensal.
2. **Prova retrospectiva na base fornecida**, medindo quantos cancelamentos seriam detectados e com quanta antecedência.
3. **Separação explícita entre risco e impacto financeiro.**
4. **Explicação determinística e auditável**, mostrando quais sinais mudaram, quando e contra qual referência.
5. **Fila limitada à capacidade do time**, por exemplo “as cinco contas que devem ser abordadas esta semana”.
6. **Implantação leve sobre planilha**, sem exigir um projeto longo de integração.

## 2. O que o protótipo atual realmente faz

O código implementa um score heurístico de 0 a 100 com seis dimensões:

| Dimensão | Peso atual |
|---|---:|
| Adoção | 30% |
| Operação | 25% |
| Suporte | 15% |
| Engajamento | 10% |
| NPS | 10% |
| Financeiro | 10% |

Ele compara os três meses mais recentes com os três anteriores, aplica uma penalização quando não há persistência, classifica risco em baixo/médio/alto e ordena contas ativas por `MRR × score / 100`. A interface organiza a decisão em **quem abordar, por que agir e o que fazer**.

### Ponto estatístico crítico

O score atual é um **índice de severidade**, não uma probabilidade calibrada de cancelamento. Portanto, `MRR × score / 100` não deve ser chamado de “receita esperada em risco” nem interpretado como valor probabilístico. A documentação da própria Gainsight faz essa distinção: sem análise de churn, um health score não quantifica a probabilidade de cancelamento e pode nem ser indicativo de churn.

Para o MVP, a nomenclatura segura é:

- **Índice de risco:** 0–100, sem símbolo de porcentagem.
- **MRR ponderado pelo risco:** usado somente como índice de ordenação.
- **Probabilidade de churn:** reservada para uma futura versão calibrada e validada.

## 3. Evidência encontrada na base do desafio

A base contém 80 clientes, dos quais 22 cancelaram e 58 continuam ativos. A amostra é pequena para um modelo complexo, mas suficiente para mostrar padrões e justificar um score transparente.

### Três meses antes do cancelamento versus ativos recentes

| Sinal | Cancelados | Ativos | Diferença observada |
|---|---:|---:|---:|
| Uso da plataforma | 60,76% | 82,62% | −21,86 p.p. |
| SLA cumprido | 56,49% | 79,52% | −23,02 p.p. |
| Tempo médio de resolução | 30,57 h | 21,56 h | +9,02 h |
| Chamados críticos/mês | 1,98 | 0,59 | +1,39 |
| Taxa de reuniões realizadas | 52% | 81% | −29 p.p. |
| Atraso médio de pagamento | 6,21 dias | 3,05 dias | +3,17 dias |
| NPS detrator ou silêncio nos dois últimos ciclos | 90,9% | 43,1% | +47,8 p.p. |

### Mudança na trajetória de seis meses

| Sinal | Cancelados | Ativos |
|---|---:|---:|
| Variação média de uso | −14,65 p.p. | +1,11 p.p. |
| Variação média de SLA | −21,64 p.p. | −1,35 p.p. |
| Variação do tempo de resolução | +5,51 h | −0,35 h |
| Variação do atraso de pagamento | +1,89 dias | +0,03 dia |

Esses dados sustentam a tese de que **trajetória é mais informativa que uma fotografia isolada**, exatamente como alerta a aba “Leia-me”: há clientes que pioraram sem cancelar, então um único mês ruim não separa risco de ruído.

## 4. Concorrentes e referências diretas

### 4.1 Gainsight

**O que oferece:** scorecards com múltiplas medidas e grupos, pesos, exceções, validade, métodos numéricos/letras/cores, entradas manuais ou automáticas e diferentes scorecards por tipo de conta. Integra mudança de score a alertas e fluxos de Customer Success.

**Sobreposição:** score multidimensional, pesos, tendência histórica, explicabilidade por componente, segmentação e ação.

**Lição para o projeto:** health score e probabilidade de churn não são sinônimos. A Gainsight explicita que a probabilidade exige análise de churn e dados de engajamento; essa precisão conceitual deve aparecer no pitch.

Fontes: [Scorecards Overview](https://support.gainsight.com/gainsight_nxt/05Scorecards/01About/Scorecards_Overview) e [Renewal Center FAQ](https://support.gainsight.com/gainsight_nxt/Renewal_Center/04FAQs/Renewal_Center_FAQs).

### 4.2 ChurnZero

**O que oferece:** ChurnScores configuráveis com dados quantitativos e qualitativos, segmentação, histórico, alertas e playbooks. Seu próprio manual recomenda uma “hot list” baseada em contas vermelhas, proximidade da renovação, valor total do contrato e ARR.

**Sobreposição:** a fila de risco × valor e a transição de score para playbook já são práticas explícitas do produto.

**Lição para o projeto:** o diferencial não pode ser apenas ordenar risco por MRR. É preciso demonstrar uma forma melhor de validar, explicar ou implantar essa decisão.

Fontes: [Customer Health Score Dashboard](https://churnzero.com/features/customer-health-scores/) e [Customer Health Score Handbook](https://churnzero.com/wp-content/uploads/2023/05/ChurnZero_customer_health_score_handbook.pdf).

### 4.3 Totango / Unison

**O que oferece:** saúde multidimensional e um modelo padrão com sentimento, engajamento, relacionamento e voz do cliente. O Unison usa e-mails, reuniões, tickets, chamadas e feedback para avaliar risco.

**Sobreposição:** agregação de sinais, risco, explicação e visão de portfólio.

**Lição para o projeto:** sentimento e profundidade de relacionamento são espaços de evolução, mas não são necessários para o MVP da base atual.

Fonte: [Standard Health Scoring](https://unison-support.totango.com/hc/en-us/articles/32488556467092-Standard-health-scoring).

### 4.4 Planhat

**O que oferece:** Health Lab com uso, suporte, sentimento, recência de contato, volume de conversas, pesos e limites específicos por segmento. Mudanças alimentam workflows e alertas que informam quem precisa de atenção e por quê.

**Sobreposição:** praticamente toda a tríade “prioridade + explicação + ação”, além de regras específicas por segmento.

**Lição para o projeto:** a Planhat recomenda validar os scores contra renovação e reconhece que modelos por regras têm pesos estimados. O protótipo pode se destacar ao tornar o backtest visível, e não apenas configurável.

Fontes: [Health Lab](https://www.planhat.com/features/health-lab) e [Customer health score: models, metrics and how to calculate it](https://www.planhat.com/customer-success/health).

### 4.5 Vitally

**O que oferece:** motor no-code com pesos, limites, regras lógicas, prévia do efeito das regras, atualização em tempo real e perfis diferentes por segmento, plano, estágio ou região. Mudanças disparam tarefas, alertas e playbooks.

**Sobreposição:** pesos, segmentos, alertas e ação recomendada.

**Lição para o projeto:** uma única régua para toda a carteira é uma limitação. Mesmo no MVP, plano ou porte deve alterar ao menos limites e prioridade, não apenas aparecer como informação visual.

Fonte: [Customer Health Score Software](https://www.vitally.io/features/health-scores).

### 4.6 Custify

**O que oferece:** scores individuais e global, tendências, sinais automáticos, playbooks e tarefas. A empresa ressalta que o score global é útil para visão rápida, mas explica pouco sem a decomposição em scores individuais.

**Sobreposição:** score global, componentes, trajetória e ação.

**Lição para o projeto:** preservar o painel de evidências é correto; o score sozinho vira “teatro de dashboard”.

Fonte: [The Full Guide to Customer Health Scores](https://www.custify.com/blog/customer-health-score-guide/).

### 4.7 ClientSuccess

**O que oferece:** SuccessScore com grupos ponderados, perfis por tipo de cliente, dados de NPS, engajamento, renovação e variações de uso em 7, 30, 60 ou 90 dias. O histórico é recalculado diariamente.

**Sobreposição:** pesos, segmentação e variação temporal.

**Lição para o projeto:** a análise de mudança ao longo do tempo já existe no mercado; o valor adicional deve ser mostrar antecedência e resultado da intervenção.

Fonte: [SuccessScore](https://help.clientsuccess.com/en/articles/12833707-successscore).

## 5. Concorrentes e referências no Brasil

### 5.1 SenseData

Plataforma brasileira de Customer Success com visão 360, KPIs customizáveis, Health Score, segmentação e jornadas automatizadas. É um concorrente direto importante por presença local e aplicação também fora do SaaS puro, incluindo indústria e saúde.

Fonte: [SenseData](https://sensedata.com.br/).

### 5.2 TW Solutions

É o concorrente mais parecido no discurso público. Declara combinar **uso, engajamento, chamados, atrasos e NPS**, trabalhar contas por prioridade e recomendar playbooks como reunião de resgate, revisão de escopo ou treinamento.

**Implicação:** não é seguro afirmar que essa combinação de sinais ou “score que vira ação” seja inédita.

Fonte: [Customer Success, Health Score e Anti-Churn](https://twsolutions.com.br/customer-success-retencao/).

### 5.3 WeON

Comunica health score, churn prediction, risco versus valor e “Próxima Melhor Ação”. A frase “não é um dashboard, é um assistente que prioriza” é especialmente próxima do posicionamento pensado para o protótipo.

Fonte: [Customer Success — WeON](https://weon.com.br/solucoes/customer-success).

### 5.4 ANCHOR

Produto verticalizado para agências de performance. Calcula score semanal com seis sinais e pesos explícitos, alega validação em agências brasileiras e envia um brief com contas em risco e ação recomendada.

**Lição para o projeto:** verticalização, antecedência mensurável e pesos auditáveis formam um posicionamento mais convincente do que uma plataforma genérica.

Fonte: [ANCHOR](https://www.getanchor.com.br/).

### 5.5 Outros exemplos locais

- [SoftCS](https://softcs.com.br/): score, prioridades do dia, automações e resumo por IA.
- [Retain](https://retain.com.br/): score de churn em tempo real, automação e WhatsApp para provedores de internet.
- [Partenero](https://partenero.com/produto/customer-success): health score configurável, jornada, alertas e playbooks.
- [CustomerScore.io](https://www.customerscore.io/pt-br/solutions/revops): previsão de churn/expansão, explicação e lista classificada para times de receita.

## 6. Matriz de sobreposição

Legenda: **● forte**, **◐ parcial**, **— não destacado na fonte consultada**.

| Empresa | Score ponderado | Trajetória | Segmentação | Explica fatores | Prioriza por receita | Playbook/ação |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Gainsight | ● | ● | ● | ● | ◐ | ● |
| ChurnZero | ● | ● | ● | ● | ● | ● |
| Totango/Unison | ● | ● | ● | ● | ◐ | ● |
| Planhat | ● | ● | ● | ● | ◐ | ● |
| Vitally | ● | ● | ● | ● | ◐ | ● |
| Custify | ● | ● | ● | ● | ◐ | ● |
| ClientSuccess | ● | ● | ● | ● | ◐ | ◐ |
| SenseData | ● | ◐ | ● | ◐ | ◐ | ● |
| TW Solutions | ● | ● | ◐ | ◐ | ◐ | ● |
| WeON | ● | ● | ◐ | ● | ● | ● |
| Protótipo atual | ● | ● | — | ● | ● | ● |

Conclusão da matriz: **nenhum dos blocos isolados é novo**. A vantagem competitiva precisa vir do recorte do usuário, da velocidade de implantação, da qualidade da validação e da disciplina da decisão.

## 7. Lacunas aproveitáveis

### 7.1 Backtest visível e compreensível

As plataformas ensinam a validar e ajustar scores, mas normalmente vendem configuração e automação. O protótipo pode mostrar na própria interface:

- quantos dos 22 cancelamentos teriam sido sinalizados;
- com um ou dois meses de antecedência;
- quantos falsos positivos seriam gerados;
- qual MRR teria entrado na fila;
- quantas contas o time precisaria trabalhar por semana.

Isso transforma “acredite no score” em “veja como ele teria se comportado”.

### 7.2 Capacidade operacional como parte do algoritmo

Em vez de mostrar todos os riscos, o usuário informa a capacidade semanal do time. O sistema retorna as melhores intervenções dentro desse limite. A métrica passa a ser **receita coberta por hora de CS**, não quantidade de alertas.

### 7.3 Foco em serviços B2B com SLA

Grande parte do mercado enfatiza SaaS e adoção de produto. A base do desafio representa uma empresa de serviços tecnológicos, com SLA, chamados críticos, reaberturas, tempo de resolução, reuniões e pagamentos. Esse contexto permite um posicionamento vertical mais claro.

### 7.4 Evidência antes da recomendação

Cada ação deve vir com uma cadeia auditável:

`sinal → mudança → persistência → impacto → ação sugerida`

Exemplo:

> SLA caiu 21 p.p. e o tempo de resolução subiu 6 h durante três meses. O padrão apareceu em X% dos cancelamentos históricos. Como a conta Enterprise representa R$ 32,6 mil de MRR, recomenda-se plano de recuperação de SLA com sponsor executivo.

### 7.5 Aprendizado com a intervenção

Registrar “ação executada”, “falso positivo”, “conta recuperada” e “cancelou” permite recalibrar pesos e medir eficácia de cada playbook. Esse ciclo fechado é mais defensável que apenas recalcular scores.

## 8. Recomendação de MVP implementável

### Manter

- Fila priorizada.
- Painel de trajetória de seis meses.
- Decomposição do score por dimensão.
- Explicação em linguagem natural baseada em regras.
- Playbook associado à causa dominante.
- Botão para descartar falso positivo.

### Alterar antes do pitch

1. Trocar “62% de risco” por “Índice de risco 62/100”.
2. Trocar “MRR exposto” por “MRR ponderado pelo risco”, a menos que haja calibração probabilística.
3. Adicionar um pequeno card de backtest, mesmo que calculado offline.
4. Mostrar “por que agora”: comparação últimos 3 meses versus 3 anteriores.
5. Adicionar “confiança do alerta”: alta quando há múltiplos sinais persistentes; baixa quando o score depende de um único indicador.
6. Permitir informar capacidade semanal, por exemplo 5 contas.
7. Manter os pesos transparentes e editáveis, mas mostrar os valores recomendados pela base histórica.

### Não implementar agora

- IA generativa para calcular o score.
- Modelo de machine learning complexo com apenas 22 cancelamentos.
- Integrações reais com CRM, help desk e e-mail.
- Automação externa de mensagens.
- Previsão numérica de churn sem calibração.

## 9. Validação mínima recomendada

Simular o score em cada mês histórico usando somente dados disponíveis até aquele mês e medir:

1. **Recall@K:** quantos cancelamentos futuros estavam entre as K contas priorizadas.
2. **Precisão@K:** quantos alertas da fila realmente cancelaram no horizonte escolhido.
3. **Antecedência mediana:** meses entre o primeiro alerta e o cancelamento.
4. **MRR capturado:** soma do MRR dos cancelamentos presentes na fila.
5. **Carga operacional:** alertas novos por semana/mês.
6. **Estabilidade:** quantas contas entram e saem da fila por ruído.

Com 22 eventos, usar validação temporal e evitar dividir aleatoriamente linhas mensais do mesmo cliente entre treino e teste, pois isso causaria vazamento de informação.

## 10. Posicionamento recomendado para os jurados

### Formulação curta

> Cancelamentos são inevitáveis; descobri-los tarde não é. Nosso copiloto usa a trajetória operacional dos contratos para montar uma fila semanal, provar por que cada conta entrou nela e recomendar a intervenção de maior impacto — sem exigir que o time confie em uma caixa-preta.

### Como responder “isso já existe?”

> Sim, plataformas de Customer Success já usam health scores. O problema é que muitas exigem implantação ampla e ainda entregam uma nota que precisa ser investigada. Nosso recorte é uma camada leve para empresas B2B de serviços com SLA: importa a planilha existente, valida o modelo no histórico da própria empresa, mostra a trajetória que sustenta o alerta e limita a fila à capacidade real do time. Não estamos inventando o health score; estamos tornando a decisão auditável e operacional.

### Proposta de valor em uma frase

> Para gestores de Customer Success em empresas B2B de serviços tecnológicos, o Radar de Retenção transforma sinais operacionais dispersos em uma fila semanal explicável e validada, priorizando a receita que pode receber ação a tempo.

## 11. Veredito

- **Aderência ao problema:** alta.
- **Implementabilidade no hackathon:** alta.
- **Originalidade da ideia genérica:** baixa a média.
- **Originalidade com o recorte recomendado:** média e defensável.
- **Risco técnico:** baixo se mantido como score explicável; alto se vendido como previsão probabilística.
- **Melhor argumento competitivo:** backtest + auditabilidade + capacidade operacional + vertical de serviços com SLA.

O projeto deve competir como uma **solução de decisão bem validada**, não como um algoritmo inédito.
