"""Testes do ui/grafico_mensal.py: eixos do gráfico mensal com o zero na mesma altura.

Propriedades (valem para qualquer dado) em casos sintéticos e nos valores mensais reais. O gráfico já montado
no app (opções do ECharts, séries inalteradas) é conferido em test_ui_painel.py.
"""
import os
import sys

import pandas as pd
import pytest

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

from ui import grafico_mensal as g                  # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")


def fracao_do_zero(eixo: dict) -> float:
    """Altura do zero, de 0 (fundo) a 1 (topo)."""
    return (0 - eixo["min"]) / (eixo["max"] - eixo["min"])


def divisoes(eixo: dict) -> float:
    return round((eixo["max"] - eixo["min"]) / eixo["interval"], 6)


def confere_propriedades(eixos, min_esq, max_esq, min_dir, max_dir):
    esq, dir_ = eixos["esq"], eixos["dir"]
    assert fracao_do_zero(esq) == pytest.approx(fracao_do_zero(dir_))       # o objetivo: zeros na mesma altura
    assert divisoes(esq) == divisoes(dir_)                                  # e as linhas de grade coincidem
    assert esq["min"] <= min(min_esq, 0) and esq["max"] >= max(max_esq, 0)  # nenhum dado sai do eixo
    assert dir_["min"] <= min(min_dir, 0) and dir_["max"] >= max(max_dir, 0)
    assert esq["min"] <= 0 <= esq["max"] and dir_["min"] <= 0 <= dir_["max"]
    assert divisoes(esq) == int(divisoes(esq))                              # o zero cai numa linha de grade


# ================================================================================================
# 1. Passo redondo
# ================================================================================================
@pytest.mark.parametrize("minimo, esperado", [(0, 1), (-5, 1), (1, 1), (1.1, 2), (2.2, 2.5), (3, 5), (5.1, 10),
                                              (500_000, 500_000), (240_000, 250_000), (600_000, 1_000_000)])
def test_passo_redondo_e_o_menor_que_comporta(minimo, esperado):
    assert g._passo_redondo(minimo) == esperado


# ================================================================================================
# 2. Sintético
# ================================================================================================
@pytest.mark.parametrize("dados", [
    (-286, 2714, 498, 1444),         # o caso do painel: deduções pequenas, margem só positiva
    (-1000, 1000, 0, 1000),          # simétrico
    (0, 900, 0, 30),                 # nada abaixo de zero
    (-50, 60, -20, 40),              # margem também negativa
    (-5, 10_000_000, 3, 7),          # margem minúscula perto da receita
    (-0.3, 0.9, 0.1, 0.2),           # valores fracionários
])
def test_zeros_alinhados_e_dados_dentro_do_eixo(dados):
    confere_propriedades(g.eixos_alinhados(*dados), *dados)


def test_serie_toda_zerada_devolve_eixo_valido():
    eixos = g.eixos_alinhados(0, 0, 0, 0)
    assert eixos["esq"]["max"] > eixos["esq"]["min"] and eixos["dir"]["max"] > eixos["dir"]["min"]
    assert fracao_do_zero(eixos["esq"]) == pytest.approx(fracao_do_zero(eixos["dir"]))


def test_margem_com_valor_negativo_ganha_espaco_abaixo_do_zero_mesmo_sem_barra_negativa():
    dados = (0, 100, -10, 50)
    eixos = g.eixos_alinhados(*dados)
    assert eixos["dir"]["min"] < 0 and eixos["esq"]["min"] < 0
    confere_propriedades(eixos, *dados)


def test_eixos_do_grafico_nega_as_deducoes():
    # deduções chegam positivas (como no app) e o gráfico as desenha negativas
    eixos = g.eixos_do_grafico([100, 300], [50, 250], [10, 20])
    assert eixos["esq"]["min"] <= -250 and eixos["esq"]["max"] >= 300
    confere_propriedades(eixos, -250, 300, 10, 20)


# ================================================================================================
# 3. Dados reais (mesma conta do app: vendas_2023 inteiro, receita bruta - líquida, sem valor negativo)
# ================================================================================================
def series_mensais_reais():
    vendas = pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"])
    v23 = vendas[(vendas["data_pedido"] >= "2023-01-01") & (vendas["data_pedido"] < "2024-01-01")].copy()
    v23["mes"] = v23["data_pedido"].dt.to_period("M").astype(str)
    meses = pd.period_range("2023-01", "2023-12", freq="M").astype(str)
    m = (v23.groupby("mes").agg(rl=("receita_liquida", "sum"), rb=("receita_bruta", "sum"),
                                mc=("margem_contribuicao", "sum")).reindex(meses, fill_value=0.0))
    return m["rl"].tolist(), (m["rb"] - m["rl"]).clip(lower=0).tolist(), m["mc"].tolist()


def test_real_eixos_do_painel():
    receita, deducoes, margem = series_mensais_reais()
    eixos = g.eixos_do_grafico(receita, deducoes, margem)
    confere_propriedades(eixos, min(-d for d in deducoes), max(receita), min(margem), max(margem))
    # o eixo esquerdo fica como o ECharts o escolhia sozinho; o da margem se ajusta a ele
    assert eixos["esq"] == {"min": -500_000, "max": 3_000_000, "interval": 500_000}
    assert eixos["dir"] == {"min": -250_000, "max": 1_500_000, "interval": 250_000}
