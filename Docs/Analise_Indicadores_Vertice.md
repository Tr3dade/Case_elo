# Análise dos Indicadores — Vértice Retail
**Artefato de processo · Diagnóstico quantitativo das 5 bases (vendas, marketing, clientes, atendimento, estoque)**
Período coberto pelas vendas: **jan/2023 a jan/2024** (13 meses) · 27.759 pedidos

---

## 1. Visão geral do negócio

| Indicador | Valor |
|---|---|
| Receita bruta | R$ 20.526.133,84 |
| Receita líquida | R$ 18.889.334,01 |
| Desconto total concedido | R$ 1.636.799,83 (**7,97%** da receita bruta) |
| Margem de contribuição (reportada) | R$ 10.270.436,65 (**54,4%** sobre receita líquida) |
| Taxa de devolução | **14,87%** dos pedidos |
| Pedidos com margem negativa | 491 (1,77%) |

A margem média de 54,4% parece saudável isoladamente, mas duas descobertas abaixo mostram que ela está **superestimada** e **mal distribuída**.

---

## 2. Achado crítico #1 — A margem reportada não desconta as devoluções

A coluna `margem_contribuicao` é **idêntica em média** entre pedidos devolvidos (R$ 369,08) e não devolvidos (R$ 370,16). Ou seja, o sistema contabiliza a margem do pedido devolvido como se ela tivesse sido realizada.

- 4.127 pedidos devolvidos "carregam" **R$ 1.523.188,67 em margem fantasma** (14,8% da margem total reportada).
- Considerando frete de ida e volta, reposição de estoque e custo operacional do ticket de troca/defeito, a **margem real da operação é inferior aos 54,4% divulgados** — provavelmente mais próxima de ~46-48% líquidos de devolução.
- **Motivos de devolução:** Defeito (25,2%), Tamanho errado (24,8%), Atraso na entrega (19,6%), Não gostei (16,2%), Arrependimento (14,2%).

**Implicação para a diretoria:** o KPI de margem hoje reportado ao board está inflado. Qualquer decisão de precificação, desconto ou investimento baseada nele subestima o problema real de rentabilidade.

---

## 3. Achado crítico #2 — Marketplace: maior canal, pior margem

| Canal | Pedidos | Receita líquida | Margem % | Desconto % | Devolução % |
|---|---|---|---|---|---|
| **Marketplace** | 6.040 | R$ 3,99M | **51,4%** | 7,7% | 15,0% |
| Google Ads | 5.505 | R$ 3,64M | 54,8% | 8,5% | 15,2% |
| Instagram Ads | 4.965 | R$ 3,27M | 55,0% | 8,0% | 15,1% |
| Orgânico | 3.246 | R$ 2,14M | 55,2% | 7,7% | 14,4% |
| Influenciador | 2.263 | R$ 2,06M | 55,6% | 8,3% | 15,0% |
| TikTok Ads | 2.928 | R$ 1,90M | 55,1% | 8,3% | 14,3% |
| Email Marketing | 2.812 | R$ 1,89M | 55,6% | 7,2% | 14,6% |

- Marketplace é o **maior canal em volume** e concentra o **maior número de pedidos com margem negativa (114 de 491, 23%)** — desproporcional ao seu peso de 21,8% do total de pedidos.
- Isso confirma a hipótese "crescimento com pior qualidade de margem": o canal que mais cresce em volume é o que menos contribui, proporcionalmente, para o resultado.

**Por categoria**, a margem é homogênea (Moda 54,5%, Beleza 54,4%, Lifestyle 54,1%, Acessórios 54,5%) e no nível de produto/SKU a variação também é pequena (52%–56%) — ou seja, **o problema de margem não está concentrado em produtos específicos, e sim em canal de venda e em devoluções**.

**Sazonalidade:** os meses de março, maio, novembro e dezembro/2023 concentram picos de volume (campanhas/datas comerciais). Novembro/23 é o mês com maior desconto médio (9,5%) e leve queda de margem (53,2%) — coerente com Black Friday.

---

## 4. Achado crítico #3 — Marketing: atribuição de receita não bate com a venda real

| Canal | Investimento | Receita "gerada" (mkt) | CAC | ROAS reportado |
|---|---|---|---|---|
| Influenciador | R$ 28,1M | R$ 217,6M | 1,76 | **7,75x** |
| TikTok Ads | R$ 29,8M | R$ 139,1M | 1,75 | 4,67x |
| Instagram Ads | R$ 30,2M | R$ 135,9M | 1,96 | 4,51x |
| Google Ads | R$ 30,2M | R$ 106,6M | 1,88 | 3,53x |
| Marketplace | R$ 32,7M | R$ 98,8M | 1,83 | 3,02x |
| Email Marketing | R$ 29,7M | R$ 91,0M | 1,79 | 3,07x |
| Orgânico | R$ 29,8M | R$ 89,6M | 1,82 | 3,01x |

**Problema de dados grave:** a base de marketing reporta **R$ 878,6 milhões** em "receita gerada" e R$ 210,4 milhões em investimento — mas a receita líquida **real**, registrada em `vendas.csv` no mesmo período, é de apenas **R$ 18,9 milhões**. A "receita gerada" do marketing é **~46x maior** que a receita efetivamente vendida.

Isso é exatamente o problema de **atribuição descolada da venda real** mencionado no briefing do case (Módulo A): cada campanha está contando conversões/receita de forma independente e sobreposta (multi-touch sem deduplicação, ou uso de projeção/potencial em vez de venda realizada). Na prática, **os ROAS e CAC reportados pelo time de marketing hoje não são confiáveis para decisão de alocação de budget** sem reconciliação com a base de vendas real.

**Achado positivo:** mesmo com essa ressalva, **Influenciador é consistentemente o canal mais eficiente** (maior ROAS, CAC comparável aos demais) — contrariando a hipótese inicial do briefing de que influenciadores trariam CAC alto e margem ruim. O canal problemático é o **Marketplace**, não o Influenciador.

---

## 5. Clientes — concentração de valor e risco de churn

| Segmento RFM | Clientes | % base | LTV médio | LTV total | Pedidos médios |
|---|---|---|---|---|---|
| Fiel | 2.612 | 17,4% | R$ 16.897 | R$ 44,1M | 34,2 |
| Campeão | 1.268 | 8,5% | R$ 26.671 | R$ 33,8M | 54,0 |
| Promissor | 4.127 | 27,5% | R$ 8.078 | R$ 33,3M | 16,0 |
| Em Risco | 3.269 | 21,8% | R$ 5.403 | R$ 17,7M | 10,7 |
| Hibernando | 1.928 | 12,9% | R$ 2.667 | R$ 5,1M | 5,3 |
| Churn | 1.796 | 12,0% | R$ 2.782 | R$ 5,0M | 5,4 |

- **Fiéis + Campeões = 25,9% dos clientes, mas 56,1% do LTV total da base** (R$ 77,9M de R$ 139,1M). Concentração alta de valor em poucos clientes — clássico 80/20.
- **Em Risco + Hibernando + Churn = 46,6% da base** (6.993 clientes) mas apenas **20% do LTV total**. É um contingente grande e de baixo valor unitário — não são o foco de recuperação de margem, mas representam custo de aquisição/atendimento não recuperado.
- Nível de fidelidade: 50% da base ainda é Bronze (7.485 clientes), sinal de que o programa de fidelidade ainda não amadureceu a base.

**Implicação:** ações de retenção devem priorizar "Em Risco" (3.269 clientes, R$ 17,7M de LTV em jogo) — é o segmento com maior LTV agregado entre os grupos de risco, ainda recuperável antes de hibernar/churnar.

---

## 6. Atendimento — onde está o custo e o retrabalho

Total de tickets: **35.841** · Custo operacional total: **R$ 532.260** · CSAT médio: **3,24/5** · Tempo médio de 1ª resposta: **135 minutos**

| Categoria do problema | Tickets | % do total | Custo total | CSAT médio |
|---|---|---|---|---|
| Onde está meu pedido? | 10.765 | **30,0%** | R$ 159.660 | 2,99 |
| Defeito | 6.509 | 18,2% | R$ 96.592 | 2,82 (pior) |
| Troca de Tamanho | 5.360 | 15,0% | R$ 79.325 | 2,99 |
| Dúvida Técnica | 5.314 | 14,8% | R$ 78.888 | 3,83 |
| Pagamento não aprovado | 4.281 | 11,9% | R$ 63.856 | 2,99 |
| Elogio | 3.611 | 10,1% | R$ 53.939 | 4,57 |

- **"Onde está meu pedido?" é, isoladamente, o maior gerador de tickets (30%) e de custo (30%)** — é o principal candidato a automação via IA (status de rastreio automatizado), com potencial de reduzir tempo de resposta e custo sem intervenção humana.
- **"Defeito" tem o pior CSAT (2,82)** e conecta diretamente com a categoria "Produto com defeito", principal motivo de devolução (25% das devoluções) — sinal de problema de qualidade/fornecedor, não só de operação logística.
- 20% dos tickets ainda estão **Aberto/Em Análise/Escalado para N2** (não resolvidos), indicando fila de trabalho represada.

---

## 7. Estoque — ruptura e criticidade

| Status | SKUs | % |
|---|---|---|
| Em Estoque | 3.993 | 79,9% |
| Estoque Crítico | 701 | 14,0% |
| Ruptura | 99 | 2,0% |
| Descontinuado | 207 | 4,1% |

- **800 SKUs (16% do catálogo) estão em ruptura ou estoque crítico**, representando **R$ 7,25 milhões em valor de estoque disponível exposto a risco de venda perdida**.
- Categoria Moda tem o maior estoque médio disponível (424 unid./SKU) e também o maior catálogo (1.729 SKUs) — merece prioridade na checagem de ruptura por concentrar volume de vendas.
- Lead time médio de reposição gira em torno de 26-28 dias em todas as categorias — não há uma categoria estruturalmente mais lenta que outra.

---

## 8. Síntese executiva — onde a margem está vazando

1. **Devoluções não descontadas da margem reportada** → ~R$ 1,52M de margem "fantasma" (14,8% do total). *Correção imediata do KPI + causa raiz em Defeito e Tamanho errado.*
2. **Canal Marketplace com margem estruturalmente mais baixa** (51,4% vs ~55%) e maior concentração de pedidos deficitários. *Candidato a revisão de comissionamento/precificação nesse canal.*
3. **Atribuição de marketing dissociada da venda real** (receita "gerada" 46x maior que a receita líquida real) → decisões de mídia hoje não são confiáveis. *Precisa de reconciliação analítica antes de qualquer realocação de budget.*
4. **"Onde está meu pedido?" consome 30% do atendimento** → maior oportunidade de automação/triagem por IA (Módulo B do case).
5. **6.993 clientes em risco/hibernando/churn** (47% da base) — foco de retenção deve ser o segmento "Em Risco" (maior LTV recuperável).
6. **16% do catálogo em ruptura/crítico**, R$ 7,25M expostos — risco direto de receita não capturada e possível motor de devoluções por atraso.

---
*Artefato gerado via análise quantitativa das bases. Metodologia: agregações por canal, categoria, produto, segmento RFM e categoria de ticket; cruzamento de taxas de devolução e status de margem.*
