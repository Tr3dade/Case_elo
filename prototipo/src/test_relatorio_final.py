"""Testes do relatorio_final.py. Sem rede e sem chave: o resultado do agente vem de um agente REAL rodando com
um LLM de mentira (roteiro pronto) sobre dados sintéticos, então o teste também confere o contrato entre
rodar_agente() e montar_relatorio_final(). Os testes com dados reais pulam se os CSVs não existirem.
"""
import json
import os

import pandas as pd
import pytest
from langchain_core.messages import AIMessage

import agente
import relatorio
import relatorio_final
from relatorio import brl
from simulador import simular, simular_politica_observada

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}
RAMPA = pd.DataFrame({"faixa_min": [0, 250, 300, 350, 400, 450], "pedidos_proprios": [10] * 6,
                      "pct_isentos": [0.0, 0.7, 0.85, 0.94, 1.0, 1.0]})


class LLMFalso:
    """Devolve, em ordem, as respostas do roteiro. Roteiro esgotado (ou um erro no roteiro) = API fora do ar."""
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def invoke(self, mensagens):
        if not self.roteiro:
            raise ConnectionError("roteiro esgotado")
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def age(acao, **campos):
    return AIMessage(content=json.dumps({"acao": acao, **campos}), usage_metadata=USO)


def perfil(raciocinio="Ler o perfil."):
    return age("perfil_canais_proprios", raciocinio=raciocinio)


def simula(threshold, raciocinio="Testar."):
    return age("simular_threshold", threshold=threshold, raciocinio=raciocinio)


def conclui(memo, recomendado=275):
    return age("concluir", threshold_recomendado=recomendado, memo=memo)


@pytest.fixture
def dados(monkeypatch):
    """100 pedidos sintéticos, R$ 32 de frete cada, no lugar dos CSVs."""
    valores = [100] * 20 + [260] * 30 + [320] * 30 + [500] * 20
    pedidos = pd.DataFrame({"order_id": range(100), "receita_bruta": valores,
                            "receita_liquida": [v * 0.9 for v in valores], "custo_frete": [32.0] * 100})
    perfil_canais = pd.DataFrame({"canal": ["Canal A"], "pedidos": [10],
                                  "pct_pedidos_com_frete": [20.0], "frete_pct_receita_liquida": [1.0]})
    monkeypatch.setattr(agente, "_carregar_dados", lambda: (pedidos, RAMPA, perfil_canais))
    return pedidos


def memo_para(pedidos, threshold=275):
    return (f"Recomendamos o threshold de R$ {threshold}, com margem recuperada de "
            f"R$ {brl(simular(threshold, pedidos)['margem_recuperada'])}, o mais próximo do alvo. "
            "O cenário de R$ 250 foi descartado por isentar mais que o alvo.")


def rodar(monkeypatch, roteiro):
    """Roda o agente de verdade (LLM de mentira) e devolve o resultado, como o front receberia."""
    llm = LLMFalso(roteiro)
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: llm)
    return agente.rodar_agente()


def fluxo_feliz(dados):
    return [perfil(), simula(250), simula(450), simula(275), conclui(memo_para(dados))]


def secao(rel, id_):
    return next(s for s in rel["secoes"] if s["id"] == id_)["markdown"]


# ---------- estrutura e contrato ----------
def test_estrutura_do_retorno_e_serializavel_em_json(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)

    assert set(rel) == {"titulo", "fallback", "motivo_fallback", "aviso", "threshold_recomendado",
                        "secoes", "tabela", "verificacoes", "markdown"}
    assert [s["id"] for s in rel["secoes"]] == ["recomendacao", "ponto_de_partida", "evidencia", "analise_do_agente",
                                                "alternativas", "premissas", "caminho", "verificacoes"]
    assert all(set(s) == {"id", "titulo", "markdown"} for s in rel["secoes"])
    assert rel["fallback"] is False and rel["aviso"] is None and rel["threshold_recomendado"] == 275
    assert rel["markdown"].startswith("# ") and all(f"## {s['titulo']}" in rel["markdown"] for s in rel["secoes"])
    assert json.loads(json.dumps(rel, ensure_ascii=False)) == rel            # pronto para virar JSON sem conversão


def test_markdown_nao_tem_tag_html_solta(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    assert "<" not in relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)["markdown"]


# ---------- a tabela e os números ----------
def test_tabela_numerica_ordenada_com_a_linha_do_alvo_no_fim(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    alvo = simular_politica_observada(dados, RAMPA)
    tabela = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)["tabela"]

    assert [l["threshold"] for l in tabela] == [250, 275, 450, None]
    assert [l["origem"] for l in tabela] == ["agente", "agente", "agente", "alvo"]
    assert [l["recomendado"] for l in tabela] == [False, True, False, False]
    for l in tabela[:-1]:
        esperado = simular(l["threshold"], dados)
        assert l["margem_recuperada"] == esperado["margem_recuperada"]
        assert l["desvio_pct_isentos"] == round(esperado["pct_pedidos_isentos"] - alvo["pct_pedidos_isentos"], 1)
    assert tabela[-1]["margem_recuperada"] == alvo["margem_recuperada"]


def test_formatacao_e_identica_a_do_caminho_percorrido_do_agente(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    markdown = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)["markdown"]
    for passo in (p for p in resultado["caminho"] if "threshold" in p):
        for campo in ("pct_pedidos_isentos", "frete_pct_receita", "margem_recuperada", "desvio_pct_isentos"):
            assert passo[campo] in markdown, f"{campo}={passo[campo]!r} do passo {passo['passo']} não aparece"


def test_ponto_de_partida_vem_dos_pedidos(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    texto = secao(relatorio_final.montar_relatorio_final(resultado, dados, RAMPA), "ponto_de_partida")
    assert "100,0% dos 100 pedidos" in texto                               # todos pagam frete
    assert "R$ 32,00 por remessa" in texto and "R$ 3.200,00 em frete" in texto
    frete_pct = 3200 / (dados["receita_liquida"].sum()) * 100
    assert f"{frete_pct:.2f}".replace(".", ",") + "%" in texto


def test_alternativas_tem_a_diferenca_de_margem_calculada_pelo_codigo(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    texto = secao(relatorio_final.montar_relatorio_final(resultado, dados, RAMPA), "alternativas")
    m = {t: simular(t, dados)["margem_recuperada"] for t in (250, 275, 450)}
    linha250 = next(l for l in texto.splitlines() if l.startswith("- **R$ 250**"))
    linha450 = next(l for l in texto.splitlines() if l.startswith("- **R$ 450**"))
    assert f"R$ {brl(m[250] - m[275])} a mais em margem que R$ 275" in linha250 and "mais generoso" in linha250
    assert f"R$ {brl(m[275] - m[450])} a menos em margem que R$ 275" in linha450 and "mais restritivo" in linha450
    assert "R$ 275**" not in texto                                         # o recomendado não é "alternativa"


def test_threshold_sem_evidencia_e_sinalizado_na_tabela_e_nas_alternativas(monkeypatch, dados):
    resultado = rodar(monkeypatch, [simula(200), simula(275), conclui(memo_para(dados))])
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)
    assert "R$ 200 (sem evidência)" in secao(rel, "evidencia")
    assert "Sem evidência nos dados: nenhum canal próprio isenta frete abaixo de R$ 250" in secao(rel, "alternativas")


# ---------- memo e verificações ----------
def test_memo_vira_citacao_e_texto_do_modelo_e_protegido(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    resultado["memo"] = "Primeira linha com <5% de desvio.\nSegunda linha."
    texto = secao(relatorio_final.montar_relatorio_final(resultado, dados, RAMPA), "analise_do_agente")
    assert "> Primeira linha com &lt;5% de desvio." in texto and "> Segunda linha." in texto
    assert "<5%" not in texto and "Texto escrito pelo agente" in texto


def test_verificacao_acusa_memo_sem_a_margem_do_recomendado(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    resultado["memo"] = "Recomendamos R$ 275 sem citar a margem."
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)
    assert [v["ok"] for v in rel["verificacoes"]] == [True, True, False, True]
    assert "✗ O memo NÃO cita a margem" in secao(rel, "verificacoes")


def test_verificacoes_todas_ok_no_fluxo_feliz(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)
    assert all(v["ok"] for v in rel["verificacoes"]) and len(rel["verificacoes"]) == 4
    assert secao(rel, "verificacoes").count("✓") == 4


# ---------- fallback: o relatório sai completo mesmo assim ----------
def test_fallback_com_passos_parciais_mostra_aviso_e_calcula_o_recomendado(monkeypatch, dados):
    # o agente simula 450 e a API cai; o threshold de fallback (o equivalente ao alvo: 250 nos dados sintéticos)
    # NÃO foi simulado por ele, então o relatório o calcula agora
    resultado = rodar(monkeypatch, [perfil(), simula(450), ConnectionError("Sandbox fora do ar")])
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)

    assert rel["fallback"] is True and "ConnectionError" in rel["aviso"]
    assert rel["markdown"].split("\n\n")[1].startswith("> **Atenção:**")
    assert [v["ok"] for v in rel["verificacoes"]] == [False, True, True, False]
    recomendado = next(l for l in rel["tabela"] if l["recomendado"])
    assert recomendado["origem"] == "motor"                                # o motor calculou o que o agente não chegou a simular
    assert "Passo 2" in secao(rel, "caminho") and "Nenhum outro" not in secao(rel, "alternativas")
    assert "não veio do agente" in secao(rel, "analise_do_agente")


def test_fallback_sem_nenhuma_acao_ainda_devolve_relatorio_completo(monkeypatch, dados):
    resultado = rodar(monkeypatch, [ConnectionError("Sandbox fora do ar")])
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)
    assert [s["id"] for s in rel["secoes"]][0] == "recomendacao" and len(rel["secoes"]) == 8
    assert secao(rel, "caminho") == "(o agente não executou nenhuma ação)"
    assert secao(rel, "alternativas") == "Nenhum outro cenário foi testado."
    assert [l["origem"] for l in rel["tabela"]] == ["motor", "alvo"]


# ---------- parâmetros ----------
def test_alvo_pre_calculado_evita_recalcular(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    alvo = simular_politica_observada(dados, RAMPA)

    def nao_deveria_ser_chamada(*args, **kwargs):
        raise AssertionError("recalculou o alvo")

    monkeypatch.setattr(relatorio_final, "simular_politica_observada", nao_deveria_ser_chamada)
    rel = relatorio_final.montar_relatorio_final(resultado, dados, RAMPA, alvo=alvo)
    assert rel["threshold_recomendado"] == 275


def test_sem_threshold_recomendado_usa_o_equivalente_ao_alvo(monkeypatch, dados):
    resultado = rodar(monkeypatch, fluxo_feliz(dados))
    resultado["threshold_recomendado"] = None
    esperado = simular_politica_observada(dados, RAMPA)["threshold_equivalente"]
    assert relatorio_final.montar_relatorio_final(resultado, dados, RAMPA)["threshold_recomendado"] == esperado


# ---------- dados reais e números já validados ----------
def test_numeros_reais_do_marketplace(monkeypatch):
    caminho = os.path.join(DATA_DIR, "marketplace_pedidos.csv")
    if not os.path.exists(caminho) or not os.path.exists(os.path.join(DATA_DIR, "rampa_canais_proprios.csv")):
        pytest.skip("rode prep_dados.py antes: os CSVs ainda não existem")
    pedidos = pd.read_csv(caminho)
    rampa = pd.read_csv(os.path.join(DATA_DIR, "rampa_canais_proprios.csv"))
    memo = (f"Recomendamos R$ 275, com margem recuperada de R$ {brl(simular(275, pedidos)['margem_recuperada'])}. "
            "O cenário de R$ 450 foi descartado por isentar bem menos que o alvo.")
    resultado = rodar(monkeypatch, [perfil(), simula(250), simula(450), simula(275), conclui(memo)])
    rel = relatorio_final.montar_relatorio_final(resultado, pedidos, rampa)

    ponto = secao(rel, "ponto_de_partida")
    assert "6.040 pedidos" in ponto and "R$ 196.721,45" in ponto and "4,93%" in ponto     # o ponto de partida validado
    tabela = secao(rel, "evidencia")
    assert "R$ 159.556,45" in tabela and "R$ 153.886,48" in tabela and "R$ 120.030,53" in tabela
    assert "| Alvo (canais próprios) | 78,0% | 1,08% | R$ 153.585,42 |" in tabela
    alternativas = secao(rel, "alternativas")
    assert "R$ 5.669,97 a mais em margem que R$ 275" in alternativas                       # 250 contra 275
    assert "R$ 33.855,95 a menos em margem que R$ 275" in alternativas                     # 450 contra 275
    assert "elimina 78,2% do custo de frete atual" in secao(rel, "recomendacao")
