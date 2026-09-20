# Stack Tecnológica — Radar de Retenção & Copiloto de Churn

Este documento descreve detalhadamente todas as tecnologias, bibliotecas, padrões de arquitetura e decisões de design utilizadas na construção do projeto **Radar de Retenção**.

---

## 1. Visão Geral da Arquitetura

O sistema é dividido em três camadas desacopladas:

```text
┌─────────────────────────────────────────────────────────────┐
│                       INTERFACE (UI)                        │
│             Streamlit · CSS Customizado · Altair            │
│       Radar de Retenção  │  Importação de Base de Dados     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    MOTOR DE RISCO & REGRAS                  │
│                     Python Puro · retention.py              │
│       Sinais  ──►  Módulos  ──►  PerfilDeRisco  ──► Fila     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      CAMADA DE DADOS                        │
│          Pandas · OpenPyXL · INOVAAPPS_base_de_dados.xlsx    │
│      clientes │ atendimento_mensal │ nps │ situacao_clientes│
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Tecnologias Utilizadas

### 2.1 Backend e Lógica de Negócio
- **Python 3 (3.11+)**: Linguagem central do projeto.
- **Dataclasses & Typing**: Uso extensivo de tipagem estática e dataclasses imutáveis (`@dataclass(frozen=True)`) para modelar `Sinal`, `Modulo`, `PerfilDeRisco`, `ClientRiskProfile` e `WeightEvidence`.
- **LRU Cache (`functools.lru_cache`)**: Otimização de performance no carregamento de dados e cálculo de evidências históricas.
- **NumPy**: Cálculos matemáticos, normalização de limites (`np.clip`), regressão linear para projeção de risco em 3 meses (`np.polyfit`) e agregação estatística.

### 2.2 Frontend e Interface de Usuário
- **Streamlit (`streamlit>=1.40,<2`)**:
  - Framework reativo para construção de dashboards web em Python.
  - Gerenciamento de estado de sessão com `st.session_state` (controle de página ativa, cliente selecionado e histórico de ações).
  - Componentes nativos utilizados: `st.segmented_control`, `st.file_uploader`, `st.metric`, `st.tabs`, `st.popover`, `st.toast`, `st.dataframe`.
- **Altair (`altair`)**:
  - Biblioteca declarativa de visualização estatística baseada em Vega-Lite.
  - Utilizada para os gráficos de tendência temporal observada vs. projetada (`forecast_chart`) e o gráfico de barras comparativo de fatores cancelados vs. ativos.

### 2.3 Processamento e Importação de Dados
- **Pandas (`pandas>=2.0,<3`)**:
  - Manipulação, mesclagem e análise temporal das tabelas relacionais.
  - Tratamento de séries temporais mensais (`pd.PeriodIndex`, `freq="M"`).
- **OpenPyXL (`openpyxl>=3.1,<4`)**:
  - Engine de leitura e validação das planilhas Excel (`.xlsx`) com suporte a múltiplas abas.

### 2.4 Design System & Estilização (Google Stitch Inspired)
- **Google Fonts**:
  - Família tipográfica: `Google Sans` e `Google Sans Text` (pesos 400, 500, 700 e 900).
- **Paleta de Cores**:
  - Azul Primário: `#2457d6` (hover `#1a44ab`, fundo `#edf3ff`).
  - Verde Sucesso: `#157a55` (fundo `#eaf8f1`).
  - Laranja Alerta: `#b96808` (fundo `#fff5df`).
  - Vermelho Risco Alto: `#c63c3c` (fundo `#fff0ed`).
  - Fundo da Tela (Canvas): `#f6f8fc`.
  - Linhas e Bordas: `#dfe5ee`.
  - Texto Principal (Ink): `#14213d`.
  - Texto Secundário (Muted): `#64748b`.
- **Componentes Visuais**:
  - Botões no formato **Pill (Cápsula)** com `border-radius: 9999px` e elevação suave ao passar o cursor.
  - Cartões com cantos arredondados (`border-radius: 18px`), sombras sutis e bordas de separação elegantes.
  - Tags e Badges de status para identificação rápida de risco, MRR e tipos de contrato.

---

## 3. Estrutura do Repositório

```text
.
├── app.py                      # Aplicação web Streamlit (UI, páginas e navegação)
├── retention.py                # Motor central de cálculo de risco e adaptadores de dados
├── requirements.txt            # Dependências Python do projeto
├── data/
│   └── INOVAAPPS_base_de_dados.xlsx # Planilha padrão com as 4 abas estruturadas
├── docs/
│   ├── ARQUITETURA.md          # Especificação técnica do fluxo e responsabilidades
│   ├── SISTEMA_DE_PESOS.md     # Metodologia e fórmulas dos pesos
│   ├── UX_NIELSEN.md           # Aplicação das 10 heurísticas de usabilidade
│   └── TECH_STACK.md           # Este documento (stack e tecnologias)
├── tests/
│   └── test_retention.py       # Suíte de testes unitários (15 testes automatizados)
└── README.md                   # Apresentação do projeto e instruções de execução
```

---

## 4. Como Executar Localmente

```bash
# 1. Crie o ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# 2. Instale as dependências
pip install -r requirements.txt

# 3. Inicie o aplicativo
streamlit run app.py
```

O aplicativo estará disponível em: `http://localhost:8501`.

---

## 5. Como Publicar na Nuvem (Deploy)

A forma recomendada e gratuita para hospedar esta aplicação é o **Streamlit Community Cloud**:

1. Suba este repositório para o seu **GitHub**.
2. Acesse **[share.streamlit.io](https://share.streamlit.io)** e conecte sua conta do GitHub.
3. Clique em **New app**, aponte para o repositório e selecione `app.py` como arquivo principal.
4. Clique em **Deploy**. Sua URL pública estará no ar em poucos minutos.
