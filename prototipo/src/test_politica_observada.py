"""Testes das funções novas do simulador: zona com evidência e cenário 'política observada'.

Dois grupos: testes com dados sintéticos (sempre rodam) e testes contra os dados reais e os números
da análise (pulados se os CSVs ainda não foram gerados por prep_dados.py).
"""
import os

import pandas as pd
import pytest

from simulador import (MENOR_THRESHOLD_OBSERVADO, curva_completa, simular,
                       simular_politica_observada)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def pedidos_sinteticos():
    # 10 pedidos de R$ 100 e 10 de R$ 500, todos com R$ 30 de frete
    valores = [100] * 10 + [500] * 10
    return pd.DataFrame({"receita_bruta": valores, "receita_liquida": valores, "custo_frete": [30.0] * 20})


RAMPA = pd.DataFrame({"faixa_min": [0, 250, 300, 350, 400, 450],
                      "pedidos_proprios": [1] * 6,
                      "pct_isentos": [0.0, 0.7, 0.85, 0.94, 1.0, 1.0]})


# ---------- zona com evidência ----------
def test_abaixo_do_menor_threshold_observado_e_extrapolacao():
    r = simular(200, pedidos_sinteticos())
    assert r["zona_com_evidencia"] is False
    assert "sem precedente" in r["aviso"]


def test_a_partir_do_menor_threshold_observado_tem_evidencia():
    for t in (MENOR_THRESHOLD_OBSERVADO, 275, 450):
        r = simular(t, pedidos_sinteticos())
        assert r["zona_com_evidencia"] is True and r["aviso"] is None


def test_curva_completa_carrega_a_sinalizacao():
    curva = curva_completa([200, 250], pedidos_sinteticos())
    assert list(curva["zona_com_evidencia"]) == [False, True]


def test_simular_devolve_tipos_nativos_para_serializar_em_json():
    import json
    json.dumps(simular(250, pedidos_sinteticos()))   # não pode levantar (np.float64/np.bool_ quebrariam)


# ---------- política observada (sintético) ----------
def test_politica_observada_nao_isenta_pedido_abaixo_de_250():
    r = simular_politica_observada(pedidos_sinteticos(), RAMPA)
    # só os 10 pedidos de R$ 500 (probabilidade 1) recuperam frete: 10 x R$ 30
    assert r["margem_recuperada"] == 300.0
    assert r["pct_pedidos_isentos"] == 50.0
    assert r["frete_restante"] == 300.0


def test_pedido_exatamente_no_limite_da_faixa_usa_a_faixa_de_cima():
    pedidos = pd.DataFrame({"receita_bruta": [250.0], "receita_liquida": [250.0], "custo_frete": [100.0]})
    assert simular_politica_observada(pedidos, RAMPA)["margem_recuperada"] == 70.0   # 0,70 x 100 = faixa [250,300)


def test_threshold_equivalente_e_multiplo_de_5_e_reproduz_o_cenario():
    r = simular_politica_observada(pedidos_sinteticos(), RAMPA)
    assert r["threshold_equivalente"] % 5 == 0
    assert simular(r["threshold_equivalente"], pedidos_sinteticos())["margem_recuperada"] == r["margem_recuperada"]


# ---------- dados reais e números da análise ----------
@pytest.fixture
def dados_reais():
    arquivos = ["marketplace_pedidos.csv", "rampa_canais_proprios.csv"]
    if not all(os.path.exists(os.path.join(DATA_DIR, a)) for a in arquivos):
        pytest.skip("rode `python prep_dados.py` para gerar os CSVs derivados")
    return [pd.read_csv(os.path.join(DATA_DIR, a)) for a in arquivos]


def test_politica_observada_bate_com_a_analise(dados_reais):
    pedidos, rampa = dados_reais
    r = simular_politica_observada(pedidos, rampa)
    assert r["margem_recuperada"] == pytest.approx(153585.42, abs=1.0)
    assert r["pct_pedidos_isentos"] == 78.0
    assert r["frete_pct_receita_nova"] == 1.08
    assert r["threshold_equivalente"] == 275


def test_politica_observada_fica_entre_os_dois_cenarios_validados(dados_reais):
    pedidos, rampa = dados_reais
    margem = simular_politica_observada(pedidos, rampa)["margem_recuperada"]
    assert simular(450, pedidos)["margem_recuperada"] < margem < simular(250, pedidos)["margem_recuperada"]


def test_constante_bate_com_a_rampa_dos_dados(dados_reais):
    _, rampa = dados_reais
    primeira_com_isencao = rampa[rampa["pct_isentos"] > 0]["faixa_min"].min()
    assert primeira_com_isencao == MENOR_THRESHOLD_OBSERVADO


def test_margem_recuperada_nunca_sobe_com_o_threshold(dados_reais):
    # a propriedade que motivou a "zona com evidência": sem contrapeso, threshold menor sempre "ganha"
    pedidos, _ = dados_reais
    margens = [simular(t, pedidos)["margem_recuperada"] for t in range(0, 1501, 10)]
    assert all(a >= b for a, b in zip(margens, margens[1:]))
