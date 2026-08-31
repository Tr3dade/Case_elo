# Relatório de Inconsistências de Dados — Vértice Retail

**Escopo:** varredura das 5 bases fornecidas (`vendas.csv`, `marketing.csv`, `clientes.csv`, `atendimento.csv`, `estoque.csv`)
**Objetivo:** mapear inconsistências, descompassos e limitações dos dados antes das análises, para que fiquem documentadas e não sejam confundidas com achados de negócio.
**Método:** checagem de (1) cobertura temporal por base, (2) integridade referencial entre chaves (`customer_id`, `sku_id`, `order_id`), (3) consistência de categorias/canais entre bases, (4) consistência interna de fórmulas (receita, margem, ROAS, estoque), (5) nulos, duplicatas e valores fora de faixa.

---

## 🔴 Críticas — afetam qualquer análise cruzada entre bases

### 1. Descompasso de período temporal entre bases
| Base | Campo de data | Período |
|---|---|---|
| `vendas.csv` | `data_pedido` | 2023-01-01 → **2024-01-26** (390 dias) |
| `marketing.csv` | `data_inicio` / `data_fim` | 2023-01-01 → 2025-12-31 |
| `clientes.csv` | `data_cadastro` | 2020-01-01 → 2025-12-28 |
| `atendimento.csv` | `data_abertura` | 2023-01-01 → 2025-12-31 |
| `estoque.csv` | `data_ultima_entrada` | 2023-01-01 → 2025-12-28 |

`vendas.csv` cobre apenas ~13 meses, enquanto as demais bases cobrem quase 3 anos. Qualquer cruzamento no mesmo range de datas sub-representa vendas.

### 2. `vendas.csv` cobre uma fração muito pequena da base de clientes
- `clientes.csv`: 15.000 clientes únicos
- `vendas.csv`: transações de apenas **346** desses clientes (2,3%)
- Os outros 14.654 clientes nunca aparecem comprando em `vendas.csv`

### 3. `total_pedidos_historico` e `ltv_acumulado` (clientes.csv) não reconciliam com vendas.csv
- 14.988 de 15.000 clientes (99,9%) têm `total_pedidos_historico` declarado divergente da contagem real de pedidos em `vendas.csv`
- Exemplo: `CLI-00001` declara 7 pedidos históricos, mas tem 0 registros em `vendas.csv`

**Leitura conjunta dos itens 1–3:** tudo indica que `clientes.csv` traz métricas agregadas de uma janela histórica maior (possivelmente desde a fundação da empresa), enquanto `vendas.csv` é um recorte/amostra de um período específico e menor — não são a mesma "fotografia" temporal. Isso deve ser explicitado como limitação metodológica, especialmente em qualquer análise que combine LTV/histórico de clientes com vendas do período recente.

### 4. `atendimento.csv` referencia pedidos que não existem em `vendas.csv`
- 18.724 de 28.589 `order_id` únicos em atendimento (65,5%) não aparecem em `vendas.csv`
- Consequência direta do descompasso temporal do item 1

---

## 🟡 Pontuais — menores, mas relevantes de documentar

### 5. Linha corrompida/vazia ao final de duas bases
- Última linha de `vendas.csv` (`order_id = ORD-072219`): quase todas as colunas nulas
- Última linha de `atendimento.csv` (`ticket_id = "TKT"`, sem sufixo numérico): quase todas as colunas nulas

### 6. Valor de categoria sem correspondência entre bases
- `marketing.csv` (`categoria_foco`) tem o valor **"Geral"**, que não existe em `vendas.csv` nem em `estoque.csv` (que usam apenas: Acessórios, Beleza, Lifestyle, Moda)
- Provavelmente campanhas institucionais/multi-categoria — não é erro, mas exige tratamento explícito em joins por categoria

### 7. 513 clientes com idade < 16 anos na data de cadastro
- Possível erro de geração/digitação em `data_nascimento`

### 8. 82 SKUs em `estoque.csv` nunca aparecem em `vendas.csv`
- Podem ser lançamentos recentes ou produtos sem giro — vale confirmar se é esperado

---

## ✅ Pontos verificados que **não são** inconsistência

| Verificação | Resultado |
|---|---|
| `receita_liquida = receita_bruta − desconto_reais` | Bate em 100% das linhas |
| `margem_contribuicao = receita_liquida − custo_produto − custo_frete` | Bate em 100% das linhas |
| `roas = receita_gerada / investimento_reais` | Bate em 100% das linhas |
| `estoque_disponivel = estoque_fisico − estoque_reservado` | Bate em 100% das linhas |
| Margem de contribuição negativa (491 vendas) | Resultado real, não erro de cálculo. Marketplace concentra a maior parte (114 casos) — reforça o diagnóstico de margem fraca no canal |
| `motivo_devolucao` preenchido com `devolvido=False` | Sempre o valor "Não se aplica" — placeholder esperado, não inconsistência |
| Duplicatas de chave primária (order_id, sku_id, customer_id, campanha_id, ticket_id) | Nenhuma encontrada |
| CSAT fora do intervalo [1,5] | Nenhum caso |
| Cliques > impressões / conversões > cliques | Nenhum caso |
| Estoque físico negativo / reservado > físico | Nenhum caso |
| `data_fechamento` < `data_abertura` (atendimento) | Nenhum caso |

---

## Recomendação para o grupo

Ao definir o escopo das análises (Diagnóstico Executivo, Dashboard, Business Case), recomenda-se:
1. **Deixar explícito o recorte temporal usado em cada análise** — especialmente quando `vendas.csv` for cruzado com `marketing`/`atendimento`/`clientes`, alinhar ao período comum (2023-01 a 2024-01) ou justificar o uso de janelas diferentes.
2. **Não usar `total_pedidos_historico`/`ltv_acumulado` de `clientes.csv` como se fossem derivados de `vendas.csv`** — são fontes independentes.
3. Tratar a linha corrompida final de `vendas.csv` e `atendimento.csv` como ruído a excluir (ou remover) antes de qualquer agregação.
4. Ao segmentar por categoria usando `marketing.csv`, decidir como tratar o valor "Geral" (excluir, ratear ou manter como categoria própria).

*Nenhum dado original foi alterado — este relatório é apenas descritivo, baseado em leitura direta dos arquivos CSV fornecidos.*
