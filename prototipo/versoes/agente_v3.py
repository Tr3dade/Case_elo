"""Agente de threshold de frete (padrão ReAct) — canal Marketplace.

Diferença para o relatorio.py: lá o LLM só escreve texto em cima de um número já escolhido.
Aqui o LLM DECIDE o que testar: ele pede ações, observa o resultado do motor determinístico
(simulador.py) e repete até ter dados para concluir com um memo executivo. Os números vêm sempre
do código; o LLM só escolhe o que testar e redige a conclusão.

O loop (ReAct = Reason + Act), com o protocolo em TEXTO:
    1. o modelo recebe a missão e a lista de ações possíveis
    2. a cada turno ele responde com UM objeto JSON: a ação escolhida
    3. nós validamos o JSON, executamos a ação e devolvemos o resultado (a "observação") numa mensagem
    4. o modelo vê a observação e decide de novo; o loop termina com a ação "concluir"

Por que texto e não function calling (bind_tools):
    A documentação da Sandbox API lista, em POST /api/chat/completions, só model, messages, stream,
    temperature e max_tokens. tools e tool_choice não fazem parte do contrato (tool_choice devolve 400).
    Nos testes reais, TODA requisição com `tools` recebeu de volta ferramentas da própria plataforma
    (search_filesystem, view_skill, execute_code...) e nunca as nossas, enquanto as requisições sem
    `tools` (o relatorio.py) responderam normalmente. Este agente usa só o que a documentação promete.
    É também o ReAct original (Yao et al.), que é texto: Thought / Action / Observation.

Proteções: máximo de passos, de ações e de respostas fora do protocolo; orçamento de tempo (uma chamada
travada da Sandbox não pode deixar a execução esperando minutos); threshold validado
dentro da ação; o memo só é aceito se citar um threshold testado e a margem de um cenário testado (se
for recusado, o modelo tem UMA chance de corrigir). Se qualquer proteção falhar (ou a API cair), o
resultado vem do caminho determinístico: o threshold equivalente à política dos canais próprios,
narrado por relatorio.gerar_relatorio (que tem o seu próprio texto reserva).

Versão agente-v3 (esta). Herda da v2.1 tudo o que está listado abaixo; o que muda é SÓ o prompt:
    a v3 não dita os extremos da rampa. Manda o modelo LER a rampa na observação do perfil, identificar
    o limite inferior (onde a isenção passa de zero) e o superior (onde chega a 100%), testar esses dois
    e refinar. Nenhum dos números da resposta aparece no prompt (test_agente.py confere isso).

Herdado da v2.1, em relação à v2:
    - "raciocinio": cada ação de ferramenta traz uma frase com o porquê. Fica na trilha e no log.
      É a justificativa que o modelo DECLARA (não uma janela para o processamento interno dele).
    - "caminho percorrido": montado pelo CÓDIGO a partir da trilha (o que foi testado e o que voltou,
      fatos do motor) mais o raciocinio (a justificativa). O modelo não narra de memória.
    - "threshold_recomendado": campo estruturado na ação concluir, devolvido no resultado.
    - python agente.py --n 3: roda o agente várias vezes e imprime uma tabela de estabilidade.
    A v2.1 SUGERE no prompt começar pelos extremos da rampa (250 e 450); a v3 tira essa dica.

Uso:  from agente import rodar_agente ;  resultado = rodar_agente()
      ou, de dentro de src/:  python agente.py            (uma execução, com progresso)
                              python agente.py --n 3      (3 execuções e tabela de estabilidade)
"""
import argparse
import json
import logging
import os
import re
import time
from datetime import datetime

import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

import relatorio
import uso_api
from relatorio import brl, registrar_log, texto_da_mensagem
from simulador import MENOR_THRESHOLD_OBSERVADO, simular, simular_politica_observada

# Versão do prompt abaixo. Mudou o texto ou o protocolo? Incremente (vai em cada entrada do log).
VERSAO_AGENTE = "agente-v3"

MAX_PASSOS = 8            # chamadas ao modelo por execução (sobra folga para 1 correção de rota)
MAX_CHAMADAS_TOOL = 5     # ações de ferramenta por execução (perfil + até 4 simulações)
MAX_TURNOS_INVALIDOS = 2  # respostas fora do protocolo toleradas; na segunda, desiste e usa o fallback
MAX_REVISOES = 1          # chances de corrigir um memo recusado pela validação
THRESHOLD_MAX = 1500      # mesmo limite do slider do app
TEMPO_MAX_SEGUNDOS = 120  # orçamento da execução inteira; ao estourar, cai no fallback

MAX_RACIOCINIO = 300      # caracteres guardados do raciocinio de cada ação

ACOES = ("perfil_canais_proprios", "simular_threshold", "concluir")

# "R$ 275", "R$275" ou "R$ 275,00", mas não o começo de "R$ 153.886,45" (dígitos seguidos de . ou , e dígito)
_PADRAO_THRESHOLD = r"R\$\s?(\d{2,4})(?:,00)?(?!\d|[.,]\d)"

DATA_DIR = os.path.join(relatorio.PROTOTIPO_DIR, "data")

MISSAO_PADRAO = "Recomende o threshold de frete grátis para o canal Marketplace."

SYSTEM_AGENTE = f"""Você é um analista de precificação de frete da Vértice Retail. Sua tarefa é recomendar UM threshold de frete grátis para o canal Marketplace (pedidos com receita bruta maior ou igual ao threshold ficam isentos de frete).

CONTEXTO
- Hoje 100% dos pedidos do Marketplace pagam frete (cerca de R$ 32 por remessa) e isso pesa na margem. Nos canais próprios a isenção de frete já existe.
- A meta NÃO é maximizar a isenção. É fazer o Marketplace reproduzir o perfil dos canais próprios: a mesma proporção de pedidos isentos e o mesmo peso do frete na receita. Nenhum canal próprio isenta frete abaixo do menor valor observado (a observação do perfil informa qual é), então thresholds abaixo disso são extrapolação e não podem ser recomendados.

COMO VOCÊ TRABALHA
Você conversa com um programa, não com uma pessoa. A cada turno responda com UM único objeto JSON, sem texto antes ou depois e sem cercas de código. O programa executa a ação e devolve a observação na mensagem seguinte. As únicas ações que existem:
{{"acao": "perfil_canais_proprios", "raciocinio": "<uma frase: por que esta ação>"}}  -> mostra a política dos canais próprios e o ALVO que o Marketplace deve reproduzir (% de pedidos isentos, peso do frete na receita, margem recuperada). Use primeiro.
{{"acao": "simular_threshold", "threshold": <valor de 0 a 1500>, "raciocinio": "<uma frase: por que este valor>"}}  -> mede o efeito desse threshold no Marketplace, o desvio em relação ao alvo e se ele tem evidência nos dados (zona_com_evidencia).
{{"acao": "concluir", "threshold_recomendado": <o threshold escolhido>, "memo": "<texto>"}}  -> encerra com o memo executivo. O threshold_recomendado deve ser um dos que você simulou.
Você NÃO tem outras ferramentas: não busque arquivos, não use a web, não execute código, não consulte skills nem conhecimento externo. Tudo de que precisa vem das observações.

REGRAS
- Comece por perfil_canais_proprios e leia a rampa de isenção dos canais próprios: identifique (a) o LIMITE INFERIOR, o menor valor de pedido em que a isenção passa de zero, e (b) o LIMITE SUPERIOR, o valor de pedido a partir do qual a isenção chega a 100%. Simule esses dois limites primeiro e depois refine entre eles em torno do que mais se aproximar do alvo.
- Em toda ação de ferramenta preencha "raciocinio" com UMA frase objetiva dizendo por que você a escolheu, citando apenas números que você já viu nas observações. Nas duas primeiras simulações, diga onde na rampa você identificou o limite. Esse texto é registrado para auditoria.
- No máximo {MAX_CHAMADAS_TOOL} ações de ferramenta no total. Quando tiver dados suficientes, envie concluir.
- Escolha o threshold com o menor desvio em relação ao alvo. Só recomende threshold com zona_com_evidencia = true.
- Copie os números exatamente como as observações devolvem (já estão no formato brasileiro). Não invente, arredonde nem calcule números novos.
- O memo tem de 5 a 7 frases, num único parágrafo, sem aspas duplas dentro do texto: o threshold recomendado, os números dele comparados ao alvo, o caminho percorrido em 1 ou 2 frases (quais limites da rampa você identificou, quais thresholds testou, na ordem, e por que o escolhido venceu), ao menos um cenário testado e descartado com o motivo, e a premissa de que a recuperação de margem só se realiza se o Marketplace se comportar como os canais próprios. Cite a margem recuperada do threshold recomendado exatamente como veio da observação. Sem saudação, sem perguntas e sem oferecer material adicional."""

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------------------------
# Dados e formatação
# ----------------------------------------------------------------------------------------------
def _carregar_dados() -> tuple:
    """Lê os três arquivos gerados por prep_dados.py: (pedidos do Marketplace, rampa, perfil)."""
    return (pd.read_csv(os.path.join(DATA_DIR, "marketplace_pedidos.csv")),
            pd.read_csv(os.path.join(DATA_DIR, "rampa_canais_proprios.csv")),
            pd.read_csv(os.path.join(DATA_DIR, "perfil_canais_proprios.csv")))


def _pct(valor: float, casas: int) -> str:
    """78.1 -> '78,1%'."""
    return f"{valor:.{casas}f}".replace(".", ",") + "%"


def _desvio(valor: float, casas: int) -> str:
    """Diferença em pontos percentuais com sinal: 0.1 -> '+0,1 p.p.' (o +0.0 evita '-0,0')."""
    return f"{round(valor, casas) + 0.0:+.{casas}f}".replace(".", ",") + " p.p."


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


# ----------------------------------------------------------------------------------------------
# Ações (o que o modelo pode pedir)
# ----------------------------------------------------------------------------------------------
def _criar_ferramentas(pedidos, rampa, perfil, alvo, testados: dict) -> dict:
    """Cria as duas ações de ferramenta, presas (closure) aos dados desta execução.

    Devolve {nome: função(args) -> str}. Ficam dentro de uma função, e não no nível do módulo, para
    não haver estado global: cada rodar_agente() tem os seus dados e o seu registro de thresholds
    testados ('testados'). Toda observação sai como texto JSON já formatado em português.
    """

    def perfil_canais_proprios(args: dict) -> str:
        limites = list(rampa["faixa_min"])
        faixas = []
        for i, linha in rampa.iterrows():
            if i == 0:
                nome = f"abaixo de R$ {int(limites[1])}"
            elif i == len(limites) - 1:
                nome = f"a partir de R$ {int(limites[i])}"
            else:
                nome = f"R$ {int(limites[i])} a R$ {int(limites[i + 1])}"
            faixas.append({"faixa": nome, "pct_isentos": _pct(linha["pct_isentos"] * 100, 1)})
        return _json({
            "menor_threshold_observado": f"R$ {MENOR_THRESHOLD_OBSERVADO}",
            "canais_proprios": [
                {"canal": c["canal"], "pedidos": int(c["pedidos"]),
                 "pct_pedidos_com_frete": _pct(c["pct_pedidos_com_frete"], 1),
                 "frete_pct_receita": _pct(c["frete_pct_receita_liquida"], 2)}
                for _, c in perfil.iterrows()],
            "rampa_isencao_canais_proprios": faixas,
            "alvo_marketplace": {
                "descricao": "perfil do Marketplace se ele adotasse a política observada nos canais próprios",
                "pct_pedidos_isentos": _pct(alvo["pct_pedidos_isentos"], 1),
                "frete_pct_receita": _pct(alvo["frete_pct_receita_nova"], 2),
                "margem_recuperada": f"R$ {brl(alvo['margem_recuperada'])}",
            },
        })

    def simular_threshold(args: dict) -> str:
        bruto = args.get("threshold")
        try:
            if isinstance(bruto, bool):
                raise TypeError("bool não é número")
            threshold = float(bruto)
        except (TypeError, ValueError):
            return _json({"erro": f"threshold deve ser um número, recebido {bruto!r}"})
        if not 0 <= threshold <= THRESHOLD_MAX:
            return _json({"erro": f"threshold deve estar entre 0 e {THRESHOLD_MAX}, recebido {threshold}"})
        r = simular(threshold, pedidos)
        testados[threshold] = r
        return _json({
            "threshold": int(threshold) if threshold.is_integer() else threshold,
            "zona_com_evidencia": r["zona_com_evidencia"],
            "aviso": r["aviso"],
            "pct_pedidos_isentos": _pct(r["pct_pedidos_isentos"], 1),
            "margem_recuperada": f"R$ {brl(r['margem_recuperada'])}",
            "frete_restante": f"R$ {brl(r['frete_restante'])}",
            "frete_pct_receita": _pct(r["frete_pct_receita_nova"], 2),
            "desvio_vs_alvo": {
                "pct_pedidos_isentos": _desvio(r["pct_pedidos_isentos"] - alvo["pct_pedidos_isentos"], 1),
                "frete_pct_receita": _desvio(r["frete_pct_receita_nova"] - alvo["frete_pct_receita_nova"], 2),
            },
        })

    return {"perfil_canais_proprios": perfil_canais_proprios, "simular_threshold": simular_threshold}


def _executar_ferramenta(ferramentas: dict, nome: str, args: dict) -> str:
    """Executa uma ação pedida pelo modelo. Erro vira observação ({"erro": ...}) em vez de exceção:
    assim o modelo vê o que deu errado e pode corrigir o argumento."""
    try:
        return ferramentas[nome](args)
    except Exception as erro:
        return _json({"erro": f"{type(erro).__name__}: {str(erro)[:200]}"})


# ----------------------------------------------------------------------------------------------
# Protocolo: ler a ação do modelo
# ----------------------------------------------------------------------------------------------
def _extrair_acao(texto: str) -> tuple:
    """Lê a resposta do modelo e devolve (ação, None) ou (None, motivo do erro).

    Tolerante com o que os modelos costumam fazer: cerca de código (```json ... ```) e texto solto
    antes ou depois do objeto. Exigente no que importa: um JSON válido com uma "acao" conhecida.
    """
    limpo = re.sub(r"^```(?:json)?\s*|\s*```$", "", (texto or "").strip(), flags=re.IGNORECASE)
    inicio, fim = limpo.find("{"), limpo.rfind("}")
    if inicio == -1 or fim <= inicio:
        return None, "não encontrei um objeto JSON na resposta"
    try:
        acao = json.loads(limpo[inicio:fim + 1])
    except json.JSONDecodeError as erro:
        return None, f"JSON inválido ({erro.msg}, posição {erro.pos})"
    if not isinstance(acao, dict) or acao.get("acao") not in ACOES:
        return None, f"o campo 'acao' deve ser um de {list(ACOES)}"
    return acao, None


def _limpar_raciocinio(valor) -> str:
    """O raciocinio declarado pelo modelo, pronto para guardar: só texto, espaços normalizados e no
    máximo MAX_RACIOCINIO caracteres. Ausente ou de outro tipo vira '' (não invalida o turno)."""
    if not isinstance(valor, str):
        return ""
    texto = " ".join(valor.split())
    return texto if len(texto) <= MAX_RACIOCINIO else texto[:MAX_RACIOCINIO - 1].rstrip() + "…"


def _resumo(acao, da_plataforma: list) -> str:
    """Uma frase curta sobre o que o modelo fez neste turno (linha de progresso do terminal)."""
    if da_plataforma:
        return f"pediu ferramenta da plataforma ({', '.join(da_plataforma)})"
    if acao is None:
        return "resposta fora do protocolo"
    return f"ação {acao['acao']}" + (f" {acao['threshold']}" if "threshold" in acao else "")


# ----------------------------------------------------------------------------------------------
# Validação do memo
# ----------------------------------------------------------------------------------------------
def _validar_memo(memo: str, testados: dict):
    """Devolve None se o memo é aceitável, ou o motivo da reprovação.

    Três condições: (1) não é vazio, (2) houve simulação, e (3) o memo cita um threshold que foi
    de fato testado, dentro da zona com evidência, e a margem recuperada de um cenário testado
    (assim os números do memo têm origem numa observação).
    """
    if len(memo.strip()) < relatorio.TAMANHO_MINIMO_RESPOSTA:
        return "memo vazio ou curto demais"
    if not testados:
        return "nenhum threshold foi simulado"
    citados = {float(n) for n in re.findall(_PADRAO_THRESHOLD, memo)}
    if not any(t in testados and testados[t]["zona_com_evidencia"] for t in citados):
        return "memo não cita um threshold testado e com evidência"
    if not any(brl(r["margem_recuperada"]) in memo for r in testados.values()):
        return "memo não cita a margem recuperada de nenhum cenário testado"
    return None


def _threshold_recomendado(declarado, memo: str, testados: dict):
    """O threshold que o agente recomendou, ou None se não der para determinar.

    Vale, nesta ordem: (1) o campo threshold_recomendado da ação concluir, se for um threshold
    testado e com evidência; (2) o primeiro "R$ N" do memo que seja um threshold testado e com
    evidência (quem recomenda costuma citar o escolhido primeiro).
    """
    def valido(t: float) -> bool:
        return t in testados and testados[t]["zona_com_evidencia"]

    if declarado is not None and not isinstance(declarado, bool):
        try:
            if valido(float(declarado)):
                return float(declarado)
        except (TypeError, ValueError):
            pass
    for n in re.findall(_PADRAO_THRESHOLD, memo):
        if valido(float(n)):
            return float(n)
    return None


# ----------------------------------------------------------------------------------------------
# Caminho percorrido (montado pelo código, não narrado pelo modelo)
# ----------------------------------------------------------------------------------------------
def montar_caminho(trilha: list) -> list:
    """Transforma a trilha em passos estruturados, prontos para uma linha do tempo na tela.

    Função pura. Os números vêm das OBSERVAÇÕES (o que o motor devolveu: fatos) e a justificativa vem
    do raciocinio (o que o modelo declarou). Observação que não é um JSON válido (ex.: a mensagem de
    limite de ações) ou que traz "erro" vira um passo com o campo "erro".
    """
    caminho = []
    for t in trilha:
        passo = {"passo": t["passo"], "acao": t["ferramenta"], "raciocinio": t.get("raciocinio", "")}
        try:
            obs = json.loads(t["observacao"])
        except (TypeError, ValueError):
            obs = {"erro": str(t["observacao"])[:200]}
        if not isinstance(obs, dict):
            obs = {"erro": "observação inesperada"}
        if "erro" in obs:
            passo["erro"] = obs["erro"]
            if "threshold" in t["args"]:
                passo["threshold"] = t["args"]["threshold"]
        elif t["ferramenta"] == "simular_threshold":
            desvio = obs.get("desvio_vs_alvo", {})
            passo.update({
                "threshold": obs.get("threshold"), "zona_com_evidencia": obs.get("zona_com_evidencia"),
                "pct_pedidos_isentos": obs.get("pct_pedidos_isentos"), "frete_pct_receita": obs.get("frete_pct_receita"),
                "margem_recuperada": obs.get("margem_recuperada"),
                "desvio_pct_isentos": desvio.get("pct_pedidos_isentos"), "desvio_frete_pct": desvio.get("frete_pct_receita"),
            })
        else:
            passo["alvo"] = obs.get("alvo_marketplace")
        caminho.append(passo)
    return caminho


def formatar_caminho(caminho: list) -> str:
    """Texto legível do caminho: uma entrada por passo, com a justificativa do agente logo abaixo."""
    if not caminho:
        return "(nenhuma ação executada)"
    entradas = []
    for p in caminho:
        if "erro" in p:
            texto = f"Passo {p['passo']} — pedido recusado pelo motor: {p['erro']}"
        elif p["acao"] == "perfil_canais_proprios":
            alvo = p.get("alvo") or {}
            texto = (f"Passo {p['passo']} — leu o perfil dos canais próprios. Alvo do Marketplace: "
                     f"{alvo.get('pct_pedidos_isentos', '?')} de pedidos isentos, "
                     f"frete em {alvo.get('frete_pct_receita', '?')} da receita.")
        else:
            aviso = "" if p.get("zona_com_evidencia", True) else " (SEM evidência nos dados)"
            texto = (f"Passo {p['passo']} — simulou R$ {p['threshold']}{aviso}: {p['pct_pedidos_isentos']} de pedidos "
                     f"isentos ({p['desvio_pct_isentos']} do alvo), frete em {p['frete_pct_receita']} da receita "
                     f"({p['desvio_frete_pct']}), margem recuperada {p['margem_recuperada']}.")
        if p.get("raciocinio"):
            texto += f"\n   Justificativa do agente: {p['raciocinio']}"
        entradas.append(texto)
    return "\n".join(entradas)


# ----------------------------------------------------------------------------------------------
# O agente
# ----------------------------------------------------------------------------------------------
def rodar_agente(missao: str = MISSAO_PADRAO) -> dict:
    """Roda o agente e devolve um dict:
        memo               texto executivo final
        fallback           True se o memo veio do caminho determinístico
        motivo_fallback    por que caiu no fallback (None se não caiu)
        cenarios_testados  resultados de simular() na ordem em que o agente os testou
        trilha             cada ação de ferramenta: passo, nome, argumentos, raciocinio e observação
        threshold_recomendado  o threshold recomendado (no fallback, o equivalente à política observada)
        caminho            passos estruturados (ver montar_caminho) para uma linha do tempo na tela
        caminho_texto      o mesmo caminho em texto legível
        passos, chamadas_tool, segundos, run_id, versao_prompt
    """
    run_id = uso_api.novo_run_id()
    t0 = time.perf_counter()
    pedidos, rampa, perfil = _carregar_dados()
    alvo = simular_politica_observada(pedidos, rampa)

    testados: dict = {}   # threshold -> resultado de simular(), preenchido pela ação simular_threshold
    trilha: list = []
    passos = chamadas_tool = invalidos = revisoes = 0
    memo, motivo = None, None
    declarado = None           # threshold_recomendado informado pelo modelo na ação concluir
    api_indisponivel = False   # True se a falha foi de API/lentidão: aí não vale chamá-la de novo

    momento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    registrar_log(f"\n---\n## Agente [{VERSAO_AGENTE}] (run {run_id}, {momento})\n"
                  f"**Prompt:**\n{SYSTEM_AGENTE}\n\n**Missão:** {missao}\n")

    try:
        ferramentas = _criar_ferramentas(pedidos, rampa, perfil, alvo, testados)
        # Sem bind_tools de propósito: ver o docstring do módulo. Só model/messages/temperature/max_tokens.
        # Sem retentativa e com timeout curto: uma chamada travada não pode custar 2 x o timeout.
        llm = relatorio.criar_llm(temperature=0.1, max_tokens=800, request_timeout=40, max_retries=0)
        # Tudo na primeira mensagem do usuário (o relatorio.py, que funciona, também usa só uma mensagem).
        mensagens = [HumanMessage(content=f"{SYSTEM_AGENTE}\n\nMISSÃO: {missao}")]

        for passo in range(1, MAX_PASSOS + 1):
            if time.perf_counter() - t0 > TEMPO_MAX_SEGUNDOS:
                motivo = f"tempo limite de {TEMPO_MAX_SEGUNDOS} s"
                api_indisponivel = True
                break
            passos = passo
            logger.info("passo %d/%d: chamando o modelo...", passo, MAX_PASSOS)
            inicio = time.perf_counter()
            try:
                resposta = llm.invoke(mensagens)
            except Exception as erro:
                uso_api.registrar_chamada(run_id, "agente", passo, relatorio.MODELO, 0, 0,
                                          time.perf_counter() - inicio, f"erro:{type(erro).__name__}")
                raise

            texto = texto_da_mensagem(resposta)
            # Se a plataforma "sequestrar" a resposta com ferramentas dela, isso vira um turno inválido.
            da_plataforma = [c["name"] for c in (getattr(resposta, "tool_calls", None) or [])]
            if da_plataforma:
                acao, erro_protocolo = None, f"você pediu ferramentas que não existem ({', '.join(da_plataforma)})"
            else:
                acao, erro_protocolo = _extrair_acao(texto)

            entrada, saida = uso_api.extrair_uso(resposta)
            uso_api.registrar_chamada(run_id, "agente", passo, relatorio.MODELO, entrada, saida,
                                      time.perf_counter() - inicio, "ok" if acao else "fora_do_protocolo")
            logger.info("passo %d: %s (%.1fs, %d tokens de entrada)",
                        passo, _resumo(acao, da_plataforma), time.perf_counter() - inicio, entrada)
            # Reconstruímos a mensagem só com o texto: reenviar tool_calls exigiria responder cada um.
            mensagens.append(AIMessage(content=texto or "(sem conteúdo)"))

            # ---- resposta fora do protocolo: uma correção de rota, na segunda desiste ----
            if acao is None:
                invalidos += 1
                registrar_log(f"\n**Passo {passo}**: resposta fora do protocolo ({erro_protocolo})\n")
                if invalidos >= MAX_TURNOS_INVALIDOS:
                    motivo = f"o modelo não seguiu o protocolo JSON ({invalidos} respostas inválidas)"
                    break
                mensagens.append(HumanMessage(content=(
                    f"RESPOSTA FORA DO PROTOCOLO: {erro_protocolo}. Responda apenas com UM objeto JSON "
                    f"com uma das ações: {list(ACOES)}. Você não tem nenhuma outra ferramenta.")))
                continue

            # ---- ação concluir: valida o memo; se recusado, uma chance de corrigir ----
            if acao["acao"] == "concluir":
                memo = str(acao.get("memo") or "")
                declarado = acao.get("threshold_recomendado")
                recusa = _validar_memo(memo, testados)
                if recusa is None:
                    break
                if revisoes < MAX_REVISOES and passo < MAX_PASSOS:
                    revisoes += 1
                    registrar_log(f"\n**Passo {passo}**: memo recusado ({recusa}); pedindo correção\n")
                    mensagens.append(HumanMessage(content=(
                        f"MEMO RECUSADO: {recusa}. Corrija e envie a ação concluir de novo, citando um threshold "
                        "que você simulou (com zona_com_evidencia = true) e a margem recuperada exatamente "
                        "como a observação devolveu.")))
                    memo = None
                    continue
                motivo = recusa
                break

            # ---- ação de ferramenta ----
            nome = acao["acao"]
            raciocinio = _limpar_raciocinio(acao.get("raciocinio"))
            args = {k: v for k, v in acao.items() if k not in ("acao", "raciocinio")}
            if chamadas_tool >= MAX_CHAMADAS_TOOL:
                observacao = (f"Limite de {MAX_CHAMADAS_TOOL} ações de ferramenta atingido. "
                              "Não peça mais ferramentas: envie agora a ação concluir com os cenários já testados.")
            else:
                chamadas_tool += 1
                observacao = _executar_ferramenta(ferramentas, nome, args)
            trilha.append({"passo": passo, "ferramenta": nome, "args": args,
                           "raciocinio": raciocinio, "observacao": observacao})
            if raciocinio:
                logger.info("   ↳ %s", raciocinio)
            registrar_log(f"\n**Passo {passo}**: `{nome}({_json(args)})` → "
                          f"{observacao[:500]}{'…' if len(observacao) > 500 else ''}\n"
                          + (f"  ↳ raciocínio: {raciocinio}\n" if raciocinio else ""))
            mensagens.append(HumanMessage(content=f"OBSERVAÇÃO ({nome}): {observacao}"))

        if memo is None and motivo is None:
            motivo = f"limite de {MAX_PASSOS} passos sem conclusão"
    except Exception as erro:
        # A mensagem completa vai só pro terminal (pode conter trecho da chave); o log leva o tipo.
        logger.warning("Agente falhou (%s): %s", type(erro).__name__, erro)
        motivo = f"{type(erro).__name__} durante a execução"
        api_indisponivel = True

    caminho = montar_caminho(trilha)
    registrar_log(f"\n**Caminho percorrido:**\n{formatar_caminho(caminho)}\n")

    if motivo is None:
        recomendado = _threshold_recomendado(declarado, memo, testados)
        registrar_log(f"\n**Memo:**\n{memo}\n\n**Threshold recomendado:** R$ {recomendado}\n"
                      f"\n**Resultado:** ok ({passos} passos, {chamadas_tool} ações de ferramenta)\n")
    else:
        # Caminho determinístico: o threshold único mais próximo da política observada.
        threshold_fallback = alvo["threshold_equivalente"]
        cenario = simular(threshold_fallback, pedidos)
        # API falhou ou está lenta: chamá-la de novo só repetiria a espera, então vai o texto-modelo direto.
        # A API respondeu mas o agente não concluiu (protocolo, memo, limites): o relatório simples escreve o parágrafo.
        fonte = "texto-modelo (API indisponível ou lenta)" if api_indisponivel else "relatório simples"
        registrar_log(f"\n**Resultado: FALLBACK** ({motivo}). Usando o threshold equivalente à política "
                      f"observada, R$ {threshold_fallback}, pelo {fonte}.\n")
        memo = relatorio.texto_reserva(cenario) if api_indisponivel else relatorio.gerar_relatorio(cenario)
        recomendado = threshold_fallback

    if isinstance(recomendado, float) and recomendado.is_integer():
        recomendado = int(recomendado)

    return {
        "run_id": run_id, "versao_prompt": VERSAO_AGENTE,
        "memo": memo, "fallback": motivo is not None, "motivo_fallback": motivo,
        "cenarios_testados": list(testados.values()), "trilha": trilha,
        "threshold_recomendado": recomendado,
        "caminho": caminho, "caminho_texto": formatar_caminho(caminho),
        "passos": passos, "chamadas_tool": chamadas_tool,
        "segundos": round(time.perf_counter() - t0, 1),
    }


# ----------------------------------------------------------------------------------------------
# Teste de estabilidade (python agente.py --n 3)
# ----------------------------------------------------------------------------------------------
def extremos_da_rampa(rampa) -> tuple:
    """(limite inferior, limite superior) da política dos canais próprios, lidos da rampa:
    o primeiro valor de pedido com isenção acima de zero e o primeiro em que a isenção chega a ~100%.
    Nos dados reais: (250.0, 450.0). Devolve None no que não existir."""
    faixas, isentos = rampa["faixa_min"].to_numpy(), rampa["pct_isentos"].to_numpy()
    inferior = next((float(f) for f, p in zip(faixas, isentos) if p > 0), None)
    superior = next((float(f) for f, p in zip(faixas, isentos) if p >= 0.999), None)
    return inferior, superior


def resumir_execucao(n: int, resultado: dict, rampa) -> dict:
    """Uma linha da tabela de estabilidade: o que esta execução fez e quanto custou.

    Em execução com fallback, "recomendado" fica None: quem escolheu o threshold foi o código, não o
    agente, e contar isso como recomendação do agente faria um agente instável parecer estável."""
    testados = [c["threshold"] for c in resultado["cenarios_testados"]]
    inferior, superior = extremos_da_rampa(rampa)
    return {
        "n": n,
        "sequencia": " → ".join(f"{t:g}" for t in testados) or "-",
        "recomendado": None if resultado["fallback"] else resultado["threshold_recomendado"],
        "extremos": inferior in testados and superior in testados,   # os dois extremos foram simulados
        "fallback": resultado["fallback"],
        "segundos": resultado["segundos"],
        "custo_usd": uso_api.resumo_uso(resultado["run_id"]).get("custo_usd", 0.0),
    }


def formatar_tabela(resumos: list) -> str:
    linhas = [f"{'#':>2}  {'sequência testada':<30}  {'recomendado':>11}  {'extremos':>8}  {'fallback':>8}  {'seg':>5}  {'US$':>7}"]
    for r in resumos:
        rec = "-" if r["recomendado"] is None else f"{r['recomendado']:g}"
        linhas.append(f"{r['n']:>2}  {r['sequencia']:<30}  {rec:>11}  {'sim' if r['extremos'] else 'não':>8}  "
                      f"{'sim' if r['fallback'] else 'não':>8}  {r['segundos']:>5.1f}  {r['custo_usd']:>7.4f}")
    return "\n".join(linhas)


def resumir_lote(resumos: list) -> str:
    recomendados = sorted({r["recomendado"] for r in resumos if r["recomendado"] is not None})
    return (f"Recomendações distintas: {recomendados} | extremos testados em "
            f"{sum(r['extremos'] for r in resumos)}/{len(resumos)} execuções | "
            f"fallback em {sum(r['fallback'] for r in resumos)}/{len(resumos)} | "
            f"custo total US$ {sum(r['custo_usd'] for r in resumos):.4f}")


def imprimir_execucao(resultado: dict) -> None:
    print("\nCAMINHO PERCORRIDO\n" + resultado["caminho_texto"])
    print("\nMEMO\n" + resultado["memo"])
    print(f"\nthreshold recomendado: R$ {resultado['threshold_recomendado']}")
    print(f"fallback: {resultado['fallback']} ({resultado['motivo_fallback']}) | {resultado['segundos']} s no total")
    print("uso desta execução:", uso_api.resumo_uso(resultado["run_id"]))


if __name__ == "__main__":
    # Teste manual com a chave real. Não interrompa com Ctrl+C: cada execução termina sozinha em no
    # máximo ~3 minutos (orçamento de tempo + uma chamada em curso).
    analisador = argparse.ArgumentParser(description="Roda o agente contra a Sandbox real.")
    analisador.add_argument("--n", type=int, default=1, choices=range(1, 11), metavar="N",
                            help="execuções seguidas (1 a 10); com N > 1 imprime a tabela de estabilidade")
    argumentos = analisador.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(message)s")
    if argumentos.n == 1:
        logger.setLevel(logging.INFO)        # mostra as linhas de progresso "passo N: ..."
        imprimir_execucao(rodar_agente())
    else:
        rampa_real = _carregar_dados()[1]
        print(f"{argumentos.n} execuções seguidas (cerca de US$ 0,05 e 40 s cada).", flush=True)
        resumos = []
        for i in range(1, argumentos.n + 1):
            resumos.append(resumir_execucao(i, rodar_agente(), rampa_real))
            r = resumos[-1]
            rec = "-" if r["recomendado"] is None else f"{r['recomendado']:g}"
            print(f"execução {i}/{argumentos.n}: {r['sequencia']} -> recomendado {rec} "
                  f"({r['segundos']} s, US$ {r['custo_usd']:.4f})", flush=True)
        print("\n" + formatar_tabela(resumos) + "\n\n" + resumir_lote(resumos))
