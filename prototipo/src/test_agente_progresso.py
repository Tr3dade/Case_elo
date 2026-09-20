"""Testes dos dois parâmetros opcionais de agente.rodar_agente: ao_passo (progresso para o front) e
dados (DataFrames em memória no lugar dos CSVs). Sem rede: o LLM é um roteiro pronto, como em test_agente.py.

O que estes testes protegem: (1) a sequência de eventos que a tela recebe; (2) que um callback quebrado
NUNCA derruba o agente nem muda o resultado; (3) que passar `dados` não lê os CSVs.
"""
import json
import re

import pandas as pd
import pytest
from langchain_core.messages import AIMessage

import agente
import relatorio
from relatorio import brl
from simulador import simular

USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}
RAMPA = pd.DataFrame({"faixa_min": [0, 250, 300, 350, 400, 450], "pedidos_proprios": [10] * 6,
                      "pct_isentos": [0.0, 0.7, 0.85, 0.94, 1.0, 1.0]})
PERFIL = pd.DataFrame({"canal": ["Canal A"], "pedidos": [10],
                       "pct_pedidos_com_frete": [20.0], "frete_pct_receita_liquida": [1.0]})


class LLMFalso:
    """Devolve, em ordem, as respostas do roteiro. Roteiro esgotado = API fora do ar."""
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def invoke(self, mensagens):
        if not self.roteiro:
            raise ConnectionError("roteiro esgotado")
        return self.roteiro.pop(0)


def age(acao, **campos):
    return AIMessage(content=json.dumps({"acao": acao, **campos}), usage_metadata=USO)


def diz(texto):
    return AIMessage(content=texto, usage_metadata=USO)


@pytest.fixture
def pedidos():
    valores = [100] * 20 + [260] * 30 + [320] * 30 + [500] * 20
    return pd.DataFrame({"order_id": range(100), "receita_bruta": valores,
                         "receita_liquida": [v * 0.9 for v in valores], "custo_frete": [32.0] * 100})


@pytest.fixture
def dados(pedidos):
    return pedidos, RAMPA, PERFIL


@pytest.fixture(autouse=True)
def sem_csv(monkeypatch):
    """Estes testes passam `dados` explicitamente: se algo tentar ler os CSVs, o teste acusa."""
    def proibido():
        raise AssertionError("não devia ler os CSVs quando dados= é passado")
    monkeypatch.setattr(agente, "_carregar_dados", proibido)


def usar_roteiro(monkeypatch, roteiro):
    llm = LLMFalso(roteiro)
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: llm)
    return llm


def memo_valido(pedidos, threshold=275):
    return (f"Recomendamos o threshold de R$ {threshold}, que recupera "
            f"R$ {brl(simular(threshold, pedidos)['margem_recuperada'])} em margem e aproxima o Marketplace "
            "do perfil dos canais próprios. O cenário de R$ 450 foi descartado por ser mais restritivo.")


def roteiro_feliz(pedidos):
    """O roteiro da demonstração: perfil, 250, 450, 300, 275 e conclui em 275."""
    return [age("perfil_canais_proprios", raciocinio="Ler o alvo."),
            age("simular_threshold", threshold=250, raciocinio="Limite inferior."),
            age("simular_threshold", threshold=450, raciocinio="Limite superior."),
            age("simular_threshold", threshold=300, raciocinio="Refinar entre os limites."),
            age("simular_threshold", threshold=275, raciocinio="Mais perto do alvo."),
            age("concluir", threshold_recomendado=275, memo=memo_valido(pedidos))]


class Coletor:
    """Guarda os eventos que o agente entrega ao callback."""
    def __init__(self):
        self.eventos = []

    def __call__(self, evento):
        self.eventos.append(evento)

    def tipos(self):
        return [e["tipo"] for e in self.eventos]


def log():
    return open(relatorio.LOG_PATH, encoding="utf-8").read()


def normalizado(texto):
    """O log com data/hora e run_id trocados por marcadores (mudam a cada execução)."""
    texto = re.sub(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "<DATA>", texto)
    return re.sub(r"run \d{8}-\d{6}-[0-9a-f]{4}", "run <RUN>", texto)


# ================================================================================================
# ao_passo: a sequência de eventos
# ================================================================================================
def test_eventos_do_fluxo_feliz_na_ordem_esperada(monkeypatch, dados, pedidos):
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    coletor = Coletor()

    r = agente.rodar_agente(ao_passo=coletor, dados=dados)

    assert coletor.tipos() == (["inicio"]
                               + ["chamada_modelo", "acao", "observacao"] * 5      # perfil + 4 simulações
                               + ["chamada_modelo", "acao", "fim"])                 # concluir
    assert all("passo" in e for e in coletor.eventos)
    assert [e["passo"] for e in coletor.eventos if e["tipo"] == "chamada_modelo"] == [1, 2, 3, 4, 5, 6]

    inicio = coletor.eventos[0]
    assert inicio["run_id"] == r["run_id"] and inicio["passo"] == 0 and inicio["max_passos"] == agente.MAX_PASSOS

    acoes = [e for e in coletor.eventos if e["tipo"] == "acao"]
    assert [(a["acao"], a["threshold"]) for a in acoes] == [
        ("perfil_canais_proprios", None), ("simular_threshold", 250), ("simular_threshold", 450),
        ("simular_threshold", 300), ("simular_threshold", 275), ("concluir", None)]
    assert acoes[1]["raciocinio"] == "Limite inferior." and acoes[-1]["threshold_recomendado"] == 275

    fim = coletor.eventos[-1]
    assert fim["fallback"] is False and fim["threshold_recomendado"] == 275 and fim["segundos"] >= 0


def test_evento_de_observacao_traz_o_passo_estruturado_igual_ao_caminho(monkeypatch, dados, pedidos):
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    coletor = Coletor()

    r = agente.rodar_agente(ao_passo=coletor, dados=dados)

    observacoes = [e for e in coletor.eventos if e["tipo"] == "observacao"]
    assert [o["detalhe"] for o in observacoes] == r["caminho"]        # o front pode mostrar já formatado
    assert observacoes[1]["ferramenta"] == "simular_threshold" and observacoes[1]["args"] == {"threshold": 250}
    assert observacoes[1]["detalhe"]["margem_recuperada"].startswith("R$ ")


def test_eventos_de_resposta_invalida_e_fallback(monkeypatch, dados):
    usar_roteiro(monkeypatch, [diz("não sei"), diz("ainda não sei")])      # 2 respostas fora do protocolo
    coletor = Coletor()

    r = agente.rodar_agente(ao_passo=coletor, dados=dados)

    assert coletor.tipos() == ["inicio", "chamada_modelo", "resposta_invalida", "chamada_modelo",
                               "resposta_invalida", "fallback", "fim"]
    invalida = coletor.eventos[2]
    assert invalida["passo"] == 1 and "JSON" in invalida["motivo"]
    fallback = next(e for e in coletor.eventos if e["tipo"] == "fallback")
    assert fallback["motivo"] == r["motivo_fallback"] and fallback["threshold"] == r["threshold_recomendado"]
    assert coletor.eventos[-1]["fallback"] is True


def test_evento_de_memo_recusado_antes_da_correcao(monkeypatch, dados, pedidos):
    memo_inventado = "Recomendamos o threshold de R$ 275, que recupera R$ 999.999,99 em margem. " * 2
    usar_roteiro(monkeypatch, [age("perfil_canais_proprios"), age("simular_threshold", threshold=250),
                               age("concluir", threshold_recomendado=250, memo=memo_inventado),
                               age("concluir", threshold_recomendado=250, memo=memo_valido(pedidos, 250))])
    coletor = Coletor()

    r = agente.rodar_agente(ao_passo=coletor, dados=dados)

    recusado = [e for e in coletor.eventos if e["tipo"] == "memo_recusado"]
    assert len(recusado) == 1 and recusado[0]["passo"] == 3 and "threshold testado" in recusado[0]["motivo"]
    assert r["fallback"] is False and r["threshold_recomendado"] == 250
    assert coletor.tipos()[-1] == "fim"


def test_sem_callback_o_agente_roda_igual(monkeypatch, dados, pedidos):
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    r = agente.rodar_agente(dados=dados)                    # ao_passo=None: o comportamento de sempre
    assert r["fallback"] is False and r["threshold_recomendado"] == 275


# ================================================================================================
# ao_passo: um callback quebrado nunca derruba o agente nem muda o resultado
# ================================================================================================
def resultado_sem_o_que_varia(r):
    return {k: v for k, v in r.items() if k not in ("run_id", "segundos")}


def test_callback_que_levanta_excecao_nao_derruba_nem_altera_o_resultado(monkeypatch, tmp_path, dados, pedidos, caplog):
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    referencia = agente.rodar_agente(dados=dados)
    log_referencia = normalizado(log())

    monkeypatch.setattr(relatorio, "LOG_PATH", str(tmp_path / "log_com_callback.md"))
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))

    def quebrado(evento):
        raise ValueError(f"tela quebrou no evento {evento['tipo']}")

    with caplog.at_level("WARNING", logger="agente"):
        r = agente.rodar_agente(ao_passo=quebrado, dados=dados)

    assert resultado_sem_o_que_varia(r) == resultado_sem_o_que_varia(referencia)
    assert normalizado(log()) == log_referencia                       # o log é idêntico, byte a byte
    avisos = [m for m in caplog.messages if "ao_passo falhou" in m]
    assert len(avisos) == 1 + 5 * 3 + 3                               # um por evento: nenhum passou em branco
    assert "ValueError" in avisos[0]


def test_callback_que_quebra_so_no_meio_deixa_o_agente_concluir(monkeypatch, dados, pedidos):
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    recebidos = []

    def quebra_na_terceira_chamada(evento):
        recebidos.append(evento["tipo"])
        if evento["tipo"] == "chamada_modelo" and evento["passo"] == 3:
            raise RuntimeError("falha pontual")

    r = agente.rodar_agente(ao_passo=quebra_na_terceira_chamada, dados=dados)

    assert r["fallback"] is False and r["threshold_recomendado"] == 275
    assert recebidos[-1] == "fim"                                     # e os eventos seguintes continuaram chegando


# ================================================================================================
# dados: DataFrames em memória no lugar dos CSVs
# ================================================================================================
def test_dados_em_memoria_sao_usados_no_lugar_dos_csvs(monkeypatch, dados, pedidos):
    llm = usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    r = agente.rodar_agente(dados=dados)                              # a fixture sem_csv falha se ler os CSVs
    assert r["fallback"] is False and [c["threshold"] for c in r["cenarios_testados"]] == [250.0, 450.0, 300.0, 275.0]
    # o alvo que o modelo viu veio dos dados passados (a rampa sintética), não dos CSVs reais
    observacao_perfil = r["trilha"][0]["observacao"]
    assert json.loads(observacao_perfil)["canais_proprios"][0]["canal"] == "Canal A"
    assert llm.roteiro == []


def test_sem_dados_continua_lendo_os_csvs(monkeypatch, pedidos):
    """dados=None é o padrão de sempre: chama _carregar_dados()."""
    chamou = []

    def carregar():
        chamou.append(True)
        return pedidos, RAMPA, PERFIL

    monkeypatch.setattr(agente, "_carregar_dados", carregar)
    usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    agente.rodar_agente()
    assert chamou == [True]


def test_assinatura_manteve_a_missao_como_primeiro_argumento(monkeypatch, dados, pedidos):
    """Quem já chamava rodar_agente("missão") segue funcionando."""
    llm = usar_roteiro(monkeypatch, roteiro_feliz(pedidos))
    inspecionadas = []
    original = llm.invoke
    llm.invoke = lambda mensagens: (inspecionadas.append(mensagens[0].content), original(mensagens))[1]
    agente.rodar_agente("Missão personalizada de teste.", dados=dados)
    assert "MISSÃO: Missão personalizada de teste." in inspecionadas[0]
