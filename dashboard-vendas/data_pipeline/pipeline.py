"""Pipeline de agregacoes do dashboard de vendas.

Le os CSVs brutos de `data/` e grava as agregacoes em `outputs/`, todas
restritas a uma janela de 12 meses fechados (a mais recente disponivel).
Versao organizada de `pipeline_bruto.py` (historico do IPython).

Uso:
    uv run python data_pipeline/pipeline.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

# `marketing.csv` NAO reconcilia com `vendas.csv`: receita_gerada soma R$ 878 mi
# contra R$ 18,9 mi de receita em vendas, e sao 115 mi de conversoes contra
# 27.758 pedidos. As duas tabelas estao em escalas diferentes, entao qualquer
# KPI que subtraia investimento de marketing da receita de vendas daria
# prejuizo artificial de ~R$ 195 mi. Marketing so e usado de forma relativa
# (comparacao entre canais) em `eficiencia_por_canal`.
ALERTA_ESCALA_MARKETING = True

DATA_DIR = Path("data")
OUTPUT_DIR = Path("outputs")

# Tamanho da janela de analise, em meses fechados.
JANELA_MESES = 12

# Pedidos cancelados nao viram receita. "Aguardando" continua contando como
# venda em aberto -- tire da lista abaixo se a regra do negocio for outra.
STATUS_PAGAMENTO_VALIDOS = ("Aprovado", "Aguardando")

# Colunas sem as quais a linha nao serve para nenhuma agregacao.
COLUNAS_CRITICAS_VENDAS = (
    "order_id",
    "sku_id",
    "data_pedido",
    "canal",
    "categoria",
    "receita_bruta",
    "receita_liquida",
    "margem_contribuicao",
    "devolvido",
    "status_pagamento",
)
COLUNAS_CRITICAS_ATENDIMENTO = ("ticket_id", "categoria_problema", "custo_operacional_ticket")

# Campos zerados quando o pedido e devolvido: o dinheiro nao ficou na empresa.
COLUNAS_MONETARIAS = ("receita_bruta", "desconto_reais", "receita_liquida", "margem_contribuicao")


# --------------------------------------------------------------------------- #
# Carga e janela de analise
# --------------------------------------------------------------------------- #

def carregar(nome: str) -> pd.DataFrame:
    """Le um CSV de `data/`. `utf-8-sig` remove o BOM presente em alguns arquivos."""
    return pd.read_csv(DATA_DIR / f"{nome}.csv", encoding="utf-8-sig")


def _dropna_criticas(df: pd.DataFrame, colunas: tuple[str, ...], rotulo: str) -> pd.DataFrame:
    """Descarta apenas linhas corrompidas nas colunas que importam.

    O script bruto usava `df.dropna()`, que derruba a linha inteira por causa de
    qualquer NaN -- inclusive campos opcionais como `motivo_devolucao` ou
    `nota_csat` de ticket ainda aberto. Hoje a diferenca e de 1 linha por
    arquivo, mas a versao ampla silenciosamente enviesaria os numeros se mais
    campos opcionais viessem vazios.
    """
    limpo = df.dropna(subset=list(colunas))
    descartadas = len(df) - len(limpo)
    if descartadas:
        print(f"[{rotulo}] {descartadas} linha(s) descartada(s) por campo critico vazio")
    return limpo


def janela_de_analise(vendas: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Os `JANELA_MESES` meses fechados mais recentes de `vendas`.

    Ancora no ultimo mes COMPLETO, nao na ultima data de pedido: a serie vai ate
    2024-01-26, e um mes parcial no fim distorce qualquer serie mensal e qualquer
    comparacao de crescimento. Descartar essa ponta custa 1.221 pedidos (4,4%) e
    entrega 12 meses cheios.

    Derivado dos dados, nao fixo em codigo -- a janela anda sozinha quando
    chegarem meses novos.
    """
    ultimo_mes_fechado = vendas["data_pedido"].max().to_period("M") - 1
    primeiro_mes = ultimo_mes_fechado - (JANELA_MESES - 1)
    return primeiro_mes.start_time, ultimo_mes_fechado.end_time


def _recortar(
    df: pd.DataFrame, coluna_data: str, janela: tuple[pd.Timestamp, pd.Timestamp], rotulo: str
) -> pd.DataFrame:
    inicio, fim = janela
    dentro = df[df[coluna_data].between(inicio, fim)]
    print(f"[{rotulo}] {len(dentro)} de {len(df)} linhas dentro da janela")
    return dentro


# --------------------------------------------------------------------------- #
# Limpeza por tabela
# --------------------------------------------------------------------------- #

def carregar_vendas_limpo() -> pd.DataFrame:
    """Vendas com tipos corrigidos, ainda SEM recorte de janela.

    Separado de `preparar_vendas` porque a janela e derivada destas datas.
    """
    vendas = carregar("vendas")
    vendas = _dropna_criticas(vendas, COLUNAS_CRITICAS_VENDAS, "vendas")

    # `devolvido` chega como object (mistura de bool e NaN), o que torna a
    # mascara booleana instavel. Cast explicito resolve.
    vendas["devolvido"] = vendas["devolvido"].astype(bool)

    vendas["data_pedido"] = pd.to_datetime(vendas["data_pedido"])
    vendas["mes"] = vendas["data_pedido"].dt.strftime("%Y-%m")
    return vendas


def preparar_vendas(
    vendas: pd.DataFrame, janela: tuple[pd.Timestamp, pd.Timestamp]
) -> pd.DataFrame:
    vendas = _recortar(vendas, "data_pedido", janela, "vendas")

    # Um pedido devolvido nao gera receita nem margem.
    vendas = vendas.copy()
    vendas.loc[vendas["devolvido"], list(COLUNAS_MONETARIAS)] = 0.0

    # Cancelados tambem nao: o script bruto os mantinha na soma (~R$ 1,9 mi).
    antes = len(vendas)
    vendas = vendas[vendas["status_pagamento"].isin(STATUS_PAGAMENTO_VALIDOS)]
    print(f"[vendas] {antes - len(vendas)} pedido(s) fora de {STATUS_PAGAMENTO_VALIDOS}")
    return vendas


def preparar_atendimento(janela: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    atendimento = carregar("atendimento")
    atendimento = _dropna_criticas(atendimento, COLUNAS_CRITICAS_ATENDIMENTO, "atendimento")
    atendimento["data_abertura"] = pd.to_datetime(atendimento["data_abertura"])
    # `atendimento.csv` cobre 2023-2025; sem este recorte o custo de atendimento
    # ficaria ~3x maior que o periodo da receita ao lado dele.
    return _recortar(atendimento, "data_abertura", janela, "atendimento")


def preparar_marketing(janela: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Campanhas iniciadas na janela.

    O recorte e por `data_inicio`: cada campanha entra uma vez e inteira. Uma
    campanha que comeca em dezembro e termina depois do fim da janela leva o
    investimento cheio para dentro -- ratear por dia seria chute, e como a
    metrica de canal e uma razao, o efeito se dilui.
    """
    marketing = carregar("marketing")
    marketing["data_inicio"] = pd.to_datetime(marketing["data_inicio"])
    return _recortar(marketing, "data_inicio", janela, "marketing")


# --------------------------------------------------------------------------- #
# Agregacoes
# --------------------------------------------------------------------------- #

def salvar(dados: pd.DataFrame | pd.Series, nome: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    caminho = OUTPUT_DIR / f"{nome}.csv"
    dados.to_csv(caminho)
    print(f"  -> {caminho} ({len(dados)} linhas)")


def serie_mensal(vendas: pd.DataFrame, coluna: str) -> pd.Series:
    return vendas.groupby("mes")[coluna].sum()


def contagem_por_canal(vendas: pd.DataFrame) -> pd.Series:
    return vendas.groupby("canal").size().sort_values(ascending=False).rename("numero_de_vendas")


def margem_pct_por_canal(vendas: pd.DataFrame) -> pd.Series:
    """Margem de contribuicao como fracao da receita liquida, por canal."""
    por_canal = vendas.groupby("canal")[["margem_contribuicao", "receita_liquida"]].sum()
    return (
        por_canal["margem_contribuicao"] / por_canal["receita_liquida"].replace(0, np.nan)
    ).rename("margem_pct")


def eficiencia_por_canal(marketing: pd.DataFrame, vendas: pd.DataFrame) -> pd.DataFrame:
    """Eficiencia de canal numa unica metrica: margem gerada por real investido.

        margem_por_real_investido = (receita_gerada * margem_pct) / investimento

    Por que uma metrica so basta -- e por que nao e `roas / cac`:
    nos dados, `roas = receita_gerada / investimento` e
    `cac = investimento / conversoes` valem como identidade exata. Logo
    `roas * cac = receita / conversoes` (ticket medio, faz sentido), mas
    `roas / cac = receita * conversoes / investimento^2`, que nao tem unidade
    interpretavel e cresce com o volume de conversoes -- nao mede eficiencia.
    Dado o investimento, CAC nao e um segundo eixo de eficiencia: ele so
    reexpressa quantas conversoes o mesmo dinheiro comprou. Quem mede retorno
    por real e o ROAS, sozinho.

    O ajuste que falta no ROAS puro e que receita bruta nao paga a conta: aqui
    ela e descontada pela margem real do canal (vinda de `vendas`), entao a
    metrica le direto -- 1,0 e o ponto de equilibrio, 2,5 significa R$ 2,50 de
    margem por real investido. As demais colunas ficam como decomposicao.
    """
    totais = marketing.groupby("canal").agg(
        investimento_reais=("investimento_reais", "sum"),
        receita_gerada=("receita_gerada", "sum"),
        conversoes=("conversoes", "sum"),
    )
    totais = totais.join(margem_pct_por_canal(vendas))

    totais["roas_agregado"] = totais["receita_gerada"] / totais["investimento_reais"]
    totais["cac_agregado"] = totais["investimento_reais"] / totais["conversoes"]
    totais["margem_gerada"] = totais["receita_gerada"] * totais["margem_pct"]
    totais["margem_por_real_investido"] = totais["margem_gerada"] / totais["investimento_reais"]
    totais["lucro_liquido_aquisicao"] = totais["margem_gerada"] - totais["investimento_reais"]
    totais["numero_de_vendas"] = contagem_por_canal(vendas)

    colunas = [
        "margem_por_real_investido",  # a metrica de decisao
        "lucro_liquido_aquisicao",  # o mesmo em R$, para dimensionar
        "roas_agregado",
        "margem_pct",
        "cac_agregado",
        "investimento_reais",
        "numero_de_vendas",
    ]
    return totais[colunas].sort_values("margem_por_real_investido", ascending=False)


def custo_por_categoria_problema(atendimento: pd.DataFrame) -> pd.Series:
    return (
        atendimento.groupby("categoria_problema")["custo_operacional_ticket"]
        .sum()
        .sort_values(ascending=False)
    )


def receita_por_categoria(vendas: pd.DataFrame) -> pd.DataFrame:
    """Receita e margem por categoria de produto, com participacao no total.

    Usa `vendas.categoria` direto, sem join com `estoque`: as duas colunas
    concordam em 100% dos 27.759 pedidos, entao o merge seria so custo.

    `margem_pct` e soma(margem)/soma(receita) da categoria -- nao a media dos
    percentuais de cada pedido, que daria o mesmo peso a um pedido de R$ 50 e a
    um de R$ 5.000.
    """
    por_categoria = vendas.groupby("categoria").agg(
        receita_liquida=("receita_liquida", "sum"),
        margem_contribuicao=("margem_contribuicao", "sum"),
        pedidos=("order_id", "size"),
    )
    por_categoria["margem_pct"] = (
        por_categoria["margem_contribuicao"] / por_categoria["receita_liquida"].replace(0, np.nan)
    )
    por_categoria["ticket_medio"] = (
        por_categoria["receita_liquida"] / por_categoria["pedidos"].replace(0, np.nan)
    )
    por_categoria["share_receita_pct"] = (
        100 * por_categoria["receita_liquida"] / por_categoria["receita_liquida"].sum()
    )
    return por_categoria.sort_values("receita_liquida", ascending=False)


# --------------------------------------------------------------------------- #
# KPIs do painel
# --------------------------------------------------------------------------- #

def kpis_principais(
    vendas: pd.DataFrame, atendimento: pd.DataFrame, janela: tuple[pd.Timestamp, pd.Timestamp]
) -> pd.DataFrame:
    """Os 4 numeros de topo do dashboard, em formato longo (1 linha por KPI).

    A coluna `meta` fica vazia de proposito: preencha com o alvo do periodo para
    o painel poder desenhar progresso vs. meta.

    Escolha dos KPIs -- um de resultado, um de rentabilidade, um de risco
    operacional e um de alavanca comercial, de modo que os dois ultimos
    expliquem o movimento dos dois primeiros:

    1. receita_liquida_total  -- o numero de resultado.
    2. margem_contribuicao_pct -- rentabilidade do que foi vendido.
    3. taxa_devolucao_pct     -- vazamento controlavel; cada ponto que cai
                                 devolve receita e margem direto aos KPIs 1 e 2.
    4. ticket_medio           -- alavanca comercial; junto com o volume de
                                 pedidos, decompoe a receita em preco x volume.

    Marketing fica FORA destes KPIs de proposito -- veja `ALERTA_ESCALA_MARKETING`.
    Todos os quatro sao da mesma janela de 12 meses, incluindo o custo de
    atendimento que aparece no contexto.
    """
    realizados = vendas[~vendas["devolvido"]]

    receita_liquida = vendas["receita_liquida"].sum()  # devolvidos ja zerados
    margem = vendas["margem_contribuicao"].sum()
    pedidos_realizados = len(realizados)

    devolvidos = int(vendas["devolvido"].sum())
    margem_perdida = _margem_perdida_com_devolucao(vendas)
    custo_atendimento = float(atendimento["custo_operacional_ticket"].sum())

    inicio, fim = janela
    periodo = f"{inicio:%Y-%m} a {fim:%Y-%m}"

    linhas = [
        {
            "kpi": "receita_liquida_total",
            "valor": round(receita_liquida, 2),
            "unidade": "R$",
            "contexto": f"{pedidos_realizados} pedidos realizados",
        },
        {
            "kpi": "margem_contribuicao_pct",
            "valor": round(100 * margem / receita_liquida, 2),
            "unidade": "%",
            "contexto": f"{_reais(margem)} de margem",
        },
        {
            "kpi": "taxa_devolucao_pct",
            "valor": round(100 * devolvidos / len(vendas), 2),
            "unidade": "%",
            "contexto": f"{devolvidos} pedidos; {_reais(margem_perdida)} de margem perdida",
        },
        {
            "kpi": "ticket_medio",
            "valor": round(receita_liquida / pedidos_realizados, 2),
            "unidade": "R$",
            "contexto": f"custo de atendimento na janela: {_reais(custo_atendimento)}",
        },
    ]
    return pd.DataFrame(linhas).assign(periodo=periodo, meta=pd.NA).set_index("kpi")


def _margem_perdida_com_devolucao(vendas: pd.DataFrame) -> float:
    """Margem que os pedidos devolvidos teriam gerado (recalculada do CSV cru).

    Necessario porque `preparar_vendas` ja zerou os campos monetarios deles.
    `order_id` e unico no arquivo, entao o `isin` nao duplica nada.
    """
    cru = carregar("vendas")
    devolvidos = vendas.loc[vendas["devolvido"], "order_id"]
    return float(cru.loc[cru["order_id"].isin(devolvidos), "margem_contribuicao"].sum())


def _reais(valor: float) -> str:
    """Formata em R$ sem separador de milhar -- vai dentro de campo CSV.

    Sem separador de proposito: virgula quebraria o campo e ponto colidiria com o
    separador decimal. O valor para maquina fica na coluna `valor`.
    """
    return f"R$ {valor:.2f}"


# --------------------------------------------------------------------------- #

def main() -> None:
    vendas_completo = carregar_vendas_limpo()
    janela = janela_de_analise(vendas_completo)
    inicio, fim = janela
    print(f"\nJanela de analise: {inicio:%Y-%m-%d} a {fim:%Y-%m-%d} ({JANELA_MESES} meses fechados)")

    vendas = preparar_vendas(vendas_completo, janela)
    atendimento = preparar_atendimento(janela)
    marketing = preparar_marketing(janela)

    print("\nGravando agregacoes:")
    salvar(serie_mensal(vendas, "receita_bruta"), "receita_bruta")
    salvar(serie_mensal(vendas, "receita_liquida"), "receita_liquida")
    salvar(serie_mensal(vendas, "margem_contribuicao"), "margem_mensal")
    salvar(contagem_por_canal(vendas), "canal_count")
    salvar(eficiencia_por_canal(marketing, vendas), "eficiencia_canal")
    salvar(custo_por_categoria_problema(atendimento), "atendimento_custo")
    salvar(receita_por_categoria(vendas), "receita_por_categoria")

    kpis = kpis_principais(vendas, atendimento, janela)
    salvar(kpis, "kpis")

    print(f"\nKPIs ({inicio:%Y-%m} a {fim:%Y-%m}):")
    for nome, linha in kpis.iterrows():
        unidade = linha["unidade"]
        valor = f"R$ {linha['valor']:,.2f}" if unidade == "R$" else f"{linha['valor']:.2f}%"
        print(f"  {nome:<26} {valor:>18}   ({linha['contexto']})")


if __name__ == "__main__":
    main()
