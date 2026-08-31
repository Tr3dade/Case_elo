"""
analise_convergencia.py

Objetivo: fechar o "segundo diamante" (convergência) testando os pontos
que ainda estavam em aberto depois do diagnóstico inicial (Analise_Indicadores_Vertice.md
+ relatorio_conselho_vertice2.md):

  BLOCO A — Escala/granularidade entre vendas.csv e marketing.csv
            (decide se dá pra confiar em qualquer reconciliação de ROAS)
  BLOCO B — Causa-raiz da margem mais baixa do Marketplace
            (mix de categoria, custo, cliente, desconto, ticket médio)
  BLOCO C — Cruzamentos entre bases (atendimento x canal, devolução x canal,
            estoque x categoria mais vendida no Marketplace)

Cada bloco responde UMA pergunta concreta — isso não é uma varredura aberta
da base inteira, é um conjunto de testes de hipótese específicos.

Segue o mesmo padrão de pastas do analise_vertice.py (base/ e saida/) para
poder ser rodado dentro do mesmo repositório do projeto.
"""

import os
import pandas as pd

# ============================================================================
# CONFIG — segue a estrutura do projeto:
#   Case_elo/
#     data/                  <- CSVs de origem (irmã de metrics/)
#     metrics/
#       analise_convergencia.py   <- este script
#       output/                    <- resultados gerados
#
# IMPORTANTE: os caminhos abaixo são ancorados na localização deste arquivo
# (__file__), não no diretório de onde o comando "python3 ..." é chamado.
# Isso garante que o script funcione tanto rodando de dentro de metrics/
# quanto rodando da raiz do projeto (python3 metrics/analise_convergencia.py).
# ============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA_SCRIPT, "..", "data")
PASTA_SAIDA = os.path.join(PASTA_SCRIPT, "output", "analise_convergencia")

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
# BLOCO A — Escala/granularidade entre vendas.csv e marketing.csv
# ============================================================================
def bloco_a_escala_bases():
    """
    Pergunta: dá para comparar investimento de marketing.csv com receita de
    vendas.csv por canal? Ou as duas bases cobrem escopos/períodos diferentes
    o suficiente para tornar qualquer reconciliação de ROAS inválida?

    Testa 3 coisas:
      A.1 — período coberto por cada base
      A.2 — proporção investimento/receita ao longo do tempo (uniforme ou concentrada?)
      A.3 — campanhas por canal vs. pedidos por canal (desproporção estrutural?)
    """
    titulo("BLOCO A — Escala e granularidade entre vendas.csv e marketing.csv")

    vendas = pd.read_csv(ARQ_VENDAS, parse_dates=["data_pedido"])
    marketing = pd.read_csv(ARQ_MARKETING, parse_dates=["data_inicio", "data_fim"])

    # --- A.1: período coberto ---
    titulo("A.1 Período coberto por cada base")
    periodo = pd.DataFrame({
        "base": ["vendas.csv", "marketing.csv (início)", "marketing.csv (fim)"],
        "data_min": [vendas["data_pedido"].min(), marketing["data_inicio"].min(), marketing["data_fim"].min()],
        "data_max": [vendas["data_pedido"].max(), marketing["data_inicio"].max(), marketing["data_fim"].max()],
    })
    print(periodo.to_string(index=False))
    salvar(periodo, "A1_periodo_cobertura")

    # --- A.2: proporção investimento/receita por mês ---
    titulo("A.2 Investimento vs. receita real por mês (uniforme ou concentrado?)")
    vendas["mes"] = vendas["data_pedido"].dt.to_period("M").astype(str)
    marketing["mes"] = marketing["data_inicio"].dt.to_period("M").astype(str)

    receita_mensal = vendas.groupby("mes")["receita_liquida"].sum()
    investimento_mensal = marketing.groupby("mes")["investimento_reais"].sum()

    prop_mensal = pd.DataFrame({
        "receita_liquida_real": receita_mensal,
        "investimento_marketing": investimento_mensal,
    }).dropna()
    prop_mensal["investimento_sobre_receita"] = (
        prop_mensal["investimento_marketing"] / prop_mensal["receita_liquida_real"]
    )
    print(prop_mensal.to_string())
    salvar(prop_mensal, "A2_proporcao_mensal_investimento_receita")

    cv = prop_mensal["investimento_sobre_receita"].std() / prop_mensal["investimento_sobre_receita"].mean()
    print(f"\n  [LEITURA] Coeficiente de variação da razão investimento/receita mês a mês: {cv:.2f}")
    print("  Se for baixo (~<0.3), a distorção é praticamente constante ao longo do tempo")
    print("  (aponta para problema estrutural/metodológico fixo, não sazonal).")
    print("  Se for alto, a distorção se concentra em períodos específicos (vale investigar quais).")

    # --- A.3: campanhas por canal vs. pedidos por canal ---
    titulo("A.3 Campanhas por canal vs. pedidos por canal")
    campanhas_canal = marketing.groupby("canal").agg(
        campanhas=("campanha_id", "count"),
        investimento_total=("investimento_reais", "sum"),
    )
    pedidos_canal = vendas.groupby("canal").agg(
        pedidos=("order_id", "count"),
        receita_total=("receita_liquida", "sum"),
    )
    comparativo = campanhas_canal.join(pedidos_canal)
    comparativo["investimento_por_campanha"] = comparativo["investimento_total"] / comparativo["campanhas"]
    comparativo["receita_por_pedido"] = comparativo["receita_total"] / comparativo["pedidos"]
    comparativo["pedidos_por_campanha"] = comparativo["pedidos"] / comparativo["campanhas"]
    print(comparativo.to_string())
    salvar(comparativo, "A3_campanhas_vs_pedidos_por_canal")
    print("\n  [LEITURA] 'pedidos_por_campanha' muito baixo (poucos pedidos para cada campanha)")
    print("  é sinal de que marketing.csv pode registrar campanhas em uma granularidade/escala")
    print("  não diretamente comparável a pedidos individuais de vendas.csv.")

    return vendas, marketing


# ============================================================================
# BLOCO B — Causa-raiz da margem mais baixa do Marketplace
# ============================================================================
def bloco_b_causa_raiz_marketplace(vendas: pd.DataFrame):
    """
    Pergunta: por que o Marketplace tem margem mais baixa? Testa 5 hipóteses
    concorrentes, todas dentro de vendas.csv + clientes.csv (dados já confiáveis,
    sem o problema de escala do Bloco A):

      B.1 — mix de categoria/subcategoria
      B.2 — composição de custo (produto + frete como % da receita)
      B.3 — mix de cliente por canal (segmento RFM, LTV)
      B.4 — desconto por categoria dentro do Marketplace
      B.5 — ticket médio e método de pagamento por canal
    """
    titulo("BLOCO B — Causa-raiz da margem do Marketplace")

    marketplace = vendas[vendas["canal"] == "Marketplace"].copy()
    outros = vendas[vendas["canal"] != "Marketplace"].copy()

    # --- B.1: mix de categoria ---
    titulo("B.1 Mix de categoria: Marketplace vs. outros canais")
    mix_mkt = marketplace["categoria"].value_counts(normalize=True).mul(100).rename("pct_marketplace")
    mix_out = outros["categoria"].value_counts(normalize=True).mul(100).rename("pct_outros_canais")
    mix_comparativo = pd.concat([mix_mkt, mix_out], axis=1)
    mix_comparativo["diferenca_pp"] = mix_comparativo["pct_marketplace"] - mix_comparativo["pct_outros_canais"]
    print(mix_comparativo.to_string())
    salvar(mix_comparativo, "B1_mix_categoria_marketplace_vs_outros")

    # --- B.2: composição de custo como % da receita ---
    titulo("B.2 Composição de custo (produto + frete) como % da receita, por canal")
    custo_pct = vendas.groupby("canal").apply(
        lambda g: pd.Series({
            "custo_produto_pct_receita": g["custo_produto"].sum() / g["receita_liquida"].sum() * 100,
            "custo_frete_pct_receita": g["custo_frete"].sum() / g["receita_liquida"].sum() * 100,
        }),
        include_groups=False,
    ).sort_values("custo_frete_pct_receita", ascending=False)
    print(custo_pct.to_string())
    salvar(custo_pct, "B2_composicao_custo_por_canal")
    print("\n  [LEITURA] Se custo_frete_pct_receita do Marketplace for visivelmente maior,")
    print("  é candidato a causa estrutural (ex: comissão de plataforma capturada em frete/custo).")

    # --- B.3: mix de cliente por canal (canal predominante de compra) ---
    titulo("B.3 Segmento RFM e LTV dos clientes que mais compram no Marketplace")
    clientes = pd.read_csv(ARQ_CLIENTES)

    # canal predominante de cada cliente = canal onde ele fez mais pedidos
    canal_predominante = (
        vendas.groupby(["customer_id", "canal"]).size()
        .reset_index(name="pedidos_no_canal")
        .sort_values("pedidos_no_canal", ascending=False)
        .drop_duplicates(subset="customer_id", keep="first")[["customer_id", "canal"]]
    )
    clientes_com_canal = clientes.merge(canal_predominante, on="customer_id", how="inner")

    perfil_por_canal = clientes_com_canal.groupby("canal").agg(
        clientes=("customer_id", "count"),
        ltv_medio=("ltv_acumulado", "mean"),
    )
    perfil_por_canal["pct_em_risco_hibernando_churn"] = clientes_com_canal.groupby("canal").apply(
        lambda g: g["segmento_rfm"].isin(["Em Risco", "Hibernando", "Churn"]).mean() * 100,
        include_groups=False,
    )
    perfil_por_canal = perfil_por_canal.sort_values("ltv_medio")
    print(perfil_por_canal.to_string())
    salvar(perfil_por_canal, "B3_perfil_cliente_por_canal_predominante")
    print("\n  [LEITURA] Se o Marketplace tiver LTV médio mais baixo e/ou maior % de clientes")
    print("  em risco/hibernando/churn, é sinal de que o canal atrai um perfil de cliente")
    print("  estruturalmente menos valioso — diagnóstico e solução diferentes de 'canal é ruim'.")

    # --- B.4: desconto por categoria dentro do Marketplace ---
    titulo("B.4 Desconto médio por categoria — dentro do Marketplace vs. média geral")
    desconto_mkt_categoria = marketplace.groupby("categoria").apply(
        lambda g: g["desconto_reais"].sum() / (g["receita_liquida"].sum() + g["desconto_reais"].sum()) * 100,
        include_groups=False,
    ).rename("desconto_pct_marketplace").sort_values(ascending=False)
    desconto_geral_categoria = vendas.groupby("categoria").apply(
        lambda g: g["desconto_reais"].sum() / (g["receita_liquida"].sum() + g["desconto_reais"].sum()) * 100,
        include_groups=False,
    ).rename("desconto_pct_geral")
    desconto_comparativo = pd.concat([desconto_mkt_categoria, desconto_geral_categoria], axis=1)
    desconto_comparativo["diferenca_pp"] = (
        desconto_comparativo["desconto_pct_marketplace"] - desconto_comparativo["desconto_pct_geral"]
    )
    print(desconto_comparativo.to_string())
    salvar(desconto_comparativo, "B4_desconto_categoria_marketplace_vs_geral")

    # --- B.5: ticket médio e método de pagamento ---
    titulo("B.5 Ticket médio e método de pagamento por canal")
    ticket_medio = vendas.groupby("canal")["receita_liquida"].mean().rename("ticket_medio").sort_values()
    print(ticket_medio.to_string())
    salvar(ticket_medio.to_frame(), "B5a_ticket_medio_por_canal")

    metodo_pagamento_mkt = marketplace["metodo_pagamento"].value_counts(normalize=True).mul(100)
    metodo_pagamento_geral = vendas["metodo_pagamento"].value_counts(normalize=True).mul(100)
    metodo_comparativo = pd.DataFrame({
        "pct_marketplace": metodo_pagamento_mkt,
        "pct_geral": metodo_pagamento_geral,
    })
    print(metodo_comparativo.to_string())
    salvar(metodo_comparativo, "B5b_metodo_pagamento_marketplace_vs_geral")

    return marketplace


# ============================================================================
# BLOCO C — Cruzamentos entre bases (evidência de apoio)
# ============================================================================
def bloco_c_cruzamentos(vendas: pd.DataFrame):
    """
    Pergunta: existe conexão entre o problema de margem do Marketplace e os
    problemas já identificados em atendimento/estoque? Testa 3 cruzamentos:

      C.1 — custo de atendimento por pedido, por canal (via order_id)
      C.2 — motivo de devolução dentro do Marketplace vs. geral
      C.3 — SKUs em ruptura/crítico concentrados nas categorias mais vendidas no Marketplace
    """
    titulo("BLOCO C — Cruzamentos entre bases")

    # --- C.1: custo de atendimento por pedido, por canal ---
    titulo("C.1 Custo de atendimento por pedido, por canal (via order_id)")
    atendimento = pd.read_csv(ARQ_ATENDIMENTO)
    # nem todo ticket tem order_id preenchido — filtra só os que têm vínculo direto
    atendimento_com_pedido = atendimento.dropna(subset=["order_id"])
    print(f"  Tickets com order_id vinculado: {len(atendimento_com_pedido)} de {len(atendimento)} "
          f"({len(atendimento_com_pedido)/len(atendimento)*100:.1f}%)")

    pedidos_canal = vendas[["order_id", "canal"]].drop_duplicates()
    atend_canal = atendimento_com_pedido.merge(pedidos_canal, on="order_id", how="inner")

    custo_atend_por_canal = atend_canal.groupby("canal").agg(
        tickets=("ticket_id", "count"),
        custo_total=("custo_operacional_ticket", "sum"),
    )
    pedidos_totais_canal = vendas.groupby("canal")["order_id"].nunique()
    custo_atend_por_canal["pedidos_no_canal"] = pedidos_totais_canal
    custo_atend_por_canal["tickets_por_pedido"] = (
        custo_atend_por_canal["tickets"] / custo_atend_por_canal["pedidos_no_canal"]
    )
    custo_atend_por_canal["custo_atendimento_por_pedido"] = (
        custo_atend_por_canal["custo_total"] / custo_atend_por_canal["pedidos_no_canal"]
    )
    custo_atend_por_canal = custo_atend_por_canal.sort_values("custo_atendimento_por_pedido", ascending=False)
    print(custo_atend_por_canal.to_string())
    salvar(custo_atend_por_canal, "C1_custo_atendimento_por_canal")

    # --- C.2: motivo de devolução dentro do Marketplace ---
    titulo("C.2 Motivo de devolução — Marketplace vs. geral")
    devolvidos = vendas[vendas["devolvido"] == True].copy()  # noqa: E712
    motivo_mkt = devolvidos[devolvidos["canal"] == "Marketplace"]["motivo_devolucao"].value_counts(normalize=True).mul(100)
    motivo_geral = devolvidos["motivo_devolucao"].value_counts(normalize=True).mul(100)
    motivo_comparativo = pd.DataFrame({
        "pct_marketplace": motivo_mkt,
        "pct_geral": motivo_geral,
    })
    print(motivo_comparativo.to_string())
    salvar(motivo_comparativo, "C2_motivo_devolucao_marketplace_vs_geral")

    # --- C.3: estoque crítico nas categorias mais vendidas no Marketplace ---
    titulo("C.3 Estoque crítico/ruptura nas categorias mais vendidas no Marketplace")
    estoque = pd.read_csv(ARQ_ESTOQUE)
    categorias_marketplace = vendas[vendas["canal"] == "Marketplace"]["categoria"].value_counts()

    estoque_por_categoria = estoque.groupby("categoria").apply(
        lambda g: pd.Series({
            "skus_totais": len(g),
            "skus_criticos_ruptura": g["status_disponibilidade"].isin(["Ruptura", "Estoque Crítico"]).sum(),
        }),
        include_groups=False,
    )
    estoque_por_categoria["pct_critico"] = (
        estoque_por_categoria["skus_criticos_ruptura"] / estoque_por_categoria["skus_totais"] * 100
    )
    estoque_por_categoria["pedidos_marketplace_na_categoria"] = categorias_marketplace
    estoque_por_categoria = estoque_por_categoria.sort_values("pct_critico", ascending=False)
    print(estoque_por_categoria.to_string())
    salvar(estoque_por_categoria, "C3_estoque_critico_x_categoria_marketplace")


# ============================================================================
# MAIN
# ============================================================================
def main():
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    vendas, marketing = bloco_a_escala_bases()
    marketplace = bloco_b_causa_raiz_marketplace(vendas)
    bloco_c_cruzamentos(vendas)

    titulo("CONCLUÍDO")
    print(f"Todas as tabelas de resultado foram salvas em: {os.path.abspath(PASTA_SAIDA)}")


if __name__ == "__main__":
    main()