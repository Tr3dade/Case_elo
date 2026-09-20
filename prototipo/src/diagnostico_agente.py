"""Diagnóstico do agente na Sandbox real. Script DESCARTÁVEL: não faz parte do protótipo.

O problema: nas execuções reais o agente chamou ferramentas da PRÓPRIA Sandbox (search_filesystem,
web_search, view_skill, execute_code...) e nunca as nossas (perfil_canais_proprios, simular_threshold).
Aqui testamos, com UMA chamada por variante (só o primeiro passo do agente), o que muda o
comportamento do modelo:

    A  configuração atual do agente                      -> baseline (deve reproduzir o problema)
    B  tool_choice forçado em perfil_canais_proprios     -> a Sandbox respeita a escolha forçada?
    C  instruções dentro da mensagem do usuário          -> o prompt de sistema está sendo ignorado?
    D  pergunta direta: "quais ferramentas você tem?"    -> as NOSSAS ferramentas chegam ao modelo?

Cada linha do resultado mostra o que o modelo pediu e marca [nossa] ou [da Sandbox].
Custo: 4 chamadas, cerca de US$ 0,03 no total. A chave nunca é impressa. Não grava em log nem em CSV.

Uso (de dentro de src/):  python diagnostico_agente.py
"""
import time

from langchain_core.messages import HumanMessage, SystemMessage

import agente
import relatorio
import uso_api
from simulador import simular_politica_observada


def montar_ferramentas():
    """As mesmas duas ferramentas do agente, com os dados reais."""
    pedidos, rampa, perfil = agente._carregar_dados()
    alvo = simular_politica_observada(pedidos, rampa)
    return agente._criar_ferramentas(pedidos, rampa, perfil, alvo, {})


def resumir(resposta, nossas: set) -> str:
    """O que o modelo respondeu: ferramentas pedidas (com marca) ou o início do texto."""
    pedidos = list(getattr(resposta, "tool_calls", None) or [])
    if pedidos:
        partes = [f"{p['name']}({p['args']}) [{'nossa' if p['name'] in nossas else 'da Sandbox'}]" for p in pedidos]
        return "pediu ferramenta: " + " | ".join(partes)
    texto = relatorio.texto_da_mensagem(resposta)
    return f"respondeu texto: {texto[:220]!r}" + ("..." if len(texto) > 220 else "")


def testar(nome: str, llm, mensagens: list, nossas: set) -> None:
    """Uma chamada ao modelo; imprime o resultado, o custo e o tempo."""
    inicio = time.perf_counter()
    try:
        resposta = llm.invoke(mensagens)
    except Exception as erro:
        print(f"[{nome}] FALHOU em {time.perf_counter() - inicio:.1f}s: {relatorio._causa_raiz(erro)}\n")
        return
    entrada, saida = uso_api.extrair_uso(resposta)
    custo = uso_api.custo_usd(entrada, saida)
    print(f"[{nome}] {time.perf_counter() - inicio:.1f}s, {entrada} in / {saida} out, US$ {custo:.4f}")
    print(f"    {resumir(resposta, nossas)}\n")


def main() -> None:
    ferramentas = montar_ferramentas()
    nossas = {f.name for f in ferramentas}
    base = relatorio.criar_llm(temperature=0.1, max_tokens=800, request_timeout=60)
    com_ferramentas = base.bind_tools(ferramentas)
    # tool_choice na forma de dicionário (a que o protocolo OpenAI exige e o bind_tools valida)
    forcado = base.bind_tools(ferramentas, tool_choice={"type": "function",
                                                        "function": {"name": "perfil_canais_proprios"}})

    normais = [SystemMessage(content=agente.SYSTEM_AGENTE), HumanMessage(content=agente.MISSAO_PADRAO)]
    tudo_no_usuario = [HumanMessage(content=agente.SYSTEM_AGENTE + "\n\nMISSÃO: " + agente.MISSAO_PADRAO)]
    pergunta = [HumanMessage(content="Sem chamar nenhuma ferramenta, responda apenas com os nomes de TODAS as "
                                     "ferramentas que você tem disponíveis nesta conversa, separados por vírgula.")]

    print("Nossas ferramentas:", sorted(nossas), "\n")
    testar("A atual                   ", com_ferramentas, normais, nossas)
    testar("B tool_choice forçado     ", forcado, normais, nossas)
    testar("C tudo na msg do usuário  ", com_ferramentas, tudo_no_usuario, nossas)
    testar("D lista de ferramentas    ", com_ferramentas, pergunta, nossas)


if __name__ == "__main__":
    main()