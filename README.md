# Radar de Retenção

MVP em Streamlit para demonstrar uma fila antecipada e acionável de retenção com pesos explicáveis e forecasting.

## Fluxo da decisão

```text
Fonte → Panorama histórico → Pesos recomendados → Risco → Previsão → Prioridade → Ação

1. QUEM PRIORIZAR        2. O QUE PODE ACONTECER  3. POR QUE        4. O QUE FAZER
Risco × mensalidade      Projeção em três meses   Fatores e pesos   Playbook recomendado
```

A interface possui dois modos. No modo recomendado, os pesos vêm da diferença histórica observada entre os 22 cancelados e os 58 ativos. No modo ajustado, o gestor altera os pesos e a fila é recalculada ao vivo. O panorama informa as métricas usadas em cada recomendação.

A experiência possui leitura **Essencial** e **Detalhada**. A visão essencial usa divulgação progressiva: mantém a decisão principal visível e preserva explicações, diagnósticos, limites e metodologia em ajudas e controles clicáveis. A aplicação das 10 heurísticas de Nielsen está documentada em [`docs/UX_NIELSEN.md`](docs/UX_NIELSEN.md).

O forecasting prolonga por três meses a inclinação linear dos seis scores mais recentes de cada cliente. É uma projeção demonstrativa, não uma probabilidade de cancelamento. O valor exposto continua sendo `risco × mensalidade` e define a ordem da fila.

A documentação está dividida em:

- [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md): componentes, responsabilidades e fluxo técnico;
- [`docs/SISTEMA_DE_PESOS.md`](docs/SISTEMA_DE_PESOS.md): origem, justificativa, fórmulas, exemplos, tratamento de dados ausentes e limites do sistema de pesos;
- [`docs/UX_NIELSEN.md`](docs/UX_NIELSEN.md): decisões de usabilidade e aplicação das heurísticas de Nielsen;
- [`docs/TECH_STACK.md`](docs/TECH_STACK.md): tecnologias, bibliotecas, arquitetura e instruções de deploy.

## Execução

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Abra `http://127.0.0.1:8501`.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os pesos e limiares desta demonstração são explicáveis, mas devem ser calibrados por backtest antes de uso real.
