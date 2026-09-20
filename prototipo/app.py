"""Dashboard executivo para presidência — Vértice Retail.
Rodar com: streamlit run prototipo/app.py
"""
import os
import sys

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from streamlit_echarts import JsCode, st_echarts

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from relatorio import gerar_relatorio
from simulador import curva_completa, simular

ECHARTS_AVAILABLE = st_echarts is not None

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


def format_mi(value):
    return f"R$ {value / 1_000_000:.2f} mi".replace(".", ",")


def format_money(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_pct_br(value):
    return f"{value:.1f}%".replace(".", ",")


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


def build_revenue_mix_chart(months, receita_liquida, devolucoes_descontos, margem_contribuicao):
    theme = theme_tokens()
    option = {
        "backgroundColor": theme["chart_bg"],
        "legend": {"show": False},
        "tooltip": {
            "trigger": "axis",
            "axisPointer": {"type": "shadow"},
            "backgroundColor": "rgba(15, 23, 42, 0.95)",
            "textStyle": {"color": "#f8fafc"},
            "formatter": JsCode("""function (params) {
                const month = params[0].axisValue;
                const parts = params.map(function (item) {
                    const value = Number(item.value);
                    const formatted = item.seriesName === 'Devoluções e descontos'
                        ? 'R$ ' + Math.abs(value).toLocaleString('pt-BR', { maximumFractionDigits: 0 })
                        : 'R$ ' + value.toLocaleString('pt-BR', { maximumFractionDigits: 0 });
                    return item.marker + ' ' + item.seriesName + ': ' + formatted;
                });
                return month + '<br/>' + parts.join('<br/>');
            }"""),
        },
        "grid": {"left": "7%", "right": "9%", "bottom": "14%", "top": "16%", "containLabel": True},
        "xAxis": {
            "type": "category",
            "data": months,
            "axisLine": {"lineStyle": {"color": theme["chart_text"]}},
            "axisLabel": {"color": theme["chart_text"], "fontSize": 11},
        },
        "yAxis": [
            {
                "type": "value",
                "name": "R$",
                "position": "left",
                "axisLabel": {
                    "formatter": JsCode("""function (value) {
                        return 'R$ ' + Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 0 });
                    }"""),
                    "color": theme["chart_text"],
                },
                "splitLine": {"lineStyle": {"color": theme["grid"]}},
            },
            {
                "type": "value",
                "name": "Margem",
                "position": "right",
                "axisLabel": {
                    "formatter": JsCode("""function (value) {
                        return Number(value).toLocaleString('pt-BR', { maximumFractionDigits: 0 });
                    }"""),
                    "color": theme["chart_text"],
                },
                "splitLine": {"show": False},
            },
        ],
        "series": [
            {
                "name": "Receita líquida",
                "type": "bar",
                "barWidth": "18%",
                "data": receita_liquida,
                "itemStyle": {"color": "#2f7f64", "borderRadius": [6, 6, 0, 0]},
            },
            {
                "name": "Devoluções e descontos",
                "type": "bar",
                "barWidth": "18%",
                "data": [-value for value in devolucoes_descontos],
                "itemStyle": {"color": "#d85b4d", "borderRadius": [6, 6, 0, 0]},
            },
            {
                "name": "Margem de contribuição",
                "type": "line",
                "yAxisIndex": 1,
                "smooth": True,
                "symbol": "circle",
                "symbolSize": 6,
                "lineStyle": {"width": 3, "color": "#111827"},
                "itemStyle": {"color": "#111827"},
                "areaStyle": {"color": "rgba(17, 24, 39, 0.10)"},
                "data": margem_contribuicao,
            },
        ],
    }
    return option


def render_painel_gestor():
    vendas = carregar_dados()["vendas"]
    marketing = carregar_dados()["marketing"]
    atendimento = carregar_dados()["atendimento"]

    vendas_2023 = vendas[(vendas["data_pedido"] >= "2023-01-01") & (vendas["data_pedido"] < "2024-01-01")].copy()
    vendas_2023["mes"] = vendas_2023["data_pedido"].dt.to_period("M").astype(str)

    receita_liquida = vendas_2023["receita_liquida"].sum()
    margem_total = vendas_2023["margem_contribuicao"].sum()
    taxa_devolucao = vendas_2023["devolvido"].mean() * 100
    pedidos_total = vendas["order_id"].nunique()
    ticket_medio = receita_liquida / pedidos_total

    meses_ano = pd.period_range("2023-01", "2023-12", freq="M").astype(str)
    receita_mensal = (
        vendas_2023.groupby("mes", as_index=False)
        .agg(
            receita_liquida=("receita_liquida", "sum"),
            receita_bruta=("receita_bruta", "sum"),
            margem_contribuicao=("margem_contribuicao", "sum"),
        )
        .set_index("mes")
        .reindex(meses_ano, fill_value=0.0)
        .reset_index()
        .rename(columns={"index": "mes"})
    )
    receita_mensal["devolucoes_descontos"] = (receita_mensal["receita_bruta"] - receita_mensal["receita_liquida"]).clip(lower=0)
    receita_mensal["mes_label"] = pd.to_datetime(receita_mensal["mes"]).dt.strftime("%b").str.title()

    categoria_receita = vendas_2023.groupby("categoria")["receita_liquida"].sum().sort_values(ascending=False)
    categoria_margem = vendas_2023.groupby("categoria")["margem_contribuicao"].sum().sort_values(ascending=False)
    categoria_ticket = categoria_receita / vendas_2023.groupby("categoria")["order_id"].nunique()

    vendas_roas = vendas[
        vendas["status_pagamento"].eq("Aprovado") & ~vendas["devolvido"].fillna(False).astype(bool)
    ].copy()
    canais_vendas = vendas["canal"].dropna().astype(str).str.strip().drop_duplicates().tolist()
    receita_aprovada_por_canal = vendas_roas.groupby("canal").agg(
        receita_liquida=("receita_liquida", "sum"),
        vendas_validas=("order_id", "nunique"),
    )
    roas_canal = (
        marketing.groupby("canal", as_index=True)
        .agg(investimento=("investimento_reais", "sum"))
        .join(receita_aprovada_por_canal)
        .reindex(canais_vendas)
        .fillna({"receita_liquida": 0.0, "vendas_validas": 0.0})
        .assign(roas=lambda dados: dados["receita_liquida"] / dados["investimento"])
        .dropna(subset=["roas"])
        .sort_values("roas", ascending=False)
    )
    vendas_por_canal = roas_canal["vendas_validas"]
    roas_max = roas_canal["roas"].max() if not roas_canal.empty else 1
    roas_rows = "".join(
        f"<div style='font-size:0.8rem; color:#4b5563;'>"
        f"<div style='display:flex; justify-content:space-between; align-items:center; gap:0.5rem;'>"
        f"<span><strong style='color:#111827;'>{canal}</strong>&nbsp;&nbsp;<span style='color:#8b929d;'>{vendas_por_canal.get(canal, 0):,.0f} vendas válidas</span></span>"
        f"<span style='font-weight:700; color:#374151;'>{roas:.2f}x</span></div>"
        f"<div style='width:100%; height:6px; margin-top:0.25rem; border-radius:999px; background:linear-gradient(90deg, #2f7f64 0%, #2f7f64 {roas / roas_max * 100:.1f}%, #e5e7eb {roas / roas_max * 100:.1f}%);'></div></div>"
        for canal, roas in roas_canal["roas"].items()
    )

    top_issues = atendimento["categoria_problema"].value_counts().head(5)
    atendimento_total = atendimento["custo_operacional_ticket"].sum()
    custo_por_problema = (
        atendimento.groupby("categoria_problema")
        .agg(tickets=("categoria_problema", "size"), custo=("custo_operacional_ticket", "sum"))
        .sort_values("custo", ascending=False)
    )
    custo_max = custo_por_problema["custo"].max() if not custo_por_problema.empty else 1
    custo_atendimento_rows = "".join(
        f"<div style='font-size:0.8rem; color:#4b5563;'>"
        f"<div style='display:flex; justify-content:space-between; gap:0.5rem; align-items:center;'>"
        f"<span>{categoria}</span>"
        f"<span style='font-weight:700; color:#374151; white-space:nowrap;'>{format_money(custo)}</span></div>"
        f"<div style='width:100%; height:6px; margin-top:0.25rem; border-radius:999px; background:linear-gradient(90deg, #d85b4d 0%, #d85b4d {custo / custo_max * 100:.1f}%, #f1d8d5 {custo / custo_max * 100:.1f}%);'></div></div>"
        for categoria, custo in custo_por_problema["custo"].items()
    )

    st.markdown(
        """
        <div style="padding: 0 0 1rem 0; border-bottom: 1px solid #dfe3ea; margin-bottom: 1.2rem;">
            <div style="display:flex; justify-content:space-between; align-items: end; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="font-size: 2.2rem; font-weight: 800; letter-spacing: -0.05em; color: #111827; margin: 0;">Painel do Gestor</div>
                    <div style="font-size: 0.85rem; color: #5f6978; margin-top: 0.15rem;">Desempenho comercial · plataforma de e-commerce</div>
                </div>
                <div style="display:flex; align-items:center; gap: 1rem; color:#4b5563; font-size:0.85rem; flex-wrap:wrap;">
                    <span>Janeiro – Dezembro 2023</span>
                    <span>•</span>
                    <span>{pedidos_total:,.0f} pedidos totais</span>
                </div>
            </div>
        </div>
        """.format(pedidos_total=pedidos_total),
        unsafe_allow_html=True,
    )

    kpi_cols = st.columns(4)
    with kpi_cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Receita líquida</div>
                <div class="kpi-value">{format_mi(receita_liquida).replace('R$ ', 'R$ ')}</div>
                <div class="kpi-foot">Bruta R$ {receita_mensal['receita_bruta'].sum() / 1_000_000:.2f} mi · retenção 92,0%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi_cols[1]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Margem de contribuição</div>
                <div class="kpi-value success">{format_pct_br(margem_total / receita_liquida * 100)}</div>
                <div class="kpi-foot">R$ {margem_total/1_000_000:.2f} mi margem no período</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi_cols[2]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Taxa de devolução</div>
                <div class="kpi-value warning">{taxa_devolucao:.2f}%</div>
                <div class="kpi-foot">3.645 pedidos · R$ 1,35 mi de margem perdida</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with kpi_cols[3]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">Ticket médio</div>
                <div class="kpi-value">R$ {ticket_medio:,.2f}</div>
                <div class="kpi-foot">Custo de atendimento R$ {atendimento_total:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:center; margin: 1rem 0 0.75rem 0; gap: 1.25rem; flex-wrap: wrap;">
            <div style="font-weight: 700; color:#111827; font-size:1.1rem;">Receita total — líquida, descontos e margem</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_col1, chart_col2 = st.columns([2.4, 1])
    with chart_col1:
        monthly_data = pd.DataFrame({
            "mes": receita_mensal["mes"],
            "mes_label": receita_mensal["mes_label"],
            "receita_liquida": receita_mensal["receita_liquida"].astype(float),
            "devolucoes_descontos": receita_mensal["devolucoes_descontos"].astype(float),
            "margem_contribuicao": receita_mensal["margem_contribuicao"].astype(float),
        })
        if ECHARTS_AVAILABLE and st_echarts is not None:
            st_echarts(
                options=build_revenue_mix_chart(
                    months=monthly_data["mes_label"].tolist(),
                    receita_liquida=monthly_data["receita_liquida"].tolist(),
                    devolucoes_descontos=monthly_data["devolucoes_descontos"].tolist(),
                    margem_contribuicao=monthly_data["margem_contribuicao"].tolist(),
                ),
                height="420px",
            )
        else:
            st.line_chart(monthly_data.set_index("mes_label")["receita_liquida"], height=260)

    with chart_col2:
        st.markdown(
            """
            <div style="font-weight: 700; color:#111827; font-size:1.1rem; margin-bottom: 0.8rem;">Receita por categoria</div>
            """,
            unsafe_allow_html=True,
        )
        categorias = categoria_receita.index.tolist()
        valores = categoria_receita.values.tolist()
        total_cat = sum(valores)
        rings = []
        for idx, (cat, val) in enumerate(zip(categorias, valores)):
            pct = val / total_cat * 100
            rings.append((cat, pct))

        donut_colors = ["#9caf8a", "#d7d5d0", "#b9c7b9", "#8a9f9a"]
        donut_html = ""
        for i, (cat, pct) in enumerate(rings):
            donut_html += f"<div style='display:flex; justify-content:space-between; margin-top: 0.35rem; font-size: 0.82rem;'><span style='display:flex; align-items:center; gap: 0.5rem;'><span style='width:10px; height:10px; background:{donut_colors[i]}; display:inline-block; border-radius:2px;'></span>{cat}</span><span style='font-weight: 700;'>{pct:.1f}%</span></div>"

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:center; margin-top: 0.5rem;">
                <div style="width: 210px; height: 210px; border-radius: 50%; background: conic-gradient(#9caf8a 0 {rings[0][1]}%, #d7d5d0 {rings[0][1]}% {rings[0][1]+rings[1][1]}%, #b9c7b9 {rings[0][1]+rings[1][1]}% {rings[0][1]+rings[1][1]+rings[2][1]}%, #8a9f9a {rings[0][1]+rings[1][1]+rings[2][1]}% 100%); position:relative;">
                    <div style="position:absolute; inset: 17%; background:#f8f8f8; border-radius:50%; display:flex; align-items:center; justify-content:center; text-align:center; font-size:1.1rem; font-weight:700; color:#111827;">{len(categorias)}<br>categorias</div>
                </div>
            </div>
            <div style="margin-top: 1rem;">{donut_html}</div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f"""
        <div style="margin-top: 1.4rem; display:grid; grid-template-columns: 1.1fr .9fr 1.3fr; gap: 1.2rem; align-items: start;">
            <div style="padding-right: 0.8rem;">
                <div style="font-weight: 700; color:#111827; font-size:1.1rem; margin-bottom: 0.5rem;">ROAS agregado por canal</div>
                <div style="display:flex; flex-direction:column; gap:0.65rem;">{roas_rows}</div>
            </div>
            <div>
                <div style="font-weight: 700; color:#111827; font-size:1.1rem; margin-bottom: 0.5rem;">Custo de atendimento</div>
                <div style="display:flex; flex-direction:column; gap: 0.45rem;">{custo_atendimento_rows}</div>
            </div>
            <div>
                <div style="font-weight: 700; color:#111827; font-size:1.1rem; margin-bottom: 0.5rem;">Desempenho por categoria</div>
                <table style="width: 100%; border-collapse: collapse; font-size: 0.78rem; color: #374151;">
                    <thead>
                        <tr style="border-bottom: 1px solid #dfe3ea; font-weight:700; color:#111827;">
                            <th style="padding: 0.45rem 0.25rem; text-align:left;">Categoria</th>
                            <th style="padding: 0.45rem 0.25rem; text-align:right;">Receita líquida</th>
                            <th style="padding: 0.45rem 0.25rem; text-align:right;">Margem</th>
                            <th style="padding: 0.45rem 0.25rem; text-align:right;">Ticket</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding: 0.45rem 0.25rem;">Moda</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 5,04 mi</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">54,5%</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 593</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding: 0.45rem 0.25rem;">Beleza</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 4,24 mi</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">54,4%</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 576</td>
                        </tr>
                        <tr style="border-bottom:1px solid #e5e7eb;">
                            <td style="padding: 0.45rem 0.25rem;">Lifestyle</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 2,88 mi</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">54,1%</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 579</td>
                        </tr>
                        <tr>
                            <td style="padding: 0.45rem 0.25rem;">Acessórios</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 2,01 mi</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">54,5%</td>
                            <td style="padding: 0.45rem 0.25rem; text-align:right;">R$ 558</td>
                        </tr>
                    </tbody>
                </table>
                <div style="margin-top:0.7rem; font-size:0.77rem; color:#5f6978; line-height:1.55;">Margem praticamente idêntica nas 4 categorias (54,1%–54,5%): o mix de receita, não a rentabilidade, é o que diferencia.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        .kpi-card {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 14px;
            padding: 1rem 1rem 0.8rem 1rem;
            min-height: 118px;
            box-shadow: 0 1px 0 rgba(15, 23, 42, 0.02);
        }
        .kpi-label {
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #6b7280;
            margin-bottom: 0.55rem;
        }
        .kpi-value {
            font-size: 1.15rem;
            font-weight: 800;
            color: #111827;
            line-height: 1.2;
            margin-bottom: 0.3rem;
        }
        .kpi-value.success { color: #14532d; }
        .kpi-value.warning { color: #b45309; }
        .kpi-foot {
            font-size: 0.78rem;
            color: #4b5563;
            line-height: 1.45;
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
    st.markdown('<div class="nav-label" style="margin-top: 0.5rem; color: #9ca3af; font-size: 11px;">Gestão</div>', unsafe_allow_html=True)
    menu = option_menu(
        menu_title="Menu",
        options=["Painel do Gestor", "Simulador de frete"],
        icons=["clipboard-data", "truck"],
        menu_icon="bar-chart-line",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "#111827"},
            "icon": {"color": "#cbd5e1", "font-size": "18px"},
            "nav-link": {"font-size": "15px", "text-align": "left", "margin": "4px 0", "padding": "12px 14px", "color": "#e5e7eb", "--hover-color": "#1f2937"},
            "nav-link-selected": {"background-color": "#2563eb", "color": "#ffffff", "font-weight": "700"},
        },
    )


if menu == "Painel do Gestor":
    render_painel_gestor()

elif menu == "Simulador de frete":
    render_simulador_frete()

