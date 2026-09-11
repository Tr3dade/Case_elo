# Case FitNutri — Queda de Ticket Médio
### Documento de Contextualização (BootCamp Nova Geração)
Integrantes: Pedro Tinoco, Matheus Trindade e Ana Laura

---


## 1. Contexto de Negócio

A FitNutri é uma rede de 3 lojas de suplementos e alimentação saudável (Centro,
Shopping Norte, Barra). Nos últimos 12 meses, o número de pedidos cresceu, mas
o **ticket médio caiu**. O diretor comercial pediu para entender:

- Por que o ticket médio cai se o volume de pedidos cresce?
- A queda é uniforme ou concentrada em algum corte (loja, categoria, canal)?
- Qual a oportunidade financeira de reverter o cenário?

## 2. Bases utilizadas

| Base | Grão | Descrição |
|---|---|---|
| `pedidos.csv` | 1 linha por pedido | receita, itens, loja, cliente, canal, desconto |
| `produtos.csv` | 1 linha por produto | categoria, preço de lista, margem |
| `campanhas_marketing.csv` | 1 linha por campanha-mês | canal, investimento, cupom, desconto médio |

## 3. Metodologia seguida

O notebook segue as 6 etapas pedidas no enunciado, cada uma com prompt no
formato **Papel + Contexto + Dado + Tarefa + Formato + Restrição**, para
manter o processo auditável (qualquer pessoa consegue rodar de novo e chegar
no mesmo número):

1. **Perfilar** as bases (tamanho, período, tipos, nulos)
2. **Tratar** anomalias (duplicados, pedidos de teste, valores inválidos)
3. **Explorar** o ticket médio por dimensão (mês, loja, canal, categoria)
4. **Testar hipótese** em cortes independentes dos dados
5. **Dimensionar** a oportunidade financeira
6. **Sintetizar** em um diagnóstico de uma frase com número

## 4. O que foi encontrado, passo a passo

### 4.1 Perfilar
- 13.835 pedidos, período de jul/2025 a jun/2026, sem colunas nulas.
- `pedido_id` não tem duplicados.
- As categorias de `pedidos.categoria_principal` batem 100% com
  `produtos.categoria` — mas **não há `produto_id` em `pedidos.csv`**, então
  o cruzamento entre as duas bases só é possível pelo nome da categoria, não
  por chave direta. Isso foi registrado como premissa, não contornado.

### 4.2 Tratar
Checamos especificamente: linhas duplicadas, receita/itens inválidos (≤ 0),
desconto fora da faixa 0–100% e clientes com volume de pedidos muito acima do
normal (possíveis contas de teste). **Nenhuma anomalia crítica foi
encontrada** — decisão: nenhum registro foi removido ou alterado, a base
segue integral para a exploração.

### 4.3 Explorar
- Ticket médio cai de **~R$ 220 para ~R$ 142** (-35%) entre o primeiro e o
  segundo semestre da base.
- O código identifica sozinho o **mês-pivô** (mês com a maior queda mês a
  mês), em vez de assumir um mês fixo — se a base mudar, a análise se
  reajusta sozinha.
- Abrindo por loja: a queda é praticamente igual nas 3 (Centro, Shopping
  Norte, Barra) — não é operação de loja.
- Abrindo por canal: a queda **não é uniforme** — alguns canais caem muito
  mais que outros.

### 4.4 Testar Hipótese
Hipótese levantada na exploração: a queda está concentrada nos canais
**Influencer** e **Instagram Ads**. Testamos em 4 cortes independentes:

| Corte | Resultado |
|---|---|
| Por loja | Queda de ~33–36% em todas — descarta causa operacional de loja |
| Por canal | Influencer e Instagram Ads caem **~70%**; os demais (Busca Paga, CRM/Email, Orgânico) variam menos de 2% |
| Timing (campanhas_marketing.csv) | Cupom de desconto ativado exatamente nesses 2 canais a partir do mês-pivô, com desconto médio saltando de ~4% para 15–30% |
| Itens/mix por pedido | Nº de itens cai de ~2,3 para ~1,6 nesses canais; mix migra para categorias de ticket mais baixo (Barras e Snacks) e cai a fatia de Whey Protein (ticket alto) |

A hipótese se sustenta em todos os 4 cortes — não é coincidência.

### 4.5 Dimensionar a Oportunidade
Fórmula: **Base Afetada × Alavanca × Taxa de Captura**

- Base afetada: ~8.078 pedidos/ano (run-rate) nos canais Influencer +
  Instagram Ads
- Alavanca: R$ 156,89 de ticket perdido por pedido nesses canais (ticket
  atual vs. ticket que os mesmos canais tinham antes do cupom)
- Cenários de taxa de captura (nunca 100%, pois reduzir o desconto tem custo
  de conversão):

| Cenário | Taxa de captura | Oportunidade anual |
|---|---|---|
| Conservador | 30% | ~R$ 380 mil |
| Base | 50% | ~R$ 634 mil |
| Otimista | 70% | ~R$ 887 mil |

## 5. Diagnóstico final

| Item | Descrição |
|---|---|
| **Fato** | O ticket médio caiu 35% de R$ 220 para R$ 142 entre o 1º e o 2º semestre da base |
| **Causa** | Ativação de cupom de desconto em Influencer e Instagram Ads (4% → 15–30%), que também passaram a concentrar mais volume (~12% → ~25% dos pedidos) e migraram o mix para categorias de ticket mais baixo |
| **Implicação** | R$ 380 mil a R$ 887 mil/ano em receita não capturada |
| **Ação recomendada** | Revisar a política de cupom nesses 2 canais (reduzir desconto médio e/ou restringir a itens de ticket mais alto), monitorando a conversão para não perder volume |

## 6. Premissas registradas (para defesa em banca/apresentação)

1. Cruzamento `pedidos` × `produtos` é feito pelo nome da categoria, não por
   chave — não há `produto_id` em `pedidos.csv`.
2. Nenhum registro foi removido no tratamento — não havia anomalia crítica
   confirmada nos dados.
3. O "mês-pivô" é definido pelo próprio código (maior queda mês a mês), não
   fixado manualmente.
4. O ticket de referência usado na etapa 4 é o histórico real dos MESMOS
   canais antes do cupom — não um benchmark externo — para não comparar
   canais estruturalmente diferentes entre si.
5. A taxa de captura é uma faixa (30–70%), não um número único, porque
   reduzir desconto tem efeito colateral esperado na conversão que os dados
   disponíveis não permitem quantificar com precisão.

## 7. Como reproduzir

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m ipykernel install --user --name=fitnutri-venv
```

Os 3 CSVs devem estar em `data/data_aula6/`. Depois é só abrir
`Aula_06_HandsOn.ipynb`, selecionar o kernel `fitnutri-venv` e rodar todas as
células em ordem — cada célula de código já traz o prompt (Papel + Contexto
+ Dado + Tarefa + Formato + Restrição) usado para gerá-la, como comentário no
topo, para manter o processo rastreável.
