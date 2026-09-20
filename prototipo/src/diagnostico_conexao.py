"""Diagnóstico v2 da conexão com a Sandbox. Script DESCARTÁVEL: não faz parte do
protótipo, serve só pra descobrir por que o relatorio.py falha.

O que já sabemos: com um prompt minúsculo ("Responda apenas: ok") as 4 formas de
chamar a Sandbox funcionaram. O relatorio.py, com o prompt real, dá "Connection
error". Então aqui usamos o PROMPT REAL e comparamos, uma variação por vez:

    1  requests direto          -> HTTP puro, sem LiteLLM
    2  chamar_llm() de verdade  -> a função do relatorio.py, do jeito que está
    3  LiteLLM config notebook  -> chave/base por variável de ambiente, sem extras
    4  igual à 3 + max_tokens=300

Pra cada uma imprime o tempo e, se falhar, a CAUSA RAIZ (o "Connection error" do
LiteLLM esconde o erro real de rede embaixo dele). A chave nunca é impressa.
Cada chamada custa centavos: a Sandbox parece somar ~10k tokens de entrada em todas.
"""
import os
import sys
import time

import requests

import relatorio  # reaproveita montar_prompt, chamar_llm e as constantes (fonte única)

RESULTADO_250 = {
    "threshold": 250, "pct_pedidos_isentos": 81.1, "margem_recuperada": 159556.45,
    "frete_restante": 37165.0, "frete_pct_receita_nova": 0.93,
}
PROMPT = relatorio.montar_prompt(RESULTADO_250)
KEY = os.getenv("API_KEY") or os.getenv("API-KEY")
BASE = relatorio.API_BASE

print("python", sys.version.split()[0], "| chave lida:", bool(KEY), "| prompt:", len(PROMPT), "caracteres\n")
if not KEY:
    sys.exit("Chave não encontrada. Confira prototipo/.env (API_KEY ou API-KEY).")


def cadeia(erro, limite=6):
    """Percorre __cause__/__context__ e devolve 'Tipo: msg <- Tipo: msg ...'.
    A última entrada costuma ser o erro de rede de verdade."""
    partes, atual, vistos = [], erro, set()
    while atual is not None and id(atual) not in vistos and len(partes) < limite:
        vistos.add(id(atual))
        partes.append(f"{type(atual).__name__}: {str(atual)[:90]}")
        atual = atual.__cause__ or atual.__context__
    return "\n         <- ".join(partes)


def via_requests():
    corpo = {"model": "gemini-3-flash-preview", "max_tokens": 300, "temperature": 0.2,
             "messages": [{"role": "user", "content": PROMPT}]}
    r = requests.post(f"{BASE}/chat/completions", json=corpo,
                      headers={"Authorization": f"Bearer {KEY}"}, timeout=60)
    dados = r.json()
    texto = dados["choices"][0]["message"]["content"] or ""
    return f"HTTP {r.status_code}, {len(texto)} caracteres, usage={dados.get('usage')}"


def via_chamar_llm():
    texto = relatorio.chamar_llm(PROMPT)
    return f"{len(texto)} caracteres: {texto[:70]!r}"


def via_notebook(**extras):
    """Config do notebook (env vars). 'extras' acrescenta parâmetros ao ChatLiteLLM."""
    os.environ["OPENAI_API_KEY"] = KEY
    os.environ["OPENAI_API_BASE"] = BASE
    from langchain_litellm import ChatLiteLLM

    llm = ChatLiteLLM(model=relatorio.MODELO, temperature=0.1, api_base=BASE, **extras)
    texto = llm.invoke(PROMPT).content
    return f"{len(texto)} caracteres: {texto[:70]!r}"


def tentar(nome, funcao):
    inicio = time.perf_counter()
    try:
        resultado = funcao()
        print(f"[{nome}] OK em {time.perf_counter() - inicio:.1f}s\n    {resultado}\n")
    except Exception as erro:
        print(f"[{nome}] FALHOU em {time.perf_counter() - inicio:.1f}s\n    causa: {cadeia(erro)}\n")


tentar("1 requests direto, prompt real", via_requests)
tentar("2 chamar_llm() do relatorio.py ", via_chamar_llm)
tentar("3 litellm config do notebook   ", via_notebook)
tentar("4 notebook + max_tokens=300    ", lambda: via_notebook(max_tokens=300))