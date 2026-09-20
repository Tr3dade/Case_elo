"""Testes do ui/painel_calculos.py: a base única do gráfico mensal, do donut e da tabela de categorias.

(1) sintético, com a conta feita à mão; (2) dados reais, que travam o fechamento com os KPIs do topo do Painel.
"""
import os
import sys

import pandas as pd
import pytest

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

from ui import painel_calculos as pc                # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")


# ================================================================================================
# 1. Sintético
# ================================================================================================
@pytest.fixture
def vendas():
    return pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4", "O5", "O6"],
        "data_pedido": pd.to_datetime(["2023-01-10", "2023-01-20", "2023-03-05", "2023-03-06", "2024-01-05", "2023-03-07"]),
        "categoria": ["A", "A", "B", "B", "A", "A"],
        "status_pagamento": ["Aprovado", "Aguardando", "Cancelado", "Aprovado", "Aprovado", "Aprovado"],
        "devolvido": [False, False, False, True, False, False],
        "receita_bruta": [110.0, 220.0, 999.0, 500.0, 700.0, 330.0],
        "receita_liquida": [100.0, 200.0, 999.0, 500.0, 700.0, 300.0],
        "margem_contribuicao": [50.0, 100.0, 400.0, 250.0, 350.0, 120.0],
    })


def test_base_valida_tira_cancelado_devolvido_e_outro_ano(vendas):
    assert pc.vendas_validas(vendas)["order_id"].tolist() == ["O1", "O2", "O6"]      # O3 cancelado, O4 devolvido, O5 de 2024


def test_mensal_tem_12_meses_com_zero_e_descontos_e_bruta_menos_liquida(vendas):
    m = pc.mensal(vendas)
    assert m["mes"].tolist() == [f"2023-{i:02d}" for i in range(1, 13)]
    assert m["mes_label"].iloc[:3].tolist() == ["Jan", "Feb", "Mar"]
    assert m["receita_liquida"].tolist() == [300.0, 0.0, 300.0] + [0.0] * 9
    assert m["margem_contribuicao"].iloc[[0, 1, 2]].tolist() == [150.0, 0.0, 120.0]
    assert m["descontos"].iloc[[0, 1, 2]].tolist() == [30.0, 0.0, 30.0]              # bruta - líquida (O1: 10 + O2: 20)


def test_por_categoria_ordena_por_receita_e_calcula_ticket_e_margem(vendas):
    c = pc.por_categoria(vendas)
    assert c.index.tolist() == ["A"]                                                # B só tem cancelado e devolvido
    assert c.loc["A", "receita_liquida"] == 600.0 and c.loc["A", "pedidos"] == 3
    assert c.loc["A", "ticket"] == 200.0
    assert c.loc["A", "margem_pct"] == pytest.approx(270 / 600 * 100)
    assert c.loc["A", "participacao_pct"] == pytest.approx(100.0)


def test_por_categoria_com_duas_categorias_ordena_da_maior_para_a_menor(vendas):
    vendas.loc[vendas["order_id"] == "O3", ["status_pagamento", "receita_liquida"]] = ["Aprovado", 900.0]   # B vira a maior
    c = pc.por_categoria(vendas)
    assert c.index.tolist() == ["B", "A"]
    assert c["participacao_pct"].sum() == pytest.approx(100.0)


# ================================================================================================
# 2. Dados reais: fecha com os KPIs do topo do Painel
# ================================================================================================
@pytest.fixture(scope="module")
def reais():
    return pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"])


def test_real_mensal_fecha_com_os_kpis(reais):
    m = pc.mensal(reais)
    assert m["receita_liquida"].sum() == pytest.approx(14_170_454.54, abs=0.01)
    assert m["margem_contribuicao"].sum() == pytest.approx(7_708_394.41, abs=0.01)
    assert m["receita_bruta"].sum() == pytest.approx(15_401_531.43, abs=0.01)
    assert m["descontos"].sum() == pytest.approx(15_401_531.43 - 14_170_454.54, abs=0.02)


def test_real_categorias_fecham_com_os_kpis_e_com_o_ticket_geral(reais):
    c = pc.por_categoria(reais)
    assert c.index.tolist() == ["Moda", "Beleza", "Lifestyle", "Acessórios"]
    assert c["receita_liquida"].sum() == pytest.approx(14_170_454.54, abs=0.01)
    assert c["margem_contribuicao"].sum() == pytest.approx(7_708_394.41, abs=0.01)
    assert c["ticket"].round().tolist() == [692, 676, 687, 660]
    assert c["receita_liquida"].sum() / c["pedidos"].sum() == pytest.approx(681.53, abs=0.005)   # ticket do card
    assert c["pedidos"].sum() == 20792
