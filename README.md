# Case Elo - Estrutura e fluxo de análise

Este projeto organiza as bases de dados de origem em uma pasta dedicada e gera arquivos de resposta em outra pasta, permitindo uma análise estruturada e reutilizável.

## Estrutura do projeto

- `base/` — arquivos CSV utilizados como fonte de dados para análise
- `saida/` — arquivos gerados após processamento e consolidação
- `consolidar_tabelas.py` — script principal que lê as bases, consolida os dados e exporta as saídas

## Tabelas de entrada (`base/`)

### 1. `clientes.csv`
Contém os dados cadastrais dos clientes.

Colunas principais:
- `customer_id` — identificador do cliente
- `nome_completo` — nome completo
- `data_nascimento` — data de nascimento
- `genero` — gênero
- `estado` e `cidade` — localização
- `nivel_fidelidade` — nível de fidelidade
- `data_cadastro` — data do cadastro
- `opt_in_newsletter` — consentimento para recebimento de e-mails
- `dispositivo_principal` — dispositivo principal utilizado
- `renda_estimada` — renda estimada
- `total_pedidos_historico` — quantidade histórica de pedidos
- `ltv_acumulado` — valor total de vida útil do cliente
- `segmento_rfm` — segmentação RFM

Uso: permite analisar perfil do cliente, mix geográfico, comportamento de fidelidade e potencial de retenção.

### 2. `vendas.csv`
Contém os pedidos realizados.

Colunas principais:
- `order_id` — identificador do pedido
- `customer_id` — cliente associado ao pedido
- `sku_id` — produto vendido
- `data_pedido` — data do pedido
- `canal` — canal de venda
- `categoria` — categoria do produto
- `produto` — nome do produto
- `quantidade` — itens vendidos
- `preco_unitario` — preço por unidade
- `receita_bruta` — receita bruta
- `desconto_reais` — valor do desconto
- `receita_liquida` — receita após desconto
- `custo_produto` — custo de produção/compra
- `custo_frete` — custo de entrega
- `metodo_pagamento` — forma de pagamento
- `status_pagamento` — status do pagamento
- `margem_contribuicao` — margem gerada pelo pedido
- `tempo_entrega_real` — tempo de entrega real
- `devolvido` — se o pedido foi devolvido
- `motivo_devolucao` — motivo da devolução

Uso: serve como base para KPIs de receita, margem, devolução, canais e desempenho operacional.

### 3. `estoque.csv`
Contém o catálogo de produtos e o estado do estoque.

Colunas principais:
- `sku_id` — identificador do SKU
- `nome_produto` — nome do produto
- `categoria` e `subcategoria` — classificação do produto
- `fornecedor_id` — fornecedor
- `lead_time_reposicao` — tempo de reposição
- `custo_unitario` — custo do produto
- `preco_venda_sugerido` — preço sugerido
- `estoque_fisico` — quantidade em estoque físico
- `estoque_reservado` — quantidade reservada
- `estoque_disponivel` — quantidade disponível para venda
- `ponto_pedido` — ponto de reposição
- `data_ultima_entrada` — última entrada
- `status_disponibilidade` — disponibilidade do produto
- `shelf_life_dias` — prazo de validade em dias
- `volume_m3` — volume do SKU em m³

Uso: permite identificar ruptura, estoque crítico, SKU em risco e a eficiência do reposicionamento.

### 4. `marketing.csv`
Contém os dados de campanhas e performance de marketing.

Colunas principais:
- `campanha_id` — identificador da campanha
- `nome_campanha` — nome da campanha
- `canal` — canal de mídia
- `categoria_foco` — categoria priorizada
- `data_inicio` e `data_fim` — período da campanha
- `investimento_reais` — valor investido
- `impressoes` — quantidade de impressões
- `cliques` — quantidade de cliques
- `conversoes` — conversões geradas
- `atribuicao` — modelo de atribuição
- `status` — status da campanha
- `roas` — retorno sobre anúncio
- `receita_gerada` — receita atribuída
- `cac` — custo de aquisição do cliente

Uso: ajuda a monitorar desempenho de canais, eficiência de aquisição e qualidade da atribuição de receita.

### 5. `atendimento.csv`
Contém os tickets de atendimento ao cliente.

Colunas principais:
- `ticket_id` — identificador do ticket
- `customer_id` — cliente relacionado
- `order_id` — pedido relacionado
- `data_abertura` / `data_fechamento` — datas do atendimento
- `canal_entrada` — canal pelo qual o ticket chegou
- `categoria_problema` — tipo de problema
- `status_atendimento` — status do ticket
- `texto_cliente` — mensagem do cliente
- `nota_csat` — avaliação do cliente
- `tempo_primeira_resposta_minutos` — tempo da primeira resposta
- `custo_operacional_ticket` — custo operacional do atendimento

Uso: permite avaliar qualidade do atendimento, custos operacionais e principais causas de insatisfação.

### Arquivos de saída (`saida/`)

### `indicadores_resumo.csv`
Tabela com indicadores agregados por área (Clientes, Vendas, Marketing, Estoque e Atendimento).

Ela reúne os principais KPIs para dar uma visão executiva do negócio.

### `dados_consolidados.csv`
Base de clientes consolidada com dados de vendas.

Estrutura:
- `customer_id`
- `segmento_rfm`
- `estado`
- `cidade`
- `nivel_fidelidade`
- `ltv_acumulado`
- `total_pedidos_vendas`
- `receita_liquida_total`
- `margem_total`
- `quantidade_itens`

Essa tabela mantém todos os clientes e inclui zeros para quem não gerou pedidos, permitindo análises de base completa.

### `clientes_que_compraram.csv`
Versão filtrada da base de clientes, contendo apenas clientes com pelo menos um pedido registrado.

Essa tabela é útil para análise de clientes ativos e para KPIs de performance de compra.

## O que o script `consolidar_tabelas.py` faz

O script executa as seguintes etapas:

1. Localiza as tabelas dentro da pasta `base/`.
2. Lê cada CSV em pandas.
3. Converte colunas numéricas para tipos adequados.
4. Calcula indicadores agregados como:
   - clientes totais
   - média de renda e LTV
   - receita líquida e margem
   - devolução
   - ROAS, CAC e campanhas
   - custo e CSAT de atendimento
   - volume e status de estoque
5. Consolida as bases de clientes e vendas por `customer_id`.
6. Gera uma base completa e outra base filtrada para clientes ativos.
7. Exporta os arquivos CSV para a pasta `saida/`.

## Como executar

No terminal, na pasta do projeto, rode:

```bash
python consolidar_tabelas.py
```

Isso irá atualizar todos os arquivos existentes em `resposta/`.

## Observações

- A organização em `base/` e `resposta/` facilita o reuso e mantém fontes de dados separadas dos artefatos finais.
- O script pode ser expandido para novas tabelas, filtros ou métricas conforme a análise evoluir.
