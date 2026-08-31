from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
BASE_DATA_DIR = BASE_DIR / "base"
RESPOSTA_DIR = BASE_DIR / "resposta"
OUTPUT_SUMARIO = RESPOSTA_DIR / "indicadores_resumo.csv"
OUTPUT_DETALHADO = RESPOSTA_DIR / "dados_consolidados.csv"
OUTPUT_CLIENTES_ATIVOS = RESPOSTA_DIR / "clientes_que_compraram.csv"


def carregar_csv(nome_arquivo: str) -> pd.DataFrame:
    caminho = BASE_DATA_DIR / nome_arquivo
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    return pd.read_csv(caminho, encoding="utf-8")


def adicionar_linha(resumo: list, dimensao: str, indicador: str, valor, unidade: str = "") -> None:
    resumo.append({
        "dimensao": dimensao,
        "indicador": indicador,
        "valor": valor,
        "unidade": unidade,
    })


def montar_indicadores() -> pd.DataFrame:
    clientes = carregar_csv("clientes.csv")
    estoque = carregar_csv("estoque.csv")
    marketing = carregar_csv("marketing.csv")
    vendas = carregar_csv("vendas.csv")
    atendimento = carregar_csv("atendimento.csv")

    for df, colunas_numeric in [
        (clientes, ["renda_estimada", "total_pedidos_historico", "ltv_acumulado"]),
        (estoque, ["lead_time_reposicao", "custo_unitario", "preco_venda_sugerido", "estoque_fisico", "estoque_reservado", "estoque_disponivel", "ponto_pedido", "shelf_life_dias", "volume_m3"]),
        (marketing, ["investimento_reais", "impressoes", "cliques", "conversoes", "roas", "receita_gerada", "cac"]),
        (vendas, ["quantidade", "preco_unitario", "receita_bruta", "desconto_reais", "receita_liquida", "custo_produto", "custo_frete", "margem_contribuicao", "tempo_entrega_real"]),
        (atendimento, ["nota_csat", "tempo_primeira_resposta_minutos", "custo_operacional_ticket"]),
    ]:
        for coluna in colunas_numeric:
            if coluna in df.columns:
                df[coluna] = pd.to_numeric(df[coluna], errors="coerce")

    resumo = []

    # Indicadores de clientes
    adicionar_linha(resumo, "Clientes", "Total de clientes", len(clientes), "qtd")
    adicionar_linha(resumo, "Clientes", "Clientes com opt-in newsletter", int(clientes[clientes["opt_in_newsletter"].astype(str).str.lower() == "true"].shape[0]), "qtd")
    adicionar_linha(resumo, "Clientes", "Renda média estimada", round(clientes["renda_estimada"].mean(), 2), "R$")
    adicionar_linha(resumo, "Clientes", "LTV médio acumulado", round(clientes["ltv_acumulado"].mean(), 2), "R$")
    adicionar_linha(resumo, "Clientes", "Pedidos médios por cliente", round(clientes["total_pedidos_historico"].mean(), 2), "qtd")
    adicionar_linha(resumo, "Clientes", "Clientes por segmento RFM", clientes["segmento_rfm"].value_counts().to_dict(), "dict")
    adicionar_linha(resumo, "Clientes", "Distribuição por gênero", clientes["genero"].value_counts(dropna=False).to_dict(), "dict")
    adicionar_linha(resumo, "Clientes", "Distribuição por estado", clientes["estado"].value_counts().to_dict(), "dict")

    # Indicadores de estoque
    adicionar_linha(resumo, "Estoque", "Total de SKUs", len(estoque), "qtd")
    adicionar_linha(resumo, "Estoque", "Estoque físico total", round(estoque["estoque_fisico"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Estoque", "Estoque disponível total", round(estoque["estoque_disponivel"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Estoque", "Estoque crítico", int(estoque[estoque["status_disponibilidade"].str.contains("Crítico", na=False)].shape[0]), "qtd")
    adicionar_linha(resumo, "Estoque", "Valor médio de custo unitário", round(estoque["custo_unitario"].mean(), 2), "R$")
    adicionar_linha(resumo, "Estoque", "Tempo médio de reposição", round(estoque["lead_time_reposicao"].mean(), 2), "dias")
    adicionar_linha(resumo, "Estoque", "Status de disponibilidade", estoque["status_disponibilidade"].value_counts().to_dict(), "dict")

    # Indicadores de marketing
    adicionar_linha(resumo, "Marketing", "Investimento total", round(marketing["investimento_reais"].sum(), 2), "R$")
    adicionar_linha(resumo, "Marketing", "Impressões totais", round(marketing["impressoes"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Marketing", "Cliques totais", round(marketing["cliques"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Marketing", "Conversões totais", round(marketing["conversoes"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Marketing", "Receita gerada total", round(marketing["receita_gerada"].sum(), 2), "R$")
    adicionar_linha(resumo, "Marketing", "ROAS médio", round(marketing["roas"].mean(), 2), "x")
    adicionar_linha(resumo, "Marketing", "CAC médio", round(marketing["cac"].mean(), 2), "R$")
    adicionar_linha(resumo, "Marketing", "Campanhas ativas", int(marketing[marketing["status"].astype(str).str.lower() == "ativa"].shape[0]), "qtd")
    adicionar_linha(resumo, "Marketing", "Campanhas por canal", marketing["canal"].value_counts().to_dict(), "dict")

    # Indicadores de vendas
    vendas["receita_liquida"] = pd.to_numeric(vendas["receita_liquida"], errors="coerce")
    vendas["margem_contribuicao"] = pd.to_numeric(vendas["margem_contribuicao"], errors="coerce")
    vendas["devolvido"] = vendas["devolvido"].astype(str).str.lower() == "true"

    adicionar_linha(resumo, "Vendas", "Total de pedidos", len(vendas), "qtd")
    adicionar_linha(resumo, "Vendas", "Receita líquida total", round(vendas["receita_liquida"].sum(), 2), "R$")
    adicionar_linha(resumo, "Vendas", "Margem de contribuição total", round(vendas["margem_contribuicao"].sum(), 2), "R$")
    adicionar_linha(resumo, "Vendas", "Ticket médio", round(vendas["receita_liquida"].mean(), 2), "R$")
    adicionar_linha(resumo, "Vendas", "Quantidade de itens vendidos", round(vendas["quantidade"].sum(), 2), "qtd")
    adicionar_linha(resumo, "Vendas", "Pedidos devolvidos", int(vendas["devolvido"].sum()), "qtd")
    adicionar_linha(resumo, "Vendas", "Taxa de devolução", round((vendas["devolvido"].mean() * 100), 2), "%")
    adicionar_linha(resumo, "Vendas", "Tempo médio de entrega", round(vendas["tempo_entrega_real"].mean(), 2), "dias")
    adicionar_linha(resumo, "Vendas", "Receita por categoria", vendas.groupby("categoria")["receita_liquida"].sum().sort_values(ascending=False).to_dict(), "dict")
    adicionar_linha(resumo, "Vendas", "Método de pagamento", vendas["metodo_pagamento"].value_counts().to_dict(), "dict")

    # Indicadores de atendimento
    atendimento["nota_csat"] = pd.to_numeric(atendimento["nota_csat"], errors="coerce")
    atendimento["tempo_primeira_resposta_minutos"] = pd.to_numeric(atendimento["tempo_primeira_resposta_minutos"], errors="coerce")
    atendimento["custo_operacional_ticket"] = pd.to_numeric(atendimento["custo_operacional_ticket"], errors="coerce")

    taxa_resolucao = (atendimento["status_atendimento"].astype(str).str.lower().eq("resolvido").mean() * 100)
    taxa_aberto = (atendimento["status_atendimento"].astype(str).str.lower().eq("aberto").mean() * 100)
    taxa_analise = (atendimento["status_atendimento"].astype(str).str.lower().eq("em análise").mean() * 100)

    adicionar_linha(resumo, "Atendimento", "Total de tickets", len(atendimento), "qtd")
    adicionar_linha(resumo, "Atendimento", "Taxa de resolução", round(taxa_resolucao, 2), "%")
    adicionar_linha(resumo, "Atendimento", "Taxa em aberto", round(taxa_aberto, 2), "%")
    adicionar_linha(resumo, "Atendimento", "Taxa em análise", round(taxa_analise, 2), "%")
    adicionar_linha(resumo, "Atendimento", "CSAT médio", round(atendimento["nota_csat"].mean(), 2), "pts")
    adicionar_linha(resumo, "Atendimento", "Tempo médio de primeira resposta", round(atendimento["tempo_primeira_resposta_minutos"].mean(), 2), "min")
    adicionar_linha(resumo, "Atendimento", "Custo operacional médio por ticket", round(atendimento["custo_operacional_ticket"].mean(), 2), "R$")
    adicionar_linha(resumo, "Atendimento", "Problemas por categoria", atendimento["categoria_problema"].value_counts().to_dict(), "dict")
    adicionar_linha(resumo, "Atendimento", "Status do atendimento", atendimento["status_atendimento"].value_counts().to_dict(), "dict")

    resumo_df = pd.DataFrame(resumo)
    resumo_df["valor"] = resumo_df["valor"].apply(lambda x: str(x).replace("{", "").replace("}", "") if isinstance(x, dict) else x)
    return resumo_df


def montar_dados_consolidados() -> tuple[pd.DataFrame, pd.DataFrame]:
    clientes = carregar_csv("clientes.csv")
    vendas = carregar_csv("vendas.csv")

    vendas = vendas.copy()
    vendas["quantidade"] = pd.to_numeric(vendas["quantidade"], errors="coerce")
    vendas["receita_liquida"] = pd.to_numeric(vendas["receita_liquida"], errors="coerce")
    vendas["margem_contribuicao"] = pd.to_numeric(vendas["margem_contribuicao"], errors="coerce")

    clientes_agg = clientes[["customer_id", "segmento_rfm", "estado", "cidade", "nivel_fidelidade", "ltv_acumulado"]].copy()
    vendas_agg = vendas.groupby("customer_id", as_index=False).agg(
        total_pedidos_vendas=("order_id", "nunique"),
        receita_liquida_total=("receita_liquida", "sum"),
        margem_total=("margem_contribuicao", "sum"),
        quantidade_itens=("quantidade", "sum"),
    )

    consolidado = clientes_agg.merge(vendas_agg, on="customer_id", how="left")
    consolidado["receita_liquida_total"] = consolidado["receita_liquida_total"].fillna(0)
    consolidado["margem_total"] = consolidado["margem_total"].fillna(0)
    consolidado["total_pedidos_vendas"] = consolidado["total_pedidos_vendas"].fillna(0)
    consolidado["quantidade_itens"] = consolidado["quantidade_itens"].fillna(0)
    consolidado["ltv_acumulado"] = pd.to_numeric(consolidado["ltv_acumulado"], errors="coerce")

    clientes_ativos = consolidado[consolidado["total_pedidos_vendas"] > 0].copy()
    clientes_ativos = clientes_ativos.reset_index(drop=True)

    return consolidado, clientes_ativos


def main() -> None:
    BASE_DATA_DIR.mkdir(exist_ok=True)
    RESPOSTA_DIR.mkdir(exist_ok=True)

    resumo_df = montar_indicadores()
    resumo_df.to_csv(OUTPUT_SUMARIO, index=False, encoding="utf-8")

    consolidado, clientes_ativos = montar_dados_consolidados()
    consolidado.to_csv(OUTPUT_DETALHADO, index=False, encoding="utf-8")
    clientes_ativos.to_csv(OUTPUT_CLIENTES_ATIVOS, index=False, encoding="utf-8")

    print(f"Arquivo gerado: {OUTPUT_SUMARIO}")
    print(f"Arquivo gerado: {OUTPUT_DETALHADO}")
    print(f"Arquivo gerado: {OUTPUT_CLIENTES_ATIVOS}")
    print(f"Clientes totais: {len(consolidado)}")
    print(f"Clientes ativos: {len(clientes_ativos)}")
    print("\nPreview dos indicadores:")
    print(resumo_df.head(15).to_string(index=False))


if __name__ == "__main__":
    main()
