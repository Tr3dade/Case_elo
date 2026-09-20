"""Testes do ui/qualidade_dados.py: os números das 7 ressalvas e as frases que os mostram.

(1) sintético, com a conta feita à mão; (2) frases com um dict montado à mão; (3) dados reais, que travam os
números da auditoria. O expander na tela é conferido no AppTest do Painel (test_ui_painel.py).
"""
import os
import sys

import pandas as pd
import pytest

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

from ui import qualidade_dados as q                 # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")


# ================================================================================================
# 1. Sintético
# ================================================================================================
@pytest.fixture
def dados():
    vendas = pd.DataFrame({
        "order_id": ["O1", "O2", "O3", "O4", "O5", "O6"],
        "customer_id": ["C1", "C1", "C1", "C2", "C3", "C4"],
        "data_pedido": pd.to_datetime(["2023-01-10", "2023-05-01", "2023-06-01", "2024-01-05", "2023-07-01", "2023-12-31"]),
        "canal": ["Marketplace", "Marketplace", "Email Marketing", "Marketplace", "Marketplace", "Email Marketing"],
        "status_pagamento": ["Aprovado", "Cancelado", "Aguardando", "Aprovado", "Aguardando", "Aprovado"],
        "devolvido": [False, False, True, False, False, False],
        "receita_bruta": [100.0, 900.0, 50.0, 700.0, 100.0, 50.0],
        "receita_liquida": [100.0, 900.0, 50.0, 700.0, 100.0, 50.0],
        "custo_frete": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0],
    })
    clientes = pd.DataFrame({"customer_id": [f"C{i}" for i in range(1, 11)],
                             "data_cadastro": ["2020-02-01"] + ["2021-01-01"] * 8 + ["2025-03-04"]})
    marketing = pd.DataFrame({
        "canal": ["Marketplace", "Email Marketing"], "data_inicio": ["2023-01-01", "2023-06-01"],
        "data_fim": ["2023-03-01", "2024-02-01"], "receita_gerada": [1000.0, 500.0],
        "investimento_reais": [100.0, 100.0]})
    atendimento = pd.DataFrame({
        "order_id": ["O1", "O9", "O9", "O10", None],       # únicos: O1, O9, O10 (o nulo não conta)
        "data_abertura": pd.to_datetime(["2023-02-01", "2025-01-01", "2024-01-01", "2024-06-01", "2023-03-01"])})
    return {"vendas": vendas, "clientes": clientes, "marketing": marketing, "atendimento": atendimento}


def test_calcular_periodos(dados):
    p = q.calcular_ressalvas(dados)["periodos"]
    assert p["vendas"] == (pd.Timestamp("2023-01-10"), pd.Timestamp("2024-01-05"))
    assert p["marketing"] == (pd.Timestamp("2023-01-01"), pd.Timestamp("2024-02-01"))    # primeiro início, último fim
    assert p["clientes"] == (pd.Timestamp("2020-02-01"), pd.Timestamp("2025-03-04"))
    assert p["atendimento"] == (pd.Timestamp("2023-02-01"), pd.Timestamp("2025-01-01"))


def test_calcular_cobertura_atendimento_e_concentracao(dados):
    r = q.calcular_ressalvas(dados)
    assert (r["clientes_em_vendas"], r["clientes_total"]) == (4, 10)                    # C1..C4
    assert (r["atendimento_sem_venda"], r["atendimento_pedidos"]) == (2, 3)             # O9 e O10 sem venda
    assert (r["top3_pedidos"], r["pedidos_total"], r["clientes_distintos_em_vendas"]) == (5, 6, 4)   # 3+1+1 de 6


def test_calcular_receita_atribuida_e_bases_de_cada_bloco(dados):
    r = q.calcular_ressalvas(dados)
    assert r["receita_atribuida"] == 1500.0
    assert r["receita_real"] == 300.0 and r["fator"] == pytest.approx(5.0)              # 100+100+50+50, sem o cancelado e o de 2024
    assert (r["kpis_pedidos"], r["kpis_receita"]) == (3, 250.0)                         # O1, O5, O6: sem cancelado (O2) e sem devolvido (O3)
    assert r["roas_pedidos"] == 4                                                       # O1, O3, O5, O6: só sem cancelado (a receita é receita_real)
    assert (r["aguardando_pedidos"], r["aguardando_receita"]) == (1, 100.0)             # só O5: o O3 também aguarda, mas foi devolvido (fora da base dos KPIs)
    assert r["pedidos_total"] == 6 and r["simulador_receita"] == 1900.0                 # vendas inteiro, inclui o O4 de 2024
    assert (r["simulador_marketplace"], r["simulador_marketplace_receita"]) == (4, 1800.0)   # O1, O2, O4, O5: todos os status


def test_atendimento_com_todos_os_pedidos_em_vendas_da_zero_sem_venda(dados):
    dados["atendimento"] = dados["atendimento"].iloc[[0]]
    assert q.calcular_ressalvas(dados)["atendimento_sem_venda"] == 0


# ================================================================================================
# 2. Frases
# ================================================================================================
def numeros_de_mentira():
    ts = pd.Timestamp
    return {
        "periodos": {"vendas": (ts("2023-01-01"), ts("2024-01-26")), "marketing": (ts("2023-01-01"), ts("2025-12-31")),
                     "clientes": (ts("2020-01-01"), ts("2025-12-28")), "atendimento": (ts("2023-01-01"), ts("2025-12-31"))},
        "clientes_total": 15000, "clientes_em_vendas": 346, "atendimento_pedidos": 28589, "atendimento_sem_venda": 18724,
        "receita_atribuida": 294_261_133.0, "receita_real": 16_669_816.0, "fator": 17.6523,
        "clientes_distintos_em_vendas": 346, "top3_pedidos": 18611, "pedidos_total": 27759,
        "kpis_pedidos": 20792, "kpis_receita": 14_170_454.0, "roas_pedidos": 24437,
        "aguardando_pedidos": 889, "aguardando_receita": 596_527.0,
        "simulador_periodo": (ts("2023-01-01"), ts("2024-01-26")), "simulador_receita": 18_889_334.0,
        "simulador_marketplace": 6040, "simulador_marketplace_receita": 3_986_568.0}


def test_sao_sete_frases_com_numeros_no_formato_brasileiro():
    textos = q.textos_ressalvas(numeros_de_mentira())
    assert len(textos) == 7
    esperado = ["01/01/2023 a 26/01/2024", "Só 346 dos 15.000 clientes do cadastro (2,3%)",
                "18.724 dos 28.589 pedidos citados no atendimento (65,5%)", "R$ 294,3 mi", "~17,7x", "R$ 16,7 mi",
                "3 maiores IDs concentram 67,0% dos pedidos",
                "(a) Os KPIs do topo, o gráfico mensal, o donut e a tabela de categorias consideram pedidos de 2023 sem "
                "cancelados e sem devolvidos (20.792 pedidos; R$ 14,2 mi de receita líquida)",
                "(b) O card de ROAS considera 2023 sem cancelados, com devolvidos (24.437 pedidos; R$ 16,7 mi)",
                "(c) O Simulador de frete parte do arquivo de vendas inteiro", "27.759 pedidos; R$ 18,9 mi",
                "Marketplace 6.040 pedidos; R$ 4,0 mi",
                "Pedidos aguardando pagamento contam como receita.** Na base dos KPIs são 889 pedidos (4,3% dos pedidos), "
                "R$ 0,6 mi de receita líquida (4,2% da receita)"]
    tela = " ".join(textos)
    for trecho in esperado:
        assert trecho in tela, trecho


def textos_ressalvas_item_6() -> str:
    return q.textos_ressalvas(numeros_de_mentira())[5]


def test_texto_e_sobrio_e_diz_que_as_bases_nao_reconciliam():
    assert "não reconciliam entre si" in q.INTRODUCAO
    tela = " ".join(q.textos_ressalvas(numeros_de_mentira()))
    assert "análises por cliente" in tela.lower() and "comprometidas" in tela
    assert "!" not in tela and "erro" not in tela.lower()      # descreve o medido, sem alarme nem culpado
    assert "Os números dos blocos não são diretamente comparáveis." in textos_ressalvas_item_6()   # a conclusão do item 6
    assert "26.538" not in tela and "O gráfico mensal considera" not in tela       # o gráfico mensal não é mais uma base à parte


# ================================================================================================
# 3. Dados reais: os números da auditoria
# ================================================================================================
@pytest.fixture(scope="module")
def reais():
    return {"vendas": pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"]),
            "clientes": pd.read_csv(os.path.join(DATA_DIR, "clientes.csv")),
            "marketing": pd.read_csv(os.path.join(DATA_DIR, "marketing.csv")),
            "atendimento": pd.read_csv(os.path.join(DATA_DIR, "atendimento.csv"),
                                       parse_dates=["data_abertura", "data_fechamento"])}


def test_real_numeros_da_auditoria(reais):
    r = q.calcular_ressalvas(reais)
    p = r["periodos"]
    assert p["vendas"][0].date().isoformat() == "2023-01-01" and p["vendas"][1].date().isoformat() == "2024-01-26"
    assert p["marketing"][0].date().isoformat() == "2023-01-01" and p["marketing"][1].date().isoformat() == "2025-12-31"
    assert p["clientes"][0].date().isoformat() == "2020-01-01" and p["clientes"][1].date().isoformat() == "2025-12-28"
    assert p["atendimento"][0].date().isoformat() == "2023-01-01" and p["atendimento"][1].date().isoformat() == "2025-12-31"
    assert (r["clientes_em_vendas"], r["clientes_total"]) == (346, 15000)
    assert (r["atendimento_sem_venda"], r["atendimento_pedidos"]) == (18724, 28589)
    assert r["top3_pedidos"] / r["pedidos_total"] == pytest.approx(0.670, abs=0.0005)
    assert r["fator"] == pytest.approx(17.65, abs=0.005)
    assert (r["kpis_pedidos"], r["roas_pedidos"], r["pedidos_total"]) == (20792, 24437, 27759)
    assert r["aguardando_pedidos"] == 889 and r["aguardando_receita"] == pytest.approx(596_526.92, abs=0.01)
    assert r["aguardando_pedidos"] / r["kpis_pedidos"] == pytest.approx(0.0428, abs=0.00005)
    assert r["aguardando_receita"] / r["kpis_receita"] == pytest.approx(0.0421, abs=0.00005)
    assert r["kpis_pedidos"] == r["roas_pedidos"] - 3645                                # 3.645 devolvidos entre os não cancelados
    assert (r["kpis_receita"], r["receita_real"], r["simulador_receita"]) == pytest.approx(
        (14_170_454.54, 16_669_816.75, 18_889_334.01), abs=0.01)
    assert r["simulador_marketplace"] == 6040 and r["simulador_marketplace_receita"] == pytest.approx(3_986_568.87, abs=0.01)
