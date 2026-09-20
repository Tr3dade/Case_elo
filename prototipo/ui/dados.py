"""Dados do Simulador de frete, montados uma vez e guardados em cache do Streamlit."""
import streamlit as st


@st.cache_data(show_spinner=False)
def carregar_dados_frete(_vendas):
    """(pedidos do Marketplace, rampa, perfil, alvo) a partir do vendas.csv que o painel já carregou.

    Reaproveita o DataFrame do painel em vez dos CSVs derivados: a auditoria mostrou que o resultado é
    idêntico, e test_prep_dados.py continua conferindo isso contra os CSVs commitados. O alvo
    (simular_politica_observada, ~100 ms) fica no cache junto: é constante enquanto os dados não mudam.

    O "_" no nome do parâmetro manda o Streamlit não calcular o hash do DataFrame a cada rerun.
    Imports dentro da função: só quem chega aqui precisa do backend carregado.
    """
    from prep_dados import preparar_tudo
    from simulador import simular_politica_observada

    pedidos, rampa, perfil = preparar_tudo(_vendas)
    return pedidos, rampa, perfil, simular_politica_observada(pedidos, rampa)
