"""Testes do prep_dados.py com um vendas.csv minúsculo escrito na hora (não depende dos dados reais)."""
import pandas as pd

import prep_dados


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
