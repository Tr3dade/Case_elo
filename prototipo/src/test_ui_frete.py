"""Testes do front do Simulador de frete (prototipo/ui/ e a ligação no app.py). Sem navegador, sem rede e sem
chave: o LLM é um roteiro pronto e o Streamlit roda no AppTest (streamlit.testing.v1).

Duas partes: (1) as peças pequenas do ui/simulador_frete.py; (2) o app inteiro no AppTest, com os pacotes reais
(streamlit-echarts) e só o menu lateral trocado por uma função controlável (o option_menu é um componente de
navegador, o AppTest não consegue clicar nele).
"""
import json
import os
import sys

import pandas as pd
import pytest
import streamlit as st
from langchain_core.messages import AIMessage
from streamlit.runtime.scriptrunner import StopException

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

import agente                                       # noqa: E402
import relatorio                                    # noqa: E402
from relatorio import brl                           # noqa: E402
from simulador import simular                       # noqa: E402
from ui import simulador_frete as ui                # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")
USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}


def pedidos_reais():
    return pd.read_csv(os.path.join(DATA_DIR, "marketplace_pedidos.csv"))


def dados_reais():
    return (pedidos_reais(), pd.read_csv(os.path.join(DATA_DIR, "rampa_canais_proprios.csv")),
            pd.read_csv(os.path.join(DATA_DIR, "perfil_canais_proprios.csv")))


class LLMFalso:
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def invoke(self, mensagens):
        if not self.roteiro:
            raise ConnectionError("roteiro esgotado")
        return self.roteiro.pop(0)


def age(acao, **campos):
    return AIMessage(content=json.dumps({"acao": acao, **campos}), usage_metadata=USO)


def roteiro_da_demo():
    """O roteiro combinado: 250, 450, 300, 275 e conclui em 275."""
    memo = (f"Recomendamos o threshold de R$ 275, que recupera R$ {brl(simular(275, pedidos_reais())['margem_recuperada'])} "
            "em margem e aproxima o Marketplace do perfil dos canais próprios. O cenário de R$ 450 foi descartado por ser mais restritivo.")
    return [age("perfil_canais_proprios", raciocinio="Ler o alvo."),
            age("simular_threshold", threshold=250, raciocinio="Limite inferior da rampa."),
            age("simular_threshold", threshold=450, raciocinio="Limite superior da rampa."),
            age("simular_threshold", threshold=300, raciocinio="Refinar entre os limites."),
            age("simular_threshold", threshold=275, raciocinio="Mais perto do alvo."),
            age("concluir", threshold_recomendado=275, memo=memo)]


# ================================================================================================
# 1. Peças pequenas
# ================================================================================================
def test_escapar_cifrao_so_troca_o_cifrao_e_aceita_vazio():
    assert ui.escapar_cifrao("de R$ 250 a R$ 450") == "de R\\$ 250 a R\\$ 450"
    assert ui.escapar_cifrao("sem cifrão") == "sem cifrão"
    assert ui.escapar_cifrao(None) == ""


def test_threshold_restaura_a_copia_guardada_e_nao_sobrescreve_o_valor_do_slider(monkeypatch):
    estado = {}
    monkeypatch.setattr(st, "session_state", estado)
    ui.inicializar_threshold(250)                        # 1ª visita: vale o padrão
    assert estado["threshold_frete"] == 250
    ui.guardar_threshold(300.0)
    estado.pop("threshold_frete")                        # o Streamlit apagou a key do slider ao sair da página
    ui.inicializar_threshold(250)
    assert estado["threshold_frete"] == 300              # voltou o valor guardado, não o padrão
    estado["threshold_frete"] = 350                      # o slider já existe: inicializar não pode pisar nele
    ui.inicializar_threshold(250)
    assert estado["threshold_frete"] == 350


def test_aplicar_threshold_grava_inteiro_no_session_state(monkeypatch):
    estado = {}
    monkeypatch.setattr(st, "session_state", estado)
    ui.aplicar_threshold(275.0)
    assert estado == {"threshold_frete": 275} and isinstance(estado["threshold_frete"], int)


class StatusFalso:
    """Faz o papel do st.status: guarda o que foi escrito. Opcionalmente levanta uma exceção a partir da N-ésima chamada."""
    def __init__(self, levanta=None, a_partir_de=None):
        self.chamadas, self.levanta, self.a_partir_de = [], levanta, a_partir_de

    def _registrar(self, tipo, conteudo):
        if self.levanta is not None and len(self.chamadas) + 1 >= self.a_partir_de:
            raise self.levanta
        self.chamadas.append((tipo, conteudo))

    def update(self, **kwargs):
        self._registrar("update", kwargs)

    def write(self, texto):
        self._registrar("write", texto)


def test_progresso_escreve_o_passo_e_escapa_o_cifrao():
    status = StatusFalso()
    progresso = ui.ProgressoNaTela(status)
    progresso({"tipo": "acao", "passo": 2, "acao": "simular_threshold", "threshold": 250, "raciocinio": "x"})
    detalhe = {"passo": 2, "acao": "simular_threshold", "raciocinio": "Limite inferior.", "threshold": 250,
               "zona_com_evidencia": True, "pct_pedidos_isentos": "81,1%", "frete_pct_receita": "0,93%",
               "margem_recuperada": "R$ 159.556,45", "desvio_pct_isentos": "+3,1 p.p.", "desvio_frete_pct": "-0,15 p.p."}
    progresso({"tipo": "observacao", "passo": 2, "ferramenta": "simular_threshold", "args": {"threshold": 250}, "detalhe": detalhe})

    assert status.chamadas[0][0] == "update" and "simular_threshold com R\\$ 250" in status.chamadas[0][1]["label"]
    texto = status.chamadas[1][1]
    assert "R\\$ 159.556,45" in texto and "R$ 159.556,45" not in texto.replace("\\$", "")
    assert "Justificativa do agente: Limite inferior." in texto


def test_progresso_segura_a_interrupcao_do_streamlit_e_fica_mudo():
    status = StatusFalso(levanta=StopException(), a_partir_de=2)       # a 2ª escrita é "interrompida"
    progresso = ui.ProgressoNaTela(status)
    for passo in (1, 2, 3, 4):
        progresso({"tipo": "chamada_modelo", "passo": passo, "max_passos": 8})
    assert progresso.interrompido is True
    assert len(status.chamadas) == 1                                    # depois da interrupção, nada mais é escrito


def test_progresso_nao_segura_erro_comum_nem_ctrl_c():
    """Erro de exibição comum sobe (o agente o registra e segue); só a exceção de controle do Streamlit é segurada."""
    with pytest.raises(ValueError):
        ui.ProgressoNaTela(StatusFalso(levanta=ValueError("x"), a_partir_de=1))({"tipo": "chamada_modelo", "passo": 1, "max_passos": 8})
    with pytest.raises(KeyboardInterrupt):
        ui.ProgressoNaTela(StatusFalso(levanta=KeyboardInterrupt(), a_partir_de=1))({"tipo": "chamada_modelo", "passo": 1, "max_passos": 8})


def test_agente_termina_normalmente_mesmo_se_a_tela_for_interrompida_no_meio(monkeypatch):
    llm = LLMFalso(roteiro_da_demo())
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kw: llm)
    progresso = ui.ProgressoNaTela(StatusFalso(levanta=StopException(), a_partir_de=3))

    r = agente.rodar_agente(ao_passo=progresso, dados=dados_reais())

    assert progresso.interrompido is True
    assert r["fallback"] is False and r["threshold_recomendado"] == 275 and llm.roteiro == []


# ================================================================================================
# 2. O app inteiro no AppTest
# ================================================================================================
@pytest.fixture
def app(monkeypatch):
    """O app com os pacotes reais, o menu controlado por st.session_state['_pagina'] e o LLM de mentira."""
    import streamlit_option_menu
    from streamlit.testing.v1 import AppTest

    monkeypatch.setattr(streamlit_option_menu, "option_menu",
                        lambda **kwargs: st.session_state.get("_pagina", "Painel do Gestor"))
    llm = LLMFalso(roteiro_da_demo())
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: llm)
    at = AppTest.from_file(os.path.join(PROTOTIPO_DIR, "app.py"), default_timeout=120)
    at.session_state["_pagina"] = "Simulador de frete"
    return at


def texto_da_tela(at) -> str:
    return " ".join(m.value for m in at.markdown)


def sem_excecao(at):
    assert [e.value for e in at.exception] == []


def test_simulador_mostra_os_numeros_ancora_e_o_aviso_de_zona(app):
    app.run()
    sem_excecao(app)
    assert app.slider[0].step == 5 and app.slider[0].value == 250            # o step novo e o default 250
    # cada tripla é (margem recuperada, % isentos, frete/receita) dos cards, em formato do app
    esperado = {250: ("R$ 159.6k", "81.1%", "0.93%"), 275: ("R$ 153.9k", "78.1%", "1.07%"),
                450: ("R$ 120.0k", "61.0%", "1.92%")}
    for threshold, numeros in esperado.items():
        app.slider[0].set_value(threshold).run()
        sem_excecao(app)
        assert app.slider[0].value == threshold
        tela = texto_da_tela(app)
        assert all(n in tela for n in numeros), (threshold, numeros)
        assert [w.value for w in app.warning] == []                            # com evidência: sem aviso

    app.slider[0].set_value(200).run()
    sem_excecao(app)
    avisos = [w.value for w in app.warning]
    assert len(avisos) == 1 and "abaixo do menor threshold observado" in avisos[0]
    assert "R\\$ 200" in avisos[0]                                              # cifrão escapado para o markdown


def test_agente_relatorio_aplicar_e_troca_de_pagina(app):
    app.run()
    sem_excecao(app)
    assert "resultado_agente" not in app.session_state and "relatorio_final" not in app.session_state

    app.button(key="rodar_agente").click().run()
    sem_excecao(app)
    resultado = app.session_state["resultado_agente"]
    relatorio_final = app.session_state["relatorio_final"]
    assert resultado["fallback"] is False and resultado["threshold_recomendado"] == 275
    assert [c["threshold"] for c in resultado["cenarios_testados"]] == [250.0, 450.0, 300.0, 275.0]
    assert relatorio_final["threshold_recomendado"] == 275 and len(relatorio_final["secoes"]) == 8
    assert [s.value for s in app.success] == ["Resposta do agente (IA), sem fallback."]
    tela = texto_da_tela(app)
    assert "estimado: tarifa não confirmada pelo mentor" in " ".join(c.value for c in app.caption)
    assert "Frete grátis no Marketplace" in tela and "\\$" in tela

    # "Aplicar no simulador" muda o slider por callback
    app.button(key="aplicar_threshold_agente").click().run()
    sem_excecao(app)
    assert app.slider[0].value == 275
    assert "R$ 153.9k" in texto_da_tela(app) and "78.1%" in texto_da_tela(app)

    # troca de página e volta: o estado (agente, relatório e slider) sobrevive
    app.session_state["_pagina"] = "Painel do Gestor"
    app.run()
    sem_excecao(app)
    app.session_state["_pagina"] = "Simulador de frete"
    app.run()
    sem_excecao(app)
    assert app.session_state["resultado_agente"]["run_id"] == resultado["run_id"]
    assert app.session_state["relatorio_final"]["titulo"] == relatorio_final["titulo"]
    assert app.slider[0].value == 275
    assert "Frete grátis no Marketplace" in texto_da_tela(app)


def test_botao_do_agente_com_api_fora_do_ar_mostra_fallback(app, monkeypatch):
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: LLMFalso([]))     # roteiro vazio = ConnectionError
    app.run()
    app.button(key="rodar_agente").click().run()
    sem_excecao(app)
    resultado = app.session_state["resultado_agente"]
    assert resultado["fallback"] is True and resultado["threshold_recomendado"] == 275     # equivalente à política observada
    assert any("Fallback" in w.value for w in app.warning)
    assert app.session_state["relatorio_final"]["fallback"] is True


def test_relatorio_rapido_existente_segue_chamando_gerar_relatorio(app, monkeypatch):
    chamadas = []
    monkeypatch.setattr(relatorio, "gerar_relatorio", lambda resultado: chamadas.append(resultado) or "Texto do relatório rápido.")
    app.run()
    app.button[[b.label for b in app.button].index("Gerar recomendação")].click().run()
    sem_excecao(app)
    assert len(chamadas) == 1 and chamadas[0]["threshold"] == 250
    assert "Texto do relatório rápido." in texto_da_tela(app)
