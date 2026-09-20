"""Testes do prep_dados.py com um vendas.csv minúsculo escrito na hora (não depende dos dados reais)."""
import os

import pandas as pd
import pytest

import prep_dados

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def escrever_vendas(tmp_path):
    linhas = [
        # canais próprios: abaixo de R$ 250 todos pagam; a partir daí, alguns isentos
        ("1", "Google Ads", 100, 100, 30.0),
        ("2", "Google Ads", 260, 260, 0.0),
        ("3", "TikTok Ads", 260, 260, 30.0),
        ("4", "TikTok Ads", 500, 500, 0.0),
        # Marketplace: não pode entrar na rampa nem no perfil dos canais próprios
        ("5", "Marketplace", 500, 500, 30.0),
        ("6", "Marketplace", 100, 100, 30.0),
    ]
    caminho = tmp_path / "vendas.csv"
    pd.DataFrame(linhas, columns=["order_id", "canal", "receita_bruta", "receita_liquida", "custo_frete"]).to_csv(caminho, index=False)
    return str(caminho)


def test_preparar_extrai_so_o_marketplace(tmp_path):
    mkt = prep_dados.preparar(escrever_vendas(tmp_path), str(tmp_path / "mkt.csv"))
    assert len(mkt) == 2 and list(mkt.columns) == ["order_id", "receita_bruta", "receita_liquida", "custo_frete"]


def test_rampa_conta_isentos_por_faixa_e_exclui_marketplace(tmp_path):
    rampa = prep_dados.preparar_rampa(escrever_vendas(tmp_path), str(tmp_path / "rampa.csv")).set_index("faixa_min")
    assert rampa.loc[0, "pedidos_proprios"] == 1 and rampa.loc[0, "pct_isentos"] == 0.0
    assert rampa.loc[250, "pedidos_proprios"] == 2 and rampa.loc[250, "pct_isentos"] == 0.5
    assert rampa.loc[450, "pedidos_proprios"] == 1 and rampa.loc[450, "pct_isentos"] == 1.0
    assert rampa["pedidos_proprios"].sum() == 4          # os 2 do Marketplace ficaram de fora


def test_perfil_tem_uma_linha_por_canal_proprio(tmp_path):
    perfil = prep_dados.preparar_perfil(escrever_vendas(tmp_path), str(tmp_path / "perfil.csv")).set_index("canal")
    assert set(perfil.index) == {"Google Ads", "TikTok Ads"}
    assert perfil.loc["Google Ads", "pct_pedidos_com_frete"] == 50.0
    assert perfil.loc["Google Ads", "frete_pct_receita_liquida"] == round(30 / 360 * 100, 2)


# ================================================================================================
# Versões em memória (usadas pelo front): têm de dar o mesmo resultado das funções que gravam CSV
# ================================================================================================
def test_funcoes_em_memoria_dao_o_mesmo_das_funcoes_de_csv(tmp_path):
    caminho = escrever_vendas(tmp_path)
    vendas = pd.read_csv(caminho)
    pd.testing.assert_frame_equal(prep_dados.pedidos_marketplace(vendas),
                                  prep_dados.preparar(caminho, str(tmp_path / "mkt.csv")))
    pd.testing.assert_frame_equal(prep_dados.rampa_canais_proprios(vendas),
                                  prep_dados.preparar_rampa(caminho, str(tmp_path / "rampa.csv")))
    pd.testing.assert_frame_equal(prep_dados.perfil_canais_proprios(vendas),
                                  prep_dados.preparar_perfil(caminho, str(tmp_path / "perfil.csv")))


def test_preparar_tudo_devolve_pedidos_rampa_e_perfil_lidos_dos_csvs(tmp_path):
    caminho = escrever_vendas(tmp_path)
    pedidos, rampa, perfil = prep_dados.preparar_tudo(pd.read_csv(caminho))
    prep_dados.preparar(caminho, str(tmp_path / "mkt.csv"))
    prep_dados.preparar_rampa(caminho, str(tmp_path / "rampa.csv"))
    prep_dados.preparar_perfil(caminho, str(tmp_path / "perfil.csv"))
    pd.testing.assert_frame_equal(pedidos, pd.read_csv(tmp_path / "mkt.csv"))
    pd.testing.assert_frame_equal(rampa, pd.read_csv(tmp_path / "rampa.csv"))
    pd.testing.assert_frame_equal(perfil, pd.read_csv(tmp_path / "perfil.csv"))


def test_em_memoria_nao_altera_o_dataframe_de_entrada(tmp_path):
    vendas = pd.read_csv(escrever_vendas(tmp_path))
    antes = vendas.copy()
    prep_dados.preparar_tudo(vendas)
    pd.testing.assert_frame_equal(vendas, antes)


def test_em_memoria_sobre_o_vendas_real_e_igual_aos_csvs_commitados():
    """A rede de proteção da integração: o front monta os dados do simulador a partir do vendas.csv que o
    painel já carregou. Se alguém mudar a limpeza dos dados (ou o vendas.csv) e os CSVs derivados ficarem
    para trás, este teste acusa. O painel lê o arquivo com parse_dates: isso não pode mudar o resultado."""
    caminhos = {n: os.path.join(DATA_DIR, n) for n in
                ("vendas.csv", "marketplace_pedidos.csv", "rampa_canais_proprios.csv", "perfil_canais_proprios.csv")}
    if not all(os.path.exists(c) for c in caminhos.values()):
        pytest.skip("dados reais não encontrados em data/")
    vendas = pd.read_csv(caminhos["vendas.csv"], parse_dates=["data_pedido"])   # como o carregar_dados() do app
    pedidos, rampa, perfil = prep_dados.preparar_tudo(vendas)
    pd.testing.assert_frame_equal(pedidos, pd.read_csv(caminhos["marketplace_pedidos.csv"]))
    pd.testing.assert_frame_equal(rampa, pd.read_csv(caminhos["rampa_canais_proprios.csv"]))
    pd.testing.assert_frame_equal(perfil, pd.read_csv(caminhos["perfil_canais_proprios.csv"]))
