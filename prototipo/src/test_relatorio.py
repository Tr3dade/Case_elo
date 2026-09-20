"""Testes do relatorio.py. Sem rede e sem chave real: o LLM é um dublê (LLMFalso) e o conftest.py
redireciona o prompts_log.md e o uso_api.csv para uma pasta temporária.

O resultado abaixo é o do cenário R$250 já validado (escrito à mão, para o teste não depender dos CSVs).
"""
import pandas as pd
import pytest
from langchain_core.messages import AIMessage

import relatorio
import uso_api

RESULTADO_250 = {
    "threshold": 250,
    "pct_pedidos_isentos": 81.1,
    "margem_recuperada": 159556.45,
    "frete_restante": 37165.0,
    "frete_pct_receita_nova": 0.93,
    "zona_com_evidencia": True,
    "aviso": None,
}
TEXTO_OK = ("Recomendamos o threshold de R$ 250, que recupera R$ 159.556,45 em margem e mantém o "
            "frete restante em 0,93% da receita do canal.")
USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}


class LLMFalso:
    """Faz o papel do ChatLiteLLM: devolve a resposta combinada, ou levanta o erro combinado."""
    def __init__(self, resposta):
        self.resposta = resposta

    def invoke(self, prompt):
        if isinstance(self.resposta, Exception):
            raise self.resposta
        return self.resposta


def usar_llm(monkeypatch, resposta):
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: LLMFalso(resposta))


def log():
    return open(relatorio.LOG_PATH, encoding="utf-8").read()


def uso():
    return pd.read_csv(uso_api.USO_PATH)


# ---------- formatação e prompt ----------
def test_brl_usa_ponto_nos_milhares_e_virgula_nos_centavos():
    assert relatorio.brl(159556.45) == "159.556,45"
    assert relatorio.brl(0.5) == "0,50"
    assert relatorio.brl(1234567.891) == "1.234.567,89"


def test_prompt_usa_formato_brasileiro_e_proibe_pergunta_final():
    prompt = relatorio.montar_prompt(RESULTADO_250)
    assert "159.556,45" in prompt      # e não 159,556.45
    assert "0,93%" in prompt           # e não 0.93%
    assert "81,1%" in prompt
    assert "R$ 250" in prompt
    assert "sem perguntas" in prompt   # v2: o modelo terminava oferecendo uma apresentação


# ---------- gerar_relatorio ----------
def test_fluxo_normal_devolve_resposta_do_llm_loga_e_registra_uso(monkeypatch):
    usar_llm(monkeypatch, AIMessage(content=TEXTO_OK, usage_metadata=USO))

    assert relatorio.gerar_relatorio(RESULTADO_250) == TEXTO_OK

    conteudo = log()
    assert f"**Prompt** ({relatorio.VERSAO_RELATORIO}," in conteudo and "159.556,45" in conteudo
    assert "**Resposta:**" in conteudo and TEXTO_OK in conteudo
    assert "FALLBACK" not in conteudo

    linha = uso().iloc[0]
    assert (linha["origem"], linha["status"]) == ("relatorio", "ok")
    assert (linha["tokens_entrada"], linha["tokens_saida"]) == (10000, 50)
    assert linha["custo_usd"] == pytest.approx(uso_api.custo_usd(10000, 50), abs=1e-6)


def test_falha_da_api_cai_no_texto_reserva_e_marca_no_log(monkeypatch):
    usar_llm(monkeypatch, ConnectionError("Sandbox indisponível"))

    texto = relatorio.gerar_relatorio(RESULTADO_250)

    assert "159.556,45" in texto                          # a tela não quebra e traz o número certo
    assert "Texto-modelo" in texto
    assert "FALLBACK, ConnectionError" in log()           # o log distingue de resposta real
    assert "Sandbox indisponível" not in log()            # mensagem completa não vai pro log
    assert uso().iloc[0]["status"] == "erro:ConnectionError"


@pytest.mark.parametrize("conteudo", ["", "   ", "ok"])
def test_resposta_vazia_ou_curta_cai_no_fallback_mas_conta_o_custo(monkeypatch, conteudo):
    usar_llm(monkeypatch, AIMessage(content=conteudo, usage_metadata=USO))

    texto = relatorio.gerar_relatorio(RESULTADO_250)

    assert "Texto-modelo" in texto and "FALLBACK, RespostaInvalida" in log()
    linha = uso().iloc[0]
    assert linha["status"] == "resposta_invalida" and linha["tokens_entrada"] == 10000   # gastou tokens


def test_log_que_nao_pode_ser_gravado_nao_derruba_o_relatorio(monkeypatch, tmp_path):
    arquivo = tmp_path / "eu_sou_um_arquivo"
    arquivo.write_text("x")
    monkeypatch.setattr(relatorio, "LOG_PATH", str(arquivo / "log.md"))   # "pasta" que é arquivo
    usar_llm(monkeypatch, AIMessage(content=TEXTO_OK, usage_metadata=USO))
    assert relatorio.gerar_relatorio(RESULTADO_250) == TEXTO_OK


# ---------- criar_llm ----------
def test_sem_chave_levanta_erro_claro():
    with pytest.raises(RuntimeError, match="API-KEY"):
        relatorio.criar_llm()


@pytest.mark.parametrize("nome", ["API_KEY", "API-KEY"])
def test_aceita_a_chave_com_underscore_ou_hifen(monkeypatch, nome):
    monkeypatch.setenv(nome, "chave-de-teste")
    assert relatorio.criar_llm(max_tokens=10) is not None


def test_api_base_sem_https_levanta_erro_claro(monkeypatch):
    # o bug que já vivemos: API_BASE = "API-KEY" virava "Connection error" lá no fundo do LiteLLM
    monkeypatch.setenv("API_KEY", "chave-de-teste")
    monkeypatch.setattr(relatorio, "API_BASE", "API-KEY")
    with pytest.raises(ValueError, match="API_BASE"):
        relatorio.criar_llm()


# ---------- auxiliares ----------
def test_texto_da_mensagem_aceita_str_e_lista_de_partes():
    assert relatorio.texto_da_mensagem(AIMessage(content="  oi  ")) == "oi"
    partes = [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]
    assert relatorio.texto_da_mensagem(AIMessage(content=partes)) == "ab"


def test_causa_raiz_desce_ate_o_erro_mais_interno():
    try:
        try:
            raise ValueError("fundo do poço")
        except ValueError as interno:
            raise RuntimeError("meio") from interno
    except RuntimeError as meio:
        topo = ConnectionError("Connection error")
        topo.__cause__ = meio
    assert relatorio._causa_raiz(topo) == "ValueError: fundo do poço"
