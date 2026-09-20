"""Motor de simulação: funções puras, sem dependência de interface nem de IA.
Recebe um threshold de frete grátis e devolve o impacto em margem no canal Marketplace.

Três coisas aqui dentro:
  simular / curva_completa     "se todo pedido com receita bruta >= threshold ficar isento de frete"
  zona com evidência           threshold abaixo do menor observado nos canais próprios é sinalizado
  simular_politica_observada   o que o Marketplace teria se copiasse a política que os canais próprios
                               já praticam (a rampa de isenção gerada por prep_dados.py)

Por que a zona com evidência existe: o simulador só soma benefício (quanto menor o threshold, mais
frete some da conta), então sozinho ele sempre "escolheria" threshold zero. O contrapeso não vem da
conta, vem dos dados: nenhum canal próprio isenta frete abaixo de R$ 250, então abaixo disso o
resultado é extrapolação, não previsão.
"""
import numpy as np
import pandas as pd

# Menor valor de pedido com frete zerado nos canais próprios. A igualdade com a rampa dos dados é
# conferida em test_politica_observada.py (se os dados mudarem, o teste avisa).
MENOR_THRESHOLD_OBSERVADO = 250

# Faixa de busca do threshold equivalente: do menor observado até o teto do slider do app, de 5 em 5.
THRESHOLD_MAX_BUSCA = 1500
PASSO_BUSCA = 5


def simular(threshold: float, pedidos: pd.DataFrame) -> dict:
    """Efeito de dar frete grátis a todo pedido com receita_bruta >= threshold.

    margem_recuperada é o frete que deixa de pesar na margem (soma do custo_frete dos pedidos
    isentos). Todos os valores saem como tipos nativos do Python (float/bool) para que o dict
    possa virar JSON sem conversão.
    """
    total_pedidos = len(pedidos)
    frete_atual = pedidos["custo_frete"].sum()
    receita_total = pedidos["receita_liquida"].sum()

    isentos = pedidos[pedidos["receita_bruta"] >= threshold]
    margem_recuperada = isentos["custo_frete"].sum()
    frete_restante = frete_atual - margem_recuperada

    com_evidencia = bool(threshold >= MENOR_THRESHOLD_OBSERVADO)
    aviso = None if com_evidencia else (
        f"R$ {threshold:.0f} está abaixo do menor threshold observado nos canais próprios "
        f"(R$ {MENOR_THRESHOLD_OBSERVADO}): sem precedente nos dados, o resultado é extrapolação.")

    return {
        "threshold": threshold,
        "pct_pedidos_isentos": float(round(len(isentos) / total_pedidos * 100, 1)),
        "margem_recuperada": float(round(margem_recuperada, 2)),
        "frete_restante": float(round(frete_restante, 2)),
        "frete_pct_receita_nova": float(round(frete_restante / receita_total * 100, 2)),
        "zona_com_evidencia": com_evidencia,
        "aviso": aviso,
    }


def curva_completa(thresholds: list, pedidos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha de simular() por threshold (inclui as colunas zona_com_evidencia e aviso)."""
    return pd.DataFrame([simular(t, pedidos) for t in thresholds])


def simular_politica_observada(pedidos: pd.DataFrame, rampa: pd.DataFrame) -> dict:
    """O Marketplace com a política de frete dos canais próprios.

    A rampa diz, para cada faixa de valor do pedido, que fração dos pedidos dos canais próprios tem
    frete zerado. Aqui essa fração é aplicada a cada pedido do Marketplace, pela faixa do seu valor:
    o pedido "recupera" pct_isentos do seu frete (valor esperado, não um sorteio).

    Devolve o mesmo formato de simular() (sem threshold) mais threshold_equivalente: o threshold
    único, múltiplo de 5 e dentro da zona com evidência, cuja margem recuperada mais se aproxima
    deste cenário. É o "corte seco" que melhor imita a rampa.
    """
    limites = rampa["faixa_min"].to_numpy()
    # searchsorted(..., side="right") - 1 = índice da última faixa com faixa_min <= valor.
    # Valor exatamente em 250 cai na faixa que começa em 250, igual ao critério do simulador.
    posicao = np.clip(np.searchsorted(limites, pedidos["receita_bruta"].to_numpy(), side="right") - 1,
                      0, len(limites) - 1)
    prob_isento = rampa["pct_isentos"].to_numpy()[posicao]

    frete = pedidos["custo_frete"].to_numpy()
    margem_recuperada = float((prob_isento * frete).sum())
    frete_restante = float(frete.sum()) - margem_recuperada
    receita_total = float(pedidos["receita_liquida"].sum())

    return {
        "margem_recuperada": round(margem_recuperada, 2),
        "pct_pedidos_isentos": round(float(prob_isento.sum()) / len(pedidos) * 100, 1),
        "frete_restante": round(frete_restante, 2),
        "frete_pct_receita_nova": round(frete_restante / receita_total * 100, 2),
        "threshold_equivalente": _threshold_equivalente(pedidos, margem_recuperada),
    }


def _threshold_equivalente(pedidos: pd.DataFrame, margem_alvo: float) -> int:
    """Threshold (múltiplo de 5, a partir do menor observado) cuja margem mais se aproxima do alvo.
    Em caso de empate vale o menor threshold (min devolve o primeiro mínimo encontrado)."""
    candidatos = range(MENOR_THRESHOLD_OBSERVADO, THRESHOLD_MAX_BUSCA + 1, PASSO_BUSCA)
    return min(candidatos, key=lambda t: abs(simular(t, pedidos)["margem_recuperada"] - margem_alvo))
