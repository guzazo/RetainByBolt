# Retain

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

## Como Acessar e Executar

### 1. Acesso Online (Sem instalação)

Você pode acessar e usar o sistema diretamente no navegador:
👉 **[https://retainbybolt.streamlit.app](https://retainbybolt.streamlit.app)**

---

### 2. Execução Local (Para desenvolvedores)

Para rodar o projeto localmente no seu computador:

```bash
# 1. Crie e ative o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o aplicativo
streamlit run app.py
```

Abra no navegador em `http://localhost:8501`.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os pesos e limiares desta demonstração são explicáveis, mas devem ser calibrados por backtest antes de uso real.
