"""ROAS do Painel do Gestor: o que o marketing reporta contra o que as vendas sustentam.

O ROAS do card ("reportado") é receita ATRIBUÍDA pelo marketing ÷ investimento. Nada garante que essa receita
exista no vendas.csv: somada, ela é ~17x a receita líquida real. O "reconciliado" troca o numerador pela receita
líquida de vendas do mesmo ano, sem cancelados (a mesma base do "N vendas" do card). Ele só vale como RANKING
relativo entre canais; os valores absolutos (0,2 a 0,4) não devem ser exibidos como se fossem o ROAS verdadeiro.

Tudo aqui é função pura sobre DataFrames (sem estado global), exceto render_aviso_roas, que escreve na tela.
O cálculo inline do card no app.py continua sendo a fonte dos valores exibidos; test_ui_roas.py confere que
roas_reportado devolve os mesmos números, para não existirem duas verdades.
"""
import pandas as pd

ANO_PADRAO = 2023
STATUS_CANCELADO = "Cancelado"


def _campanhas_do_ano(marketing: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Campanhas com data_inicio no ano (data ilegível vira NaT e fica de fora, como no card)."""
    return marketing[pd.to_datetime(marketing["data_inicio"], errors="coerce").dt.year.eq(ano)]


def _receita_real_por_canal(vendas: pd.DataFrame, ano: int) -> pd.Series:
    """Soma de receita_liquida por canal: pedidos do ano, sem os Cancelados (devolvidos ficam, como no card)."""
    do_ano = vendas[vendas["data_pedido"].dt.year.eq(ano) & vendas["status_pagamento"].ne(STATUS_CANCELADO)]
    return do_ano.groupby("canal")["receita_liquida"].sum()


def _por_canal(campanhas: pd.DataFrame) -> pd.DataFrame:
    return campanhas.groupby("canal").agg(atribuida=("receita_gerada", "sum"),
                                          investimento=("investimento_reais", "sum"))


def roas_reportado(marketing: pd.DataFrame, ano: int = ANO_PADRAO) -> pd.Series:
    """ROAS por canal como o marketing reporta: soma(receita_gerada) ÷ soma(investimento_reais).

    Só campanhas iniciadas no ano. Do maior para o menor, que é a ordem do card. Canal com investimento
    zero não tem ROAS definido e sai da série.
    """
    por_canal = _por_canal(_campanhas_do_ano(marketing, ano))
    roas = (por_canal["atribuida"] / por_canal["investimento"]).replace([float("inf")], float("nan"))
    return roas.dropna().sort_values(ascending=False)


def roas_reconciliado(marketing: pd.DataFrame, vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> pd.Series:
    """ROAS por canal com a receita REAL: soma(receita_liquida em vendas) ÷ investimento das mesmas campanhas.

    Canal com campanha mas sem nenhuma venda fica com 0 (e não some), porque "vendeu zero" é informação.
    Use só para ordenar canais: o valor absoluto depende de o vendas.csv cobrir tudo o que o marketing atribui.
    """
    investimento = _por_canal(_campanhas_do_ano(marketing, ano))["investimento"]
    real = _receita_real_por_canal(vendas, ano).reindex(investimento.index, fill_value=0.0)
    roas = (real / investimento).replace([float("inf")], float("nan"))
    return roas.dropna().sort_values(ascending=False)


def totais_atribuida_e_real(marketing: pd.DataFrame, vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> tuple:
    """(receita atribuída, receita real) em R$, nos canais que têm campanha no ano.

    É o par que sustenta o fator de distorção; fica público para o texto das ressalvas mostrar os dois
    valores sem repetir a conta.
    """
    atribuida = _por_canal(_campanhas_do_ano(marketing, ano))["atribuida"]
    real = _receita_real_por_canal(vendas, ano).reindex(atribuida.index, fill_value=0.0).sum()
    return float(atribuida.sum()), float(real)


def fator_distorcao(marketing: pd.DataFrame, vendas: pd.DataFrame, ano: int = ANO_PADRAO) -> float:
    """Receita atribuída pelo marketing ÷ receita real de vendas, nos canais que têm campanha no ano.

    Devolve NaN se não houver receita real (não dá para dividir por zero e chamar de "fator").
    """
    atribuida, real = totais_atribuida_e_real(marketing, vendas, ano)
    return atribuida / real if real else float("nan")


def posicao(serie: pd.Series, canal: str) -> int:
    """Posição (1 = maior valor) do canal na série. Empate fica com a melhor posição para todos os empatados."""
    return int(serie.rank(ascending=False, method="min")[canal])


def texto_aviso_roas(marketing: pd.DataFrame, vendas: pd.DataFrame, canal: str = "Marketplace",
                     ano: int = ANO_PADRAO):
    """Texto do aviso, com fator e posições calculados agora; None se não der para calcular.

    Mostra só as POSIÇÕES do ranking reconciliado, nunca os valores. Se a ordem dos canais não mudar, o texto
    diz que se mantém em vez de afirmar uma mudança que não existe.
    """
    reportado = roas_reportado(marketing, ano)
    reconciliado = roas_reconciliado(marketing, vendas, ano)
    fator = fator_distorcao(marketing, vendas, ano)
    if canal not in reportado.index or canal not in reconciliado.index or pd.isna(fator):
        return None
    mudou = list(reportado.index) != list(reconciliado.index)
    verbo = "o ranking muda" if mudou else "o ranking se mantém"
    fator_br = f"{fator:.1f}".replace(".", ",")                 # vírgula decimal, como no resto do painel
    return (f"A receita atribuída pelo marketing é ~{fator_br}x a receita real de vendas no mesmo período. "
            f"Com a receita real, {verbo} ({canal}: {posicao(reportado, canal)}º → "
            f"{posicao(reconciliado, canal)}º de {len(reportado)}). "
            "Use como indicativo, não para alocar budget.")


def render_aviso_roas(marketing: pd.DataFrame, vendas: pd.DataFrame) -> None:
    """Mostra o st.warning logo abaixo do card. Sem dados suficientes, não mostra nada."""
    import streamlit as st
    from ui.simulador_frete import escapar_cifrao          # o markdown do Streamlit lê "$...$" como fórmula

    texto = texto_aviso_roas(marketing, vendas)
    if texto:
        st.warning(escapar_cifrao(texto))
