"""Testes do uso_api.py: custo, gravação do CSV e resumo. Sem rede."""
import pandas as pd
import pytest
from langchain_core.messages import AIMessage

import uso_api


def test_custo_do_exemplo_combinado():
    # 10.000 tokens de entrada + 200 de saída = US$ 0,0056
    assert uso_api.custo_usd(10000, 200) == pytest.approx(0.0056)


def test_tarifa_reproduz_linhas_do_painel_da_sandbox():
    # (entrada, saída, custo mostrado no painel "My consumption"); tolerância = arredondamento do painel
    painel = [(23400, 1100, 0.0149), (18800, 2500, 0.0169), (20000, 1100, 0.0134), (19300, 622, 0.0115),
              (17700, 1500, 0.0135), (16300, 1300, 0.0121), (16000, 2600, 0.0159), (16800, 662, 0.0104)]
    for entrada, saida, custo in painel:
        assert uso_api.custo_usd(entrada, saida) == pytest.approx(custo, abs=0.00015)


def test_extrair_uso():
    msg = AIMessage(content="x", usage_metadata={"input_tokens": 10, "output_tokens": 3, "total_tokens": 13})
    assert uso_api.extrair_uso(msg) == (10, 3)
    assert uso_api.extrair_uso(AIMessage(content="sem uso")) == (0, 0)
    assert uso_api.extrair_uso(object()) == (0, 0)


def test_registro_cria_cabecalho_uma_vez_e_acumula_linhas():
    uso_api.registrar_chamada("r1", "agente", 1, "m", 10000, 100, 1.5)
    uso_api.registrar_chamada("r1", "agente", 2, "m", 11000, 300, 2.0)
    uso = pd.read_csv(uso_api.USO_PATH)
    assert list(uso.columns) == uso_api.COLUNAS
    assert len(uso) == 2
    assert open(uso_api.USO_PATH, encoding="utf-8").read().count("data_hora") == 1


def test_resumo_soma_por_origem_e_filtra_por_execucao(monkeypatch):
    monkeypatch.setattr(uso_api, "COTACAO_USD_BRL", 5.0)
    uso_api.registrar_chamada("r1", "agente", 1, "m", 10000, 200, 1.0)
    uso_api.registrar_chamada("r1", "agente", 2, "m", 10000, 200, 1.0)
    uso_api.registrar_chamada("r2", "relatorio", 1, "m", 10000, 200, 1.0)

    geral = uso_api.resumo_uso()
    assert geral["chamadas"] == 3 and geral["execucoes"] == 2
    assert geral["custo_usd"] == pytest.approx(3 * 0.0056)
    assert geral["custo_brl"] == pytest.approx(3 * 0.0056 * 5.0)
    assert geral["por_origem"]["agente"]["chamadas"] == 2

    so_r1 = uso_api.resumo_uso("r1")
    assert so_r1["chamadas"] == 2 and so_r1["custo_usd"] == pytest.approx(2 * 0.0056)


def test_resumo_sem_arquivo_e_sem_cotacao():
    assert uso_api.resumo_uso() == {"chamadas": 0}
    uso_api.registrar_chamada("r1", "agente", 1, "m", 1000, 10, 0.5)
    assert uso_api.resumo_uso()["custo_brl"] is None     # cotação não preenchida


def test_falha_ao_gravar_nao_derruba_o_fluxo(monkeypatch, tmp_path):
    arquivo = tmp_path / "eu_sou_um_arquivo"
    arquivo.write_text("x")
    monkeypatch.setattr(uso_api, "USO_PATH", str(arquivo / "uso.csv"))   # "pasta" que é arquivo
    uso_api.registrar_chamada("r1", "agente", 1, "m", 1, 1, 0.1)         # não pode levantar
