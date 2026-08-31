"""
analise_final.py

Objetivo: fechar o ciclo de análise consolidando os 3 pilares testados nos
scripts anteriores (analise_vertice.py e analise_convergencia.py) num único
relatório de síntese, em Markdown, pronto para embasar o Diagnóstico
Executivo e o Pitch.

Este script NÃO depende dos CSVs de saída dos outros scripts — ele recalcula
tudo direto de data/, para não correr risco de sintetizar em cima de um
resultado desatualizado. A única coisa nova aqui (que ainda não tinha sido
calculada em nenhum dos scripts anteriores) é o item pendente do Pilar 2:
a reconciliação de ROAS FILTRADA para o mesmo período de vendas.csv
(ver Bloco A do analise_convergencia.py — marketing.csv cobre até 2025,
vendas.csv só até jan/2024, então a reconciliação correta precisa
descartar campanhas fora desse período antes de comparar por canal).

Pilares:
  1. Margem por canal                          -> já validado (achado 1)
  2. ROAS/CAC reconciliado, filtrado por período -> item que estava pendente
  3. Causa-raiz (frete/logística no Marketplace) -> já validado (achado do
     analise_convergencia.py, Bloco B.2 + C.2)

Saída: metrics/output/analise_final/sintese_final.md
       metrics/output/analise_final/pilares_resumo.csv
"""

import os
import pandas as pd

# ============================================================================
# CONFIG — ancorado na localização deste arquivo (mesmo padrão dos outros
# dois scripts), não no diretório de onde o comando é chamado.
# ============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_SCRIPT, "..", "data")
PASTA_SAIDA = os.path.join(PASTA_SCRIPT, "output", "analise_final")

ARQ_VENDAS = os.path.join(PASTA_DADOS, "vendas.csv")
ARQ_MARKETING = os.path.join(PASTA_DADOS, "marketing.csv")

pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


def salvar(df: pd.DataFrame, nome: str):
    os.makedirs(PASTA_SAIDA, exist_ok=True)
    caminho = os.path.join(PASTA_SAIDA, f"{nome}.csv")
    df.to_csv(caminho, encoding="utf-8-sig")
    print(f"  -> salvo em {caminho}")
    return df


def titulo(texto: str):
    print("\n" + "=" * 90)
    print(texto)
    print("=" * 90)


# ============================================================================
# PILAR 1 — Margem por canal (recalculado para o relatório final)
# ============================================================================
def pilar_1_margem(vendas: pd.DataFrame) -> dict:
    titulo("PILAR 1 — Margem por canal")

    por_canal = vendas.groupby("canal").agg(
        pedidos=("order_id", "count"),
        receita_liquida=("receita_liquida", "sum"),
        margem=("margem_contribuicao", "sum"),
    )
    por_canal["margem_pct"] = por_canal["margem"] / por_canal["receita_liquida"] * 100
    por_canal = por_canal.sort_values("margem_pct")
    print(por_canal.to_string())

    margem_marketplace = por_canal.loc["Marketplace", "margem_pct"]
    margem_outros = por_canal.drop("Marketplace")["margem_pct"].mean()
    gap_pp = margem_outros - margem_marketplace

    print(f"\n  [SÍNTESE] Marketplace: {margem_marketplace:.2f}% de margem vs. "
          f"{margem_outros:.2f}% médio dos outros canais (gap de {gap_pp:.2f}pp).")

    return {
        "status": "CONFIRMADO",
        "margem_marketplace_pct": round(margem_marketplace, 2),
        "margem_outros_pct": round(margem_outros, 2),
        "gap_pp": round(gap_pp, 2),
        "periodo": f"{vendas['data_pedido'].min().date()} a {vendas['data_pedido'].max().date()}",
    }


# ============================================================================
# PILAR 2 — ROAS reconciliado, filtrado ao período de vendas.csv
# (este é o cálculo que faltava — a peça pendente da análise)
# ============================================================================
def pilar_2_roas_reconciliado(vendas: pd.DataFrame, marketing: pd.DataFrame) -> dict:
    titulo("PILAR 2 — ROAS reconciliado (filtrado ao período de vendas.csv)")

    periodo_ini = vendas["data_pedido"].min()
    periodo_fim = vendas["data_pedido"].max()
    print(f"  Período de referência (vendas.csv): {periodo_ini.date()} a {periodo_fim.date()}")

    # filtra só campanhas com início dentro do período coberto por vendas.csv
    marketing_periodo = marketing[
        (marketing["data_inicio"] >= periodo_ini) & (marketing["data_inicio"] <= periodo_fim)
    ].copy()
    print(f"  Campanhas dentro do período: {len(marketing_periodo)} de {len(marketing)} "
          f"({len(marketing_periodo)/len(marketing)*100:.1f}%)")

    receita_real_canal = vendas.groupby("canal")["receita_liquida"].sum()
    investimento_canal = marketing_periodo.groupby("canal")["investimento_reais"].sum()

    recon = pd.DataFrame({
        "receita_liquida_real": receita_real_canal,
        "investimento_periodo": investimento_canal,
    }).dropna()
    recon["roas_reconciliado"] = recon["receita_liquida_real"] / recon["investimento_periodo"]
    recon = recon.sort_values("roas_reconciliado", ascending=False)
    recon["posicao"] = range(1, len(recon) + 1)
    print(recon.to_string())
    salvar(recon, "pilar2_roas_reconciliado_periodo")

    posicao_marketplace = int(recon.loc["Marketplace", "posicao"])
    total_canais = len(recon)
    # critério definido em conversa: sustenta o pilar se Marketplace ficar
    # entre os 2 piores (posição 6 ou 7 de 7 canais)
    sustenta = posicao_marketplace >= total_canais - 1

    print(f"\n  [SÍNTESE] Marketplace fica na posição {posicao_marketplace} de {total_canais} "
          f"em ROAS reconciliado (1 = melhor).")
    print(f"  Critério (2 piores sustentam o pilar): "
          f"{'SUSTENTA' if sustenta else 'NÃO SUSTENTA'}")
    print("  [ALERTA] mesmo filtrado por período, os valores absolutos de ROAS reconciliado")
    print("  seguem baixos para todos os canais (investimento >> receita atribuível), o que")
    print("  indica que ainda pode haver mismatch de granularidade entre as bases (marketing.csv")
    print("  não tem campanha_id em vendas.csv — o join é só por rótulo de canal, não transacional).")
    print("  Tratar o RANKING relativo como o sinal confiável, não os valores absolutos.")

    return {
        "status": "SUSTENTA" if sustenta else "NÃO SUSTENTA",
        "posicao_marketplace": posicao_marketplace,
        "total_canais": total_canais,
        "ressalva": "valores absolutos pouco confiáveis (possível mismatch de granularidade "
                    "entre vendas.csv e marketing.csv); usar apenas o ranking relativo",
    }


# ============================================================================
# PILAR 3 — Causa-raiz (frete/logística), recalculado para o relatório final
# ============================================================================
def pilar_3_causa_raiz(vendas: pd.DataFrame) -> dict:
    titulo("PILAR 3 — Causa-raiz: composição de custo por canal")

    custo_pct = vendas.groupby("canal").apply(
        lambda g: pd.Series({
            "custo_frete_pct_receita": g["custo_frete"].sum() / g["receita_liquida"].sum() * 100,
        }),
        include_groups=False,
    ).sort_values("custo_frete_pct_receita", ascending=False)
    print(custo_pct.to_string())

    frete_marketplace = custo_pct.loc["Marketplace", "custo_frete_pct_receita"]
    frete_outros = custo_pct.drop("Marketplace")["custo_frete_pct_receita"].mean()

    receita_marketplace = vendas[vendas["canal"] == "Marketplace"]["receita_liquida"].sum()
    frete_atual = vendas[vendas["canal"] == "Marketplace"]["custo_frete"].sum()
    frete_hipotetico = receita_marketplace * (frete_outros / 100)
    oportunidade = frete_atual - frete_hipotetico

    print(f"\n  [SÍNTESE] Frete do Marketplace: {frete_marketplace:.2f}% da receita vs. "
          f"{frete_outros:.2f}% médio dos outros canais.")
    print(f"  Margem adicional recuperável estimada: R$ {oportunidade:,.2f}")

    return {
        "status": "CONFIRMADO",
        "causa": "custo de frete/logística do Marketplace desproporcional aos demais canais",
        "frete_marketplace_pct": round(frete_marketplace, 2),
        "frete_outros_pct": round(frete_outros, 2),
        "oportunidade_recuperavel_reais": round(oportunidade, 2),
        "hipoteses_descartadas": "mix de categoria, mix de cliente/RFM, desconto por categoria, "
                                  "ticket médio, método de pagamento, custo de atendimento",
    }


# ============================================================================
# RELATÓRIO FINAL EM MARKDOWN
# ============================================================================
def gerar_relatorio_md(p1: dict, p2: dict, p3: dict):
    titulo("Gerando relatório de síntese")

    md = f"""# Síntese Final — Diagnóstico Vértice Retail (Marketplace)

*Gerado automaticamente por `analise_final.py`. Consolida os 3 pilares testados
em `analise_vertice.py` e `analise_convergencia.py`.*

## Status dos 3 pilares

| Pilar | Status | Achado |
|---|---|---|
| 1. Margem | **{p1['status']}** | Marketplace: {p1['margem_marketplace_pct']}% vs. {p1['margem_outros_pct']}% dos demais (gap de {p1['gap_pp']}pp) |
| 2. ROAS reconciliado | **{p2['status']}** | Marketplace na posição {p2['posicao_marketplace']} de {p2['total_canais']} (1 = melhor) |
| 3. Causa-raiz | **{p3['status']}** | {p3['causa']} |

## Pilar 1 — Margem (confirmado)

O Marketplace tem margem estruturalmente mais baixa que os demais canais,
sem explicação por categoria, SKU ou sazonalidade (achado original,
`Analise_Indicadores_Vertice.md` e `relatorio_conselho_vertice2.md`).

## Pilar 2 — ROAS reconciliado

Reconciliação feita filtrando `marketing.csv` apenas para campanhas com
início dentro do período coberto por `vendas.csv` ({p1.get('periodo', '')}),
usando receita real de venda em vez da "receita gerada" reportada por
marketing (que está inflada e cobre um período ~2x maior que as vendas).

**Ressalva importante:** {p2['ressalva']}. O ranking relativo entre canais é
o sinal utilizável; os valores absolutos de ROAS não devem ser citados no
pitch como número definitivo.

## Pilar 3 — Causa-raiz (confirmado)

- Custo de frete do Marketplace: **{p3['frete_marketplace_pct']}%** da receita
- Custo de frete médio dos demais canais: **{p3['frete_outros_pct']}%** da receita
- Margem adicional recuperável estimada: **R$ {p3['oportunidade_recuperavel_reais']:,.2f}**

Hipóteses alternativas testadas e descartadas: {p3['hipoteses_descartadas']}.

Achado de apoio (base independente): "Atraso na entrega" é proporcionalmente
mais comum nas devoluções do Marketplace (23,6%) do que na média geral
(19,6%) — mesmo sintoma logístico, capturado em outra base.

## Recomendação para o Pitch

Abrir com o sintoma (Pilar 1: margem do Marketplace abaixo dos demais canais),
fechar com a causa-raiz (Pilar 3: custo de frete/logística desproporcional,
provavelmente ligado à estrutura de comissão da plataforma), e usar o Pilar 2
como evidência de apoio com a ressalva de confiabilidade explicitada — não
como pilar central do argumento.
"""

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    caminho_md = os.path.join(PASTA_SAIDA, "sintese_final.md")
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"  -> salvo em {caminho_md}")

    resumo_df = pd.DataFrame([
        {"pilar": "1. Margem", **p1},
        {"pilar": "2. ROAS reconciliado", **p2},
        {"pilar": "3. Causa-raiz", **p3},
    ])
    salvar(resumo_df, "pilares_resumo")


# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    vendas = pd.read_csv(ARQ_VENDAS, parse_dates=["data_pedido"])
    marketing = pd.read_csv(ARQ_MARKETING, parse_dates=["data_inicio", "data_fim"])

    p1 = pilar_1_margem(vendas)
    p2 = pilar_2_roas_reconciliado(vendas, marketing)
    p3 = pilar_3_causa_raiz(vendas)

    gerar_relatorio_md(p1, p2, p3)

    titulo("CONCLUÍDO")
    print(f"Relatório final em: {os.path.join(PASTA_SAIDA, 'sintese_final.md')}")


if __name__ == "__main__":
    main()