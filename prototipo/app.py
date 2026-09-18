"""Interface Streamlit do simulador de threshold de frete — Marketplace.
Rodar com: streamlit run prototipo/app.py
"""
import os, sys
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from simulador import simular, curva_completa
from relatorio import gerar_relatorio

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@st.cache_data
def carregar_pedidos():
    return pd.read_csv(os.path.join(BASE_DIR, "data", "marketplace_pedidos.csv"))

st.set_page_config(page_title="Simulador de Frete — Marketplace", layout="centered")
st.title("Simulador de frete grátis — Marketplace")
st.caption("Vértice Retail — impacto de estender a política de frete grátis ao canal Marketplace")

pedidos = carregar_pedidos()

col1, col2 = st.columns(2)
if col1.button("Cenário Conservador (R$450)"):
    st.session_state["threshold"] = 450
if col2.button("Cenário Alinhado (R$250)"):
    st.session_state["threshold"] = 250

threshold = st.slider("Threshold de frete grátis (R$)", 0, 1500,
    value=st.session_state.get("threshold", 250), step=10)

resultado = simular(threshold, pedidos)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Margem recuperada", f"R$ {resultado['margem_recuperada']/1000:.1f} mil".replace(".", ","))
m2.metric("Pedidos isentos", f"{resultado['pct_pedidos_isentos']}%")
m3.metric("Frete restante", f"R$ {resultado['frete_restante']/1000:.1f} mil".replace(".", ","))
m4.metric("Frete % da receita", f"{resultado['frete_pct_receita_nova']}%")

st.subheader("Curva completa")
curva = curva_completa([0,100,150,200,250,300,350,400,450,500,600,700,800,1000,1500], pedidos)
st.line_chart(curva.set_index("threshold")["margem_recuperada"])

st.subheader("Relatório executivo")
if st.button("Gerar relatório"):
    with st.spinner("Gerando..."):
        st.markdown(gerar_relatorio(resultado))
