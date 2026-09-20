"""O Painel do Gestor inteiro no AppTest: card do ROAS, aviso, ressalvas e KPIs.

Mesmo esquema de test_ui_frete.py: pacotes reais (streamlit-echarts) e só o menu lateral trocado por uma função
(o option_menu é um componente de navegador, o AppTest não clica nele). Sem rede e sem chave: o Painel não
chama LLM nenhum, e o conftest.py ainda remove a chave da API por garantia.
"""
import os
import re
import sys

import pandas as pd
import pytest

PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
if PROTOTIPO_DIR not in sys.path:
    sys.path.insert(0, PROTOTIPO_DIR)

from ui import roas                                 # noqa: E402

DATA_DIR = os.path.join(PROTOTIPO_DIR, "data")

# O que o card mostrava ANTES desta mudança: valores, vendas por canal e ordem não podem mudar.
CARD_ANTES = [("Influenciador", "1,986", "7.48"), ("TikTok Ads", "2,583", "4.65"),
              ("Instagram Ads", "4,386", "4.54"), ("Google Ads", "4,825", "3.50"),
              ("Orgânico", "2,873", "3.19"), ("Email Marketing", "2,484", "3.15"),
              ("Marketplace", "5,300", "2.92")]
KPI_RECEITA_LIQUIDA, KPI_MARGEM = 14_170_454.54, 7_708_394.41
KPIS_ANTES = [("Receita líquida", "R$ 14,17 mi", "Bruta R$ 15,40 mi · retenção 92.0%"),
              ("Margem de contribuição", "54,4%", "R$ 7.71 mi margem no período"),
              ("Taxa de devolução", "14.92%", "3,645 pedidos · R$ 1,35 mi de margem perdida"),
              ("Ticket médio", "R$ 681.53", "Custo de atendimento R$ 179,4 mil")]


@pytest.fixture(scope="module")
def painel():
    """Painel do Gestor já rodado (uma vez por módulo: o app carrega ~28 mil linhas)."""
    import streamlit_option_menu
    from streamlit.testing.v1 import AppTest

    original = streamlit_option_menu.option_menu
    streamlit_option_menu.option_menu = lambda **kwargs: "Painel do Gestor"
    try:
        at = AppTest.from_file(os.path.join(PROTOTIPO_DIR, "app.py"), default_timeout=120)
        at.run()
    finally:
        streamlit_option_menu.option_menu = original
    return at


def texto_da_tela(at) -> str:
    return " ".join(m.value for m in at.markdown)


def test_painel_roda_sem_excecao(painel):
    assert [e.value for e in painel.exception] == []


def test_card_do_roas_tem_o_novo_rotulo_e_subtitulo(painel):
    tela = texto_da_tela(painel)
    assert "ROAS reportado pelo marketing" in tela
    assert "receita atribuída, não reconciliada · campanhas iniciadas em 2023" in tela
    assert "ROAS agregado por canal" not in tela


def test_card_do_roas_mantem_valores_vendas_e_ordem(painel):
    linhas = re.findall(r"<strong[^>]*>([^<]+)</strong>&nbsp;&nbsp;<span[^>]*>([\d.,]+) vendas</span></span>"
                        r"<span[^>]*>([\d.]+)x</span>", texto_da_tela(painel))
    assert linhas == CARD_ANTES


def test_kpis_do_painel_nao_mudaram(painel):
    kpis = re.findall(r'kpi-label">([^<]+)</div>\s*<div class="kpi-value[^"]*">([^<]+)</div>\s*'
                      r'<div class="kpi-foot">([^<]+)</div>', texto_da_tela(painel))
    assert kpis == KPIS_ANTES


def test_ui_roas_devolve_os_mesmos_valores_do_card(painel):
    """Cruzamento: o cálculo inline do app.py e o ui/roas.py não podem virar duas verdades."""
    linhas = re.findall(r"<strong[^>]*>([^<]+)</strong>&nbsp;&nbsp;<span[^>]*>[\d.,]+ vendas</span></span>"
                        r"<span[^>]*>([\d.]+)x</span>", texto_da_tela(painel))
    marketing = pd.read_csv(os.path.join(DATA_DIR, "marketing.csv"))
    reportado = roas.roas_reportado(marketing)
    assert [(canal, f"{valor:.2f}") for canal, valor in reportado.items()] == linhas


def test_aviso_de_reconciliacao_abaixo_do_card(painel):
    avisos = [w.value for w in painel.warning]
    assert len(avisos) == 1
    assert avisos[0] == ("A receita atribuída pelo marketing é ~17,7x a receita real de vendas no mesmo período. "
                         "Com a receita real, o ranking muda (Marketplace: 7º → 2º de 7). "
                         "Use como indicativo, não para alocar budget.")
    assert "0,3" not in avisos[0] and "0,2" not in avisos[0]     # só posições, nunca os valores 0,2 a 0,4


def test_ressalvas_expander_fechado_com_as_sete_frases(painel):
    assert len(painel.expander) == 1
    expander = painel.expander[0]
    assert expander.label == "Ressalvas sobre os dados"
    assert expander.proto.expanded is False                                    # começa FECHADO
    dentro = " ".join(m.value for m in expander.markdown)
    assert "não reconciliam entre si" in dentro
    for trecho in ["346 dos 15.000 clientes", "18.724 dos 28.589 pedidos", "67,0% dos pedidos", "24.437 pedidos",
                   "Marketplace 6.040 pedidos", "~17,7x", "Períodos diferentes",
                   "(a) Os KPIs do topo, o gráfico mensal, o donut e a tabela de categorias", "(b) O card de ROAS",
                   "(c) O Simulador de frete", "889 pedidos (4,3% dos pedidos)", "contam como receita"]:
        assert trecho in dentro, trecho
    assert "26.538" not in dentro                                              # o gráfico mensal saiu da lista de bases
    frases = [m for m in expander.markdown[-1].value.split("\n") if m.startswith("- ")]
    assert len(frases) == 7


def test_ressalvas_escapam_o_cifrao(painel):
    dentro = " ".join(m.value for m in painel.expander[0].markdown)
    assert "R\\$ 294,3 mi" in dentro and "R$ 294,3" not in dentro.replace("R\\$", "")


# ================================================================================================
# Gráfico mensal: opções do ECharts lidas do AppTest (o componente aparece como "bidi_component")
# ================================================================================================
def opcoes_do_grafico(at) -> dict:
    import json
    componentes = at.get("bidi_component")
    assert len(componentes) == 1                                               # só o gráfico mensal usa ECharts
    return json.loads(componentes[0].proto.json)["options"]


def test_grafico_mantem_series_e_desenho_e_alinha_os_zeros(painel):
    from test_ui_grafico_mensal import fracao_do_zero, series_mensais_reais
    receita, deducoes, margem = series_mensais_reais()
    opcoes = opcoes_do_grafico(painel)
    barras_receita, barras_deducoes, linha = opcoes["series"]
    # as séries saem da base dos KPIs (sem cancelados e sem devolvidos); deduções negativas, margem em linha
    # suavizada no eixo 2
    assert barras_receita["data"] == pytest.approx(receita)
    assert barras_deducoes["data"] == pytest.approx([-d for d in deducoes])
    assert linha["data"] == pytest.approx(margem)
    assert (barras_receita["type"], barras_deducoes["type"], linha["type"]) == ("bar", "bar", "line")
    assert linha["smooth"] is True and linha["yAxisIndex"] == 1
    assert barras_deducoes["name"] == "Descontos"                              # devolução não está nesta base
    assert sum(barras_receita["data"]) == pytest.approx(KPI_RECEITA_LIQUIDA, abs=0.01)   # bate com o card do topo
    assert sum(linha["data"]) == pytest.approx(KPI_MARGEM, abs=0.01)
    # o que mudou: os dois eixos com min/max/interval e o zero na mesma altura
    esq, dir_ = opcoes["yAxis"]
    assert {"min", "max", "interval"} <= set(esq) and {"min", "max", "interval"} <= set(dir_)
    assert fracao_do_zero(esq) == pytest.approx(fracao_do_zero(dir_))
    assert esq["min"] < 0 < esq["max"]                                         # deduções continuam abaixo do zero
    assert min(-d for d in deducoes) >= esq["min"] and max(receita) <= esq["max"]
    assert max(margem) <= dir_["max"]


def test_eixo_da_margem_nao_rotula_a_parte_negativa(painel):
    formatter = opcoes_do_grafico(painel)["yAxis"][1]["axisLabel"]["formatter"]
    assert "< 0) return ''" in formatter


# ================================================================================================
# Tabela e donut de categorias: mesma base dos KPIs, nada digitado
# ================================================================================================
TICKETS_ERRADOS = ("R$ 593", "R$ 576", "R$ 579", "R$ 558")        # o que estava digitado no HTML
CATEGORIAS = [("Moda", "R$ 5,04 mi", "54,5%", "R$ 692"), ("Beleza", "R$ 4,24 mi", "54,4%", "R$ 676"),
              ("Lifestyle", "R$ 2,88 mi", "54,1%", "R$ 687"), ("Acessórios", "R$ 2,01 mi", "54,5%", "R$ 660")]


def linhas_da_tabela_de_categorias(at) -> list:
    html = next(m.value for m in at.markdown if "Desempenho por categoria" in m.value)
    linhas = re.findall(r"<tr[^>]*>(.*?)</tr>", html, flags=re.S)[1:]              # a primeira é o cabeçalho
    return [tuple(re.findall(r"<td[^>]*>(.*?)</td>", linha)) for linha in linhas]


def test_tabela_de_categorias_e_calculada_e_o_ticket_esta_certo(painel):
    assert linhas_da_tabela_de_categorias(painel) == CATEGORIAS
    tela = texto_da_tela(painel)
    for errado in TICKETS_ERRADOS:
        assert errado not in tela, errado


def test_ticket_das_categorias_e_coerente_com_o_ticket_geral(painel):
    tickets = {c: int(t.replace("R$ ", "")) for c, _, _, t in linhas_da_tabela_de_categorias(painel)}
    assert min(tickets.values()) <= 681.53 <= max(tickets.values())            # o geral é média ponderada das categorias


def test_donut_e_tabela_usam_a_mesma_base(painel):
    from ui import painel_calculos
    vendas = pd.read_csv(os.path.join(DATA_DIR, "vendas.csv"), parse_dates=["data_pedido"])
    fatias = painel_calculos.por_categoria(vendas)["participacao_pct"]
    tela = texto_da_tela(painel)
    for categoria, pct in fatias.items():
        assert f"{categoria}</span><span style='font-weight: 700;'>{pct:.1f}%" in tela, categoria
    assert fatias.round(1).to_dict() == {"Moda": 35.6, "Beleza": 29.9, "Lifestyle": 20.3, "Acessórios": 14.2}
