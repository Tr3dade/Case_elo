"""Relatório final do protótipo de frete grátis (Marketplace), montado pelo CÓDIGO.

Os três textos do projeto e o que cada um faz:
    relatorio.py        relatório rápido: 1 chamada à Sandbox, 1 parágrafo sobre 1 cenário
    agente.py           o agente decide o que testar e conclui com um memo
    relatorio_final.py  (este) junta tudo numa apresentação completa

Este módulo NÃO chama a API. Os fatos vêm do motor (simulador.py) e do resultado do agente; o único
texto de IA que entra é o memo que o próprio agente escreveu; o resto é texto fixo ou frase-modelo
preenchida com números. Por isso roda em milissegundos, não inventa número e é totalmente testável.

Uso (num front Streamlit, por exemplo):
    resultado = rodar_agente()
    relatorio = montar_relatorio_final(resultado, pedidos, rampa)
    st.markdown(relatorio["markdown"])                 # o relatório inteiro, ou
    for secao in relatorio["secoes"]: ...              # seção por seção (abas, expanders)
    st.dataframe(pd.DataFrame(relatorio["tabela"]))    # a tabela de evidência, em números
"""
import pandas as pd

# A formatação vem do agente, para os números do caminho percorrido e os do relatório nunca divergirem.
from agente import _desvio, _pct, formatar_caminho
from relatorio import brl
from simulador import MENOR_THRESHOLD_OBSERVADO, simular, simular_politica_observada

SEPARADOR_JUSTIFICATIVA = "\n   Justificativa do agente: "     # como formatar_caminho() separa a justificativa


# ----------------------------------------------------------------------------------------------
# Formatação
# ----------------------------------------------------------------------------------------------
def _num(valor):
    """275.0 -> 275 (inteiro quando for inteiro), 287.5 -> 287.5."""
    valor = float(valor)
    return int(valor) if valor.is_integer() else valor


def _reais(valor: float) -> str:
    return f"R$ {brl(valor)}"


def _inteiro_br(n: int) -> str:
    """6040 -> '6.040'."""
    return f"{n:,}".replace(",", ".")


def _seguro(texto: str) -> str:
    """Texto escrito pelo modelo, pronto para o markdown: '<' vira &lt; para que um trecho entre < e >
    não seja lido como tag HTML e sumir da tela (o mesmo problema que já tivemos no log de prompts)."""
    return (texto or "").replace("<", "&lt;")


# ----------------------------------------------------------------------------------------------
# Peças do relatório (cada uma é uma função pequena e testável)
# ----------------------------------------------------------------------------------------------
def _linha(cenario: dict, alvo: dict, recomendado: bool, origem: str) -> dict:
    """Uma linha NUMÉRICA da tabela de evidência a partir de um resultado de simular()."""
    pct = float(cenario["pct_pedidos_isentos"])
    frete = float(cenario["frete_pct_receita_nova"])
    return {
        "rotulo": f"R$ {_num(cenario['threshold'])}",
        "threshold": _num(cenario["threshold"]),
        "pct_pedidos_isentos": pct,
        "frete_pct_receita": frete,
        "margem_recuperada": float(cenario["margem_recuperada"]),
        "desvio_pct_isentos": round(pct - alvo["pct_pedidos_isentos"], 1),
        "desvio_frete_pct": round(frete - alvo["frete_pct_receita_nova"], 2),
        "zona_com_evidencia": bool(cenario["zona_com_evidencia"]),
        "recomendado": recomendado,
        "origem": origem,                     # "agente": o agente simulou; "motor": calculado agora pelo relatório
    }


def _linha_do_alvo(alvo: dict) -> dict:
    return {"rotulo": "Alvo (canais próprios)", "threshold": None,
            "pct_pedidos_isentos": float(alvo["pct_pedidos_isentos"]),
            "frete_pct_receita": float(alvo["frete_pct_receita_nova"]),
            "margem_recuperada": float(alvo["margem_recuperada"]),
            "desvio_pct_isentos": None, "desvio_frete_pct": None, "zona_com_evidencia": None,
            "recomendado": False, "origem": "alvo"}


def _tabela_markdown(linhas: list) -> str:
    texto = ["| Cenário | Pedidos isentos | Frete / receita | Margem recuperada | Desvio vs alvo (isentos) |",
             "|---|---|---|---|---|"]
    for l in linhas:
        if l["origem"] == "alvo":
            texto.append(f"| {l['rotulo']} | {_pct(l['pct_pedidos_isentos'], 1)} | {_pct(l['frete_pct_receita'], 2)} "
                         f"| {_reais(l['margem_recuperada'])} | — |")
            continue
        nome = f"**{l['rotulo']} (recomendado)**" if l["recomendado"] else l["rotulo"]
        if not l["zona_com_evidencia"]:
            nome += " (sem evidência)"
        texto.append(f"| {nome} | {_pct(l['pct_pedidos_isentos'], 1)} | {_pct(l['frete_pct_receita'], 2)} "
                     f"| {_reais(l['margem_recuperada'])} | {_desvio(l['desvio_pct_isentos'], 1)} |")
    return "\n".join(texto)


def _frase_alternativa(linha: dict, linha_rec: dict) -> str:
    """Uma frase-modelo sobre um cenário descartado; todos os números foram calculados pelo código."""
    desvio = linha["desvio_pct_isentos"]
    if desvio > 0:
        juizo = "É mais generoso que a política observada nos canais próprios."
    elif desvio < 0:
        juizo = "É mais restritivo que a política observada nos canais próprios."
    else:
        juizo = "Reproduz a política observada nos canais próprios."
    diferenca = linha["margem_recuperada"] - linha_rec["margem_recuperada"]
    if diferenca > 0:
        margem = f"recupera {_reais(diferenca)} a mais em margem que {linha_rec['rotulo']}"
    elif diferenca < 0:
        margem = f"recupera {_reais(-diferenca)} a menos em margem que {linha_rec['rotulo']}"
    else:
        margem = f"recupera a mesma margem que {linha_rec['rotulo']}"
    frase = (f"- **{linha['rotulo']}**: isenta {_pct(linha['pct_pedidos_isentos'], 1)} dos pedidos "
             f"({_desvio(desvio, 1)} do alvo) e deixa o frete em {_pct(linha['frete_pct_receita'], 2)} da receita; "
             f"{margem}. {juizo}")
    if not linha["zona_com_evidencia"]:
        frase += f" Sem evidência nos dados: nenhum canal próprio isenta frete abaixo de R$ {MENOR_THRESHOLD_OBSERVADO}."
    return frase


def _caminho_markdown(caminho: list) -> str:
    """O caminho percorrido, um passo por item, com a justificativa do agente embaixo (texto plano)."""
    if not caminho:
        return "(o agente não executou nenhuma ação)"
    itens = []
    for passo in caminho:
        principal, _, justificativa = formatar_caminho([passo]).partition(SEPARADOR_JUSTIFICATIVA)
        item = f"- {principal}"
        if justificativa:
            item += f"\n  - Justificativa do agente: {_seguro(justificativa)}"
        itens.append(item)
    return "\n".join(itens)


def _premissas() -> list:
    return [
        "A margem recuperada é um **potencial**: supõe que o Marketplace passe a se comportar como os canais próprios.",
        "A simulação é **estática**: não mede efeito na demanda, no ticket médio nem na conversão.",
        "Nos dados, pedidos isentos aparecem com frete zero, mas **não se observa quem absorve o custo da remessa**.",
        f"Thresholds abaixo de R$ {MENOR_THRESHOLD_OBSERVADO} não têm precedente nos canais próprios e não são recomendados.",
        "A base cobre cerca de um ano de vendas: os números não são projeções para outros períodos.",
    ]


# ----------------------------------------------------------------------------------------------
# O relatório
# ----------------------------------------------------------------------------------------------
def montar_relatorio_final(resultado: dict, pedidos: pd.DataFrame, rampa: pd.DataFrame, alvo: dict = None) -> dict:
    """Monta o relatório completo a partir do resultado de rodar_agente().

    resultado  o dict devolvido por agente.rodar_agente()
    pedidos    DataFrame de marketplace_pedidos.csv (o mesmo que o simulador usa)
    rampa      DataFrame de rampa_canais_proprios.csv
    alvo       opcional: o dict de simular_politica_observada(pedidos, rampa). Passe-o pronto para não
               recalcular (~100 ms) a cada chamada; é constante enquanto os dados não mudam.

    Devolve um dict:
        titulo, fallback, motivo_fallback, aviso (texto do aviso de fallback, ou None), threshold_recomendado
        secoes         lista de {id, titulo, markdown}: uma por seção, para montar abas ou blocos
        tabela         lista de linhas NUMÉRICAS (uma por cenário mais a linha do alvo): gráficos e st.dataframe
        verificacoes   lista de {ok, texto}: as 4 checagens automáticas
        markdown       o relatório inteiro num texto só
    Sempre devolve o relatório completo, inclusive quando o agente caiu em fallback (com um aviso no topo).
    """
    alvo = alvo or simular_politica_observada(pedidos, rampa)
    fallback = bool(resultado["fallback"])
    memo = resultado.get("memo") or ""

    recomendado = resultado.get("threshold_recomendado")
    if recomendado is None:                                   # defensivo: cai no threshold equivalente ao alvo
        recomendado = alvo["threshold_equivalente"]
    recomendado = _num(recomendado)

    # ---- os cenários: os que o agente simulou e, se faltar, o recomendado calculado agora pelo motor ----
    do_agente = {float(c["threshold"]): c for c in resultado["cenarios_testados"]}
    simulado_pelo_agente = float(recomendado) in do_agente
    cenario_rec = do_agente[float(recomendado)] if simulado_pelo_agente else simular(float(recomendado), pedidos)

    linhas = [_linha(c, alvo, float(c["threshold"]) == float(recomendado), "agente") for c in do_agente.values()]
    if not simulado_pelo_agente:
        linhas.append(_linha(cenario_rec, alvo, True, "motor"))
    linhas.sort(key=lambda l: float(l["threshold"]))
    linha_rec = next(l for l in linhas if l["recomendado"])
    linhas.append(_linha_do_alvo(alvo))

    # ---- o ponto de partida, direto dos pedidos ----
    n = len(pedidos)
    frete_total = float(pedidos["custo_frete"].sum())
    receita = float(pedidos["receita_liquida"].sum())
    pct_pagam = float((pedidos["custo_frete"] > 0).mean() * 100)
    frete_hoje_pct = frete_total / receita * 100

    # ---- as seções ----
    recomendacao = (
        f"**Adotar frete grátis, no Marketplace, para pedidos a partir de R$ {recomendado}.**\n\n"
        f"Com esse threshold, {_pct(linha_rec['pct_pedidos_isentos'], 1)} dos pedidos ficam isentos de frete e o frete "
        f"passa de {_pct(frete_hoje_pct, 2)} para {_pct(linha_rec['frete_pct_receita'], 2)} da receita líquida, "
        f"recuperando {_reais(linha_rec['margem_recuperada'])} em margem "
        f"(elimina {_pct(linha_rec['margem_recuperada'] / frete_total * 100, 1)} do custo de frete atual). "
        f"O alvo, a política já praticada nos canais próprios, é de {_pct(alvo['pct_pedidos_isentos'], 1)} de pedidos "
        f"isentos e frete em {_pct(alvo['frete_pct_receita_nova'], 2)} da receita.")

    ponto_de_partida = (
        f"Hoje {_pct(pct_pagam, 1)} dos {_inteiro_br(n)} pedidos do Marketplace pagam frete "
        f"(em média {_reais(frete_total / n)} por remessa). No período da base, isso soma {_reais(frete_total)} em frete, "
        f"ou {_pct(frete_hoje_pct, 2)} da receita líquida do canal ({_reais(receita)}).")

    evidencia = _tabela_markdown(linhas)

    nota_memo = ("_Este texto não veio do agente: é o texto do caminho determinístico (fallback)._" if fallback
                 else "_Texto escrito pelo agente (IA)._")
    analise = "\n".join("> " + linha for linha in (_seguro(memo).splitlines() or [""])) + "\n\n" + nota_memo

    outras = [l for l in linhas if l["origem"] != "alvo" and not l["recomendado"]]
    alternativas = ("\n".join(_frase_alternativa(l, linha_rec) for l in outras) if outras
                    else "Nenhum outro cenário foi testado.")

    premissas = "\n".join(f"- {p}" for p in _premissas())
    caminho = _caminho_markdown(resultado.get("caminho", []))

    # ---- as verificações automáticas ----
    memo_cita_margem = brl(linha_rec["margem_recuperada"]) in memo
    verificacoes = [
        {"ok": simulado_pelo_agente,
         "texto": (f"O threshold recomendado (R$ {recomendado}) foi simulado pelo agente." if simulado_pelo_agente else
                   f"O threshold recomendado (R$ {recomendado}) NÃO foi simulado pelo agente: o cenário foi calculado agora pelo motor.")},
        {"ok": linha_rec["zona_com_evidencia"],
         "texto": (f"O threshold recomendado tem evidência nos dados (a partir de R$ {MENOR_THRESHOLD_OBSERVADO}, o menor valor observado nos canais próprios)."
                   if linha_rec["zona_com_evidencia"] else
                   f"O threshold recomendado NÃO tem evidência nos dados (abaixo de R$ {MENOR_THRESHOLD_OBSERVADO}).")},
        {"ok": memo_cita_margem,
         "texto": (f"O memo cita a margem recuperada do threshold recomendado ({_reais(linha_rec['margem_recuperada'])})." if memo_cita_margem else
                   f"O memo NÃO cita a margem recuperada do threshold recomendado ({_reais(linha_rec['margem_recuperada'])}).")},
        {"ok": not fallback,
         "texto": ("O relatório veio do agente, sem fallback." if not fallback else
                   f"O relatório veio do caminho determinístico (fallback): {resultado.get('motivo_fallback')}.")},
    ]
    verificacoes_md = "\n".join(f"- {'✓' if v['ok'] else '✗'} {v['texto']}" for v in verificacoes)

    secoes = [
        {"id": "recomendacao", "titulo": "Recomendação", "markdown": recomendacao},
        {"id": "ponto_de_partida", "titulo": "Ponto de partida", "markdown": ponto_de_partida},
        {"id": "evidencia", "titulo": "Evidência", "markdown": evidencia},
        {"id": "analise_do_agente", "titulo": "Análise do agente", "markdown": analise},
        {"id": "alternativas", "titulo": "Alternativas descartadas", "markdown": alternativas},
        {"id": "premissas", "titulo": "Premissas e limites", "markdown": premissas},
        {"id": "caminho", "titulo": "Como chegamos aqui", "markdown": caminho},
        {"id": "verificacoes", "titulo": "Verificações", "markdown": verificacoes_md},
    ]

    titulo = f"Frete grátis no Marketplace: recomendação de R$ {recomendado}"
    aviso = (f"Este relatório veio do caminho determinístico (fallback): {resultado.get('motivo_fallback')}. "
             f"O threshold é o equivalente à política dos canais próprios e o texto da análise não foi escrito pelo agente.") if fallback else None

    partes = [f"# {titulo}"]
    if aviso:
        partes.append(f"> **Atenção:** {aviso}")
    partes += [f"## {s['titulo']}\n\n{s['markdown']}" for s in secoes]

    return {
        "titulo": titulo, "fallback": fallback, "motivo_fallback": resultado.get("motivo_fallback"),
        "aviso": aviso, "threshold_recomendado": recomendado,
        "secoes": secoes, "tabela": linhas, "verificacoes": verificacoes,
        "markdown": "\n\n".join(partes),
    }
