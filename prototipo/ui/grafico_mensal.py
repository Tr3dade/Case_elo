"""Escala dos dois eixos do gráfico mensal (receita líquida e deduções à esquerda, margem à direita).

O problema: com as deduções desenhadas ABAIXO do zero, o eixo esquerdo vai de um pouco abaixo de zero até o
máximo da receita (o zero fica ~14% acima do fundo). O eixo da margem só tem valores positivos, então o ECharts o
começa em 0 no fundo do gráfico. Resultado: dois "zeros" em alturas diferentes, e a linha da margem parece
comparável com as barras quando não é.

A correção é só de escala, nenhum dado muda: os dois eixos passam a ter o MESMO número de divisões acima e abaixo
do zero (cada um com o seu passo "redondo"). O zero cai na mesma altura e as linhas de grade coincidem.
"""
import math

# Múltiplos "redondos" para o passo de cada eixo (1, 2, 2,5, 5 ou 10 vezes uma potência de 10).
PASSOS_REDONDOS = (1, 2, 2.5, 5, 10)
DIVISOES_MAX = 8                      # o eixo esquerdo usa o menor passo redondo que cabe em até 8 divisões
_FOLGA = 1e-9                         # tolerância de ponto flutuante nas comparações de "cabe / não cabe"


def _passo_redondo(minimo: float) -> float:
    """Menor passo redondo que é maior ou igual a `minimo` (1 se `minimo` for zero ou negativo)."""
    if minimo <= 0:
        return 1
    potencia = 10 ** math.floor(math.log10(minimo))
    for fator in PASSOS_REDONDOS:
        if fator * potencia >= minimo * (1 - _FOLGA):
            return fator * potencia


def eixos_alinhados(min_esq: float, max_esq: float, min_dir: float, max_dir: float) -> dict:
    """{"esq": {min, max, interval}, "dir": {...}} com o zero na mesma altura nos dois eixos.

    Os quatro parâmetros são o menor e o maior valor plotado em cada eixo. O eixo esquerdo manda: escolhe o passo
    e quantas divisões ficam abaixo (k_neg) e acima (k_pos) do zero. O direito usa as MESMAS contagens com o
    menor passo redondo que ainda comporta os dados dele.
    """
    menor_esq, maior_esq = min(min_esq, 0), max(max_esq, 0)         # o zero sempre entra no eixo
    menor_dir, maior_dir = min(min_dir, 0), max(max_dir, 0)

    # Sobe de passo redondo em passo redondo até o eixo caber em DIVISOES_MAX divisões. (Dividir o intervalo por
    # um número fixo de divisões e arredondar para cima saltava de 500 mil para 1 mi por 0,01% de diferença.)
    passo_esq = _passo_redondo((maior_esq - menor_esq) / DIVISOES_MAX)
    while math.ceil(maior_esq / passo_esq - _FOLGA) + math.ceil(-menor_esq / passo_esq - _FOLGA) > DIVISOES_MAX:
        passo_esq = _passo_redondo(passo_esq * 1.0001)              # o próximo passo redondo acima
    k_pos = math.ceil(maior_esq / passo_esq - _FOLGA)
    k_neg = math.ceil(-menor_esq / passo_esq - _FOLGA)
    # o eixo direito pode ter dado onde o esquerdo não tem: garante ao menos uma divisão desse lado
    if maior_dir > 0:
        k_pos = max(k_pos, 1)
    if menor_dir < 0:
        k_neg = max(k_neg, 1)
    k_pos = max(k_pos, 1) if k_pos + k_neg == 0 else k_pos          # série toda zerada: eixo com ao menos 1 divisão

    exigido_dir = max(maior_dir / k_pos if k_pos else 0, -menor_dir / k_neg if k_neg else 0)
    passo_dir = _passo_redondo(exigido_dir)
    return {
        "esq": {"min": -k_neg * passo_esq, "max": k_pos * passo_esq, "interval": passo_esq},
        "dir": {"min": -k_neg * passo_dir, "max": k_pos * passo_dir, "interval": passo_dir},
    }


def eixos_do_grafico(receita_liquida, devolucoes_descontos, margem_contribuicao) -> dict:
    """eixos_alinhados a partir das MESMAS três listas que o gráfico recebe.

    As deduções chegam positivas e o gráfico as desenha negativas (-valor), então o menor valor do eixo
    esquerdo é o negativo da maior dedução. Fica aqui, e não no app.py, para a convenção de sinal ter um dono só.
    """
    barras = list(receita_liquida) + [-valor for valor in devolucoes_descontos]
    margem = list(margem_contribuicao)
    return eixos_alinhados(min(barras), max(barras), min(margem), max(margem))
