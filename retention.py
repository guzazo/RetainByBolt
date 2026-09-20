"""Motor declarativo e agnóstico de risco de retenção.

As classes Sinal, Modulo e PerfilDeRisco não conhecem Excel, SLA, NPS ou MRR.
Elas recebem apenas valores normalizados (0-100), disponibilidade e pesos.
O adaptador INOVAAPPS, no fim do arquivo, é a única camada que conhece a fonte.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd


DATA_PATH = Path(__file__).parent / "data" / "INOVAAPPS_base_de_dados.xlsx"
ACTIVE_DATA_PATH: Path | str | None = None
PRESET_SAAS = "Preset SaaS B2B"
PRESET_B2C = "Preset Assinatura B2C"

REQUIRED_SHEETS = {
    "clientes": ["cliente_id", "plano", "segmento", "valor_mensal"],
    "atendimento_mensal": ["cliente_id", "mes_ref", "uso_plataforma_pct"],
    "pesquisas_nps": ["cliente_id", "mes_ref", "respondeu"],
    "situacao_clientes": ["cliente_id", "situacao"],
}


def get_active_data_path() -> Path:
    if ACTIVE_DATA_PATH is not None:
        return Path(ACTIVE_DATA_PATH)
    return DATA_PATH


def set_active_dataset(custom_path: Path | str | None) -> None:
    """Atualiza o arquivo de dados ativo e limpa caches do motor."""
    global ACTIVE_DATA_PATH
    ACTIVE_DATA_PATH = Path(custom_path) if custom_path else None
    load_source_data.cache_clear()
    recommended_weight_evidence.cache_clear()


def validate_dataset(file_or_path: Path | str | object) -> tuple[bool, list[str], dict[str, object]]:
    """Valida se o arquivo Excel possui as abas e colunas necessárias para o motor."""
    errors: list[str] = []
    summary: dict[str, object] = {}
    try:
        excel_file = pd.ExcelFile(file_or_path)
        sheet_names = excel_file.sheet_names
        for sheet, req_cols in REQUIRED_SHEETS.items():
            if sheet not in sheet_names:
                errors.append(f"Aba obrigatória ausente: '{sheet}'")
            else:
                df = pd.read_excel(excel_file, sheet_name=sheet, nrows=5)
                missing_cols = [col for col in req_cols if col not in df.columns]
                if missing_cols:
                    errors.append(f"Aba '{sheet}' está sem as colunas: {', '.join(missing_cols)}")

        if not errors:
            df_clients = pd.read_excel(excel_file, sheet_name="clientes")
            df_status = pd.read_excel(excel_file, sheet_name="situacao_clientes")
            df_monthly = pd.read_excel(excel_file, sheet_name="atendimento_mensal")
            summary = {
                "total_clients": len(df_clients),
                "active_clients": int((df_status["situacao"] == "Ativo").sum()) if "situacao" in df_status.columns else len(df_clients),
                "canceled_clients": int((df_status["situacao"] == "Cancelado").sum()) if "situacao" in df_status.columns else 0,
                "total_mrr": float(df_clients["valor_mensal"].sum()) if "valor_mensal" in df_clients.columns else 0.0,
                "months_count": len(df_monthly["mes_ref"].unique()) if "mes_ref" in df_monthly.columns else 0,
            }
            return True, [], summary
        return False, errors, summary
    except Exception as exc:
        return False, [f"Erro ao processar planilha Excel: {str(exc)}"], summary


def _clip(value: float | None) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(np.clip(value, 0, 100))


def normalize_weights(weights: Mapping[str, float]) -> dict[str, float]:
    """Normaliza pesos positivos; se todos forem zero, distribui igualmente."""
    if not weights:
        return {}
    clean = {key: max(float(value), 0.0) for key, value in weights.items()}
    total = sum(clean.values())
    if total == 0:
        return {key: 100.0 / len(clean) for key in clean}
    return {key: value * 100.0 / total for key, value in clean.items()}


@dataclass(frozen=True)
class Sinal:
    """Uma evidência genérica já convertida para risco entre 0 e 100."""

    id: str
    nome: str
    peso_configurado: float
    ativo: bool = True
    valor_normalizado: float | None = None
    qualidade_dado: float = 1.0
    evidencia: str = ""

    @property
    def disponivel(self) -> bool:
        return self.ativo and self.valor_normalizado is not None


@dataclass(frozen=True)
class ResultadoModulo:
    id: str
    nome: str
    score: float
    cobertura: float
    qualidade: float
    sinais_disponiveis: int
    sinais_configurados: int
    pesos_redistribuidos: Mapping[str, float]
    evidencias: tuple[str, ...]


@dataclass(frozen=True)
class Modulo:
    """Agrupa sinais e redistribui pesos somente entre os disponíveis."""

    id: str
    nome: str
    peso_configurado: float
    sinais: tuple[Sinal, ...]
    ativo: bool = True

    def calcular(self) -> ResultadoModulo | None:
        configurados = [s for s in self.sinais if s.ativo]
        disponiveis = [s for s in configurados if s.disponivel]
        if not self.ativo or not configurados or not disponiveis:
            return None

        pesos_base = normalize_weights({s.id: s.peso_configurado for s in configurados})
        pesos_usados = normalize_weights({s.id: pesos_base[s.id] for s in disponiveis})
        score = sum(float(s.valor_normalizado) * pesos_usados[s.id] / 100 for s in disponiveis)
        cobertura = sum(pesos_base[s.id] for s in disponiveis) / 100
        qualidade = sum(s.qualidade_dado * pesos_usados[s.id] / 100 for s in disponiveis)
        evidencias = tuple(
            s.evidencia
            for s in sorted(disponiveis, key=lambda item: item.valor_normalizado or 0, reverse=True)
            if s.evidencia
        )
        return ResultadoModulo(
            id=self.id,
            nome=self.nome,
            score=round(score, 1),
            cobertura=round(cobertura, 4),
            qualidade=round(qualidade, 4),
            sinais_disponiveis=len(disponiveis),
            sinais_configurados=len(configurados),
            pesos_redistribuidos=pesos_usados,
            evidencias=evidencias,
        )


@dataclass(frozen=True)
class ResultadoRisco:
    score: float
    confianca: float
    cobertura: float
    sinais_ativos: int
    sinais_configurados: int
    pesos_redistribuidos: Mapping[str, float]
    modulos: tuple[ResultadoModulo, ...]


@dataclass(frozen=True)
class PerfilDeRisco:
    """Núcleo: combina módulos sem conhecer o significado de cada um."""

    modulos: tuple[Modulo, ...]
    suficiencia_historica: float = 1.0

    def calcular(self) -> ResultadoRisco:
        ativos = [m for m in self.modulos if m.ativo]
        if not ativos:
            return ResultadoRisco(0, 0, 0, 0, 0, {}, ())

        pesos_base = normalize_weights({m.id: m.peso_configurado for m in ativos})
        pares = [(m, m.calcular()) for m in ativos]
        disponiveis = [(m, r) for m, r in pares if r is not None]
        configurados = sum(len([s for s in m.sinais if s.ativo]) for m in ativos)
        if not disponiveis:
            return ResultadoRisco(0, 0, 0, 0, configurados, {}, ())

        pesos_usados = normalize_weights({m.id: pesos_base[m.id] for m, _ in disponiveis})
        score = sum(r.score * pesos_usados[m.id] / 100 for m, r in disponiveis)

        # Dados ausentes saem do score, mas derrubam cobertura/confiança.
        cobertura = sum(pesos_base[m.id] * r.cobertura / 100 for m, r in disponiveis)
        qualidade = sum(
            pesos_base[m.id] * r.cobertura * r.qualidade / 100 for m, r in disponiveis
        )
        confianca = qualidade * float(np.clip(self.suficiencia_historica, 0, 1))
        return ResultadoRisco(
            score=round(float(np.clip(score, 0, 100)), 1),
            confianca=round(confianca * 100, 1),
            cobertura=round(cobertura * 100, 1),
            sinais_ativos=sum(r.sinais_disponiveis for _, r in disponiveis),
            sinais_configurados=configurados,
            pesos_redistribuidos=pesos_usados,
            modulos=tuple(r for _, r in disponiveis),
        )


@dataclass(frozen=True)
class DefinicaoSinal:
    id: str
    nome: str
    peso: float


@dataclass(frozen=True)
class DefinicaoModulo:
    id: str
    nome: str
    peso: float
    sinais: tuple[DefinicaoSinal, ...]
    acao: str
    motivo: str


@dataclass(frozen=True)
class Preset:
    nome: str
    descricao: str
    unidade_valor: str
    modulos: tuple[DefinicaoModulo, ...]


@dataclass(frozen=True)
class WeightEvidence:
    module_id: str
    module_name: str
    recommended_weight: float
    active_average: float
    canceled_average: float
    difference: float
    source_signals: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class RiskForecast:
    actual_months: tuple[str, ...]
    actual_scores: tuple[float, ...]
    forecast_months: tuple[str, ...]
    forecast_scores: tuple[float, ...]
    current_score: float
    future_score: float
    change: float


PRESETS: dict[str, Preset] = {
    PRESET_SAAS: Preset(
        PRESET_SAAS,
        "Contratos recorrentes com operação, suporte e relacionamento de Customer Success.",
        "MRR",
        (
            DefinicaoModulo("operacao", "Operação", 30, (
                DefinicaoSinal("sla_tendencia", "Deterioração do SLA", 45),
                DefinicaoSinal("sla_nivel", "Nível atual do SLA", 30),
                DefinicaoSinal("resolucao", "Tempo de resolução", 25),
            ), "Plano de recuperação operacional", "SLA ou tempo de resolução deterioraram."),
            DefinicaoModulo("suporte", "Suporte", 20, (
                DefinicaoSinal("friccao_suporte", "Fricção de suporte", 100),
            ), "Análise de causa-raiz dos chamados", "Chamados e reclamações indicam fricção."),
            DefinicaoModulo("cs", "Engajamento de CS", 20, (
                DefinicaoSinal("reunioes_perdidas", "Reuniões não realizadas", 100),
            ), "Contato com sponsor e retomada da cadência", "A rotina de relacionamento perdeu força."),
            DefinicaoModulo("adocao", "Adoção", 15, (
                DefinicaoSinal("uso_tendencia", "Queda de uso", 60),
                DefinicaoSinal("uso_nivel", "Nível de utilização", 40),
            ), "Sessão de adoção técnica", "A utilização perdeu força."),
            DefinicaoModulo("satisfacao", "Satisfação", 10, (
                DefinicaoSinal("nps", "Sinal de NPS", 100),
            ), "Entrevista com o decisor", "A satisfação ou a resposta à pesquisa exige atenção."),
            DefinicaoModulo("financeiro", "Financeiro", 5, (
                DefinicaoSinal("atraso_pagamento", "Atraso de pagamento", 100),
            ), "Negociação financeira preventiva", "Há pressão de pagamento ou renovação."),
        ),
    ),
    PRESET_B2C: Preset(
        PRESET_B2C,
        "Microassinaturas priorizadas por frequência, recência, engajamento e renovação.",
        "valor mensal",
        (
            DefinicaoModulo("transacao", "Frequência transacional", 35, (
                DefinicaoSinal("frequencia_queda", "Queda de frequência", 70),
                DefinicaoSinal("frequencia_nivel", "Frequência atual", 30),
            ), "Campanha personalizada de reativação", "A frequência transacional caiu."),
            DefinicaoModulo("recencia", "Recência", 25, (
                DefinicaoSinal("recencia_atividade", "Recência de atividade", 100),
            ), "Lembrete de benefício não utilizado", "O cliente está se afastando do produto."),
            DefinicaoModulo("engajamento", "Engajamento no produto", 20, (
                DefinicaoSinal("engajamento_queda", "Queda abrupta de engajamento", 100),
            ), "Jornada de redescoberta de benefícios", "O uso dos benefícios perdeu intensidade."),
            DefinicaoModulo("renovacao", "Renovação e pagamento", 15, (
                DefinicaoSinal("falha_pagamento", "Pressão de pagamento", 100),
            ), "Recuperação preventiva de pagamento", "Há risco de falha na próxima cobrança."),
            DefinicaoModulo("friccao", "Fricção de serviço", 5, (
                DefinicaoSinal("friccao_servico", "Reembolsos ou contatos críticos", 100),
            ), "Compensação e resolução da fricção", "Ocorrências recentes prejudicaram a experiência."),
        ),
    ),
}

DEFAULT_WEIGHTS = {m.nome: m.peso for m in PRESETS[PRESET_SAAS].modulos}


def get_preset(name: str) -> Preset:
    return PRESETS[name]


@dataclass(frozen=True)
class ClientRiskProfile:
    client_id: str
    segment: str
    plan: str
    economic_value: float
    risk_score: float
    risk_level: str
    exposed_value: float
    priority_level: str
    confidence: float
    coverage: float
    active_signal_count: int
    configured_signal_count: int
    module_results: tuple[ResultadoModulo, ...]
    module_weights: Mapping[str, float]
    explanation: str
    recommendation: str
    recommendation_reason: str
    persistent: bool
    trajectories: Mapping[str, tuple[tuple[str, ...], tuple[float, ...]]]

    @property
    def mrr(self) -> float:
        return self.economic_value

    @property
    def exposed_mrr(self) -> float:
        return self.exposed_value


RiskProfile = ClientRiskProfile


def risk_level(score: float) -> str:
    if score >= 50:
        return "Alto"
    if score >= 30:
        return "Médio"
    return "Baixo"


def priority_level(value: float) -> str:
    if value >= 15_000:
        return "Crítica"
    if value >= 8_000:
        return "Alta"
    if value >= 3_000:
        return "Média"
    return "Monitorar"


@lru_cache(maxsize=1)
def load_source_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    path = get_active_data_path()
    clients = pd.read_excel(path, sheet_name="clientes")
    monthly = pd.read_excel(path, sheet_name="atendimento_mensal")
    nps = pd.read_excel(path, sheet_name="pesquisas_nps")
    status = pd.read_excel(path, sheet_name="situacao_clientes")
    monthly["mes_ref"] = pd.PeriodIndex(monthly["mes_ref"], freq="M")
    nps["mes_ref"] = pd.PeriodIndex(nps["mes_ref"], freq="M")
    return clients, monthly, nps, status


MONTHS_PT = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}


class InovaappsAdapter:
    """Traduz a planilha do desafio para sinais canônicos consumidos pelo núcleo."""

    def __init__(self) -> None:
        self.clients, self.monthly, self.nps, self.status = load_source_data()
        self.latest = self.monthly["mes_ref"].max()

    @staticmethod
    def _mean(frame: pd.DataFrame, column: str) -> float | None:
        if column not in frame or frame.empty:
            return None
        value = frame[column].mean()
        return None if pd.isna(value) else float(value)

    def _nps(self, client_id: str, as_of: pd.Period | None = None) -> tuple[float | None, str]:
        frame = self.nps[self.nps["cliente_id"] == client_id]
        if as_of is not None:
            frame = frame[frame["mes_ref"] <= as_of]
        frame = frame.sort_values("mes_ref").tail(2)
        if frame.empty:
            return None, "NPS sem dados"
        unanswered = int((frame["respondeu"] == 0).sum())
        if unanswered == 2:
            return 85.0, "silêncio nos dois últimos ciclos de NPS"
        if unanswered == 1 and frame.iloc[-1]["respondeu"] == 0:
            return 68.0, "silêncio no último ciclo de NPS"
        classification = str(frame.iloc[-1]["classificacao_nps"])
        note = frame.iloc[-1]["nota_nps"]
        scores = {"Detrator": 80.0, "Neutro": 35.0, "Promotor": 5.0}
        return scores.get(classification, 50.0), f"NPS {classification.lower()} ({int(note)})"

    def canonical_signals(self, client_id: str, as_of: pd.Period | None = None) -> tuple[dict[str, tuple[float | None, str]], dict[str, tuple[tuple[str, ...], tuple[float, ...]]], float]:
        reference = as_of or self.latest
        history = self.monthly[self.monthly["cliente_id"] == client_id].sort_values("mes_ref")
        history = history[history["mes_ref"] <= reference]
        recent = history[history["mes_ref"].between(reference - 2, reference)]
        previous = history[history["mes_ref"].between(reference - 5, reference - 3)]
        recent_usage, previous_usage = self._mean(recent, "uso_plataforma_pct"), self._mean(previous, "uso_plataforma_pct")
        recent_sla, previous_sla = self._mean(recent, "pct_sla_cumprido"), self._mean(previous, "pct_sla_cumprido")
        recent_resolution, previous_resolution = self._mean(recent, "tempo_medio_resolucao_h"), self._mean(previous, "tempo_medio_resolucao_h")
        usage_drop = None if recent_usage is None or previous_usage is None else previous_usage - recent_usage
        sla_drop = None if recent_sla is None or previous_sla is None else previous_sla - recent_sla
        resolution_change = None if recent_resolution is None or previous_resolution is None else recent_resolution - previous_resolution

        expected = recent["reunioes_previstas"].sum() if "reunioes_previstas" in recent else None
        done = recent["reunioes_realizadas"].sum() if "reunioes_realizadas" in recent else None
        missed = None if expected in (None, 0) or done is None else 1 - float(done) / float(expected)
        critical = self._mean(recent, "chamados_criticos")
        reopened = self._mean(recent, "chamados_reabertos")
        complaints = self._mean(recent, "reclamacoes_formais")
        if None in (critical, reopened, complaints):
            friction = None
        else:
            friction = _clip(critical / 3 * 35 + reopened / 3 * 35 + complaints / 2 * 30)
        payment = self._mean(recent, "dias_atraso_pagamento")
        payment_score = None if payment is None else _clip(payment / 15 * 100)
        nps_score, nps_evidence = self._nps(client_id, reference)

        def drop_score(drop: float | None, maximum: float) -> float | None:
            return None if drop is None else _clip(max(drop, 0) / maximum * 100)

        def low_score(level: float | None, reference: float, span: float) -> float | None:
            return None if level is None else _clip(max(reference - level, 0) / span * 100)

        values = {
            "uso_tendencia": (drop_score(usage_drop, 20), f"uso caiu {max(usage_drop or 0, 0):.0f} pontos"),
            "uso_nivel": (low_score(recent_usage, 70, 40), f"utilização recente em {recent_usage:.0f}%" if recent_usage is not None else ""),
            "sla_tendencia": (drop_score(sla_drop, 25), f"SLA caiu {max(sla_drop or 0, 0):.0f} pontos"),
            "sla_nivel": (low_score(recent_sla, 85, 35), f"SLA recente em {recent_sla:.0f}%" if recent_sla is not None else ""),
            "resolucao": (drop_score(resolution_change, 15), f"tempo de resolução aumentou {max(resolution_change or 0, 0):.0f}h"),
            "friccao_suporte": (friction, "chamados críticos, reaberturas ou reclamações aumentaram"),
            "reunioes_perdidas": (None if missed is None else _clip(missed * 100), f"{max(missed or 0, 0):.0%} das reuniões não ocorreram"),
            "nps": (nps_score, nps_evidence),
            "atraso_pagamento": (payment_score, f"média de {payment or 0:.0f} dias de atraso"),
            # O B2C usa proxies demonstrativos; em produção, outro adaptador entregaria os mesmos ids.
            "frequencia_queda": (drop_score(usage_drop, 20), f"frequência caiu {max(usage_drop or 0, 0):.0f} pontos"),
            "frequencia_nivel": (low_score(recent_usage, 70, 40), f"frequência recente em {recent_usage:.0f}%" if recent_usage is not None else ""),
            "recencia_atividade": (low_score(recent_usage, 75, 55), "recência estimada pela atividade recente"),
            "engajamento_queda": (drop_score(usage_drop, 25), f"engajamento caiu {max(usage_drop or 0, 0):.0f} pontos"),
            "falha_pagamento": (payment_score, "pressão de pagamento na renovação"),
            "friccao_servico": (friction, "ocorrências críticas recentes no atendimento"),
        }

        window = history.tail(6)
        months = tuple(MONTHS_PT[p.month] for p in window["mes_ref"])
        trajectories: dict[str, tuple[tuple[str, ...], tuple[float, ...]]] = {}
        if "uso_plataforma_pct" in window:
            trajectories["Atividade / uso"] = (months, tuple(float(v) for v in window["uso_plataforma_pct"].fillna(0)))
        if "pct_sla_cumprido" in window:
            trajectories["SLA cumprido"] = (months, tuple(float(v) for v in window["pct_sla_cumprido"].fillna(0)))
        return values, trajectories, min(len(window) / 6, 1.0)


def _instantiate_modules(
    preset: Preset,
    canonical: Mapping[str, tuple[float | None, str]],
    settings: Mapping[str, Mapping[str, float | bool]] | None,
) -> tuple[Modulo, ...]:
    modules: list[Modulo] = []
    settings = settings or {}
    for definition in preset.modulos:
        config = settings.get(definition.id, {})
        signals = tuple(
            Sinal(
                id=s.id,
                nome=s.nome,
                peso_configurado=s.peso,
                valor_normalizado=canonical.get(s.id, (None, ""))[0],
                evidencia=canonical.get(s.id, (None, ""))[1],
            )
            for s in definition.sinais
        )
        modules.append(Modulo(
            id=definition.id,
            nome=definition.nome,
            peso_configurado=float(config.get("weight", definition.peso)),
            ativo=bool(config.get("active", True)),
            sinais=signals,
        ))
    return tuple(modules)


@lru_cache(maxsize=4)
def recommended_weight_evidence(preset_name: str = PRESET_SAAS) -> tuple[WeightEvidence, ...]:
    """Recomenda pesos pela separação histórica entre ativos e cancelados.

    É uma análise exploratória interpretável, não uma probabilidade treinada de churn.
    """
    preset = get_preset(preset_name)
    adapter = InovaappsAdapter()
    canceled_ids = set(adapter.status.loc[adapter.status["situacao"] == "Cancelado", "cliente_id"])
    scores: dict[str, dict[str, list[float]]] = {
        module.id: {"active": [], "canceled": []} for module in preset.modulos
    }
    for customer in adapter.clients.itertuples():
        history = adapter.monthly[adapter.monthly["cliente_id"] == customer.cliente_id]
        if history.empty:
            continue
        reference = history["mes_ref"].max()
        canonical, _, history_ratio = adapter.canonical_signals(customer.cliente_id, reference)
        result = PerfilDeRisco(_instantiate_modules(preset, canonical, None), history_ratio).calcular()
        group = "canceled" if customer.cliente_id in canceled_ids else "active"
        for module in result.modulos:
            scores[module.id][group].append(module.score)

    raw_strengths: dict[str, float] = {}
    summaries: dict[str, tuple[float, float, float]] = {}
    for definition in preset.modulos:
        active_values = scores[definition.id]["active"]
        canceled_values = scores[definition.id]["canceled"]
        active_mean = float(np.mean(active_values)) if active_values else 0.0
        canceled_mean = float(np.mean(canceled_values)) if canceled_values else 0.0
        difference = canceled_mean - active_mean
        # Um piso pequeno evita apagar totalmente um fator com pouca separação nesta amostra.
        raw_strengths[definition.id] = max(difference, 1.0)
        summaries[definition.id] = (active_mean, canceled_mean, difference)

    normalized = normalize_weights(raw_strengths)
    evidence: list[WeightEvidence] = []
    for definition in preset.modulos:
        active_mean, canceled_mean, difference = summaries[definition.id]
        signal_names = tuple(signal.nome for signal in definition.sinais)
        direction = (
            f"cancelados ficaram {difference:.1f} pontos acima dos ativos"
            if difference > 0
            else "não separou bem cancelados de ativos nesta amostra"
        )
        evidence.append(WeightEvidence(
            module_id=definition.id,
            module_name=definition.nome,
            recommended_weight=round(normalized[definition.id], 1),
            active_average=round(active_mean, 1),
            canceled_average=round(canceled_mean, 1),
            difference=round(difference, 1),
            source_signals=signal_names,
            explanation=f"{definition.nome}: {direction}. Foram usados: {', '.join(signal_names)}.",
        ))
    return tuple(sorted(evidence, key=lambda item: item.recommended_weight, reverse=True))


def forecast_client_risk(
    client_id: str,
    preset_name: str = PRESET_SAAS,
    module_settings: Mapping[str, Mapping[str, float | bool]] | None = None,
) -> RiskForecast:
    """Projeção linear de três meses a partir dos seis scores observados mais recentes."""
    preset = get_preset(preset_name)
    adapter = InovaappsAdapter()
    periods = tuple(sorted(adapter.monthly.loc[adapter.monthly["cliente_id"] == client_id, "mes_ref"].unique()))
    usable = periods[5:]
    selected_periods = usable[-6:] if len(usable) >= 6 else usable
    scores: list[float] = []
    for period in selected_periods:
        canonical, _, history_ratio = adapter.canonical_signals(client_id, period)
        result = PerfilDeRisco(_instantiate_modules(preset, canonical, module_settings), history_ratio).calcular()
        scores.append(result.score)
    if not scores:
        return RiskForecast((), (), (), (), 0, 0, 0)
    x = np.arange(len(scores), dtype=float)
    slope, intercept = np.polyfit(x, np.asarray(scores), 1) if len(scores) > 1 else (0.0, scores[0])
    # A projeção parte do valor atual e prolonga somente a inclinação observada.
    future = tuple(round(float(np.clip(scores[-1] + slope * step, 0, 100)), 1) for step in range(1, 4))
    future_periods = tuple(selected_periods[-1] + index for index in range(1, 4))
    actual_labels = tuple(MONTHS_PT[p.month] for p in selected_periods)
    forecast_labels = tuple(MONTHS_PT[p.month] for p in future_periods)
    return RiskForecast(
        actual_months=actual_labels,
        actual_scores=tuple(scores),
        forecast_months=forecast_labels,
        forecast_scores=future,
        current_score=round(scores[-1], 1),
        future_score=future[-1],
        change=round(future[-1] - scores[-1], 1),
    )


def build_profiles(
    preset_name: str | Mapping[str, float] = PRESET_SAAS,
    module_settings: Mapping[str, Mapping[str, float | bool]] | None = None,
) -> list[ClientRiskProfile]:
    """Monta a demo. O primeiro argumento antigo (dict de pesos) segue compatível."""
    if isinstance(preset_name, Mapping):
        legacy = preset_name
        preset_name = PRESET_SAAS
        preset_legacy = get_preset(preset_name)
        module_settings = {
            m.id: {"active": True, "weight": legacy.get(m.nome, m.peso)} for m in preset_legacy.modulos
        }
    preset = get_preset(str(preset_name))
    adapter = InovaappsAdapter()
    active_ids = set(adapter.status.loc[adapter.status["situacao"] == "Ativo", "cliente_id"])
    profiles: list[ClientRiskProfile] = []

    for customer in adapter.clients[adapter.clients["cliente_id"].isin(active_ids)].itertuples():
        canonical, trajectories, history_ratio = adapter.canonical_signals(customer.cliente_id)
        modules = _instantiate_modules(preset, canonical, module_settings)
        result = PerfilDeRisco(modules, history_ratio).calcular()
        exposed = round(float(customer.valor_mensal) * result.score / 100, 2)
        definitions = {m.id: m for m in preset.modulos}
        contributions = sorted(
            result.modulos,
            key=lambda r: r.score * result.pesos_redistribuidos.get(r.id, 0),
            reverse=True,
        )
        top = contributions[0] if contributions else None
        definition = definitions.get(top.id) if top else None
        evidence = [] if top is None else [e for e in top.evidencias if e][:2]
        explanation = (
            "Dados insuficientes para formar um alerta."
            if top is None
            else f"{top.nome} é o principal vetor de risco: "
            + (" e ".join(evidence) if evidence else "score acima do padrão esperado")
            + "."
        )
        high_signals = sum(
            1 for m in modules for s in m.sinais
            if m.ativo and s.disponivel and float(s.valor_normalizado) >= 60
        )
        profiles.append(ClientRiskProfile(
            client_id=customer.cliente_id,
            segment=customer.segmento,
            plan=customer.plano,
            economic_value=float(customer.valor_mensal),
            risk_score=result.score,
            risk_level=risk_level(result.score),
            exposed_value=exposed,
            priority_level=priority_level(exposed),
            confidence=result.confianca,
            coverage=result.cobertura,
            active_signal_count=result.sinais_ativos,
            configured_signal_count=result.sinais_configurados,
            module_results=result.modulos,
            module_weights=result.pesos_redistribuidos,
            explanation=explanation,
            recommendation=definition.acao if definition else "Coletar mais dados",
            recommendation_reason=definition.motivo if definition else "A cobertura atual não permite recomendar uma intervenção.",
            persistent=high_signals >= 2,
            trajectories=trajectories,
        ))
    return sorted(profiles, key=lambda p: p.exposed_value, reverse=True)


def at_risk(profiles: list[ClientRiskProfile]) -> list[ClientRiskProfile]:
    return [profile for profile in profiles if profile.risk_level in {"Alto", "Médio"}]
