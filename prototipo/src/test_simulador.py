"""Testes de regressão — valores esperados vêm da análise já validada
manualmente (threshold 250 -> ~R$159.556, threshold 450 -> ~R$120.031)."""
import pandas as pd
from simulador import simular

def carregar_pedidos():
    return pd.read_csv("../data/marketplace_pedidos.csv")

def test_threshold_250():
    assert abs(simular(250, carregar_pedidos())["margem_recuperada"] - 159556.45) < 1.0

def test_threshold_450():
    assert abs(simular(450, carregar_pedidos())["margem_recuperada"] - 120030.53) < 1.0

def test_threshold_zero_recupera_tudo():
    assert simular(0, carregar_pedidos())["pct_pedidos_isentos"] == 100.0

def test_threshold_alto_nao_recupera_nada():
    assert simular(999999, carregar_pedidos())["margem_recuperada"] == 0
