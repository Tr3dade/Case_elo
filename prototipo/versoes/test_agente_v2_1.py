"""Testes do agente.py (versão agente-v2.1). Sem rede: o LLM é um roteiro pronto (LLMFalso) e os dados
são sintéticos, então a suíte roda em segundos e sem gastar tokens.

O roteiro é a lista de respostas que o "modelo" dará, uma por chamada. No protocolo em texto cada
resposta é um objeto JSON com a ação (ou texto solto, para testar respostas fora do protocolo).
Cada teste monta o roteiro que exercita um caminho: fluxo feliz, raciocinio, caminho percorrido,
threshold recomendado, memo com número inventado, threshold sem evidência, limites, erro da API...

A última seção (VERSÃO) é a única que difere entre a v2.1 e a v3: ela confere o prompt de cada versão.
"""
import json
import os

import pandas as pd
import pytest
from langchain_core.messages import AIMessage, HumanMessage

import agente
import relatorio
import uso_api
from relatorio import brl
from simulador import simular, simular_politica_observada

USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


class LLMFalso:
    """Faz o papel do ChatLiteLLM: devolve, em ordem, as respostas do roteiro e guarda o histórico
    de mensagens recebido em cada chamada. Roteiro esgotado = API fora do ar."""
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.chamadas = []           # cópia do histórico de mensagens em cada invoke

    def invoke(self, mensagens):
        self.chamadas.append(list(mensagens))
        if not self.roteiro:
            raise ConnectionError("roteiro esgotado")
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def diz(texto):
    return AIMessage(content=texto, usage_metadata=USO)


def age(acao, **campos):
    return diz(json.dumps({"acao": acao, **campos}))


def perfil(raciocinio=None):
    return age("perfil_canais_proprios", **({"raciocinio": raciocinio} if raciocinio else {}))


def simula(threshold, raciocinio=None):
    campos = {"threshold": threshold}
    if raciocinio:
        campos["raciocinio"] = raciocinio
    return age("simular_threshold", **campos)


def conclui(memo, recomendado=None):
    campos = {"memo": memo}
    if recomendado is not None:
        campos["threshold_recomendado"] = recomendado
    return age("concluir", **campos)


RAMPA = pd.DataFrame({"faixa_min": [0, 250, 300, 350, 400, 450], "pedidos_proprios": [10] * 6,
                      "pct_isentos": [0.0, 0.7, 0.85, 0.94, 1.0, 1.0]})


@pytest.fixture
def dados(monkeypatch):
    """Dados sintéticos no lugar dos CSVs: 100 pedidos, R$ 32 de frete cada."""
    valores = [100] * 20 + [260] * 30 + [320] * 30 + [500] * 20
    pedidos = pd.DataFrame({"order_id": range(100), "receita_bruta": valores,
                            "receita_liquida": [v * 0.9 for v in valores], "custo_frete": [32.0] * 100})
    perfil_canais = pd.DataFrame({"canal": ["Canal A"], "pedidos": [10],
                                  "pct_pedidos_com_frete": [20.0], "frete_pct_receita_liquida": [1.0]})
    monkeypatch.setattr(agente, "_carregar_dados", lambda: (pedidos, RAMPA, perfil_canais))
    return pedidos


def usar_roteiro(monkeypatch, roteiro):
    llm = LLMFalso(roteiro)
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: llm)
    return llm


def memo_valido(pedidos, threshold=275):
    return (f"Recomendamos o threshold de R$ {threshold}, que recupera "
            f"R$ {brl(simular(threshold, pedidos)['margem_recuperada'])} em margem e aproxima o Marketplace "
            "do perfil dos canais próprios. O cenário de R$ 250 foi descartado por ser mais generoso.")


MEMO_INVENTADO = "Recomendamos o threshold de R$ 275, que recupera R$ 999.999,99 em margem. " * 2


def log():
    return open(relatorio.LOG_PATH, encoding="utf-8").read()


def linhas_de_uso():
    return pd.read_csv(uso_api.USO_PATH)


def cenarios_testados_para(dados, *thresholds):
    return {float(t): simular(t, dados) for t in thresholds}


# ================================================================================================
# Fluxo feliz
# ================================================================================================
def test_fluxo_feliz(monkeypatch, dados):
    llm = usar_roteiro(monkeypatch, [
        perfil("Preciso ver a política dos canais próprios e o alvo."),
        simula(250, "Limite inferior observado nos canais próprios."),
        simula(275, "Entre os extremos, mais perto do alvo."),
        conclui(memo_valido(dados), recomendado=275)])

    r = agente.rodar_agente()

    assert r["fallback"] is False and r["motivo_fallback"] is None
    assert [c["threshold"] for c in r["cenarios_testados"]] == [250.0, 275.0]
    assert r["passos"] == 4 and r["chamadas_tool"] == 3
    assert [t["ferramenta"] for t in r["trilha"]] == ["perfil_canais_proprios", "simular_threshold", "simular_threshold"]
    assert r["trilha"][1]["args"] == {"threshold": 250}                 # o raciocinio não é argumento
    assert r["trilha"][1]["raciocinio"] == "Limite inferior observado nos canais próprios."
    assert r["threshold_recomendado"] == 275
    assert "R$ 275" in r["memo"] and r["segundos"] >= 0
    assert r["versao_prompt"] == agente.VERSAO_AGENTE

    # a primeira mensagem carrega as instruções e a missão; cada observação volta como mensagem do usuário
    assert isinstance(llm.chamadas[0][0], HumanMessage) and "MISSÃO:" in llm.chamadas[0][0].content
    segunda_volta = llm.chamadas[1]
    assert isinstance(segunda_volta[-1], HumanMessage) and segunda_volta[-1].content.startswith("OBSERVAÇÃO (perfil_canais_proprios)")
    # o histórico alterna usuário/modelo (requisito do protocolo de chat) e nunca carrega tool_calls
    assert [type(m).__name__ for m in llm.chamadas[-1]] == ["HumanMessage", "AIMessage"] * 3 + ["HumanMessage"]

    # uma linha de uso por chamada ao modelo, todas do agente e da mesma execução
    uso = linhas_de_uso()
    assert len(uso) == 4 and set(uso["origem"]) == {"agente"} and set(uso["run_id"]) == {r["run_id"]}
    assert uso["tokens_entrada"].sum() == 40000 and set(uso["status"]) == {"ok"}

    assert f"Agente [{agente.VERSAO_AGENTE}]" in log() and "**Resultado:** ok" in log()


def test_aceita_json_em_cerca_de_codigo_e_com_texto_solto(monkeypatch, dados):
    usar_roteiro(monkeypatch, [
        diz('```json\n{"acao": "simular_threshold", "threshold": 275}\n```'),
        diz("Pronto, concluo agora: " + json.dumps({"acao": "concluir", "memo": memo_valido(dados)}) + " Obrigado!"),
    ])
    r = agente.rodar_agente()
    assert r["fallback"] is False and r["passos"] == 2


def test_observacao_da_simulacao_traz_numeros_no_formato_brasileiro_e_desvio(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(250), conclui("x" * 50)])
    r = agente.rodar_agente()
    obs = json.loads(r["trilha"][0]["observacao"])
    assert obs["margem_recuperada"] == f"R$ {brl(simular(250, dados)['margem_recuperada'])}"
    assert obs["zona_com_evidencia"] is True
    assert "p.p." in obs["desvio_vs_alvo"]["pct_pedidos_isentos"]


def test_observacao_do_perfil_traz_o_alvo(monkeypatch, dados):
    usar_roteiro(monkeypatch, [perfil(), conclui("x" * 50)])
    obs = json.loads(agente.rodar_agente()["trilha"][0]["observacao"])
    alvo = simular_politica_observada(dados, RAMPA)
    assert obs["alvo_marketplace"]["margem_recuperada"] == f"R$ {brl(alvo['margem_recuperada'])}"
    assert obs["menor_threshold_observado"] == "R$ 250" and len(obs["rampa_isencao_canais_proprios"]) == 6


def test_perfil_traz_o_que_o_modelo_precisa_para_deduzir_os_extremos(monkeypatch, dados):
    # É o que torna a v3 possível: os dois extremos estão escritos na observação, não no prompt.
    usar_roteiro(monkeypatch, [perfil(), conclui("x" * 50)])
    obs = json.loads(agente.rodar_agente()["trilha"][0]["observacao"])
    rampa = obs["rampa_isencao_canais_proprios"]
    assert obs["menor_threshold_observado"] == "R$ 250"                       # limite inferior
    assert rampa[0]["pct_isentos"] == "0,0%" and rampa[0]["faixa"].startswith("abaixo de")
    assert rampa[-1]["pct_isentos"] == "100,0%" and rampa[-1]["faixa"].startswith("a partir de")   # onde satura


# ================================================================================================
# raciocinio: a justificativa declarada pelo modelo em cada ação
# ================================================================================================
def test_raciocinio_vai_para_a_trilha_o_log_e_o_caminho_mas_nao_para_os_argumentos(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(250, "Limite inferior observado."), conclui("x" * 50)])
    r = agente.rodar_agente()
    assert r["trilha"][0]["args"] == {"threshold": 250}
    assert r["trilha"][0]["raciocinio"] == "Limite inferior observado."
    assert "↳ raciocínio: Limite inferior observado." in log()
    assert "Justificativa do agente: Limite inferior observado." in r["caminho_texto"]


@pytest.mark.parametrize("valor", [None, 42, ["a"], {"x": 1}, ""])
def test_raciocinio_ausente_ou_de_tipo_errado_vira_vazio_e_nao_invalida_o_turno(monkeypatch, dados, valor):
    usar_roteiro(monkeypatch, [diz(json.dumps({"acao": "simular_threshold", "threshold": 250, "raciocinio": valor})),
                               conclui("x" * 50)])
    r = agente.rodar_agente()
    assert r["trilha"][0]["raciocinio"] == "" and r["trilha"][0]["args"] == {"threshold": 250}
    assert list(linhas_de_uso()["status"])[0] == "ok"                       # o turno continuou válido


def test_raciocinio_longo_e_cortado_e_espacos_sao_normalizados(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(250, "palavra   " * 100), conclui("x" * 50)])
    raciocinio = agente.rodar_agente()["trilha"][0]["raciocinio"]
    assert len(raciocinio) <= agente.MAX_RACIOCINIO and raciocinio.endswith("…") and "  " not in raciocinio


# ================================================================================================
# threshold_recomendado
# ================================================================================================
def test_threshold_recomendado_prefere_o_campo_declarado_ao_primeiro_da_memo(monkeypatch, dados):
    margem = brl(simular(275, dados)["margem_recuperada"])
    memo = (f"O cenário de R$ 250 foi descartado por ser mais generoso. Recomendamos R$ 275, com margem "
            f"recuperada de R$ {margem}, mais perto do alvo.")           # o primeiro "R$ N" do memo é 250
    usar_roteiro(monkeypatch, [simula(250), simula(275), conclui(memo, recomendado=275)])
    assert agente.rodar_agente()["threshold_recomendado"] == 275


@pytest.mark.parametrize("declarado", [None, 300, 200, "abc", True])
def test_threshold_recomendado_ausente_ou_invalido_e_inferido_do_memo(monkeypatch, dados, declarado):
    # 300 e 200 não foram simulados, "abc" não é número e True é bool: nenhum vale, então vem do memo
    usar_roteiro(monkeypatch, [simula(275), conclui(memo_valido(dados), recomendado=declarado)])
    assert agente.rodar_agente()["threshold_recomendado"] == 275


def test_threshold_recomendado_no_fallback_e_o_equivalente_a_politica_observada(monkeypatch, dados):
    usar_roteiro(monkeypatch, [ConnectionError("Sandbox fora do ar")])
    r = agente.rodar_agente()
    assert r["fallback"] is True
    assert r["threshold_recomendado"] == simular_politica_observada(dados, RAMPA)["threshold_equivalente"]


def test_threshold_recomendado_unitario(dados):
    testados = cenarios_testados_para(dados, 200, 275)                     # 200 não tem evidência
    assert agente._threshold_recomendado(275, "qualquer", testados) == 275.0
    assert agente._threshold_recomendado(200, "Recomendamos R$ 275.", testados) == 275.0    # sem evidência: ignora
    assert agente._threshold_recomendado(None, "Talvez R$ 300 ou R$ 275.", testados) == 275.0   # 300 não foi testado
    assert agente._threshold_recomendado(None, "sem nenhum valor", testados) is None


# ================================================================================================
# Caminho percorrido: montado pelo código a partir da trilha
# ================================================================================================
def test_caminho_e_montado_a_partir_da_trilha(monkeypatch, dados):
    usar_roteiro(monkeypatch, [perfil("Vejo o alvo."), simula(250, "Extremo inferior."),
                               simula(275, "Perto do alvo."), conclui(memo_valido(dados))])
    r = agente.rodar_agente()

    assert [p["passo"] for p in r["caminho"]] == [1, 2, 3]
    assert [p.get("threshold") for p in r["caminho"]] == [None, 250, 275]
    obs = json.loads(r["trilha"][1]["observacao"])
    passo = r["caminho"][1]
    assert passo["margem_recuperada"] == obs["margem_recuperada"]              # o número vem do motor
    assert passo["desvio_pct_isentos"] == obs["desvio_vs_alvo"]["pct_pedidos_isentos"]
    assert r["caminho"][0]["alvo"]["pct_pedidos_isentos"]

    texto = r["caminho_texto"]
    assert "Passo 1 — leu o perfil" in texto and "Passo 2 — simulou R$ 250" in texto
    assert obs["margem_recuperada"] in texto and "Justificativa do agente: Perto do alvo." in texto
    assert "**Caminho percorrido:**" in log() and "Passo 3" in log()


def test_caminho_parcial_quando_a_execucao_falha_no_meio(monkeypatch, dados):
    usar_roteiro(monkeypatch, [perfil(), simula(250), ConnectionError("Sandbox fora do ar")])
    r = agente.rodar_agente()
    assert r["fallback"] is True and len(r["caminho"]) == 2 and "Passo 2" in r["caminho_texto"]


def test_caminho_vazio_quando_nada_foi_executado(monkeypatch, dados):
    usar_roteiro(monkeypatch, [ConnectionError("Sandbox fora do ar")])
    r = agente.rodar_agente()
    assert r["caminho"] == [] and "nenhuma ação" in r["caminho_texto"]


def test_caminho_mostra_pedido_recusado_e_threshold_sem_evidencia(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(5000), simula(200), conclui("x" * 50)])
    r = agente.rodar_agente()
    assert "erro" in r["caminho"][0] and r["caminho"][0]["threshold"] == 5000
    assert r["caminho"][1]["zona_com_evidencia"] is False
    assert "recusado pelo motor" in r["caminho_texto"] and "SEM evidência nos dados" in r["caminho_texto"]


def test_montar_caminho_aceita_observacao_que_nao_e_json():
    trilha = [{"passo": 6, "ferramenta": "simular_threshold", "args": {"threshold": 250}, "raciocinio": "",
               "observacao": "Limite de 5 ações de ferramenta atingido."}]
    passo = agente.montar_caminho(trilha)[0]
    assert passo["erro"].startswith("Limite de 5") and passo["threshold"] == 250


# ================================================================================================
# Memo: validação e chance de correção
# ================================================================================================
def test_memo_com_numero_inventado_cai_no_fallback(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(275), conclui(MEMO_INVENTADO), conclui(MEMO_INVENTADO)])
    r = agente.rodar_agente()
    assert r["fallback"] is True and "margem" in r["motivo_fallback"]
    esperado = simular_politica_observada(dados, RAMPA)["threshold_equivalente"]
    assert f"R$ {esperado}" in log() and f"R$ {esperado}" in r["memo"]     # fallback usa o threshold equivalente
    assert "FALLBACK" in log()


def test_memo_recusado_ganha_uma_chance_de_corrigir(monkeypatch, dados):
    llm = usar_roteiro(monkeypatch, [simula(275), conclui(MEMO_INVENTADO), conclui(memo_valido(dados))])
    r = agente.rodar_agente()
    assert r["fallback"] is False and r["passos"] == 3
    assert llm.chamadas[2][-1].content.startswith("MEMO RECUSADO")
    assert "memo recusado" in log()


def test_threshold_sem_evidencia_e_sinalizado_e_nao_e_aceito_no_memo(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(200), conclui(memo_valido(dados, 200)), conclui(memo_valido(dados, 200))])
    r = agente.rodar_agente()
    obs = json.loads(r["trilha"][0]["observacao"])
    assert obs["zona_com_evidencia"] is False and "sem precedente" in obs["aviso"]
    assert r["fallback"] is True and "evidência" in r["motivo_fallback"]


# ================================================================================================
# Proteções
# ================================================================================================
def test_limite_de_passos_e_de_chamadas_de_ferramenta(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(250) for _ in range(20)])
    r = agente.rodar_agente()
    assert r["fallback"] is True and "passos" in r["motivo_fallback"]
    assert r["passos"] == agente.MAX_PASSOS
    assert (linhas_de_uso()["origem"] == "agente").sum() == agente.MAX_PASSOS
    assert r["chamadas_tool"] == agente.MAX_CHAMADAS_TOOL
    assert "Limite" in r["trilha"][-1]["observacao"]        # as ações além do limite foram recusadas, sem executar


def test_orcamento_de_tempo_estourado_cai_no_fallback_sem_chamar_o_modelo(monkeypatch, dados):
    llm = usar_roteiro(monkeypatch, [perfil()])
    monkeypatch.setattr(agente, "TEMPO_MAX_SEGUNDOS", 0)          # qualquer tempo decorrido já estoura
    r = agente.rodar_agente()
    assert r["fallback"] is True and "tempo limite" in r["motivo_fallback"] and r["passos"] == 0
    assert llm.chamadas == []                                     # nem o agente nem o fallback chamaram a API
    assert "Texto-modelo" in r["memo"] and "texto-modelo" in log()


def test_erro_da_api_cai_no_fallback_e_registra_o_erro(monkeypatch, dados):
    usar_roteiro(monkeypatch, [ConnectionError("Sandbox fora do ar")])
    r = agente.rodar_agente()
    assert r["fallback"] is True and r["motivo_fallback"] == "ConnectionError durante a execução"
    assert linhas_de_uso().loc[0, "status"] == "erro:ConnectionError"
    assert "Sandbox fora do ar" not in log()                # mensagem completa não vai pro log
    assert r["memo"]                                        # o usuário sempre recebe um texto
    assert "Texto-modelo" in r["memo"]                      # e sem chamar a API de novo (ela acabou de falhar)


def test_sem_chave_cai_no_fallback(monkeypatch, dados):
    # sem usar_roteiro: criar_llm de verdade, sem chave (o conftest removeu)
    r = agente.rodar_agente()
    assert r["fallback"] is True and "RuntimeError" in r["motivo_fallback"]


def test_acao_de_simulacao_rejeita_threshold_invalido(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula(5000), simula(-10), simula("abc"), simula(True), conclui("x" * 50)])
    r = agente.rodar_agente()
    assert len(r["trilha"]) == 4 and all("erro" in json.loads(t["observacao"]) for t in r["trilha"])
    assert r["cenarios_testados"] == []                     # nada foi simulado


def test_threshold_numerico_em_texto_e_aceito(monkeypatch, dados):
    usar_roteiro(monkeypatch, [simula("275"), conclui(memo_valido(dados))])
    r = agente.rodar_agente()
    assert r["fallback"] is False and [c["threshold"] for c in r["cenarios_testados"]] == [275.0]


# ================================================================================================
# Respostas fora do protocolo
# ================================================================================================
def test_resposta_fora_do_protocolo_ganha_uma_correcao_de_rota(monkeypatch, dados):
    llm = usar_roteiro(monkeypatch, [diz("Vou buscar os arquivos de vendas."), simula(275), conclui(memo_valido(dados))])
    r = agente.rodar_agente()
    assert r["fallback"] is False and r["passos"] == 3
    assert llm.chamadas[1][-1].content.startswith("RESPOSTA FORA DO PROTOCOLO")
    assert list(linhas_de_uso()["status"]) == ["fora_do_protocolo", "ok", "ok"]


def test_duas_respostas_fora_do_protocolo_caem_no_fallback(monkeypatch, dados):
    usar_roteiro(monkeypatch, [diz("blá"), diz("blá blá")])
    r = agente.rodar_agente()
    assert r["fallback"] is True and "protocolo" in r["motivo_fallback"] and r["passos"] == 2


def test_ferramenta_da_plataforma_e_turno_invalido_e_nao_volta_no_historico(monkeypatch, dados):
    # a Sandbox real respondeu assim quando recebia `tools` (search_filesystem...): tool_calls sem conteúdo
    sequestro = AIMessage(content="", usage_metadata=USO,
                          tool_calls=[{"name": "search_filesystem", "args": {"pattern": "x"}, "id": "p1", "type": "tool_call"}])
    llm = usar_roteiro(monkeypatch, [sequestro, simula(275), conclui(memo_valido(dados))])
    r = agente.rodar_agente()
    assert r["fallback"] is False
    assert "search_filesystem" in llm.chamadas[1][-1].content             # o modelo é avisado do erro
    assert all(not getattr(m, "tool_calls", None) for m in llm.chamadas[1])   # e o tool_call não é reenviado
    assert linhas_de_uso().loc[0, "status"] == "fora_do_protocolo"


# ================================================================================================
# Leitura do protocolo (unitário)
# ================================================================================================
def test_extrair_acao_le_json_limpo_cerca_e_texto_solto():
    assert agente._extrair_acao('{"acao": "perfil_canais_proprios"}')[0] == {"acao": "perfil_canais_proprios"}
    assert agente._extrair_acao('```json\n{"acao": "concluir", "memo": "ok"}\n```')[0]["acao"] == "concluir"
    assert agente._extrair_acao('Claro! {"acao": "simular_threshold", "threshold": 300} feito.')[0]["threshold"] == 300


@pytest.mark.parametrize("texto, trecho", [
    ("", "não encontrei"),
    ("vou pensar", "não encontrei"),
    ('{"acao": "simular_threshold", "threshold": 275', "não encontrei"),      # chave sem fechar
    ('{"acao": "simular_threshold", "threshold": }', "JSON inválido"),
    ('{"acao": "buscar_na_web"}', "acao"),
    ('{"threshold": 275}', "acao"),
])
def test_extrair_acao_recusa_o_que_nao_e_protocolo(texto, trecho):
    acao, erro = agente._extrair_acao(texto)
    assert acao is None and trecho in erro


# ================================================================================================
# Validador do memo (unitário)
# ================================================================================================
def test_validar_memo_aceita_threshold_no_fim_da_frase(dados):
    memo = f"Recomendamos R$ 275. A margem recuperada é R$ {brl(simular(275, dados)['margem_recuperada'])}, dentro do alvo."
    assert agente._validar_memo(memo, cenarios_testados_para(dados, 275)) is None


def test_validar_memo_aceita_threshold_escrito_com_centavos(dados):
    # os modelos costumam escrever "R$ 275,00"
    memo = f"Recomendamos R$ 275,00. A margem recuperada é R$ {brl(simular(275, dados)['margem_recuperada'])}, dentro do alvo."
    assert agente._validar_memo(memo, cenarios_testados_para(dados, 275)) is None


def test_validar_memo_nao_confunde_valor_monetario_com_threshold(dados):
    # "R$ 1.600,00" não pode ser lido como o threshold R$ 1: o memo não cita nenhum threshold testado
    margem = brl(simular(275, dados)["margem_recuperada"])
    memo = f"A margem recuperada é R$ {margem} no cenário escolhido pela equipe de pricing."
    assert "threshold" in agente._validar_memo(memo, cenarios_testados_para(dados, 275))


def test_validar_memo_recusa_vazio_e_sem_simulacao(dados):
    assert "vazio" in agente._validar_memo("curto", {})
    assert "nenhum" in agente._validar_memo("x" * 60, {})


# ================================================================================================
# Teste de estabilidade: python agente.py --n 3 (funções puras)
# ================================================================================================
def resultado_falso(testados, recomendado=275, fallback=False):
    return {"cenarios_testados": [{"threshold": float(t)} for t in testados], "threshold_recomendado": recomendado,
            "fallback": fallback, "segundos": 12.3, "run_id": "execucao-sem-uso-registrado"}


def test_extremos_da_rampa():
    assert agente.extremos_da_rampa(RAMPA) == (250.0, 400.0)               # na sintética a isenção satura em 400
    sem_isencao = pd.DataFrame({"faixa_min": [0, 250], "pct_isentos": [0.0, 0.0]})
    assert agente.extremos_da_rampa(sem_isencao) == (None, None)


def test_extremos_da_rampa_real():
    caminho = os.path.join(DATA_DIR, "rampa_canais_proprios.csv")
    if not os.path.exists(caminho):
        pytest.skip("rode prep_dados.py antes: os CSVs ainda não existem")
    assert agente.extremos_da_rampa(pd.read_csv(caminho)) == (250.0, 450.0)


def test_resumir_execucao_marca_se_os_dois_extremos_foram_testados():
    r1 = agente.resumir_execucao(1, resultado_falso([250, 400, 300, 275]), RAMPA)
    assert r1["sequencia"] == "250 → 400 → 300 → 275" and r1["extremos"] is True and r1["recomendado"] == 275
    assert agente.resumir_execucao(2, resultado_falso([250, 275]), RAMPA)["extremos"] is False
    r3 = agente.resumir_execucao(3, resultado_falso([], recomendado=None, fallback=True), RAMPA)
    assert r3["sequencia"] == "-" and r3["extremos"] is False and r3["fallback"] is True


def test_resumir_execucao_nao_conta_o_fallback_como_recomendacao_do_agente():
    # no fallback o threshold (275) foi escolhido pelo código: na tabela isso não pode virar "recomendação"
    r = agente.resumir_execucao(4, resultado_falso([250], recomendado=275, fallback=True), RAMPA)
    assert r["recomendado"] is None and r["fallback"] is True


def test_tabela_e_resumo_do_lote():
    resumos = [agente.resumir_execucao(1, resultado_falso([250, 400, 275]), RAMPA),
               agente.resumir_execucao(2, resultado_falso([250, 400, 300], recomendado=300), RAMPA),
               agente.resumir_execucao(3, resultado_falso([], recomendado=275, fallback=True), RAMPA)]
    tabela = agente.formatar_tabela(resumos)
    assert "sequência testada" in tabela and "250 → 400 → 275" in tabela and len(tabela.splitlines()) == 4
    lote = agente.resumir_lote(resumos)
    assert "[275, 300]" in lote and "fallback em 1/3" in lote        # o fallback não entra nas recomendações


# ================================================================================================
# VERSÃO: o que muda entre v2.1 e v3 é só o prompt
# ================================================================================================
def test_versao_e_prompt_da_v2_1():
    assert agente.VERSAO_AGENTE == "agente-v2.1"
    p = agente.SYSTEM_AGENTE
    assert '"raciocinio"' in p and '"threshold_recomendado"' in p and "caminho percorrido" in p
    assert "extremos da rampa (250 e 450)" in p          # a v2.1 SUGERE os extremos no prompt

