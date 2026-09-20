"""Registro de uso da API: tokens, custo e tempo de cada chamada ao LLM.

Existe separado do prompts_log.md de propósito: o log em markdown é a narrativa (prompt e resposta,
para a banca ler); este CSV é dado tabular, que dá para somar (custo total do projeto, custo por
análise). Uma linha por chamada à API. Uma "execução" (run_id) pode ter várias chamadas: o agente
faz uma por passo, então o custo de uma análise é a soma das linhas do mesmo run_id.

Nada aqui pode derrubar o fluxo principal: se o CSV não puder ser gravado, só avisa no terminal.
Rodar `python uso_api.py` imprime o resumo do CSV.
"""
import logging
import os
import uuid
from datetime import datetime

import pandas as pd

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
USO_PATH = os.path.join(PROTOTIPO_DIR, "prompts", "uso_api.csv")

# Tarifa da Sandbox: dedução a partir do painel "My consumption" (reproduz 8 de 8 linhas com custo
# exato, diferença máxima de US$ 0,0001). Ainda não confirmada pelo mentor: revisar se ele responder.
USD_POR_MILHAO_ENTRADA = 0.50
USD_POR_MILHAO_SAIDA = 3.00

# Cotação do dia para converter em reais. Preencher antes de usar o resumo em R$ (ex.: 5.40).
COTACAO_USD_BRL = None

COLUNAS = ["data_hora", "run_id", "origem", "passo", "modelo",
           "tokens_entrada", "tokens_saida", "custo_usd", "segundos", "status"]

logger = logging.getLogger(__name__)


def novo_run_id() -> str:
    """Identificador de uma execução: data/hora + 4 caracteres aleatórios (evita colisão no mesmo segundo)."""
    return datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:4]


def custo_usd(tokens_entrada: int, tokens_saida: int) -> float:
    """Custo em dólar de uma chamada, pela tarifa por milhão de tokens."""
    return (tokens_entrada * USD_POR_MILHAO_ENTRADA + tokens_saida * USD_POR_MILHAO_SAIDA) / 1_000_000


def extrair_uso(mensagem) -> tuple:
    """(tokens_entrada, tokens_saida) de uma resposta do LangChain. (0, 0) se a API não informou."""
    meta = getattr(mensagem, "usage_metadata", None) or {}
    return int(meta.get("input_tokens", 0) or 0), int(meta.get("output_tokens", 0) or 0)


def registrar_chamada(run_id: str, origem: str, passo: int, modelo: str,
                      tokens_entrada: int, tokens_saida: int, segundos: float,
                      status: str = "ok") -> None:
    """Acrescenta uma linha ao CSV (cria arquivo e cabeçalho na primeira vez).

    status: 'ok' quando a API respondeu, ou 'erro:<TipoDoErro>' quando a chamada falhou
    (nesse caso os tokens ficam 0, porque a API não devolveu contagem).
    """
    linha = pd.DataFrame([{
        "data_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "run_id": run_id, "origem": origem, "passo": passo, "modelo": modelo,
        "tokens_entrada": tokens_entrada, "tokens_saida": tokens_saida,
        "custo_usd": round(custo_usd(tokens_entrada, tokens_saida), 6),
        "segundos": round(segundos, 2), "status": status,
    }], columns=COLUNAS)
    try:
        os.makedirs(os.path.dirname(USO_PATH), exist_ok=True)
        novo_arquivo = not os.path.exists(USO_PATH)
        linha.to_csv(USO_PATH, mode="a", header=novo_arquivo, index=False, encoding="utf-8")
    except OSError as erro:
        logger.warning("Não consegui gravar %s: %s", USO_PATH, erro)


def resumo_uso(run_id: str = None) -> dict:
    """Soma o CSV. Com run_id, considera só aquela execução.

    Devolve chamadas, execuções, tokens, custo em USD (e em BRL se COTACAO_USD_BRL estiver
    preenchida), custo médio por execução e o mesmo detalhamento por origem (relatorio/agente).
    """
    if not os.path.exists(USO_PATH):
        return {"chamadas": 0}
    uso = pd.read_csv(USO_PATH)
    if run_id is not None:
        uso = uso[uso["run_id"] == run_id]
    if uso.empty:
        return {"chamadas": 0}

    def somar(df):
        total = float(df["custo_usd"].sum())
        return {
            "chamadas": int(len(df)),
            "execucoes": int(df["run_id"].nunique()),
            "tokens_entrada": int(df["tokens_entrada"].sum()),
            "tokens_saida": int(df["tokens_saida"].sum()),
            "custo_usd": round(total, 4),
            "custo_brl": round(total * COTACAO_USD_BRL, 4) if COTACAO_USD_BRL else None,
            "custo_medio_por_execucao_usd": round(total / df["run_id"].nunique(), 4),
        }

    resumo = somar(uso)
    resumo["por_origem"] = {origem: somar(g) for origem, g in uso.groupby("origem")}
    return resumo


if __name__ == "__main__":
    import json
    print(json.dumps(resumo_uso(), indent=2, ensure_ascii=False))
