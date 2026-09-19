"""Dashboard executivo para presidência — Vértice Retail.
Rodar com: streamlit run prototipo/app.py
"""
import os
import sys

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from relatorio import gerar_relatorio
from simulador import curva_completa, simular

try:
    from streamlit_echarts import st_echarts
    ECHARTS_AVAILABLE = True
except Exception:
    st_echarts = None
    ECHARTS_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")


@st.cache_data
def carregar_dados():
    vendas = pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"])
    clientes = pd.read_csv(os.path.join(DATA_DIR, "clientes.csv"))
    marketing = pd.read_csv(os.path.join(DATA_DIR, "marketing.csv"))
    atendimento = pd.read_csv(os.path.join(DATA_DIR, "atendimento.csv"), parse_dates=["data_abertura", "data_fechamento"])
    estoque = pd.read_csv(os.path.join(DATA_DIR, "estoque.csv"))
    return {
        "vendas": vendas,
        "clientes": clientes,
        "marketing": marketing,
        "atendimento": atendimento,
        "estoque": estoque,
    }


def format_currency(value):
    if abs(value) >= 1_000_000:
        return f"R$ {value/1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"R$ {value/1_000:.1f}k"
    return f"R$ {value:,.0f}"


def format_pct(value):
    return f"{value:.1f}%"


def theme_tokens():
    streamlit_theme = getattr(st.context, "theme", {})
    theme_type = streamlit_theme.get("type") or streamlit_theme.get("base") or "light"
    if theme_type == "dark":
        return {
            "app_bg": "#0f172a", "surface": "#172033", "text": "#f8fafc",
            "muted": "#cbd5e1", "border": "#334155", "chart_bg": "#1e293b",
            "chart_text": "#f8fafc", "chart_shadow": "#020617", "grid": "rgba(255,255,255,0.18)",
        }
    return {
        "app_bg": "#ffffff", "surface": "#ffffff", "text": "#111827",
        "muted": "#4b5563", "border": "#e5e7eb", "chart_bg": "#e8eef7",
        "chart_text": "#1f2937", "chart_shadow": "#ffffff", "grid": "rgba(15,23,42,0.14)",
    }


@st.cache_data
def carregar_pedidos_marketplace():
    return pd.read_csv(os.path.join(DATA_DIR, "marketplace_pedidos.csv"))


def metric_card(label, value, subtitle, accent="#6d5ef5"):
    st.markdown(
        f"""
        <div style="
            background: var(--secondary-background-color); border: 1px solid var(--border-color); border-radius: 16px; padding: 16px 18px;
            min-height: 120px; margin-bottom: 12px; box-shadow: 0 3px 10px rgba(15,23,42,0.05);
        ">
            <div style="font-size: 11px; font-weight: 800; letter-spacing: 0.12em; color: {accent}; text-transform: uppercase; margin-bottom: 10px;">{label}</div>
            <div style="font-size: 30px; font-weight: 800; color: var(--text-color); margin-bottom: 6px;">{value}</div>
            <div style="font-size: 12px; color: var(--text-color); opacity: 0.72;">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def highlight_box(title, bullets, accent="#dbeafe"):
    items = "".join(f"<li>{b}</li>" for b in bullets)
    st.markdown(
        f"""
        <div style="background: color-mix(in srgb, {accent} 28%, var(--background-color)); border: 1px solid var(--border-color); border-left: 7px solid #2563eb; border-radius: 18px; padding: 18px 20px; min-height: 190px; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(15,23,42,0.08);">
            <div style="display: inline-block; background: var(--secondary-background-color); color: var(--text-color); border: 1px solid var(--border-color); font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; border-radius: 999px; padding: 8px 15px; font-size: 11px; margin-bottom: 14px; box-shadow: 0 2px 5px rgba(15,23,42,0.06);">{title}</div>
            <ul style="margin: 0; padding-left: 20px; line-height: 1.9; font-size: 15px; font-weight: 600; color: var(--text-color);">
                {items}
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_bar_chart(title, categories, values, color="#6d5ef5"):
    theme = theme_tokens()
    option = {
        "backgroundColor": theme["chart_bg"],
        "title": {"text": title, "left": "center", "top": 12, "textStyle": {"fontSize": 22, "fontWeight": "700", "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
        "grid": {"left": "8%", "right": "4%", "bottom": "14%", "top": "26%", "containLabel": True},
        "xAxis": {"type": "category", "data": categories, "axisLine": {"lineStyle": {"color": theme["chart_text"]}}, "axisLabel": {"color": theme["chart_text"], "fontSize": 14, "fontWeight": "600", "interval": 0, "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "yAxis": {"type": "value", "axisLine": {"lineStyle": {"color": theme["chart_text"]}}, "splitLine": {"lineStyle": {"color": theme["grid"]}}, "axisLabel": {"color": theme["chart_text"], "fontSize": 13, "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "series": [{
            "type": "bar",
            "barWidth": "52%",
            "data": values,
            "itemStyle": {"color": color, "borderRadius": [8, 8, 0, 0]},
            "label": {"show": True, "position": "top", "fontSize": 13, "fontWeight": "600", "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4},
        }],
    }
    return option


def build_pie_chart(title, data_dict, colors):
    theme = theme_tokens()
    option = {
        "backgroundColor": theme["chart_bg"],
        "title": {"text": title, "left": "center", "top": 12, "textStyle": {"fontSize": 22, "fontWeight": "700", "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "tooltip": {"trigger": "item", "formatter": "{b}: {d}%"},
        "legend": {"bottom": 0, "left": "center", "textStyle": {"fontSize": 13, "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "series": [{
            "type": "pie",
            "radius": ["42%", "72%"],
            "center": ["50%", "54%"],
            "avoidLabelOverlap": False,
            "itemStyle": {"borderRadius": 8, "borderColor": "#fff", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}: {d}%", "fontSize": 13, "fontWeight": "600", "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4},
            "data": [{"value": int(v), "name": k, "itemStyle": {"color": colors[i]}} for i, (k, v) in enumerate(data_dict.items())],
        }],
    }
    return option


def build_line_chart(title, labels, values, color="#3fbf9f", highlight=None):
    theme = theme_tokens()
    series = {
        "type": "line",
        "smooth": True,
        "symbol": "circle",
        "symbolSize": 6,
        "data": values,
        "lineStyle": {"width": 3, "color": color},
        "itemStyle": {"color": color},
        "areaStyle": {"color": "rgba(63, 191, 159, 0.15)"},
    }
    if highlight is not None:
        series["markPoint"] = {
            "symbol": "pin",
            "symbolSize": 58,
            "itemStyle": {"color": "#dc2626"},
            "label": {"color": "#ffffff", "fontWeight": "700", "textShadowColor": "#334155", "textShadowBlur": 3},
            "data": [{"coord": [highlight[0], highlight[1]], "value": format_currency(highlight[1])}],
        }

    option = {
        "backgroundColor": theme["chart_bg"],
        "title": {"text": title, "left": "center", "top": 12, "textStyle": {"fontSize": 22, "fontWeight": "700", "color": theme["chart_text"], "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "tooltip": {"trigger": "axis"},
        "grid": {"left": "8%", "right": "4%", "bottom": "14%", "top": "26%", "containLabel": True},
        "xAxis": {"type": "category", "boundaryGap": False, "data": labels, "axisLine": {"lineStyle": {"color": theme["chart_text"]}}, "axisLabel": {"color": theme["chart_text"], "fontSize": 14, "fontWeight": "600", "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "yAxis": {"type": "value", "axisLine": {"lineStyle": {"color": theme["chart_text"]}}, "splitLine": {"lineStyle": {"color": theme["grid"]}}, "axisLabel": {"color": theme["chart_text"], "fontSize": 13, "textShadowColor": theme["chart_shadow"], "textShadowBlur": 4}},
        "series": [series],
    }
    return option


def render_chart(chart_type, title, labels, values, color="#6d5ef5", highlight=None):
    if ECHARTS_AVAILABLE and st_echarts is not None:
        if chart_type == "bar":
            return st_echarts(options=build_bar_chart(title, labels, values, color=color), height="520px")
        if chart_type == "line":
            return st_echarts(options=build_line_chart(title, labels, values, color=color, highlight=highlight), height="520px")
        if chart_type == "pie":
            palette = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2"]
            return st_echarts(options=build_pie_chart(title, dict(zip(labels, values)), palette), height="520px")

    df = pd.DataFrame({"categoria": labels, "valor": values})
    if chart_type == "bar":
        st.bar_chart(df.set_index("categoria")["valor"], height=520)
        return None
    if chart_type == "line":
        st.line_chart(df.set_index("categoria")["valor"], height=520)
        return None
    if chart_type == "pie":
        st.bar_chart(df.set_index("categoria")["valor"], height=520)
        return None
    return None


def render_simulador_frete():
    pedidos = carregar_pedidos_marketplace()

    st.markdown('<div class="dashboard-title">Simulador de frete grátis — Marketplace</div>', unsafe_allow_html=True)
    st.markdown('<div class="dashboard-subtitle">Avalie o impacto financeiro de alterar o threshold de frete grátis.</div>', unsafe_allow_html=True)

    cenario_col1, cenario_col2 = st.columns(2)
    with cenario_col1:
        if st.button("Cenário conservador · R$ 450", width="stretch"):
            st.session_state["threshold_frete"] = 450
    with cenario_col2:
        if st.button("Cenário alinhado · R$ 250", width="stretch"):
            st.session_state["threshold_frete"] = 250

    threshold = st.slider(
        "Threshold de frete grátis",
        min_value=0,
        max_value=1500,
        value=st.session_state.get("threshold_frete", 250),
        step=10,
        format="R$ %d",
    )
    st.session_state["threshold_frete"] = threshold
    resultado = simular(threshold, pedidos)

    st.markdown("<div style='height: 0.5rem'></div>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Margem recuperada", format_currency(resultado["margem_recuperada"]), "Frete convertido em margem", "#0f766e")
    with m2:
        metric_card("Pedidos isentos", f"{resultado['pct_pedidos_isentos']:.1f}%", "Pedidos acima do threshold", "#2563eb")
    with m3:
        metric_card("Frete restante", format_currency(resultado["frete_restante"]), "Custo após a política", "#f59e0b")
    with m4:
        metric_card("Frete / receita", f"{resultado['frete_pct_receita_nova']:.2f}%", "Peso do frete no canal", "#dc2626")

    st.markdown("<hr style='margin: 1.2rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    thresholds = sorted(set([0, 100, 150, 200, 250, 300, 350, 400, 450, 500, 600, 700, 800, 1000, 1500, threshold]))
    curva = curva_completa(thresholds, pedidos)
    labels_curva = [f"R$ {int(valor)}" for valor in curva["threshold"]]
    valores_curva = [round(float(valor), 2) for valor in curva["margem_recuperada"]]
    indice_atual = labels_curva.index(f"R$ {threshold}")
    render_chart(
        "line",
        f"Impacto do threshold na margem recuperada · selecionado: R$ {threshold}",
        labels_curva,
        valores_curva,
        color="#0f766e",
        highlight=(labels_curva[indice_atual], valores_curva[indice_atual]),
    )

    with st.container(border=True):
        st.subheader("Relatório executivo")
        st.caption("Síntese da decisão para o cenário atualmente selecionado.")
        if st.button("Gerar recomendação", type="primary"):
            with st.spinner("Gerando recomendação..."):
                st.markdown(gerar_relatorio(resultado))


st.set_page_config(page_title="Dashboard Executivo — Vértice Retail", layout="wide")

theme = theme_tokens()

st.markdown(
    """
    <style>
        :root { color-scheme: light dark; }
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stHeader"] {
            background: var(--background-color) !important;
            color: var(--text-color) !important;
        }
        [data-testid="stDecoration"] { background: var(--primary-color) !important; }
        [data-testid="stSidebar"] {
            background: #111827;
            color: white;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] span {
            color: white !important;
        }
        .block-container {
            padding-top: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .dashboard-title {
            font-size: 2.4rem;
            font-weight: 800;
            color: var(--text-color) !important;
            margin: 0;
        }
        .dashboard-subtitle {
            color: var(--text-color) !important;
            opacity: 0.72;
            font-size: 1rem;
            margin-top: 0.3rem;
            margin-bottom: 1.5rem;
        }
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stCaptionContainer"],
        [data-testid="stSlider"] label,
        [data-testid="stNumberInput"] label {
            color: var(--text-color) !important;
        }
        .nav-label {
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #d1d5db;
            margin-bottom: 0.5rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


dados = carregar_dados()
vendas = dados["vendas"]
clientes = dados["clientes"]
marketing = dados["marketing"]
atendimento = dados["atendimento"]
estoque = dados["estoque"]

receita_total = vendas["receita_liquida"].sum()
margem_total = vendas["margem_contribuicao"].sum()
frete_total = vendas["custo_frete"].sum()
orders_total = vendas["order_id"].nunique()
ticket_medio = receita_total / orders_total
pct_devolucao = vendas["devolvido"].mean() * 100
avg_csat = atendimento["nota_csat"].mean()
roas_medio = marketing["roas"].mean()
ltv_medio = clientes["ltv_acumulado"].mean()
repeat_rate = (clientes["total_pedidos_historico"] > 1).mean() * 100
churn_pct = clientes["segmento_rfm"].eq("Churn").mean() * 100
stock_critico = (estoque["status_disponibilidade"] == "Estoque Crítico").sum()
stock_ruptura = (estoque["status_disponibilidade"] == "Ruptura").sum()

canal_receita = vendas.groupby("canal")["receita_liquida"].sum().sort_values(ascending=False).head(5)
canal_roas = marketing.groupby("canal")["roas"].mean().sort_values(ascending=False).head(5)
canal_margem = vendas.groupby("canal")["margem_contribuicao"].sum().sort_values(ascending=False).head(5)
canal_margem_pct = (canal_margem / canal_receita.reindex(canal_margem.index) * 100).sort_values(ascending=False)
segmento_clientes = clientes["segmento_rfm"].value_counts().sort_values(ascending=False)
estoque_status = estoque["status_disponibilidade"].value_counts().sort_values(ascending=False)
monthly_revenue = (
    vendas.assign(mes=vendas["data_pedido"].dt.to_period("M").astype(str))
    .groupby("mes")["receita_liquida"].sum()
    .sort_index()
    .tail(6)
)

with st.sidebar:
    st.markdown('<div class="nav-label">Vértice Retail</div>', unsafe_allow_html=True)
    menu = option_menu(
        menu_title="Dashboard",
        options=["Simulador de frete", "Resumo", "Financeiro", "Marketing", "Clientes", "Operações", "Atendimento"],
        icons=["truck", "speedometer2", "cash-stack", "megaphone", "people", "boxes", "headset"],
        menu_icon="bar-chart-line",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#111827"},
            "icon": {"color": "#cbd5e1", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "4px 0", "padding": "12px 14px", "color": "#e5e7eb", "--hover-color": "#1f2937"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "#ffffff", "font-weight": "700"},
        },
    )


st.markdown('<div class="dashboard-title">Dashboard executivo — Vértice Retail</div>', unsafe_allow_html=True)
st.markdown('<div class="dashboard-subtitle">Indicadores de alto impacto para decisões estratégicas.</div>', unsafe_allow_html=True)

if menu == "Simulador de frete":
    render_simulador_frete()

elif menu == "Resumo":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Receita líquida", format_currency(receita_total), "Volume de operação em moeda real", "#6d5ef5")
    with col2:
        metric_card("Margem", format_currency(margem_total), f"Margem de contribuição de {format_pct(margem_total / receita_total * 100)}", "#1f9d61")
    with col3:
        metric_card("Ticket médio", format_currency(ticket_medio), f"{orders_total:,.0f} pedidos", "#f59e0b")
    with col4:
        metric_card("ROAS médio", f"{roas_medio:.1f}x", "Retorno do marketing", "#14b8a6")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        highlight_box("Atenção da diretoria", [
            f"Receita líquida em operação: {format_currency(receita_total)}",
            f"Margem de contribuição: {format_currency(margem_total)}",
            f"Churn atual: {format_pct(churn_pct)}",
            f"Risco de estoque: {stock_ruptura} rupturas",
        ], accent="#e0f2fe")
    with c2:
        highlight_box("Oportunidades de maior impacto", [
            f"Canal líder: {canal_receita.index[0]}",
            f"ROAS principal: {canal_roas.index[0]} ({canal_roas.iloc[0]:.1f}x)",
            f"SLA de atendimento: {format_pct((atendimento['tempo_primeira_resposta_minutos'] <= 1440).mean()*100)}",
            f"CSAT médio: {avg_csat:.2f}/5",
        ], accent="#dcfce7")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

    st.markdown("<h2 style='font-size: 1.45rem; color: #111827; margin: 0 0 0.4rem 0;'>Atenção: margem de contribuição</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; margin-bottom: 0.8rem;'>Canais que mais concentram geração e eficiência de margem.</p>", unsafe_allow_html=True)
    render_chart(
        "bar",
        "Margem de contribuição por canal",
        [str(x) for x in canal_margem.index],
        [round(float(v), 2) for v in canal_margem.values],
        color="#0f766e",
    )
    render_chart(
        "bar",
        "Margem percentual por canal",
        [str(x) for x in canal_margem_pct.index],
        [round(float(v), 2) for v in canal_margem_pct.values],
        color="#f59e0b",
    )

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        render_chart("bar", "Receita por canal", [str(x) for x in canal_receita.index], [round(float(v), 2) for v in canal_receita.values], color="#6d5ef5")
    with c2:
        render_chart("bar", "ROAS por canal", [str(x) for x in canal_roas.index], [round(float(v), 2) for v in canal_roas.values], color="#16a34a")

elif menu == "Financeiro":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Receita líquida", format_currency(receita_total), "Faturamento operacional", "#6d5ef5")
    with col2:
        metric_card("Margem total", format_currency(margem_total), f"{format_pct(margem_total / receita_total * 100)} da receita", "#16a34a")
    with col3:
        metric_card("Frete", format_currency(frete_total), "Custo logístico coberto", "#f59e0b")
    with col4:
        metric_card("Ticket médio", format_currency(ticket_medio), "Gasto médio por pedido", "#2563eb")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size: 1.45rem; color: #111827; margin: 0 0 0.35rem 0;'>Calculadora de margem</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: #475569; margin-bottom: 0.8rem;'>Simule como custos variáveis e fixos alteram a margem de contribuição.</p>", unsafe_allow_html=True)
    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1:
        receita_simulada = st.number_input("Receita simulada", min_value=0.0, value=float(receita_total), step=1000.0, format="%.2f")
    with calc_col2:
        custos_variaveis = st.number_input("Custos variáveis", min_value=0.0, value=float(max(receita_total - margem_total, 0)), step=1000.0, format="%.2f")
    with calc_col3:
        custos_fixos = st.number_input("Custos fixos", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

    margem_simulada = receita_simulada - custos_variaveis - custos_fixos
    margem_simulada_pct = margem_simulada / receita_simulada * 100 if receita_simulada else 0
    resultado_col1, resultado_col2 = st.columns(2)
    with resultado_col1:
        metric_card("Margem simulada", format_currency(margem_simulada), f"{format_pct(margem_simulada_pct)} da receita", "#0f766e")
    with resultado_col2:
        metric_card("Ponto de equilíbrio", format_currency(custos_fixos), "Custos fixos informados", "#f59e0b")

    sensibilidade = [max(receita_simulada - (receita_simulada * taxa) - custos_fixos, 0) for taxa in [0.30, 0.40, 0.50, 0.60, 0.70]]
    render_chart("line", "Sensibilidade da margem aos custos variáveis", ["30%", "40%", "50%", "60%", "70%"], [round(float(valor), 2) for valor in sensibilidade], color="#0f766e")
    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    render_chart("line", "Evolução da receita mensal", [str(x) for x in monthly_revenue.index], [round(float(v), 2) for v in monthly_revenue.values], color="#3fbf9f")

elif menu == "Marketing":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("ROAS médio", f"{roas_medio:.1f}x", "Retorno bruto por canal", "#14b8a6")
    with col2:
        metric_card("CAC", f"{marketing['cac'].mean():.2f}", "Custo de aquisição", "#f97316")
    with col3:
        metric_card("Conversões", f"{marketing['conversoes'].sum():,.0f}", "Leads convertidos", "#8b5cf6")
    with col4:
        metric_card("Canal líder", str(canal_roas.index[0]), f"{canal_roas.iloc[0]:.1f}x ROAS", "#10b981")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        render_chart("bar", "Receita por canal", [str(x) for x in canal_receita.index], [round(float(v), 2) for v in canal_receita.values], color="#6d5ef5")
    with c2:
        render_chart("bar", "ROAS por canal", [str(x) for x in canal_roas.index], [round(float(v), 2) for v in canal_roas.values], color="#22c55e")

elif menu == "Clientes":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("LTV médio", format_currency(ltv_medio), "Valor de vida do cliente", "#6366f1")
    with col2:
        metric_card("Recompra", format_pct(repeat_rate), "Clientes com mais de um pedido", "#22c55e")
    with col3:
        metric_card("Churn", format_pct(churn_pct), "Clientes em risco", "#ef4444")
    with col4:
        metric_card("Segmento principal", str(segmento_clientes.index[0]), f"{segmento_clientes.iloc[0]:,.0f} clientes", "#f59e0b")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    render_chart("pie", "Segmentos de clientes", [str(k) for k in segmento_clientes.index], [int(v) for v in segmento_clientes.values], color="#6d5ef5")

elif menu == "Operações":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Devolução", format_pct(pct_devolucao), "Taxa de devolução", "#ef4444")
    with col2:
        metric_card("Ruptura", f"{stock_ruptura}", "SKUs sem disponibilidade", "#f97316")
    with col3:
        metric_card("Estoque crítico", f"{stock_critico}", "Itens em risco de ausência", "#eab308")
    with col4:
        metric_card("Lead time", f"{estoque['lead_time_reposicao'].mean():.0f} dias", "Tempo médio de reposição", "#0ea5e9")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    render_chart("pie", "Status de estoque", [str(k) for k in estoque_status.index], [int(v) for v in estoque_status.values], color="#3eb489")

elif menu == "Atendimento":
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Tickets", f"{len(atendimento):,.0f}", "Volume total de contatos", "#6366f1")
    with col2:
        metric_card("SLA", format_pct((atendimento['tempo_primeira_resposta_minutos'] <= 1440).mean() * 100), "Atendimento dentro do prazo", "#16a34a")
    with col3:
        metric_card("CSAT", f"{avg_csat:.2f}/5", "Satisfação do cliente", "#f59e0b")
    with col4:
        metric_card("Custo total", format_currency(atendimento['custo_operacional_ticket'].sum()), "Custo operacional do atendimento", "#ef4444")

    st.markdown("<hr style='margin: 1rem 0 1.2rem 0; border: 1px solid #e5e7eb;'>", unsafe_allow_html=True)
    top_problems = atendimento["categoria_problema"].value_counts().head(5)
    render_chart("bar", "Principais problemas de atendimento", [str(x) for x in top_problems.index], [int(v) for v in top_problems.values], color="#ff9f43")

