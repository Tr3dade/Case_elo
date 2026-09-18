"""Lê vendas.csv, filtra o canal Marketplace e salva só as colunas
que o motor de simulação precisa. Roda uma vez, offline."""
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def preparar(caminho_vendas: str, caminho_saida: str) -> pd.DataFrame:
    vendas = pd.read_csv(caminho_vendas).dropna(subset=["order_id", "canal", "custo_frete"])
    mkt = vendas[vendas["canal"] == "Marketplace"][["order_id", "receita_bruta", "receita_liquida", "custo_frete"]]
    mkt.to_csv(caminho_saida, index=False)
    return mkt

if __name__ == "__main__":
    entrada = os.path.join(BASE_DIR, "..", "data", "vendas.csv")
    saida = os.path.join(BASE_DIR, "..", "data", "marketplace_pedidos.csv")
    df = preparar(entrada, saida)
    print(f"{len(df)} pedidos do Marketplace salvos em {saida}")
