"""MVP simples: pesos explicados, previsão, prioridade e ação."""

from __future__ import annotations

import base64
from pathlib import Path
import re

import altair as alt
import pandas as pd
import streamlit as st

from retention import (
    DATA_PATH,
    PRESET_SAAS,
    ClientRiskProfile,
    at_risk,
    build_profiles,
    forecast_client_risk,
    get_active_data_path,
    recommended_weight_evidence,
    set_active_dataset,
    validate_dataset,
)


st.set_page_config(page_title="Retain | by bolt", page_icon="↗", layout="wide")


APP_DIR = Path(__file__).parent
LANDING_PATH = APP_DIR / "assets" / "retain_landing.html"
LOGO_PATH = APP_DIR / "assets" / "retain-logo.png"


def brl(value: float) -> str:
    return f"R$ {value:,.0f}".replace(",", ".")


def styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700;900&family=Google+Sans+Text:wght@400;500;700&display=swap');

        :root{--ink:#14213d;--muted:#64748b;--line:#dfe5ee;--canvas:#f6f8fc;
        --blue:#2457d6;--blue-hover:#1a44ab;--blue-bg:#edf3ff;--red:#c63c3c;--red-bg:#fff0ed;
        --orange:#b96808;--orange-bg:#fff5df;--green:#157a55;--green-bg:#eaf8f1}

        html, body, [class*="css"], .stApp {
            font-family: 'Google Sans', 'Google Sans Text', -apple-system, BlinkMacSystemFont, sans-serif !important;
        }

        .stApp{background:var(--canvas);color:var(--ink)}.block-container{max-width:1380px;padding-top:1.2rem;padding-bottom:4rem}
        [data-testid="stHeader"]{background:transparent}h1,h2,h3,h4{font-family:'Google Sans', sans-serif !important;letter-spacing:-.03em}
        .eyebrow{color:var(--blue);font-size:.7rem;font-weight:900;letter-spacing:.13em;text-transform:uppercase}
        .subtitle{color:var(--muted);font-size:1rem}.flow{display:flex;align-items:center;gap:.5rem;flex-wrap:wrap;margin:.8rem 0 1.1rem}
        .flow-step{background:white;border:1px solid var(--line);border-radius:999px;padding:.48rem .72rem;font-size:.72rem;font-weight:800}
        .arrow{color:#94a3b8;font-weight:900}.story{background:white;border:1px solid var(--line);border-radius:18px;padding:1.05rem 1.15rem}
        .story-blue{border-left:5px solid var(--blue)}.story-green{border-left:5px solid var(--green)}
        .big{font-size:2rem;font-weight:950;line-height:1.05}.small{font-size:.76rem;color:var(--muted)}
        .queue{background:white;border:1px solid var(--line);border-radius:13px;padding:.72rem .8rem;margin:.4rem 0 .18rem}
        .queue.selected{border:2px solid var(--blue);background:var(--blue-bg)}.row{display:flex;justify-content:space-between;gap:.6rem}
        .name{font-weight:900}.money{text-align:right;font-weight:900}.badge{display:inline-block;padding:.2rem .42rem;border-radius:999px;
        font-size:.63rem;font-weight:850;margin:.35rem .2rem 0 0}.high{background:var(--red-bg);color:var(--red)}
        .medium{background:var(--orange-bg);color:var(--orange)}.neutral{background:#eef2f7;color:#45556c}
        .factor{display:flex;justify-content:space-between;font-size:.78rem;font-weight:800;margin-top:.45rem}
        .action{background:linear-gradient(135deg,var(--green-bg),#fbfffd);border:1px solid #bce7d2;border-radius:16px;padding:1rem}
        .action-title{color:var(--green);font-size:1.1rem;font-weight:950}.explain{background:var(--blue-bg);border-radius:12px;padding:.75rem .85rem;color:#24458f}
        .step-card{background:white;border:1px solid var(--line);border-radius:15px;padding:.9rem 1rem;min-height:150px}
        .step-number{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--blue);color:white;font-weight:950}
        .step-title{font-size:.92rem;font-weight:950;margin:.55rem 0 .3rem}.step-copy{font-size:.78rem;line-height:1.48;color:var(--muted)}
        .formula-box{background:#101b35;color:white;border-radius:15px;padding:1rem 1.1rem;margin:.5rem 0}
        .formula-main{font-size:1.12rem;font-weight:900}.formula-note{color:#cbd5e1;font-size:.76rem;margin-top:.35rem}
        .factor-card{background:white;border:1px solid var(--line);border-radius:14px;padding:.85rem 1rem;margin:.45rem 0}
        .factor-card strong{font-size:.9rem}.factor-card p{font-size:.76rem;color:var(--muted);margin:.3rem 0 0;line-height:1.45}
        div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:.55rem .75rem;border-radius:13px}
        div[data-testid="stButton"]>button{border-radius:9px;font-weight:800}
        div[data-testid="stPopover"]>button{min-height:0;border-radius:999px;padding:.24rem .62rem;
        font-size:.72rem;font-weight:850;color:var(--blue);border-color:#b9caf5;background:var(--blue-bg)}
        div[data-testid="stExpander"]{background:white;border:1px solid var(--line);border-radius:14px}
        .status-strip{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin:.35rem 0 1rem}
        .status-item{background:white;border:1px solid var(--line);border-radius:999px;padding:.3rem .62rem;
        font-size:.7rem;font-weight:800;color:#45556c}.status-dot{display:inline-block;width:7px;height:7px;
        border-radius:50%;background:#22a06b;margin-right:.35rem}.section-head{display:flex;justify-content:space-between;
        align-items:flex-end;gap:1rem;margin-bottom:.25rem}.compact-note{font-size:.74rem;color:var(--muted)}
        .empty-safe{background:#fff7e6;border:1px solid #f4d08a;border-radius:12px;padding:.8rem;color:#7a4b00}

        /* Google Stitch Pill Button */
        .stitch-pill-btn div[data-testid="stButton"] > button {
            background-color: var(--blue) !important;
            color: #ffffff !important;
            border-radius: 9999px !important;
            padding: 0.65rem 1.6rem !important;
            font-family: 'Google Sans', 'Google Sans Text', sans-serif !important;
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            border: none !important;
            box-shadow: 0 2px 8px rgba(36, 87, 214, 0.28) !important;
            transition: all 0.2s ease !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.5rem !important;
            width: 100% !important;
        }
        .stitch-pill-btn div[data-testid="stButton"] > button:hover {
            background-color: var(--blue-hover) !important;
            box-shadow: 0 4px 14px rgba(36, 87, 214, 0.42) !important;
            transform: translateY(-1px) !important;
        }

        .back-btn div[data-testid="stButton"] > button {
            background-color: white !important;
            color: var(--ink) !important;
            border: 1px solid var(--line) !important;
            border-radius: 9999px !important;
            padding: 0.42rem 1.2rem !important;
            font-size: 0.85rem !important;
            font-weight: 700 !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
        }
        .back-btn div[data-testid="stButton"] > button:hover {
            border-color: var(--blue) !important;
            color: var(--blue) !important;
        }

        .import-box {
            background: white;
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 1.5rem;
            margin: 1.2rem 0;
            box-shadow: 0 2px 8px rgba(20, 33, 61, 0.04);
        }
        .import-box-title {
            font-size: 1.15rem;
            font-weight: 900;
            color: var(--ink);
            margin-bottom: 0.5rem;
        }
        .tag-sheet {
            display: inline-block;
            padding: 0.28rem 0.65rem;
            border-radius: 8px;
            font-size: 0.75rem;
            font-weight: 800;
            background: var(--blue-bg);
            color: var(--blue);
            margin: 0.2rem 0.35rem 0.2rem 0;
            border: 1px solid #c9dafb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    """Render the approved Stitch landing page and connect every CTA to the live dashboard."""
    html = LANDING_PATH.read_text(encoding="utf-8")
    html = re.sub(
        r'<button(?P<attrs>[^>]*?) onclick="openDashboard\(event\)">(?P<body>.*?)</button>',
        r'<a\g<attrs> href="?view=radar" target="_blank" rel="noopener">\g<body></a>',
        html,
        flags=re.DOTALL,
    )
    logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    logo_uri = f"data:image/png;base64,{logo_data}"
    html = re.sub(
        r'(<img alt="Retain Logo"[^>]*?src=")[^"]+("[^>]*>)',
        rf"\g<1>{logo_uri}\g<2>",
        html,
    )
    st.markdown(
        """
        <style>
          [data-testid="stSidebar"], [data-testid="stHeader"],
          [data-testid="stToolbar"], [data-testid="stDecoration"] {display:none !important}
          .stApp, [data-testid="stAppViewContainer"] {background:#F6F8FC !important}
          .block-container {max-width:none !important;padding:0 !important;margin:0 !important}
          [data-testid="stVerticalBlock"] {gap:0 !important}
          iframe[data-testid="stIFrame"] {display:block;border:0;width:100%}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.iframe(html, height=720, width="stretch")


def detail_badge(label: str, body: str) -> None:
    """Keep explanations available without competing with the primary task."""
    with st.popover(label):
        st.markdown(body)


def optional_caption(text: str, detailed: bool) -> None:
    if detailed:
        st.caption(text)


def queue_card(profile: ClientRiskProfile, selected: bool, position: int) -> None:
    risk_class = "high" if profile.risk_level == "Alto" else "medium"
    st.markdown(
        f"""
        <div class="queue{' selected' if selected else ''}">
          <div class="row"><div><div class="name">{position}. Cliente {profile.client_id}</div>
          <div class="small">{profile.plan} · {profile.segment}</div></div>
          <div><div class="money">{brl(profile.exposed_value)}</div><div class="small">valor exposto</div></div></div>
          <span class="badge {risk_class}">Risco {profile.risk_score:.0f}/100</span>
          <span class="badge neutral">MRR {brl(profile.economic_value)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Selecionado" if selected else "Ver história",
        key=f"select-{profile.client_id}",
        disabled=selected,
        type="primary" if selected else "secondary",
        width="stretch",
    ):
        st.session_state.selected_client_id = profile.client_id
        st.rerun()


def forecast_chart(profile: ClientRiskProfile, forecast) -> alt.Chart:
    actual = pd.DataFrame({
        "ordem": range(len(forecast.actual_scores)),
        "mês": forecast.actual_months,
        "risco": forecast.actual_scores,
        "tipo": "Observado",
    })
    projection = pd.DataFrame({
        "ordem": range(len(forecast.actual_scores) - 1, len(forecast.actual_scores) + 3),
        "mês": (forecast.actual_months[-1],) + forecast.forecast_months,
        "risco": (forecast.actual_scores[-1],) + forecast.forecast_scores,
        "tipo": "Projeção",
    })
    data = pd.concat([actual, projection], ignore_index=True)
    order = list(forecast.actual_months) + list(forecast.forecast_months)
    line = (
        alt.Chart(data)
        .mark_line(point=True, strokeWidth=3)
        .encode(
            x=alt.X("mês:N", sort=order, title=None),
            y=alt.Y("risco:Q", scale=alt.Scale(domain=[0, 100]), title="Risco"),
            color=alt.Color("tipo:N", scale=alt.Scale(domain=["Observado", "Projeção"], range=["#2457d6", "#c63c3c"]), title=None),
            strokeDash=alt.StrokeDash("tipo:N", scale=alt.Scale(domain=["Observado", "Projeção"], range=[[1, 0], [7, 5]]), legend=None),
            tooltip=["mês:N", "tipo:N", alt.Tooltip("risco:Q", format=".1f")],
        )
    )
    threshold = alt.Chart(pd.DataFrame({"risco": [50]})).mark_rule(color="#d97706", strokeDash=[4, 4]).encode(y="risco:Q")
    return (line + threshold).properties(height=245).configure_view(strokeWidth=0)


def render_import_page(detailed_view: bool) -> None:
    back_col, _ = st.columns([2, 5])
    with back_col:
        st.markdown('<div class="back-btn">', unsafe_allow_html=True)
        if st.button("← Voltar ao painel Retain", key="btn_back_to_radar"):
            st.session_state.page = "radar"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="eyebrow">Sistema · Gestão de Dados</div>', unsafe_allow_html=True)
    st.title("Importar base de dados")
    st.markdown(
        '<div class="subtitle">Carregue uma planilha Excel (.xlsx) contendo o histórico de atendimento, '
        'clientes, pesquisas NPS e situação contratual para alimentar o Retain.</div>',
        unsafe_allow_html=True,
    )

    current_path = get_active_data_path()
    current_name = st.session_state.get("active_dataset_name", current_path.name)
    is_custom = current_path != DATA_PATH

    st.markdown(
        f"""
        <div class="status-strip" role="status" aria-label="Estado da base atual">
          <span class="status-item"><span class="status-dot"></span>Base ativa atual: <strong>{current_name}</strong></span>
          <span class="status-item">{'Base customizada' if is_custom else 'Base padrão do sistema (INOVAAPPS)'}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if is_custom:
        if st.button("Restaurar base padrão original (INOVAAPPS)", icon=":material/restart_alt:"):
            set_active_dataset(None)
            st.session_state.active_dataset_name = "INOVAAPPS_base_de_dados.xlsx"
            st.toast("Base padrão restaurada com sucesso!", icon=":material/check_circle:")
            st.rerun()

    st.markdown('<div class="import-box">', unsafe_allow_html=True)
    st.markdown('<div class="import-box-title">Upload de nova planilha</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="small">Selecione ou arraste um arquivo <code>.xlsx</code> estruturado com as abas obrigatórias:</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="margin: 0.6rem 0 1rem;">
          <span class="tag-sheet">📁 clientes</span>
          <span class="tag-sheet">📁 atendimento_mensal</span>
          <span class="tag-sheet">📁 pesquisas_nps</span>
          <span class="tag-sheet">📁 situacao_clientes</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Selecione a planilha Excel",
        type=["xlsx"],
        key="uploader_excel",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        is_valid, errors, summary = validate_dataset(uploaded_file)
        if not is_valid:
            st.error("A planilha enviada não atende aos requisitos mínimos do sistema:")
            for err in errors:
                st.markdown(f"- ❌ {err}")
            st.info(
                "Dica: Certifique-se de que a planilha contenha as 4 abas obrigatórias "
                "(**clientes**, **atendimento_mensal**, **pesquisas_nps** e **situacao_clientes**) "
                "com a chave `cliente_id`."
            )
        else:
            st.success("✓ Planilha validada com sucesso! As 4 abas obrigatórias e os campos essenciais foram identificados.")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total de clientes", summary.get("total_clients", 0))
            m2.metric("Clientes ativos", summary.get("active_clients", 0))
            m3.metric("Clientes cancelados", summary.get("canceled_clients", 0))
            m4.metric("MRR Total", brl(summary.get("total_mrr", 0.0)))

            st.markdown("#### Pré-visualização das abas")
            excel_preview = pd.ExcelFile(uploaded_file)
            p_tabs = st.tabs(["1 · Clientes", "2 · Atendimento Mensal", "3 · Pesquisas NPS", "4 · Situação"])
            with p_tabs[0]:
                st.dataframe(pd.read_excel(excel_preview, sheet_name="clientes").head(8), hide_index=True, width="stretch")
            with p_tabs[1]:
                st.dataframe(pd.read_excel(excel_preview, sheet_name="atendimento_mensal").head(8), hide_index=True, width="stretch")
            with p_tabs[2]:
                st.dataframe(pd.read_excel(excel_preview, sheet_name="pesquisas_nps").head(8), hide_index=True, width="stretch")
            with p_tabs[3]:
                st.dataframe(pd.read_excel(excel_preview, sheet_name="situacao_clientes").head(8), hide_index=True, width="stretch")

            st.markdown('<div class="stitch-pill-btn" style="max-width: 420px; margin-top: 1.5rem;">', unsafe_allow_html=True)
            if st.button("Confirmar e aplicar base ao sistema  →", key="btn_confirm_import", type="primary"):
                save_dir = Path(__file__).parent / "tmp"
                save_dir.mkdir(parents=True, exist_ok=True)
                save_path = save_dir / f"imported_{uploaded_file.name}"
                save_path.write_bytes(uploaded_file.getvalue())
                set_active_dataset(save_path)
                st.session_state.active_dataset_name = uploaded_file.name
                st.session_state.just_imported = True
                st.session_state.page = "radar"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)


styles()

if "page" not in st.session_state:
    st.session_state.page = "radar" if st.query_params.get("view") == "radar" else "landing"

if st.query_params.get("view") == "radar" and st.session_state.page == "landing":
    st.session_state.page = "radar"

if st.session_state.page == "landing":
    render_landing_page()
    st.stop()

with st.sidebar:
    st.markdown("### Retain · by bolt")
    page_options = ["Início", "Painel Retain", "Importar base de dados"]
    current_page_idx = {"landing": 0, "radar": 1, "importar_base": 2}.get(st.session_state.page, 1)
    selected_nav = st.radio(
        "Páginas do sistema",
        page_options,
        index=current_page_idx,
        label_visibility="collapsed",
    )
    if selected_nav == "Início" and st.session_state.page != "landing":
        st.session_state.page = "landing"
        st.query_params["view"] = "landing"
        st.rerun()
    elif selected_nav == "Painel Retain" and st.session_state.page != "radar":
        st.session_state.page = "radar"
        st.query_params["view"] = "radar"
        st.rerun()
    elif selected_nav == "Importar base de dados" and st.session_state.page != "importar_base":
        st.session_state.page = "importar_base"
        st.rerun()

    st.markdown("---")
    st.markdown("### Preferências")
    reading_mode = st.segmented_control(
        "Nível de detalhe",
        ["Essencial", "Detalhado"],
        default="Essencial",
        help="A visão essencial recolhe explicações; nenhuma informação é removida.",
    )
    detailed_view = reading_mode == "Detalhado"
    st.caption("A interface lembra esta escolha durante a sessão.")
    with st.expander("Ajuda rápida"):
        st.markdown(
            "**Fila:** clientes ordenados pela perda financeira potencial.  \n"
            "**Risco:** intensidade dos sinais, de 0 a 100.  \n"
            "**Valor exposto:** risco × mensalidade.  \n"
            "Use os botões **Entenda** e **Como funciona?** para abrir explicações sem sair da tela."
        )

if st.session_state.page == "importar_base":
    render_import_page(detailed_view)
    st.stop()

# Header alinhado à identidade aprovada no Stitch.
logo_col, head_col1, head_col2 = st.columns([0.32, 3, 1.4], vertical_alignment="center")
with logo_col:
    st.image(str(LOGO_PATH), width=58)
with head_col1:
    st.markdown('<div class="eyebrow">Retain <span style="color:#94a3b8">· by bolt</span></div>', unsafe_allow_html=True)
    st.title("Da base à próxima ação")
    optional_caption(
        "Entenda o risco, veja sua direção e aja primeiro onde há mais valor exposto.",
        detailed_view,
    )
with head_col2:
    st.markdown('<div class="stitch-pill-btn">', unsafe_allow_html=True)
    if st.button("Importar base de dados  →", key="btn_header_import", type="primary"):
        st.session_state.page = "importar_base"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("just_imported"):
    st.toast("Base de dados importada e aplicada com sucesso!", icon=":material/check_circle:")
    st.session_state.just_imported = False

current_path = get_active_data_path()
current_name = st.session_state.get("active_dataset_name", current_path.name)
is_custom = current_path != DATA_PATH

st.markdown(
    f"""
    <div class="status-strip" role="status" aria-label="Estado do sistema">
      <span class="status-item"><span class="status-dot"></span>Base: <strong>{current_name}</strong></span>
      <span class="status-item">{'Base customizada' if is_custom else 'Base padrão'}</span>
      <span class="status-item">Modelo demonstrativo</span>
    </div>
    """,
    unsafe_allow_html=True,
)

evidence = recommended_weight_evidence(PRESET_SAAS)
recommended = {item.module_id: item.recommended_weight for item in evidence}
mode = st.segmented_control(
    "Como deseja definir os pesos?",
    ["Recomendado pela base", "Ajustado pelo gestor"],
    default="Recomendado pela base",
    help="Use a recomendação histórica ou simule o julgamento do gestor.",
)

if mode == "Recomendado pela base":
    chosen = recommended
    top = evidence[0]
    detail_badge(
        f"Entenda o maior peso · {top.module_name} {top.recommended_weight:.1f}%",
        f"**{top.module_name}** recebeu o maior peso porque foi o fator que mais separou "
        "clientes cancelados de ativos nesta base histórica. Isso é evidência exploratória, não causalidade.",
    )
else:
    optional_caption("A soma é normalizada automaticamente para 100%.", detailed_view)
    if st.button("Restaurar pesos recomendados", icon=":material/restart_alt:"):
        for item in evidence:
            st.session_state[f"custom-{item.module_id}"] = int(round(item.recommended_weight))
        st.rerun()
    cols = st.columns(6)
    chosen = {}
    for column, item in zip(cols, evidence):
        with column:
            chosen[item.module_id] = st.slider(item.module_name, 0, 50, int(round(item.recommended_weight)), 1, key=f"custom-{item.module_id}")
    largest_change = max(evidence, key=lambda item: abs(chosen[item.module_id] - round(item.recommended_weight)))
    delta = chosen[largest_change.module_id] - round(largest_change.recommended_weight)
    if delta == 0:
        manager_story = "o gestor está usando a recomendação histórica arredondada. Mova um peso para comparar cenários."
    else:
        direction = "aumentou" if delta > 0 else "reduziu"
        manager_story = f"o gestor {direction} a importância de {largest_change.module_name} em {abs(delta):.0f} pontos frente à recomendação arredondada."
    detail_badge(
        "Ver impacto do ajuste",
        f"**Leitura do Retain:** {manager_story} A fila e a previsão foram recalculadas.",
    )

settings = {module_id: {"active": weight > 0, "weight": weight} for module_id, weight in chosen.items()}
if not any(item["active"] for item in settings.values()):
    st.error("Ative pelo menos um fator para calcular o risco.", icon=":material/error:")
    st.stop()
profiles = build_profiles(PRESET_SAAS, settings)
risky = at_risk(profiles)
if "selected_client_id" not in st.session_state or not any(p.client_id == st.session_state.selected_client_id for p in profiles):
    st.session_state.selected_client_id = (risky or profiles)[0].client_id
selected = next(p for p in profiles if p.client_id == st.session_state.selected_client_id)
forecast = forecast_client_risk(selected.client_id, PRESET_SAAS, settings)

k1, k2, k3 = st.columns(3)
k1.metric("Clientes ativos", len(profiles), help="Clientes ativos monitorados nesta base.")
k2.metric(
    "Alertas na fila",
    len(risky),
    f"{sum(p.risk_level == 'Alto' for p in risky)} de risco alto",
    help="Clientes acima do limiar de atenção e que pedem análise humana.",
)
k3.metric(
    "Valor exposto total",
    brl(sum(p.exposed_value for p in risky)),
    help="Soma de risco × mensalidade dos clientes na fila. Não é previsão de perda.",
)

queue_col, story_col = st.columns([0.76, 1.64], gap="large")
with queue_col:
    st.markdown('<div class="eyebrow">Quem atender primeiro</div>', unsafe_allow_html=True)
    st.subheader("Fila de prioridade")
    detail_badge(
        "Por que esta ordem?",
        "A fila usa **valor exposto = score de risco × mensalidade**. Assim, um risco moderado em uma conta "
        "de alto valor pode vir antes de um risco alto em uma conta menor. A ordem orienta; não decide pelo gestor.",
    )
    optional_caption("Ordenada por risco × mensalidade.", detailed_view)
    if risky:
        for index, profile in enumerate(sorted(risky, key=lambda p: p.exposed_value, reverse=True)[:7], 1):
            queue_card(profile, profile.client_id == selected.client_id, index)
    else:
        st.markdown(
            '<div class="empty-safe">Nenhum cliente está acima do limiar atual. Revise os pesos ou continue monitorando a base.</div>',
            unsafe_allow_html=True,
        )

with story_col:
    st.markdown('<div class="eyebrow">A história deste cliente</div>', unsafe_allow_html=True)
    st.subheader(f"Cliente {selected.client_id}")
    st.markdown(
        f'<span class="badge neutral">{selected.plan}</span>'
        f'<span class="badge neutral">{selected.segment}</span>'
        f'<span class="badge neutral">Mensalidade {brl(selected.economic_value)}</span>',
        unsafe_allow_html=True,
    )

    now_col, future_col, value_col = st.columns(3)
    now_col.metric(
        "Risco hoje",
        f"{selected.risk_score:.0f}/100",
        selected.risk_level,
        help="Intensidade combinada dos sinais deste cliente; não é probabilidade de churn.",
    )
    forecast_delta = f"{forecast.change:+.1f} pontos em 3 meses"
    future_col.metric(
        "Projeção em 3 meses",
        f"{forecast.future_score:.0f}/100",
        forecast_delta,
        delta_color="inverse",
        help="Extensão linear da tendência recente; não é promessa nem probabilidade confirmada.",
    )
    value_col.metric(
        "Valor exposto",
        brl(selected.exposed_value),
        f"{selected.risk_score:.0f}% × {brl(selected.economic_value)}",
        delta_color="off",
        help="Indicador de prioridade financeira, calculado como risco × mensalidade.",
    )

    if forecast.change > 3:
        headline = f"Se a tendência continuar, o risco pode subir de {forecast.current_score:.0f} para {forecast.future_score:.0f} em três meses."
    elif forecast.change < -3:
        headline = f"A tendência aponta melhora: de {forecast.current_score:.0f} para {forecast.future_score:.0f} em três meses."
    else:
        headline = f"A tendência indica estabilidade próxima de {forecast.future_score:.0f} pontos nos próximos três meses."
    st.markdown(f'<div class="story story-blue"><div class="big">{headline}</div></div>', unsafe_allow_html=True)
    detail_badge(
        "Limites da projeção",
        "A projeção é uma extensão linear demonstrativa dos sinais recentes. Ela **não** é uma promessa, "
        "uma relação causal nem uma probabilidade confirmada de cancelamento.",
    )
    st.altair_chart(forecast_chart(selected, forecast), width="stretch")

    factors_col, action_col = st.columns([1, 1], gap="large")
    with factors_col:
        st.markdown('<div class="eyebrow">Por que este alerta</div>', unsafe_allow_html=True)
        for module in sorted(selected.module_results, key=lambda item: item.score * selected.module_weights.get(item.id, 0), reverse=True)[:3]:
            weight = selected.module_weights.get(module.id, 0)
            st.markdown(f'<div class="factor"><span>{module.nome}</span><span>{module.score:.0f}/100 · peso {weight:.0f}%</span></div>', unsafe_allow_html=True)
            st.progress(int(module.score))
        detail_badge(
            "Ler diagnóstico",
            selected.explanation
            + "\n\n**Score** mede a intensidade do sinal neste cliente. **Peso** mede a importância geral do fator no modelo.",
        )
    with action_col:
        st.markdown('<div class="eyebrow">O que fazer agora</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="action"><div class="action-title">{selected.recommendation}</div></div>', unsafe_allow_html=True)
        detail_badge("Por que esta ação?", selected.recommendation_reason)
        if "action_log" not in st.session_state:
            st.session_state.action_log = []
        action_key = (selected.client_id, selected.recommendation)
        action_registered = action_key in st.session_state.action_log
        if st.button(
            "Ação registrada" if action_registered else "Registrar ação",
            type="secondary" if action_registered else "primary",
            width="stretch",
            disabled=action_registered,
            icon=":material/check:" if action_registered else ":material/add_task:",
        ):
            st.session_state.action_log.append(action_key)
            st.toast("Ação registrada. O acompanhamento já pode começar.", icon=":material/check_circle:")
            st.rerun()
        if action_registered and st.button("Desfazer registro", key=f"undo-{selected.client_id}", width="stretch"):
            st.session_state.action_log.remove(action_key)
            st.toast("Registro desfeito.")
            st.rerun()

st.markdown("---")
show_methodology = st.toggle(
    "Ver transparência e metodologia",
    value=detailed_view,
    help="Abre os cálculos, tabelas, limitações e a explicação completa dos pesos.",
)
if not show_methodology:
    st.caption("Cálculos, fontes e limitações continuam disponíveis neste controle.")
    st.stop()

st.markdown('<div class="eyebrow">Transparência e metodologia</div>', unsafe_allow_html=True)
st.subheader("Como os dados viraram pesos")
detail_badge(
    "Origem da recomendação",
    "O peso não é uma opinião da IA. Ele nasce de uma comparação exploratória entre os "
    "**58 clientes ativos** e os **22 cancelados** da base fictícia.",
)

step_1, step_2, step_3 = st.columns(3)
with step_1:
    st.markdown(
        '<div class="step-card"><span class="step-number">1</span>'
        '<div class="step-title">Transformamos os dados em scores</div>'
        '<div class="step-copy">Cada sinal — como queda de uso, SLA ou NPS — é convertido em risco de 0 a 100. '
        '<strong>0</strong> significa pouco sinal de risco; <strong>100</strong>, sinal muito forte.</div></div>',
        unsafe_allow_html=True,
    )
with step_2:
    st.markdown(
        '<div class="step-card"><span class="step-number">2</span>'
        '<div class="step-title">Comparamos os dois grupos</div>'
        '<div class="step-copy">Calculamos o score médio dos ativos e o score médio dos cancelados. '
        'A diferença é: <strong>média dos cancelados − média dos ativos</strong>.</div></div>',
        unsafe_allow_html=True,
    )
with step_3:
    st.markdown(
        '<div class="step-card"><span class="step-number">3</span>'
        '<div class="step-title">A diferença vira peso</div>'
        '<div class="step-copy">Somamos as diferenças dos seis fatores. A parte que cada fator representa '
        'nessa soma vira seu peso recomendado. Todos os pesos juntos somam <strong>100%</strong>.</div></div>',
        unsafe_allow_html=True,
    )

total_difference = sum(max(item.difference, 1.0) for item in evidence)
overview_1, overview_2, overview_3, overview_4 = st.columns(4)
overview_1.metric("Clientes analisados", "80", "base fictícia", delta_color="off")
overview_2.metric("Ativos", "58", "grupo de comparação", delta_color="off")
overview_3.metric("Cancelados", "22", "grupo de referência", delta_color="off")
overview_4.metric("Soma das diferenças", f"{total_difference:.1f} pts", "base para dividir os pesos", delta_color="off")

factor_details = {
    "adocao": {
        "measures": "Perda de uso e baixo aproveitamento da plataforma",
        "raw": "uso_plataforma_pct",
        "meaning": "Quanto o comportamento de uso aponta afastamento do produto.",
    },
    "operacao": {
        "measures": "Deterioração da entrega e da qualidade operacional",
        "raw": "pct_sla_cumprido; tempo_medio_resolucao_h",
        "meaning": "Quanto o serviço está ficando mais lento ou descumprindo o combinado.",
    },
    "suporte": {
        "measures": "Fricção, reincidência e gravidade no suporte",
        "raw": "chamados_criticos; chamados_reabertos; reclamacoes_formais",
        "meaning": "Quanto os problemas do cliente são graves, repetidos ou continuam sem solução.",
    },
    "satisfacao": {
        "measures": "Insatisfação declarada ou silêncio do cliente",
        "raw": "respondeu; nota_nps; classificacao_nps",
        "meaning": "Quanto o NPS e a ausência de resposta sugerem distanciamento.",
    },
    "cs": {
        "measures": "Perda da cadência de relacionamento com Customer Success",
        "raw": "reunioes_previstas; reunioes_realizadas",
        "meaning": "Quanto reuniões previstas deixaram de acontecer.",
    },
    "financeiro": {
        "measures": "Pressão financeira antes do cancelamento",
        "raw": "dias_atraso_pagamento",
        "meaning": "Quanto o atraso de pagamento sinaliza dificuldade ou menor intenção de continuar.",
    },
}

visual_tab, table_tab, calculation_tab = st.tabs(
    ["1 · Resumo visual", "2 · Tabela detalhada", "3 · Conta passo a passo"]
)

with visual_tab:
    st.markdown("#### O que mais separou cancelados de ativos?")
    st.caption(
        "As barras são scores médios de risco de 0 a 100 — não são percentuais de cancelamento. "
        "Quanto maior a distância entre vermelho e azul, mais aquele fator ajudou a diferenciar os grupos."
    )
    comparison_rows = []
    factor_order = [item.module_name for item in evidence]
    for item in evidence:
        comparison_rows.extend([
            {"Fator": item.module_name, "Grupo": "Ativos", "Score médio": item.active_average},
            {"Fator": item.module_name, "Grupo": "Cancelados", "Score médio": item.canceled_average},
        ])
    comparison = pd.DataFrame(comparison_rows)
    comparison_chart = (
        alt.Chart(comparison)
        .mark_bar(cornerRadiusEnd=4)
        .encode(
            y=alt.Y("Fator:N", sort=factor_order, title=None),
            yOffset="Grupo:N",
            x=alt.X("Score médio:Q", scale=alt.Scale(domain=[0, 100]), title="Score médio de risco (0 a 100)"),
            color=alt.Color(
                "Grupo:N",
                scale=alt.Scale(domain=["Ativos", "Cancelados"], range=["#2457d6", "#c63c3c"]),
                title=None,
            ),
            tooltip=["Fator:N", "Grupo:N", alt.Tooltip("Score médio:Q", format=".1f")],
        )
        .properties(height=330)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(comparison_chart, width="stretch")

    st.markdown("#### Resultado: distribuição recomendada dos 100%")
    weight_chart_data = pd.DataFrame([
        {"Fator": item.module_name, "Peso": item.recommended_weight, "Rótulo": f"{item.recommended_weight:.1f}%"}
        for item in evidence
    ])
    bars = alt.Chart(weight_chart_data).mark_bar(cornerRadiusEnd=5, color="#2457d6").encode(
        y=alt.Y("Fator:N", sort=factor_order, title=None),
        x=alt.X("Peso:Q", scale=alt.Scale(domain=[0, 25]), title="Peso recomendado (%)"),
        tooltip=["Fator:N", alt.Tooltip("Peso:Q", format=".1f")],
    )
    labels = alt.Chart(weight_chart_data).mark_text(align="left", dx=5, fontWeight="bold").encode(
        y=alt.Y("Fator:N", sort=factor_order), x="Peso:Q", text="Rótulo:N"
    )
    st.altair_chart((bars + labels).properties(height=270).configure_view(strokeWidth=0), width="stretch")

with table_tab:
    st.markdown("#### Dicionário completo da recomendação")
    st.caption(
        "O panorama foi separado em duas tabelas para evitar rolagem lateral: primeiro, de onde vêm os fatores; "
        "depois, como os números viram pesos. Passe o cursor sobre os títulos para ver as explicações."
    )
    source_rows = []
    math_rows = []
    for position, item in enumerate(evidence, 1):
        detail = factor_details[item.module_id]
        source_rows.append({
            "Ordem": position,
            "Fator": item.module_name,
            "O que mede": detail["measures"],
            "Sinais calculados": ", ".join(item.source_signals),
            "Colunas da base": detail["raw"],
        })
        math_rows.append({
            "Fator": item.module_name,
            "Ativos (0–100)": item.active_average,
            "Cancelados (0–100)": item.canceled_average,
            "Diferença": item.difference,
            "Conta do peso": f"{max(item.difference, 1.0):.1f} ÷ {total_difference:.1f} × 100",
            "Peso": item.recommended_weight / 100,
        })

    st.markdown("##### A. Quais dados alimentam cada fator?")
    st.dataframe(
        pd.DataFrame(source_rows),
        hide_index=True,
        width="stretch",
        height=360,
        column_config={
            "Ordem": st.column_config.NumberColumn("#", help="Posição do maior para o menor peso", width="small"),
            "Fator": st.column_config.TextColumn("Fator", help="Grupo de sinais que contam a mesma parte da história", width="medium"),
            "O que mede": st.column_config.TextColumn("O que este fator mede", width="large"),
            "Sinais calculados": st.column_config.TextColumn("Sinais usados pelo motor", help="Indicadores de risco produzidos a partir das colunas originais", width="large"),
            "Colunas da base": st.column_config.TextColumn("Colunas originais", help="Campos de entrada encontrados no Excel", width="large"),
        },
    )

    st.markdown("##### B. Como a comparação vira peso?")
    st.dataframe(
        pd.DataFrame(math_rows),
        hide_index=True,
        width="stretch",
        height=280,
        column_config={
            "Fator": st.column_config.TextColumn("Fator", width="medium"),
            "Ativos (0–100)": st.column_config.NumberColumn("Média dos ativos", help="Score médio de risco do fator entre os 58 ativos; não é porcentagem de churn", format="%.1f"),
            "Cancelados (0–100)": st.column_config.NumberColumn("Média dos cancelados", help="Score médio de risco do fator entre os 22 cancelados; não é porcentagem de churn", format="%.1f"),
            "Diferença": st.column_config.NumberColumn("Diferença", help="Média dos cancelados menos média dos ativos", format="+%.1f"),
            "Conta do peso": st.column_config.TextColumn("Conta do peso", width="medium"),
            "Peso": st.column_config.NumberColumn("Peso recomendado", help="Parte deste fator na soma de todas as diferenças", format="percent"),
        },
    )
    st.info(
        "Importante: 51,2 em Adoção não quer dizer que 51,2% dos clientes cancelaram. "
        "Quer dizer que o score médio de risco de Adoção dos cancelados foi 51,2 em uma escala de 0 a 100."
    )

    st.markdown("#### Explicação fator por fator")
    for item in evidence:
        detail = factor_details[item.module_id]
        with st.expander(f"{item.module_name} — por que recebeu {item.recommended_weight:.1f}%?"):
            st.write(detail["meaning"])
            st.write(f"**Dados de entrada:** {detail['raw']}.")
            st.write(f"**Sinais de risco calculados:** {', '.join(item.source_signals)}.")
            st.write(
                f"O grupo ativo teve média **{item.active_average:.1f}/100** e o grupo cancelado, "
                f"**{item.canceled_average:.1f}/100**. A diferença observada foi "
                f"**aproximadamente {item.canceled_average:.1f} − {item.active_average:.1f} = {item.difference:.1f} pontos**. "
                "A conta usa as médias completas; os valores exibidos estão arredondados."
            )
            st.write(
                f"Essa diferença representa **{max(item.difference, 1.0):.1f} ÷ {total_difference:.1f} × 100 "
                f"= {item.recommended_weight:.1f}%** da força de separação observada."
            )

with calculation_tab:
    example = evidence[0]
    st.markdown(f"#### Exemplo completo: {example.module_name}")
    st.markdown(
        f'<div class="formula-box"><div class="formula-main">'
        f'1. Diferença ≈ {example.canceled_average:.1f} − {example.active_average:.1f} = {example.difference:.1f} pontos'
        f'</div><div class="formula-note">score médio dos cancelados menos score médio dos ativos; cálculo feito antes do arredondamento</div></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="formula-box"><div class="formula-main">'
        f'2. Peso = {max(example.difference, 1.0):.1f} ÷ {total_difference:.1f} × 100 = {example.recommended_weight:.1f}%'
        f'</div><div class="formula-note">diferença deste fator dividida pela soma das diferenças dos seis fatores</div></div>',
        unsafe_allow_html=True,
    )
    st.write(
        f"Em palavras: de cada 100 pontos de importância distribuídos pelo sistema, "
        f"**{example.recommended_weight:.1f} pontos vão para {example.module_name}**, porque esse fator apresentou "
        f"a maior distância entre quem continuou ativo e quem cancelou nesta amostra."
    )
    st.markdown("#### O que esta análise pode e não pode afirmar")
    limitation_1, limitation_2 = st.columns(2)
    with limitation_1:
        st.success(
            "**Pode afirmar:** nesta base, determinados fatores apareceram com scores de risco maiores entre "
            "os cancelados. Isso ajuda a criar uma primeira recomendação transparente de pesos."
        )
    with limitation_2:
        st.warning(
            "**Não pode afirmar ainda:** que esses pesos causam cancelamento, que funcionarão igual em outra empresa "
            "ou que o score é uma probabilidade real de churn."
        )
    st.caption(
        "Método atual: para cada cliente, usamos o último período disponível; depois comparamos as médias dos grupos. "
        "É uma análise exploratória da própria amostra, sem validação externa. Em produção, os pesos devem ser testados "
        "em dados futuros e acompanhados por taxa de acerto, falsos positivos e resultados das ações de retenção."
    )
