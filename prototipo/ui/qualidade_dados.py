"""Ressalvas sobre os dados do Painel do Gestor: onde as bases não reconciliam entre si.

Os números vêm dos CSVs carregados, calculados a cada carga de dados (nada digitado à mão aqui): se o CSV mudar,
o texto muda junto. Três camadas, para cada uma ser testável sozinha:
    calcular_ressalvas(dados)   função pura: DataFrames -> dict de números
    textos_ressalvas(r)         função pura: dict -> lista de frases (com "$" ainda SEM escape)
    render_ressalvas(dados)     desenha o expander fechado (números em cache, "$" escapado)

Por que existe: o painel mistura bases que não conversam (só 2,3% dos clientes aparecem em vendas, dois terços
dos pedidos do atendimento não existem em vendas, três customer_id concentram 2/3 dos pedidos...). O texto é sóbrio
de propósito: descreve o que foi medido e o que fica comprometido, sem apontar culpado.
"""
import pandas as pd
import streamlit as st

from ui import roas

ANO_PAINEL = 2023
STATUS_CANCELADO = "Cancelado"


def _periodo(datas: pd.Series) -> tuple:
    datas = pd.to_datetime(datas, errors="coerce")
    return datas.min(), datas.max()


def calcular_ressalvas(dados: dict) -> dict:
    """Números das 6 ressalvas, a partir de {"vendas", "clientes", "marketing", "atendimento"} (DataFrames).

    O Simulador de frete não é lido aqui: o que ele usa é exatamente o vendas inteiro filtrado pelo
    prep_dados.pedidos_marketplace, então a contagem dele sai da mesma função (import dentro da função: só
    quem chega aqui precisa do backend carregado).
    """
    from prep_dados import pedidos_marketplace

    vendas, clientes = dados["vendas"], dados["clientes"]
    marketing, atendimento = dados["marketing"], dados["atendimento"]

    # (1) período de cada base (marketing: do primeiro início ao último fim de campanha)
    ini_mkt, _ = _periodo(marketing["data_inicio"])
    _, fim_mkt = _periodo(marketing["data_fim"])
    periodos = {"vendas": _periodo(vendas["data_pedido"]), "marketing": (ini_mkt, fim_mkt),
                "clientes": _periodo(clientes["data_cadastro"]), "atendimento": _periodo(atendimento["data_abertura"])}

    # (2) clientes de clientes.csv que aparecem em vendas.csv
    clientes_total = clientes["customer_id"].nunique()
    clientes_em_vendas = clientes["customer_id"].isin(set(vendas["customer_id"].dropna())).sum()

    # (3) pedidos citados no atendimento que não existem em vendas
    pedidos_atendimento = set(atendimento["order_id"].dropna())
    atendimento_sem_venda = len(pedidos_atendimento - set(vendas["order_id"]))

    # (4) receita atribuída pelo marketing contra a receita real (mesma base do card do ROAS)
    atribuida, real = roas.totais_atribuida_e_real(marketing, vendas, ANO_PAINEL)

    # (5) concentração de customer_id em vendas: pedidos únicos dos 3 IDs mais frequentes
    pedidos_por_cliente = vendas.groupby("customer_id")["order_id"].nunique().sort_values(ascending=False)
    pedidos_total = vendas["order_id"].nunique()

    # (6) base de cada bloco: KPIs do topo (sem cancelados e sem devolvidos), card de ROAS (sem cancelados, com
    # devolvidos; a receita dele é a receita_real de (4)), gráfico mensal (todos os status) e Simulador (vendas inteiro)
    do_ano = vendas[vendas["data_pedido"].dt.year.eq(ANO_PAINEL)]
    sem_cancelados = do_ano[do_ano["status_pagamento"].ne(STATUS_CANCELADO)]
    kpis = sem_cancelados[sem_cancelados["devolvido"].eq(False)]
    marketplace = pedidos_marketplace(vendas)

    return {
        "periodos": periodos,
        "clientes_total": int(clientes_total),
        "clientes_em_vendas": int(clientes_em_vendas),
        "atendimento_pedidos": len(pedidos_atendimento),
        "atendimento_sem_venda": atendimento_sem_venda,
        "receita_atribuida": atribuida,
        "receita_real": real,
        "fator": roas.fator_distorcao(marketing, vendas, ANO_PAINEL),
        "clientes_distintos_em_vendas": int(vendas["customer_id"].nunique()),
        "top3_pedidos": int(pedidos_por_cliente.head(3).sum()),
        "pedidos_total": int(pedidos_total),
        "kpis_pedidos": int(kpis["order_id"].nunique()),
        "kpis_receita": float(kpis["receita_liquida"].sum()),
        "roas_pedidos": int(sem_cancelados["order_id"].nunique()),
        "mensal_pedidos": int(do_ano["order_id"].nunique()),
        "mensal_receita": float(do_ano["receita_liquida"].sum()),
        "simulador_periodo": periodos["vendas"],
        "simulador_receita": float(vendas["receita_liquida"].sum()),
        "simulador_marketplace": len(marketplace),
        "simulador_marketplace_receita": float(marketplace["receita_liquida"].sum()),
    }


# ----------------------------------------------------------------------------------------------
# Texto (funções puras: recebem o dict de números e devolvem frases)
# ----------------------------------------------------------------------------------------------
def _inteiro(n) -> str:
    return f"{int(n):,}".replace(",", ".")


def _pct(parte, total) -> str:
    return f"{parte / total * 100:.1f}%".replace(".", ",")


def _mi(valor) -> str:
    return f"R$ {valor / 1_000_000:.1f} mi".replace(".", ",")


def _data(ts) -> str:
    return ts.strftime("%d/%m/%Y")


def _intervalo(par) -> str:
    return f"{_data(par[0])} a {_data(par[1])}"


INTRODUCAO = ("As bases usadas no painel não reconciliam entre si. Os pontos abaixo foram medidos nos arquivos "
              "carregados e mostram onde os números do painel devem ser lidos com cautela.")


def textos_ressalvas(r: dict) -> list:
    """As 6 ressalvas em frases, na ordem. O "$" sai sem escape: quem exibe escapa (ver render_ressalvas)."""
    p = r["periodos"]
    fator = f"{r['fator']:.1f}".replace(".", ",")
    return [
        f"**Períodos diferentes.** Vendas: {_intervalo(p['vendas'])}. Marketing (campanhas): {_intervalo(p['marketing'])}. "
        f"Clientes (data de cadastro): {_intervalo(p['clientes'])}. Atendimento (abertura dos tickets): "
        f"{_intervalo(p['atendimento'])}.",
        f"**Cobertura de clientes.** Só {_inteiro(r['clientes_em_vendas'])} dos {_inteiro(r['clientes_total'])} clientes "
        f"do cadastro ({_pct(r['clientes_em_vendas'], r['clientes_total'])}) aparecem em vendas.",
        f"**Atendimento sem venda correspondente.** {_inteiro(r['atendimento_sem_venda'])} dos "
        f"{_inteiro(r['atendimento_pedidos'])} pedidos citados no atendimento "
        f"({_pct(r['atendimento_sem_venda'], r['atendimento_pedidos'])}) não existem em vendas.",
        f"**Receita atribuída acima da real.** A receita atribuída pelo marketing ({_mi(r['receita_atribuida'])}, "
        f"campanhas iniciadas em {ANO_PAINEL}) é ~{fator}x a receita líquida real de vendas no mesmo período "
        f"({_mi(r['receita_real'])}). Use o ROAS reportado como indicativo, não para alocar budget.",
        f"**customer_id de vendas não é chave de cliente confiável.** Os 3 maiores IDs concentram "
        f"{_pct(r['top3_pedidos'], r['pedidos_total'])} dos pedidos, entre {_inteiro(r['clientes_distintos_em_vendas'])} "
        "IDs distintos. Análises por cliente feitas a partir de vendas ficam comprometidas.",
        f"**Cada bloco do Painel usa uma base diferente.** Os KPIs do topo consideram pedidos de {ANO_PAINEL} sem "
        f"cancelados e sem devolvidos ({_inteiro(r['kpis_pedidos'])} pedidos; {_mi(r['kpis_receita'])} de receita "
        f"líquida). O card de ROAS considera {ANO_PAINEL} sem cancelados, com devolvidos "
        f"({_inteiro(r['roas_pedidos'])} pedidos; {_mi(r['receita_real'])}). O gráfico mensal considera {ANO_PAINEL} "
        f"com todos os status ({_inteiro(r['mensal_pedidos'])} pedidos; {_mi(r['mensal_receita'])}). O Simulador de "
        f"frete parte do arquivo de vendas inteiro, de {_intervalo(r['simulador_periodo'])}, com todos os status "
        f"({_inteiro(r['pedidos_total'])} pedidos; {_mi(r['simulador_receita'])}), e simula só um canal "
        f"(Marketplace {_inteiro(r['simulador_marketplace'])} pedidos; {_mi(r['simulador_marketplace_receita'])}). "
        "Os números dos blocos não são diretamente comparáveis.",
    ]


# ----------------------------------------------------------------------------------------------
# Tela
# ----------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def carregar_ressalvas(_dados):
    """calcular_ressalvas com cache do Streamlit: os números só mudam se os CSVs mudarem.

    O "_" no nome do parâmetro manda o Streamlit não calcular o hash dos DataFrames a cada rerun (mesmo padrão
    de ui/dados.py).
    """
    return calcular_ressalvas(_dados)


def render_ressalvas(dados: dict) -> None:
    """Expander FECHADO no fim do Painel. O cifrão é escapado: o markdown lê "$...$" como fórmula."""
    from ui.simulador_frete import escapar_cifrao

    textos = textos_ressalvas(carregar_ressalvas(dados))
    with st.expander("Ressalvas sobre os dados", expanded=False):
        st.markdown(escapar_cifrao(INTRODUCAO))
        st.markdown(escapar_cifrao("\n".join(f"- {t}" for t in textos)))
