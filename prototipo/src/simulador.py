"""Motor de simulação — função pura, sem dependência de interface.
Recebe um threshold de frete grátis e devolve o impacto em margem."""
import pandas as pd

def simular(threshold: float, pedidos: pd.DataFrame) -> dict:
    total_pedidos = len(pedidos)
    frete_atual = pedidos["custo_frete"].sum()
    receita_total = pedidos["receita_liquida"].sum()

    isentos = pedidos[pedidos["receita_bruta"] >= threshold]
    margem_recuperada = isentos["custo_frete"].sum()
    frete_restante = frete_atual - margem_recuperada

    return {
        "threshold": threshold,
        "pct_pedidos_isentos": round(len(isentos) / total_pedidos * 100, 1),
        "margem_recuperada": round(margem_recuperada, 2),
        "frete_restante": round(frete_restante, 2),
        "frete_pct_receita_nova": round(frete_restante / receita_total * 100, 2),
    }

def curva_completa(thresholds: list, pedidos: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([simular(t, pedidos) for t in thresholds])
