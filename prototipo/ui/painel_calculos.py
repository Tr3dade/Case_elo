"""Agregados do Painel do Gestor sobre UMA base só: o gráfico mensal, o donut e a tabela de categorias saem daqui.

A base é a mesma dos KPIs do topo: pedidos do ano, sem cancelados e sem devolvidos. Assim a soma das barras
mensais, a soma das categorias e o card "Receita líquida" dão o mesmo número. Antes o gráfico e o donut usavam
todos os status (R$ 18,1 mi contra R$ 14,2 mi dos KPIs) e a tabela de categorias era digitada à mão no HTML.

Tudo aqui é função pura sobre DataFrames (sem estado global), para ser testada sem o Streamlit.
"""
import pandas as pd

ANO_PADRAO = 2023
STATUS_CANCELADO = "Cancelado"


def vendas_validas(vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> pd.DataFrame:
    """Pedidos do ano sem cancelados e sem devolvidos: a base dos KPIs e de tudo o que este módulo agrega."""
    do_ano = vendas[vendas["data_pedido"].dt.year.eq(ano)]
    nao_cancelados = do_ano[do_ano["status_pagamento"].ne(STATUS_CANCELADO)]
    return nao_cancelados[nao_cancelados["devolvido"].eq(False)]


def mensal(vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> pd.DataFrame:
    """Uma linha por mês do ano (mês sem venda vira zero): receita_liquida, receita_bruta, margem_contribuicao
    e descontos (bruta - líquida, ou seja, só desconto_reais: devolução não está nesta base).

    O índice é o mês "AAAA-MM". Colunas: mes, mes_label (Jan, Fev...), e as quatro acima.
    """
    base = vendas_validas(vendas, ano).assign(mes=lambda d: d["data_pedido"].dt.to_period("M").astype(str))
    meses = pd.period_range(f"{ano}-01", f"{ano}-12", freq="M").astype(str)
    por_mes = (base.groupby("mes")
               .agg(receita_liquida=("receita_liquida", "sum"), receita_bruta=("receita_bruta", "sum"),
                    margem_contribuicao=("margem_contribuicao", "sum"))
               .reindex(meses, fill_value=0.0)
               .rename_axis("mes")
               .reset_index())
    por_mes["descontos"] = (por_mes["receita_bruta"] - por_mes["receita_liquida"]).clip(lower=0)
    por_mes["mes_label"] = pd.to_datetime(por_mes["mes"]).dt.strftime("%b").str.title()
    return por_mes


def por_categoria(vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> pd.DataFrame:
    """Uma linha por categoria, da maior para a menor receita: receita_liquida, margem_contribuicao, pedidos
    (order_id únicos), ticket (receita ÷ pedidos), margem_pct e participacao_pct (fatia da receita total).

    O índice é a categoria.
    """
    base = vendas_validas(vendas, ano)
    por_cat = (base.groupby("categoria")
               .agg(receita_liquida=("receita_liquida", "sum"), margem_contribuicao=("margem_contribuicao", "sum"),
                    pedidos=("order_id", "nunique"))
               .sort_values("receita_liquida", ascending=False))
    por_cat["ticket"] = por_cat["receita_liquida"] / por_cat["pedidos"]
    por_cat["margem_pct"] = por_cat["margem_contribuicao"] / por_cat["receita_liquida"] * 100
    por_cat["participacao_pct"] = por_cat["receita_liquida"] / por_cat["receita_liquida"].sum() * 100
    return por_cat
