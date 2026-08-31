import os
import pandas as pd

# ============================================================================
# CONFIG — ancorado na localização deste arquivo, não no diretório de onde
# o comando "python3 ..." é chamado (funciona rodando de metrics/ ou da raiz)
# ============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_SCRIPT, "..", "data")
PASTA_SAIDA = os.path.join(PASTA_SCRIPT, "output", "analise_vertice")

ARQ_VENDAS = os.path.join(PASTA_DADOS, "vendas.csv")
ARQ_MARKETING = os.path.join(PASTA_DADOS, "marketing.csv")
ARQ_CLIENTES = os.path.join(PASTA_DADOS, "clientes.csv")
ARQ_ATENDIMENTO = os.path.join(PASTA_DADOS, "atendimento.csv")
ARQ_ESTOQUE = os.path.join(PASTA_DADOS, "estoque.csv")

pd.set_option("display.width", 160)
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda x: f"{x:,.2f}")


def salvar(df: pd.DataFrame, nome: str):
    """Salva um DataFrame em /saida e retorna o próprio df (para encadear)."""
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
# 1. VENDAS — visão geral, canal, categoria, produto, mês, devoluções
# ============================================================================
def analisar_vendas():
    titulo("1. VENDAS — visão geral")
    df = pd.read_csv(ARQ_VENDAS, parse_dates=["data_pedido"])
    df["devolvido"] = df["devolvido"].astype(bool)
    df["mes"] = df["data_pedido"].dt.to_period("M").astype(str)

    receita_liquida = df["receita_liquida"].sum()
    margem_total = df["margem_contribuicao"].sum()
    desconto_total = df["desconto_reais"].sum()
    taxa_devolucao = df["devolvido"].mean() * 100

    resumo = pd.DataFrame({
        "indicador": [
            "Pedidos", "Receita bruta", "Receita líquida", "Desconto total",
            "Desconto % s/ receita bruta", "Margem de contribuição total",
            "Margem % s/ receita líquida", "Taxa de devolução (%)",
            "Pedidos com margem negativa",
        ],
        "valor": [
            len(df), df["receita_bruta"].sum(), receita_liquida, desconto_total,
            desconto_total / df["receita_bruta"].sum() * 100, margem_total,
            margem_total / receita_liquida * 100, taxa_devolucao,
            (df["margem_contribuicao"] < 0).sum(),
        ],
    })
    print(resumo.to_string(index=False))
    salvar(resumo, "01_vendas_resumo_geral")

    # --- ALERTA: margem não é ajustada pela devolução ---
    margem_devolvidos = df.loc[df["devolvido"], "margem_contribuicao"].sum()
    print(f"\n  [ALERTA] Margem 'presa' em pedidos devolvidos (não descontada do "
          f"total reportado): R$ {margem_devolvidos:,.2f} "
          f"({margem_devolvidos/margem_total*100:.1f}% da margem total)")

    # --- por canal ---
    titulo("1.1 Vendas por canal")
    por_canal = df.groupby("canal").agg(
        pedidos=("order_id", "count"),
        receita_liquida=("receita_liquida", "sum"),
        margem=("margem_contribuicao", "sum"),
        desconto=("desconto_reais", "sum"),
        taxa_devolucao=("devolvido", "mean"),
        pedidos_margem_negativa=("margem_contribuicao", lambda s: (s < 0).sum()),
    )
    por_canal["margem_pct"] = por_canal["margem"] / por_canal["receita_liquida"] * 100
    por_canal["desconto_pct"] = (
        por_canal["desconto"] / (por_canal["receita_liquida"] + por_canal["desconto"]) * 100
    )
    por_canal["taxa_devolucao"] *= 100
    por_canal = por_canal.sort_values("receita_liquida", ascending=False)
    print(por_canal.to_string())
    salvar(por_canal, "02_vendas_por_canal")

    # --- por categoria ---
    titulo("1.2 Vendas por categoria de produto")
    por_categoria = df.groupby("categoria").agg(
        pedidos=("order_id", "count"),
        receita_liquida=("receita_liquida", "sum"),
        margem=("margem_contribuicao", "sum"),
        desconto=("desconto_reais", "sum"),
        taxa_devolucao=("devolvido", "mean"),
    )
    por_categoria["margem_pct"] = por_categoria["margem"] / por_categoria["receita_liquida"] * 100
    por_categoria["taxa_devolucao"] *= 100
    por_categoria = por_categoria.sort_values("receita_liquida", ascending=False)
    print(por_categoria.to_string())
    salvar(por_categoria, "03_vendas_por_categoria")

    # --- por produto (mínimo de pedidos para relevância estatística) ---
    titulo("1.3 Vendas por produto (margem %, mínimo 30 pedidos)")
    por_produto = df.groupby("produto").agg(
        pedidos=("order_id", "count"),
        receita_liquida=("receita_liquida", "sum"),
        margem=("margem_contribuicao", "sum"),
        taxa_devolucao=("devolvido", "mean"),
    )
    por_produto = por_produto[por_produto["pedidos"] >= 30].copy()
    por_produto["margem_pct"] = por_produto["margem"] / por_produto["receita_liquida"] * 100
    por_produto["taxa_devolucao"] *= 100
    por_produto = por_produto.sort_values("margem_pct")
    print("Piores 10 em margem %:")
    print(por_produto.head(10).to_string())
    salvar(por_produto, "04_vendas_por_produto")

    # --- tendência mensal ---
    titulo("1.4 Tendência mensal")
    mensal = df.groupby("mes").agg(
        pedidos=("order_id", "count"),
        receita_liquida=("receita_liquida", "sum"),
        margem=("margem_contribuicao", "sum"),
        desconto=("desconto_reais", "sum"),
        taxa_devolucao=("devolvido", "mean"),
    )
    mensal["margem_pct"] = mensal["margem"] / mensal["receita_liquida"] * 100
    mensal["taxa_devolucao"] *= 100
    print(mensal.to_string())
    salvar(mensal, "05_vendas_tendencia_mensal")

    # --- motivos de devolução ---
    titulo("1.5 Motivos de devolução")
    devolvidos = df[df["devolvido"]]
    motivos = devolvidos["motivo_devolucao"].value_counts().to_frame("qtd_tickets")
    motivos["pct"] = motivos["qtd_tickets"] / motivos["qtd_tickets"].sum() * 100
    print(motivos.to_string())
    salvar(motivos, "06_motivos_devolucao")

    return df


# ============================================================================
# 2. MARKETING — eficiência por canal e conciliação com vendas reais
# ============================================================================
def analisar_marketing(receita_liquida_vendas: float):
    titulo("2. MARKETING — eficiência por canal")
    df = pd.read_csv(ARQ_MARKETING, parse_dates=["data_inicio", "data_fim"])

    por_canal = df.groupby("canal").agg(
        campanhas=("campanha_id", "count"),
        investimento=("investimento_reais", "sum"),
        conversoes=("conversoes", "sum"),
        receita_gerada_reportada=("receita_gerada", "sum"),
    )
    por_canal["cac_real"] = por_canal["investimento"] / por_canal["conversoes"]
    por_canal["roas_real"] = por_canal["receita_gerada_reportada"] / por_canal["investimento"]
    por_canal = por_canal.sort_values("roas_real", ascending=False)
    print(por_canal.to_string())
    salvar(por_canal, "07_marketing_por_canal")

    receita_gerada_total = df["receita_gerada"].sum()
    fator_distorcao = receita_gerada_total / receita_liquida_vendas
    print(f"\n  [ALERTA] Receita 'gerada' reportada pelo marketing: "
          f"R$ {receita_gerada_total:,.2f}")
    print(f"  [ALERTA] Receita líquida real (vendas.csv): "
          f"R$ {receita_liquida_vendas:,.2f}")
    print(f"  [ALERTA] Fator de distorção (atribuição vs. venda real): "
          f"{fator_distorcao:.1f}x — indica sobreposição/duplicidade de atribuição "
          f"entre campanhas.")

    return df


# ============================================================================
# 3. CLIENTES — segmentação RFM e concentração de valor
# ============================================================================
def analisar_clientes():
    titulo("3. CLIENTES — segmentação RFM")
    df = pd.read_csv(ARQ_CLIENTES)

    por_segmento = df.groupby("segmento_rfm").agg(
        clientes=("customer_id", "count"),
        ltv_medio=("ltv_acumulado", "mean"),
        ltv_total=("ltv_acumulado", "sum"),
        pedidos_medio=("total_pedidos_historico", "mean"),
    )
    por_segmento["pct_clientes"] = por_segmento["clientes"] / por_segmento["clientes"].sum() * 100
    por_segmento["pct_ltv"] = por_segmento["ltv_total"] / por_segmento["ltv_total"].sum() * 100
    por_segmento = por_segmento.sort_values("ltv_total", ascending=False)
    print(por_segmento.to_string())
    salvar(por_segmento, "08_clientes_por_segmento_rfm")

    titulo("3.1 Nível de fidelidade")
    fidelidade = df["nivel_fidelidade"].value_counts().to_frame("clientes")
    fidelidade["pct"] = fidelidade["clientes"] / fidelidade["clientes"].sum() * 100
    print(fidelidade.to_string())
    salvar(fidelidade, "09_clientes_nivel_fidelidade")

    risco = df[df["segmento_rfm"].isin(["Em Risco", "Hibernando", "Churn"])]
    print(f"\n  [DESTAQUE] Clientes em risco/hibernando/churn: {len(risco)} "
          f"({len(risco)/len(df)*100:.1f}% da base), representando "
          f"R$ {risco['ltv_acumulado'].sum():,.2f} de LTV "
          f"({risco['ltv_acumulado'].sum()/df['ltv_acumulado'].sum()*100:.1f}% do LTV total).")

    return df


# ============================================================================
# 4. ATENDIMENTO — volume, custo e qualidade por categoria de problema
# ============================================================================
def analisar_atendimento():
    titulo("4. ATENDIMENTO — por categoria de problema")
    df = pd.read_csv(ARQ_ATENDIMENTO)

    por_categoria = df.groupby("categoria_problema").agg(
        tickets=("ticket_id", "count"),
        custo_total=("custo_operacional_ticket", "sum"),
        tempo_resposta_medio_min=("tempo_primeira_resposta_minutos", "mean"),
        csat_medio=("nota_csat", "mean"),
    )
    por_categoria["pct_tickets"] = por_categoria["tickets"] / por_categoria["tickets"].sum() * 100
    por_categoria = por_categoria.sort_values("tickets", ascending=False)
    print(por_categoria.to_string())
    salvar(por_categoria, "10_atendimento_por_categoria")

    titulo("4.1 Status dos tickets")
    status = df["status_atendimento"].value_counts().to_frame("tickets")
    status["pct"] = status["tickets"] / status["tickets"].sum() * 100
    print(status.to_string())
    salvar(status, "11_atendimento_status")

    return df


# ============================================================================
# 5. ESTOQUE — disponibilidade e criticidade
# ============================================================================
def analisar_estoque():
    titulo("5. ESTOQUE — status de disponibilidade")
    df = pd.read_csv(ARQ_ESTOQUE)

    status = df["status_disponibilidade"].value_counts().to_frame("skus")
    status["pct"] = status["skus"] / status["skus"].sum() * 100
    print(status.to_string())
    salvar(status, "12_estoque_status")

    titulo("5.1 Estoque por categoria")
    por_categoria = df.groupby("categoria").agg(
        skus=("sku_id", "count"),
        estoque_disponivel_medio=("estoque_disponivel", "mean"),
        lead_time_medio=("lead_time_reposicao", "mean"),
    )
    print(por_categoria.to_string())
    salvar(por_categoria, "13_estoque_por_categoria")

    criticos = df[df["status_disponibilidade"].isin(["Ruptura", "Estoque Crítico"])]
    valor_exposto = (criticos["custo_unitario"] * criticos["estoque_disponivel"]).sum()
    print(f"\n  [DESTAQUE] SKUs em ruptura/crítico: {len(criticos)} "
          f"({len(criticos)/len(df)*100:.1f}% do catálogo). "
          f"Valor de estoque exposto: R$ {valor_exposto:,.2f}")

    return df


# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    df_vendas = analisar_vendas()
    analisar_marketing(receita_liquida_vendas=df_vendas["receita_liquida"].sum())
    analisar_clientes()
    analisar_atendimento()
    analisar_estoque()

    titulo("CONCLUÍDO")
    print(f"Todas as tabelas de resultado foram salvas em: {os.path.abspath(PASTA_SAIDA)}")

if __name__ == "__main__":
    main()
