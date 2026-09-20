"""Testes do ui/roas.py: ROAS reportado x reconciliado, fator de distorção e o texto do aviso.

Duas partes: (1) casos sintéticos pequenos, com a conta feita à mão nos comentários; (2) os dados reais, que
travam os números da auditoria (2023, sem cancelados) para uma mudança de base não passar em silêncio.
Sem rede, sem chave, sem navegador.
"""
import math
import os
import sys

import pandas as pd
import pytest

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

from ui import roas                                 # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")


# ================================================================================================
# 1. Sintético
# ================================================================================================
@pytest.fixture
def marketing():
    """X: 2 campanhas de 2023 (rec 800, inv 200); Y: 1 (rec 200, inv 100); o resto deve ficar de fora."""
    return pd.DataFrame({
        "canal": ["X", "X", "Y", "Y", "Y", "Z", "W"],
        "data_inicio": ["2023-03-01", "2023-06-01", "2023-01-01", "2022-12-31", "2024-01-01", "sem data", "2023-05-01"],
        "receita_gerada": [500.0, 300.0, 200.0, 999.0, 999.0, 999.0, 50.0],
        "investimento_reais": [100.0, 100.0, 100.0, 999.0, 999.0, 999.0, 0.0],
    })


@pytest.fixture
def vendas():
    """X: 40 aprovado + 10 aguardando = 50 (o cancelado de 1000 e o pedido de 2024 não contam); Y: 100."""
    return pd.DataFrame({
        "canal": ["X", "X", "X", "X", "Y"],
        "data_pedido": pd.to_datetime(["2023-02-01", "2023-08-01", "2023-09-01", "2024-01-05", "2023-11-30"]),
        "status_pagamento": ["Aprovado", "Aguardando", "Cancelado", "Aprovado", "Aprovado"],
        "receita_liquida": [40.0, 10.0, 1000.0, 1000.0, 100.0],
    })


def test_reportado_soma_por_canal_so_do_ano_e_ignora_investimento_zero(marketing):
    r = roas.roas_reportado(marketing)
    assert list(r.index) == ["X", "Y"]                       # ordem decrescente; W (inv 0) e Z (sem data) fora
    assert r["X"] == pytest.approx(800 / 200)
    assert r["Y"] == pytest.approx(200 / 100)                # 2022 e 2024 não entram


def test_reportado_aceita_outro_ano(marketing):
    r = roas.roas_reportado(marketing, ano=2024)
    assert list(r.index) == ["Y"] and r["Y"] == pytest.approx(1.0)


def test_reconciliado_usa_receita_liquida_sem_cancelados_e_so_do_ano(marketing, vendas):
    r = roas.roas_reconciliado(marketing, vendas)
    assert list(r.index) == ["Y", "X"]                       # a ordem virou em relação ao reportado
    assert r["X"] == pytest.approx(50 / 200)
    assert r["Y"] == pytest.approx(100 / 100)


def test_reconciliado_canal_com_campanha_e_sem_venda_fica_com_zero(marketing, vendas):
    r = roas.roas_reconciliado(marketing, vendas[vendas["canal"] == "X"])
    assert r["Y"] == 0.0 and list(r.index) == ["X", "Y"]


def test_fator_e_atribuida_total_sobre_real_total(marketing, vendas):
    # atribuída dos canais com campanha em 2023: X 800 + Y 200 + W 50 = 1050; real: X 50 + Y 100 (W sem venda) = 150
    assert roas.fator_distorcao(marketing, vendas) == pytest.approx(1050 / 150)


def test_fator_sem_receita_real_e_nan(marketing, vendas):
    assert math.isnan(roas.fator_distorcao(marketing, vendas.iloc[0:0]))


def test_posicao_e_um_baseada_e_empate_fica_com_a_melhor(marketing, vendas):
    r = roas.roas_reportado(marketing)
    assert (roas.posicao(r, "X"), roas.posicao(r, "Y")) == (1, 2)
    empate = pd.Series({"A": 3.0, "B": 3.0, "C": 1.0})
    assert (roas.posicao(empate, "A"), roas.posicao(empate, "B"), roas.posicao(empate, "C")) == (1, 1, 3)


def test_texto_do_aviso_traz_fator_e_posicoes_e_nao_os_valores(marketing, vendas):
    texto = roas.texto_aviso_roas(marketing, vendas, canal="X")
    assert "~7,0x a receita real" in texto                   # 1050/150 = 7,0, vírgula decimal
    assert "o ranking muda (X: 1º → 2º de 2)" in texto
    assert "não para alocar budget" in texto
    assert "0,25" not in texto and "0.25" not in texto       # o valor reconciliado não é exibido


def test_texto_do_aviso_nao_afirma_mudanca_que_nao_existe(marketing):
    vendas_proporcionais = pd.DataFrame({                    # X vende 4x Y: mesma ordem do reportado
        "canal": ["X", "Y"], "data_pedido": pd.to_datetime(["2023-02-01", "2023-02-01"]),
        "status_pagamento": ["Aprovado", "Aprovado"], "receita_liquida": [400.0, 100.0]})
    texto = roas.texto_aviso_roas(marketing, vendas_proporcionais, canal="X")
    assert "o ranking se mantém (X: 1º → 1º de 2)" in texto


def test_texto_do_aviso_e_none_se_nao_da_para_calcular(marketing, vendas):
    assert roas.texto_aviso_roas(marketing, vendas, canal="Canal Inexistente") is None
    assert roas.texto_aviso_roas(marketing, vendas.iloc[0:0], canal="X") is None


def test_aviso_na_tela_usa_warning_e_escapa_cifrao(marketing, vendas, monkeypatch):
    import streamlit as st
    from ui import roas as modulo
    mostrados = []
    monkeypatch.setattr(st, "warning", mostrados.append)
    monkeypatch.setattr(modulo, "texto_aviso_roas", lambda *a, **k: "R$ 5 mil e R$ 6 mil")
    modulo.render_aviso_roas(marketing, vendas)
    assert mostrados == ["R\\$ 5 mil e R\\$ 6 mil"]
    monkeypatch.setattr(modulo, "texto_aviso_roas", lambda *a, **k: None)
    modulo.render_aviso_roas(marketing, vendas)
    assert len(mostrados) == 1                               # sem texto, não desenha nada


# ================================================================================================
# 2. Dados reais: os números da auditoria (2023, sem cancelados)
# ================================================================================================
@pytest.fixture(scope="module")
def reais():
    return (pd.read_csv(os.path.join(DATA_DIR, "marketing.csv")),
            pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"]))


ROAS_REPORTADO = {"Influenciador": 7.48, "TikTok Ads": 4.65, "Instagram Ads": 4.54, "Google Ads": 3.50,
                  "Orgânico": 3.19, "Email Marketing": 3.15, "Marketplace": 2.92}
ROAS_RECONCILIADO = {"Google Ads": 0.3609, "Marketplace": 0.3354, "Instagram Ads": 0.2718, "Orgânico": 0.1878,
                     "Email Marketing": 0.1757, "Influenciador": 0.1753, "TikTok Ads": 0.1729}


def test_real_reportado_bate_com_o_card_do_painel(reais):
    marketing, _ = reais
    r = roas.roas_reportado(marketing)
    assert list(r.index) == list(ROAS_REPORTADO)             # mesma ordem do card
    for canal, esperado in ROAS_REPORTADO.items():
        assert r[canal] == pytest.approx(esperado, abs=0.005), canal


def test_real_reconciliado_e_ranking(reais):
    marketing, vendas = reais
    r = roas.roas_reconciliado(marketing, vendas)
    assert list(r.index) == list(ROAS_RECONCILIADO)
    for canal, esperado in ROAS_RECONCILIADO.items():
        assert r[canal] == pytest.approx(esperado, abs=0.0006), canal
    reportado = roas.roas_reportado(marketing)
    assert (roas.posicao(reportado, "Marketplace"), roas.posicao(r, "Marketplace")) == (7, 2)


def test_real_totais_e_fator(reais):
    marketing, vendas = reais
    campanhas = roas._campanhas_do_ano(marketing, 2023)
    assert len(campanhas) == 1126
    assert campanhas["investimento_reais"].sum() == pytest.approx(69.63e6, abs=0.01e6)
    assert campanhas["receita_gerada"].sum() == pytest.approx(294.26e6, abs=0.01e6)
    assert roas._receita_real_por_canal(vendas, 2023).sum() == pytest.approx(16.67e6, abs=0.01e6)
    assert roas.fator_distorcao(marketing, vendas) == pytest.approx(17.65, abs=0.005)


def test_real_texto_do_aviso(reais):
    marketing, vendas = reais
    assert roas.texto_aviso_roas(marketing, vendas) == (
        "A receita atribuída pelo marketing é ~17,7x a receita real de vendas no mesmo período. "
        "Com a receita real, o ranking muda (Marketplace: 7º → 2º de 7). "
        "Use como indicativo, não para alocar budget.")
