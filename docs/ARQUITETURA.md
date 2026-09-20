# Arquitetura do Copiloto de Retenção

## Objetivo

O núcleo recebe sinais normalizados de risco e não conhece a fonte, o setor ou o nome original das colunas. SLA, NPS, pedidos e logins pertencem aos adaptadores e presets — nunca à fórmula central.

```text
Excel / CRM / Produto / Billing
              │
              ▼
         Adaptador da fonte
              │
              ▼
  Sinal(id, peso, ativo, valor 0–100)
              │
              ▼
     Modulo(peso, sinais[])
              │
              ▼
 PerfilDeRisco(modulos[]) ──► risco + confiança + cobertura
              │
              ▼
 risco × valor econômico ──► fila de prioridade
```

## Responsabilidades

- `Sinal`: representa uma evidência normalizada. `None` significa indisponível; nunca significa risco zero.
- `Modulo`: combina sinais disponíveis e redistribui seus pesos internamente.
- `PerfilDeRisco`: combina módulos disponíveis e redistribui seus pesos sem conhecer seus significados.
- `Preset`: declara quais módulos, sinais, pesos e playbooks pertencem a um modelo de negócio.
- `InovaappsAdapter`: única camada que conhece as abas e colunas do Excel oficial.
- `ClientRiskProfile`: objeto pronto para apresentação, contendo risco, confiança, prioridade e explicação.

## Matemática

```text
peso_redistribuido(i) = peso(i) / soma(pesos disponíveis)
risco = Σ(score(i) × peso_redistribuido(i))

cobertura = Σ(peso_base(módulo) × cobertura_interna(módulo))
confiança = cobertura × qualidade_dos_dados × suficiência_histórica
```

Consequências:

- Um módulo desativado é uma decisão de configuração e não reduz confiança.
- Um módulo ativo sem dados sai do score, mas reduz confiança.
- Um valor normalizado igual a `0` é evidência real de baixo risco.
- Um valor `None` é ausência de evidência.
- Se todos os módulos forem desligados, o motor retorna risco e confiança zero sem falhar.

## Presets demonstrados

### SaaS B2B

- Operação: 30%
- Suporte: 20%
- Engajamento de CS: 20%
- Adoção: 15%
- Satisfação: 10%
- Financeiro: 5%

### Assinatura B2C

- Frequência transacional: 35%
- Recência: 25%
- Engajamento no produto: 20%
- Renovação e pagamento: 15%
- Fricção de serviço: 5%

Como a base oficial é B2B, o preset B2C usa atividade e atendimento como proxies apenas para comprovar a portabilidade. Em produção, um adaptador B2C entregaria pedidos, logins, renovações e reembolsos reais aos mesmos objetos genéricos.

## Como adicionar um novo módulo

1. Criar uma `DefinicaoModulo` dentro de um preset.
2. Declarar seus `DefinicaoSinal`, pesos e playbook.
3. Fazer o adaptador da fonte produzir os ids declarados com valores entre 0 e 100.
4. Não alterar `Sinal`, `Modulo` nem `PerfilDeRisco`.

```python
DefinicaoModulo(
    id="logistica",
    nome="Experiência de entrega",
    peso=25,
    sinais=(
        DefinicaoSinal("atraso_entrega", "Atrasos", 60),
        DefinicaoSinal("pedido_incompleto", "Pedidos incompletos", 40),
    ),
    acao="Crédito preventivo e revisão da rota",
    motivo="A experiência logística deteriorou.",
)
```

## Validação

Os testes cobrem redistribuição de sinais e módulos ausentes, diferença entre ausência e desativação, todos os módulos desligados, troca de preset, limites dos scores, prioridade econômica e os 58 clientes ativos.

## Pesos recomendados e forecasting

O sistema possui dois níveis de ponderação: pesos internos, usados para combinar os sinais de um módulo, e pesos dos módulos, usados para formar o score final. Para cada módulo, o sistema calcula a pontuação média dos clientes ativos e cancelados. A diferença entre as médias, com piso técnico de `1,0` ponto, representa a força exploratória do fator. Essas forças são normalizadas para 100% e formam os pesos recomendados.

A origem dos dados, as fórmulas de cada sinal, a justificativa do método, a redistribuição por ausência de dados, exemplos completos e as limitações estão documentados em [`SISTEMA_DE_PESOS.md`](SISTEMA_DE_PESOS.md).

O forecasting recalcula o risco nos seis meses observados mais recentes, ajusta uma tendência linear e prolonga somente sua inclinação por três meses, partindo do risco atual. A projeção é limitada ao intervalo de 0 a 100 e deve ser apresentada como cenário caso a tendência continue.

```bash
python -m unittest discover -s tests -v
```

## Links

- Protótipo local: `http://127.0.0.1:8501`
- Documentação visual da equipe: <https://canva.link/fy3klgauf9b2yzf>
