"""Gerador de relatório executivo via LLM (o caminho simples: uma chamada, sem ferramentas).

O LLM recebe o resultado JÁ calculado por simulador.py e só escreve o texto executivo em cima.
Ele não decide nada. (O agente.py é o caminho em que o LLM decide o que testar.) Este módulo
também guarda o que os dois caminhos compartilham: a conexão com a Sandbox e o log de prompts.

Funções, uma responsabilidade cada:
    montar_prompt    resultado do simulador -> texto do prompt. Pura, sem rede.
    criar_llm        ÚNICO lugar que configura a conexão com a Sandbox (usado por aqui e pelo agente).
    chamar_llm       uma chamada ao modelo + registro de tokens/custo. Levanta exceção se falhar.
    gerar_relatorio  ponto de entrada: monta, loga, chama, trata falha. Sempre devolve um texto.
"""
import logging
import os
import time
from datetime import datetime

from dotenv import load_dotenv

import uso_api

# Caminhos ancorados no próprio arquivo: funcionam de qualquer pasta de execução.
PROTOTIPO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LOG_PATH = os.path.join(PROTOTIPO_DIR, "prompts", "prompts_log.md")

# Lê prototipo/.env e joga as variáveis em os.environ. Se o arquivo não existir não dá erro,
# só não carrega nada (por isso criar_llm confere se a chave veio).
load_dotenv(os.path.join(PROTOTIPO_DIR, ".env"))

API_BASE = "https://chat.eloagents.click/api"
# O prefixo "openai/" manda o LiteLLM falar o protocolo compatível com OpenAI no endereço API_BASE.
# O resto ("gemini-3-flash-preview") é o modelo que a Sandbox expõe por trás desse protocolo.
MODELO = "openai/gemini-3-flash-preview"

# Versão do prompt de montar_prompt. Mudou o texto? Incremente e registre em prompts/versoes_prompts.md.
VERSAO_RELATORIO = "relatorio-v2"

# Resposta com menos caracteres que isto é tratada como falha (o notebook da Aula 7 documenta
# respostas vazias da Sandbox em chamadas soltas, e "vazio" chega sem levantar exceção).
TAMANHO_MINIMO_RESPOSTA = 60

logger = logging.getLogger(__name__)


class RespostaInvalida(Exception):
    """O modelo respondeu, mas a resposta é vazia ou curta demais para ser usada."""


# ----------------------------------------------------------------------------------------------
# Formatação
# ----------------------------------------------------------------------------------------------
def brl(valor: float) -> str:
    """Formata no padrão brasileiro: 159556.45 -> '159.556,45'.

    O formato do Python (:,.2f) sai como '159,556.45' (americano), o que confunde o modelo e o
    leitor de um relatório em português. A troca passa por um caractere temporário para a vírgula
    e o ponto não se sobreporem.
    """
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _decimal_br(valor: float) -> str:
    """0.93 -> '0,93'. Só troca o separador decimal (usado nos percentuais)."""
    return str(valor).replace(".", ",")


def montar_prompt(resultado: dict) -> str:
    """Recebe o dict de simulador.simular() e devolve o texto enviado ao LLM.

    Função pura: mesma entrada, mesma saída, sem rede e sem chave. Por isso dá para testá-la sozinha.
    """
    return (
        "Você é um analista financeiro. Escreva um parágrafo curto (3-4 frases) "
        "recomendando a decisão abaixo para a diretoria da Vértice Retail, "
        "em português, tom executivo, sem inventar números além dos fornecidos. "
        "Responda apenas com o parágrafo: sem saudação, sem perguntas e sem oferecer "
        "material adicional.\n\n"
        f"Threshold de frete grátis simulado: R$ {resultado['threshold']:.0f}\n"
        f"Margem recuperada projetada: R$ {brl(resultado['margem_recuperada'])}\n"
        f"Pedidos que passam a ter frete grátis: {_decimal_br(resultado['pct_pedidos_isentos'])}%\n"
        f"Frete restante como % da receita do canal: {_decimal_br(resultado['frete_pct_receita_nova'])}%\n"
    )


# ----------------------------------------------------------------------------------------------
# Conexão com a Sandbox
# ----------------------------------------------------------------------------------------------
def criar_llm(**extras):
    """Cria o cliente do modelo. É o único lugar que sabe URL, modelo e chave.

    'extras' sobrescreve os padrões (ex.: criar_llm(temperature=0.1, max_tokens=800)).
    Levanta ValueError se API_BASE não for uma URL e RuntimeError se a chave não existir: os dois
    erros que, escondidos atrás do "Connection error" do LiteLLM, já nos custaram horas de diagnóstico.
    """
    if not API_BASE.startswith(("http://", "https://")):
        raise ValueError(f"API_BASE inválida: {API_BASE!r} (precisa começar com https://)")
    chave = os.environ.get("API_KEY") or os.environ.get("API-KEY")
    if not chave:
        raise RuntimeError("API_KEY (ou API-KEY) não encontrada. Confira o arquivo prototipo/.env")

    # Import aqui dentro: quem só usa montar_prompt (ex.: testes) não precisa da biblioteca instalada.
    from langchain_litellm import ChatLiteLLM

    parametros = {
        "model": MODELO,
        "api_base": API_BASE,
        "api_key": chave,
        "temperature": 0.2,      # baixo: queremos texto estável, não criativo
        "request_timeout": 30,   # segundos; evita a demo travar esperando a API
        "max_retries": 1,
    }
    parametros.update(extras)
    return ChatLiteLLM(**parametros)


def texto_da_mensagem(mensagem) -> str:
    """Texto de uma resposta do LangChain. O conteúdo pode vir como str ou como lista de partes."""
    conteudo = getattr(mensagem, "content", "")
    if isinstance(conteudo, list):
        conteudo = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in conteudo)
    return (conteudo or "").strip()


def chamar_llm(prompt: str, run_id: str = "") -> str:
    """Envia o prompt ao modelo e devolve o texto. Grava uma linha em uso_api.csv por chamada.

    Levanta exceção se a chamada falhar ou se a resposta for vazia/curta demais; quem trata é
    gerar_relatorio, então aqui não há try/except de recuperação, só o registro do que aconteceu.
    """
    llm = criar_llm(max_tokens=300)          # o prompt pede 3-4 frases
    inicio = time.perf_counter()
    try:
        resposta = llm.invoke(prompt)
    except Exception as erro:
        uso_api.registrar_chamada(run_id, "relatorio", 1, MODELO, 0, 0,
                                  time.perf_counter() - inicio, f"erro:{type(erro).__name__}")
        raise

    texto = texto_da_mensagem(resposta)
    valida = len(texto) >= TAMANHO_MINIMO_RESPOSTA
    entrada, saida = uso_api.extrair_uso(resposta)
    # Resposta inválida também gastou tokens: entra no custo, com status próprio.
    uso_api.registrar_chamada(run_id, "relatorio", 1, MODELO, entrada, saida,
                              time.perf_counter() - inicio, "ok" if valida else "resposta_invalida")
    if not valida:
        raise RespostaInvalida(f"resposta com {len(texto)} caracteres (mínimo {TAMANHO_MINIMO_RESPOSTA})")
    return texto


# ----------------------------------------------------------------------------------------------
# Log e fallback
# ----------------------------------------------------------------------------------------------
def registrar_log(texto: str) -> None:
    """Acrescenta um trecho ao prompts_log.md (cria a pasta se não existir).
    Falha de gravação só avisa: o log nunca pode derrubar o relatório."""
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(texto)
    except OSError as erro:
        logger.warning("Não consegui gravar %s: %s", LOG_PATH, erro)


def texto_reserva(resultado: dict) -> str:
    """Texto montado por template, usado quando a API não responde ou responde algo inutilizável."""
    return (
        "*(Texto-modelo: a IA não respondeu, então este parágrafo foi montado "
        "direto dos números da simulação.)*\n\n"
        f"Recomenda-se frete grátis acima de R$ {resultado['threshold']:.0f} no Marketplace, "
        f"recuperando R$ {brl(resultado['margem_recuperada'])} em margem e isentando "
        f"{_decimal_br(resultado['pct_pedidos_isentos'])}% dos pedidos. O frete restante "
        f"passa a representar {_decimal_br(resultado['frete_pct_receita_nova'])}% da receita do canal."
    )


def _causa_raiz(erro: BaseException) -> str:
    """Desce a cadeia __cause__/__context__ até o erro mais interno. O "Connection error" do LiteLLM
    esconde o erro real (URL sem https, DNS, conexão cortada...) alguns níveis abaixo."""
    vistos = set()
    while id(erro) not in vistos:
        vistos.add(id(erro))
        proximo = erro.__cause__ or erro.__context__
        if proximo is None:
            break
        erro = proximo
    return f"{type(erro).__name__}: {str(erro)[:150]}"


def gerar_relatorio(resultado: dict) -> str:
    """Ponto de entrada: qualquer front chama só esta função e sempre recebe um texto.

    Fluxo: monta o prompt -> loga -> chama o LLM -> loga a resposta -> devolve.
    Se o LLM falhar, devolve o texto reserva em vez de derrubar a tela, e o log marca FALLBACK
    (com o tipo do erro) para não passar por resposta real do modelo.
    """
    run_id = uso_api.novo_run_id()
    prompt = montar_prompt(resultado)
    momento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Prompt em bloco de código: fora dele, o markdown esconde trechos entre < e > (lidos como tags HTML).
    # O prompt já termina com quebra de linha, então a cerca de fechamento vem logo depois dele.
    registrar_log(f"\n---\n**Prompt** ({VERSAO_RELATORIO}, {momento}):\n```text\n{prompt}```\n")

    try:
        texto = chamar_llm(prompt, run_id)
        registrar_log(f"\n**Resposta:**\n{texto}\n")
    except Exception as erro:
        # A mensagem completa e a causa raiz vão só para o terminal (podem conter trecho da chave).
        # O log, que é entregável, leva apenas o tipo do erro.
        logger.warning("LLM falhou (%s). Causa raiz: %s", type(erro).__name__, _causa_raiz(erro))
        texto = texto_reserva(resultado)
        registrar_log(f"\n**Resposta (FALLBACK, {type(erro).__name__}):**\n{texto}\n")
    return texto


if __name__ == "__main__":
    # Teste manual com a chave real: python relatorio.py (de dentro de src/)
    import pandas as pd
    from simulador import simular

    pedidos = pd.read_csv(os.path.join(PROTOTIPO_DIR, "data", "marketplace_pedidos.csv"))
    resultado = simular(250, pedidos)
    print(resultado, "\n")
    print(gerar_relatorio(resultado))
    print("\nuso desta execução:", uso_api.resumo_uso())
