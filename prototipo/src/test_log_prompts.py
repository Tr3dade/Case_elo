"""Testes do log de prompts: (1) o formato NOVO que agente.py e relatorio.py gravam (prompt em bloco de
código, threshold sem ".0") e (2) corrigir_log_prompts.py, que conserta o log ANTIGO. Sem rede e sem chave.
"""
import json

import pandas as pd
import pytest
from langchain_core.messages import AIMessage

import agente
import corrigir_log_prompts as corrigir
import relatorio
from relatorio import brl
from simulador import simular

USO = {"input_tokens": 10000, "output_tokens": 50, "total_tokens": 10050}
RAMPA = pd.DataFrame({"faixa_min": [0, 250, 300, 350, 400, 450], "pedidos_proprios": [10] * 6,
                      "pct_isentos": [0.0, 0.7, 0.85, 0.94, 1.0, 1.0]})


class LLMFalso:
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)

    def invoke(self, mensagens):
        return self.roteiro.pop(0)


def age(acao, **campos):
    return AIMessage(content=json.dumps({"acao": acao, **campos}), usage_metadata=USO)


@pytest.fixture
def dados(monkeypatch):
    valores = [100] * 20 + [260] * 30 + [320] * 30 + [500] * 20
    pedidos = pd.DataFrame({"order_id": range(100), "receita_bruta": valores,
                            "receita_liquida": [v * 0.9 for v in valores], "custo_frete": [32.0] * 100})
    perfil = pd.DataFrame({"canal": ["Canal A"], "pedidos": [10],
                           "pct_pedidos_com_frete": [20.0], "frete_pct_receita_liquida": [1.0]})
    monkeypatch.setattr(agente, "_carregar_dados", lambda: (pedidos, RAMPA, perfil))
    return pedidos


def rodar_agente_ok(monkeypatch, pedidos):
    memo = (f"Recomendamos R$ 275, com margem recuperada de R$ {brl(simular(275, pedidos)['margem_recuperada'])}, "
            "o mais próximo do alvo. O cenário de R$ 250 foi descartado por isentar mais que o alvo.")
    llm = LLMFalso([age("perfil_canais_proprios"), age("simular_threshold", threshold=250),
                    age("simular_threshold", threshold=275),
                    age("concluir", threshold_recomendado=275, memo=memo)])
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: llm)
    return agente.rodar_agente()


def log():
    return open(relatorio.LOG_PATH, encoding="utf-8").read()


# ================================================================================================
# 1. Formato NOVO do log
# ================================================================================================
def test_prompt_do_agente_vai_em_bloco_de_codigo_com_os_placeholders_intactos(monkeypatch, dados):
    rodar_agente_ok(monkeypatch, dados)
    conteudo = log()
    assert "**Prompt:**\n```text\n" in conteudo and "\n```\n\n**Missão:**" in conteudo
    dentro = conteudo.split("**Prompt:**\n```text\n")[1].split("\n```\n\n**Missão:**")[0]
    assert dentro == agente.SYSTEM_AGENTE                        # o prompt inteiro, sem perder nada
    assert "<o threshold escolhido>" in dentro                   # justamente o que o markdown esconderia fora do bloco


def test_o_prompt_do_agente_nao_contem_cerca_de_codigo_que_quebraria_o_bloco():
    assert "```" not in agente.SYSTEM_AGENTE


def test_threshold_recomendado_sai_no_log_sem_ponto_zero(monkeypatch, dados):
    rodar_agente_ok(monkeypatch, dados)
    assert "**Threshold recomendado:** R$ 275\n" in log() and "275.0" not in log()


def test_prompt_do_relatorio_vai_em_bloco_de_codigo(monkeypatch):
    texto = ("Recomenda-se o threshold de R$ 250, com 81,1% de pedidos isentos e frete de 0,93% da receita, "
             "recuperando R$ 159.556,45 em margem.")
    monkeypatch.setattr(relatorio, "criar_llm", lambda **kwargs: LLMFalso([AIMessage(content=texto, usage_metadata=USO)]))
    resultado = {"threshold": 250, "pct_pedidos_isentos": 81.1, "margem_recuperada": 159556.45,
                 "frete_restante": 37165.0, "frete_pct_receita_nova": 0.93}

    relatorio.gerar_relatorio(resultado)

    prompt = relatorio.montar_prompt(resultado)
    assert "```" not in prompt
    assert f"```text\n{prompt}```\n\n**Resposta:**" in log()     # cerca colada ao prompt, resposta logo depois


def test_o_que_o_corretor_faz_num_prompt_antigo_do_agente_e_exatamente_o_que_o_agente_novo_grava():
    antigo = f"\n---\n## Agente [agente-v3] (run r1, 2026-09-20 10:00:00)\n**Prompt:**\n{agente.SYSTEM_AGENTE}\n\n**Missão:** M\n"
    novo = f"\n---\n## Agente [agente-v3] (run r1, 2026-09-20 10:00:00)\n**Prompt:**\n```text\n{agente.SYSTEM_AGENTE}\n```\n\n**Missão:** M\n"
    assert corrigir.corrigir_texto(antigo)[0] == novo


# ================================================================================================
# 2. corrigir_log_prompts.py
# ================================================================================================
PROMPT_AGENTE = "Regra 1.\n\nCONTEXTO\nAções: {\"acao\": \"concluir\", \"threshold_recomendado\": <o threshold escolhido>, \"memo\": \"<texto>\"}\n\nREGRAS\n- fim."
PROMPT_RELATORIO = "Você é um analista.\n\nThreshold: R$ 250\nFrete restante como % da receita do canal: 0,93%\n"

LOG_ANTIGO = (
    # relatório, cabeçalho mais antigo (só a data)
    f"\n---\n**Prompt** (2026-09-20 01:41:11):\n{PROMPT_RELATORIO}\n\n**Resposta:**\nTexto do modelo.\n"
    # agente com sucesso
    f"\n---\n## Agente [agente-v2] (run a1, 2026-09-20 02:00:00)\n**Prompt:**\n{PROMPT_AGENTE}\n\n**Missão:** Recomende.\n"
    "\n**Passo 1**: `perfil_canais_proprios({})` → {\"menor_threshold_observado\": \"R$ 250\"}\n"
    "\n**Memo:**\nTexto.\n\n**Resultado:** ok (5 passos, 4 ações de ferramenta)\n"
    # relatório, cabeçalho com versão, e resposta em FALLBACK
    f"\n---\n**Prompt** (relatorio-v2, 2026-09-20 03:00:00):\n{PROMPT_RELATORIO}\n\n**Resposta (FALLBACK, ConnectionError):**\nTexto-modelo.\n"
    # agente em fallback
    f"\n---\n## Agente [agente-v3] (run a2, 2026-09-20 04:00:00)\n**Prompt:**\n{PROMPT_AGENTE}\n\n**Missão:** Recomende.\n"
    "\n**Resultado: FALLBACK** (tempo limite).\n"
)


def test_corrige_os_prompts_do_agente_e_do_relatorio():
    novo, n_agente, n_relatorio = corrigir.corrigir_texto(LOG_ANTIGO)
    assert (n_agente, n_relatorio) == (2, 2)
    assert novo.count("```text\n") == 4 and novo.count("\n```\n") == 4      # 4 aberturas e 4 fechamentos
    assert f"```text\n{PROMPT_AGENTE}\n```\n\n**Missão:**" in novo
    assert "<o threshold escolhido>" in novo.split("```text\n")[2]           # o placeholder ficou DENTRO de um bloco


def test_so_insere_e_a_verificacao_confirma_que_volta_identico():
    novo, _, _ = corrigir.corrigir_texto(LOG_ANTIGO)
    assert corrigir.verificar(LOG_ANTIGO, novo) is True
    assert len(novo) == len(LOG_ANTIGO) + 4 * len(corrigir.CERCA_ABRE + corrigir.CERCA_FECHA)   # 4 prompts, só inserção
    assert all(linha in novo.splitlines() for linha in LOG_ANTIGO.splitlines())                 # nenhuma linha original sumiu


def test_verificar_detecta_qualquer_alteracao_alem_das_cercas():
    novo, _, _ = corrigir.corrigir_texto(LOG_ANTIGO)
    assert corrigir.verificar(LOG_ANTIGO, novo.replace("Texto do modelo.", "Texto ALTERADO.")) is False
    assert corrigir.verificar(LOG_ANTIGO, novo + "linha a mais") is False


def test_entrada_incompleta_sem_o_que_vem_depois_do_prompt_e_preservada():
    truncado = f"\n---\n## Agente [agente-v3] (run a3, 2026-09-20 05:00:00)\n**Prompt:**\n{PROMPT_AGENTE}\n"
    assert corrigir.corrigir_texto(truncado)[0] == truncado


def test_main_grava_o_arquivo_corrigido_e_e_idempotente(tmp_path, capsys):
    arquivo = tmp_path / "prompts_log.md"
    arquivo.write_text(LOG_ANTIGO, encoding="utf-8")

    assert corrigir.main(str(arquivo)) == 0
    corrigido = arquivo.read_text(encoding="utf-8")
    assert corrigido != LOG_ANTIGO and "Corrigido: 2 prompt(s) do agente e 2 do relatório" in capsys.readouterr().out

    assert corrigir.main(str(arquivo)) == 0                                       # 2ª vez: não faz nada
    assert arquivo.read_text(encoding="utf-8") == corrigido
    assert "já está corrigido" in capsys.readouterr().out


def test_main_aborta_sem_gravar_se_a_verificacao_falhar(tmp_path, monkeypatch, capsys):
    arquivo = tmp_path / "prompts_log.md"
    arquivo.write_text(LOG_ANTIGO, encoding="utf-8")
    monkeypatch.setattr(corrigir, "verificar", lambda original, novo: False)

    assert corrigir.main(str(arquivo)) == 1
    assert arquivo.read_text(encoding="utf-8") == LOG_ANTIGO                     # nada foi gravado
    assert "ABORTADO" in capsys.readouterr().out


def test_main_com_arquivo_inexistente_devolve_2(tmp_path, capsys):
    assert corrigir.main(str(tmp_path / "nao_existe.md")) == 2
    assert "não encontrado" in capsys.readouterr().out


def test_main_sem_nenhum_prompt_no_formato_esperado_nao_altera_o_arquivo(tmp_path, capsys):
    arquivo = tmp_path / "prompts_log.md"
    arquivo.write_text("# Um log qualquer\n\nsem prompts registrados\n", encoding="utf-8")
    assert corrigir.main(str(arquivo)) == 0
    assert arquivo.read_text(encoding="utf-8") == "# Um log qualquer\n\nsem prompts registrados\n"
    assert "Nenhum prompt encontrado" in capsys.readouterr().out
