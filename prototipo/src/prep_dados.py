"""Lê vendas.csv e gera os arquivos derivados que o motor de simulação usa.
Roda uma vez, offline: `python prep_dados.py` (de dentro de src/). Aqui só há filtro e contagem;
nenhuma regra de negócio mora neste arquivo.

Saídas, em data/:
  marketplace_pedidos.csv     pedidos do Marketplace (order_id, receita_bruta, receita_liquida, custo_frete)
  rampa_canais_proprios.csv   política de frete grátis OBSERVADA nos outros canais: para cada faixa de
                              valor do pedido, quantos pedidos e que fração deles tem frete zerado
  perfil_canais_proprios.csv  uma linha por canal próprio: % de pedidos que pagam frete e o peso do
                              frete na receita líquida
"""
import os

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CANAL_MARKETPLACE = "Marketplace"

# Limite inferior de cada faixa de valor do pedido, em R$ (a última faixa é aberta: 450 ou mais).
# O 250 é o menor valor com frete zerado nos canais próprios: ver MENOR_THRESHOLD_OBSERVADO em
# simulador.py, cuja igualdade com esta rampa é conferida por test_politica_observada.py.
FAIXAS_RAMPA = [0, 250, 300, 350, 400, 450]

COLUNAS_CANAIS_PROPRIOS = ["order_id", "canal", "custo_frete", "receita_bruta", "receita_liquida"]


def _canais_proprios_de(vendas: pd.DataFrame) -> pd.DataFrame:
    """Vendas de todos os canais EXCETO o Marketplace, sem linhas com dado faltando (em memória)."""
    vendas = vendas.dropna(subset=COLUNAS_CANAIS_PROPRIOS)
    return vendas[vendas["canal"] != CANAL_MARKETPLACE]


# ----------------------------------------------------------------------------------------------
# Versões em memória: recebem o DataFrame de vendas e devolvem o resultado, sem tocar em disco.
# É o que permite ao front (que já tem o vendas.csv carregado) montar os dados do simulador sem
# depender dos CSVs derivados. As funções de CSV mais abaixo são casca em cima destas.
# ----------------------------------------------------------------------------------------------
def pedidos_marketplace(vendas: pd.DataFrame) -> pd.DataFrame:
    """Pedidos do Marketplace, só com as colunas que o simulador precisa."""
    vendas = vendas.dropna(subset=["order_id", "canal", "custo_frete"])
    return vendas[vendas["canal"] == CANAL_MARKETPLACE][["order_id", "receita_bruta", "receita_liquida", "custo_frete"]]


def rampa_canais_proprios(vendas: pd.DataFrame) -> pd.DataFrame:
    """Política de frete dos canais próprios: por faixa de valor, a fração de pedidos com frete zerado.

    Um pedido de valor exatamente igual ao limite de uma faixa pertence à faixa de cima
    (250 entra em [250, 300)), o mesmo critério do simulador (receita_bruta >= threshold).
    Faixa sem nenhum pedido fica com pct_isentos = 0.0.
    """
    proprios = _canais_proprios_de(vendas)
    faixa = pd.cut(proprios["receita_bruta"], bins=FAIXAS_RAMPA + [float("inf")],
                   right=False, labels=FAIXAS_RAMPA)
    isento = (proprios["custo_frete"] == 0).groupby(faixa, observed=False)
    return pd.DataFrame({
        "faixa_min": FAIXAS_RAMPA,
        "pedidos_proprios": isento.size().to_numpy(),
        "pct_isentos": isento.mean().fillna(0.0).round(6).to_numpy(),
    })


def perfil_canais_proprios(vendas: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por canal próprio: % de pedidos que pagam frete e frete como % da receita líquida."""
    por_canal = _canais_proprios_de(vendas).groupby("canal")
    return pd.DataFrame({
        "pedidos": por_canal.size(),
        "pct_pedidos_com_frete": (por_canal["custo_frete"].apply(lambda s: (s > 0).mean()) * 100).round(1),
        "frete_pct_receita_liquida": (por_canal["custo_frete"].sum() / por_canal["receita_liquida"].sum() * 100).round(2),
    }).reset_index()


def preparar_tudo(vendas: pd.DataFrame) -> tuple:
    """(pedidos do Marketplace, rampa, perfil) em memória, no mesmo formato do que o agente lê dos CSVs.

    O índice dos pedidos é refeito (0, 1, 2...) porque é assim que o pd.read_csv os devolve: o resultado
    fica igual ao de agente._carregar_dados(), e é isso que test_prep_dados.py confere contra os CSVs.
    """
    return (pedidos_marketplace(vendas).reset_index(drop=True),
            rampa_canais_proprios(vendas),
            perfil_canais_proprios(vendas))


# ----------------------------------------------------------------------------------------------
# Versões com CSV (o que o __main__ usa): leem vendas.csv, chamam a função em memória e gravam.
# ----------------------------------------------------------------------------------------------
def preparar(caminho_vendas: str, caminho_saida: str) -> pd.DataFrame:
    """Pedidos do Marketplace, só com as colunas que o simulador precisa."""
    mkt = pedidos_marketplace(pd.read_csv(caminho_vendas))
    mkt.to_csv(caminho_saida, index=False)
    return mkt


def preparar_rampa(caminho_vendas: str, caminho_saida: str) -> pd.DataFrame:
    """Política de frete dos canais próprios (ver rampa_canais_proprios), gravada em CSV."""
    rampa = rampa_canais_proprios(pd.read_csv(caminho_vendas))
    rampa.to_csv(caminho_saida, index=False)
    return rampa


def preparar_perfil(caminho_vendas: str, caminho_saida: str) -> pd.DataFrame:
    """Uma linha por canal próprio (ver perfil_canais_proprios), gravada em CSV."""
    perfil = perfil_canais_proprios(pd.read_csv(caminho_vendas))
    perfil.to_csv(caminho_saida, index=False)
    return perfil


if __name__ == "__main__":
    dados = os.path.join(BASE_DIR, "..", "data")
    entrada = os.path.join(dados, "vendas.csv")
    mkt = preparar(entrada, os.path.join(dados, "marketplace_pedidos.csv"))
    rampa = preparar_rampa(entrada, os.path.join(dados, "rampa_canais_proprios.csv"))
    perfil = preparar_perfil(entrada, os.path.join(dados, "perfil_canais_proprios.csv"))
    print(f"{len(mkt)} pedidos do Marketplace | rampa com {len(rampa)} faixas | {len(perfil)} canais próprios")
    print(rampa.to_string(index=False))
